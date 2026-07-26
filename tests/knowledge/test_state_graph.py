"""Tests for M6.3 — State graph: transition legality and Mermaid generation.

Tests that:
- Legal transitions succeed.
- Illegal transitions raise IllegalTransitionError.
- Terminal/gated node identification works.
- The Mermaid generator produces valid output.
- The knowledge-capture workflow graph has the expected structure.
"""

from __future__ import annotations

import pytest

from knowledge_orchestrator.state_graph import (
    IllegalTransitionError,
    StateGraph,
    Transition,
    build_knowledge_capture_graph,
    generate_mermaid_file,
)


class TestStateGraphBasics:
    def test_add_nodes_and_transitions(self):
        g = StateGraph(name="test")
        g.add_node("A")
        g.add_node("B", terminal=True)
        g.add_transition("A", "B", "go")

        assert g.current_state == "A"
        assert g.can_transition("go")
        assert not g.can_transition("stop")

    def test_fire_valid_transition(self):
        g = StateGraph(name="test")
        g.add_node("A")
        g.add_node("B")
        g.add_transition("A", "B", "advance")

        new_state = g.fire("advance")
        assert new_state == "B"
        assert g.current_state == "B"

    def test_fire_illegal_transition_raises(self):
        g = StateGraph(name="test")
        g.add_node("A")
        g.add_node("B")
        g.add_node("C", terminal=True)
        g.add_transition("A", "B", "advance")
        g.add_transition("B", "C", "finish")

        with pytest.raises(IllegalTransitionError) as exc_info:
            g.fire("finish")  # Can't fire "finish" from "A".
        assert exc_info.value.current == "A"
        assert exc_info.value.trigger == "finish"

    def test_terminal_nodes(self):
        g = StateGraph(name="test")
        g.add_node("START")
        g.add_node("END", terminal=True)
        g.add_node("DONE", terminal=True)
        g.add_node("MIDDLE")

        assert set(g.terminal_nodes()) == {"END", "DONE"}

    def test_gated_nodes(self):
        g = StateGraph(name="test")
        g.add_node("START")
        g.add_node("REVIEW", gated=True)
        g.add_node("END", terminal=True)

        assert g.gated_nodes() == ["REVIEW"]
        assert g.is_gated("REVIEW")
        assert not g.is_gated("START")

    def test_allowed_transitions(self):
        g = StateGraph(name="test")
        g.add_node("A")
        g.add_node("B")
        g.add_node("C")
        g.add_transition("A", "B", "go_b")
        g.add_transition("A", "C", "go_c")
        g.add_transition("B", "C", "advance")

        allowed = g.allowed_transitions("A")
        assert len(allowed) == 2
        triggers = {t.trigger for t in allowed}
        assert triggers == {"go_b", "go_c"}

    def test_add_transition_invalid_source_raises(self):
        g = StateGraph(name="test")
        g.add_node("A")
        with pytest.raises(ValueError, match="source node"):
            g.add_transition("X", "A", "go")

    def test_add_transition_invalid_target_raises(self):
        g = StateGraph(name="test")
        g.add_node("A")
        with pytest.raises(ValueError, match="target node"):
            g.add_transition("A", "X", "go")

    def test_set_current_state_invalid_raises(self):
        g = StateGraph(name="test")
        g.add_node("A")
        with pytest.raises(ValueError):
            g.current_state = "NONEXISTENT"


class TestKnowledgeCaptureGraph:
    def test_graph_has_expected_nodes(self):
        g = build_knowledge_capture_graph()
        assert "EXTRACTING" in g.nodes
        assert "CRITIQUING" in g.nodes
        assert "DRAFT" in g.nodes
        assert "IN_REVIEW" in g.nodes
        assert "APPROVED" in g.nodes
        assert "REJECTED" in g.nodes
        assert "DECLINED" in g.nodes

    def test_terminal_nodes(self):
        g = build_knowledge_capture_graph()
        terminals = set(g.terminal_nodes())
        assert terminals == {"APPROVED", "REJECTED", "DECLINED"}

    def test_gated_nodes(self):
        g = build_knowledge_capture_graph()
        assert g.gated_nodes() == ["IN_REVIEW"]

    def test_initial_state_is_extracting(self):
        g = build_knowledge_capture_graph()
        assert g.initial_state == "EXTRACTING"
        assert g.current_state == "EXTRACTING"

    def test_happy_path_transitions(self):
        g = build_knowledge_capture_graph()
        # EXTRACTING → CRITIQUING → DRAFT → IN_REVIEW → APPROVED
        assert g.fire("extract_complete") == "CRITIQUING"
        assert g.fire("critic_approve") == "DRAFT"
        assert g.fire("submit_for_review") == "IN_REVIEW"
        assert g.fire("approve") == "APPROVED"
        assert g.is_terminal()

    def test_revision_loop(self):
        g = build_knowledge_capture_graph()
        assert g.fire("extract_complete") == "CRITIQUING"
        assert g.fire("critic_revise") == "EXTRACTING"
        assert g.fire("extract_complete") == "CRITIQUING"
        assert g.fire("critic_approve") == "DRAFT"

    def test_extraction_refused(self):
        g = build_knowledge_capture_graph()
        assert g.fire("extraction_refused") == "DECLINED"
        assert g.is_terminal()

    def test_illegal_transition_from_approved(self):
        g = build_knowledge_capture_graph()
        g.current_state = "APPROVED"
        with pytest.raises(IllegalTransitionError):
            g.fire("submit_for_review")

    def test_reject_from_draft(self):
        g = build_knowledge_capture_graph()
        g.current_state = "DRAFT"
        assert g.fire("reject") == "REJECTED"
        assert g.is_terminal()

    def test_reject_from_in_review(self):
        g = build_knowledge_capture_graph()
        g.current_state = "IN_REVIEW"
        assert g.fire("reject") == "REJECTED"


class TestMermaidGeneration:
    def test_to_mermaid_contains_required_elements(self):
        g = build_knowledge_capture_graph()
        mermaid = g.to_mermaid()

        assert "stateDiagram-v2" in mermaid
        assert "EXTRACTING" in mermaid
        assert "CRITIQUING" in mermaid
        assert "IN_REVIEW" in mermaid
        assert "APPROVED" in mermaid
        assert "[*]" in mermaid
        assert "HITL gate" in mermaid
        assert "terminal" in mermaid
        assert "-->" in mermaid

    def test_generate_file(self, tmp_path):
        output = str(tmp_path / "test.mmd")
        content = generate_mermaid_file(output)
        assert "stateDiagram-v2" in content
        with open(output, encoding="utf-8") as f:
            assert f.read().startswith("stateDiagram-v2")
