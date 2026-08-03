"""Deciding which operations agent answers a question.

An operator asks "what would the cheap overnight schedule cost us in CO2" without
knowing that four agents exist, let alone which one holds the emissions tool. Something
has to choose. The obvious choice — give a supervisor model the roster and let it
decide — is the one deliberately not made here.

**Why the routing is deterministic.** A model-driven supervisor makes the choice of
calculation itself an inference, which is the one thing this estate keeps out of the
model everywhere else (ADR-006). It is also unreviewable: nothing diffs, nothing can be
asserted, and a routing regression looks identical to a good day. And it is a
prompt-injection surface — text carried into the turn could steer the choice of agent,
which is a choice about which tools become reachable. Keyword scoring over declared
domains is less clever and strictly better on all three counts: it is a pure function of
the question, it fails visibly, and :func:`route` is unit-testable without a network.

**What it does not decide.** Routing selects an agent; it grants nothing. Every tool
still re-applies the caller's role and plant scope in the BFF, so a question routed to
the carbon advisor by an operator who may not read that plant is refused by the tool
exactly as the REST route would refuse it. Routing being wrong costs a worse answer, not
a wider one.

**The orchestrator is the fallback, not a fifth domain.** Zero specialists matched means
nobody owns the question; several matched means it spans them. Both are the
orchestrator's job, and both are reported with the reason, so "why did this go to the
orchestrator" is answerable from the response rather than from the logs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence

from .agent_manifest import (
    PROJECT_OPERATIONS,
    AgentSpec,
    orchestrator_for_project,
    specialists_for_project,
)

# Why the routing decision exists as a value: the BFF returns it to the caller, so an
# operator can see that a cross-domain question went to the orchestrator rather than
# wondering why the answer covers more ground than they asked about.

REASON_SINGLE_DOMAIN = "single-domain"
REASON_MULTI_DOMAIN = "multi-domain"
REASON_NO_MATCH = "no-domain-match"
REASON_EXPLICIT = "explicit"


@dataclass(frozen=True, slots=True)
class DomainMatch:
    """One specialist's score against a question, and the words that produced it."""

    agent: str
    domain: str
    keywords: tuple[str, ...]

    @property
    def score(self) -> int:
        return len(self.keywords)


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    """Which agent should answer, and the evidence for choosing it."""

    agent: str
    reason: str
    matches: tuple[DomainMatch, ...] = ()

    @property
    def domains(self) -> tuple[str, ...]:
        """The domains the question touched, strongest first."""
        return tuple(match.domain for match in self.matches)

    def as_dict(self) -> dict[str, object]:
        """The wire shape returned alongside an answer."""
        return {
            "agent": self.agent,
            "reason": self.reason,
            "domains": list(self.domains),
            "matchedKeywords": {
                match.domain: list(match.keywords) for match in self.matches
            },
        }


def route(
    question: str,
    *,
    project: str = PROJECT_OPERATIONS,
    specialists: Optional[Sequence[AgentSpec]] = None,
    orchestrator: Optional[AgentSpec] = None,
) -> RoutingDecision:
    """Choose the agent for one question.

    Exactly one specialist matching means that specialist owns the question. Zero or
    several means the orchestrator does — in the first case because nobody owns it and
    the orchestrator holds every tool, in the second because the question spans domains
    and splitting it across agents would leave the operator to combine the answers.

    Falls back to the strongest specialist when no orchestrator is deployed, so a
    partially reconciled estate still answers rather than failing.

    ``specialists`` and ``orchestrator`` default to the manifest's roster for
    ``project``. Passing ``specialists`` means the caller is supplying the *whole*
    roster, so ``orchestrator`` is then taken literally — including ``None``, which
    is how a manifest without an orchestrator is expressed.
    """
    explicit_roster = specialists is not None
    candidates = (
        tuple(specialists)
        if specialists is not None
        else specialists_for_project(project)
    )
    if orchestrator is not None:
        supervisor: Optional[AgentSpec] = orchestrator
    elif explicit_roster:
        supervisor = None
    else:
        supervisor = orchestrator_for_project(project)

    matches = _score(question, candidates)

    if len(matches) == 1:
        return RoutingDecision(matches[0].agent, REASON_SINGLE_DOMAIN, matches)

    reason = REASON_MULTI_DOMAIN if matches else REASON_NO_MATCH
    if supervisor is not None:
        return RoutingDecision(supervisor.name, reason, matches)
    if matches:
        # No orchestrator deployed: the strongest domain is the least-bad answer, and
        # saying which domains were dropped is more useful than a silent narrowing.
        return RoutingDecision(matches[0].agent, reason, matches)
    if candidates:
        return RoutingDecision(candidates[0].name, reason, matches)
    raise LookupError(f"No operations agents are declared for project {project!r}.")


def _score(question: str, specialists: Sequence[AgentSpec]) -> tuple[DomainMatch, ...]:
    """Match each specialist's keywords against the question, strongest first.

    Ties are broken by manifest order rather than arbitrarily, so the same question
    always routes the same way — a router whose output depends on set iteration order
    is a router whose tests pass until they do not.
    """
    text = question.casefold()
    matches: list[DomainMatch] = []
    for spec in specialists:
        hits = tuple(
            keyword for keyword in spec.routing_keywords if _contains(text, keyword)
        )
        if hits:
            matches.append(DomainMatch(spec.name, spec.domain, hits))
    matches.sort(key=lambda match: (-match.score, _order(specialists, match.agent)))
    return tuple(matches)


def _order(specialists: Sequence[AgentSpec], name: str) -> int:
    for index, spec in enumerate(specialists):
        if spec.name == name:
            return index
    return len(specialists)


def _contains(text: str, keyword: str) -> bool:
    """Word-boundary match, so 'scope 2' hits and 'cost' does not fire on 'costume'.

    Substring matching would route half the questions to every agent: 'ets' appears
    inside 'targets', 'load' inside 'download'. The keyword is escaped because several
    contain characters that are regex-significant.
    """
    return re.search(rf"(?<!\w){re.escape(keyword.casefold())}(?!\w)", text) is not None


__all__ = [
    "REASON_EXPLICIT",
    "REASON_MULTI_DOMAIN",
    "REASON_NO_MATCH",
    "REASON_SINGLE_DOMAIN",
    "DomainMatch",
    "RoutingDecision",
    "route",
]
