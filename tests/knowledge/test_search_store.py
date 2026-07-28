"""Tests for the AI Search procedure store and the local fallback.

The Azure path is exercised through a fake SDK surface rather than a live service:
what matters is that the schema, the APPROVED-only invariant, the document shape and
the RetrievalResult contract are right, and none of those need a network.
"""

from __future__ import annotations

import pytest

from knowledge_orchestrator.models import (
    ExtractedKnowledge,
    Procedure,
    ProcedureStatus,
)
from knowledge_orchestrator.retrieval import RetrievalResult
from knowledge_orchestrator.search_store import (
    DEFAULT_INDEX_NAME,
    ENV_SEARCH_ENDPOINT,
    ENV_SEARCH_INDEX,
    ENV_STORE_MODE,
    AzureSearchProcedureStore,
    LocalProcedureStore,
    SearchStoreConfig,
    _document_key,
    create_procedure_store,
)


def _knowledge():
    return ExtractedKnowledge(
        observation="Hearth sector reads high temperature anomaly detected.",
        recommended_check="Compare neighboring shell thermocouples and review flow history.",
        rationale="Corroborating signals distinguish real thermal events from faulty sensors.",
        safety_boundary="Do not bypass alarms or change setpoints without approval.",
        citations=(),
    )


def _procedure(proc_id="PROC-TEMP-0001", status=ProcedureStatus.APPROVED):
    return Procedure(
        procedure_id=proc_id,
        title="Hearth temperature verification",
        status=status,
        version=2,
        knowledge=_knowledge(),
        session_id=None,
        created_by="system",
    )


# ---------------------------------------------------------------------------
# Fake SDK surface
# ---------------------------------------------------------------------------


class _FakeSearchClient:
    def __init__(self):
        self.uploaded: list[dict] = []
        self.deleted: list[dict] = []
        self.search_calls: list[dict] = []
        self.results: list[dict] = []
        self.closed = False

    def merge_or_upload_documents(self, documents):
        self.uploaded.extend(documents)

    def delete_documents(self, documents):
        self.deleted.extend(documents)

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return list(self.results)

    def close(self):
        self.closed = True


class _FakeIndexClient:
    def __init__(self):
        self.indexes: list[object] = []
        self.closed = False

    def create_or_update_index(self, index):
        self.indexes.append(index)

    def close(self):
        self.closed = True


@pytest.fixture
def azure_store(monkeypatch):
    """An AzureSearchProcedureStore wired to fake clients."""
    config = SearchStoreConfig(
        endpoint="https://srch-test.search.windows.net",
        index_name="novasteel-procedures",
        foundry_endpoint="https://foundry-test.cognitiveservices.azure.com",
        embed_deployment="text-embedding-3-large",
    )
    store = AzureSearchProcedureStore(config, credential=object())
    search_client = _FakeSearchClient()
    index_client = _FakeIndexClient()
    monkeypatch.setattr(store, "_search_client", lambda: search_client)
    monkeypatch.setattr(store, "_index_client", lambda: index_client)
    # ensure_index() would need the real SDK models to build a schema.
    monkeypatch.setattr(store, "ensure_index", lambda: None)
    return store, search_client, index_client


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def test_config_from_env_returns_none_without_endpoint(monkeypatch):
    monkeypatch.delenv(ENV_SEARCH_ENDPOINT, raising=False)
    assert SearchStoreConfig.from_env() is None


def test_config_from_env_defaults_index_name(monkeypatch):
    monkeypatch.setenv(ENV_SEARCH_ENDPOINT, "https://srch-test.search.windows.net/")
    monkeypatch.delenv(ENV_SEARCH_INDEX, raising=False)
    config = SearchStoreConfig.from_env()
    assert config is not None
    # Trailing slash stripped so URL joins never double up.
    assert config.endpoint == "https://srch-test.search.windows.net"
    assert config.index_name == DEFAULT_INDEX_NAME


def test_document_key_is_search_legal_and_reversible():
    assert _document_key("PROC-TEMP-0001#c2") == "PROC-TEMP-0001_c2"
    assert "#" not in _document_key("PROC-TEMP-0001#c2")


# ---------------------------------------------------------------------------
# Security invariant
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status",
    [ProcedureStatus.DRAFT, ProcedureStatus.IN_REVIEW, ProcedureStatus.REJECTED],
)
def test_index_rejects_non_approved_procedures(azure_store, status):
    store, search_client, _ = azure_store
    with pytest.raises(ValueError, match="only APPROVED procedures"):
        store.index([_procedure(status=status)])
    # Nothing may be written before the check completes.
    assert search_client.uploaded == []


def test_index_rejects_batch_containing_one_draft(azure_store):
    store, search_client, _ = azure_store
    procedures = [
        _procedure("PROC-A-0001"),
        _procedure("PROC-B-0002", status=ProcedureStatus.DRAFT),
    ]
    with pytest.raises(ValueError):
        store.index(procedures)
    assert search_client.uploaded == []


def test_local_store_rejects_non_approved_procedures():
    store = LocalProcedureStore()
    with pytest.raises(ValueError):
        store.index([_procedure(status=ProcedureStatus.DRAFT)])


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------


