"""Tests for the curated Fabric answers behind the predefined Copilot questions."""

from __future__ import annotations

import re

import pytest

from knowledge_orchestrator.copilot import fabric_answers
from knowledge_orchestrator.copilot.agents import (
    AzureFoundryChatAgent,
    LocalCopilotChatAgent,
)
from knowledge_orchestrator.copilot.fabric_answer_data import CARDS
from knowledge_orchestrator.copilot.models import (
    SUPPORTED_LANGUAGES,
    ChatTurnRequest,
    ReasoningTier,
    ScreenContext,
    SourceKind,
)
from knowledge_orchestrator.copilot.suggestion_data import SUGGESTIONS_BY_SECTION

# The chips that ask for public context keep the online-search behaviour, so they
# deliberately have no Fabric card. Everything else on a screen must have one.
SEARCH_CHIPS: dict[str, int] = {
    "command-center": 3,
    "operations": 3,
    "furnace-health": 3,
    "energy-optimization": 3,
    "quality": 3,
    "sustainability-compliance": 3,
    "knowledge-hub": 3,
    "executive-overview": 3,
    "platform-ops": 3,
    "device-operations": 4,
    "dashboards": 4,
}


def turn(question: str, **kwargs) -> ChatTurnRequest:
    return ChatTurnRequest(
        question=question,
        language=kwargs.pop("language", "en"),
        reasoning=kwargs.pop("reasoning", ReasoningTier.DEFAULT),
        online_search=kwargs.pop("online_search", False),
        context=kwargs.pop("context", ScreenContext()),
    )


# --- coverage --------------------------------------------------------------


def test_every_non_search_suggestion_has_a_card():
    uncovered: list[tuple[str, int]] = []
    for section, by_language in SUGGESTIONS_BY_SECTION.items():
        for index, question in enumerate(by_language["en"]):
            covered = fabric_answers.card_for_question(question) is not None
            expected = index != SEARCH_CHIPS[section]
            if covered is not expected:
                uncovered.append((section, index))
    assert uncovered == []


def test_search_chips_stay_on_the_online_corpus():
    for section, index in SEARCH_CHIPS.items():
        for language in SUPPORTED_LANGUAGES:
            question = SUGGESTIONS_BY_SECTION[section][language][index]
            assert fabric_answers.card_for_question(question) is None


@pytest.mark.parametrize("card", CARDS, ids=lambda card: card.card_id)
def test_card_resolves_from_every_language(card):
    for language in SUPPORTED_LANGUAGES:
        question = SUGGESTIONS_BY_SECTION[card.section][language][card.index]
        answer = fabric_answers.answer_for(question, language)
        assert answer is not None
        assert answer.card is card


@pytest.mark.parametrize("card", CARDS, ids=lambda card: card.card_id)
def test_card_is_translated_into_every_language(card):
    assert set(card.body) == set(SUPPORTED_LANGUAGES)


@pytest.mark.parametrize("card", CARDS, ids=lambda card: card.card_id)
def test_card_cites_at_least_one_fabric_dataset(card):
    assert card.datasets
    for dataset in card.datasets:
        assert dataset.source_id.startswith("fabric:")
        assert dataset.snippet


def test_bodies_avoid_markup_the_panel_cannot_render():
    # The panel renders paragraphs, **bold** and _italic_ only.
    for card in CARDS:
        for language, body in card.body.items():
            assert "|" not in body, (card.card_id, language)
            assert "`" not in body, (card.card_id, language)
            assert not any(
                line.startswith("#") for line in body.splitlines()
            ), (card.card_id, language)


def test_translations_preserve_the_figures():
    """A translated body may reword prose, never drop or alter a figure."""
    for card in CARDS:
        expected = _figures(card.body["en"])
        for language, body in card.body.items():
            if language == "en":
                continue
            missing = expected - _figures(body)
            assert not missing, (card.card_id, language, sorted(missing))


def _figures(body: str) -> set[str]:
    """Every numeric literal in a body: figures, ids, versions, timestamps."""
    return set(re.findall(r"\d[\d.,]*\d|\d", body))


# --- normalisation ---------------------------------------------------------


def test_matching_survives_punctuation_and_case():
    question = SUGGESTIONS_BY_SECTION["furnace-health"]["en"][1]
    assert fabric_answers.card_for_question(question.upper()) is not None
    assert fabric_answers.card_for_question(question.replace("?", "")) is not None
    assert fabric_answers.card_for_question(f"  {question}  ") is not None


