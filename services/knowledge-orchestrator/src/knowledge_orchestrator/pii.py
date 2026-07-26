"""PII detection, redaction, and pseudonymization for the NovaSteel orchestrator.

Detects personally identifiable information (PII) in text and provides two
removal strategies:

* **redact** — replaces each match with ``[REDACTED:{KIND}]``, a stable opaque
  marker suitable for audit logs and cross-boundary outputs (GDPR Art. 5(1)(c)).
* **pseudonymize** — replaces each match with ``[{KIND}:{hash8}]`` where
  ``hash8 = sha256(salt + normalized_text)[:8]``, allowing per-session linkage
  for GDPR-safe analytics without re-identification across sessions.

``PiiMatch.__repr__`` never exposes the raw matched text (mirrors the
``_redact`` convention in ``audit.py`` for sensitive field values).

Categories detected:
    email         — standard email addresses
    phone         — international / EU phone numbers (E.164 and local formats)
    iban          — IBANs validated by the ISO 13616 mod-97 checksum
    person_name   — names following operator-role context keywords
    employee_id   — EMP-##### badge IDs
    ipv4          — IPv4 dotted-quad addresses
    dob           — dates of birth following contextual keywords

Overlapping matches: the longest span is kept; ties broken by earliest start.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Callable


# ---------------------------------------------------------------------------
# PiiMatch dataclass
# ---------------------------------------------------------------------------


@dataclass
class PiiMatch:
    """A single PII detection hit.

    The raw ``text`` field MUST NOT be logged directly — use ``__repr__``
    or ``redact()`` for any output that may enter a log sink. This mirrors
    the ``_redact`` sentinel in ``audit.py`` that replaces sensitive values
    with ``[REDACTED]``.
    """

    kind: str   # e.g. "email", "phone", "iban", …
    start: int  # character offset (inclusive) in the source text
    end: int    # character offset (exclusive) in the source text
    text: str   # raw matched text — NEVER log this field directly

    def __repr__(self) -> str:
        # Raw PII value is always redacted in repr, consistent with audit.py
        # _redact() which replaces sensitive dict values with "[REDACTED]".
        return (
            f"PiiMatch(kind={self.kind!r}, "
            f"start={self.start}, "
            f"end={self.end}, "
            f"text='[REDACTED]')"
        )


# ---------------------------------------------------------------------------
# RedactionResult
# ---------------------------------------------------------------------------


@dataclass
class RedactionResult:
    """Result of redacting PII from a text string."""

    text: str                    # redacted text with [REDACTED:{KIND}] markers
    matches: list[PiiMatch]      # resolved (non-overlapping) matches, in document order
    counts: dict[str, int]       # {kind: occurrence_count}


# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# Email addresses — RFC 5321 subset; avoids matching bare hostnames.
_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

# International / EU phone numbers.
# Matches: E.164 (+CC area subscriber), EU-local (0X XX XX XX XX style).
# Requires space/dash/dot separators (excludes bare digit runs like timestamps).
_PHONE_RE = re.compile(
    r"(?<!\d)"
    r"(?:"
    r"\+\d{1,3}[\s\-.]?\d{1,4}(?:[\s\-.]\d{2,4}){2,5}"  # E.164 international
    r"|00\d{2,3}[\s\-.]?\d{4,12}"                         # 00CC international
    r"|0\d[\s\-.]\d{2}(?:[\s\-.]\d{2}){3}"                # EU local 0X XX XX XX XX
    r")"
    r"(?!\d)",
    re.ASCII,
)

# IBAN candidate: 2-letter country code + 2 check digits + 11–28 BBAN chars.
# Compact (no spaces) form; validated by mod-97 before being emitted.
# The lookbehind/lookahead prevent partial matches inside longer alphanumeric runs.
_IBAN_CANDIDATE_RE = re.compile(
    r"(?<![A-Z\d])([A-Z]{2}\d{2}[A-Z0-9]{11,28})(?![A-Z0-9])"
)

# Person names following an operator-role keyword (case-insensitive for the keyword).
# Name requires Title-Case words (each word starts with uppercase — the (?i:…) scoped
# inline flag applies only to the keyword group, not to the name capture).
_PERSON_NAME_RE = re.compile(
    r"(?i:(?:operator|interviewee|expert|technician|engineer)\s*[:\-]\s*)"
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"
)

# Employee / badge ID: EMP- followed by exactly 5 digits.
_EMP_ID_RE = re.compile(r"\bEMP-\d{5}\b")

# IPv4 dotted-quad (strict octet validation, word-boundary anchors).
_IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

# Dates of birth following contextual keywords.
# The capture group (group 1) is the date value only; the surrounding context stays.
_DOB_RE = re.compile(
    r"(?:born(?:\s+on)?|dob|date\s+of\s+birth)\s*[:\-]?\s*"
    r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}"
    r"|\d{1,2}\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?"
    r"|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?"
    r"|nov(?:ember)?|dec(?:ember)?)\s+\d{2,4}"
    r"|\d{4})",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# IBAN mod-97 validation (ISO 13616)
# ---------------------------------------------------------------------------


def _validate_iban(iban: str) -> bool:
    """Return True if *iban* satisfies the ISO 13616 mod-97 check.

    Algorithm:
    1. Strip spaces and convert to uppercase.
    2. Move the first 4 characters to the end.
    3. Replace each letter with its decimal value (A=10, …, Z=35).
    4. Interpret the resulting digit string as an integer; it must equal 1 mod 97.
    """
    cleaned = re.sub(r"\s", "", iban).upper()
    if not (15 <= len(cleaned) <= 34):
        return False
    rearranged = cleaned[4:] + cleaned[:4]
    # Convert letters to their numeric equivalents (A=10, B=11, ..., Z=35).
    numeric_str = "".join(
        str(ord(c) - 55) if c.isalpha() else c for c in rearranged
    )
    return int(numeric_str) % 97 == 1


# ---------------------------------------------------------------------------
# Overlap resolution
# ---------------------------------------------------------------------------


def _resolve_overlaps(matches: list[PiiMatch]) -> list[PiiMatch]:
    """Return a non-overlapping subset of *matches*, keeping the longest span.

    When two matches overlap:
    * Keep the one with the greater span length.
    * On a tie, keep the one with the smaller ``start`` offset.

    The result is sorted in document order (ascending ``start``).
    """
    if not matches:
        return []

    # Greedy longest-first selection: sort by span length descending, then
    # by start ascending, then process each candidate.
    sorted_candidates = sorted(
        matches, key=lambda m: (-(m.end - m.start), m.start)
    )

    accepted: list[PiiMatch] = []
    for candidate in sorted_candidates:
        # Accept if the candidate does not overlap any already-accepted match.
        if not any(
            candidate.start < a.end and candidate.end > a.start
            for a in accepted
        ):
            accepted.append(candidate)

    return sorted(accepted, key=lambda m: m.start)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


def detect(text: str) -> list[PiiMatch]:
    """Detect all PII in *text* and return a non-overlapping list in document order.

    When matches from different detectors overlap, the longest span is kept;
    ties are broken by earliest start position.
    """
    candidates: list[PiiMatch] = []

    for m in _EMAIL_RE.finditer(text):
        candidates.append(PiiMatch("email", m.start(), m.end(), m.group()))

    for m in _PHONE_RE.finditer(text):
        candidates.append(PiiMatch("phone", m.start(), m.end(), m.group()))

    for m in _IBAN_CANDIDATE_RE.finditer(text):
        raw = m.group(1)
        if _validate_iban(raw):
            candidates.append(PiiMatch("iban", m.start(1), m.end(1), raw))

    for m in _PERSON_NAME_RE.finditer(text):
        # Only capture the name part (group 1), not the role keyword prefix.
        candidates.append(
            PiiMatch("person_name", m.start(1), m.end(1), m.group(1))
        )

    for m in _EMP_ID_RE.finditer(text):
        candidates.append(PiiMatch("employee_id", m.start(), m.end(), m.group()))

    for m in _IPV4_RE.finditer(text):
        candidates.append(PiiMatch("ipv4", m.start(), m.end(), m.group()))

    for m in _DOB_RE.finditer(text):
        # Only capture the date value (group 1), leaving the context keyword intact.
        candidates.append(PiiMatch("dob", m.start(1), m.end(1), m.group(1)))

    return _resolve_overlaps(candidates)


# ---------------------------------------------------------------------------
# Span replacement helper
# ---------------------------------------------------------------------------


def _replace_spans(
    text: str,
    matches: list[PiiMatch],
    replacement_fn: Callable[[PiiMatch], str],
) -> str:
    """Build a new string by replacing each matched span with ``replacement_fn(match)``.

    Processes matches in *reverse* document order so earlier offsets remain
    valid after each substitution.
    """
    result = text
    for m in reversed(matches):
        result = result[: m.start] + replacement_fn(m) + result[m.end :]
    return result


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------


def redact(text: str) -> RedactionResult:
    """Replace all PII in *text* with ``[REDACTED:{KIND}]`` placeholders.

    Returns a :class:`RedactionResult` containing the redacted text, the list
    of resolved matches (non-overlapping, in document order), and a per-kind
    occurrence count.
    """
    matches = detect(text)
    redacted_text = _replace_spans(
        text, matches, lambda m: f"[REDACTED:{m.kind.upper()}]"
    )
    counts: dict[str, int] = {}
    for m in matches:
        counts[m.kind] = counts.get(m.kind, 0) + 1
    return RedactionResult(text=redacted_text, matches=matches, counts=counts)


# ---------------------------------------------------------------------------
# Pseudonymization
# ---------------------------------------------------------------------------


def pseudonymize(text: str, salt: str) -> str:
    """Replace each PII match with a ``[{KIND}:{hash8}]`` pseudonym.

    ``hash8`` is the first 8 hex characters of ``sha256(salt + normalized_text)``,
    providing deterministic per-session linkability while preventing re-identification
    across sessions that use different salts (GDPR-safe analytics).

    The same ``(salt, original_text)`` pair always produces the same pseudonym,
    so repeated mentions of the same PII value collapse to a single token within
    a session.
    """
    matches = detect(text)

    def _placeholder(m: PiiMatch) -> str:
        normalized = m.text.strip().lower()
        digest = hashlib.sha256(
            f"{salt}{normalized}".encode("utf-8")
        ).hexdigest()[:8]
        return f"[{m.kind.upper()}:{digest}]"

    return _replace_spans(text, matches, _placeholder)
