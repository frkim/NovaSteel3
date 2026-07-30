"""Hybrid grounded RAG retriever for the APPROVED procedure corpus.

Combines BM25 lexical ranking with cosine semantic similarity via Reciprocal Rank
Fusion (RRF). RRF is the defensible fusion choice: it is scale-free and requires
no score normalization — only the per-modality ranks matter, so BM25 scores and
cosine similarities are fused without any calibration.

Security invariant (api-contracts §10.2): only APPROVED procedures may be indexed;
attempting to index any other status raises immediately.
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import re
from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

from .foundry_endpoints import normalize_endpoint, openai_v1_url, token_scope
from .grounding import GroundingError
from .models import Procedure
from .procedure_workflow import is_retrievable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stop words and tokenization helpers
# ---------------------------------------------------------------------------

_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "shall", "can", "not", "no", "if",
        "this", "that", "it", "its", "as", "up", "out", "than", "then", "so",
        "also", "into", "about", "any", "all", "each", "which", "who", "what",
        "when", "where", "how", "such", "more", "other", "must", "need",
    }
)

_TOKEN_RE = re.compile(r"\b[a-z]+\b")


def _stem(word: str) -> str:
    """Minimal suffix stripping for consistent lexical normalization.

    Longer suffixes are checked first to avoid double-stripping. The word must
    be at least 4 characters after stripping to be valid.
    """
    for suffix in (
        "ings", "ing", "tions", "tion", "edly", "ally", "ers", "ed", "ly",
        "er", "est", "es", "s",
    ):
        min_len = len(suffix) + 3
        if len(word) > min_len and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _tokenize(text: str) -> list[str]:
    """Lowercase, alphabetic-only, stop-word-filtered, stemmed token list."""
    raw = _TOKEN_RE.findall(text.lower())
    return [_stem(t) for t in raw if t not in _STOP_WORDS]


# ---------------------------------------------------------------------------
# Chunk dataclass
# ---------------------------------------------------------------------------

_OVERLAP_CHARS = 80  # characters of preceding section included as overlap


@dataclass(frozen=True)
class Chunk:
    """A single retrievable text unit derived from one section of a Procedure."""

    chunk_id: str       # stable: "{procedure_id}#c{n}"
    procedure_id: str
    procedure_title: str
    section: str        # observation | recommended_check | rationale | safety_boundary
    text: str           # retrieval text (title prefix + optional overlap + section body)
    token_count: int    # approximate whitespace-based token count


def chunk_procedure(procedure: Procedure) -> list[Chunk]:
    """Split a Procedure into retrievable Chunks on section boundaries.

    Each chunk is prefixed with the procedure title so queries about a topic
    surface the procedure name even when querying a sub-section. A small
    character overlap from the previous section is prepended to preserve
    cross-section context; chunk ids are deterministic: ``{proc_id}#c{n}``.
    """
    sections = [
        ("observation", procedure.knowledge.observation),
        ("recommended_check", procedure.knowledge.recommended_check),
        ("rationale", procedure.knowledge.rationale),
        ("safety_boundary", procedure.knowledge.safety_boundary),
    ]

    chunks: list[Chunk] = []
    prev_body = ""
    for n, (section_name, body) in enumerate(sections):
        overlap = prev_body[-_OVERLAP_CHARS:].strip() if prev_body else ""
        text = (
            f"{procedure.title}: {overlap} {body}".strip()
            if overlap
            else f"{procedure.title}: {body}"
        )
        chunks.append(
            Chunk(
                chunk_id=f"{procedure.procedure_id}#c{n}",
                procedure_id=procedure.procedure_id,
                procedure_title=procedure.title,
                section=section_name,
                text=text,
                token_count=len(text.split()),
            )
        )
        prev_body = body

    return chunks


# ---------------------------------------------------------------------------
# BM25 index  (k1=1.5, b=0.75 — Robertson/Sparck Jones parameters)
# ---------------------------------------------------------------------------


class _BM25Index:
    """BM25 inverted index over a fixed corpus of tokenized texts.

    k1=1.5 controls term-frequency saturation; b=0.75 controls document-length
    normalisation. Both are the standard empirically validated defaults.
    """

    k1: float = 1.5
    b: float = 0.75

    def __init__(self) -> None:
        self._chunk_tokens: list[list[str]] = []
        self._doc_freq: dict[str, int] = {}
        self._avgdl: float = 0.0

    def fit(self, texts: list[str]) -> None:
        """Build the index from a list of document texts."""
        self._chunk_tokens = [_tokenize(t) for t in texts]
        n = len(self._chunk_tokens)

        self._doc_freq = {}
        for tokens in self._chunk_tokens:
            for term in set(tokens):
                self._doc_freq[term] = self._doc_freq.get(term, 0) + 1

        total_tokens = sum(len(t) for t in self._chunk_tokens)
        self._avgdl = total_tokens / n if n > 0 else 0.0

    def scores(self, query: str) -> list[float]:
        """Return a BM25 score for every indexed document given ``query``."""
        q_tokens = _tokenize(query)
        n = len(self._chunk_tokens)
        result = [0.0] * n

        for term in q_tokens:
            if term not in self._doc_freq:
                continue
            df = self._doc_freq[term]
            # Robertson's IDF (always ≥ 0; rare terms → higher weight)
            idf = math.log((n - df + 0.5) / (df + 0.5) + 1.0)
            for i, tokens in enumerate(self._chunk_tokens):
                tf = tokens.count(term)
                if tf == 0:
                    continue
                dl = len(tokens)
                denom = tf + self.k1 * (
                    1.0 - self.b + self.b * dl / max(self._avgdl, 1e-9)
                )
                tf_norm = (tf * (self.k1 + 1.0)) / denom
                result[i] += idf * tf_norm

        return result


# ---------------------------------------------------------------------------
# Embedding providers
# ---------------------------------------------------------------------------


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for text embedding backends used in semantic retrieval."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one L2-normalised float vector per input text."""
        ...


