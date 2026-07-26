"""Tests for M6.1 — Reflection / critic loop.

Tests that:
- A well-grounded draft is approved on the first pass.
- A poorly-grounded draft forces exactly one revision (iteration cap honoured).
- The 2-iteration cap is enforced.
- Audit log records every iteration.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from knowledge_orchestrator.adapters.base import AgentResult
from knowledge_orchestrator.adapters.local_foundry import LocalFoundryKnowledgeAgent
from knowledge_orchestrator.audit import AuditLog
from knowledge_orchestrator.critic import (
    CriticResult,
    CriticVerdict,
    DeterministicCritic,
    LLMCritic,
    MAX_CRITIC_ITERATIONS,
    ReflectionOutcome,
    run_reflection_loop,
)
from knowledge_orchestrator.models import (
    Citation,
    ExtractedKnowledge,
    SourceType,
    Transcript,
    TranscriptSegment,
)


@pytest.fixture
def good_transcript():
    return Transcript(
        session_id="IV-CRITIC-001",
        language="en",
        status="COMPLETED",
        segments=(
            TranscriptSegment("seg-001", "Operator A", 0, 10,
                              "The hearth temperature rises above normal.", 0.95),
            TranscriptSegment("seg-002", "Operator A", 10, 20,
                              "Check the cooling water flow.", 0.93),
            TranscriptSegment("seg-003", "Operator A", 20, 30,
                              "Never bypass the alarm without approval.", 0.97),
        ),
    )


class TestDeterministicCritic:
    def test_approves_well_grounded_draft(self, good_transcript):
        knowledge = ExtractedKnowledge(
            observation="Temperature rises.",
            recommended_check="Check cooling flow.",
            rationale="Indicates degradation.",
            safety_boundary="Never bypass alarm.",
            citations=(
                Citation(SourceType.TRANSCRIPT_SEGMENT, "seg-001", "temp rises"),
            ),
        )
        critic = DeterministicCritic()
        result = critic.critique(knowledge, good_transcript)
        assert result.verdict == CriticVerdict.APPROVE

    def test_revises_missing_citations(self, good_transcript):
        knowledge = ExtractedKnowledge(
            observation="Temperature rises.",
            recommended_check="Check cooling flow.",
            rationale="Indicates degradation.",
            safety_boundary="Never bypass alarm.",
            citations=(),  # No citations!
        )
        critic = DeterministicCritic()
        result = critic.critique(knowledge, good_transcript)
        assert result.verdict == CriticVerdict.REVISE
        assert any("no citations" in r for r in result.reasons)

    def test_revises_invalid_segment_id(self, good_transcript):
        knowledge = ExtractedKnowledge(
            observation="Temperature rises.",
            recommended_check="Check cooling flow.",
            rationale="Indicates degradation.",
            safety_boundary="Never bypass alarm.",
            citations=(
                Citation(SourceType.TRANSCRIPT_SEGMENT, "seg-FAKE", "fake"),
            ),
        )
        critic = DeterministicCritic()
        result = critic.critique(knowledge, good_transcript)
        assert result.verdict == CriticVerdict.REVISE
        assert any("seg-FAKE" in r for r in result.reasons)

    def test_revises_empty_safety_boundary(self, good_transcript):
        knowledge = ExtractedKnowledge(
            observation="Temperature rises.",
            recommended_check="Check cooling flow.",
            rationale="Indicates degradation.",
            safety_boundary="",
            citations=(
                Citation(SourceType.TRANSCRIPT_SEGMENT, "seg-001", "text"),
            ),
        )
        critic = DeterministicCritic()
        result = critic.critique(knowledge, good_transcript)
        assert result.verdict == CriticVerdict.REVISE


class TestLLMCritic:
    def test_approve_response(self, good_transcript):
        mock_complete = MagicMock(return_value="APPROVE")
        critic = LLMCritic(mock_complete)
        knowledge = ExtractedKnowledge(
            observation="Obs", recommended_check="Check",
            rationale="Rat", safety_boundary="Safety",
            citations=(Citation(SourceType.TRANSCRIPT_SEGMENT, "seg-001", "t"),),
        )
        result = critic.critique(knowledge, good_transcript)
        assert result.verdict == CriticVerdict.APPROVE

    def test_revise_response(self, good_transcript):
        mock_complete = MagicMock(return_value="REVISE: missing citation, unclear safety")
        critic = LLMCritic(mock_complete)
        knowledge = ExtractedKnowledge(
            observation="Obs", recommended_check="Check",
            rationale="Rat", safety_boundary="Safety",
            citations=(Citation(SourceType.TRANSCRIPT_SEGMENT, "seg-001", "t"),),
        )
        result = critic.critique(knowledge, good_transcript)
        assert result.verdict == CriticVerdict.REVISE
        assert "missing citation" in result.reasons

    def test_fallback_on_exception(self, good_transcript):
        mock_complete = MagicMock(side_effect=RuntimeError("network error"))
        critic = LLMCritic(mock_complete)
        knowledge = ExtractedKnowledge(
            observation="Obs", recommended_check="Check",
            rationale="Rat", safety_boundary="Safety",
            citations=(Citation(SourceType.TRANSCRIPT_SEGMENT, "seg-001", "t"),),
        )
        result = critic.critique(knowledge, good_transcript)
        # Falls back to deterministic — should still return a verdict.
        assert result.verdict in (CriticVerdict.APPROVE, CriticVerdict.REVISE)


class TestReflectionLoop:
    def test_well_grounded_draft_approved_first_pass(self, good_transcript):
        agent = LocalFoundryKnowledgeAgent()
        critic = DeterministicCritic()
        audit = AuditLog()

        outcome = run_reflection_loop(
            agent=agent,
            critic=critic,
            task="Extract a procedure",
            transcript=good_transcript,
            audit=audit,
            correlation_id="test-reflect-1",
        )

        assert outcome.approved
        assert outcome.final_result.knowledge is not None
        assert len(outcome.iterations) == 1
        assert outcome.iterations[0].verdict == CriticVerdict.APPROVE
        assert not outcome.capped

    def test_poorly_grounded_forces_revision(self, good_transcript):
        """A mock agent that produces bad output first, then good output."""
        bad_knowledge = ExtractedKnowledge(
            observation="Obs", recommended_check="Check",
            rationale="Rat", safety_boundary="Safety",
            citations=(),  # No citations → critic should revise.
        )
        good_knowledge = ExtractedKnowledge(
            observation="Temperature rises.",
            recommended_check="Check cooling flow.",
            rationale="Indicates degradation.",
            safety_boundary="Never bypass alarm.",
            citations=(Citation(SourceType.TRANSCRIPT_SEGMENT, "seg-001", "text"),),
        )

        call_count = [0]

        class MockAgent:
            agent_name = "knowledge-capture"

            def extract_draft(self, task, transcript):
                call_count[0] += 1
                if call_count[0] == 1:
                    return AgentResult(refused=False, knowledge=bad_knowledge, trace=("first",))
                return AgentResult(refused=False, knowledge=good_knowledge, trace=("second",))

        agent = MockAgent()
        critic = DeterministicCritic()
        audit = AuditLog()

        outcome = run_reflection_loop(
            agent=agent,
            critic=critic,
            task="Extract",
            transcript=good_transcript,
            audit=audit,
            correlation_id="test-reflect-2",
        )

        assert outcome.approved
        assert call_count[0] == 2  # Extracted twice.
        assert len(outcome.iterations) == 2
        assert outcome.iterations[0].verdict == CriticVerdict.REVISE
        assert outcome.iterations[1].verdict == CriticVerdict.APPROVE

    def test_iteration_cap_enforced(self, good_transcript):
        """Agent always produces ungrounded output — should cap at MAX_CRITIC_ITERATIONS."""
        bad_knowledge = ExtractedKnowledge(
            observation="Obs", recommended_check="Check",
            rationale="Rat", safety_boundary="Safety",
            citations=(),  # Always bad.
        )

        class AlwaysBadAgent:
            agent_name = "knowledge-capture"

            def extract_draft(self, task, transcript):
                return AgentResult(refused=False, knowledge=bad_knowledge, trace=("bad",))

        agent = AlwaysBadAgent()
        critic = DeterministicCritic()
        audit = AuditLog()

        outcome = run_reflection_loop(
            agent=agent,
            critic=critic,
            task="Extract",
            transcript=good_transcript,
            audit=audit,
            correlation_id="test-cap",
        )

        # Should have hit the cap.
        assert outcome.capped
        assert len(outcome.iterations) == MAX_CRITIC_ITERATIONS + 1

    def test_audit_log_records_iterations(self, good_transcript):
        agent = LocalFoundryKnowledgeAgent()
        critic = DeterministicCritic()
        audit = AuditLog()

        run_reflection_loop(
            agent=agent,
            critic=critic,
            task="Extract a procedure",
            transcript=good_transcript,
            audit=audit,
            correlation_id="test-audit",
        )

        records = audit.query(domain="knowledge")
        assert len(records) >= 1
        actions = [r.action for r in records]
        assert any("reflection.critic" in a for a in actions)
