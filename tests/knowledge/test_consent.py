from datetime import timedelta

import pytest

from knowledge_orchestrator import consent as c
from knowledge_orchestrator.models import ConsentState, utcnow


def _session(**overrides):
    kwargs = dict(
        session_id="IV-1",
        operator_ref="OP-1",
        language="en",
        speaker_role="operator",
        retention_days=30,
    )
    kwargs.update(overrides)
    return c.create_session(**kwargs)


def test_create_requires_capture_scope():
    with pytest.raises(c.ConsentError):
        _session(scope="performance-monitoring")


def test_create_requires_positive_retention():
    with pytest.raises(c.ConsentError):
        _session(retention_days=0)


def test_grant_sets_deadline_and_allows_capture():
    rec = c.grant(_session())
    assert rec.state is ConsentState.GRANTED
    assert rec.retention_deadline is not None
    assert c.is_capture_allowed(rec) is True


def test_pending_and_denied_block_capture():
    rec = _session()
    assert c.is_capture_allowed(rec) is False
    denied = c.deny(rec)
    assert denied.state is ConsentState.DENIED
    assert c.is_capture_allowed(denied) is False


def test_illegal_transition_denied_to_granted():
    denied = c.deny(_session())
    with pytest.raises(c.ConsentError):
        c.grant(denied)


def test_withdraw_emits_deletion_directive():
    granted = c.grant(_session())
    updated, directive = c.withdraw(granted, "DEL-REQ-9")
    assert updated.state is ConsentState.WITHDRAWN
    assert directive.session_id == "IV-1"
    assert directive.deletion_request_ref == "DEL-REQ-9"
    assert c.is_capture_allowed(updated) is False


def test_expired_after_retention_deadline():
    granted = c.grant(_session(), now=utcnow() - timedelta(days=40))
    assert c.is_capture_allowed(granted) is False  # deadline already passed
    expired = c.expire(granted)
    assert expired.state is ConsentState.EXPIRED


def test_require_capture_allowed_raises_when_not_granted():
    with pytest.raises(c.ConsentError):
        c.require_capture_allowed(_session())


def test_terminal_states():
    assert c.is_terminal(ConsentState.WITHDRAWN)
    assert c.is_terminal(ConsentState.DENIED)
    assert c.is_terminal(ConsentState.EXPIRED)
    assert not c.is_terminal(ConsentState.GRANTED)
