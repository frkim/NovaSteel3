"""Content-safety screening for the NovaSteel knowledge-orchestrator.

Provides a :class:`ContentSafetyProvider` Protocol and two implementations:

* :class:`LocalHeuristicContentSafety` — deterministic, offline, pattern-based.
  Reuses the injection vocabulary already present in ``prompt_defense`` (no
  duplicate lists) and adds patterns for hate, self-harm, sexual, and violence
  categories.  Works with zero network access.
* :class:`AzureContentSafetyProvider` (in ``adapters/azure_content_safety.py``) —
  calls the Azure AI Content Safety REST API with managed identity; falls back to
  LocalHeuristicContentSafety on any failure.

Severity scale 0–7 (aligns with Azure's FourSeverityLevels mapped to 0,2,4,6
with 7 reserved for fail-closed conditions):
    0   Clean / no signal
    2   Mild / low-confidence
    4   Moderate / actionable
    6   Severe / explicit
    7   Fail-closed sentinel (Azure adapter only)

Default block threshold: severity ≥ 4.
"""

from __future__ import annotations

import enum
import re
import time
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from . import prompt_defense


# ---------------------------------------------------------------------------
# Enums and dataclasses
# ---------------------------------------------------------------------------


class SafetyCategory(str, enum.Enum):
    HATE = "hate"
    SELFHARM = "selfharm"
    SEXUAL = "sexual"
    VIOLENCE = "violence"
    JAILBREAK = "jailbreak"
    PROMPT_INJECTION = "prompt_injection"


@dataclass
class SafetyVerdict:
    """Result of a content-safety screening pass."""

    allowed: bool                   # True if no category exceeded the threshold
    categories: dict[str, int]      # {category_name: severity_0_to_7}
    blockedBy: list[str]            # category names that exceeded the threshold
    providerUsed: str               # which provider produced this verdict
    latencyMs: float                # wall-clock milliseconds for the analysis call


DEFAULT_BLOCK_THRESHOLD: int = 4


# ---------------------------------------------------------------------------
# ContentSafetyProvider Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class ContentSafetyProvider(Protocol):
    """Protocol for pluggable content-safety backends.

    Implementors return a raw severity score (0–7) for each :class:`SafetyCategory`.
    The :func:`screen_input` / :func:`screen_output` helpers apply the configurable
    threshold and build the :class:`SafetyVerdict`.
    """

    name: str

    def analyze(self, text: str) -> dict[str, int]:
        """Return severity scores (0–7) keyed by :class:`SafetyCategory` value."""
        ...


# ---------------------------------------------------------------------------
# Offline heuristic patterns
# ---------------------------------------------------------------------------

# Hate speech — explicit dehumanisation, calls to eliminate groups.
_HATE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(?:hate|inferior|subhuman|exterminate)\s+(?:race|ethnic|religion|group)\b",
        re.I,
    ),
    re.compile(r"\b(?:kill|eliminate|destroy)\s+all\s+\w+\b", re.I),
    re.compile(r"\b(?:racial|ethnic)\s+(?:cleansing|slur)\b", re.I),
]

# Self-harm — direct references to harming oneself.
_SELFHARM_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:self[\-\s]?harm|self[\-\s]?injur|suicide|suicidal)\b", re.I),
    re.compile(r"\bhow\s+to\s+(?:kill|hurt|harm)\s+(?:my|your)self\b", re.I),
    re.compile(r"\b(?:cut|burn)\s+myself\b", re.I),
]

# Sexual — explicit sexual content.
_SEXUAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:explicit\s+sexual|pornograph|nude\s+image|child\s+sex)\b", re.I),
    re.compile(r"\b(?:sexual\s+abuse|sexual\s+exploit)\b", re.I),
]

# Violence — instructions or threats for physical harm.
_VIOLENCE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(?:bomb|explosive|weapon|grenade)\s+(?:how|make|build|create|instructions)\b",
        re.I,
    ),
    re.compile(r"\bhow\s+to\s+(?:make|build|assemble)\s+a\s+(?:bomb|weapon|explosive)\b", re.I),
    re.compile(r"\b(?:threaten|assault|murder|kill)\s+(?:someone|a\s+person)\b", re.I),
    re.compile(r"\b(?:attack|shooting|stabbing)\s+plan\b", re.I),
]

# Base64-ish blobs — long runs of base64 characters may encode hidden payloads.
_BASE64_BLOB_RE = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")

