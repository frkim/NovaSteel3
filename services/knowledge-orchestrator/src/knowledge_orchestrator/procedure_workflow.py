"""Procedure draft -> review -> approved workflow (api-contracts §4.7, §10.2, §9.3).

An agent may only *create* a DRAFT. Status transitions require human roles; approval
requires the ``Knowledge.Publisher`` role, an optimistic-concurrency ``expectedVersion``
check (STALE_APPROVAL 409), and produces an immutable, version-bumped APPROVED record
that triggers a derived-index update. APPROVED/REJECTED are terminal.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Optional

from .models import (
    ExtractedKnowledge,
    Procedure,
    ProcedureStatus,
    utcnow,
)

PUBLISHER_ROLE = "Knowledge.Publisher"

# Allowed status transitions.
_ALLOWED: dict[ProcedureStatus, set[ProcedureStatus]] = {
    ProcedureStatus.DRAFT: {ProcedureStatus.IN_REVIEW, ProcedureStatus.REJECTED},
    ProcedureStatus.IN_REVIEW: {ProcedureStatus.APPROVED, ProcedureStatus.REJECTED},
    ProcedureStatus.APPROVED: set(),
    ProcedureStatus.REJECTED: set(),
}


class WorkflowError(Exception):
    """Raised for an illegal transition or a missing authorization role."""


class StaleApprovalError(Exception):
    """Raised (as 409 STALE_APPROVAL) when ``expected_version`` does not match."""


def create_draft(
    procedure_id: str,
    title: str,
    knowledge: ExtractedKnowledge,
    session_id: Optional[str],
    created_by: str,
) -> Procedure:
    """Create a new DRAFT procedure (the only status an agent may originate)."""
    return Procedure(
        procedure_id=procedure_id,
        title=title,
        status=ProcedureStatus.DRAFT,
        version=1,
        knowledge=knowledge,
        session_id=session_id,
        created_by=created_by,
    )


def submit_for_review(procedure: Procedure, actor: str) -> Procedure:
    """Transition DRAFT -> IN_REVIEW."""
    _check(procedure.status, ProcedureStatus.IN_REVIEW)
    return replace(
        procedure,
        status=ProcedureStatus.IN_REVIEW,
        updated_at=utcnow(),
    )


def approve(
    procedure: Procedure,
    actor: str,
    actor_roles: set[str],
    expected_version: int,
    now: Optional[datetime] = None,
) -> Procedure:
    """Transition IN_REVIEW -> APPROVED under the Knowledge.Publisher role.

    Enforces optimistic concurrency: ``expected_version`` must equal the current
    version or :class:`StaleApprovalError` is raised (never a silent overwrite).
    """
    if PUBLISHER_ROLE not in actor_roles:
        raise WorkflowError(
            f"approval requires role '{PUBLISHER_ROLE}'; actor lacks it"
        )
    _check(procedure.status, ProcedureStatus.APPROVED)
    if expected_version != procedure.version:
        raise StaleApprovalError(
            f"expected version {expected_version} but current is {procedure.version}"
        )
    now = now or utcnow()
    return replace(
        procedure,
        status=ProcedureStatus.APPROVED,
        version=procedure.version + 1,
        approved_by=actor,
        approved_at=now,
        updated_at=now,
    )


def reject(procedure: Procedure, actor: str, actor_roles: set[str]) -> Procedure:
    """Transition DRAFT/IN_REVIEW -> REJECTED (requires the publisher role)."""
    if PUBLISHER_ROLE not in actor_roles:
        raise WorkflowError(f"rejection requires role '{PUBLISHER_ROLE}'")
    _check(procedure.status, ProcedureStatus.REJECTED)
    return replace(procedure, status=ProcedureStatus.REJECTED, updated_at=utcnow())


def is_retrievable(procedure: Procedure) -> bool:
    """Only APPROVED procedures are ever reachable through general retrieval."""
    return procedure.status is ProcedureStatus.APPROVED


def _check(current: ProcedureStatus, target: ProcedureStatus) -> None:
    if target not in _ALLOWED.get(current, set()):
        raise WorkflowError(
            f"illegal procedure transition {current.value} -> {target.value}"
        )
