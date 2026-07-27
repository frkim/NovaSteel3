"""NovaSteel Copilot chat assistant.

An in-product, M365-Copilot-style assistant docked next to the analytics
dashboard. It is screen-aware (a bare "what is the risk?" resolves to the
notion that screen is about), multilingual across the five supported UI
languages, backed by one Azure AI Foundry deployment per reasoning tier with a
deterministic offline fallback, and grounded on a curated glossary plus an
explicit, opt-in public-context corpus.

Layering: ``models`` -> ``context``/``glossary``/``suggestions``/``online`` ->
``agents`` -> ``service``. The BFF talks to ``CopilotService`` only.
"""

from .agents import (
    AzureFoundryChatAgent,
    CopilotChatAgent,
    LocalCopilotChatAgent,
    create_chat_agents,
)
from .context import ResolvedContext, ScreenProfile, profile_for, resolve
from .glossary import GlossaryEntry, all_entries, lookup, search
from .models import (
    SUPPORTED_LANGUAGES,
    ChatMessage,
    ChatSource,
    ChatTurnRequest,
    ChatTurnResult,
    Conversation,
    GroundingItem,
    MessageRole,
    ReasoningTier,
    ScreenContext,
    SourceKind,
    normalize_language,
)
from .online import OnlineHit, online_context
from .service import ChatResponse, CopilotService, CopilotValidationError, resolve_auto_tier
from .store import ConversationNotFoundError, ConversationStore
from .suggestions import SuggestionSet, suggestions_for

__all__ = [
    "SUPPORTED_LANGUAGES",
    "AzureFoundryChatAgent",
    "ChatMessage",
    "ChatResponse",
    "ChatSource",
    "ChatTurnRequest",
    "ChatTurnResult",
    "Conversation",
    "ConversationNotFoundError",
    "ConversationStore",
    "CopilotChatAgent",
    "CopilotService",
    "CopilotValidationError",
    "GlossaryEntry",
    "GroundingItem",
    "LocalCopilotChatAgent",
    "MessageRole",
    "OnlineHit",
    "ReasoningTier",
    "ResolvedContext",
    "ScreenContext",
    "ScreenProfile",
    "SourceKind",
    "SuggestionSet",
    "all_entries",
    "create_chat_agents",
    "lookup",
    "normalize_language",
    "online_context",
    "profile_for",
    "resolve",
    "resolve_auto_tier",
    "search",
    "suggestions_for",
]
