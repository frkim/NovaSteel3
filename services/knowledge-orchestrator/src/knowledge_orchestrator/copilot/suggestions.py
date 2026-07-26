"""Persona-scoped suggested questions for the Copilot chat assistant.

Selection logic only; the wording lives in ``suggestion_data``. The panel shows
these as chips before the first turn so an evaluator who does not know the
domain can still drive the demo.
"""

from __future__ import annotations

from dataclasses import dataclass

from .context import profile_for
from .models import normalize_language
from .suggestion_data import DEFAULT_SUGGESTIONS, SUGGESTIONS_BY_SECTION

MAX_SUGGESTIONS = 5


@dataclass(frozen=True)
class SuggestionSet:
    """The chips rendered for one screen in one language."""

    section: str
    persona: str
    language: str
    questions: tuple[str, ...]

    def to_view(self) -> dict[str, object]:
        return {
            "section": self.section,
            "persona": self.persona,
            "language": self.language,
            "questions": list(self.questions),
        }


def suggestions_for(
    section: str | None,
    language: str | None = None,
    *,
    limit: int = MAX_SUGGESTIONS,
) -> SuggestionSet:
    """Return the suggested questions for a dashboard section.

    Unknown sections fall back to the generic set rather than raising, so a
    future screen still renders a usable panel before its copy is written.
    """
    lang = normalize_language(language)
    slug = (section or "").strip().lower()
    profile = profile_for(slug)
    by_language = SUGGESTIONS_BY_SECTION.get(slug)
    if by_language is None:
        questions = DEFAULT_SUGGESTIONS.get(lang, DEFAULT_SUGGESTIONS["en"])
        return SuggestionSet(
            section=slug or profile.section,
            persona=profile.persona,
            language=lang,
            questions=tuple(questions[:limit]),
        )

    questions = by_language.get(lang) or by_language["en"]
    return SuggestionSet(
        section=profile.section,
        persona=profile.persona,
        language=lang,
        questions=tuple(questions[:limit]),
    )