def test_free_text_questions_are_not_intercepted():
    assert fabric_answers.card_for_question("What is a tuyere?") is None
    assert fabric_answers.answer_for("") is None


def test_missing_translation_falls_back_to_english(monkeypatch):
    card = fabric_answers.CARDS_BY_ID["furnace-health-q2"]
    question = SUGGESTIONS_BY_SECTION["furnace-health"]["de"][card.index]
    monkeypatch.setitem(card.body, "de", "")

    answer = fabric_answers.answer_for(question, "de")
    assert answer is not None
    assert answer.body == card.body["en"]


# --- agent behaviour -------------------------------------------------------


def test_local_agent_serves_the_card_verbatim():
    card = fabric_answers.CARDS_BY_ID["energy-optimization-q1"]
    question = SUGGESTIONS_BY_SECTION["energy-optimization"]["en"][card.index]

    result = LocalCopilotChatAgent().answer(turn(question))

    assert card.body["en"] in result.answer
    assert "Microsoft Fabric" in result.answer
    kinds = {source.kind for source in result.sources}
    assert SourceKind.FABRIC in kinds
    assert {source.title for source in result.sources} >= {
        dataset.title for dataset in card.datasets
    }


def test_local_agent_answers_the_chip_in_the_requested_language():
    card = fabric_answers.CARDS_BY_ID["quality-q1"]
    question = SUGGESTIONS_BY_SECTION["quality"]["fr"][card.index]

    result = LocalCopilotChatAgent().answer(turn(question, language="fr"))

    assert card.body["fr"] in result.answer


def test_local_agent_adds_the_screen_source_with_context_on():
    card = fabric_answers.CARDS_BY_ID["furnace-health-q2"]
    question = SUGGESTIONS_BY_SECTION["furnace-health"]["en"][card.index]
    context = ScreenContext(section="furnace-health", sub_view="lining-forecast")

    with_context = LocalCopilotChatAgent().answer(turn(question, context=context))
    without_context = LocalCopilotChatAgent().answer(turn(question))

    assert SourceKind.SCREEN in {s.kind for s in with_context.sources}
    assert SourceKind.SCREEN not in {s.kind for s in without_context.sources}


def test_high_tier_explains_the_fabric_route():
    card = fabric_answers.CARDS_BY_ID["platform-ops-q2"]
    question = SUGGESTIONS_BY_SECTION["platform-ops"]["en"][card.index]

    result = LocalCopilotChatAgent().answer(
        turn(question, reasoning=ReasoningTier.HIGH)
    )

    assert "predefined analytical questions" in result.answer
    assert any("fabric card" in entry for entry in result.trace)


def test_fabric_answers_stay_deterministic():
    agent = LocalCopilotChatAgent()
    card = fabric_answers.CARDS_BY_ID["command-center-q1"]
    question = SUGGESTIONS_BY_SECTION["command-center"]["en"][card.index]

    assert agent.answer(turn(question)).answer == agent.answer(turn(question)).answer


def test_foundry_agent_never_rewords_a_fabric_answer(monkeypatch):
    """The model is not asked: it could only paraphrase figures that are on screen."""
    card = fabric_answers.CARDS_BY_ID["energy-optimization-q1"]
    question = SUGGESTIONS_BY_SECTION["energy-optimization"]["en"][card.index]
    agent = AzureFoundryChatAgent(
        tier=ReasoningTier.DEFAULT, endpoint="https://example.invalid", deployment="d"
    )
    calls: list[tuple[str, str]] = []

    def refuse(system: str, user: str) -> str:
        calls.append((system, user))
        raise AssertionError("the model must not be called for a Fabric answer")

    monkeypatch.setattr(agent, "_complete", refuse)
    result = agent.answer(turn(question))

    assert calls == []
    assert card.body["en"] in result.answer
    assert result.agent == "copilot-chat-default"
    assert SourceKind.FABRIC in {source.kind for source in result.sources}
    assert "fabric result served verbatim" in result.trace


def test_free_text_still_reaches_the_model(monkeypatch):
    agent = AzureFoundryChatAgent(
        tier=ReasoningTier.DEFAULT, endpoint="https://example.invalid", deployment="d"
    )
    monkeypatch.setattr(agent, "_complete", lambda system, user: "model answer")

    result = agent.answer(turn("What is a tuyere?"))

    assert result.answer == "model answer"
