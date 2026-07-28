"""Backend selection for the Copilot "Online search" toggle.

Ticking "Online search" has always meant "you may also use clearly-labelled public
context". What that resolves to at runtime now depends on ``ONLINE_SEARCH_MODE``:

``web_iq``
    Foundry IQ's *web knowledge source*, queried through the same knowledge base the
    procedure agent uses. This is the preferred backend: retrieval, reranking and
    citation happen inside the agentic pipeline, results are domain-restricted, and
    there is no second grounding path to keep consistent.

``web_search``
    The Agent Service ``web_search`` tool. The fallback when Foundry IQ is not
    available in the region or the knowledge base has not been provisioned. It
    returns web results directly to the agent rather than through the knowledge base.

``offline`` (default)
    The curated in-repo corpus in :mod:`knowledge_orchestrator.copilot.online`.

The default is ``offline`` and that is a deliberate compliance position, not
timidity. Both web backends are First Party Consumption Services: the Microsoft DPA
does not cover them, and query content — which for a plant assistant can itself
disclose process detail — leaves the Azure compliance and geographic boundary. So
the live backends must be switched on explicitly, and whichever backend answered is
recorded in the turn trace so an auditor can tell after the fact.

Whatever the mode, this module returns plain :class:`OnlineHit` values, so the
agent's grounding assembly and the ONLINE source labelling are unchanged.
"""

from __future__ import annotations

import logging
from typing import Optional, Protocol

from ..foundry_iq import (
    ONLINE_MODE_OFFLINE,
    ONLINE_MODE_WEB_IQ,
    ONLINE_MODE_WEB_SEARCH,
    KnowledgeBaseConfig,
    knowledge_base_config_from_env,
    online_search_mode,
)
from .context import ResolvedContext
from .models import DEFAULT_LANGUAGE
from .online import MAX_HITS, OnlineHit, online_context

logger = logging.getLogger(__name__)


class OnlineSearchProvider(Protocol):
    """Contract every online-search backend honours."""

    mode: str

    def search(
        self,
        resolved: ResolvedContext,
        question: str,
        language: str = DEFAULT_LANGUAGE,
        *,
        limit: int = MAX_HITS,
    ) -> list[OnlineHit]: ...


class CuratedOnlineSearchProvider:
    """The offline default: rank the curated public-context corpus."""

    mode = ONLINE_MODE_OFFLINE

    def search(
        self,
        resolved: ResolvedContext,
        question: str,
        language: str = DEFAULT_LANGUAGE,
        *,
        limit: int = MAX_HITS,
    ) -> list[OnlineHit]:
        return online_context(resolved, question, language, limit=limit)


class WebIQOnlineSearchProvider:
    """Queries the Foundry IQ web knowledge source via the knowledge base.

    Retrieval runs against the knowledge base rather than a raw search endpoint, so
    the web source goes through the same query planning, reranking and citation the
    procedure source does — the operator gets one consistent citation style whether
    an answer came from a procedure or from a public standard.

    Any failure falls through to the curated corpus: a public-context lookup is an
    enhancement, and losing it must never cost the operator their answer.
    """

    mode = ONLINE_MODE_WEB_IQ

    def __init__(
        self,
        config: KnowledgeBaseConfig,
        credential: object = None,
        fallback: Optional[OnlineSearchProvider] = None,
    ) -> None:
        self._config = config
        self._credential = credential
        self._fallback = fallback or CuratedOnlineSearchProvider()

    def _get_credential(self) -> object:
        if self._credential is None:
            from azure.identity import DefaultAzureCredential

            self._credential = DefaultAzureCredential()
        return self._credential

    def _retrieve(self, question: str, limit: int) -> list[OnlineHit]:  # pragma: no cover - requires network
        from azure.search.documents.indexes import SearchIndexClient

        from ..foundry_iq import KNOWLEDGE_API_VERSION, WEB_SOURCE_NAME

        client = SearchIndexClient(
            endpoint=self._config.search_endpoint,
            credential=self._get_credential(),
            api_version=KNOWLEDGE_API_VERSION,
        )
        try:
            response = client.retrieve(
                knowledge_base_name=self._config.knowledge_base_name,
                retrieval_request={
                    "messages": [
                        {"role": "user", "content": [{"type": "text", "text": question}]}
                    ],
                    # Restricted to the web source: the procedure source is already
                    # retrieved separately and grounded with its own citation rules.
                    "knowledgeSourceParams": [
                        {"knowledgeSourceName": WEB_SOURCE_NAME, "kind": "web"}
                    ],
                },
            )
        finally:
            client.close()

        return _hits_from_references(response, limit)

    def search(
        self,
        resolved: ResolvedContext,
        question: str,
        language: str = DEFAULT_LANGUAGE,
        *,
        limit: int = MAX_HITS,
    ) -> list[OnlineHit]:
        try:
            hits = self._retrieve(question, limit)
        except Exception as exc:
            logger.warning(
                "Foundry IQ web knowledge source unavailable (%s) — falling back to "
                "the curated public-context corpus",
                exc,
            )
            return self._fallback.search(resolved, question, language, limit=limit)

        if not hits:
            return self._fallback.search(resolved, question, language, limit=limit)
        return hits


