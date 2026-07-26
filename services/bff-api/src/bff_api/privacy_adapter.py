"""Adapter from the BFF boundary to the GDPR Art. 17 erasure domain.

Composes the knowledge orchestrator (interview transcripts, procedures, the
hash-chained audit log) and the Copilot conversation store into a single
``ErasureService`` so a data subject's right to erasure can be exercised
across every store that holds personal data.

The audit chain is never mutated: erasure hard-deletes from source stores,
pseudonymizes procedure attribution and *appends* an ``erasure.executed``
tombstone, so ``verify()`` holds before and after every execution.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .contracts import ErrorCode
from .errors import ApiError

_ROOT = Path(__file__).resolve().parents[4]
_KNOWLEDGE_SRC = _ROOT / "services" / "knowledge-orchestrator" / "src"


class PrivacyAdapter:
    """Exposes submit / preview / execute / list for erasure requests."""

    def __init__(self, *, knowledge: Any, copilot: Any, salt: str) -> None:
        if str(_KNOWLEDGE_SRC) not in sys.path:
            sys.path.insert(0, str(_KNOWLEDGE_SRC))
        try:
            from knowledge_orchestrator.erasure import (
                ErasureError,
                ErasureNotFoundError,
                ErasureService,
                ErasureStatus,
                SubjectType,
            )
        except ImportError as exc:  # pragma: no cover - repository integration failure
            raise RuntimeError("knowledge-orchestrator is required by the BFF.") from exc

        orchestrator = knowledge.orchestrator
        self._service = ErasureService(
            audit_log=orchestrator.audit,
            session_store=orchestrator,
            procedure_store=orchestrator,
            copilot_store=copilot.conversation_store,
            salt_fn=lambda: salt,
        )
        self._not_found = ErasureNotFoundError
        self._error = ErasureError
        self._subject_type = SubjectType
        self._status = ErasureStatus

    # -- commands -----------------------------------------------------------

    def submit(
        self,
        *,
        subject_type: str,
        subject_id: str,
        requested_by: str,
        reason: str,
    ) -> dict[str, Any]:
        try:
            request = self._service.submit(
                subject_type=self._coerce_subject_type(subject_type),
                subject_id=subject_id,
                requested_by=requested_by,
                reason=reason,
            )
        except self._error as exc:
            raise ApiError(422, ErrorCode.VALIDATION_ERROR, str(exc)) from exc
        return self._request_view(request)

    def execute(self, request_id: str) -> dict[str, Any]:
        try:
            receipt = self._service.execute(request_id)
        except self._not_found as exc:
            raise ApiError(404, ErrorCode.NOT_FOUND, str(exc)) from exc
        except self._error as exc:
            raise ApiError(409, ErrorCode.ERASURE_STATE_CONFLICT, str(exc)) from exc
        return self._receipt_view(receipt)

    # -- queries ------------------------------------------------------------

    def preview(self, request_id: str) -> dict[str, Any]:
        try:
            return self._request_view(self._service.preview(request_id))
        except self._not_found as exc:
            raise ApiError(404, ErrorCode.NOT_FOUND, str(exc)) from exc

    def list_requests(
        self, *, subject_id: str | None = None, status: str | None = None
    ) -> dict[str, Any]:
        parsed_status = None
        if status:
            try:
                parsed_status = self._status(status.upper())
            except ValueError as exc:
                raise ApiError(
                    400, ErrorCode.VALIDATION_ERROR, f"unknown status '{status}'"
                ) from exc
        items = self._service.list_requests(subject_id=subject_id, status=parsed_status)
        return {
            "items": [self._request_view(item) for item in items],
            "total": len(items),
        }

    # -- helpers ------------------------------------------------------------

    def _coerce_subject_type(self, value: str) -> Any:
        try:
            return self._subject_type((value or "").upper())
        except ValueError as exc:
            raise ApiError(
                400,
                ErrorCode.VALIDATION_ERROR,
                f"unknown subjectType '{value}'",
            ) from exc

    def _request_view(self, request: Any) -> dict[str, Any]:
        """Never echoes ``subjectId`` — the raw identifier stays server-side."""
        return {
            "requestId": request.requestId,
            "subjectType": request.subjectType.value,
            "requestedBy": request.requestedBy,
            "reason": request.reason,
            "status": request.status.value,
            "createdAt": request.createdAt,
            "completedAt": request.completedAt,
            "targets": [self._target_view(t) for t in request.targets],
            "receiptHash": request.receiptHash,
        }

    def _receipt_view(self, receipt: Any) -> dict[str, Any]:
        return {
            "requestId": receipt.requestId,
            "subjectPseudonym": receipt.subjectId,
            "status": receipt.status.value,
            "executedAt": receipt.executedAt,
            "targets": [self._target_view(t) for t in receipt.targets],
            "erasedCounts": dict(receipt.erasedCounts),
            "retainedCounts": dict(receipt.retainedCounts),
            "auditChainRef": receipt.auditChainRef,
            "chainVerifiedAfter": receipt.chainVerifiedAfter,
        }

    @staticmethod
    def _target_view(target: Any) -> dict[str, Any]:
        return {
            "store": target.store,
            "recordCount": target.recordCount,
            "action": target.action,
            "legalBasis": target.legalBasis,
            "completed": target.completed,
        }


__all__ = ["PrivacyAdapter"]
