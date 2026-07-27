"""Domain models for the NovaSteel Copilot chat assistant.

Pure standard-library dataclasses shared by the context resolver, glossary,
suggestion selector, conversation store, agent adapters and service layer.

References:
* solution-architecture.md (Foundry agents)
* api-contracts.md (Copilot chat endpoints)
* security-governance-and-threat-model.md (grounding, prompt defence)
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Optional

SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "fr", "de", "nl", "es")
DEFAULT_LANGUAGE = "en"


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def iso(ts: datetime) -> str:
    """Render a UTC ISO-8601 ``Z`` timestamp, matching the API ``asOf`` contract."""
    return ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_language(locale: str | None) -> str:
    """Map a locale such as ``fr-LU`` onto a supported two-letter language.

    Unknown or missing locales fall back to English so a partially configured
    shell still renders a usable panel rather than failing the request.
    """
    language = (locale or DEFAULT_LANGUAGE)[:2].lower()
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


class ReasoningTier(str, enum.Enum):
    """User-selectable reasoning effort.

    ``AUTO`` is resolved by the service into ``DEFAULT`` or ``HIGH`` before an
    agent is chosen, so an adapter never has to interpret it.
    """

    AUTO = "auto"
    DEFAULT = "default"
    HIGH = "high"

    @classmethod
    def parse(cls, value: str | None) -> "ReasoningTier":
        candidate = (value or cls.AUTO.value).strip().lower()
        for tier in cls:
            if tier.value == candidate:
                return tier
        raise ValueError(f"Unsupported reasoning tier: {value!r}")


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class SourceKind(str, enum.Enum):
    """Where a cited fragment came from.

    The distinction is surfaced in the UI: operators must be able to see at a
    glance whether an answer leaned on internal grounded material or on a
    public web result.
    """

    INTERNAL = "internal"
    ONLINE = "online"
    GLOSSARY = "glossary"
    SCREEN = "screen"
    KNOWLEDGE = "knowledge"


@dataclass(frozen=True)
class ChatSource:
    """A citation attached to an assistant answer."""

    kind: SourceKind
    source_id: str
    title: str
    snippet: str = ""
    url: Optional[str] = None

    def to_view(self) -> dict[str, object]:
        view: dict[str, object] = {
            "kind": self.kind.value,
            "sourceId": self.source_id,
            "title": self.title,
            "snippet": self.snippet,
        }
        if self.url:
            view["url"] = self.url
        return view


@dataclass(frozen=True)
class ScreenContext:
    """The dashboard location a question was asked from.

    This is what lets "what is the risk?" resolve to *lining risk* when the
    operator is looking at Furnace Health.
    """

    site: str = ""
    section: str = ""
    sub_view: str = ""
    persona: str = ""

    @property
    def route(self) -> str:
        parts = [part for part in (self.section, self.sub_view) if part]
        return "/".join(parts)

    @property
    def is_general(self) -> bool:
        """True when the caller supplied no screen.

        The "Screen context" toggle in the chat panel is off by default. When it
        is off the panel sends no context at all, and the assistant must answer
        as a general steel expert: no screen framing, no screen summary, no
        screen citation.
        """
        section = (self.section or "").strip()
        return not section or section == "-"

    def to_view(self) -> dict[str, str]:
        return {
            "site": self.site,
            "section": self.section,
            "subView": self.sub_view,
            "persona": self.persona,
        }


@dataclass(frozen=True)
class ChatMessage:
    """One turn in a conversation."""

    message_id: str
    role: MessageRole
    content: str
    created_at: datetime = field(default_factory=utcnow)
    sources: tuple[ChatSource, ...] = ()
    reasoning: Optional[ReasoningTier] = None
    online_search: bool = False
    agent: str = ""

    def to_view(self) -> dict[str, object]:
        view: dict[str, object] = {
            "messageId": self.message_id,
            "role": self.role.value,
            "content": self.content,
            "createdAt": iso(self.created_at),
            "sources": [source.to_view() for source in self.sources],
        }
        if self.reasoning is not None:
            view["reasoning"] = self.reasoning.value
        if self.role is MessageRole.ASSISTANT:
            view["onlineSearch"] = self.online_search
            view["agent"] = self.agent
        return view


@dataclass(frozen=True)
class Conversation:
    """A stored chat thread owned by exactly one user.

    Temporary chats are represented by the same structure but are never handed
    to the store, so they leave no trace once the panel is closed.
    """

    conversation_id: str
    owner: str
    title: str
    language: str
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    messages: tuple[ChatMessage, ...] = ()
    temporary: bool = False

    def with_messages(self, *appended: ChatMessage) -> "Conversation":
        return replace(
            self,
            messages=self.messages + appended,
            updated_at=utcnow(),
        )

    def to_summary(self) -> dict[str, object]:
        return {
            "conversationId": self.conversation_id,
            "title": self.title,
            "language": self.language,
            "createdAt": iso(self.created_at),
            "updatedAt": iso(self.updated_at),
            "messageCount": len(self.messages),
            "temporary": self.temporary,
        }

    def to_view(self) -> dict[str, object]:
        view = self.to_summary()
        view["messages"] = [message.to_view() for message in self.messages]
        return view


@dataclass(frozen=True)
class GroundingItem:
    """A retrieval hit supplied by the caller as extra grounding.

    The BFF owns the demo corpora (public-context and general steel knowledge);
    it retrieves the relevant fragments and hands them to the agent so the
    *answer itself* is grounded on them, rather than bolting citations onto an
    already-composed answer.
    """

    source_id: str
    title: str
    snippet: str
    kind: SourceKind = SourceKind.KNOWLEDGE
    url: str = ""

    def to_source(self) -> ChatSource:
        return ChatSource(
            kind=self.kind,
            source_id=self.source_id,
            title=self.title,
            snippet=self.snippet,
            url=self.url or None,
        )


@dataclass(frozen=True)
class ChatTurnRequest:
    """A validated question ready to be answered."""

    question: str
    language: str
    reasoning: ReasoningTier
    online_search: bool
    context: ScreenContext
    history: tuple[ChatMessage, ...] = ()
    grounding: tuple[GroundingItem, ...] = ()


@dataclass(frozen=True)
class ChatTurnResult:
    """An agent's answer plus the metadata the UI renders around it."""

    answer: str
    sources: tuple[ChatSource, ...] = ()
    agent: str = ""
    resolved_reasoning: ReasoningTier = ReasoningTier.DEFAULT
    online_search_used: bool = False
    resolved_terms: tuple[str, ...] = ()
    trace: tuple[str, ...] = ()
