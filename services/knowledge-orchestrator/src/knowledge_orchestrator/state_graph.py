"""Introspectable state graph for the knowledge-capture workflow (M6).

Promotes the DRAFT → IN_REVIEW → APPROVED workflow into an explicit, introspectable
``StateGraph`` class. Hand-rolled (no LangGraph dependency) — lightweight and fully
testable offline.

The graph is introspectable: ``to_mermaid()`` generates a Mermaid state diagram that
can be embedded in the deck / documentation. Human-in-the-loop approval gates are
terminal/gated nodes — HITL *inside* a state graph is the "autonomy with control"
story the EU AI Act narrative requires.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass(frozen=True)
class Transition:
    """A single allowed state transition with optional guard and actor."""

    source: str
    target: str
    trigger: str
    guard: Optional[str] = None  # Human-readable guard condition
    actor: str = "system"  # "agent", "human", or "system"


class IllegalTransitionError(Exception):
    """Raised when a transition is attempted that is not in the graph."""

    def __init__(self, current: str, target: str, trigger: str):
        self.current = current
        self.target = target
        self.trigger = trigger
        super().__init__(
            f"Illegal transition: {current} --[{trigger}]--> {target}"
        )


@dataclass
class StateGraph:
    """An explicit, introspectable state graph for workflow orchestration.

    Nodes represent workflow states. Edges (transitions) are the allowed moves,
    each with a trigger name, optional guard condition, and actor classification.
    Terminal nodes have no outgoing transitions and represent workflow completion.
    Gated nodes require human approval before the transition fires.
    """

    name: str
    nodes: dict[str, dict] = field(default_factory=dict)
    transitions: list[Transition] = field(default_factory=list)
    initial_state: str = ""
    _current_state: str = ""

    def add_node(
        self,
        name: str,
        *,
        terminal: bool = False,
        gated: bool = False,
        description: str = "",
        actor: str = "system",
    ) -> "StateGraph":
        """Add a state node to the graph."""
        self.nodes[name] = {
            "terminal": terminal,
            "gated": gated,
            "description": description,
            "actor": actor,
        }
        if not self.initial_state:
            self.initial_state = name
            self._current_state = name
        return self

    def add_transition(
        self,
        source: str,
        target: str,
        trigger: str,
        *,
        guard: Optional[str] = None,
        actor: str = "system",
    ) -> "StateGraph":
        """Add an allowed transition between two nodes."""
        if source not in self.nodes:
            raise ValueError(f"source node '{source}' not in graph")
        if target not in self.nodes:
            raise ValueError(f"target node '{target}' not in graph")
        self.transitions.append(
            Transition(source=source, target=target, trigger=trigger, guard=guard, actor=actor)
        )
        return self

    @property
    def current_state(self) -> str:
        return self._current_state

    @current_state.setter
    def current_state(self, value: str) -> None:
        if value not in self.nodes:
            raise ValueError(f"state '{value}' not in graph")
        self._current_state = value

    def is_terminal(self, state: Optional[str] = None) -> bool:
        """Check if the given state (or current) is terminal."""
        s = state or self._current_state
        return self.nodes.get(s, {}).get("terminal", False)

    def is_gated(self, state: Optional[str] = None) -> bool:
        """Check if the given state (or current) requires human approval."""
        s = state or self._current_state
        return self.nodes.get(s, {}).get("gated", False)

    def allowed_transitions(self, state: Optional[str] = None) -> list[Transition]:
        """Return transitions available from the given state (or current)."""
        s = state or self._current_state
        return [t for t in self.transitions if t.source == s]

    def can_transition(self, trigger: str, state: Optional[str] = None) -> bool:
        """Check if a specific trigger is legal from the given state."""
        s = state or self._current_state
        return any(t.trigger == trigger for t in self.allowed_transitions(s))

    def fire(self, trigger: str) -> str:
        """Execute a transition by trigger name. Raises if illegal."""
        matching = [
            t for t in self.transitions
            if t.source == self._current_state and t.trigger == trigger
        ]
        if not matching:
            raise IllegalTransitionError(self._current_state, "?", trigger)
        transition = matching[0]
        self._current_state = transition.target
        return self._current_state

    def terminal_nodes(self) -> list[str]:
        """Return all terminal node names."""
        return [n for n, props in self.nodes.items() if props.get("terminal")]

    def gated_nodes(self) -> list[str]:
        """Return all human-gated node names."""
        return [n for n, props in self.nodes.items() if props.get("gated")]

    def to_mermaid(self) -> str:
        """Generate a Mermaid state diagram from the graph definition."""
        lines = ["stateDiagram-v2"]

        # Node descriptions.
        for name, props in self.nodes.items():
            desc = props.get("description", name)
            safe_name = name.replace(" ", "_").replace("-", "_")
            if props.get("terminal"):
                lines.append(f"    {safe_name} : {name} (terminal)")
            elif props.get("gated"):
                lines.append(f"    {safe_name} : {name} [HITL gate]")
            else:
                lines.append(f"    {safe_name} : {name}")

        lines.append("")

        # Initial state.
        if self.initial_state:
            safe_initial = self.initial_state.replace(" ", "_").replace("-", "_")
            lines.append(f"    [*] --> {safe_initial}")

        # Transitions.
        for t in self.transitions:
            src = t.source.replace(" ", "_").replace("-", "_")
            tgt = t.target.replace(" ", "_").replace("-", "_")
            label = t.trigger
            if t.guard:
                label += f" [{t.guard}]"
            if t.actor == "human":
                label += " 👤"
            lines.append(f"    {src} --> {tgt} : {label}")

        # Terminal states.
        for name in self.terminal_nodes():
            safe_name = name.replace(" ", "_").replace("-", "_")
            lines.append(f"    {safe_name} --> [*]")

        return "\n".join(lines)


# --- Pre-built knowledge-capture workflow graph ------------------------------


def build_knowledge_capture_graph() -> StateGraph:
    """Build the DRAFT→IN_REVIEW→APPROVED knowledge-capture state graph.

    Includes the reflection/critic loop as internal sub-states and the
    human-in-the-loop approval gates as gated terminal nodes.
    """
    g = StateGraph(name="knowledge-capture-workflow")

    # States.
    g.add_node("EXTRACTING", description="Agent extracting draft from transcript", actor="agent")
    g.add_node("CRITIQUING", description="Critic agent reviewing draft quality", actor="agent")
    g.add_node("DRAFT", description="Draft ready for human submission to review", actor="agent")
    g.add_node("IN_REVIEW", gated=True, description="Awaiting human publisher approval", actor="human")
    g.add_node("APPROVED", terminal=True, description="Immutable approved procedure", actor="human")
    g.add_node("REJECTED", terminal=True, description="Procedure rejected by publisher", actor="human")
    g.add_node("DECLINED", terminal=True, description="Agent declined — insufficient grounding", actor="agent")

    # Transitions.
    g.add_transition("EXTRACTING", "CRITIQUING", "extract_complete", actor="agent")
    g.add_transition("CRITIQUING", "DRAFT", "critic_approve", actor="agent")
    g.add_transition("CRITIQUING", "EXTRACTING", "critic_revise", guard="iterations < 2", actor="agent")
    g.add_transition("CRITIQUING", "DECLINED", "critic_reject", guard="max iterations reached", actor="agent")
    g.add_transition("EXTRACTING", "DECLINED", "extraction_refused", actor="agent")
    g.add_transition("DRAFT", "IN_REVIEW", "submit_for_review", actor="human")
    g.add_transition("IN_REVIEW", "APPROVED", "approve", guard="Knowledge.Publisher role", actor="human")
    g.add_transition("IN_REVIEW", "REJECTED", "reject", guard="Knowledge.Publisher role", actor="human")
    g.add_transition("DRAFT", "REJECTED", "reject", guard="Knowledge.Publisher role", actor="human")

    return g


def generate_mermaid_file(output_path: str) -> str:
    """Generate the Mermaid diagram and write it to a file. Returns the content."""
    graph = build_knowledge_capture_graph()
    content = graph.to_mermaid()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content + "\n")
    return content
