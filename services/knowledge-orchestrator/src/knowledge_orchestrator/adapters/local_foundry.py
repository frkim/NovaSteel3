"""Deterministic, offline Foundry knowledge-capture agent for tests and the demo.

This fake reproduces the *governed behaviour* of the real Foundry agent without any
cloud call: it applies the safety meta-prompt and spotlighting, ignores instructions
embedded in the untrusted transcript, and extracts the four required fields
(``observation``, ``recommended_check``, ``rationale``, ``safety_boundary``) with
transcript-segment citations (demo-runbook.md §7, api-contracts §10.3). It writes only
DRAFTs; it never publishes.
"""

from __future__ import annotations

from ..models import (
    Citation,
    ExtractedKnowledge,
    SourceType,
    Transcript,
    TranscriptSegment,
)
from .. import prompt_defense
from .base import AgentResult, FoundryAgentAdapter

# Deterministic keyword buckets used to classify operator statements into the four
# governed extraction fields. Order matters: safety first, then checks.
_SAFETY_HINTS = ("do not", "never", "without", "bypass", "alarm", "approval")
_CHECK_HINTS = ("check", "compare", "inspect", "measure", "validate", "request", "look")
_OBSERVATION_HINTS = ("rise", "warm", "normal", "persist", "drift", "appear", "slower")

_OPERATOR_LABELS = ("operator", "interviewee", "expert")


class LocalFoundryKnowledgeAgent(FoundryAgentAdapter):
    """A deterministic knowledge-capture agent honouring prompt-injection defenses."""

    agent_name = "knowledge-capture"

    def extract_draft(self, task: str, transcript: Transcript) -> AgentResult:
        trace: list[str] = ["applied safety meta-prompt", "spotlighted transcript"]

        # The task itself is trusted input; a direct-injection task is refused.
        task_scan = prompt_defense.scan_for_injection(task)
        if task_scan.severity is prompt_defense.InjectionSeverity.HIGH:
            return AgentResult(
                refused=True,
                knowledge=None,
                trace=tuple(trace + [f"refused: task injection {task_scan.matched_patterns}"]),
                refusal_reason="task contains a prompt-injection attempt",
            )

        observations: list[str] = []
        checks: list[str] = []
        rationales: list[str] = []
        boundaries: list[str] = []
        cited: list[Citation] = []

        for seg in transcript.segments:
            if not _is_operator(seg):
                continue

            scan = prompt_defense.scan_for_injection(seg.text)
            if scan.flagged and scan.severity is prompt_defense.InjectionSeverity.HIGH:
                # Untrusted data cannot issue instructions: ignore, log, do not extract.
                trace.append(
                    f"ignored injected instruction in {seg.segment_id}: "
                    f"{scan.matched_patterns}"
                )
                continue

            bucket = _classify(seg.text)
            citation = Citation(
                source_type=SourceType.TRANSCRIPT_SEGMENT,
                source_id=seg.segment_id,
                quote=seg.text,
            )
            if bucket == "safety":
                boundaries.append(seg.text)
            elif bucket == "check":
                checks.append(seg.text)
            elif bucket == "observation":
                observations.append(seg.text)
            else:
                rationales.append(seg.text)
            cited.append(citation)

        if not cited:
            return AgentResult(
                refused=True,
                knowledge=None,
                trace=tuple(trace + ["refused: no groundable operator content"]),
                refusal_reason="no citable operator knowledge in transcript",
            )

        knowledge = ExtractedKnowledge(
            observation=_join(observations) or "Operator described the observed signal.",
            recommended_check=_join(checks)
            or "Verify related sensors and cooling data before acting.",
            rationale=_join(rationales)
            or "Corroborating signals reduce false positives from sensor faults.",
            safety_boundary=_join(boundaries)
            or "Do not change furnace or cooling controls from interview guidance.",
            citations=tuple(cited),
        )
        trace.append(f"extracted grounded draft with {len(cited)} citations")
        return AgentResult(refused=False, knowledge=knowledge, trace=tuple(trace))


def _is_operator(seg: TranscriptSegment) -> bool:
    return any(lbl in seg.speaker.lower() for lbl in _OPERATOR_LABELS)


def _classify(text: str) -> str:
    lowered = text.lower()
    if any(h in lowered for h in _SAFETY_HINTS):
        return "safety"
    if any(h in lowered for h in _CHECK_HINTS):
        return "check"
    if any(h in lowered for h in _OBSERVATION_HINTS):
        return "observation"
    return "rationale"


def _join(items: list[str]) -> str:
    return " ".join(dict.fromkeys(items)).strip()
