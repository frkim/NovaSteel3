"""Tests for M6.2 — Multi-agent handoff (energy-dispatch ↔ RUL scoring).

Tests that:
- Handoff triggers when a schedule violates an RUL constraint.
- Handoff does NOT trigger when the schedule is safe.
- Re-planning applies the RUL constraint correctly.
- Audit log captures handoff events.
"""

from __future__ import annotations

import pytest

from knowledge_orchestrator.audit import AuditLog
from knowledge_orchestrator.handoff import (
    HandoffOutcome,
    LocalDispatchReplanner,
    LocalRULScorer,
    RULConstraint,
    ReplanResult,
    ScheduleProposal,
    execute_handoff,
)


@pytest.fixture
def safe_proposal():
    """A schedule that fits within default safe limits."""
    return ScheduleProposal(
        schedule_id="SCH-001",
        furnace_id="LUX-BF-01",
        planned_slots=(1, 2, 3),  # 3 heats, well under 8 max.
        total_mwh=150.0,
        estimated_co2_kg=45000.0,
    )


@pytest.fixture
def unsafe_proposal():
    """A schedule that exceeds the max safe heats."""
    return ScheduleProposal(
        schedule_id="SCH-002",
        furnace_id="LUX-BF-01",
        planned_slots=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10),  # 10 heats > 8 max.
        total_mwh=500.0,
        estimated_co2_kg=150000.0,
    )


@pytest.fixture
def low_rul_proposal():
    """A schedule for a furnace with low RUL (below threshold)."""
    return ScheduleProposal(
        schedule_id="SCH-003",
        furnace_id="LUX-BF-02",
        planned_slots=(1, 2, 3),
        total_mwh=150.0,
        estimated_co2_kg=45000.0,
    )


class TestLocalRULScorer:
    def test_safe_schedule_not_exceeded(self, safe_proposal):
        scorer = LocalRULScorer(rul_days=30.0, max_safe_heats=8, threshold_days=21.0)
        constraint = scorer.evaluate_schedule_safety(safe_proposal)
        assert not constraint.threshold_exceeded
        assert constraint.furnace_id == "LUX-BF-01"

    def test_too_many_heats_exceeded(self, unsafe_proposal):
        scorer = LocalRULScorer(rul_days=30.0, max_safe_heats=8, threshold_days=21.0)
        constraint = scorer.evaluate_schedule_safety(unsafe_proposal)
        assert constraint.threshold_exceeded
        assert "10 heats > max safe 8" in constraint.reason

    def test_low_rul_exceeded(self, safe_proposal):
        scorer = LocalRULScorer(rul_days=18.0, max_safe_heats=8, threshold_days=21.0)
        constraint = scorer.evaluate_schedule_safety(safe_proposal)
        assert constraint.threshold_exceeded
        assert "18" in constraint.reason


class TestLocalDispatchReplanner:
    def test_trims_to_max_safe_heats(self, unsafe_proposal):
        constraint = RULConstraint(
            furnace_id="LUX-BF-01",
            remaining_useful_life_days=30.0,
            max_safe_heats=8,
            threshold_exceeded=True,
            reason="too many heats",
        )
        replanner = LocalDispatchReplanner()
        result = replanner.replan_with_constraint(unsafe_proposal, constraint)
        assert len(result.adjusted_slots) == 8
        assert result.total_mwh == unsafe_proposal.total_mwh * (8 / 10)
        assert result.constraint_applied == "too many heats"


class TestHandoffExecution:
    def test_no_handoff_when_safe(self, safe_proposal):
        scorer = LocalRULScorer(rul_days=30.0, max_safe_heats=8, threshold_days=21.0)
        replanner = LocalDispatchReplanner()
        audit = AuditLog()

        outcome = execute_handoff(
            proposal=safe_proposal,
            rul_scorer=scorer,
            replanner=replanner,
            audit=audit,
            correlation_id="test-safe",
        )

        assert not outcome.handoff_triggered
        assert outcome.replan is None
        assert outcome.constraint is not None
        assert not outcome.constraint.threshold_exceeded

    def test_handoff_triggers_on_rul_violation(self, unsafe_proposal):
        scorer = LocalRULScorer(rul_days=30.0, max_safe_heats=8, threshold_days=21.0)
        replanner = LocalDispatchReplanner()
        audit = AuditLog()

        outcome = execute_handoff(
            proposal=unsafe_proposal,
            rul_scorer=scorer,
            replanner=replanner,
            audit=audit,
            correlation_id="test-unsafe",
        )

        assert outcome.handoff_triggered
        assert outcome.replan is not None
        assert len(outcome.replan.adjusted_slots) == 8
        assert outcome.constraint.threshold_exceeded

    def test_handoff_triggers_on_low_rul(self, low_rul_proposal):
        scorer = LocalRULScorer(rul_days=18.0, max_safe_heats=8, threshold_days=21.0)
        replanner = LocalDispatchReplanner()

        outcome = execute_handoff(
            proposal=low_rul_proposal,
            rul_scorer=scorer,
            replanner=replanner,
            correlation_id="test-low-rul",
        )

        assert outcome.handoff_triggered
        assert outcome.constraint.threshold_exceeded

    def test_audit_captures_handoff(self, unsafe_proposal):
        scorer = LocalRULScorer(rul_days=30.0, max_safe_heats=8, threshold_days=21.0)
        replanner = LocalDispatchReplanner()
        audit = AuditLog()

        execute_handoff(
            proposal=unsafe_proposal,
            rul_scorer=scorer,
            replanner=replanner,
            audit=audit,
            correlation_id="test-audit-handoff",
        )

        records = audit.query(domain="energy")
        actions = {r.action for r in records}
        assert "handoff.rul_check" in actions
        assert "handoff.replan" in actions
        assert audit.verify()

    def test_trace_describes_negotiation(self, unsafe_proposal):
        scorer = LocalRULScorer(rul_days=30.0, max_safe_heats=8, threshold_days=21.0)
        replanner = LocalDispatchReplanner()

        outcome = execute_handoff(
            proposal=unsafe_proposal,
            rul_scorer=scorer,
            replanner=replanner,
            correlation_id="test-trace",
        )

        assert any("handoff" in t for t in outcome.trace)
        assert any("replan" in t for t in outcome.trace)
