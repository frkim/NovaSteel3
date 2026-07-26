"""Tests for the GDPR Art. 17 erasure service (services/…/erasure.py).

The single most important property proved here is in ``test_audit_chain_verifies_before_and_after_execute``:
the append-only, hash-chained audit log passes ``AuditLog.verify()`` both *before*
and *after* erasure, because existing records are never modified — only a new
``erasure.executed`` tombstone record is appended.

All 40 tests use the real ``AuditLog`` (from audit.py) for chain-integrity assertions
and lightweight in-memory fakes for the three injectable store protocols.

Run with:
    cd 'D:\\work\\20260724 - Novasteel 3'
    $env:PYTHONIOENCODING='utf-8'
    services\\bff-api\\.venv\\Scripts\\python.exe -m pytest tests\\knowledge\\test_erasure.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import pytest

# ---------------------------------------------------------------------------
# Path bootstrap (mirrors conftest.py)
# ---------------------------------------------------------------------------
_SERVICE = Path(__file__).resolve().parents[2] / "services" / "knowledge-orchestrator"
_SRC = _SERVICE / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from knowledge_orchestrator.audit import AuditLog
from knowledge_orchestrator.erasure import (
    ErasureError,
    ErasureNotFoundError,
    ErasureReceipt,
    ErasureRequest,
    ErasureService,
    ErasureStatus,
    ErasureTarget,
    IllegalTransitionError,
    SubjectType,
    _pseudonymize,
)

# ---------------------------------------------------------------------------
# In-memory test doubles
# ---------------------------------------------------------------------------


class _FakeSessionStore:
    """In-process session + transcript store implementing InterviewSessionStoreProtocol."""

    def __init__(self) -> None:
        self._sessions: dict[str, str] = {}       # session_id -> owner
        self._transcripts: dict[str, str] = {}    # session_id -> transcript text

    def add_session(
        self, session_id: str, owner: str, transcript: str = ""
    ) -> None:
        self._sessions[session_id] = owner
        if transcript:
            self._transcripts[session_id] = transcript

    def get_transcript(self, session_id: str) -> Optional[str]:
        return self._transcripts.get(session_id)

    # --- Protocol methods ---

    def scan_subject_sessions(self, subject_id: str) -> list[str]:
        return [sid for sid, owner in self._sessions.items() if owner == subject_id]

    def erase_session_transcripts(self, session_ids: list[str]) -> int:
        count = 0
        for sid in session_ids:
            if self._transcripts.pop(sid, None) is not None:
                count += 1
        return count


class _FakeProcedureStore:
    """In-process procedure store implementing ProcedureStoreProtocol."""

    def __init__(self) -> None:
        # proc_id -> {"created_by": str, "body": str}
        self._procs: dict[str, dict[str, str]] = {}

    def add_procedure(
        self, proc_id: str, created_by: str, body: str = "operational safety content"
    ) -> None:
        self._procs[proc_id] = {"created_by": created_by, "body": body}

    def get_created_by(self, proc_id: str) -> Optional[str]:
        p = self._procs.get(proc_id)
        return p["created_by"] if p else None

    def get_body(self, proc_id: str) -> Optional[str]:
        p = self._procs.get(proc_id)
        return p["body"] if p else None

    # --- Protocol methods ---

    def scan_subject_procedures(self, subject_id: str) -> list[str]:
        return [
            pid for pid, p in self._procs.items() if p["created_by"] == subject_id
        ]

    def pseudonymize_procedures(self, procedure_ids: list[str], pseudo_id: str) -> int:
        count = 0
        for pid in procedure_ids:
            if pid in self._procs:
                self._procs[pid]["created_by"] = pseudo_id
                count += 1
        return count


class _FakeCopilotStore:
    """In-process Copilot conversation store implementing CopilotStoreProtocol."""

    def __init__(self) -> None:
        # owner -> list of conversation-content strings
        self._convs: dict[str, list[str]] = {}

    def add_conversations(self, owner: str, *contents: str) -> None:
        self._convs.setdefault(owner, []).extend(contents)

    def get_all(self, owner: str) -> list[str]:
        return list(self._convs.get(owner, []))

    # --- Protocol methods ---

    def count_subject_conversations(self, owner_id: str) -> int:
        return len(self._convs.get(owner_id, []))

    def erase_subject_conversations(self, owner_id: str) -> int:
        convs = self._convs.pop(owner_id, [])
        return len(convs)


# ---------------------------------------------------------------------------
# Factory helper
# ---------------------------------------------------------------------------


def _make_service(
    *,
    audit_log: Optional[AuditLog] = None,
    sessions: Optional[_FakeSessionStore] = None,
    procedures: Optional[_FakeProcedureStore] = None,
    copilot: Optional[_FakeCopilotStore] = None,
    salt: str = "test-salt-fixed",
    legal_hold_fn=None,
    target_hold_fn=None,
) -> ErasureService:
    return ErasureService(
        audit_log=audit_log if audit_log is not None else AuditLog(),
        session_store=sessions if sessions is not None else _FakeSessionStore(),
        procedure_store=procedures if procedures is not None else _FakeProcedureStore(),
        copilot_store=copilot if copilot is not None else _FakeCopilotStore(),
        salt_fn=lambda: salt,
        legal_hold_fn=legal_hold_fn if legal_hold_fn is not None else (lambda _: False),
        target_hold_fn=target_hold_fn
        if target_hold_fn is not None
        else (lambda _s, _t: False),
    )


def _submit_and_execute(svc: ErasureService, subject_id: str = "alice") -> ErasureReceipt:
    req = svc.submit(SubjectType.INTERVIEW_PARTICIPANT, subject_id, "admin", "GDPR Art. 17")
    return svc.execute(req.requestId)


# ===========================================================================
# 1. HEADLINE — chain integrity before AND after execute
# ===========================================================================


def test_audit_chain_verifies_before_and_after_execute():
    """HEADLINE: audit.verify() is True before and after a complete erasure execution.

    This is the proof that crypto-shredding + tombstoning does not corrupt the chain.
    We pre-populate real audit records (simulating interview lifecycle events) and
    assert that verify() passes at every stage: before submit, after submit, and
    after execute().
    """
    audit = AuditLog()
    sessions = _FakeSessionStore()
    sessions.add_session("IV-001", "alice", "voice transcript text")

    # Pre-existing audit records (e.g. from interview lifecycle)
    audit.append(
        correlation_id="IV-001",
        domain="knowledge",
        action="interview.create",
        entity_id="IV-001",
        actor="alice",
        inputs={"scope": "knowledge-capture"},
        output={"consentState": "GRANTED"},
    )
    audit.append(
        correlation_id="IV-001",
        domain="knowledge",
        action="interview.transcribe",
        entity_id="IV-001",
        actor="mi-ns-knowledge",
        inputs={"language": "en", "audio": "ref.wav"},
        output={"status": "COMPLETED", "segments": 3},
    )

    assert audit.verify() is True, "chain must verify before any erasure"
    chain_len_before = len(audit)

    svc = _make_service(audit_log=audit, sessions=sessions)
    req = svc.submit(SubjectType.INTERVIEW_PARTICIPANT, "alice", "admin", "GDPR Art. 17")

    assert audit.verify() is True, "chain must verify after erasure.requested appended"

    receipt = svc.execute(req.requestId)

    assert audit.verify() is True, "chain MUST verify after erasure.executed appended"
    assert len(audit) > chain_len_before, "chain must have grown (tombstone appended)"
    assert receipt.chainVerifiedAfter is True, "receipt must confirm chain verification"


# ===========================================================================
# 2. Tombstoned payload is unrecoverable
# ===========================================================================


def test_tombstoned_payload_is_unrecoverable_from_all_stores():
    """Personal transcript text is irrecoverable after execute() from every store.

    The session store is hard-deleted.  The audit chain never held the raw text
    (audit._redact() strips 'transcript'/'audio' keys), so it cannot be recovered
    from there either.
    """
    personal_text = "Operator Alice: furnace temperature must reach 1 450 °C before tapping"
    sessions = _FakeSessionStore()
    sessions.add_session("IV-001", "alice", personal_text)

    audit = AuditLog()
    # Simulate a pre-existing audit record that mentions the session but NOT the text
    audit.append(
        correlation_id="IV-001",
        domain="knowledge",
        action="interview.transcribe",
        entity_id="IV-001",
        actor="alice",
        inputs={"language": "en", "audio": "ref.wav"},   # "audio" is redacted
        output={"transcript": personal_text},             # "transcript" is redacted
    )

    svc = _make_service(audit_log=audit, sessions=sessions)
    req = svc.submit(SubjectType.INTERVIEW_PARTICIPANT, "alice", "admin", "GDPR Art. 17")
    svc.execute(req.requestId)

    # Transcript gone from session store
    assert sessions.get_transcript("IV-001") is None, "transcript must be deleted"

    # Personal text must not appear anywhere in the audit chain
    chain_dump = " ".join(
        json.dumps(
            {
                "entity_id": r.entity_id,
                "actor": r.actor,
                "inputs": r.inputs,
                "output": r.output,
            }
        )
        for r in audit.query()
    )
    assert personal_text not in chain_dump, "personal text must not survive in audit chain"

    # Chain must still verify
    assert audit.verify() is True


# ===========================================================================
# 3 & 4. Chain length grows
# ===========================================================================


def test_audit_chain_length_grows_after_submit():
    """submit() appends exactly one erasure.requested record to the chain."""
    audit = AuditLog()
    svc = _make_service(audit_log=audit)
    before = len(audit)
    svc.submit(SubjectType.OPERATOR, "bob", "admin", "test")
    assert len(audit) == before + 1


def test_audit_chain_length_grows_after_execute():
    """execute() appends exactly one erasure.executed record (the tombstone)."""
    audit = AuditLog()
    svc = _make_service(audit_log=audit)
    before = len(audit)
    req = svc.submit(SubjectType.OPERATOR, "bob", "admin", "test")
    after_submit = len(audit)
    svc.execute(req.requestId)
    assert len(audit) == after_submit + 1, "execute() must append exactly one record"
    assert len(audit) > before


def test_audit_records_never_removed_only_appended():
    """The chain is append-only: records present before erasure remain afterward."""
    audit = AuditLog()
    audit.append(
        correlation_id="c1",
        domain="knowledge",
        action="draft.create",
        entity_id="PROC-1",
        actor="alice",
        output={"status": "DRAFT"},
    )
    ids_before = {r.record_hash for r in audit.query()}
    svc = _make_service(audit_log=audit)
    _submit_and_execute(svc, "alice")
    ids_after = {r.record_hash for r in audit.query()}
    assert ids_before.issubset(ids_after), "all pre-erasure records must still be present"


# ===========================================================================
# 5. Full happy path
# ===========================================================================


def test_full_happy_path_submit_preview_execute_gives_correct_counts():
    """submit → preview → execute produces a receipt with correct erasedCounts/retainedCounts."""
    sessions = _FakeProcedureStore.__new__(_FakeProcedureStore)  # avoid confusion
    sessions = _FakeSessionStore()
    sessions.add_session("IV-001", "alice", "transcript A")
    sessions.add_session("IV-002", "alice", "transcript B")

    procs = _FakeProcedureStore()
    procs.add_procedure("PROC-IV-001", "alice", "check hearth temperature")

    copilot = _FakeCopilotStore()
    copilot.add_conversations("alice", "chat A", "chat B", "chat C")

    svc = _make_service(sessions=sessions, procedures=procs, copilot=copilot)
    req = svc.submit(SubjectType.INTERVIEW_PARTICIPANT, "alice", "admin", "GDPR Art. 17")

    # Preview reflects the inventory without executing
    preview = svc.preview(req.requestId)
    assert preview.status == ErasureStatus.PENDING
    stores = {t.store for t in preview.targets}
    assert "interview-transcripts" in stores
    assert "knowledge-procedures" in stores
    assert "copilot-conversations" in stores

    receipt = svc.execute(req.requestId)

    assert receipt.status == ErasureStatus.COMPLETED
    assert receipt.erasedCounts["interview-transcripts"] == 2
    assert receipt.erasedCounts["knowledge-procedures"] == 1
    assert receipt.erasedCounts["copilot-conversations"] == 3
    assert "audit-chain" in receipt.retainedCounts
    assert "telemetry-attribution" in receipt.retainedCounts


# ===========================================================================
# 6. Erased / retained counts
# ===========================================================================


def test_erased_counts_reflect_actual_deletions():
    sessions = _FakeSessionStore()
    sessions.add_session("IV-A", "carol", "text")
    svc = _make_service(sessions=sessions)
    receipt = _submit_and_execute(svc, "carol")
    assert receipt.erasedCounts.get("interview-transcripts") == 1
    assert receipt.erasedCounts.get("copilot-conversations") == 0


def test_retained_counts_include_audit_chain_and_telemetry():
    svc = _make_service()
    receipt = _submit_and_execute(svc)
    assert "audit-chain" in receipt.retainedCounts
    assert "telemetry-attribution" in receipt.retainedCounts


# ===========================================================================
# 7. Idempotency
# ===========================================================================


def test_idempotent_re_execute_returns_identical_receipt():
    """Calling execute() twice on a COMPLETED request returns the same receipt object."""
    svc = _make_service()
    req = svc.submit(SubjectType.OPERATOR, "dave", "admin", "test")
    receipt1 = svc.execute(req.requestId)
    receipt2 = svc.execute(req.requestId)
    assert receipt1 is receipt2, "idempotent execute must return the cached receipt"


def test_idempotent_re_execute_does_not_grow_audit_chain():
    """A second execute() on a COMPLETED request must NOT append another audit record."""
    audit = AuditLog()
    svc = _make_service(audit_log=audit)
    req = svc.submit(SubjectType.OPERATOR, "dave", "admin", "test")
    svc.execute(req.requestId)
    len_after_first = len(audit)
    svc.execute(req.requestId)
    assert len(audit) == len_after_first, "idempotent re-execute must not grow the chain"


def test_idempotent_re_execute_does_not_delete_already_erased_data():
    """A second execute() must not fail even though transcripts are already gone."""
    sessions = _FakeSessionStore()
    sessions.add_session("IV-001", "eve", "data")
    svc = _make_service(sessions=sessions)
    req = svc.submit(SubjectType.INTERVIEW_PARTICIPANT, "eve", "admin", "test")
    svc.execute(req.requestId)
    # Second execute — must not raise and must return same receipt
    receipt = svc.execute(req.requestId)
    assert receipt.status == ErasureStatus.COMPLETED


# ===========================================================================
# 8 & 9. Legal hold
# ===========================================================================


def test_legal_hold_rejects_request_at_submit_time():
    """If the subject is under a global legal hold, submit() raises ErasureError immediately."""
    svc = _make_service(legal_hold_fn=lambda _: True)
    with pytest.raises(ErasureError):
        svc.submit(SubjectType.OPERATOR, "frank", "admin", "GDPR Art. 17")


def test_legal_hold_rejected_request_is_stored_with_rejected_status():
    """The REJECTED request is saved so auditors can see what was attempted."""
    svc = _make_service(legal_hold_fn=lambda _: True)
    with pytest.raises(ErasureError) as exc_info:
        svc.submit(SubjectType.OPERATOR, "frank", "admin", "GDPR Art. 17")
    # Extract request_id from error message
    msg = str(exc_info.value)
    # The request should be findable in the service's internal store
    requests = svc.list_requests(subject_id="frank", status=ErasureStatus.REJECTED)
    assert len(requests) == 1
    assert requests[0].status == ErasureStatus.REJECTED


def test_legal_hold_appends_audit_record_on_rejection():
    """An erasure.rejected audit record is appended even for a REJECTED request."""
    audit = AuditLog()
    svc = _make_service(audit_log=audit, legal_hold_fn=lambda _: True)
    with pytest.raises(ErasureError):
        svc.submit(SubjectType.OPERATOR, "frank", "admin", "test")
    records = audit.query(domain="erasure")
    assert any(r.action == "erasure.rejected" for r in records)
    assert audit.verify() is True


def test_per_target_hold_yields_partially_completed():
    """When a specific store is under legal hold, status becomes PARTIALLY_COMPLETED."""
    sessions = _FakeSessionStore()
    sessions.add_session("IV-001", "grace", "transcript")

    # Only interview-transcripts is held; others proceed normally
    def held(subject_id: str, store: str) -> bool:
        return store == "interview-transcripts"

    svc = _make_service(sessions=sessions, target_hold_fn=held)
    req = svc.submit(SubjectType.INTERVIEW_PARTICIPANT, "grace", "admin", "GDPR")
    receipt = svc.execute(req.requestId)

    assert receipt.status == ErasureStatus.PARTIALLY_COMPLETED
    held_target = next(
        t for t in receipt.targets if t.store == "interview-transcripts"
    )
    assert held_target.completed is False
    assert held_target.action == "retain-legal-basis"
    # Transcript was NOT deleted because the store was held
    assert sessions.get_transcript("IV-001") == "transcript"


# ===========================================================================
# 10 & 11. Procedures
# ===========================================================================


def test_procedures_are_pseudonymized_not_deleted():
    """The procedure store must still contain the procedure after erasure (body retained)."""
    procs = _FakeProcedureStore()
    procs.add_procedure("PROC-001", "henry", "check hearth lining thickness")
    svc = _make_service(procedures=procs)
    _submit_and_execute(svc, "henry")
    # Procedure still exists
    assert procs.get_body("PROC-001") is not None


def test_procedure_body_survives_erasure_unchanged():
    """The operational body text must be identical before and after erasure."""
    body = "Inspect refractory brick thickness; replace if < 15 cm."
    procs = _FakeProcedureStore()
    procs.add_procedure("PROC-001", "ivan", body)
    svc = _make_service(procedures=procs)
    _submit_and_execute(svc, "ivan")
    assert procs.get_body("PROC-001") == body


def test_procedure_attribution_replaced_with_pseudonym_not_raw_id():
    """After erasure the created_by field must be the pseudonym, not the raw subject id."""
    subject_id = "julia-operator"
    procs = _FakeProcedureStore()
    procs.add_procedure("PROC-001", subject_id, "check tapping temperature")
    svc = _make_service(procedures=procs, salt="fixed-salt-for-test")
    _submit_and_execute(svc, subject_id)
    new_created_by = procs.get_created_by("PROC-001")
    assert new_created_by != subject_id, "raw subject id must be replaced"
    assert subject_id not in (new_created_by or ""), "raw id must not appear in pseudonym"


def test_procedure_target_action_is_pseudonymize():
    """The target for knowledge-procedures must specify 'pseudonymize' action."""
    procs = _FakeProcedureStore()
    procs.add_procedure("PROC-001", "karl", "safety boundary text")
    svc = _make_service(procedures=procs)
    req = svc.submit(SubjectType.INTERVIEW_PARTICIPANT, "karl", "admin", "GDPR")
    target = next(t for t in req.targets if t.store == "knowledge-procedures")
    assert target.action == "pseudonymize"
    assert target.legalBasis is not None and "Art. 17(3)" in target.legalBasis


# ===========================================================================
# 12. Raw subjectId never leaks
# ===========================================================================


def test_raw_subject_id_not_in_receipt_subject_id_field():
    """receipt.subjectId must be the pseudonym, not the raw identifier."""
    subject_id = "leaking-operator-id-12345"
    svc = _make_service()
    receipt = _submit_and_execute(svc, subject_id)
    assert receipt.subjectId != subject_id
    assert subject_id not in receipt.subjectId


def test_raw_subject_id_not_in_receipt_repr():
    """repr(receipt) must not expose the raw subject id."""
    subject_id = "leaking-operator-id-12345"
    svc = _make_service()
    receipt = _submit_and_execute(svc, subject_id)
    assert subject_id not in repr(receipt)


def test_raw_subject_id_not_in_request_repr():
    """repr(ErasureRequest) must not expose the raw subject id."""
    subject_id = "sensitive-subject-id-99"
    svc = _make_service()
    req = svc.submit(SubjectType.OPERATOR, subject_id, "admin", "test")
    assert subject_id not in repr(req)


def test_raw_subject_id_not_in_audit_entity_id():
    """Audit records' entity_id fields must contain only the pseudonym."""
    subject_id = "sensitive-subject-id-99"
    audit = AuditLog()
    svc = _make_service(audit_log=audit)
    req = svc.submit(SubjectType.OPERATOR, subject_id, "admin", "test")
    svc.execute(req.requestId)
    for r in audit.query(domain="erasure"):
        assert subject_id not in r.entity_id, (
            f"entity_id={r.entity_id!r} must not contain raw subject_id"
        )