class HashingEmbeddingProvider:
    """Offline, deterministic embedding via a character n-gram hashing trick.

    Projects each text into a 256-dimensional space using a seeded bag-of-ngrams
    representation (n ∈ {2, 3, 4}), then L2-normalises the result. Uses
    ``hashlib.sha256`` — not Python's built-in ``hash()`` — so the output is
    identical across interpreter restarts and PYTHONHASHSEED settings.

    Properties guaranteed:
    * Same text ⇒ identical vector (deterministic)
    * Each vector has unit L2 norm
    * Cosine similarity of a vector with itself == 1.0 exactly
    """

    DIM: int = 256
    _NGRAM_SIZES: tuple[int, ...] = (2, 3, 4)
    _SEED: bytes = b"novasteel-hashing-embed-v1"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.DIM
        lowered = text.lower()
        for n in self._NGRAM_SIZES:
            for i in range(len(lowered) - n + 1):
                ngram = lowered[i : i + n].encode("utf-8")
                digest = hashlib.sha256(self._SEED + ngram).digest()
                # Dimension from first 2 bytes; sign from third byte LSB.
                dim = int.from_bytes(digest[:2], "big") % self.DIM
                sign = 1.0 if digest[2] & 1 else -1.0
                vec[dim] += sign
        # L2-normalise so cosine similarity reduces to a dot product.
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            vec = [x / norm for x in vec]
        return vec


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors (handles non-normalised inputs)."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


# Environment variable names (mirroring azure_foundry.py)
_ENV_ENDPOINT = "FOUNDRY_ENDPOINT"
_ENV_EMBED_DEPLOYMENT = "FOUNDRY_EMBED_DEPLOYMENT"
_DEFAULT_EMBED_DEPLOYMENT = "text-embedding-3-large"


