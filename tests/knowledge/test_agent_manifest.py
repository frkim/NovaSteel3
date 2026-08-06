"""Tests for the declarative agent manifest.

The manifest is the artifact that replaces "agents get created lazily whenever the
service happens to run". What matters here is not that it parses, but that the two
invariants it exists to hold cannot be broken by an edit: agents that read untrusted
content hold no calculation tools, and every tool an agent names actually exists.

Since ADR-020 collapsed the roster into a single Foundry project, the first invariant
is asserted against the agent *definitions* by name rather than against a project
grouping — that grouping no longer separates anything, and a test that reads it back
from the same predicate it is meant to check would assert nothing.
"""

from __future__ import annotations

import pytest

from knowledge_orchestrator import agent_manifest
from knowledge_orchestrator.agent_manifest import (
    CARBON_ADVISOR_AGENT_NAME,
    ENERGY_ADVISOR_AGENT_NAME,
    MAINTENANCE_ADVISOR_AGENT_NAME,
    MANIFEST,
    ORCHESTRATOR_AGENT_NAME,
    PROCEDURE_AGENT_NAME,
    PROJECT_ENDPOINT_ENV,
    PROJECT_NOVASTEEL,
    QUALITY_ADVISOR_AGENT_NAME,
    TOOL_KNOWLEDGE_MCP,
    TOOL_WEB_SEARCH,
    WEB_SEARCH_AGENT_NAME,
    agent_spec,
    agents_for_project,
    knowledge_agents,
    operations_agents,
    orchestrator_for_project,
    projects,
    specialists_for_project,
)
from knowledge_orchestrator.agent_tools import TOOL_CATALOGUE

BUILTIN_TOOLS = {TOOL_KNOWLEDGE_MCP, TOOL_WEB_SEARCH}

# The agents that read untrusted or semi-trusted content. Named explicitly, because
# the point of the test below is that *these* agents never gain a calculation tool.
READERS_OF_UNTRUSTED_CONTENT = (PROCEDURE_AGENT_NAME, WEB_SEARCH_AGENT_NAME)


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


def test_agents_that_read_untrusted_content_hold_no_calculation_tools():
    """The containment, asserted where it now lives: on the definition.

    The procedure and web-search agents read untrusted content — approved procedures,
    interview transcripts, web results. One project now hosts every agent, so nothing
    structural stops a reviewer adding `simulate_energy_dispatch` to the procedure
    agent; this test is what stops it. If it ever passes with a function tool on one
    of these two, a prompt injected into a retrieved procedure has a path to a
    NovaSteel calculation.
    """
    for name in READERS_OF_UNTRUSTED_CONTENT:
        spec = agent_spec(name)
        assert set(spec.tools) <= BUILTIN_TOOLS, (
            f"{spec.name} reads untrusted content but holds function tools "
            f"{sorted(set(spec.tools) - BUILTIN_TOOLS)}"
        )


def test_operations_agents_hold_only_function_tools():
    """The mirror of the rule above: no tool-calling agent also retrieves.

    An agent that both retrieves untrusted text and calls a calculation is the
    single-agent version of the boundary ADR-019 drew between projects, and is the
    one shape ADR-020 must not produce.
    """
    ops = operations_agents()
    assert ops, "the roster must hold at least one tool-calling agent"
    for spec in ops:
        assert set(spec.tools) <= set(TOOL_CATALOGUE), (
            f"{spec.name} holds both a retrieval tool and a calculation tool"
        )


def test_the_two_groups_partition_the_roster():
    """Every agent is either a reader or a caller, and none is both."""
    readers = set(knowledge_agents())
    callers = set(operations_agents())
    assert not readers & callers
    assert readers | callers == set(MANIFEST)
    assert {spec.name for spec in readers} == set(READERS_OF_UNTRUSTED_CONTENT)


def test_one_project_hosts_the_whole_roster():
    """ADR-020: the roster is no longer split across projects."""
    assert projects() == (PROJECT_NOVASTEEL,)
    assert agents_for_project(PROJECT_NOVASTEEL) == MANIFEST
    assert PROJECT_ENDPOINT_ENV[PROJECT_NOVASTEEL] == "FOUNDRY_PROJECT_ENDPOINT"


def test_agent_spec_looks_up_by_name():
    for name in (
        PROCEDURE_AGENT_NAME,
        WEB_SEARCH_AGENT_NAME,
        ENERGY_ADVISOR_AGENT_NAME,
        MAINTENANCE_ADVISOR_AGENT_NAME,
        CARBON_ADVISOR_AGENT_NAME,
        QUALITY_ADVISOR_AGENT_NAME,
        ORCHESTRATOR_AGENT_NAME,
    ):
        assert agent_spec(name).name == name
        assert agent_spec(name).project == PROJECT_NOVASTEEL


# --- the specialist / orchestrator split ------------------------------------