def test_raw_subject_id_not_in_audit_inputs_or_output():
    """Audit records' inputs/output dicts must not contain the raw subject id."""
    subject_id = "sensitive-subject-id-99"
    audit = AuditLog()
    svc = _make_service(audit_log=audit)
    req = svc.submit(SubjectType.OPERATOR, subject_id, "admin", "test")
    svc.execute(req.requestId)
    for r in audit.query(domain="erasure"):
        inputs_str = json.dumps(r.inputs)
        output_str = json.dumps(r.output)
        assert subject_id not in inputs_str, "raw id must not appear in audit inputs"
        assert subject_id not in output_str, "raw id must not appear in audit output"


# ===========================================================================
# 13. Pseudonymization properties
# ===========================================================================


def test_pseudonymization_is_deterministic_per_salt():
    """The same (subject_id, salt) always produces the same pseudonym."""
    p1 = _pseudonymize("alice", "my-salt")
    p2 = _pseudonymize("alice", "my-salt")
    assert p1 == p2


def test_pseudonymization_differs_across_salts():
    """Different salts must produce different pseudonyms for the same subject."""
    p1 = _pseudonymize("alice", "salt-A")
    p2 = _pseudonymize("alice", "salt-B")
    assert p1 != p2


def test_pseudonymization_differs_across_subjects_same_salt():
    """Different subjects must produce different pseudonyms even with the same salt."""
    p1 = _pseudonymize("alice", "salt-X")
    p2 = _pseudonymize("bob", "salt-X")
    assert p1 != p2


