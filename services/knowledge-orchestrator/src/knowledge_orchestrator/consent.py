"""Consent state machine (security-governance-and-threat-model.md §13).

Consent is captured before recording, is scoped strictly to ``knowledge-capture``
(never surveillance/performance monitoring), carries a retention deadline, and can
be withdrawn — withdrawal propagates a raw-audio deletion directive (GDPR Art. 17).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from .models import CONSENT_SCOPE, ConsentRecord, ConsentState, utcnow


class ConsentError(Exception):
    """Raised for an illegal consent transition or a disallowed consent scope."""


# Allowed transitions for the consent lifecycle. Terminal states have no successors.
_ALLOWED: dict[ConsentState, set[ConsentState]] = {
    ConsentState.PENDING: {ConsentState.GRANTED, ConsentState.DENIED},
    ConsentState.GRANTED: {ConsentState.WITHDRAWN, ConsentState.EXPIRED},
    ConsentState.DENIED: set(),
    ConsentState.WITHDRAWN: set(),
    ConsentState.EXPIRED: set(),
}

_TERMINAL = {ConsentState.DENIED, ConsentState.WITHDRAWN, ConsentState.EXPIRED}


@dataclass(frozen=True)
class DeletionDirective:
    """Instruction to erase raw audio for a session when consent is withdrawn."""

    session_id: str
    reason: str
    deletion_request_ref: str


def create_session(
    session_id: str,
    operator_ref: str,
    language: str,
    speaker_role: str,
    retention_days: int,
    scope: str = CONSENT_SCOPE,
) -> ConsentRecord:
    """Create a PENDING consent record for a new interview session.

    ``scope`` must equal ``knowledge-capture``; any other scope is rejected so the
    system can never be silently repurposed for surveillance (security §13).
    """
    _require_capture_scope(scope)
    if retention_days <= 0:
        raise ConsentError("retention_days must be a positive number of days")
    return ConsentRecord(
        session_id=session_id,
        operator_ref=operator_ref,
        scope=scope,
        state=ConsentState.PENDING,
        granted_at=None,
        retention_days=retention_days,
        retention_deadline=None,
        language=language,
        speaker_role=speaker_role,
    )


def grant(record: ConsentRecord, now: Optional[datetime] = None) -> ConsentRecord:
    """Transition PENDING -> GRANTED and stamp the retention deadline."""
    _require_capture_scope(record.scope)
    _check(record.state, ConsentState.GRANTED)
    now = now or utcnow()
    deadline = now + timedelta(days=record.retention_days)
    return record.with_state(
        ConsentState.GRANTED, granted_at=now, retention_deadline=deadline
    )


def deny(record: ConsentRecord) -> ConsentRecord:
    """Transition PENDING -> DENIED (operator declined to be recorded)."""
    _check(record.state, ConsentState.DENIED)
    return record.with_state(ConsentState.DENIED)


def withdraw(record: ConsentRecord, deletion_request_ref: str) -> tuple[ConsentRecord, DeletionDirective]:
    """Transition GRANTED -> WITHDRAWN and emit a raw-audio deletion directive."""
    _check(record.state, ConsentState.WITHDRAWN)
    updated = record.with_state(
        ConsentState.WITHDRAWN, deletion_request_ref=deletion_request_ref
    )
    directive = DeletionDirective(
        session_id=record.session_id,
        reason="consent-withdrawn",
        deletion_request_ref=deletion_request_ref,
    )
    return updated, directive


def expire(record: ConsentRecord) -> ConsentRecord:
    """Transition GRANTED -> EXPIRED when the retention deadline has passed."""
    _check(record.state, ConsentState.EXPIRED)
    return record.with_state(ConsentState.EXPIRED)


def is_capture_allowed(record: ConsentRecord, now: Optional[datetime] = None) -> bool:
    """Return True only when audio capture/submission is currently permitted."""
    if record.state is not ConsentState.GRANTED:
        return False
    if record.retention_deadline is None:
        return False
    now = now or utcnow()
    return now <= record.retention_deadline


def require_capture_allowed(record: ConsentRecord, now: Optional[datetime] = None) -> None:
    """Raise ConsentError unless capture is currently permitted for this session."""
    if not is_capture_allowed(record, now):
        raise ConsentError(
            f"audio capture not permitted for session {record.session_id} "
            f"in consent state {record.state.value}"
        )


def is_terminal(state: ConsentState) -> bool:
    return state in _TERMINAL


def _check(current: ConsentState, target: ConsentState) -> None:
    if target not in _ALLOWED.get(current, set()):
        raise ConsentError(
            f"illegal consent transition {current.value} -> {target.value}"
        )


def _require_capture_scope(scope: str) -> None:
    if scope != CONSENT_SCOPE:
        raise ConsentError(
            f"consent scope must be '{CONSENT_SCOPE}', refusing scope '{scope}'"
        )
