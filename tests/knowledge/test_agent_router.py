"""Tests for the deterministic operations router.

The router is the thing that decides which calculation an operator's question can
reach. That makes it worth asserting rather than trusting, and it is only assertable
at all because the routing is a pure function of the question rather than an
inference — which is the argument for building it this way in the first place.

Two properties matter more than the individual routes: a question that clearly
belongs to one specialist must not fan out to the orchestrator (that would make every
answer a survey), and a question that spans specialists must not be silently narrowed
to one (that would drop half the answer without saying so).
"""

from __future__ import annotations

import pytest

from knowledge_orchestrator.agent_manifest import (
    CARBON_ADVISOR_AGENT_NAME,
    DOMAIN_CARBON,
    DOMAIN_ENERGY,
    DOMAIN_MAINTENANCE,
    DOMAIN_QUALITY,
    ENERGY_ADVISOR_AGENT_NAME,
    MAINTENANCE_ADVISOR_AGENT_NAME,
    ORCHESTRATOR_AGENT_NAME,
    PROJECT_NOVASTEEL,
    QUALITY_ADVISOR_AGENT_NAME,
    AgentSpec,
    knowledge_agents,
    specialists_for_project,
)
from knowledge_orchestrator.agent_router import (
    REASON_MULTI_DOMAIN,
    REASON_NO_MATCH,
    REASON_SINGLE_DOMAIN,
    route,
)


# --- single-domain routing ---------------------------------------------------


@pytest.mark.parametrize(
    ("question", "expected", "domain"),
    [
        (
            "What would shifting tonight's heat schedule cost us?",
            ENERGY_ADVISOR_AGENT_NAME,
            DOMAIN_ENERGY,
        ),
        (
            "How much CO2e did we emit last month and what is the ETS exposure?",
            CARBON_ADVISOR_AGENT_NAME,
            DOMAIN_CARBON,
        ),
        (
            "Why is the first-pass yield falling on this coil?",
            QUALITY_ADVISOR_AGENT_NAME,
            DOMAIN_QUALITY,
        ),
        (
            "When does the refractory lining need relining?",
            MAINTENANCE_ADVISOR_AGENT_NAME,
            DOMAIN_MAINTENANCE,
        ),
    ],
)
def test_a_single_domain_question_reaches_its_specialist(question, expected, domain):
    decision = route(question)
    assert decision.agent == expected
    assert decision.reason == REASON_SINGLE_DOMAIN
    assert decision.domains == (domain,)


def test_routing_is_case_insensitive():
    assert route("SCOPE 2 EMISSIONS").agent == CARBON_ADVISOR_AGENT_NAME


def test_the_matched_keywords_are_reported_as_the_evidence():
    """"Why did this go there" has to be answerable from the response, not the
    logs."""
    decision = route("What is our carbon footprint?")
    assert decision.matches[0].domain == DOMAIN_CARBON
    assert set(decision.matches[0].keywords) == {"carbon", "footprint"}


# --- the orchestrator --------------------------------------------------------


def test_a_cross_domain_question_reaches_the_orchestrator():
    """Splitting this across two agents would leave the operator to combine the
    answers, which is the unsourced arithmetic ADR-006 exists to prevent."""
    decision = route(
        "If we shift the schedule to the cheap overnight tariff, "
        "what does that do to our CO2 emissions?"
    )
    assert decision.agent == ORCHESTRATOR_AGENT_NAME
    assert decision.reason == REASON_MULTI_DOMAIN
    assert set(decision.domains) == {DOMAIN_ENERGY, DOMAIN_CARBON}


def test_a_question_spanning_three_domains_still_reaches_the_orchestrator():
    decision = route(
        "Does the cheaper dispatch schedule hurt first-pass yield or shorten "
        "lining life?"
    )
    assert decision.agent == ORCHESTRATOR_AGENT_NAME
    assert set(decision.domains) == {DOMAIN_ENERGY, DOMAIN_QUALITY, DOMAIN_MAINTENANCE}


def test_an_unmatched_question_reaches_the_orchestrator_not_an_arbitrary_specialist():
    """Nobody owns it, and the orchestrator is the only agent holding every tool, so
    it is the one with a chance of answering."""
    decision = route("Good morning, can you help me?")
    assert decision.agent == ORCHESTRATOR_AGENT_NAME
    assert decision.reason == REASON_NO_MATCH
    assert decision.domains == ()


def test_domains_are_ordered_by_strength():
    """The strongest signal first, so a UI reporting one domain reports the right
    one."""
    decision = route(
        "Compare the energy cost, the dispatch schedule and the tariff peak "
        "against our CO2."
    )
    assert decision.domains[0] == DOMAIN_ENERGY


# --- what routing is not -----------------------------------------------------


def test_routing_never_selects_an_agent_that_reads_untrusted_content():
    """The knowledge agents read untrusted content. Reaching one from the tool-calling
    endpoint would be the containment collapsing, so they are not candidates.

    Since ADR-020 they share a Foundry project with the advisors, which makes this the
    assertion that keeps them unreachable: routing selects on `domain`, and a knowledge
    agent declares none.
    """
    knowledge_names = {spec.name for spec in knowledge_agents()}
    assert knowledge_names
    for question in (
        "How do I tap the furnace safely?",
        "What does the procedure say about slag?",
        "Search the web for refractory guidance.",
    ):
        assert route(question).agent not in knowledge_names


def test_every_specialist_is_reachable_by_at_least_one_of_its_own_keywords():
    """A keyword that cannot select its own agent is either dead or claimed
    elsewhere; either way the specialist is quietly less reachable than it reads."""
    for spec in specialists_for_project(PROJECT_NOVASTEEL):
        reachable = [
            keyword
            for keyword in spec.routing_keywords
            if route(f"Tell me about {keyword}.").agent == spec.name
        ]
        assert reachable, f"no keyword of {spec.name} selects it"


def test_keywords_match_on_word_boundaries():
    """Substring matching would route half the questions everywhere: 'ets' lives
    inside 'targets', 'load' inside 'download'."""
    decision = route("What are the production targets we downloaded?")
    assert decision.reason == REASON_NO_MATCH


def test_routing_is_stable_for_the_same_question():
    """A router whose output depends on iteration order passes its tests until it
    does not."""
    question = "What does the cheaper schedule do to emissions?"
    assert {route(question).agent for _ in range(20)} == {
        route(question).agent
    }


# --- degraded estates --------------------------------------------------------


def _spec(name: str, domain: str, keywords: tuple[str, ...]) -> AgentSpec:
    return AgentSpec(
        name=name,
        project=PROJECT_NOVASTEEL,
        description="test",
        instructions="test",
        tools=(),
        domain=domain,
        routing_keywords=keywords,
    )


def test_without_an_orchestrator_the_strongest_domain_still_answers():
    """A partially reconciled estate should degrade to a narrower answer rather than
    to no answer."""
    specialists = (
        _spec("a", "alpha", ("alpha", "aa")),
        _spec("b", "beta", ("beta",)),
    )
    decision = route(
        "alpha aa beta", specialists=specialists, orchestrator=None
    )
    assert decision.agent == "a"
    assert decision.reason == REASON_MULTI_DOMAIN
    # The dropped domain is still reported, so the narrowing is visible.
    assert set(decision.domains) == {"alpha", "beta"}


def test_an_empty_roster_fails_loudly():
    with pytest.raises(LookupError):
        route("anything", specialists=(), orchestrator=None)