def test_pseudonymization_does_not_contain_raw_subject_id():
    """The pseudonym string must not contain the raw subject id as a substring."""
    subject_id = "alice-operator"
    pseudo = _pseudonymize(subject_id, "some-salt")
    assert subject_id not in pseudo


def test_receipt_subject_id_matches_pseudonymize_function():
    """receipt.subjectId must equal _pseudonymize(subject_id, salt)."""
    subject_id = "mary"
    salt = "consistent-salt"
    svc = _make_service(salt=salt)
    receipt = _submit_and_execute(svc, subject_id)
    expected = _pseudonymize(subject_id, salt)
    assert receipt.subjectId == expected


# ===========================================================================
# 14. Illegal state transitions
# ===========================================================================


def test_illegal_transition_execute_on_rejected_raises():
    """execute() on a REJECTED request must raise IllegalTransitionError."""
    svc = _make_service(legal_hold_fn=lambda _: True)
    with pytest.raises(ErasureError):
        svc.submit(SubjectType.OPERATOR, "norm", "admin", "test")
    # find the REJECTED request
    reqs = svc.list_requests(subject_id="norm", status=ErasureStatus.REJECTED)
    assert len(reqs) == 1
    with pytest.raises(IllegalTransitionError):
        svc.execute(reqs[0].requestId)


