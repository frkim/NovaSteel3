"""Applying the agent manifest to Foundry Agent Service.

Agents have no ARM resource type, so ``azd up`` cannot create them and a Bicep
what-if cannot show them. The gap that leaves is not theoretical: both deployed
NovaSteel projects contained zero agents, because the only code that created one ran
lazily inside a service that had never been deployed. Infrastructure said the
platform was ready; the platform was empty.

This module closes that gap the same way the rest of the estate is managed —
declaratively, from a reviewable artifact, applied by an explicit step. Run it at
release time, after the Bicep deployment and before smoke tests:

.. code-block:: console

   python -m knowledge_orchestrator.agent_reconciler          # apply
   python -m knowledge_orchestrator.agent_reconciler --dry-run # report only

It is idempotent. ``create_version`` is create-or-new-version by agent name, so
re-running produces a new version of an unchanged agent rather than a duplicate, and
the manifest stays the single source of truth for what an agent *is*.

Reconciliation is per project and each project is independent: the operations project
being undeployed must not stop the knowledge agents from being applied, so a project
that is not configured is reported as skipped rather than failing the run.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Optional, Sequence

from .agent_manifest import MANIFEST, AgentSpec, agents_for_project, projects
from .agent_service import (
    DEFAULT_MODEL,
    ENV_CHAT_DEPLOYMENT,
    FoundryAgentService,
    HostedAgent,
    agent_service_status,
)
from .foundry_iq import knowledge_base_config_from_env

logger = logging.getLogger(__name__)

OUTCOME_APPLIED = "applied"
OUTCOME_PLANNED = "planned"
OUTCOME_SKIPPED = "skipped"
OUTCOME_FAILED = "failed"


@dataclass
class AgentOutcome:
    """What happened to one agent in one reconcile run."""

    name: str
    project: str
    outcome: str
    detail: str = ""
    agent_id: str = ""
    version: str = ""

    @property
    def ok(self) -> bool:
        return self.outcome in (OUTCOME_APPLIED, OUTCOME_PLANNED, OUTCOME_SKIPPED)


@dataclass
class ReconcileReport:
    """The result of reconciling the whole manifest."""

    outcomes: list[AgentOutcome] = field(default_factory=list)

    @property
    def failed(self) -> tuple[AgentOutcome, ...]:
        return tuple(o for o in self.outcomes if o.outcome == OUTCOME_FAILED)

    @property
    def ok(self) -> bool:
        return not self.failed

    def summary(self) -> str:
        counts: dict[str, int] = {}
        for outcome in self.outcomes:
            counts[outcome.outcome] = counts.get(outcome.outcome, 0) + 1
        return ", ".join(f"{count} {name}" for name, count in sorted(counts.items()))

    def render(self) -> str:
        lines = [f"{'AGENT':<34} {'PROJECT':<11} {'OUTCOME':<9} DETAIL"]
        for outcome in self.outcomes:
            detail = outcome.detail or (
                f"version {outcome.version}" if outcome.version else ""
            )
            lines.append(
                f"{outcome.name:<34} {outcome.project:<11} "
                f"{outcome.outcome:<9} {detail}"
            )
        lines.append("")
        lines.append(self.summary() or "nothing to do")
        return "\n".join(lines)


def reconcile(
    specs: Sequence[AgentSpec] = MANIFEST,
    *,
    dry_run: bool = False,
    service_factory=None,
) -> ReconcileReport:
    """Apply every spec to its project.

    ``service_factory`` exists for tests and takes ``(project, endpoint)``; the
    default builds a real :class:`FoundryAgentService` per project so one client and
    one credential are reused across that project's agents.
    """
    report = ReconcileReport()
    factory = service_factory or _default_service_factory

    for project in _projects_in(specs):
        project_specs = [spec for spec in specs if spec.project == project]
        status = agent_service_status(project)
        if not status.enabled:
            # Not an error. A project that is not deployed in this environment — the
            # cost-capped demo estate does not run both — should leave the others
            # reconcilable rather than failing the release step.
            for spec in project_specs:
                report.outcomes.append(
                    AgentOutcome(spec.name, project, OUTCOME_SKIPPED, status.reason)
                )
            continue

        if dry_run:
            for spec in project_specs:
                report.outcomes.append(
                    AgentOutcome(
                        spec.name,
                        project,
                        OUTCOME_PLANNED,
                        f"would apply to {status.project_endpoint}",
                    )
                )
            continue

        try:
            service = factory(project, status.project_endpoint)
        except Exception as exc:
            logger.warning("Cannot reach the %s project: %s", project, exc)
            for spec in project_specs:
                report.outcomes.append(
                    AgentOutcome(spec.name, project, OUTCOME_FAILED, str(exc))
                )
            continue

        for spec in project_specs:
            report.outcomes.append(_apply(service, spec, project))

    return report


def _apply(service, spec: AgentSpec, project: str) -> AgentOutcome:
    """Apply one spec, turning any failure into an outcome rather than an exception.

    One malformed agent must not prevent the rest of the roster from being applied:
    a partially reconciled estate where the failure is named is far more useful than
    an aborted run where it is not.
    """
    try:
        hosted: HostedAgent = service.ensure_agent(spec)
    except Exception as exc:
        logger.exception("Failed to apply agent %s", spec.name)
        return AgentOutcome(
            spec.name, project, OUTCOME_FAILED, f"{type(exc).__name__}: {exc}"
        )
    return AgentOutcome(
        spec.name,
        project,
        OUTCOME_APPLIED,
        detail=f"tools: {', '.join(hosted.tools) or 'none'}",
        agent_id=hosted.agent_id,
        version=hosted.version,
    )


def _default_service_factory(project: str, endpoint: str) -> FoundryAgentService:
    return FoundryAgentService(
        project_endpoint=endpoint,
        model=os.environ.get(ENV_CHAT_DEPLOYMENT, DEFAULT_MODEL),
        knowledge_base=knowledge_base_config_from_env(),
    )


def _projects_in(specs: Sequence[AgentSpec]) -> tuple[str, ...]:
    if specs is MANIFEST:
        return projects()
    seen: list[str] = []
    for spec in specs:
        if spec.project not in seen:
            seen.append(spec.project)
    return tuple(seen)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point. Returns a non-zero exit code when any agent failed."""
    parser = argparse.ArgumentParser(
        prog="python -m knowledge_orchestrator.agent_reconciler",
        description="Apply the NovaSteel agent manifest to Foundry Agent Service.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be applied without calling Foundry.",
    )
    parser.add_argument(
        "--project",
        action="append",
        choices=list(projects()),
        help="Limit to one project. Repeatable. Defaults to every project.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    specs = MANIFEST
    if args.project:
        specs = tuple(
            spec for project in args.project for spec in agents_for_project(project)
        )

    report = reconcile(specs, dry_run=args.dry_run)
    print(report.render())
    return 0 if report.ok else 1


if __name__ == "__main__":  # pragma: no cover - CLI wiring
    sys.exit(main())


__all__ = [
    "OUTCOME_APPLIED",
    "OUTCOME_FAILED",
    "OUTCOME_PLANNED",
    "OUTCOME_SKIPPED",
    "AgentOutcome",
    "ReconcileReport",
    "main",
    "reconcile",
]
