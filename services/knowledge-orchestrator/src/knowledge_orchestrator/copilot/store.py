"""Conversation storage for the Copilot chat assistant.

In-process, per-owner and bounded. The demo deliberately keeps chat history off
Fabric: conversations contain free-text questions typed by a named user, so
persisting them would widen the data-protection surface for no demo value. A
container restart clears history, which is the documented behaviour.

Temporary chats never reach this store at all -- the service simply skips the
save, which is what makes the "temporary chat" toggle honest rather than
cosmetic.
"""

from __future__ import annotations

import threading
import uuid
from typing import Optional

from .models import (
    ChatMessage,
    Conversation,
    MessageRole,
    normalize_language,
    utcnow,
)

# Bounds chosen so a long demo session cannot grow memory without limit.
MAX_CONVERSATIONS_PER_OWNER = 25
MAX_MESSAGES_PER_CONVERSATION = 60
TITLE_MAX_LENGTH = 60


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def derive_title(question: str) -> str:
    """Use the first question as the thread title, the way M365 Copilot does."""
    text = " ".join((question or "").split())
    if not text:
        return "New chat"
    if len(text) <= TITLE_MAX_LENGTH:
        return text
    return text[: TITLE_MAX_LENGTH - 1].rstrip() + "\u2026"


class ConversationNotFoundError(LookupError):
    """Raised when an owner asks for a conversation they do not have."""

    def __init__(self, conversation_id: str):
        super().__init__(f"Conversation not found: {conversation_id}")
        self.conversation_id = conversation_id


class ConversationStore:
    """Thread-safe, owner-scoped conversation storage."""

    def __init__(
        self,
        max_conversations: int = MAX_CONVERSATIONS_PER_OWNER,
        max_messages: int = MAX_MESSAGES_PER_CONVERSATION,
    ):
        self._lock = threading.RLock()
        self._by_owner: dict[str, dict[str, Conversation]] = {}
        self._max_conversations = max_conversations
        self._max_messages = max_messages

    # -- reads ------------------------------------------------------------

    def list(self, owner: str) -> list[Conversation]:
        """Most recently updated first, which is the order the panel renders."""
        with self._lock:
            conversations = list(self._by_owner.get(owner, {}).values())
        return sorted(conversations, key=lambda c: c.updated_at, reverse=True)

    def get(self, owner: str, conversation_id: str) -> Conversation:
        with self._lock:
            conversation = self._by_owner.get(owner, {}).get(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        return conversation

    def find(self, owner: str, conversation_id: str) -> Optional[Conversation]:
        with self._lock:
            return self._by_owner.get(owner, {}).get(conversation_id)

    # -- writes -----------------------------------------------------------

    def create(self, owner: str, *, title: str, language: str) -> Conversation:
        conversation = Conversation(
            conversation_id=new_id("conv"),
            owner=owner,
            title=title,
            language=normalize_language(language),
        )
        with self._lock:
            self._save_locked(conversation)
        return conversation

    def append(
        self,
        owner: str,
        conversation_id: str,
        *,
        question: ChatMessage,
        answer: ChatMessage,
    ) -> Conversation:
        """Append a user/assistant pair, trimming the oldest turns if needed."""
        with self._lock:
            existing = self._by_owner.get(owner, {}).get(conversation_id)
            if existing is None:
                raise ConversationNotFoundError(conversation_id)
            messages = (*existing.messages, question, answer)
            if len(messages) > self._max_messages:
                messages = messages[-self._max_messages :]
            updated = Conversation(
                conversation_id=existing.conversation_id,
                owner=existing.owner,
                title=existing.title or derive_title(question.content),
                language=existing.language,
                created_at=existing.created_at,
                updated_at=utcnow(),
                messages=messages,
                temporary=existing.temporary,
            )
            self._save_locked(updated)
        return updated

    def delete(self, owner: str, conversation_id: str) -> None:
        with self._lock:
            owned = self._by_owner.get(owner, {})
            if conversation_id not in owned:
                raise ConversationNotFoundError(conversation_id)
            del owned[conversation_id]

    def clear(self, owner: str | None = None) -> None:
        with self._lock:
            if owner is None:
                self._by_owner.clear()
            else:
                self._by_owner.pop(owner, None)

    # -- internals --------------------------------------------------------

    def _save_locked(self, conversation: Conversation) -> None:
        owned = self._by_owner.setdefault(conversation.owner, {})
        owned[conversation.conversation_id] = conversation
        if len(owned) > self._max_conversations:
            oldest = sorted(owned.values(), key=lambda c: c.updated_at)
            for stale in oldest[: len(owned) - self._max_conversations]:
                owned.pop(stale.conversation_id, None)


def user_message(content: str) -> ChatMessage:
    return ChatMessage(
        message_id=new_id("msg"),
        role=MessageRole.USER,
        content=content,
    )