def test_illegal_transition_execute_on_in_progress_raises():
    """execute() on an IN_PROGRESS request must raise IllegalTransitionError."""
    svc = _make_service()
    req = svc.submit(SubjectType.OPERATOR, "olivia", "admin", "test")
    # Simulate concurrent execution by manually flipping the state
    req.status = ErasureStatus.IN_PROGRESS
    with pytest.raises(IllegalTransitionError):
        svc.execute(req.requestId)


def test_illegal_transition_raises_correct_error_type():
    """IllegalTransitionError must be a subclass of ErasureError."""
    assert issubclass(IllegalTransitionError, ErasureError)


# ===========================================================================
# 15. Unknown request_id
# ===========================================================================


def test_unknown_request_id_raises_erasure_not_found_error():
    """get() and execute() raise ErasureNotFoundError for unknown request IDs."""
    svc = _make_service()
    with pytest.raises(ErasureNotFoundError):
        svc.get("non-existent-id")


def test_unknown_request_id_execute_raises():
    svc = _make_service()
    with pytest.raises(ErasureNotFoundError):
        svc.execute("does-not-exist")


def test_unknown_request_id_preview_raises():
    svc = _make_service()
    with pytest.raises(ErasureNotFoundError):
        svc.preview("does-not-exist")


# ===========================================================================
# 16. Subject with no data anywhere
# ===========================================================================


