"""Tests for the release-time agent reconciler.

The reconciler exists because of a specific production failure: both deployed
Foundry projects contained zero agents, since the only code that created one ran
lazily inside a service that had never been deployed. These tests pin the behaviour
that makes it a dependable release step -- it applies every spec, it reports rather
than raises, and one broken agent does not take the roster down with it.
"""

from __future__ import annotations

from knowledge_orchestrator import agent_reconciler
from knowledge_orchestrator.agent_manifest import (
    MANIFEST,
    PROJECT_ENDPOINT_ENV,
    PROJECT_KNOWLEDGE,
    PROJECT_OPERATIONS,
    AgentSpec,
)
from knowledge_orchestrator.agent_reconciler import (
    OUTCOME_APPLIED,
    OUTCOME_FAILED,
    OUTCOME_PLANNED,
    OUTCOME_SKIPPED,
    reconcile,
)
from knowledge_orchestrator.agent_service import HostedAgent

ENDPOINT = "https://x.services.ai.azure.com/api/projects/p"
OPS_ENDPOINT = "https://x.services.ai.azure.com/api/projects/ops"


class _FakeService:
    """Records what it was asked to apply, and can be told to fail for one agent."""

    def __init__(self, project: str, endpoint: str, fail_for: str | None = None):
        self.project = project
        self.endpoint = endpoint
        self.fail_for = fail_for
        self.applied: list[str] = []

    def ensure_agent(self, spec, registry=None):
        if spec.name == self.fail_for:
            raise RuntimeError("model deployment not found")
        self.applied.append(spec.name)
        return HostedAgent(
            name=spec.name,
            agent_id=f"id-{spec.name}",
            model="gpt-5-mini",
            tools=tuple(spec.tools),
            version="3",
        )


def _factory(created: list[_FakeService], fail_for: str | None = None):
    def _make(project: str, endpoint: str) -> _FakeService:
        service = _FakeService(project, endpoint, fail_for)
        created.append(service)
        return service

    return _make


def _enable(monkeypatch, *projects: str) -> None:
    for project in projects:
        monkeypatch.setenv(
            PROJECT_ENDPOINT_ENV[project],
            OPS_ENDPOINT if project == PROJECT_OPERATIONS else ENDPOINT,
        )


def test_reconcile_applies_the_whole_manifest(monkeypatch):
    _enable(monkeypatch, PROJECT_KNOWLEDGE, PROJECT_OPERATIONS)
    created: list[_FakeService] = []

    report = reconcile(service_factory=_factory(created))

    assert report.ok
    assert {outcome.outcome for outcome in report.outcomes} == {OUTCOME_APPLIED}
    assert {outcome.name for outcome in report.outcomes} == {
        spec.name for spec in MANIFEST
    }


def test_reconcile_uses_one_client_per_project(monkeypatch):
    """A client and a credential per project, not per agent."""
    _enable(monkeypatch, PROJECT_KNOWLEDGE, PROJECT_OPERATIONS)
    created: list[_FakeService] = []

    reconcile(service_factory=_factory(created))

    assert len(created) == 2
    assert {service.project for service in created} == {
        PROJECT_KNOWLEDGE,
        PROJECT_OPERATIONS,
    }


def test_each_project_gets_its_own_endpoint(monkeypatch):
    """The two projects are a trust boundary; reconciling both against one endpoint
    would silently put tool-calling agents in the project that reads untrusted
    content."""
    _enable(monkeypatch, PROJECT_KNOWLEDGE, PROJECT_OPERATIONS)
    created: list[_FakeService] = []

    reconcile(service_factory=_factory(created))

    endpoints = {service.project: service.endpoint for service in created}
    assert endpoints[PROJECT_KNOWLEDGE] == ENDPOINT
    assert endpoints[PROJECT_OPERATIONS] == OPS_ENDPOINT


def test_an_undeployed_project_is_skipped_not_failed(monkeypatch):
    """The demo estate may not run both projects. That must not fail a release."""
    monkeypatch.delenv(PROJECT_ENDPOINT_ENV[PROJECT_OPERATIONS], raising=False)
    _enable(monkeypatch, PROJECT_KNOWLEDGE)
    created: list[_FakeService] = []

    report = reconcile(service_factory=_factory(created))

    assert report.ok
    by_project = {
        outcome.name: outcome.outcome
        for outcome in report.outcomes
        if outcome.project == PROJECT_OPERATIONS
    }
    assert set(by_project.values()) == {OUTCOME_SKIPPED}
    assert any(
        outcome.outcome == OUTCOME_APPLIED
        for outcome in report.outcomes
        if outcome.project == PROJECT_KNOWLEDGE
    )