def test_index_uploads_one_document_per_chunk(azure_store):
    store, search_client, _ = azure_store
    store.index([_procedure()])

    # chunk_procedure emits one chunk per knowledge section.
    assert len(search_client.uploaded) == 4
    doc = search_client.uploaded[0]
    assert doc["chunk_key"] == "PROC-TEMP-0001_c0"
    assert doc["chunk_id"] == "PROC-TEMP-0001#c0"
    assert doc["procedure_id"] == "PROC-TEMP-0001"
    assert doc["section"] == "observation"
    assert doc["procedure_title"] == "Hearth temperature verification"
    assert doc["text"]
    assert doc["token_count"] > 0
    assert search_client.closed


def test_index_of_empty_list_writes_nothing(azure_store):
    store, search_client, _ = azure_store
    store.index([])
    assert search_client.uploaded == []


def test_delete_procedure_filters_by_procedure_id(azure_store):
    store, search_client, _ = azure_store
    search_client.results = [
        {"chunk_key": "PROC-TEMP-0001_c0"},
        {"chunk_key": "PROC-TEMP-0001_c1"},
    ]
    deleted = store.delete_procedure("PROC-TEMP-0001")

    assert deleted == 2
    assert search_client.search_calls[0]["filter"] == "procedure_id eq 'PROC-TEMP-0001'"
    assert search_client.deleted == [
        {"chunk_key": "PROC-TEMP-0001_c0"},
        {"chunk_key": "PROC-TEMP-0001_c1"},
    ]


# ---------------------------------------------------------------------------
# Retrieval contract
# ---------------------------------------------------------------------------


def test_search_uses_semantic_hybrid_query(azure_store, monkeypatch):
    store, search_client, _ = azure_store
    search_client.results = [
        {
            "chunk_id": "PROC-TEMP-0001#c0",
            "procedure_id": "PROC-TEMP-0001",
            "procedure_title": "Hearth temperature verification",
            "section": "observation",
            "text": "Hearth sector reads high temperature.",
            "token_count": 6,
            "@search.score": 4.2,
            "@search.reranker_score": 2.7,
        }
    ]
    # VectorizableTextQuery lives in the real SDK; stub the import site.
    import sys
    import types

    module = types.ModuleType("azure.search.documents.models")
    module.VectorizableTextQuery = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, "azure.search.documents.models", module)

    result = store.search("hearth temperature", top_k=3)

    call = search_client.search_calls[0]
    assert call["query_type"] == "semantic"
    assert call["top"] == 3
    assert call["vector_queries"], "hybrid search must issue a vector query"

    assert isinstance(result, RetrievalResult)
    assert result.declined is False
    assert result.providerUsed == "azure-ai-search"
    chunk = result.chunks[0]
    assert chunk.chunk.chunk_id == "PROC-TEMP-0001#c0"
    assert chunk.lexicalScore == pytest.approx(4.2)
    assert chunk.semanticScore == pytest.approx(2.7)


def test_search_declines_when_nothing_matches(azure_store, monkeypatch):
    store, search_client, _ = azure_store
    search_client.results = []
    import sys
    import types

    module = types.ModuleType("azure.search.documents.models")
    module.VectorizableTextQuery = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, "azure.search.documents.models", module)

    result = store.search("something unrelated")

    assert result.declined is True
    assert result.declineReason == "no_grounded_source"
    assert result.chunks == []


# ---------------------------------------------------------------------------
# Local store + factory
# ---------------------------------------------------------------------------


def test_local_store_round_trip():
    store = LocalProcedureStore()
    store.index([_procedure()])
    result = store.search("hearth temperature anomaly")

    assert result.declined is False
    assert result.chunks
    assert result.chunks[0].chunk.procedure_id == "PROC-TEMP-0001"


def test_local_store_delete_removes_from_retrieval():
    store = LocalProcedureStore()
    store.index([_procedure()])
    removed = store.delete_procedure("PROC-TEMP-0001")

    assert removed == 4
    assert store.search("hearth temperature anomaly").declined is True


def test_local_store_delete_unknown_procedure_is_noop():
    store = LocalProcedureStore()
    store.index([_procedure()])
    assert store.delete_procedure("PROC-NOPE-9999") == 0


def test_factory_returns_local_without_configuration(monkeypatch):
    monkeypatch.delenv(ENV_SEARCH_ENDPOINT, raising=False)
    monkeypatch.delenv(ENV_STORE_MODE, raising=False)
    assert isinstance(create_procedure_store(), LocalProcedureStore)


def test_factory_honours_explicit_local_override(monkeypatch):
    monkeypatch.setenv(ENV_SEARCH_ENDPOINT, "https://srch-test.search.windows.net")
    monkeypatch.setenv(ENV_STORE_MODE, "local")
    assert isinstance(create_procedure_store(), LocalProcedureStore)


def test_factory_falls_back_when_sdk_missing(monkeypatch):
    """An unconfigured or SDK-less environment degrades; it must not raise."""
    monkeypatch.setenv(ENV_SEARCH_ENDPOINT, "https://srch-test.search.windows.net")
    monkeypatch.delenv(ENV_STORE_MODE, raising=False)

    def _boom(self):
        raise ImportError("azure-search-documents is not installed")

    monkeypatch.setattr(AzureSearchProcedureStore, "ensure_index", _boom)
    assert isinstance(create_procedure_store(), LocalProcedureStore)
