"""Azure AI Search procedure store — the durable home of the APPROVED corpus.

Until now the approved procedures lived only in :class:`retrieval.HybridRetriever`,
an in-process BM25 + cosine index rebuilt from scratch on every start. That is fine
for a single replica and for the offline demo, but it cannot be shared between the
BFF and the orchestrator, it cannot be queried by an agent, and it does not survive
a restart. This module moves the corpus into Azure AI Search so that:

* every replica queries the same corpus;
* the Foundry IQ knowledge base has something to point a knowledge source at, which
  is what lets the hosted procedure agent answer from procedures (see
  :mod:`knowledge_orchestrator.agent_service`);
* GDPR erasure can delete a document by key rather than rebuilding an index.

Design notes
------------
Two decisions are worth spelling out because they are not obvious:

**The index is built here, not in Bicep.** Search indexes, knowledge sources and
knowledge bases are data-plane objects; ARM has no resource type for them. So
``infra/bicep/modules/ai-search.bicep`` provisions the *service* and outputs the
agreed index name, and this module creates the *schema* at startup. The names are
the contract between the two.

**Retrieval returns the same shape as the local retriever.** ``search()`` returns a
:class:`retrieval.RetrievalResult` with the same ``ScoredChunk``/``Chunk`` payloads,
so citation enforcement, the decline path and every existing consumer work unchanged
regardless of which backend is live.

Following the repository convention, the Azure SDKs are imported lazily inside
methods, the module is importable with nothing but the standard library, and any
failure to reach Search degrades to the in-memory retriever with a logged warning
rather than raising.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Optional, Protocol, runtime_checkable

from .models import Procedure
from .foundry_endpoints import normalize_endpoint
from .procedure_workflow import is_retrievable
from .retrieval import (
    Chunk,
    EmbeddingProvider,
    HybridRetriever,
    RetrievalResult,
    ScoredChunk,
    chunk_procedure,
)

logger = logging.getLogger(__name__)

ENV_SEARCH_ENDPOINT = "AI_SEARCH_ENDPOINT"
ENV_SEARCH_INDEX = "AI_SEARCH_INDEX"
ENV_FOUNDRY_ENDPOINT = "FOUNDRY_ENDPOINT"
ENV_EMBED_DEPLOYMENT = "FOUNDRY_EMBED_DEPLOYMENT"
ENV_STORE_MODE = "PROCEDURE_STORE_MODE"  # "azure" | "local" (explicit override)

DEFAULT_INDEX_NAME = "novasteel-procedures"
DEFAULT_EMBED_MODEL = "text-embedding-3-large"

# text-embedding-3-large native width. Kept explicit rather than inferred because the
# index schema must be fixed before the first document is written, and a mismatch
# fails at write time with an unhelpful error.
EMBEDDING_DIMENSIONS = 3072

VECTOR_PROFILE_NAME = "novasteel-vector-profile"
VECTOR_ALGORITHM_NAME = "novasteel-hnsw"
VECTORIZER_NAME = "novasteel-vectorizer"
SEMANTIC_CONFIG_NAME = "novasteel-semantic"


@runtime_checkable
class ProcedureStore(Protocol):
    """Backend-agnostic contract for the approved-procedure corpus."""

    def index(self, procedures: list[Procedure]) -> None:
        """Replace the stored corpus with *procedures* (APPROVED only)."""
        ...

    def search(self, query: str, top_k: int = 5) -> RetrievalResult:
        """Return the most relevant chunks for *query*."""
        ...

    def delete_procedure(self, procedure_id: str) -> int:
        """Remove every chunk of *procedure_id*. Returns the number deleted."""
        ...


@dataclass(frozen=True)
class SearchStoreConfig:
    """Resolved configuration for :class:`AzureSearchProcedureStore`."""

    endpoint: str
    index_name: str = DEFAULT_INDEX_NAME
    foundry_endpoint: str = ""
    embed_deployment: str = DEFAULT_EMBED_MODEL

    @classmethod
    def from_env(cls) -> Optional["SearchStoreConfig"]:
        """Build a config from the environment, or ``None`` if Search is not wired."""
        endpoint = os.environ.get(ENV_SEARCH_ENDPOINT, "").strip()
        if not endpoint:
            return None
        return cls(
            endpoint=endpoint.rstrip("/"),
            index_name=os.environ.get(ENV_SEARCH_INDEX, "").strip() or DEFAULT_INDEX_NAME,
            foundry_endpoint=normalize_endpoint(os.environ.get(ENV_FOUNDRY_ENDPOINT, "")),
            embed_deployment=(
                os.environ.get(ENV_EMBED_DEPLOYMENT, "").strip() or DEFAULT_EMBED_MODEL
            ),
        )


def _document_key(chunk_id: str) -> str:
    """Encode a chunk id into a legal Search document key.

    Search keys allow only letters, digits, underscore, dash and equals — our chunk
    ids contain ``#``. Substituting rather than hashing keeps the key reversible, so
    a document can still be identified from its id in the portal during triage.
    """
    return chunk_id.replace("#", "_")


class AzureSearchProcedureStore:
    """Stores and retrieves APPROVED procedure chunks in Azure AI Search.

    Uses hybrid retrieval (BM25 + vector) with semantic reranking, which is the same
    fusion strategy as the local retriever but executed service-side and with a
    trained reranker on top. Authentication is managed identity only; the search
    service runs with ``disableLocalAuth: true`` so there is no key path at all.
    """

    provider_used = "azure-ai-search"

    def __init__(self, config: SearchStoreConfig, credential: Any = None) -> None:
        self._config = config
        self._credential = credential
        self._index_ready = False

    # -- clients -----------------------------------------------------------

    def _get_credential(self) -> Any:
        if self._credential is None:
            from azure.identity import DefaultAzureCredential

            self._credential = DefaultAzureCredential()
        return self._credential

    def _index_client(self) -> Any:
        from azure.search.documents.indexes import SearchIndexClient

        return SearchIndexClient(
            endpoint=self._config.endpoint, credential=self._get_credential()
        )

    def _search_client(self) -> Any:
        from azure.search.documents import SearchClient

        return SearchClient(
            endpoint=self._config.endpoint,
            index_name=self._config.index_name,
            credential=self._get_credential(),
        )

    # -- schema ------------------------------------------------------------

    def _build_index_definition(self) -> Any:
        """Define the procedure index: retrievable text, filters, vectors, semantics."""
        from azure.search.documents.indexes.models import (
            AzureOpenAIVectorizer,
            AzureOpenAIVectorizerParameters,
            HnswAlgorithmConfiguration,
            SearchableField,
            SearchField,
            SearchFieldDataType,
            SearchIndex,
            SemanticConfiguration,
            SemanticField,
            SemanticPrioritizedFields,
            SemanticSearch,
            SimpleField,
            VectorSearch,
            VectorSearchProfile,
        )

        fields = [
            SimpleField(name="chunk_key", type=SearchFieldDataType.String, key=True),
            SimpleField(
                name="chunk_id", type=SearchFieldDataType.String, filterable=True
            ),
            SimpleField(
                name="procedure_id",
                type=SearchFieldDataType.String,
                filterable=True,
                # Filterable + facetable so erasure can delete by procedure and the
                # portal can show corpus composition at a glance.
                facetable=True,
            ),
            SearchableField(name="procedure_title", type=SearchFieldDataType.String),
            SimpleField(name="section", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="text", type=SearchFieldDataType.String),
            SimpleField(name="token_count", type=SearchFieldDataType.Int32),
            SearchField(
                name="text_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                # Not retrievable: 3072 floats per chunk would dominate every response
                # payload and the caller never needs them.
                retrievable=False,
                vector_search_dimensions=EMBEDDING_DIMENSIONS,
                vector_search_profile_name=VECTOR_PROFILE_NAME,
            ),
        ]

        # Integrated vectorization: Search calls the embedding deployment itself, both
        # when indexing and when vectorizing an incoming query, using its own managed
        # identity. That keeps a single embedding model in play for both sides of the
        # comparison — mismatched query/document embeddings are a classic silent
        # relevance bug.
        vectorizers = []
        if self._config.foundry_endpoint:
            vectorizers.append(
                AzureOpenAIVectorizer(
                    vectorizer_name=VECTORIZER_NAME,
                    parameters=AzureOpenAIVectorizerParameters(
                        resource_url=self._config.foundry_endpoint,
                        deployment_name=self._config.embed_deployment,
                        model_name=self._config.embed_deployment,
                    ),
                )
            )

        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name=VECTOR_ALGORITHM_NAME)],
            profiles=[
                VectorSearchProfile(
                    name=VECTOR_PROFILE_NAME,
                    algorithm_configuration_name=VECTOR_ALGORITHM_NAME,
                    vectorizer_name=VECTORIZER_NAME if vectorizers else None,
                )
            ],
            vectorizers=vectorizers or None,
        )

        semantic_search = SemanticSearch(
            configurations=[
                SemanticConfiguration(
                    name=SEMANTIC_CONFIG_NAME,
                    prioritized_fields=SemanticPrioritizedFields(
                        title_field=SemanticField(field_name="procedure_title"),
                        content_fields=[SemanticField(field_name="text")],
                    ),
                )
            ]
        )

        return SearchIndex(
            name=self._config.index_name,
            fields=fields,
            vector_search=vector_search,
            semantic_search=semantic_search,
        )

    def ensure_index(self) -> None:
        """Create or update the procedure index. Idempotent."""
        if self._index_ready:
            return
        client = self._index_client()
        try:
            client.create_or_update_index(self._build_index_definition())
            self._index_ready = True
            logger.info(
                "AI Search index '%s' ready at %s",
                self._config.index_name,
                self._config.endpoint,
            )
        finally:
            client.close()

    # -- writes ------------------------------------------------------------

    def index(self, procedures: list[Procedure]) -> None:
        """Upload every chunk of every APPROVED procedure.

        Mirrors the security invariant of :meth:`retrieval.HybridRetriever.index`:
        a non-APPROVED procedure raises before anything is written, so a draft can
        never reach the shared corpus (api-contracts §10.2).
        """
        for p in procedures:
            if not is_retrievable(p):
                raise ValueError(
                    f"Procedure '{p.procedure_id}' has status '{p.status.value}' "
                    "and cannot be indexed — only APPROVED procedures are "
                    "retrievable (api-contracts §10.2)."
                )

        self.ensure_index()

        documents: list[dict[str, Any]] = []
        for p in procedures:
            for chunk in chunk_procedure(p):
                documents.append(
                    {
                        "chunk_key": _document_key(chunk.chunk_id),
                        "chunk_id": chunk.chunk_id,
                        "procedure_id": chunk.procedure_id,
                        "procedure_title": chunk.procedure_title,
                        "section": chunk.section,
                        "text": chunk.text,
                        "token_count": chunk.token_count,
                    }
                )

        if not documents:
            return

        client = self._search_client()
        try:
            # Batched because Search caps a single upload request at 1000 documents.
            for start in range(0, len(documents), 500):
                client.merge_or_upload_documents(documents=documents[start : start + 500])
        finally:
            client.close()

        logger.info(
            "Indexed %d chunks from %d approved procedures into '%s'",
            len(documents),
            len(procedures),
            self._config.index_name,
        )

    def delete_procedure(self, procedure_id: str) -> int:
        """Delete every chunk belonging to *procedure_id*.

        Used by the GDPR erasure path: a procedure withdrawn from the corpus must
        stop being retrievable immediately, not at the next full reindex.
        """
        client = self._search_client()
        try:
            hits = client.search(
                search_text="*",
                filter=f"procedure_id eq '{procedure_id}'",
                select=["chunk_key"],
                top=1000,
            )
            keys = [{"chunk_key": h["chunk_key"]} for h in hits]
            if keys:
                client.delete_documents(documents=keys)
            return len(keys)
        finally:
            client.close()

    # -- reads -------------------------------------------------------------

    def search(self, query: str, top_k: int = 5) -> RetrievalResult:
        """Hybrid keyword + vector search with semantic reranking.

        The returned ``ScoredChunk`` carries the semantic reranker score in
        ``semanticScore`` and the BM25 score in ``lexicalScore``; ``fusedScore`` is
        Search's own RRF output. Ranks are positional, because the service returns
        results already fused rather than exposing per-modality rankings.
        """
        from azure.search.documents.models import VectorizableTextQuery

        client = self._search_client()
        try:
            vector_queries = None
            if self._config.foundry_endpoint:
                vector_queries = [
                    VectorizableTextQuery(
                        text=query,
                        k_nearest_neighbors=max(top_k * 2, 10),
                        fields="text_vector",
                    )
                ]

            results = client.search(
                search_text=query,
                vector_queries=vector_queries,
                query_type="semantic",
                semantic_configuration_name=SEMANTIC_CONFIG_NAME,
                top=top_k,
            )
            scored = [
                self._to_scored_chunk(hit, rank)
                for rank, hit in enumerate(results, start=1)
            ]
        finally:
            client.close()

        if not scored:
            return RetrievalResult(
                query=query,
                chunks=[],
                providerUsed=self.provider_used,
                declined=True,
                declineReason="no_grounded_source",
            )

        return RetrievalResult(
            query=query,
            chunks=scored,
            providerUsed=self.provider_used,
            declined=False,
            declineReason=None,
        )

    @staticmethod
    def _to_scored_chunk(hit: Any, rank: int) -> ScoredChunk:
        chunk = Chunk(
            chunk_id=hit.get("chunk_id", ""),
            procedure_id=hit.get("procedure_id", ""),
            procedure_title=hit.get("procedure_title", ""),
            section=hit.get("section", ""),
            text=hit.get("text", ""),
            token_count=int(hit.get("token_count") or 0),
        )
        return ScoredChunk(
            chunk=chunk,
            lexicalRank=rank,
            semanticRank=rank,
            lexicalScore=float(hit.get("@search.score") or 0.0),
            semanticScore=float(hit.get("@search.reranker_score") or 0.0),
            fusedScore=float(hit.get("@search.score") or 0.0),
        )


class LocalProcedureStore:
    """In-memory :class:`ProcedureStore` backed by :class:`HybridRetriever`.

    The offline default and the fallback whenever AI Search is unreachable. Keeping
    the same interface means no caller needs to know which backend is live.
    """

    provider_used = "local-hybrid"

    def __init__(self, embedding_provider: Optional[EmbeddingProvider] = None) -> None:
        self._retriever = HybridRetriever(embedding_provider=embedding_provider)
        self._procedures: dict[str, Procedure] = {}

    def index(self, procedures: list[Procedure]) -> None:
        self._procedures = {p.procedure_id: p for p in procedures}
        self._retriever.index(procedures)

    def search(self, query: str, top_k: int = 5) -> RetrievalResult:
        return self._retriever.retrieve(query, top_k=top_k)

    def delete_procedure(self, procedure_id: str) -> int:
        if procedure_id not in self._procedures:
            return 0
        removed = self._procedures.pop(procedure_id)
        self._retriever.index(list(self._procedures.values()))
        return len(chunk_procedure(removed))


def create_procedure_store(
    embedding_provider: Optional[EmbeddingProvider] = None,
) -> ProcedureStore:
    """Return the AI Search store when it is configured, else the in-memory one.

    Mirrors :func:`adapter_factory.create_agent`: an unreachable or unconfigured
    Azure backend is a degraded mode, never a startup failure, so the demo and the
    offline test suite keep working with no environment at all.
    """
    if os.environ.get(ENV_STORE_MODE, "").lower() == "local":
        logger.info("Procedure store explicitly set to 'local' — using in-memory store")
        return LocalProcedureStore(embedding_provider)

    config = SearchStoreConfig.from_env()
    if config is None:
        logger.info("No %s configured — using in-memory procedure store", ENV_SEARCH_ENDPOINT)
        return LocalProcedureStore(embedding_provider)

    try:
        store = AzureSearchProcedureStore(config)
        store.ensure_index()
        logger.info("Azure AI Search procedure store configured: %s", config.endpoint)
        return store
    except ImportError as exc:
        logger.warning(
            "azure-search-documents not available (%s) — falling back to the in-memory "
            "procedure store. Install the 'azure' extra from the approved feed to "
            "enable the shared corpus.",
            exc,
        )
        return LocalProcedureStore(embedding_provider)
    except Exception as exc:
        logger.warning(
            "Failed to initialize the AI Search procedure store (%s) — falling back "
            "to the in-memory store",
            exc,
        )
        return LocalProcedureStore(embedding_provider)