def test_no_data_subject_yields_completed_receipt_with_all_zero_erased_counts():
    """A subject with nothing in any store yields COMPLETED with zero erased records."""
    svc = _make_service()  # all stores empty
    receipt = _submit_and_execute(svc, "unknown-nobody")
    assert receipt.status == ErasureStatus.COMPLETED
    assert receipt.erasedCounts.get("interview-transcripts") == 0
    assert receipt.erasedCounts.get("knowledge-procedures") == 0
    assert receipt.erasedCounts.get("copilot-conversations") == 0


def test_no_data_subject_chain_still_verifies():
    """Even for a subject with no data, the chain verifies before and after."""
    audit = AuditLog()
    svc = _make_service(audit_log=audit)
    assert audit.verify() is True
    _submit_and_execute(svc, "ghost-user")
    assert audit.verify() is True


# ===========================================================================
# 17 & 18. Receipt fields
# ===========================================================================


def test_receipt_contains_audit_chain_ref():
    """receipt.auditChainRef must be the record_hash of the erasure.executed entry."""
    audit = AuditLog()
    svc = _make_service(audit_log=audit)
    receipt = _submit_and_execute(svc)
    erasure_records = [r for r in audit.query(domain="erasure") if r.action == "erasure.executed"]
    assert len(erasure_records) == 1
    assert receipt.auditChainRef == erasure_records[0].record_hash


