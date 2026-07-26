"""Optional FastAPI wiring for the knowledge-orchestrator (BFF-compatible routes).

This module is imported only when FastAPI is available (resolved from the approved
feed). The core service in ``orchestrator.py`` is transport-agnostic and does not
depend on FastAPI, so tests and the offline demo never require it. Routes mirror the
``/v1/knowledge/*`` contracts in api-contracts.md §4.7/§10.
"""

from __future__ import annotations

from typing import Optional

try:  # pragma: no cover - exercised only when FastAPI is installed
    from fastapi import Body, FastAPI, HTTPException, Query
except ImportError:  # pragma: no cover
    FastAPI = None  # type: ignore


from .orchestrator import (
    ConflictError,
    ForbiddenError,
    KnowledgeOrchestrator,
    NotFoundError,
    OrchestratorError,
)

_STATUS = {
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "FORBIDDEN": 403,
    "ORCHESTRATOR_ERROR": 400,
}


def create_app(orchestrator: Optional[KnowledgeOrchestrator] = None):  # pragma: no cover
    """Build a FastAPI app exposing the knowledge-orchestrator routes."""
    if FastAPI is None:
        raise RuntimeError(
            "FastAPI is not installed; resolve it from the approved feed to serve HTTP"
        )

    orch = orchestrator or KnowledgeOrchestrator()
    app = FastAPI(title="NovaSteel knowledge-orchestrator", version="1.0")

    def _guard(fn):
        try:
            return fn()
        except OrchestratorError as exc:
            raise HTTPException(status_code=_STATUS.get(exc.code, 400), detail=str(exc))

    @app.post("/v1/knowledge/interviews")
    def create_interview(body: dict = Body(...)):
        consent = body.get("consent", {})
        return _guard(
            lambda: orch.create_interview(
                operator_ref=body["operatorRef"],
                language=body.get("language", "en"),
                retention_days=consent.get("retentionDays", 30),
                consent_granted=consent.get("granted", False),
                scope=consent.get("scope", "knowledge-capture"),
            )
        )

    @app.get("/v1/knowledge/interviews/{session_id}/transcript")
    def get_transcript(session_id: str):
        return _guard(lambda: orch.get_transcript(session_id))

    @app.get("/v1/knowledge/procedures")
    def list_procedures(
        status: Optional[str] = None,
        q: Optional[str] = None,
        page: int = Query(1, ge=1),
        size: int = Query(50, ge=1, le=200),
    ):
        return _guard(lambda: orch.list_procedures(status=status, q=q, page=page, size=size))

    @app.get("/v1/knowledge/search")
    def search(q: str = ""):
        return _guard(lambda: orch.search_procedures(q))

    @app.post("/v1/knowledge/procedures/{procedure_id}:approve")
    def approve(procedure_id: str, body: dict = Body(...), idempotency_key: str = ""):
        return _guard(
            lambda: orch._procedure_view(
                orch.approve_procedure(
                    procedure_id=procedure_id,
                    actor=body["actor"],
                    actor_roles=set(body.get("roles", [])),
                    expected_version=body["expectedVersion"],
                    idempotency_key=idempotency_key or body.get("idempotencyKey", ""),
                )
            )
        )

    @app.get("/v1/audit/decisions")
    def audit(domain: str = "knowledge", entityId: Optional[str] = None):
        return _guard(lambda: orch.get_audit(domain=domain, entity_id=entityId))

    return app
