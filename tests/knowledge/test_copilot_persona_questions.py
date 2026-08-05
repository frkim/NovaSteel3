"""The chat panel's per-persona questions must all be answered from Fabric.

The panel offers each of the eight personas four questions before any screen is
chosen (``PERSONA_QUESTIONS`` in ``CopilotPanel.tsx``). They reach the
orchestrator as free text, so nothing but this test keeps the two sides in step:
reword a chip in the panel and the card stops matching, silently, and the
question falls back to "that is not in my knowledge base yet".
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from knowledge_orchestrator.copilot import fabric_answers
from knowledge_orchestrator.copilot.agents import LocalCopilotChatAgent
from knowledge_orchestrator.copilot.fabric_persona_data import PERSONA_CARDS
from knowledge_orchestrator.copilot.models import (
    SUPPORTED_LANGUAGES,
    ChatTurnRequest,
    ReasoningTier,
    ScreenContext,
    SourceKind,
)

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "apps" / "analytics-mfe" / "src" / "components" / "copilot" / "CopilotPanel.tsx"

_ENTRY = re.compile(r"\{\s*persona:\s*'(?P<persona>(?:[^'\\]|\\.)*)'\s*,\s*question:\s*'(?P<question>(?:[^'\\]|\\.)*)'\s*\}")


def _unescape(value: str) -> str:
    """Turn a TypeScript single-quoted literal back into plain text."""
    return (
        value.replace("\\'", "'")
        .replace("\\\\", "\\")
        .encode("utf-8")
        .decode("unicode_escape")
        .encode("latin-1", "ignore")
        .decode("utf-8", "ignore")
        if "\\u" in value
        else value.replace("\\'", "'").replace("\\\\", "\\")
    )


def panel_questions() -> list[tuple[str, str]]:
    source = PANEL.read_text(encoding="utf-8")
    block = source.split("const PERSONA_QUESTIONS: PersonaQuestion[] = [", 1)[1]
    block = block.split("\n]", 1)[0]
    return [
        (_unescape(match.group("persona")), _unescape(match.group("question")))
        for match in _ENTRY.finditer(block)
    ]


PANEL_QUESTIONS = panel_questions()


def turn(question: str, **kwargs) -> ChatTurnRequest:
    return ChatTurnRequest(
        question=question,
        language=kwargs.pop("language", "en"),
        reasoning=kwargs.pop("reasoning", ReasoningTier.DEFAULT),
        online_search=kwargs.pop("online_search", False),
        context=kwargs.pop("context", ScreenContext()),
    )


def test_the_panel_still_declares_four_questions_per_persona():
    personas: dict[str, int] = {}
    for persona, _ in PANEL_QUESTIONS:
        personas[persona] = personas.get(persona, 0) + 1
    assert len(personas) == 8
    assert set(personas.values()) == {4}


@pytest.mark.parametrize(
    "persona,question",
    PANEL_QUESTIONS,
    ids=[f"{persona}: {question[:40]}" for persona, question in PANEL_QUESTIONS],
)
def test_every_persona_question_is_answered_by_the_data_agent(persona, question):
    card = fabric_answers.card_for_question(question)
    assert card is not None, f"{persona} has no Fabric card for {question!r}"
    assert card.datasets

    result = LocalCopilotChatAgent().answer(turn(question))

    assert "Microsoft Fabric" in result.answer
    assert "Retrieved from Fabric" in result.answer
    assert SourceKind.FABRIC in {source.kind for source in result.sources}
    for dataset in card.datasets:
        assert dataset.statement in result.answer


@pytest.mark.parametrize("card", PERSONA_CARDS, ids=lambda card: card.card_id)
def test_persona_card_answers_in_every_language(card):
    for language in SUPPORTED_LANGUAGES:
        answer = fabric_answers.answer_for(card.prompts[0], language)
        assert answer is not None
        assert answer.language == language
        assert answer.body == card.body[language]


def test_every_persona_card_is_reachable_from_the_panel():
    """No orphan cards: a card whose prompt no chip sends is dead weight."""
    asked = {fabric_answers.normalize_question(q) for _, q in PANEL_QUESTIONS}
    for card in PERSONA_CARDS:
        keys = {fabric_answers.normalize_question(p) for p in card.prompts}
        assert keys & asked, card.card_id


def test_persona_questions_never_dead_end_on_the_knowledge_fallback():
    agent = LocalCopilotChatAgent()
    for _, question in PANEL_QUESTIONS:
        answer = agent.answer(turn(question)).answer
        assert "not in my steel knowledge base" not in answer, question
