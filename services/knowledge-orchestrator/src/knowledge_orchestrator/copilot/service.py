"""Service layer for the Copilot chat assistant.

Owns everything the transport should not: input validation, ``auto`` reasoning
resolution, agent selection, conversation persistence and the view models the
BFF serialises. The FastAPI layer stays a thin adapter over this.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from .agents import CopilotChatAgent, create_chat_agents
from .context import resolve as resolve_context
from .glossary import GlossaryEntry, all_entries, search
from .models import (
    ChatMessage,
    ChatTurnRequest,
    Conversation,
    MessageRole,
    ReasoningTier,
    ScreenContext,
    normalize_language,
)
from .store import ConversationStore, derive_title, new_id, user_message
from .suggestions import SuggestionSet, suggestions_for

logger = logging.getLogger(__name__)

MAX_QUESTION_LENGTH = 1500
MAX_HISTORY_TURNS = 8

# Wording that signals a question worth spending a reasoning model on when the
# user leaves the selector on "Auto". Covers the five supported languages.
_HIGH_EFFORT_MARKERS = frozenset(
    {
        "why", "compare", "comparison", "trade", "tradeoff", "trade-off", "simulate",
        "scenario", "impact", "explain", "difference", "root", "cause", "should",
        "pourquoi", "comparer", "comparaison", "arbitrage", "simuler", "scenario",
        "impact", "expliquer", "difference", "cause", "racine", "devrais",
        "warum", "vergleichen", "vergleich", "abwagung", "simulieren", "szenario",
        "auswirkung", "erklaren", "unterschied", "ursache", "sollte",
        "waarom", "vergelijken", "vergelijking", "afweging", "simuleren", "scenario",
        "impact", "uitleggen", "verschil", "oorzaak", "moet",
        "por", "que", "comparar", "comparacion", "compensacion", "simular",
        "escenario", "impacto", "explicar", "diferencia", "causa", "raiz", "deberia",
    }
)
AUTO_LENGTH_THRESHOLD = 120


class CopilotValidationError(ValueError):
    """Raised for a malformed chat request."""

    def __init__(self, message: str, *, field: str = ""):
        super().__init__(message)
        self.field = field


@dataclass(frozen=True)
class ChatResponse:
    """Everything the panel needs to render one completed turn."""

    conversation: Conversation
    question: ChatMessage
    answer: ChatMessage
    resolved_reasoning: ReasoningTier
    resolved_concepts: tuple[str, ...]
    online_search_used: bool
    persisted: bool

    def to_view(self) -> dict[str, object]:
        return {
            "conversationId": self.conversation.conversation_id,
            "title": self.conversation.title,
            "language": self.conversation.language,
            "temporary": self.conversation.temporary,
            "persisted": self.persisted,
            "resolvedReasoning": self.resolved_reasoning.value,
            "resolvedConcepts": list(self.resolved_concepts),
            "onlineSearchUsed": self.online_search_used,
            "question": self.question.to_view(),
            "answer": self.answer.to_view(),
        }


def resolve_auto_tier(question: str) -> ReasoningTier:
    """Decide which tier ``auto`` maps to.

    Deliberately transparent rather than clever: a long question, or one that
    asks *why* / *compare* / *what if*, gets the reasoning deployment. The
    resolved tier is echoed back to the UI so the choice is never hidden.
    """
    text = (question or "").strip()
    if len(text) >= AUTO_LENGTH_THRESHOLD:
        return ReasoningTier.HIGH
    words = {word.strip("?!.,;:").lower() for word in text.split()}
    if words & _HIGH_EFFORT_MARKERS:
        return ReasoningTier.HIGH
    return ReasoningTier.DEFAULT


class CopilotService:
    """Application service behind the ``/v1/copilot/*`` endpoints."""

    def __init__(
        self,
        agents: Optional[dict[ReasoningTier, CopilotChatAgent]] = None,
        store: Optional[ConversationStore] = None,
    ):
        self._agents = agents or create_chat_agents()
        self._store = store or ConversationStore()

    # -- suggestions & glossary -------------------------------------------

    def suggestions(self, section: str | None, language: str | None) -> SuggestionSet:
        return suggestions_for(section, language)

    def glossary(
        self,
        query: str | None,
        language: str | None,
        *,
        section: str | None = None,
        limit: int = 8,
    ) -> list[GlossaryEntry]:
        """Search the glossary, or list every term when the query is empty."""
        text = (query or "").strip()
        if not text:
            return all_entries(language, section=section)[:limit]
        return search(text, language, section=section, limit=limit)

    # -- conversations ------------------------------------------------------

    def list_conversations(self, owner: str) -> list[Conversation]:
        return self._store.list(owner)

    def get_conversation(self, owner: str, conversation_id: str) -> Conversation:
        return self._store.get(owner, conversation_id)

    def delete_conversation(self, owner: str, conversation_id: str) -> None:
        self._store.delete(owner, conversation_id)

    # -- chat ---------------------------------------------------------------

    def chat(
        self,
        *,
        owner: str,
        question: str,
        language: str | None = None,
        reasoning: str | None = None,
        online_search: bool = False,
        temporary: bool = False,
        conversation_id: str | None = None,
        context: ScreenContext | None = None,
    ) -> ChatResponse:
        """Answer one question and, unless the chat is temporary, persist it."""
        text = (question or "").strip()
        if not text:
            raise CopilotValidationError("Question must not be empty.", field="question")
        if len(text) > MAX_QUESTION_LENGTH:
            raise CopilotValidationError(
                f"Question must be at most {MAX_QUESTION_LENGTH} characters.",
                field="question",
            )

        try:
            requested = ReasoningTier.parse(reasoning)
        except ValueError as exc:
            raise CopilotValidationError(str(exc), field="reasoning") from exc

        lang = normalize_language(language)
        screen = context or ScreenContext()
        resolved_tier = (
            resolve_auto_tier(text) if requested is ReasoningTier.AUTO else requested
        )

        conversation = self._resolve_conversation(
            owner=owner,
            conversation_id=conversation_id,
            title=derive_title(text),
            language=lang,
            temporary=temporary,
        )

        history = conversation.messages[-(MAX_HISTORY_TURNS * 2) :]
        agent = self._agents.get(resolved_tier) or self._agents[ReasoningTier.DEFAULT]
        result = agent.answer(
            ChatTurnRequest(
                question=text,
                language=lang,
                reasoning=resolved_tier,
                online_search=online_search,
                context=screen,
                history=tuple(history),
            )
        )

        asked = user_message(text)
        answered = ChatMessage(
            message_id=new_id("msg"),
            role=MessageRole.ASSISTANT,
            content=result.answer,
            sources=result.sources,
            reasoning=result.resolved_reasoning,
            online_search=result.online_search_used,
            agent=result.agent,
        )

        persisted = False
        if temporary:
            conversation = conversation.with_messages(asked, answered)
        else:
            conversation = self._store.append(
                owner, conversation.conversation_id, question=asked, answer=answered
            )
            persisted = True

        concepts = resolve_context(text, screen).labels
        logger.info(
            "copilot chat: section=%s tier=%s online=%s agent=%s persisted=%s",
            screen.section or "-",
            resolved_tier.value,
            result.online_search_used,
            result.agent,
            persisted,
        )

        return ChatResponse(
            conversation=conversation,
            question=asked,
            answer=answered,
            resolved_reasoning=resolved_tier,
            resolved_concepts=concepts,
            online_search_used=result.online_search_used,
            persisted=persisted,
        )

    # -- internals ----------------------------------------------------------

    def _resolve_conversation(
        self,
        *,
        owner: str,
        conversation_id: str | None,
        title: str,
        language: str,
        temporary: bool,
    ) -> Conversation:
        if temporary:
            return Conversation(
                conversation_id=conversation_id or new_id("temp"),
                owner=owner,
                title=title,
                language=language,
                temporary=True,
            )
        if conversation_id:
            existing = self._store.find(owner, conversation_id)
            if existing is not None:
                return existing
        return self._store.create(owner, title=title, language=language)
