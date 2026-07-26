"""Glossary lookup for the Copilot chat assistant.

Backs the panel's glossary box -- the operator types a word *or* a fragment of
a definition and gets an instant answer -- and also lets the chat agents attach
a definition to an answer without hard-coding any wording.

Search is accent- and case-insensitive so ``emissions``, ``Émissions`` and
``EMISSIONS`` behave identically across the five supported languages.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, cast

from .glossary_data import GLOSSARY_DATA
from .models import DEFAULT_LANGUAGE, normalize_language

# Relevance weights, highest first. Ordering matters more than the absolute
# values: an exact term hit must always outrank a definition mention.
_SCORE_EXACT_TERM = 100
_SCORE_TERM_PREFIX = 80
_SCORE_TERM_WORD = 60
_SCORE_TERM_SUBSTRING = 40
_SCORE_DEFINITION = 20
_SCORE_SCREEN_BONUS = 5

MIN_QUERY_LENGTH = 2


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


@dataclass(frozen=True)
class GlossaryEntry:
    """One glossary term rendered in a single language."""

    term_id: str
    term: str
    definition: str
    language: str
    screens: tuple[str, ...] = ()

    def to_view(self) -> dict[str, object]:
        return {
            "termId": self.term_id,
            "term": self.term,
            "definition": self.definition,
            "language": self.language,
            "screens": list(self.screens),
        }


def _localized(term_id: str, language: str) -> GlossaryEntry:
    raw = GLOSSARY_DATA[term_id]
    terms = cast(dict[str, str], raw["term"])
    definitions = cast(dict[str, str], raw["definition"])
    screens = cast(Sequence[str], raw.get("screens", ()))
    return GlossaryEntry(
        term_id=term_id,
        term=terms.get(language) or terms[DEFAULT_LANGUAGE],
        definition=definitions.get(language) or definitions[DEFAULT_LANGUAGE],
        language=language,
        screens=tuple(screens),
    )


def all_entries(language: str | None = None, *, section: str | None = None) -> list[GlossaryEntry]:
    """Return every term, optionally narrowed to the ones tagged for a screen.

    Sorted by localized term so the glossary box has a stable, alphabetical
    resting state before the operator types anything.
    """
    lang = normalize_language(language)
    entries = [_localized(term_id, lang) for term_id in GLOSSARY_DATA]
    if section:
        wanted = section.strip().lower()
        entries = [entry for entry in entries if wanted in entry.screens]
    return sorted(entries, key=lambda entry: _fold(entry.term))


def _score(entry: GlossaryEntry, needle: str, section: str | None) -> int:
    term = _fold(entry.term)
    definition = _fold(entry.definition)

    if term == needle:
        score = _SCORE_EXACT_TERM
    elif term.startswith(needle):
        score = _SCORE_TERM_PREFIX
    elif any(word.startswith(needle) for word in term.replace("/", " ").split()):
        score = _SCORE_TERM_WORD
    elif needle in term:
        score = _SCORE_TERM_SUBSTRING
    elif needle in definition:
        score = _SCORE_DEFINITION
    else:
        return 0

    if section and section.strip().lower() in entry.screens:
        score += _SCORE_SCREEN_BONUS
    return score


def search(
    query: str,
    language: str | None = None,
    *,
    section: str | None = None,
    limit: int = 8,
) -> list[GlossaryEntry]:
    """Rank glossary entries against a free-text query.

    Matches against the localized term *and* the localized definition, because
    the box is documented as "search by term or by wording inside a
    definition". Terms tagged for the caller's current screen get a small
    bonus so an ambiguous word resolves the way the operator expects.
    """
    lang = normalize_language(language)
    needle = _fold((query or "").strip())
    if len(needle) < MIN_QUERY_LENGTH:
        return []

    scored: list[tuple[int, str, GlossaryEntry]] = []
    for term_id in GLOSSARY_DATA:
        entry = _localized(term_id, lang)
        score = _score(entry, needle, section)
        if score:
            scored.append((score, _fold(entry.term), entry))

    scored.sort(key=lambda row: (-row[0], row[1]))
    return [entry for _, _, entry in scored[:limit]]


def lookup(query: str, language: str | None = None, *, section: str | None = None) -> Optional[GlossaryEntry]:
    """Return the single best match for a query, or ``None``."""
    matches = search(query, language, section=section, limit=1)
    return matches[0] if matches else None


def entry_by_id(term_id: str, language: str | None = None) -> Optional[GlossaryEntry]:
    if term_id not in GLOSSARY_DATA:
        return None
    return _localized(term_id, normalize_language(language))


def entries_for(
    hints: Iterable[tuple[str, Optional[str]]],
    language: str | None = None,
) -> list[GlossaryEntry]:
    """Resolve ``(label, explicit_term_id)`` pairs onto glossary entries.

    An explicit identifier always wins: some concepts are worded differently
    from the glossary term that defines them (*Maintenance window* is defined
    under *Work order*), and a heuristic would land on the wrong entry.
    """
    lang = normalize_language(language)
    resolved: list[GlossaryEntry] = []
    seen: set[str] = set()
    for label, explicit in hints:
        term_id = explicit if explicit in GLOSSARY_DATA else _best_term_for_label(label)
        if term_id and term_id not in seen:
            seen.add(term_id)
            resolved.append(_localized(term_id, lang))
    return resolved


def entries_for_labels(labels: Iterable[str], language: str | None = None) -> list[GlossaryEntry]:
    """Resolve canonical English concept labels onto glossary entries.

    ``context.py`` deliberately knows nothing about glossary identifiers, so it
    hands over English labels such as ``"Lining risk"``. The whole label is
    tried first; when the glossary has no term under that exact wording -- a
    concept like "Energy cost" against a term called "Energy intensity (GJ/t)"
    -- the label's own words are tried in turn, longest first. Results are
    rendered in the caller's language.
    """
    return entries_for(((label, None) for label in labels), language)


def _best_term_for_label(label: str) -> Optional[str]:
    needle = _fold(label.strip())
    if not needle:
        return None

    best: tuple[int, str] | None = None
    for term_id in GLOSSARY_DATA:
        english = _fold(cast(dict[str, str], GLOSSARY_DATA[term_id]["term"])[DEFAULT_LANGUAGE])
        if english == needle:
            score = _SCORE_EXACT_TERM
        elif english.startswith(needle) or needle in english:
            score = _SCORE_TERM_SUBSTRING
        else:
            continue
        if best is None or score > best[0]:
            best = (score, term_id)
    if best:
        return best[1]

    # Fall back to the label's individual words so a concept still lands on a
    # relevant definition instead of leaving the answer ungrounded.
    words = sorted(
        (word for word in needle.replace("/", " ").split() if len(word) >= 3),
        key=len,
        reverse=True,
    )
    for word in words:
        matches = search(word, DEFAULT_LANGUAGE, limit=1)
        if matches:
            return matches[0].term_id
    return None
