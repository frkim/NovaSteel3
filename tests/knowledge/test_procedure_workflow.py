import pytest

from knowledge_orchestrator import procedure_workflow as wf
from knowledge_orchestrator.models import (
    Citation,
    ExtractedKnowledge,
    ProcedureStatus,
    SourceType,
)


def _knowledge():
    return ExtractedKnowledge(
        observation="obs",
        recommended_check="check",
        rationale="why",
        safety_boundary="never bypass alarms",
        citations=(Citation(SourceType.TRANSCRIPT_SEGMENT, "seg-002"),),
    )


def _draft():
    return wf.create_draft("PROC-1", "Title", _knowledge(), "IV-1", "knowledge-capture")


def test_agent_only_creates_draft():
    p = _draft()
    assert p.status is ProcedureStatus.DRAFT
    assert p.version == 1


def test_full_happy_path():
    p = wf.submit_for_review(_draft(), actor="ke")
    assert p.status is ProcedureStatus.IN_REVIEW
    approved = wf.approve(p, actor="ke", actor_roles={wf.PUBLISHER_ROLE}, expected_version=1)
    assert approved.status is ProcedureStatus.APPROVED
    assert approved.version == 2
    assert approved.approved_by == "ke"
    assert wf.is_retrievable(approved)


def test_approve_requires_publisher_role():
    p = wf.submit_for_review(_draft(), actor="ke")
    with pytest.raises(wf.WorkflowError):
        wf.approve(p, actor="ke", actor_roles={"Operator.Read"}, expected_version=1)


def test_approve_stale_version_rejected():
    p = wf.submit_for_review(_draft(), actor="ke")
    with pytest.raises(wf.StaleApprovalError):
        wf.approve(p, actor="ke", actor_roles={wf.PUBLISHER_ROLE}, expected_version=99)


def test_cannot_approve_a_draft_directly():
    with pytest.raises(wf.WorkflowError):
        wf.approve(_draft(), actor="ke", actor_roles={wf.PUBLISHER_ROLE}, expected_version=1)


def test_approved_is_terminal():
    p = wf.submit_for_review(_draft(), actor="ke")
    approved = wf.approve(p, actor="ke", actor_roles={wf.PUBLISHER_ROLE}, expected_version=1)
    with pytest.raises(wf.WorkflowError):
        wf.reject(approved, actor="ke", actor_roles={wf.PUBLISHER_ROLE})


def test_draft_not_retrievable():
    assert not wf.is_retrievable(_draft())


def test_reject_requires_role():
    with pytest.raises(wf.WorkflowError):
        wf.reject(_draft(), actor="ke", actor_roles=set())
