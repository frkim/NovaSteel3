"""Unit tests for the Copilot chat domain: context, glossary, suggestions, store."""

from __future__ import annotations

import pytest

from knowledge_orchestrator.copilot import context as ctx
from knowledge_orchestrator.copilot import glossary as gl
from knowledge_orchestrator.copilot.models import (
    SUPPORTED_LANGUAGES,
    ReasoningTier,
    ScreenContext,
    normalize_language,
)
from knowledge_orchestrator.copilot.online import online_context
from knowledge_orchestrator.copilot.screen_copy import SCREEN_SUMMARIES
from knowledge_orchestrator.copilot.store import (
    ConversationNotFoundError,
    ConversationStore,
    derive_title,
    user_message,
)
from knowledge_orchestrator.copilot.suggestions import suggestions_for

SECTIONS = tuple(profile.section for profile in ctx._PROFILES)


# --- context resolution ---------------------------------------------------


def test_bare_risk_question_resolves_to_lining_risk_on_furnace_health():
    """The headline behaviour: an ambiguous question is disambiguated by screen."""
    resolved = ctx.resolve(
        "What is the risk?", ScreenContext(section="furnace-health", sub_view="lining-forecast")
    )
    assert resolved.primary.key == "lining_risk"
    assert resolved.matched_explicitly is False


def test_same_bare_question_resolves_differently_on_another_screen():
    resolved = ctx.resolve(
        "What is the risk?",
        ScreenContext(section="sustainability-compliance", sub_view="ets-exposure"),
    )
    assert resolved.primary.key == "ets_exposure"


def test_explicit_concept_beats_the_screen_default():
    resolved = ctx.resolve(
        "Explain how thermal signature works",
        ScreenContext(section="furnace-health", sub_view="lining-forecast"),
    )
    assert resolved.primary.key == "thermal_signature"
    assert resolved.matched_explicitly is True


def test_sub_view_reorders_the_screen_concepts():
    planner = ctx.resolve(
        "What should I do?",
        ScreenContext(section="furnace-health", sub_view="maintenance-planner"),
    )
    assert planner.primary.key == "maintenance_window"


@pytest.mark.parametrize(
    "question,language",
    [
        ("Quel est le risque de garnissage ?", "fr"),
        ("Wie ist das Zustellungsrisiko?", "de"),
        ("Wat is het vuurvastrisico?", "nl"),
        ("Cual es el riesgo de revestimiento?", "es"),
    ],
)
def test_concepts_are_triggered_in_every_supported_language(question, language):
    resolved = ctx.resolve(question, ScreenContext(section="furnace-health"))
    assert resolved.primary.key == "lining_risk", language
    assert resolved.matched_explicitly is True


def test_unknown_section_falls_back_to_command_center():
    assert ctx.profile_for("does-not-exist").section == "command-center"


def test_every_profile_has_a_localized_summary_in_every_language():
    for section in SECTIONS:
        profile = ctx.profile_for(section)
        assert SCREEN_SUMMARIES[section]["en"] == profile.summary
        for language in SUPPORTED_LANGUAGES:
            assert profile.summary_in(language).strip()


def test_pinned_glossary_ids_all_exist():
    """A typo in a pin would silently degrade answers, so assert them here."""
    for concept in ctx.ALL_CONCEPTS:
        if concept.glossary_id is not None:
            assert gl.entry_by_id(concept.glossary_id) is not None, concept.key


# --- glossary --------------------------------------------------------------


def test_glossary_search_is_accent_and_case_insensitive():
    assert gl.search("EMISSIONS", "en")
    assert gl.search("emissions", "en")
    assert [entry.term_id for entry in gl.search("Émissions", "fr")]


def test_glossary_matches_wording_inside_a_definition():
    """The box is documented as searching definitions, not just terms."""
    hits = gl.search("percentile", "en")
    assert any(entry.term_id == "p10-p50-p90" for entry in hits)


def test_exact_term_outranks_a_definition_mention():
    hits = gl.search("cbam", "en")
    assert hits[0].term_id == "cbam"


def test_short_queries_are_ignored():
    assert gl.search("e", "en") == []