def test_receipt_chain_verified_after_is_true():
    """receipt.chainVerifiedAfter must be True after a normal erasure."""
    svc = _make_service()
    receipt = _submit_and_execute(svc)
    assert receipt.chainVerifiedAfter is True


def test_receipt_executed_at_is_populated():
    """receipt.executedAt must be a non-empty ISO timestamp."""
    svc = _make_service()
    receipt = _submit_and_execute(svc)
    assert receipt.executedAt and "T" in receipt.executedAt


# ===========================================================================
# 19. list_requests / get
# ===========================================================================


def test_get_request_returns_correct_request():
    svc = _make_service()
    req = svc.submit(SubjectType.OPERATOR, "petra", "admin", "test")
    fetched = svc.get(req.requestId)
    assert fetched.requestId == req.requestId


def test_list_requests_filter_by_subject_id():
    svc = _make_service()
    svc.submit(SubjectType.OPERATOR, "quinn", "admin", "test 1")
    svc.submit(SubjectType.OPERATOR, "ruth", "admin", "test 2")
    quinn_reqs = svc.list_requests(subject_id="quinn")
    assert all(r.subjectId == "quinn" for r in quinn_reqs)
    assert len(quinn_reqs) == 1


def test_list_requests_filter_by_status():
    svc = _make_service()
    req = svc.submit(SubjectType.OPERATOR, "stan", "admin", "test")
    svc.execute(req.requestId)
    pending = svc.list_requests(status=ErasureStatus.PENDING)
    completed = svc.list_requests(status=ErasureStatus.COMPLETED)
    assert not any(r.requestId == req.requestId for r in pending)
    assert any(r.requestId == req.requestId for r in completed)


