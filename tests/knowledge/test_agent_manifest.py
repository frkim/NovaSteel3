"""Tests for the declarative agent manifest.

The manifest is the artifact that replaces "agents get created lazily whenever the
service happens to run". What matters here is not that it parses, but that the two
invariants it exists to hold cannot be broken by an edit: agents that read untrusted
content hold no calculation tools, and every tool an agent names actually exists.
"""

from __future__ import annotations

import pytest

from knowledge_orchestrator import agent_manifest
from knowledge_orchestrator.agent_manifest import (
    ENERGY_ADVISOR_AGENT_NAME,
    MAINTENANCE_ADVISOR_AGENT_NAME,
    MANIFEST,
    PROCEDURE_AGENT_NAME,
    PROJECT_ENDPOINT_ENV,
    PROJECT_KNOWLEDGE,
    PROJECT_OPERATIONS,
    TOOL_KNOWLEDGE_MCP,
    TOOL_WEB_SEARCH,
    WEB_SEARCH_AGENT_NAME,
    agent_spec,
    agents_for_project,
    projects,
)
from knowledge_orchestrator.agent_tools import TOOL_CATALOGUE

BUILTIN_TOOLS = {TOOL_KNOWLEDGE_MCP, TOOL_WEB_SEARCH}


def test_every_agent_name_is_unique():
    names = [spec.name for spec in MANIFEST]
    assert len(names) == len(set(names))


def test_every_named_tool_exists():
    """A typo in a tool name would otherwise surface as an agent that silently
    cannot do its job, which is exactly the failure mode a manifest is meant to
    remove."""
    for spec in MANIFEST:
        for tool in spec.tools:
            assert (
                tool in BUILTIN_TOOLS or tool in TOOL_CATALOGUE
            ), f"{spec.name} names unknown tool {tool!r}"


def test_knowledge_agents_hold_no_calculation_tools():
    """The trust boundary, asserted.

    Agents in the knowledge project read untrusted content: approved procedures,
    interview transcripts, web results. If one of them ever gained a function tool,
    a prompt injected into a retrieved procedure would have a path to a NovaSteel
    calculation. That must fail the build, not a review.
    """
    for spec in agents_for_project(PROJECT_KNOWLEDGE):
        assert set(spec.tools) <= BUILTIN_TOOLS, (
            f"{spec.name} is in the knowledge project but holds function tools "
            f"{sorted(set(spec.tools) - BUILTIN_TOOLS)}"
        )


def test_operations_agents_hold_only_function_tools():
    """The mirror of the rule above: nothing in the operations project retrieves."""
    ops = agents_for_project(PROJECT_OPERATIONS)
    assert ops, "the operations project must host at least one agent"
    for spec in ops:
        assert set(spec.tools) <= set(TOOL_CATALOGUE), (
            f"{spec.name} holds a builtin retrieval tool; retrieval belongs in the "
            "knowledge project"
        )


def test_each_project_has_its_own_endpoint_variable():
    """Two projects mean two endpoints. Sharing one would collapse the boundary."""
    assert projects() == (PROJECT_KNOWLEDGE, PROJECT_OPERATIONS)
    values = [PROJECT_ENDPOINT_ENV[name] for name in projects()]
    assert len(set(values)) == len(values)


def test_agent_spec_looks_up_by_name():
    assert agent_spec(PROCEDURE_AGENT_NAME).project == PROJECT_KNOWLEDGE
    assert agent_spec(WEB_SEARCH_AGENT_NAME).project == PROJECT_KNOWLEDGE
    assert agent_spec(ENERGY_ADVISOR_AGENT_NAME).project == PROJECT_OPERATIONS
    assert agent_spec(MAINTENANCE_ADVISOR_AGENT_NAME).project == PROJECT_OPERATIONS


def test_agent_spec_error_names_the_known_agents():
    with pytest.raises(KeyError) as excinfo:
        agent_spec("novasteel-does-not-exist")
    assert PROCEDURE_AGENT_NAME in str(excinfo.value)


def test_tool_calling_instructions_forbid_self_computation():
    """Every operations agent must be told the calculation is not its job.

    ADR-006 keeps the MILP and the physics model authoritative. The instruction
    block is the only thing standing between that decision and a model that happily
    estimates a saving in prose, so it is asserted rather than trusted.
    """
    for spec in agents_for_project(PROJECT_OPERATIONS):
        lowered = spec.instructions.lower()
        assert "never" in lowered
        assert any(word in lowered for word in ("compute", "estimate"))
        for tool in spec.tools:
            assert tool in spec.instructions, (
                f"{spec.name} does not tell the model to call {tool}"
            )


def test_proposal_language_is_present_in_operations_instructions():
    """ADR-007: an agent may propose, never decide."""
    for spec in agents_for_project(PROJECT_OPERATIONS):
        assert "PROPOSAL" in spec.instructions


def test_manifest_module_exposes_a_stable_surface():
    for name in ("MANIFEST", "agents_for_project", "agent_spec", "projects"):
        assert hasattr(agent_manifest, name)
