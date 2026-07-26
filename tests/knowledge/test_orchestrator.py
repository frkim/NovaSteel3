import pytest

from knowledge_orchestrator.orchestrator import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)


def _create_and_transcribe(orch, audio_meta, granted=True):
    created = orch.create_interview(
        operator_ref="OP-DEMO-014",
        language="en",
        retention_days=30,
        consent_granted=granted,
    )
    sid = created["sessionId"]
    if granted:
        orch.submit_audio(session_id=sid, meta=audio_meta(sid), audio_ref="op.wav")
    return sid


def test_end_to_end_happy_path(orchestrator, audio_meta):
    orch = orchestrator
    sid = _create_and_transcribe(orch, audio_meta)

    transcript = orch.get_transcript(sid)
    assert transcript["status"] == "COMPLETED"
    assert transcript["classification"] == "Highly Confidential"

    draft = orch.extract_draft(session_id=sid, title="Hearth check")
    assert draft.status.value == "DRAFT"
    assert draft.citations

    # Draft is not retrievable via approved-only search.
    assert orch.search_procedures("hearth")["total"] == 0

    orch.submit_for_review(draft.procedure_id, actor="ke")
    approved = orch.approve_procedure(
        procedure_id=draft.procedure_id,
        actor="ke",
        actor_roles={"Knowledge.Publisher"},
        expected_version=draft.version,
        idempotency_key="k1",
    )
    assert approved.status.value == "APPROVED"
    assert orch.search_procedures("hearth")["total"] == 1


def test_submit_audio_requires_consent(orchestrator, audio_meta):
    orch = orchestrator
    created = orch.create_interview(
        operator_ref="OP-1", language="en", retention_days=30, consent_granted=False
    )
    sid = created["sessionId"]
    with pytest.raises(Exception):
        orch.submit_audio(session_id=sid, meta=audio_meta(sid), audio_ref="op.wav")


def test_approve_requires_publisher_role(orchestrator, audio_meta):
    orch = orchestrator
    sid = _create_and_transcribe(orch, audio_meta)
    draft = orch.extract_draft(session_id=sid, title="t")
    orch.submit_for_review(draft.procedure_id, actor="ke")
    with pytest.raises(ForbiddenError):
        orch.approve_procedure(
            procedure_id=draft.procedure_id,
            actor="ke",
            actor_roles={"Operator.Read"},
            expected_version=draft.version,
            idempotency_key="k",
        )


def test_approve_is_idempotent(orchestrator, audio_meta):
    orch = orchestrator
    sid = _create_and_transcribe(orch, audio_meta)
    draft = orch.extract_draft(session_id=sid, title="t")
    orch.submit_for_review(draft.procedure_id, actor="ke")
    a1 = orch.approve_procedure(
        procedure_id=draft.procedure_id,
        actor="ke",
        actor_roles={"Knowledge.Publisher"},
        expected_version=draft.version,
        idempotency_key="same",
    )
    a2 = orch.approve_procedure(
        procedure_id=draft.procedure_id,
        actor="ke",
        actor_roles={"Knowledge.Publisher"},
        expected_version=999,  # ignored on idempotent replay
        idempotency_key="same",
    )
    assert a1.version == a2.version == 2


def test_stale_version_conflict(orchestrator, audio_meta):
    orch = orchestrator
    sid = _create_and_transcribe(orch, audio_meta)
    draft = orch.extract_draft(session_id=sid, title="t")
    orch.submit_for_review(draft.procedure_id, actor="ke")
    with pytest.raises(ConflictError):
        orch.approve_procedure(
            procedure_id=draft.procedure_id,
            actor="ke",
            actor_roles={"Knowledge.Publisher"},
            expected_version=42,
            idempotency_key="k",
        )


def test_withdraw_consent_deletes_transcript_and_audits(orchestrator, audio_meta):
    orch = orchestrator
    sid = _create_and_transcribe(orch, audio_meta)
    result = orch.withdraw_consent(session_id=sid, deletion_request_ref="DEL-1")
    assert result["consentState"] == "WITHDRAWN"
    assert result["deletion"]["deletionRequestRef"] == "DEL-1"
    with pytest.raises(ForbiddenError):
        orch.get_transcript(sid)


def test_audit_chain_valid_after_flow(orchestrator, audio_meta):
    orch = orchestrator
    sid = _create_and_transcribe(orch, audio_meta)
    orch.extract_draft(session_id=sid, title="t")
    assert orch.audit.verify() is True
    records = orch.get_audit()
    actions = {r["action"] for r in records}
    assert {"interview.create", "interview.transcribe", "draft.create"} <= actions


def test_unknown_session_not_found(orchestrator):
    with pytest.raises(NotFoundError):
        orchestrator.get_transcript("NOPE")