# ===========================================================================
# 20. Copilot conversations
# ===========================================================================


def test_copilot_conversations_deleted_on_execute():
    """All Copilot conversations owned by the subject must be deleted."""
    copilot = _FakeCopilotStore()
    copilot.add_conversations("tina", "What is the energy price?", "Show me alerts.")
    svc = _make_service(copilot=copilot)
    _submit_and_execute(svc, "tina")
    assert copilot.count_subject_conversations("tina") == 0


def test_copilot_conversations_of_other_owner_untouched():
    """Erasure of one subject must not touch another user's conversations."""
    copilot = _FakeCopilotStore()
    copilot.add_conversations("uma", "my chat")
    copilot.add_conversations("vic", "vic's private chat")
    svc = _make_service(copilot=copilot)
    _submit_and_execute(svc, "uma")
    assert copilot.count_subject_conversations("vic") == 1


# ===========================================================================
# 21. Telemetry target
# ===========================================================================


def test_telemetry_always_retained_with_legal_basis():
    """The telemetry-attribution target must always be retain-legal-basis and completed."""
    svc = _make_service()
    req = svc.submit(SubjectType.OPERATOR, "wendy", "admin", "test")
    receipt = svc.execute(req.requestId)
    telemetry_target = next(
        t for t in receipt.targets if t.store == "telemetry-attribution"
    )
    assert telemetry_target.action == "retain-legal-basis"
    assert telemetry_target.completed is True
    assert telemetry_target.legalBasis is not None


