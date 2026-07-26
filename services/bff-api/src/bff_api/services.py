"""Composition root for BFF adapters, workers, state, and audit boundaries."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .audit import AppendOnlyAudit
from .auth import Authenticator
from .capacity import CapacityAdapter, LocalCapacityAdapter, UnconfiguredArmCapacityAdapter
from .config import Settings
from .events import AlertEventBuffer
from .idempotency import IdempotencyStore
from .knowledge_adapter import KnowledgeAdapter
from .repository import DemoRepository


_ROOT = Path(__file__).resolve().parents[4]
for _source in (
    _ROOT / "services" / "optimizer-worker" / "src",
    _ROOT / "services" / "scoring-worker" / "src",
):
    if str(_source) not in sys.path:
        sys.path.insert(0, str(_source))

from optimizer_worker import EnergyDispatchOptimizer, OptimizationError  # noqa: E402
from scoring_worker import ScoringError, ScoringWorker  # noqa: E402


@dataclass
class BffServices:
    """Mutable local orchestration state scoped to one FastAPI app instance."""

    settings: Settings
    repository: DemoRepository
    authenticator: Authenticator
    audit: AppendOnlyAudit
    idempotency: IdempotencyStore
    events: AlertEventBuffer
    capacity: CapacityAdapter
    knowledge: KnowledgeAdapter
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
        return cls(
            settings=settings,
            repository=repository,
            authenticator=Authenticator(settings),
            audit=AppendOnlyAudit(),
            idempotency=IdempotencyStore(),
            events=AlertEventBuffer(repository.alerts_rows()),
            capacity=capacity,
            knowledge=KnowledgeAdapter(demo_mode=settings.is_demo_mode),
        )

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