class WebSearchToolProvider(WebIQOnlineSearchProvider):
    """Agent Service ``web_search`` tool backend.

    Used where Foundry IQ is unavailable. It shares the fallback behaviour of its
    parent but reaches the web through the Agent Service tool rather than a knowledge
    source, so results arrive without knowledge-base reranking and are marked as such
    in the trace.
    """

    mode = ONLINE_MODE_WEB_SEARCH

    def _retrieve(self, question: str, limit: int) -> list[OnlineHit]:  # pragma: no cover - requires network
        from ..agent_service import run_web_search

        return run_web_search(question, limit=limit)


def _hits_from_references(response: object, limit: int) -> list[OnlineHit]:
    """Normalise a knowledge-base retrieval response into :class:`OnlineHit`.

    Defensive about the response shape because it is preview API surface: anything
    unrecognised yields no hits, which degrades to the curated corpus rather than
    raising into an operator's chat turn.
    """
    references = getattr(response, "references", None)
    if references is None and isinstance(response, dict):
        references = response.get("references")
    if not references:
        return []

    hits: list[OnlineHit] = []
    for index, ref in enumerate(references):
        get = ref.get if isinstance(ref, dict) else lambda k, d=None: getattr(ref, k, d)
        url = get("url") or get("sourceUrl") or ""
        title = get("title") or url or f"Web result {index + 1}"
        snippet = get("content") or get("snippet") or ""
        if not snippet:
            continue
        hits.append(
            OnlineHit(
                source_id=f"web-{index + 1}",
                title=str(title),
                snippet=str(snippet)[:600],
                url=str(url),
            )
        )
        if len(hits) >= limit:
            break
    return hits


def create_online_search_provider() -> OnlineSearchProvider:
    """Select the online-search backend from the environment.

    Mirrors every other adapter factory in the service: an unconfigured or
    unreachable cloud backend is a logged degradation to the curated corpus, never a
    startup failure.
    """
    mode = online_search_mode()
    if mode == ONLINE_MODE_OFFLINE:
        return CuratedOnlineSearchProvider()

    config = knowledge_base_config_from_env()
    if config is None:
        logger.warning(
            "ONLINE_SEARCH_MODE=%s but AI Search is not configured — online search "
            "stays on the curated corpus",
            mode,
        )
        return CuratedOnlineSearchProvider()

    provider_cls = (
        WebIQOnlineSearchProvider if mode == ONLINE_MODE_WEB_IQ else WebSearchToolProvider
    )
    logger.warning(
        "Online search backend '%s' enabled. Queries sent to it leave the Azure "
        "compliance and geographic boundary and are not covered by the Microsoft DPA.",
        mode,
    )
    return provider_cls(config)