# ===========================================================================
# 22. submit() creates PENDING with correct shape
# ===========================================================================


def test_submit_creates_pending_request_with_all_five_targets():
    """submit() must return a PENDING request with all five store targets listed."""
    svc = _make_service()
    req = svc.submit(SubjectType.INTERVIEW_PARTICIPANT, "xena", "admin", "GDPR")
    assert req.status == ErasureStatus.PENDING
    stores = {t.store for t in req.targets}
    assert stores == {
        "interview-transcripts",
        "knowledge-procedures",
        "copilot-conversations",
        "audit-chain",
        "telemetry-attribution",
    }


def test_submit_appends_erasure_requested_audit_record():
    """submit() must append an 'erasure.requested' record to the audit chain."""
    audit = AuditLog()
    svc = _make_service(audit_log=audit)
    svc.submit(SubjectType.OPERATOR, "yara", "admin", "test")
    records = audit.query(domain="erasure")
    assert any(r.action == "erasure.requested" for r in records)


def test_request_id_is_deterministic_for_same_subject_and_timestamp(monkeypatch):
    """_make_request_id produces the same UUID5 for the same (subject, timestamp) pair."""
    from knowledge_orchestrator import erasure as erasure_mod
    fixed_ts = "2026-01-01T00:00:00Z"

    # Patch utcnow so the timestamp is fixed across both calls
    class _FixedDT:
        def astimezone(self, tz):
            return self
        def strftime(self, fmt):
            return fixed_ts

    monkeypatch.setattr(erasure_mod, "utcnow", lambda: _FixedDT())
    monkeypatch.setattr(erasure_mod, "iso", lambda _dt: fixed_ts)

    svc1 = _make_service()
    req1 = svc1.submit(SubjectType.OPERATOR, "zara", "admin", "test")

    svc2 = _make_service()
    req2 = svc2.submit(SubjectType.OPERATOR, "zara", "admin", "test")

    assert req1.requestId == req2.requestId


# ===========================================================================
# 23. Multiple sessions all erased
# ===========================================================================


def test_multiple_sessions_all_transcripts_erased():
    """Erasure must delete transcripts from ALL sessions linked to the subject."""
    sessions = _FakeSessionStore()
    sessions.add_session("IV-001", "alice", "part one of transcript")
    sessions.add_session("IV-002", "alice", "part two of transcript")
    sessions.add_session("IV-003", "alice", "part three of transcript")
    svc = _make_service(sessions=sessions)
    receipt = _submit_and_execute(svc, "alice")
    assert sessions.get_transcript("IV-001") is None
    assert sessions.get_transcript("IV-002") is None
    assert sessions.get_transcript("IV-003") is None
    assert receipt.erasedCounts["interview-transcripts"] == 3


# ===========================================================================
# 24. Chain integrity with pre-existing records
# ===========================================================================


def test_chain_integrity_with_many_pre_existing_records():
    """audit.verify() must hold even when the chain has many records before erasure."""
    audit = AuditLog()
    for i in range(20):
        audit.append(
            correlation_id=f"c{i}",
            domain="knowledge",
            action="procedure.approve",
            entity_id=f"PROC-{i}",
            actor="ke",
            output={"version": i + 1},
            decision="APPROVED",
        )
    assert audit.verify() is True
    svc = _make_service(audit_log=audit)
    _submit_and_execute(svc, "alice")
    assert audit.verify() is True