class AzureOpenAIEmbeddingProvider:
    """Foundry embedding provider (mirrors AzureFoundryKnowledgeAgent).

    Calls the Foundry project model's versionless OpenAI v1 route
    (``/openai/v1/embeddings``), not the classic dated deployments path — see
    :mod:`knowledge_orchestrator.foundry_endpoints`.

    Authenticates with ``DefaultAzureCredential`` (managed identity / developer
    identity). Falls back to :class:`HashingEmbeddingProvider` on any failure
    (missing endpoint, auth error, network error). The ``provider_used`` attribute
    records which backend was actually used for the most recent call.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None,
        credential=None,
    ) -> None:
        self._endpoint = normalize_endpoint(
            endpoint or os.environ.get(_ENV_ENDPOINT, "")
        )
        self._deployment = deployment or os.environ.get(
            _ENV_EMBED_DEPLOYMENT, _DEFAULT_EMBED_DEPLOYMENT
        )
        self._credential = credential
        self._fallback = HashingEmbeddingProvider()
        self.provider_used: str = "AzureOpenAIEmbeddingProvider"

    def _get_token(self) -> str:  # pragma: no cover — requires azure-identity
        credential = self._credential or _default_azure_credential()
        return credential.get_token(token_scope()).token

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self._endpoint:
            logger.warning(
                "FOUNDRY_ENDPOINT not set; falling back to HashingEmbeddingProvider"
            )
            self.provider_used = "HashingEmbeddingProvider"
            return self._fallback.embed(texts)
        try:
            result = self._azure_embed(texts)
            self.provider_used = "AzureOpenAIEmbeddingProvider"
            return result
        except Exception as exc:
            logger.warning(
                "Azure embedding call failed (%s); falling back to HashingEmbeddingProvider",
                exc,
            )
            self.provider_used = "HashingEmbeddingProvider"
            return self._fallback.embed(texts)

    def _azure_embed(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover
        import requests  # lazily imported — zero cloud deps for tests

        url = openai_v1_url(self._endpoint, "embeddings")
        token = self._get_token()
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"input": texts, "model": self._deployment},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        ordered = sorted(data["data"], key=lambda x: x["index"])
        return [e["embedding"] for e in ordered]


def _default_azure_credential():  # pragma: no cover — requires azure-identity
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()


# ---------------------------------------------------------------------------
# Retrieval results
# ---------------------------------------------------------------------------


@dataclass
class ScoredChunk:
    """A chunk annotated with per-modality and fused retrieval scores."""

    chunk: Chunk
    lexicalRank: int     # 1-based position in BM25 ranking
    semanticRank: int    # 1-based position in cosine ranking
    lexicalScore: float  # raw BM25 score
    semanticScore: float # cosine similarity
    fusedScore: float    # RRF score (the sort key)


@dataclass
class RetrievalResult:
    """The outcome of a single retrieval query."""

    query: str
    chunks: list[ScoredChunk]   # empty on decline
    providerUsed: str
    declined: bool
    declineReason: Optional[str]  # "no_grounded_source" | None


# ---------------------------------------------------------------------------
# Hybrid retriever
# ---------------------------------------------------------------------------

_RRF_K = 60  # RRF damping constant — standard choice; larger → blunter fusion


class HybridRetriever:
    """Hybrid BM25 + cosine retriever over an APPROVED procedure corpus.

    Security invariant: ``index()`` raises :class:`ValueError` for any non-APPROVED
    procedure (``procedure_workflow.is_retrievable`` check).  Only indexed chunks are
    ever surfaced; drafts are unreachable by construction.
    """

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        min_score: float = 0.01,
    ) -> None:
        self._emb = embedding_provider or HashingEmbeddingProvider()
        self._min_score = min_score
        self._chunks: list[Chunk] = []
        self._bm25 = _BM25Index()
        self._embeddings: list[list[float]] = []

    def index(self, procedures: list[Procedure]) -> None:
        """Build or rebuild the retrieval index from a list of APPROVED procedures.

        Raises :class:`ValueError` if any procedure is not APPROVED.
        """
        for p in procedures:
            if not is_retrievable(p):
                raise ValueError(
                    f"Procedure '{p.procedure_id}' has status '{p.status.value}' "
                    "and cannot be indexed — only APPROVED procedures are "
                    "retrievable (api-contracts §10.2)."
                )

        self._chunks = []
        for p in procedures:
            self._chunks.extend(chunk_procedure(p))

        if not self._chunks:
            return

        texts = [c.text for c in self._chunks]
        self._bm25.fit(texts)
        self._embeddings = self._emb.embed(texts)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_score: Optional[float] = None,
    ) -> RetrievalResult:
        """Return the top-k most relevant chunks for *query*.

        Returns ``declined=True`` with zero chunks when the index is empty or no
        chunk clears the relevance floor, so callers can render the canonical
        "I don't have an approved source for that" response.
        """
        threshold = min_score if min_score is not None else self._min_score
        provider_used = getattr(self._emb, "provider_used", type(self._emb).__name__)

        if not self._chunks:
            return RetrievalResult(
                query=query,
                chunks=[],
                providerUsed=provider_used,
                declined=True,
                declineReason="no_grounded_source",
            )

        # --- Lexical ranking (BM25) ---
        lex_scores = self._bm25.scores(query)
        lex_order = sorted(range(len(lex_scores)), key=lambda i: lex_scores[i], reverse=True)
        lex_rank: dict[int, int] = {idx: rank + 1 for rank, idx in enumerate(lex_order)}

        # --- Semantic ranking (cosine) ---
        q_vec = self._emb.embed([query])[0]
        sem_scores = [_cosine(q_vec, e) for e in self._embeddings]
        sem_order = sorted(range(len(sem_scores)), key=lambda i: sem_scores[i], reverse=True)
        sem_rank: dict[int, int] = {idx: rank + 1 for rank, idx in enumerate(sem_order)}

        # --- RRF fusion ---
        n = len(self._chunks)
        rrf: list[tuple[int, float]] = []
        for i in range(n):
            lr = lex_rank.get(i, n + 1)
            sr = sem_rank.get(i, n + 1)
            fused = 1.0 / (_RRF_K + lr) + 1.0 / (_RRF_K + sr)
            rrf.append((i, fused))
        rrf.sort(key=lambda x: x[1], reverse=True)

        # Update provider_used (may have changed if Azure fell back during embed)
        provider_used = getattr(self._emb, "provider_used", type(self._emb).__name__)

        # --- Apply threshold and top_k ---
        scored: list[ScoredChunk] = []
        for i, fused_score in rrf[:top_k]:
            if fused_score < threshold:
                break
            scored.append(
                ScoredChunk(
                    chunk=self._chunks[i],
                    lexicalRank=lex_rank[i],
                    semanticRank=sem_rank[i],
                    lexicalScore=lex_scores[i],
                    semanticScore=sem_scores[i],
                    fusedScore=fused_score,
                )
            )

        if not scored:
            return RetrievalResult(
                query=query,
                chunks=[],
                providerUsed=provider_used,
                declined=True,
                declineReason="no_grounded_source",
            )

        return RetrievalResult(
            query=query,
            chunks=scored,
            providerUsed=provider_used,
            declined=False,
            declineReason=None,
        )


# ---------------------------------------------------------------------------
# Citation enforcement
# ---------------------------------------------------------------------------

# Matches [[PROC-APPROVED-0001#c2]] or [[PROC-APPROVED-0001]] (procedure-level).
# Procedure ids are ALL_CAPS with hyphens; chunk suffix is #c<integer>.
CITATION_PATTERN: re.Pattern[str] = re.compile(
    r"\[\[([A-Z][A-Z0-9\-]+(?:#c\d+)?)\]\]"
)

# Sentences containing any of these meta-phrases are not subject to citation
# enforcement (they are system-generated decline or routing messages).
_META_PHRASES: frozenset[str] = frozenset(
    {
        "i don't have an approved source",
        "i do not have an approved source",
        "i cannot answer",
        "i was unable to find",
        "no approved procedure",
        "i don't know",
        "please consult an authorized procedure",
    }
)

# Factual-claim threshold: sentences at or above this word count that are not
# questions and not meta-phrases must carry at least one citation marker.
_FACTUAL_CLAIM_MIN_WORDS: int = 8

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


class CitationError(GroundingError):
    """Raised when an AI answer fails inline-citation enforcement.

    Inherits from :class:`GroundingError` so existing callers that catch
    ``GroundingError`` automatically handle citation violations too.
    """


def extract_citations(answer: str) -> list[str]:
    """Return a list of all citation ids found in *answer* (deduplicated, ordered)."""
    seen: dict[str, None] = {}
    for m in CITATION_PATTERN.finditer(answer):
        seen[m.group(1)] = None
    return list(seen)


def _is_factual_claim(sentence: str) -> bool:
    """Return True if *sentence* is long enough and non-question to require a citation."""
    s = sentence.strip()
    if not s or s.endswith("?"):
        return False
    if len(s.split()) < _FACTUAL_CLAIM_MIN_WORDS:
        return False
    s_lower = s.lower()
    if any(phrase in s_lower for phrase in _META_PHRASES):
        return False
    return True


def enforce_answer_citations(
    answer: str,
    allowed_chunk_ids: set[str],
) -> None:
    """Enforce that *answer* is properly grounded with inline citation markers.

    Raises :class:`CitationError` when:
    * The answer is non-empty but contains no ``[[...]]`` citation markers.
    * A citation marker references a chunk id (or procedure id) not in
      *allowed_chunk_ids* (i.e. was not retrieved).
    * Any sentence that constitutes a factual claim carries no citation marker.

    Decline sentences (those containing a ``_META_PHRASE``) are exempt from all
    citation requirements, allowing ``build_decline_answer`` output to pass freely.
    """
    if not answer or not answer.strip():
        return  # empty answers have no citation obligations

    # Allow decline / routing answers through without citations.
    answer_lower = answer.lower()
    if any(phrase in answer_lower for phrase in _META_PHRASES):
        return

    reasons: list[str] = []
    cited_ids = extract_citations(answer)

    if not cited_ids:
        reasons.append("answer contains no [[...]] citation markers")
    else:
        # Build the set of procedure ids that have at least one retrieved chunk.
        allowed_proc_ids = {cid.split("#")[0] for cid in allowed_chunk_ids}

        for cid in cited_ids:
            if "#c" in cid:
                # Specific chunk reference — must be an exact match.
                if cid not in allowed_chunk_ids:
                    reasons.append(
                        f"citation '[[{cid}]]' references a chunk that was not retrieved"
                    )
            else:
                # Procedure-level reference — any retrieved chunk from that procedure qualifies.
                if cid not in allowed_proc_ids:
                    reasons.append(
                        f"citation '[[{cid}]]' has no retrieved chunks in this result"
                    )

    # Per-sentence check: every factual-claim sentence must carry a citation.
    for sent in _SENTENCE_SPLIT_RE.split(answer):
        if _is_factual_claim(sent) and not CITATION_PATTERN.search(sent):
            reasons.append(
                f"factual sentence lacks an inline citation: "
                f"'{sent[:100]}{'...' if len(sent) > 100 else ''}'"
            )
            break  # one report is enough; avoid noisy lists

    if reasons:
        raise CitationError(reasons)


# ---------------------------------------------------------------------------
# Decline path
# ---------------------------------------------------------------------------

_DECLINE_TEMPLATES: dict[str, str] = {
    "en": (
        "I don't have an approved source for that question. "
        "Please consult an authorized procedure or contact engineering."
    ),
}


def build_decline_answer(reason: str, language: str = "en") -> str:
    """Return the canonical decline text for *reason*.

    The returned string is allow-listed in :func:`enforce_answer_citations` so
    it passes citation checks without any ``[[...]]`` markers. Callers should
    render this verbatim rather than constructing ad-hoc refusal text.
    """
    return _DECLINE_TEMPLATES.get(language, _DECLINE_TEMPLATES["en"])
