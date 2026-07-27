"""Adapter from the BFF boundary to the Copilot chat service.

Mirrors :mod:`knowledge_adapter`: the orchestrator package is injected onto
``sys.path`` once, imports stay lazy so the BFF has no hard build-time coupling,
and domain errors are mapped onto the BFF's ``ApiError`` envelope so routes stay
free of orchestrator types.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

from .contracts import ErrorCode
from .copilot_online_corpus import CORPUS_LABEL, RETRIEVAL_DATE, search_offline_corpus
from .copilot_steel_corpus import search_steel_corpus
from .errors import ApiError

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[4]
_KNOWLEDGE_SRC = _ROOT / "services" / "knowledge-orchestrator" / "src"


class CopilotAdapter:
    """Delegates screen-aware chat, glossary and conversation history."""

    def __init__(self) -> None:
        if str(_KNOWLEDGE_SRC) not in sys.path:
            sys.path.insert(0, str(_KNOWLEDGE_SRC))
        try:
            from knowledge_orchestrator.copilot import (
                ConversationNotFoundError,
                CopilotService,
                CopilotValidationError,
                ScreenContext,
            )
        except ImportError as exc:  # pragma: no cover - repository integration failure
            raise RuntimeError("knowledge-orchestrator is required by the BFF.") from exc

        self._service = CopilotService()
        self._screen_context = ScreenContext
        self._not_found = ConversationNotFoundError
        self._validation = CopilotValidationError

    # -- read-only surface --------------------------------------------------

    def suggestions(self, *, section: str | None, language: str | None) -> dict[str, Any]:
        return self._service.suggestions(section, language).to_view()

    def glossary(
        self,
        *,
        query: str | None,
        language: str | None,
        section: str | None,
        limit: int,
    ) -> dict[str, Any]:
        entries = self._service.glossary(
            query, language, section=section, limit=limit
        )
        return {
            "query": (query or "").strip(),
            "language": entries[0].language if entries else (language or "en")[:2].lower(),
            "entries": [entry.to_view() for entry in entries],
        }

    def list_conversations(self, *, owner: str) -> dict[str, Any]:
        return {
            "conversations": [
                conversation.to_summary()
                for conversation in self._service.list_conversations(owner)
            ]
        }

    def get_conversation(self, *, owner: str, conversation_id: str) -> dict[str, Any]:
        try:
            return self._service.get_conversation(owner, conversation_id).to_view()
        except self._not_found as exc:
            raise ApiError(404, ErrorCode.NOT_FOUND, str(exc)) from exc

    def delete_conversation(self, *, owner: str, conversation_id: str) -> None:
        try:
            self._service.delete_conversation(owner, conversation_id)
        except self._not_found as exc:
            raise ApiError(404, ErrorCode.NOT_FOUND, str(exc)) from exc

    def delete_all_conversations(self, *, owner: str) -> int:
        """Delete every conversation for *owner*. Returns the count removed."""
        conversations = self._service.list_conversations(owner)
        count = 0
        for conv in conversations:
            try:
                self._service.delete_conversation(owner, conv.conversation_id)
                count += 1
            except self._not_found:
                pass
        return count

    def glossary_online_fallback(
        self,
        *,
        query: str,
        language: str | None,
    ) -> dict[str, Any]:
        """Search for a glossary term using the online corpus (or offline fallback)."""
        lang = (language or "en")[:2].lower()
        live_endpoint = os.environ.get("COPILOT_SEARCH_ENDPOINT")
        if live_endpoint:
            # TODO: call the real search endpoint when available
            pass
        # Offline fallback: search both corpora
        results = search_offline_corpus(query)
        steel_results = search_steel_corpus(query)
        items = []
        for r in results:
            items.append({
                "title": r.title,
                "snippet": r.snippet,
                "url": r.url,
                "publishedDate": r.published,
                "retrievedAt": RETRIEVAL_DATE,
                "kind": "online",
                "offlineCorpus": True,
            })
        for r in steel_results:
            items.append({
                "title": r.title,
                "snippet": r.content[:200],
                "url": "",
                "publishedDate": "",
                "retrievedAt": "",
                "kind": "knowledge",
                "offlineCorpus": True,
            })
        return {
            "query": query,
            "language": lang,
            "results": items,
            "offlineCorpus": not bool(live_endpoint),
            "corpusLabel": CORPUS_LABEL if not live_endpoint else None,
        }

    @property
    def conversation_store(self) -> Any:
        """Exposes the store so the privacy adapter can erase subject chat history."""
        return self._service.conversation_store

    # -- chat ---------------------------------------------------------------

    def chat(
        self,
        *,
        owner: str,
        question: str,
        language: str | None,
        reasoning: str | None,
        online_search: bool,
        temporary: bool,
        conversation_id: str | None,
        context: dict[str, Any] | None,
        correlation_id: str,
    ) -> dict[str, Any]:
        screen = context or {}
        try:
            response = self._service.chat(
                owner=owner,
                question=question,
                language=language,
                reasoning=reasoning,
                online_search=online_search,
                temporary=temporary,
                conversation_id=conversation_id,
                context=self._screen_context(
                    site=str(screen.get("site") or ""),
                    section=str(screen.get("section") or ""),
                    sub_view=str(screen.get("subView") or ""),
                    persona=str(screen.get("persona") or ""),
                ),
            )
        except self._validation as exc:
            raise ApiError(400, ErrorCode.VALIDATION_ERROR, str(exc)) from exc
        except self._not_found as exc:
            raise ApiError(404, ErrorCode.NOT_FOUND, str(exc)) from exc

        logger.info(
            "copilot chat answered correlation_id=%s section=%s tier=%s",
            correlation_id,
            screen.get("section") or "-",
            response.resolved_reasoning.value,
        )
        view = response.to_view()

        # Post-processing: inject supplementary online corpus sources
        if online_search and not os.environ.get("COPILOT_SEARCH_ENDPOINT"):
            extra = search_offline_corpus(question)
            for item in extra:
                view["answer"]["sources"].append({
                    "sourceId": item.source_id,
                    "title": item.title,
                    "kind": "online",
                    "snippet": item.snippet,
                    "url": item.url,
                    "publishedDate": item.published,
                    "retrievedAt": RETRIEVAL_DATE,
                    "offlineCorpus": True,
                    "corpusLabel": CORPUS_LABEL,
                })

        # Post-processing: inject steel corpus when no screen context (general mode)
        section_val = str(screen.get("section") or "")
        if not section_val or section_val == "-":
            extra_steel = search_steel_corpus(question)
            for item in extra_steel:
                view["answer"]["sources"].append({
                    "sourceId": item.entry_id,
                    "title": item.title,
                    "kind": "knowledge",
                    "snippet": item.content[:200],
                    "url": "",
                    "publishedDate": "",
                    "retrievedAt": "",
                    "offlineCorpus": True,
                })

        return view