def test_every_specialist_owns_exactly_one_calculation():
    """One agent, one concern, one tool. What a specialist can do has to be legible
    from its definition; an agent that accumulates tools stops being reviewable."""
    for spec in specialists_for_project(PROJECT_NOVASTEEL):
        assert len(spec.tools) == 1, f"{spec.name} holds {len(spec.tools)} tools"


def test_every_specialist_declares_a_distinct_domain():
    """Two specialists sharing a domain would make routing between them arbitrary."""
    domains = [spec.domain for spec in specialists_for_project(PROJECT_NOVASTEEL)]
    assert all(domains)
    assert len(domains) == len(set(domains))


def test_every_specialist_declares_routing_keywords():
    """A specialist with no keywords can never be selected, so it would silently
    become an agent nobody can reach."""
    for spec in specialists_for_project(PROJECT_NOVASTEEL):
        assert spec.routing_keywords, f"{spec.name} is unroutable"


def test_no_keyword_is_claimed_by_two_domains():
    """A shared keyword makes every question containing it multi-domain, which
    quietly routes a growing share of traffic to the orchestrator."""
    seen: dict[str, str] = {}
    for spec in specialists_for_project(PROJECT_NOVASTEEL):
        for keyword in spec.routing_keywords:
            assert keyword not in seen, (
                f"{keyword!r} is claimed by both {seen.get(keyword)} and {spec.name}"
            )
            seen[keyword] = spec.name


def test_there_is_exactly_one_orchestrator():
    orchestrators = [spec for spec in MANIFEST if spec.is_orchestrator]
    assert len(orchestrators) == 1
    assert orchestrators[0].name == ORCHESTRATOR_AGENT_NAME
    assert orchestrator_for_project(PROJECT_NOVASTEEL) is orchestrators[0]


def test_the_orchestrator_holds_every_specialist_tool():
    """It exists to answer questions that span the specialists, so a tool it lacks
    is a cross-domain question it silently answers incompletely."""
    orchestrator = orchestrator_for_project(PROJECT_NOVASTEEL)
    specialist_tools = {
        tool
        for spec in specialists_for_project(PROJECT_NOVASTEEL)
        for tool in spec.tools
    }
    assert set(orchestrator.tools) == specialist_tools


def test_the_orchestrator_is_not_itself_a_routing_target():
    """It is the fallback, not a fifth domain. Keywords would make it compete with
    the specialists it is meant to back."""
    orchestrator = orchestrator_for_project(PROJECT_NOVASTEEL)
    assert orchestrator.routing_keywords == ()
    assert orchestrator.domain == ""
    assert orchestrator not in specialists_for_project(PROJECT_NOVASTEEL)


def test_no_agent_that_reads_untrusted_content_is_an_orchestrator():
    """An orchestrator holds every function tool. Making one of the readers an
    orchestrator would hand the full calculation surface to an agent that ingests
    untrusted text — the exact escalation the project split used to prevent."""
    for name in READERS_OF_UNTRUSTED_CONTENT:
        assert not agent_spec(name).is_orchestrator
    assert orchestrator_for_project(PROJECT_NOVASTEEL) in operations_agents()


def test_every_catalogued_tool_is_reachable_from_some_agent():
    """A tool nobody declares is a schema with no agent behind it — dead review
    surface that reads as capability."""
    declared = {tool for spec in MANIFEST for tool in spec.tools}
    assert set(TOOL_CATALOGUE) <= declared


def test_the_orchestrator_is_told_not_to_resolve_a_trade_off():
    """The whole point of surfacing a tension rather than settling it: weighting
    cost against carbon against asset life is a planner's decision, not a model's."""
    instructions = agent_spec(ORCHESTRATOR_AGENT_NAME).instructions.lower()
    assert "trade-off" in instructions
    assert "do not resolve it" in instructions


def test_the_orchestrator_may_not_combine_two_results_arithmetically():
    """ADR-006 survives the fan-out or it does not survive at all: an orchestrator
    that adds two tool outputs together has become the calculation."""
    instructions = " ".join(
        agent_spec(ORCHESTRATOR_AGENT_NAME).instructions.lower().split()
    )
    assert "never combine two tool results arithmetically" in instructions


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
    for spec in operations_agents():
        lowered = spec.instructions.lower()
        assert "never" in lowered
        assert any(word in lowered for word in ("compute", "estimate"))
        for tool in spec.tools:
            assert tool in spec.instructions, (
                f"{spec.name} does not tell the model to call {tool}"
            )


def test_proposal_language_is_present_in_operations_instructions():
    """ADR-007: an agent may propose, never decide."""
    for spec in operations_agents():
        assert "PROPOSAL" in spec.instructions


def test_manifest_module_exposes_a_stable_surface():
    for name in ("MANIFEST", "agents_for_project", "agent_spec", "projects"):
        assert hasattr(agent_manifest, name)
