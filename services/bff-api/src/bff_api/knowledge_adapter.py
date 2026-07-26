"""Adapter from the BFF boundary to the completed knowledge orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .contracts import ErrorCode
from .errors import ApiError


_ROOT = Path(__file__).resolve().parents[4]
_KNOWLEDGE_SRC = _ROOT / "services" / "knowledge-orchestrator" / "src"


class KnowledgeAdapter:
    """Delegates the consent/review workflow without reimplementing its internals."""

    def __init__(self, *, demo_mode: bool) -> None:
        if str(_KNOWLEDGE_SRC) not in sys.path:
            sys.path.insert(0, str(_KNOWLEDGE_SRC))
        try:
            from knowledge_orchestrator import KnowledgeOrchestrator
            from knowledge_orchestrator.models import AudioMetadata
            from knowledge_orchestrator.orchestrator import (
                ConflictError,
                ForbiddenError,
                NotFoundError,
            )
        except ImportError as exc:  # pragma: no cover - repository integration failure
            raise RuntimeError("knowledge-orchestrator is required by the BFF.") from exc
        self._orchestrator = KnowledgeOrchestrator()
        self._audio_metadata = AudioMetadata
        self._errors = (NotFoundError, ForbiddenError, ConflictError)
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
