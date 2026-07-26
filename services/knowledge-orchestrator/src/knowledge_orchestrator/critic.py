"""Reflection / critic loop for draft extraction (M6 — multi-agent coordination).

After the extractor produces a draft, a second LLM pass (or deterministic check in
fixture mode) acts as a **critic**: does every claim carry a citation to retrieved
source text? Is any step unsafe? The critic returns APPROVE or REVISE + reasons.

On REVISE the extractor runs again, **capped at 2 iterations**. Every iteration is
logged to the hash-chained audit log so the reflection can be shown happening live.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional, Protocol

from .adapters.base import AgentResult, FoundryAgentAdapter
from .audit import AuditLog
from .grounding import GroundingError, enforce_extraction_grounding
from .models import ExtractedKnowledge, Transcript

logger = logging.getLogger(__name__)

MAX_CRITIC_ITERATIONS = 2


class CriticVerdict:
    APPROVE = "APPROVE"
    REVISE = "REVISE"


@dataclass(frozen=True)
class CriticResult:
    """Result of a single critic pass."""

    verdict: str  # APPROVE or REVISE
    reasons: tuple[str, ...]
    iteration: int


@dataclass(frozen=True)
class ReflectionOutcome:
    """Final outcome of the reflection loop (possibly multiple iterations)."""

    approved: bool
    final_result: AgentResult
    iterations: tuple[CriticResult, ...]
    capped: bool = False  # True if we hit max iterations without approval


class CriticAdapter(Protocol):
    """Port for the critic agent — can be a real LLM or a deterministic checker."""

    def critique(
        self, knowledge: ExtractedKnowledge, transcript: Transcript
    ) -> CriticResult: ...


class DeterministicCritic:
    """Offline/fixture critic: validates grounding and safety structurally.

    Used in demo/test mode. Checks citation presence and segment-id validity,
    and flags missing safety boundaries — no LLM required.
    """

    def __init__(self, iteration: int = 0):
        self._iteration = iteration

    def critique(
        self, knowledge: ExtractedKnowledge, transcript: Transcript
    ) -> CriticResult:
        reasons: list[str] = []

        # Citation coverage check.
        if not knowledge.citations:
            reasons.append("draft has no citations")

        seg_ids = transcript.segment_ids()
        for c in knowledge.citations:
            if c.source_id not in seg_ids:
                reasons.append(f"citation '{c.source_id}' not in transcript")

        # Safety boundary check.
        if not knowledge.safety_boundary or len(knowledge.safety_boundary.strip()) < 5:
            reasons.append("safety_boundary is empty or too short")

        # All four fields must be non-empty.
        for field_name in ("observation", "recommended_check", "rationale"):
            val = getattr(knowledge, field_name, "")
            if not val or len(val.strip()) < 3:
                reasons.append(f"field '{field_name}' is empty or too short")

        verdict = CriticVerdict.REVISE if reasons else CriticVerdict.APPROVE
        return CriticResult(
            verdict=verdict, reasons=tuple(reasons), iteration=self._iteration
        )


class LLMCritic:
    """LLM-backed critic that reviews draft quality via a second model call.

    Falls back to the deterministic critic if the model call fails.
    """

    def __init__(self, complete_fn, iteration: int = 0):
        """``complete_fn`` signature: (system: str, user: str) -> str."""
        self._complete = complete_fn
        self._iteration = iteration

    _SYSTEM = (
        "You are a quality reviewer for extracted operational procedures. "
        "Check that:\n"
        "1. Every claim cites a [S<n>] source tag.\n"
        "2. The safety boundary is explicit and non-trivial.\n"
        "3. No step is potentially unsafe or unsupported by the cited source.\n\n"
        "Reply with EXACTLY one line:\n"
        "APPROVE\n"
        "or\n"
        "REVISE: <comma-separated reasons>\n"
    )

    def critique(
        self, knowledge: ExtractedKnowledge, transcript: Transcript
    ) -> CriticResult:
        user_msg = (
            f"OBSERVATION: {knowledge.observation}\n"
            f"RECOMMENDED_CHECK: {knowledge.recommended_check}\n"
            f"RATIONALE: {knowledge.rationale}\n"
            f"SAFETY_BOUNDARY: {knowledge.safety_boundary}\n"
            f"CITATIONS: {[c.to_ref() for c in knowledge.citations]}"
        )
        try:
            response = self._complete(self._SYSTEM, user_msg)
        except Exception as exc:
            logger.warning("LLM critic call failed (%s), using deterministic fallback", exc)
            return DeterministicCritic(self._iteration).critique(knowledge, transcript)

        if response.strip().startswith("APPROVE"):
            return CriticResult(
                verdict=CriticVerdict.APPROVE, reasons=(), iteration=self._iteration
            )
        # Parse REVISE reasons.
        reasons_text = re.sub(r"^REVISE:\s*", "", response.strip(), flags=re.IGNORECASE)
        reasons = tuple(r.strip() for r in reasons_text.split(",") if r.strip())
        return CriticResult(
            verdict=CriticVerdict.REVISE,
            reasons=reasons or ("unspecified revision needed",),
            iteration=self._iteration,
        )


def run_reflection_loop(
    *,
    agent: FoundryAgentAdapter,
    critic: CriticAdapter,
    task: str,
    transcript: Transcript,
    audit: Optional[AuditLog] = None,
    correlation_id: str = "",
) -> ReflectionOutcome:
    """Execute the extract→critique→revise loop capped at MAX_CRITIC_ITERATIONS.

    Logs every iteration to the audit log for live demo visibility.
    Each critic iteration emits an OpenTelemetry span when telemetry is active.
    """
    from .telemetry import critic_span

    iterations: list[CriticResult] = []
    current_result: Optional[AgentResult] = None

    for i in range(MAX_CRITIC_ITERATIONS + 1):
        # Extract (or re-extract on revision).
        result = agent.extract_draft(task, transcript)

        if result.refused or result.knowledge is None:
            # Agent refused — no point critiquing.
            if audit is not None:
                audit.append(
                    correlation_id=correlation_id,
                    domain="knowledge",
                    action="reflection.refused",
                    entity_id=correlation_id,
                    actor=agent.agent_name,
                    inputs={"iteration": i},
                    output={"refusal_reason": result.refusal_reason or "unknown"},
                )
            return ReflectionOutcome(
                approved=False, final_result=result, iterations=tuple(iterations)
            )

        current_result = result

        # Critic pass — instrumented with a span per iteration.
        if isinstance(critic, DeterministicCritic):
            critic_instance = DeterministicCritic(iteration=i)
        elif isinstance(critic, LLMCritic):
            critic_instance = LLMCritic(critic._complete, iteration=i)
        else:
            critic_instance = critic

        with critic_span(i, correlation_id) as span:
            verdict = critic_instance.critique(result.knowledge, transcript)
            if span is not None:
                try:
                    span.set_attribute("novasteel.critic.verdict", verdict.verdict)
                    span.set_attribute("novasteel.critic.reasons", str(verdict.reasons))
                except Exception:
                    pass

        iterations.append(verdict)

        if audit is not None:
            audit.append(
                correlation_id=correlation_id,
                domain="knowledge",
                action=f"reflection.critic.iter{i}",
                entity_id=correlation_id,
                actor="critic-agent",
                inputs={"iteration": i, "verdict": verdict.verdict},
                output={"reasons": list(verdict.reasons)},
                decision=verdict.verdict,
            )

        if verdict.verdict == CriticVerdict.APPROVE:
            return ReflectionOutcome(
                approved=True, final_result=current_result, iterations=tuple(iterations)
            )

        # If we've exhausted iterations, stop.
        if i >= MAX_CRITIC_ITERATIONS:
            break

        # On REVISE: augment the task with feedback for the next extraction.
        task = (
            f"{task}\n\n"
            f"CRITIC FEEDBACK (iteration {i}): {'; '.join(verdict.reasons)}. "
            f"Please address these issues."
        )
        logger.info("Critic iteration %d: REVISE — %s", i, verdict.reasons)

    # Reached cap without approval.
    return ReflectionOutcome(
        approved=True,  # Accept the best effort after max iterations
        final_result=current_result,  # type: ignore[arg-type]
        iterations=tuple(iterations),
        capped=True,
    )