def test_dry_run_touches_nothing(monkeypatch):
    _enable(monkeypatch, PROJECT_KNOWLEDGE, PROJECT_OPERATIONS)
    created: list[_FakeService] = []

    report = reconcile(dry_run=True, service_factory=_factory(created))

    assert created == []
    assert {outcome.outcome for outcome in report.outcomes} == {OUTCOME_PLANNED}
    assert report.ok


def test_one_broken_agent_does_not_stop_the_rest(monkeypatch):
    """A partially reconciled estate where the failure is named beats an aborted
    run where it is not."""
    _enable(monkeypatch, PROJECT_KNOWLEDGE, PROJECT_OPERATIONS)
    created: list[_FakeService] = []
    target = MANIFEST[0].name

    report = reconcile(service_factory=_factory(created, fail_for=target))

    assert not report.ok
    failed = {outcome.name for outcome in report.failed}
    assert failed == {target}
    applied = {
        outcome.name for outcome in report.outcomes if outcome.outcome == OUTCOME_APPLIED
    }
    assert applied == {spec.name for spec in MANIFEST} - {target}


def test_an_unreachable_project_fails_only_its_own_agents(monkeypatch):
    _enable(monkeypatch, PROJECT_KNOWLEDGE, PROJECT_OPERATIONS)

    def _make(project: str, endpoint: str):
        if project == PROJECT_OPERATIONS:
            raise RuntimeError("connection refused")
        return _FakeService(project, endpoint)

    report = reconcile(service_factory=_make)

    assert not report.ok
    outcomes = {
        outcome.project: outcome.outcome for outcome in report.outcomes
    }
    assert outcomes[PROJECT_OPERATIONS] == OUTCOME_FAILED
    assert outcomes[PROJECT_KNOWLEDGE] == OUTCOME_APPLIED


def test_reconcile_accepts_a_subset_of_specs(monkeypatch):
    """The CLI's --project flag narrows the roster; only those projects are touched."""
    _enable(monkeypatch, PROJECT_KNOWLEDGE, PROJECT_OPERATIONS)
    created: list[_FakeService] = []
    subset = [spec for spec in MANIFEST if spec.project == PROJECT_OPERATIONS]

    report = reconcile(subset, service_factory=_factory(created))

    assert {service.project for service in created} == {PROJECT_OPERATIONS}
    assert {outcome.name for outcome in report.outcomes} == {
        spec.name for spec in subset
    }


def test_report_render_names_every_agent(monkeypatch):
    _enable(monkeypatch, PROJECT_KNOWLEDGE, PROJECT_OPERATIONS)
    report = reconcile(service_factory=_factory([]))
    rendered = report.render()
    for spec in MANIFEST:
        assert spec.name in rendered
    assert report.summary() in rendered


def test_cli_dry_run_exits_zero(monkeypatch, capsys):
    _enable(monkeypatch, PROJECT_KNOWLEDGE, PROJECT_OPERATIONS)
    assert agent_reconciler.main(["--dry-run"]) == 0
    assert "planned" in capsys.readouterr().out


def test_cli_reports_failure_with_a_nonzero_exit(monkeypatch):
    """A release step that cannot fail the pipeline is not a release step."""
    _enable(monkeypatch, PROJECT_KNOWLEDGE, PROJECT_OPERATIONS)

    def _boom(project: str, endpoint: str):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(agent_reconciler, "_default_service_factory", _boom)
    assert agent_reconciler.main([]) != 0


def test_cli_project_filter_selects_one_project(monkeypatch, capsys):
    _enable(monkeypatch, PROJECT_KNOWLEDGE, PROJECT_OPERATIONS)
    agent_reconciler.main(["--dry-run", "--project", PROJECT_OPERATIONS])
    out = capsys.readouterr().out
    assert PROJECT_KNOWLEDGE not in out
    for spec in MANIFEST:
        if spec.project == PROJECT_OPERATIONS:
            assert spec.name in out


def test_spec_projects_are_preserved_for_custom_rosters():
    """A hand-built roster reconciles against the project its specs declare."""
    spec = AgentSpec(
        name="test-agent",
        project=PROJECT_OPERATIONS,
        description="d",
        instructions="i",
        tools=(),
    )
    assert agent_reconciler._projects_in([spec]) == (PROJECT_OPERATIONS,)
