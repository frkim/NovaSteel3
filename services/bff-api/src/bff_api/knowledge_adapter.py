"""Adapter from the BFF boundary to the completed knowledge orchestrator."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from .contracts import ErrorCode
from .errors import ApiError

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[4]
_KNOWLEDGE_SRC = _ROOT / "services" / "knowledge-orchestrator" / "src"


class KnowledgeAdapter:
    """Delegates the consent/review workflow without reimplementing its internals.

    Selects the Azure Foundry adapter when FOUNDRY_ENDPOINT is configured,
    falling back to the local deterministic agent otherwise. The local path
    is the default and preserves byte-stable demo results.
    """

    def __init__(self, *, demo_mode: bool) -> None:
        if str(_KNOWLEDGE_SRC) not in sys.path:
            sys.path.insert(0, str(_KNOWLEDGE_SRC))
        try:
            from knowledge_orchestrator import KnowledgeOrchestrator
            from knowledge_orchestrator.adapter_factory import create_agent
            from knowledge_orchestrator.models import AudioMetadata
            from knowledge_orchestrator.orchestrator import (
                ConflictError,
                ForbiddenError,
                NotFoundError,
            )
            from knowledge_orchestrator.procedure_workflow import (
                WorkflowError,
                StaleApprovalError,
            )
        except ImportError as exc:  # pragma: no cover - repository integration failure
            raise RuntimeError("knowledge-orchestrator is required by the BFF.") from exc

        # Select agent via the adapter factory (Azure when FOUNDRY_ENDPOINT set,
        # local fixture otherwise). Fail-safe: factory handles import failures.
        agent = create_agent()
        self._orchestrator = KnowledgeOrchestrator(agent=agent)
        self._audio_metadata = AudioMetadata
        self._errors = (NotFoundError, ForbiddenError, ConflictError)
        self._workflow_errors = (WorkflowError, StaleApprovalError)
        self._demo_mode = demo_mode
        if demo_mode:
            self._seed_demo_procedures()

    def create_interview(
        self,
        *,
        operator_ref: str,
        language: str,
        retention_days: int,
        correlation_id: str,
    ) -> dict[str, Any]:
        try:
            created = self._orchestrator.create_interview(
                operator_ref=operator_ref,
                language=language,
                retention_days=retention_days,
                consent_granted=True,
                correlation_id=correlation_id,
            )
            if self._demo_mode:
                self._submit_fixture_audio(created["sessionId"], language, correlation_id)
                draft = self._orchestrator.extract_draft(
                    session_id=created["sessionId"],
                    title="Synthetic hearth-sector verification draft",
                    correlation_id=correlation_id,
                )
                created["draftProcedureId"] = draft.procedure_id
            return created
        except self._errors as exc:
            raise _map_error(exc) from exc

    def transcript(self, session_id: str) -> dict[str, Any]:
        try:
            return self._orchestrator.get_transcript(session_id)
        except self._errors as exc:
            raise _map_error(exc) from exc

    def list_procedures(
        self, *, status: str | None, q: str | None, page: int, size: int
    ) -> dict[str, Any]:
        try:
            return self._orchestrator.list_procedures(
                status=status, q=q, page=page, size=size
            )
        except self._errors as exc:
            raise _map_error(exc) from exc

    def search(self, q: str) -> dict[str, Any]:
        try:
            return self._orchestrator.search_procedures(q)
        except self._errors as exc:
            raise _map_error(exc) from exc

    def query(self, q: str, *, top_k: int = 5) -> dict[str, Any]:
        """Grounded RAG answer with content-safety screening and PII redaction."""
        try:
            return self._orchestrator.answer_query(q, top_k=top_k)
        except self._errors as exc:
            raise _map_error(exc) from exc

    @property
    def orchestrator(self) -> Any:
        """Exposes the orchestrator so the privacy adapter can erase its stores."""
        return self._orchestrator

    def submit_for_review(
        self,
        *,
        procedure_id: str,
        actor: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        try:
            procedure = self._orchestrator.submit_for_review(procedure_id, actor)
            return self._orchestrator._procedure_view(procedure)
        except self._workflow_errors as exc:
            raise ApiError(403, ErrorCode.FORBIDDEN_ROLE, str(exc)) from exc
        except self._errors as exc:
            raise _map_error(exc) from exc

    def reject(
        self,
        *,
        procedure_id: str,
        actor: str,
        roles: set[str],
        reason: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        try:
            procedure = self._orchestrator.reject_procedure(
                procedure_id=procedure_id,
                actor=actor,
                actor_roles=roles,
                correlation_id=correlation_id,
            )
            return self._orchestrator._procedure_view(procedure)
        except self._workflow_errors as exc:
            raise ApiError(403, ErrorCode.FORBIDDEN_ROLE, str(exc)) from exc
        except self._errors as exc:
            raise _map_error(exc) from exc

    def approve(
        self,
        *,
        procedure_id: str,
        actor: str,
        roles: set[str],
        expected_version: int,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        try:
            procedure = self._orchestrator.approve_procedure(
                procedure_id=procedure_id,
                actor=actor,
                actor_roles=roles,
                expected_version=expected_version,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
            )
            return self._orchestrator._procedure_view(procedure)
        except self._errors as exc:
            raise _map_error(exc) from exc

    def audit_records(self) -> list[dict[str, Any]]:
        return self._orchestrator.get_audit()

    def get_procedure(self, procedure_id: str) -> dict[str, Any]:
        try:
            procedure = self._orchestrator.get_procedure(procedure_id)
            return self._orchestrator._procedure_view(procedure)
        except self._errors as exc:
            raise _map_error(exc) from exc

    def seed_demo_batch(self) -> dict[str, Any]:
        """Seed a batch of realistic sample entries in assorted states."""
        seeded: list[dict[str, Any]] = []
        for entry in _DEMO_SEED_CORPUS:
            sid = self._create_and_draft(entry)
            view = self._orchestrator._procedure_view(self._orchestrator.get_procedure(sid))
            target = entry.get("target_status", "DRAFT")
            if target in ("IN_REVIEW", "APPROVED", "REJECTED"):
                self._orchestrator.submit_for_review(sid, actor="ke-demo-seed")
                view = self._orchestrator._procedure_view(self._orchestrator.get_procedure(sid))
            if target == "APPROVED":
                proc = self._orchestrator.get_procedure(sid)
                self._orchestrator.approve_procedure(
                    procedure_id=sid,
                    actor="ke-demo-seed",
                    actor_roles={"Knowledge.Publisher"},
                    expected_version=proc.version,
                    idempotency_key=f"seed-{sid}",
                    correlation_id="seed-demo-batch",
                )
                view = self._orchestrator._procedure_view(self._orchestrator.get_procedure(sid))
            if target == "REJECTED":
                self._orchestrator.reject_procedure(
                    procedure_id=sid,
                    actor="ke-demo-seed",
                    actor_roles={"Knowledge.Publisher"},
                    correlation_id="seed-demo-batch",
                )
                view = self._orchestrator._procedure_view(self._orchestrator.get_procedure(sid))
            seeded.append(view)
        return {"seeded": len(seeded), "procedures": seeded}

    def reset_demo(self) -> dict[str, Any]:
        """Reset the knowledge store to just the initial seed procedures."""
        self._orchestrator._repos.procedures.clear()
        self._orchestrator._repos.consents.clear()
        self._orchestrator._repos.transcripts.clear()
        self._orchestrator._repos.idempotency.clear()
        if hasattr(self._orchestrator.audit, '_records'):
            self._orchestrator.audit._records.clear()
        self._seed_demo_procedures()
        count = len(self._orchestrator._repos.procedures)
        return {"reset": True, "procedureCount": count}

    def _create_and_draft(self, entry: dict[str, Any]) -> str:
        """Create an interview + draft from a seed entry definition."""
        interview = self._orchestrator.create_interview(
            operator_ref=entry.get("author", "ke-demo-seed"),
            language="en",
            retention_days=30,
            consent_granted=True,
            correlation_id=f"seed-{entry['title'][:20]}",
        )
        session_id = interview["sessionId"]
        self._submit_fixture_audio(session_id, "en", f"seed-{entry['title'][:20]}")
        draft = self._orchestrator.extract_draft(
            session_id=session_id,
            title=entry["title"],
            correlation_id=f"seed-{entry['title'][:20]}",
        )
        return draft.procedure_id

    def _seed_demo_procedures(self) -> None:
        """Seed one in-review and one approved synthetic-only procedure."""
        first = self._orchestrator.create_interview(
            operator_ref="OP-DEMO-014",
            language="en",
            retention_days=30,
            consent_granted=True,
            correlation_id="seed-knowledge-review",
        )
        self._submit_fixture_audio(first["sessionId"], "en", "seed-knowledge-review")
        draft = self._orchestrator.extract_draft(
            session_id=first["sessionId"],
            title="Hearth sector over-temperature verification",
            correlation_id="seed-knowledge-review",
        )
        self._orchestrator.submit_for_review(draft.procedure_id, actor="ke-demo")

        second = self._orchestrator.create_interview(
            operator_ref="OP-DEMO-015",
            language="en",
            retention_days=30,
            consent_granted=True,
            correlation_id="seed-knowledge-approved",
        )
        self._submit_fixture_audio(second["sessionId"], "en", "seed-knowledge-approved")
        approved_draft = self._orchestrator.extract_draft(
            session_id=second["sessionId"],
            title="Approved cooling-circuit inspection procedure",
            correlation_id="seed-knowledge-approved",
        )
        self._orchestrator.submit_for_review(approved_draft.procedure_id, actor="ke-demo")
        self._orchestrator.approve_procedure(
            procedure_id=approved_draft.procedure_id,
            actor="ke-demo",
            actor_roles={"Knowledge.Publisher"},
            expected_version=approved_draft.version,
            idempotency_key="seed-knowledge-approved-key",
            correlation_id="seed-knowledge-approved",
        )

    def _submit_fixture_audio(
        self, session_id: str, language: str, correlation_id: str
    ) -> None:
        meta = self._audio_metadata(
            session_id=session_id,
            content_type="audio/wav",
            duration_seconds=95.0,
            sample_rate_hz=16000,
            channels=1,
            size_bytes=3_000_000,
            language=language,
            speaker_role="operator",
            checksum="sha256:novasteel-synthetic-fixture",
        )
        self._orchestrator.submit_audio(
            session_id=session_id,
            meta=meta,
            audio_ref="synthetic-op-demo-014.wav",
            correlation_id=correlation_id,
        )


def _map_error(error: Exception) -> ApiError:
    name = type(error).__name__
    if name == "NotFoundError":
        return ApiError(404, ErrorCode.NOT_FOUND, "The requested knowledge resource was not found.")
    if name == "ForbiddenError":
        return ApiError(403, ErrorCode.FORBIDDEN_ROLE, "Knowledge workflow access was denied.")
    if name == "ConflictError":
        message = str(error)
        code = ErrorCode.STALE_APPROVAL if "expected version" in message else ErrorCode.VALIDATION_ERROR
        return ApiError(409 if code is ErrorCode.STALE_APPROVAL else 400, code, message)
    return ApiError(400, ErrorCode.VALIDATION_ERROR, "Knowledge workflow request is invalid.")


_DEMO_SEED_CORPUS: list[dict[str, Any]] = [
    {"title": "Blast furnace tuyere blockage detection", "author": "jean-dupont", "target_status": "APPROVED"},
    {"title": "Refractory lining ultrasound thickness measurement", "author": "karl-meyer", "target_status": "APPROVED"},
    {"title": "Hot metal desulfurization torpedo car procedure", "author": "pierre-martin", "target_status": "APPROVED"},
    {"title": "EAF electrode regulation and setpoint optimization", "author": "hans-schmidt", "target_status": "APPROVED"},
    {"title": "Ladle furnace slag foaming control", "author": "sophie-lambert", "target_status": "APPROVED"},
    {"title": "Continuous caster mold level oscillation monitoring", "author": "marco-rossi", "target_status": "APPROVED"},
    {"title": "Hot strip mill coilbox temperature uniformity check", "author": "jean-dupont", "target_status": "APPROVED"},
    {"title": "Cold rolling mill thickness gauge calibration", "author": "karl-meyer", "target_status": "APPROVED"},
    {"title": "Cooling water circuit differential pressure alarm response", "author": "pierre-martin", "target_status": "APPROVED"},
    {"title": "Gas cleaning electrostatic precipitator spark rate tuning", "author": "hans-schmidt", "target_status": "APPROVED"},
    {"title": "Overhead crane load-test and wire-rope inspection", "author": "sophie-lambert", "target_status": "IN_REVIEW"},
    {"title": "Energy load shedding protocol during grid frequency dip", "author": "marco-rossi", "target_status": "IN_REVIEW"},
    {"title": "Lockout/tagout verification for caster segment change", "author": "jean-dupont", "target_status": "IN_REVIEW"},
    {"title": "EU ETS continuous emission monitoring calibration", "author": "karl-meyer", "target_status": "IN_REVIEW"},
    {"title": "SPC control chart response for slab surface defects", "author": "pierre-martin", "target_status": "IN_REVIEW"},
    {"title": "Blast furnace gas holder pressure trip recovery", "author": "hans-schmidt", "target_status": "DRAFT"},
    {"title": "Refractory relining scheduling and heat-up curve", "author": "sophie-lambert", "target_status": "DRAFT"},
    {"title": "Tapping runner gunning material selection criteria", "author": "marco-rossi", "target_status": "DRAFT"},
    {"title": "EAF scrap bucket loading sequence and density check", "author": "jean-dupont", "target_status": "DRAFT"},
    {"title": "Ladle argon stirring plug maintenance window", "author": "karl-meyer", "target_status": "DRAFT"},
    {"title": "Secondary cooling zone nozzle clogging diagnostic", "author": "pierre-martin", "target_status": "REJECTED"},
    {"title": "Coke oven battery heating flue temperature survey", "author": "hans-schmidt", "target_status": "APPROVED"},
    {"title": "BOS vessel refractory wear profiling by laser scan", "author": "sophie-lambert", "target_status": "APPROVED"},
    {"title": "Rolling mill work-roll cambering and thermal crown", "author": "marco-rossi", "target_status": "IN_REVIEW"},
    {"title": "Sinter plant ignition hood burner alignment check", "author": "jean-dupont", "target_status": "APPROVED"},
]