def test_screen_scoped_listing():
    entries = gl.all_entries("en", section="platform-ops")
    assert entries
    assert all("platform-ops" in entry.screens for entry in entries)


def test_entries_for_prefers_the_explicit_identifier():
    entries = gl.entries_for([("Maintenance window", "work-order")], "en")
    assert [entry.term_id for entry in entries] == ["work-order"]


def test_entries_for_falls_back_to_label_words():
    entries = gl.entries_for([("Energy cost", None)], "en")
    assert entries and entries[0].term_id == "energy-intensity-gj-per-tonne"


def test_glossary_renders_in_the_requested_language():
    entry = gl.entry_by_id("lining-risk", "de")
    assert entry is not None
    assert entry.language == "de"
    assert entry.term != gl.entry_by_id("lining-risk", "en").term


def test_unknown_language_falls_back_to_english():
    assert normalize_language("pt-BR") == "en"
    assert normalize_language(None) == "en"
    assert normalize_language("FR-lu") == "fr"


# --- suggestions -----------------------------------------------------------


@pytest.mark.parametrize("section", SECTIONS)
@pytest.mark.parametrize("language", SUPPORTED_LANGUAGES)
def test_every_screen_has_five_suggestions_in_every_language(section, language):
    result = suggestions_for(section, language)
    assert len(result.questions) == 5
    assert all(question.strip() for question in result.questions)
    assert result.persona == ctx.profile_for(section).persona


def test_unknown_section_still_returns_suggestions():
    result = suggestions_for("nope", "fr")
    assert len(result.questions) == 5


# --- online context --------------------------------------------------------


def test_online_context_is_only_reachable_through_the_toggle():
    """The corpus itself is unconditional; the gate lives in the agent."""
    resolved = ctx.resolve("ETS announcements", ScreenContext(section="sustainability-compliance"))
    hits = online_context(resolved, "What are the latest ETS main announcements?", "en")
    assert hits
    assert any(hit.source_id.startswith("eu-ets") for hit in hits)
    assert all(hit.url.startswith("https://") for hit in hits)


def test_online_context_is_localized():
    resolved = ctx.resolve("spot price", ScreenContext(section="energy-optimization"))
    en = online_context(resolved, "spot price", "en")
    fr = online_context(resolved, "spot price", "fr")
    assert en and fr
    assert en[0].source_id == fr[0].source_id
    assert en[0].snippet != fr[0].snippet


# --- conversation store ----------------------------------------------------


def test_conversations_are_scoped_to_their_owner():
    store = ConversationStore()
    mine = store.create("alice", title="t", language="en")
    with pytest.raises(ConversationNotFoundError):
        store.get("bob", mine.conversation_id)
    assert store.list("bob") == []


def test_append_and_delete_round_trip():
    store = ConversationStore()
    conversation = store.create("alice", title="t", language="en")
    updated = store.append(
        "alice",
        conversation.conversation_id,
        question=user_message("q"),
        answer=user_message("a"),
    )
    assert len(updated.messages) == 2
    store.delete("alice", conversation.conversation_id)
    with pytest.raises(ConversationNotFoundError):
        store.get("alice", conversation.conversation_id)


def test_oldest_conversations_are_evicted():
    store = ConversationStore(max_conversations=3)
    for index in range(5):
        store.create("alice", title=f"t{index}", language="en")
    assert len(store.list("alice")) == 3


def test_messages_are_trimmed_to_the_cap():
    store = ConversationStore(max_messages=4)
    conversation = store.create("alice", title="t", language="en")
    for _ in range(5):
        store.append(
            "alice",
            conversation.conversation_id,
            question=user_message("q"),
            answer=user_message("a"),
        )
    assert len(store.get("alice", conversation.conversation_id).messages) == 4


def test_title_is_derived_from_the_first_question():
    assert derive_title("  What is the   risk? ") == "What is the risk?"
    assert derive_title("") == "New chat"
    assert len(derive_title("x" * 200)) == 60


def test_reasoning_tier_parsing():
    assert ReasoningTier.parse(None) is ReasoningTier.AUTO
    assert ReasoningTier.parse(" HIGH ") is ReasoningTier.HIGH
    with pytest.raises(ValueError):
        ReasoningTier.parse("ultra")
