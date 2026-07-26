"""Adapter from the BFF boundary to the Copilot chat service.

Mirrors :mod:`knowledge_adapter`: the orchestrator package is injected onto
``sys.path`` once, imports stay lazy so the BFF has no hard build-time coupling,
and domain errors are mapped onto the BFF's ``ApiError`` envelope so routes stay
free of orchestrator types.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from .contracts import ErrorCode
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
        return response.to_view()
