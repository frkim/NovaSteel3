"""Deterministic Fabric answers for the Copilot's predefined questions.

Selection logic only; the wording lives in ``fabric_answer_data`` and the
per-language ``fabric_answers_<lang>`` modules.

Why this exists
---------------
Every chip rendered by :mod:`suggestions` is a question the demo already knows
the answer to: the figure is on the screen behind the panel, in the fixture pack
the BFF serves, or in the gold tables the Fabric data agent (``da-novasteelv3``)
queries. Answering those chips from the glossary alone wasted the best part of
the story, so the panel now serves the *data* answer — the same synthetic
figures, cited back to the Fabric dataset that carries them.

This is the deterministic stand-in for
``docs/architecture/copilot-fabric-data-agent.md`` option A: the answer is
composed from a curated Fabric result rather than from a live capacity, so the
demo is reproducible, works offline, and never depends on an F2 being resumed.

Matching is by question text alone, in any of the five languages. It cannot key
off the screen: the panel's "Screen context" toggle is off by default, so a chip
usually arrives with no section attached.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from .fabric_answer_data import CARDS, WORKSPACE, FabricCard
from .models import ChatSource, SourceKind, normalize_language
from .suggestion_data import SUGGESTIONS_BY_SECTION


def normalize_question(text: str) -> str:
    """Fold a question down to the characters that carry its identity.

    Punctuation, spacing and case are dropped so a chip still matches when the
    shell round-trips it through a text field: what is left is the letters and
    digits of the sentence.
    """
    return "".join(char for char in (text or "").casefold() if char.isalnum())


@dataclass(frozen=True)
class FabricAnswer:
    """One resolved answer, ready for an agent to serve."""

    card: FabricCard
    language: str
    body: str

    @property
    def sources(self) -> tuple[ChatSource, ...]:
        return tuple(
            ChatSource(
                kind=SourceKind.FABRIC,
                source_id=dataset.source_id,
                title=dataset.title,
                snippet=dataset.snippet,
            )
            for dataset in self.card.datasets
        )


def _build_index() -> dict[str, FabricCard]:
    """Map every wording that reaches a card onto it.

    Two kinds of card are indexed. A screen chip names a screen/index pair, and
    is registered under its wording in each of the five languages -- a pair with
    no matching suggestion is a typo, and is reported at import time rather than
    silently never matching. A persona question carries its verbatim prompts
    instead, because the chat panel sends those as free text.
    """
    index: dict[str, FabricCard] = {}
    for card in CARDS:
        if card.section:
            by_language = SUGGESTIONS_BY_SECTION.get(card.section)
            if by_language is None:
                raise ValueError(f"Fabric card {card.card_id}: unknown section")
            for language, questions in by_language.items():
                if card.index >= len(questions):
                    raise ValueError(
                        f"Fabric card {card.card_id}: no {language} question at index {card.index}"
                    )
                index[normalize_question(questions[card.index])] = card
        for prompt in card.prompts:
            key = normalize_question(prompt)
            if not key:
                raise ValueError(f"Fabric card {card.card_id}: empty prompt")
            index[key] = card
        if not card.section and not card.prompts:
            raise ValueError(f"Fabric card {card.card_id}: no section and no prompt")
    return index


_INDEX: Final[dict[str, FabricCard]] = _build_index()

CARDS_BY_ID: Final[dict[str, FabricCard]] = {card.card_id: card for card in CARDS}


def card_for_question(question: str) -> Optional[FabricCard]:
    """Return the card a question matches, or ``None`` for free-text questions."""
    return _INDEX.get(normalize_question(question))


def answer_for(question: str, language: str | None = None) -> Optional[FabricAnswer]:
    """Resolve one predefined question into its Fabric answer.

    Falls back to the English body when a translation is missing, so a partially
    translated pack degrades to an answer in the wrong language rather than to
    no answer at all.
    """
    card = card_for_question(question)
    if card is None:
        return None
    lang = normalize_language(language)
    body = card.body.get(lang) or card.body.get("en")
    if not body:
        return None
    return FabricAnswer(card=card, language=lang, body=body)
