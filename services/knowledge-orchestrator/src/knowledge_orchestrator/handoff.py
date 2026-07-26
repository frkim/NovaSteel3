"""Multi-agent handoff: energy-dispatch ↔ RUL/scoring negotiation (M6).

Implements the rubric's "coordination patterns such as handoffs" by defining a
clean protocol for the energy-dispatch agent to hand off to the scoring/RUL agent
when a proposed schedule would push a furnace past its RUL threshold.

The RUL agent returns a constraint (max remaining cycles / earliest deadline);
the dispatch agent re-plans respecting that constraint. This models the real
business tension: schedules that are both cheap AND safe.

**Design note:** the optimizer-worker and scoring-worker services are owned by
other agents. This module defines only the *interface/protocol* and the handoff
orchestration logic. The actual workers plug in via the protocol.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Protocol

from .audit import AuditLog

logger = logging.getLogger(__name__)


# --- Protocols (ports for optimizer & scoring workers) -----------------------


@dataclass(frozen=True)
class ScheduleProposal:
    """A proposed energy schedule for one or more furnaces."""

    schedule_id: str
    furnace_id: str
    planned_slots: tuple[int, ...]  # time-slot indices
    total_mwh: float
    estimated_co2_kg: float


@dataclass(frozen=True)
class RULConstraint:
    """Constraint returned by the RUL/scoring agent."""

    furnace_id: str
    remaining_useful_life_days: float
    max_safe_heats: int
    threshold_exceeded: bool
    reason: str


@dataclass(frozen=True)
class ReplanResult:
    """Result of re-planning after a RUL constraint is applied."""

    schedule_id: str
    furnace_id: str
    adjusted_slots: tuple[int, ...]
    constraint_applied: str
    total_mwh: float
    estimated_co2_kg: float


class RULScoringPort(Protocol):
    """Port for the RUL/scoring agent — evaluates whether a schedule is safe."""

    def evaluate_schedule_safety(
        self, proposal: ScheduleProposal
    ) -> RULConstraint: ...


class DispatchReplanPort(Protocol):
    """Port for the dispatch agent to re-plan with a constraint."""

    def replan_with_constraint(
        self, proposal: ScheduleProposal, constraint: RULConstraint
    ) -> ReplanResult: ...


# --- Deterministic fixtures for demo/test mode ------------------------------


class LocalRULScorer:
    """Deterministic fixture: flags proposals that exceed the configured threshold."""

    def __init__(
        self,
        rul_days: float = 25.0,
        max_safe_heats: int = 8,
        threshold_days: float = 21.0,
    ):
        self._rul_days = rul_days
        self._max_safe_heats = max_safe_heats
        self._threshold = threshold_days

    def evaluate_schedule_safety(
        self, proposal: ScheduleProposal
    ) -> RULConstraint:
        heats_requested = len(proposal.planned_slots)
        exceeded = (
            self._rul_days <= self._threshold
            or heats_requested > self._max_safe_heats
        )
        reason = (
            f"RUL {self._rul_days:.0f}d <= threshold {self._threshold:.0f}d"
            if self._rul_days <= self._threshold
            else (
                f"requested {heats_requested} heats > max safe {self._max_safe_heats}"
                if heats_requested > self._max_safe_heats
                else "within safe limits"
            )
        )
        return RULConstraint(
            furnace_id=proposal.furnace_id,
            remaining_useful_life_days=self._rul_days,
            max_safe_heats=self._max_safe_heats,
            threshold_exceeded=exceeded,
            reason=reason,
        )


class LocalDispatchReplanner:
    """Deterministic fixture: trims scheduled heats to respect the RUL constraint."""

    def replan_with_constraint(
        self, proposal: ScheduleProposal, constraint: RULConstraint
    ) -> ReplanResult:
        # Trim to max_safe_heats.
        safe_slots = proposal.planned_slots[: constraint.max_safe_heats]
        ratio = len(safe_slots) / max(len(proposal.planned_slots), 1)
        return ReplanResult(
            schedule_id=proposal.schedule_id,
            furnace_id=proposal.furnace_id,
            adjusted_slots=safe_slots,
            constraint_applied=constraint.reason,
            total_mwh=proposal.total_mwh * ratio,
            estimated_co2_kg=proposal.estimated_co2_kg * ratio,
        )


# --- Handoff orchestration ---------------------------------------------------


@dataclass(frozen=True)
class HandoffOutcome:
    """Result of the dispatch→scoring handoff negotiation."""

    handoff_triggered: bool
    original_proposal: ScheduleProposal
    constraint: Optional[RULConstraint] = None
    replan: Optional[ReplanResult] = None
    trace: tuple[str, ...] = ()


def execute_handoff(
    *,
    proposal: ScheduleProposal,
    rul_scorer: RULScoringPort,
    replanner: DispatchReplanPort,
    audit: Optional[AuditLog] = None,
    correlation_id: str = "",
) -> HandoffOutcome:
    """Execute the energy-dispatch → RUL scoring handoff.

    If the RUL scorer reports the schedule exceeds the safety threshold,
    hands off to the scoring agent for a constraint, then the dispatch agent
    re-plans. Logs every step to the audit trail.
    Each hop emits an OpenTelemetry span when telemetry is active.
    """
    from .telemetry import handoff_span

    trace: list[str] = []

    # Step 1: RUL evaluation.
    with handoff_span(
        "handoff.rul_check",
        correlation_id,
        furnace_id=proposal.furnace_id,
        schedule_id=proposal.schedule_id,
    ) as span:
        constraint = rul_scorer.evaluate_schedule_safety(proposal)
        if span is not None:
            try:
                span.set_attribute("novasteel.handoff.rul_days", constraint.remaining_useful_life_days)
                span.set_attribute("novasteel.handoff.threshold_exceeded", constraint.threshold_exceeded)
                span.set_attribute("novasteel.handoff.decision",
                                   "HANDOFF_TRIGGERED" if constraint.threshold_exceeded else "SAFE")
            except Exception:
                pass

    trace.append(
        f"rul_eval: furnace={constraint.furnace_id} "
        f"rul={constraint.remaining_useful_life_days:.0f}d "
        f"exceeded={constraint.threshold_exceeded}"
    )

    if audit is not None:
        audit.append(
            correlation_id=correlation_id,
            domain="energy",
            action="handoff.rul_check",
            entity_id=proposal.schedule_id,
            actor="scoring-agent",
            inputs={
                "furnace_id": proposal.furnace_id,
                "heats": len(proposal.planned_slots),
            },
            output={
                "rul_days": constraint.remaining_useful_life_days,
                "max_safe_heats": constraint.max_safe_heats,
                "exceeded": constraint.threshold_exceeded,
            },
            decision="HANDOFF_TRIGGERED" if constraint.threshold_exceeded else "SAFE",
        )

    if not constraint.threshold_exceeded:
        trace.append("no handoff needed: schedule within safe limits")
        return HandoffOutcome(
            handoff_triggered=False,
            original_proposal=proposal,
            constraint=constraint,
            trace=tuple(trace),
        )

    # Step 2: Handoff — dispatch agent re-plans with constraint.
    trace.append(f"handoff: dispatch→scoring constraint={constraint.reason}")

    with handoff_span(
        "handoff.replan",
        correlation_id,
        furnace_id=proposal.furnace_id,
        constraint_reason=constraint.reason,
    ) as span:
        replan = replanner.replan_with_constraint(proposal, constraint)
        if span is not None:
            try:
                span.set_attribute("novasteel.handoff.adjusted_heats", len(replan.adjusted_slots))
                span.set_attribute("novasteel.handoff.co2_kg", replan.estimated_co2_kg)
                span.set_attribute("novasteel.handoff.decision", "REPLANNED")
            except Exception:
                pass

    trace.append(
        f"replan: adjusted to {len(replan.adjusted_slots)} slots, "
        f"co2={replan.estimated_co2_kg:.0f}kg"
    )

    if audit is not None:
        audit.append(
            correlation_id=correlation_id,
            domain="energy",
            action="handoff.replan",
            entity_id=proposal.schedule_id,
            actor="energy-dispatch-agent",
            inputs={
                "constraint": constraint.reason,
                "original_heats": len(proposal.planned_slots),
            },
            output={
                "adjusted_heats": len(replan.adjusted_slots),
                "co2_kg": replan.estimated_co2_kg,
            },
            decision="REPLANNED",
        )

    return HandoffOutcome(
        handoff_triggered=True,
        original_proposal=proposal,
        constraint=constraint,
        replan=replan,
        trace=tuple(trace),
    )