# Tool-name smuggling — references to internal tool/function names in user text.
_TOOL_SMUGGLE_RE = re.compile(
    r"\b(?:approve_procedure|publish_procedure|delete_session|"
    r"commit_draft|schedule_audit)\b",
    re.I,
)


# ---------------------------------------------------------------------------
# LocalHeuristicContentSafety
# ---------------------------------------------------------------------------


class LocalHeuristicContentSafety:
    """Offline, deterministic content-safety provider using pattern matching.

    Reuses the injection-detection vocabulary from :mod:`prompt_defense` for
    the jailbreak and prompt_injection categories, avoiding a second maintenance
    burden on those pattern lists.

    Catches the classic injection strings described in the threat model:
    "ignore previous instructions", "you are now DAN", base64-ish blobs, and
    tool-name smuggling.  All pattern checks are stateless and side-effect-free.
    """

    name: str = "LocalHeuristicContentSafety"

    def analyze(self, text: str) -> dict[str, int]:
        """Return severity scores (0–7) for each :class:`SafetyCategory`."""
        scores: dict[str, int] = {cat.value: 0 for cat in SafetyCategory}

        if not text:
            return scores

        # --- Hate ---
        for rx in _HATE_PATTERNS:
            if rx.search(text):
                scores["hate"] = max(scores["hate"], 6)
                break

        # --- Self-harm ---
        for rx in _SELFHARM_PATTERNS:
            if rx.search(text):
                scores["selfharm"] = max(scores["selfharm"], 6)
                break

        # --- Sexual ---
        for rx in _SEXUAL_PATTERNS:
            if rx.search(text):
                scores["sexual"] = max(scores["sexual"], 4)
                break

        # --- Violence ---
        for rx in _VIOLENCE_PATTERNS:
            if rx.search(text):
                scores["violence"] = max(scores["violence"], 6)
                break

        # --- Jailbreak / Prompt Injection (reuse prompt_defense vocabulary) ---
        injection = prompt_defense.scan_for_injection(text)

        if injection.severity is prompt_defense.InjectionSeverity.HIGH:
            scores["jailbreak"] = max(scores["jailbreak"], 6)
            scores["prompt_injection"] = max(scores["prompt_injection"], 6)
        elif injection.severity is prompt_defense.InjectionSeverity.LOW:
            scores["prompt_injection"] = max(scores["prompt_injection"], 2)

        # Explicit DAN pattern (supplements the role-hijack pattern in prompt_defense).
        if re.search(r"\byou\s+are\s+now\s+dan\b", text, re.I):
            scores["jailbreak"] = max(scores["jailbreak"], 6)

        # Base64-ish blobs may contain encoded injection payloads.
        if _BASE64_BLOB_RE.search(text):
            scores["prompt_injection"] = max(scores["prompt_injection"], 4)

        # Tool-name smuggling attempts to trigger internal functions via text.
        if _TOOL_SMUGGLE_RE.search(text):
            scores["prompt_injection"] = max(scores["prompt_injection"], 4)

        return scores


# ---------------------------------------------------------------------------
# Screening helpers
# ---------------------------------------------------------------------------


def screen_input(
    text: str,
    provider: ContentSafetyProvider,
    threshold: int = DEFAULT_BLOCK_THRESHOLD,
) -> SafetyVerdict:
    """Screen user input and return a :class:`SafetyVerdict`.

    Blocks categories at or above *threshold* (default: 4).  Latency includes
    only the ``analyze()`` call, not I/O overhead from the caller.
    """
    return _screen(text, provider, threshold)


def screen_output(
    text: str,
    provider: ContentSafetyProvider,
    threshold: int = DEFAULT_BLOCK_THRESHOLD,
) -> SafetyVerdict:
    """Screen model output and return a :class:`SafetyVerdict`.

    Identical logic to :func:`screen_input`; provided as a distinct entry point
    so callers can apply different thresholds for input vs. output if needed.
    """
    return _screen(text, provider, threshold)


def _screen(
    text: str,
    provider: ContentSafetyProvider,
    threshold: int,
) -> SafetyVerdict:
    t0 = time.monotonic()
    categories = provider.analyze(text)
    latency_ms = (time.monotonic() - t0) * 1000.0

    blocked_by = [cat for cat, sev in categories.items() if sev >= threshold]
    return SafetyVerdict(
        allowed=not bool(blocked_by),
        categories=categories,
        blockedBy=blocked_by,
        providerUsed=provider.name,
        latencyMs=latency_ms,
    )
