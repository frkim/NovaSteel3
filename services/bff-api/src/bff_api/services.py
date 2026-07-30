"""Composition root for BFF adapters, workers, state, and audit boundaries."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .adapters import AuditStorePort, IdempotencyStorePort
from .adapters.factory import create_audit_store, create_idempotency_store
from .auth import Authenticator
from .capacity import CapacityAdapter, LocalCapacityAdapter, UnconfiguredArmCapacityAdapter
from .config import Settings
from .copilot_adapter import CopilotAdapter
from .device_adapter import DeviceAdapter
from .dispatch_port import bind_dispatch_agent
from .events import AlertEventBuffer
from .knowledge_adapter import KnowledgeAdapter
from .privacy_adapter import PrivacyAdapter
from .repository import DemoRepository


_ROOT = Path(__file__).resolve().parents[4]
for _source in (
    _ROOT / "services" / "optimizer-worker" / "src",
    _ROOT / "services" / "scoring-worker" / "src",
):
    if str(_source) not in sys.path:
        sys.path.insert(0, str(_source))

from optimizer_worker import EnergyDispatchOptimizer, OptimizationError  # noqa: E402
from optimizer_worker.metrics import record_dispatch_metrics  # noqa: E402
from scoring_worker import ScoringError, ScoringWorker  # noqa: E402
from scoring_worker.metrics import record_quality_metrics, record_rul_metrics  # noqa: E402


@dataclass
class BffServices:
    """Mutable local orchestration state scoped to one FastAPI app instance."""

    settings: Settings
    repository: DemoRepository
    authenticator: Authenticator
    audit: AuditStorePort
    idempotency: IdempotencyStorePort
    events: AlertEventBuffer
    capacity: CapacityAdapter
    knowledge: KnowledgeAdapter
    copilot: CopilotAdapter
    privacy: PrivacyAdapter
    devices: DeviceAdapter
    optimizer: EnergyDispatchOptimizer = field(default_factory=EnergyDispatchOptimizer)
    scorer: ScoringWorker = field(default_factory=ScoringWorker)
    recommendations: dict[str, dict[str, Any]] = field(default_factory=dict)
    forecasts: dict[str, tuple[dict[str, Any], str]] = field(default_factory=dict)

    @classmethod
    def create(cls, settings: Settings) -> "BffServices":
        repository = DemoRepository.load(settings)
        capacity_id = (
            settings.capacity_allowlist[0]
            if settings.capacity_allowlist
            else "cap-novasteel-demo-sc"
        )
        capacity: CapacityAdapter
        if settings.is_demo_mode or settings.capacity_mode == "local":
            capacity = LocalCapacityAdapter(
                capacity_id=capacity_id,
                environment="demo" if settings.is_demo_mode else settings.environment,
            )
        else:
            capacity = UnconfiguredArmCapacityAdapter(
                capacity_id=capacity_id, environment=settings.environment
            )
        knowledge = KnowledgeAdapter(demo_mode=settings.is_demo_mode)
        copilot = CopilotAdapter()
        services = cls(
            settings=settings,
            repository=repository,
            authenticator=Authenticator(settings),
            audit=create_audit_store(),
            idempotency=create_idempotency_store(),
            events=AlertEventBuffer(repository.alerts_rows()),
            capacity=capacity,
            knowledge=knowledge,
            copilot=copilot,
            privacy=PrivacyAdapter(
                knowledge=knowledge,
                copilot=copilot,
                salt=f"novasteel-erasure-{settings.environment}",
            ),
            devices=DeviceAdapter(demo_mode=settings.is_demo_mode),
        )
        # Late binding, not a constructor argument: the dispatch port needs the fully
        # assembled services (optimizer + repository + audit), which do not exist until
        # this instance does.
        bind_dispatch_agent(services)
        return services

    def lining_forecast(self, *, asset_id: str, correlation_id: str) -> dict[str, Any]:
        cached = self.forecasts.get(asset_id)
        if cached is not None:
            return dict(cached[0]) | {"auditRef": cached[1]}
        component_id = self.repository.lining_component(asset_id)
        if component_id is None:
            raise ScoringError("No lining model is configured for this asset.")
        result = self.scorer.score_lining(
            asset_id=asset_id,
            component_id=component_id,
            telemetry=self.repository.raw_telemetry(asset_id),
            source_ref=f"simulator:{self.repository.source}",
        )
        record = self.audit.append(
            domain="furnace",
            entity_id=asset_id,
            correlation_id=correlation_id,
            action="lining.score",
            actor="scoring-worker",
            input_snapshot_ref=f"simulator:{self.repository.source}",
            model_version=result["modelVersion"],
            output={
                "value": result["value"],
                "unit": result["unit"],
                "confidence": result["confidence"],
                "riskScore": result["riskScore"],
            },
        )
        # Emit RUL metrics (side-effect free, no-op when telemetry inactive)
        record_rul_metrics(result)
        self.forecasts[asset_id] = (dict(result), record.audit_id)
        return dict(result) | {"auditRef": record.audit_id}

    def simulate_energy(
        self,
        *,
        site: str,
        horizon_hours: int,
        scenario: str,
        constraints: Mapping[str, Any],
        correlation_id: str,
        actor: str,
    ) -> dict[str, Any]:
        result = self.optimizer.simulate(
            site=site,
            horizon_hours=horizon_hours,
            scenario=scenario,
            energy_intervals=self.repository.raw_energy(site),
            batches=self.repository.raw_heat_batches(site),
            constraints=constraints,
        )
        # Emit dispatch metrics (side-effect free, no-op when telemetry inactive)
        record_dispatch_metrics(result)
        recommendation_id = result["recommendationId"]
        existing = self.recommendations.get(recommendation_id)
        if existing is None:
            self.recommendations[recommendation_id] = dict(result)
            record = self.audit.append(
                domain="energy",
                entity_id=recommendation_id,
                correlation_id=correlation_id,
                action="energy.simulate",
                actor=actor,
                input_snapshot_ref=f"simulator:{self.repository.source}",
                model_version=result["modelVersion"],
                output={
                    "savings": result["savings"],
                    "hardConstraintViolations": result["hardConstraintViolations"],
                },
            )
            self.recommendations[recommendation_id]["auditRef"] = record.audit_id
        return dict(self.recommendations[recommendation_id])

    def energy_recommendation(self, recommendation_id: str) -> dict[str, Any] | None:
        item = self.recommendations.get(recommendation_id)
        return dict(item) if item else None

    def list_recommendations(self, site: str) -> list[dict[str, Any]]:
        return [
            dict(item)
            for item in self.recommendations.values()
            if item.get("site") == site
        ]


__all__ = ["BffServices", "OptimizationError", "ScoringError"]
