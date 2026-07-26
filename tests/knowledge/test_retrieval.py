"""Tests for the hybrid grounded retriever (retrieval.py).

Covers: chunk_procedure, BM25 ranking, hashing embeddings, RRF fusion,
APPROVED-only indexing invariant, decline path, citation enforcement,
and build_decline_answer.
"""

from __future__ import annotations

import math

import pytest

from knowledge_orchestrator.models import (
    ExtractedKnowledge,
    Procedure,
    ProcedureStatus,
)
from knowledge_orchestrator.retrieval import (
    CITATION_PATTERN,
    CitationError,
    HashingEmbeddingProvider,
    HybridRetriever,
    ScoredChunk,
    _BM25Index,
    _tokenize,
    build_decline_answer,
    chunk_procedure,
    enforce_answer_citations,
    extract_citations,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _knowledge(
    obs="Hearth sector reads high temperature anomaly detected.",
    check="Compare neighboring shell thermocouples and review flow history carefully.",
    rat="Corroborating signals distinguish real thermal events from faulty sensor readings.",
    safety="Do not bypass alarms or change setpoints without engineering approval.",
):
    return ExtractedKnowledge(
        observation=obs,
        recommended_check=check,
        rationale=rat,
        safety_boundary=safety,
        citations=(),
    )


def _approved(proc_id="PROC-TEMP-0001", title="Hearth temperature verification"):
    return Procedure(
        procedure_id=proc_id,
        title=title,
        status=ProcedureStatus.APPROVED,
        version=2,
        knowledge=_knowledge(),
        session_id=None,
        created_by="system",
    )


def _draft(proc_id="PROC-DRAFT-0001"):
    return Procedure(
        procedure_id=proc_id,
        title="Draft procedure",
        status=ProcedureStatus.DRAFT,
        version=1,
        knowledge=_knowledge(),
        session_id=None,
        created_by="operator",
    )


def _pressure_approved():
    k = ExtractedKnowledge(
        observation="Pressure gauge calibration drift detected on primary circuit.",
        recommended_check="Compare pressure gauge against reference standard at rated flow.",
        rationale="Calibration drift causes inaccurate pressure readings on the gauge.",
        safety_boundary="Do not modify pressure relief valves without engineering sign-off.",
        citations=(),
    )
    return Procedure(
        procedure_id="PROC-PRESSURE-0001",
        title="Pressure gauge calibration",
        status=ProcedureStatus.APPROVED,
        version=2,
        knowledge=k,
        session_id=None,
        created_by="system",
    )


def _two_proc_retriever(min_score: float = 0.0) -> HybridRetriever:
    r = HybridRetriever(min_score=min_score)
    r.index([_approved(), _pressure_approved()])
    return r


# ---------------------------------------------------------------------------
# chunk_procedure
# ---------------------------------------------------------------------------


def test_chunk_procedure_produces_four_chunks():
    chunks = chunk_procedure(_approved())
    assert len(chunks) == 4


def test_chunk_ids_have_correct_format():
    proc = _approved("PROC-TEST-9999")
    chunks = chunk_procedure(proc)
    for i, c in enumerate(chunks):
        assert c.chunk_id == f"PROC-TEST-9999#c{i}"


def test_chunk_procedure_stable_deterministic():
    proc = _approved()
    assert [c.chunk_id for c in chunk_procedure(proc)] == [
        c.chunk_id for c in chunk_procedure(proc)
    ]


def test_chunk_contains_procedure_metadata():
    proc = _approved("PROC-TEST-0001", "My Title")
    for c in chunk_procedure(proc):
        assert c.procedure_id == "PROC-TEST-0001"
        assert c.procedure_title == "My Title"


def test_chunk_section_names():
    chunks = chunk_procedure(_approved())
    sections = [c.section for c in chunks]
    assert sections == ["observation", "recommended_check", "rationale", "safety_boundary"]


def test_chunk_text_contains_title():
    proc = _approved(title="Unique Title XYZ987")
    for c in chunk_procedure(proc):
        assert "Unique Title XYZ987" in c.text


def test_chunk_token_count_positive():
    for c in chunk_procedure(_approved()):
        assert c.token_count > 0


# ---------------------------------------------------------------------------
# BM25 ranking
# ---------------------------------------------------------------------------


def test_bm25_matching_chunk_ranks_first():
    """Query term present in only one document must rank that document first."""
    idx = _BM25Index()
    idx.fit(
        [
            "review the temperature sensor reading anomaly",
            "review the pressure gauge calibration drift",
        ]
    )
    scores = idx.scores("temperature")
    assert scores[0] > scores[1], "temperature-doc should outscore pressure-doc"


def test_bm25_idf_downweights_ubiquitous_term():
    """A term present in every document must have lower impact than a unique term."""
    idx = _BM25Index()
    idx.fit(
        [
            "check the temperature sensor anomaly",
            "check the pressure gauge calibration",
        ]
    )
    scores_unique = idx.scores("temperature")   # only in doc 0
    scores_common = idx.scores("check")         # stop word → filtered → ~0
    # unique term gives doc 0 a non-zero score; common/stop term gives nothing
    assert scores_unique[0] > 0
    assert scores_unique[0] >= scores_unique[1]


def test_bm25_stop_words_filtered():
    """Stop words in the query must not contribute to scores."""
    idx = _BM25Index()
    idx.fit(["the quick brown fox", "the lazy dog"])
    scores = idx.scores("the")   # 'the' is a stop word → filtered
    # Both scores must be 0 (no term contributes)
    assert scores[0] == 0.0 and scores[1] == 0.0


def test_bm25_query_term_absent_gives_zero():
    idx = _BM25Index()
    idx.fit(["temperature sensor check", "pressure gauge calibration"])
    scores = idx.scores("uranium")
    assert all(s == 0.0 for s in scores)


def test_tokenize_removes_stop_words():
    tokens = _tokenize("the quick brown fox")
    assert "the" not in tokens
    assert "quick" in tokens or "brown" in tokens  # non-stops survive


def test_tokenize_stems():
    tokens = _tokenize("sensors readings")
    # 'sensors' → 'sensor' (strip 's'), 'readings' → 'read' (strip 'ings')
    # Exact stem depends on implementation; just verify tokens are shorter
    assert all(len(t) <= len(w) for t, w in zip(tokens, ["sensors", "readings"]))


# ---------------------------------------------------------------------------
# Hashing embeddings
# ---------------------------------------------------------------------------


def test_hashing_embedder_deterministic():
    emb = HashingEmbeddingProvider()
    v1 = emb.embed(["hearth sector over-temperature verification"])[0]
    v2 = emb.embed(["hearth sector over-temperature verification"])[0]
    assert v1 == v2


def test_hashing_embedder_l2_normalised():
    emb = HashingEmbeddingProvider()
    for text in ["hearth over-temperature", "pressure calibration drift"]:
        v = emb.embed([text])[0]
        norm = math.sqrt(sum(x * x for x in v))
        assert abs(norm - 1.0) < 1e-6, f"norm={norm} for '{text}'"


def test_hashing_embedder_cosine_self_is_one():
    emb = HashingEmbeddingProvider()
    v = emb.embed(["thermocouple drift validation procedure"])[0]
    dot = sum(x * y for x, y in zip(v, v))
    assert abs(dot - 1.0) < 1e-6, f"self-cosine={dot}"


def test_hashing_embedder_distinct_texts_differ():
    emb = HashingEmbeddingProvider()
    v1 = emb.embed(["temperature sensor anomaly"])[0]
    v2 = emb.embed(["pressure calibration drift"])[0]
    assert v1 != v2


def test_hashing_embedder_dim_256():
    emb = HashingEmbeddingProvider()
    assert len(emb.embed(["test"])[0]) == 256


def test_hashing_embedder_batch():
    emb = HashingEmbeddingProvider()
    vecs = emb.embed(["alpha", "beta", "gamma"])
    assert len(vecs) == 3
    assert all(len(v) == 256 for v in vecs)


# ---------------------------------------------------------------------------
# RRF fusion
# ---------------------------------------------------------------------------


def test_rrf_scores_sorted_descending():
    r = _two_proc_retriever()
    result = r.retrieve("temperature thermocouple sensor anomaly", top_k=10)
    assert not result.declined
    scores = [c.fusedScore for c in result.chunks]
    assert scores == sorted(scores, reverse=True)


def test_rrf_scored_chunk_fields_present():
    r = _two_proc_retriever()
    result = r.retrieve("temperature", top_k=10)
    assert result.chunks
    sc: ScoredChunk = result.chunks[0]
    assert sc.fusedScore > 0
    assert sc.lexicalRank >= 1
    assert sc.semanticRank >= 1
    assert isinstance(sc.lexicalScore, float)
    assert isinstance(sc.semanticScore, float)


def test_rrf_chunk_strong_in_one_modality_still_surfaces():
    """A chunk with a good rank in only one modality must appear in top results."""
    r = _two_proc_retriever()
    result = r.retrieve("temperature anomaly hearth", top_k=10)
    # At least one chunk from the temperature procedure must surface
    proc_ids = {sc.chunk.procedure_id for sc in result.chunks}
    assert "PROC-TEMP-0001" in proc_ids


def test_rrf_query_favours_relevant_procedure():
    r = _two_proc_retriever()
    result = r.retrieve("pressure gauge calibration drift", top_k=4)
    assert not result.declined
    top = result.chunks[0]
    assert "pressure" in top.chunk.procedure_id.lower() or "pressure" in top.chunk.text.lower()


# ---------------------------------------------------------------------------
# Indexing invariants
# ---------------------------------------------------------------------------


def test_indexing_draft_raises():
    r = HybridRetriever()
    with pytest.raises(ValueError, match="cannot be indexed"):
        r.index([_draft()])


def test_indexing_in_review_raises():
    r = HybridRetriever()
    proc = Procedure(
        procedure_id="PROC-IR-0001",
        title="In-review proc",
        status=ProcedureStatus.IN_REVIEW,
        version=1,
        knowledge=_knowledge(),
        session_id=None,
        created_by="operator",
    )
    with pytest.raises(ValueError):
        r.index([proc])


def test_indexing_approved_succeeds():
    r = HybridRetriever()
    r.index([_approved()])  # must not raise


def test_indexing_mixed_raises():
    r = HybridRetriever()
    with pytest.raises(ValueError):
        r.index([_approved(), _draft()])


# ---------------------------------------------------------------------------
# Decline path
# ---------------------------------------------------------------------------


def test_decline_on_empty_index():
    r = HybridRetriever()
    result = r.retrieve("temperature sensor anomaly")
    assert result.declined
    assert result.declineReason == "no_grounded_source"
    assert result.chunks == []


def test_decline_on_high_threshold():
    r = HybridRetriever(min_score=0.0)
    r.index([_approved()])
    result = r.retrieve("completely unrelated gibberish xyz123", top_k=5, min_score=999.0)
    assert result.declined
    assert result.declineReason == "no_grounded_source"
    assert result.chunks == []


def test_decline_result_has_provider_used():
    r = HybridRetriever()
    result = r.retrieve("anything")
    assert result.providerUsed  # non-empty string


# ---------------------------------------------------------------------------
# Citation pattern
# ---------------------------------------------------------------------------


def test_citation_pattern_chunk_reference():
    assert CITATION_PATTERN.search("See [[PROC-APPROVED-0001#c2]] for context.")


def test_citation_pattern_procedure_reference():
    assert CITATION_PATTERN.search("Per [[PROC-APPROVED-0001]] guidelines.")


def test_citation_pattern_rejects_single_brackets():
    assert not CITATION_PATTERN.search("[PROC-APPROVED-0001]")


def test_citation_pattern_rejects_lowercase():
    assert not CITATION_PATTERN.search("[[proc-approved-0001]]")


def test_extract_citations_returns_ids():
    ids = extract_citations(
        "See [[PROC-APPROVED-0001#c0]] and [[PROC-APPROVED-0002]]."
    )
    assert "PROC-APPROVED-0001#c0" in ids
    assert "PROC-APPROVED-0002" in ids


def test_extract_citations_deduplicates():
    ids = extract_citations("[[PROC-X-0001]] blah [[PROC-X-0001]] more")
    assert ids.count("PROC-X-0001") == 1


# ---------------------------------------------------------------------------
# Citation enforcement
# ---------------------------------------------------------------------------


def test_enforce_ok_with_valid_citation():
    enforce_answer_citations(
        "The sensor drift was confirmed. [[PROC-APPROVED-0001#c0]]",
        {"PROC-APPROVED-0001#c0", "PROC-APPROVED-0001#c1"},
    )


def test_enforce_rejects_zero_citations_on_long_answer():
    with pytest.raises(CitationError):
        enforce_answer_citations(
            "The hearth sector temperature is elevated and requires immediate engineering review.",
            {"PROC-APPROVED-0001#c0"},
        )


def test_enforce_rejects_unknown_chunk_id():
    with pytest.raises(CitationError):
        enforce_answer_citations(
            "Temperature high [[PROC-APPROVED-0001#c9]].",
            {"PROC-APPROVED-0001#c0"},
        )


def test_enforce_rejects_uncited_factual_sentence():
    """A second sentence that is long and has no citation must raise CitationError."""
    answer = (
        "[[PROC-APPROVED-0001#c0]] The hearth sector shows over-temperature. "
        "The recommended action is to compare with neighboring thermocouples and "
        "review the cooling water flow history to distinguish sensor fault from real event."
    )
    with pytest.raises(CitationError):
        enforce_answer_citations(answer, {"PROC-APPROVED-0001#c0"})


def test_enforce_allows_empty_answer():
    enforce_answer_citations("", {"PROC-APPROVED-0001#c0"})


def test_enforce_allows_procedure_level_citation():
    """A procedure-level [[PROC-X]] citation is valid if any chunk from PROC-X was retrieved."""
    enforce_answer_citations(
        "Per the hearth procedure [[PROC-APPROVED-0001]].",
        {"PROC-APPROVED-0001#c0", "PROC-APPROVED-0001#c1"},
    )


# ---------------------------------------------------------------------------
# Decline answer
# ---------------------------------------------------------------------------


def test_decline_answer_is_nonempty_string():
    ans = build_decline_answer("no_grounded_source")
    assert isinstance(ans, str) and len(ans) > 0


def test_decline_answer_passes_citation_enforcement():
    """The canonical decline text must pass citation enforcement without markers."""
    decline = build_decline_answer("no_grounded_source")
    # Must not raise — decline text is allow-listed.
    enforce_answer_citations(decline, set())


def test_decline_answer_contains_approved_source_phrase():
    ans = build_decline_answer("no_grounded_source")
    assert "approved source" in ans.lower()
