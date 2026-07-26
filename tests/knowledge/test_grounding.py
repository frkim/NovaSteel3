import pytest

from knowledge_orchestrator import grounding as g
from knowledge_orchestrator.models import Citation, SourceType


def _proc_cite(pid):
    return Citation(SourceType.APPROVED_PROCEDURE, pid)


def _seg_cite(sid):
    return Citation(SourceType.TRANSCRIPT_SEGMENT, sid)


def test_retrieval_grounding_ok():
    res = g.enforce_retrieval_grounding("answer", [_proc_cite("P1")], {"P1", "P2"})
    assert res.grounded


def test_retrieval_rejects_empty_answer():
    with pytest.raises(g.GroundingError):
        g.enforce_retrieval_grounding("", [_proc_cite("P1")], {"P1"})


def test_retrieval_rejects_missing_citations():
    with pytest.raises(g.GroundingError):
        g.enforce_retrieval_grounding("answer", [], {"P1"})


def test_retrieval_rejects_unapproved_procedure():
    with pytest.raises(g.GroundingError) as exc:
        g.enforce_retrieval_grounding("answer", [_proc_cite("DRAFT-1")], {"P1"})
    assert any("not an approved procedure" in r for r in exc.value.reasons)


def test_retrieval_rejects_transcript_citation():
    with pytest.raises(g.GroundingError):
        g.enforce_retrieval_grounding("answer", [_seg_cite("seg-1")], {"seg-1"})


def test_extraction_grounding_ok():
    res = g.enforce_extraction_grounding([_seg_cite("seg-002")], {"seg-002", "seg-003"})
    assert res.grounded


def test_extraction_rejects_invented_segment():
    with pytest.raises(g.GroundingError) as exc:
        g.enforce_extraction_grounding([_seg_cite("seg-999")], {"seg-002"})
    assert any("does not exist" in r for r in exc.value.reasons)


def test_extraction_rejects_procedure_citation():
    with pytest.raises(g.GroundingError):
        g.enforce_extraction_grounding([_proc_cite("P1")], {"seg-002"})
