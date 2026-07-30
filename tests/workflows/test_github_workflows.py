"""Structural validation for every GitHub Actions workflow in this repository.

The workflows are the only automated gate in front of `main`, so a broken
trigger filter, an unresolvable `needs` reference or an unpinned action stays
invisible until a run fails (or, worse, silently stops running). These tests
parse `.github/workflows/*.yml` and assert the invariants the repository relies
on, including the supply-chain hardening rules documented in
`docs/tech/security_requirement.md`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = ROOT / ".github" / "workflows"

WORKFLOW_FILES = sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(WORKFLOW_DIR.glob("*.yaml"))

PINNED_SHA = re.compile(r"^[0-9a-f]{40}$")
USES_LINE = re.compile(r"^\s*-?\s*uses:\s*(?P<action>[^@\s]+)@(?P<ref>\S+)(?P<rest>.*)$")
EXPRESSION = re.compile(r"\$\{\{\s*(?P<body>[^}]*?)\s*\}\}")
REPO_SCRIPT = re.compile(
    r"(?:tools/validation|tools/presentation|infra/scripts|fabric/scripts)/[\w.-]+\.(?:py|ps1|mjs|cjs)"
)
EMIT_FILTER = re.compile(r"^\s*emit\s+(?P<name>[\w-]+)\s+'(?P<pattern>[^']+)'", re.MULTILINE)
FILTER_PATH = re.compile(r"[\w.-]+(?:/[\w.-]+)*/")

# Interpolating these contexts straight into a `run:` script splices
# attacker-influenced text into the shell. They must be passed through `env:`.
UNTRUSTED_RUN_CONTEXTS = ("inputs.", "github.event.", "steps.")


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _triggers(workflow: dict[str, Any]) -> dict[str, Any]:
    # PyYAML resolves the bare `on` key to the boolean True (YAML 1.1).
    triggers = workflow.get("on", workflow.get(True))
    assert triggers is not None, "the workflow declares no trigger"
    return triggers


def _steps(job: dict[str, Any]) -> list[dict[str, Any]]:
    return [step for step in job.get("steps", []) or [] if isinstance(step, dict)]


def _jobs(workflow: dict[str, Any]) -> dict[str, Any]:
    return workflow.get("jobs", {}) or {}


def test_the_workflow_directory_is_not_empty() -> None:
    assert WORKFLOW_FILES, f"no workflow files were found under {WORKFLOW_DIR}"


@pytest.mark.parametrize("path", WORKFLOW_FILES, ids=lambda p: p.name)
def test_workflow_parses_and_declares_least_privilege_permissions(path: Path) -> None:
    workflow = _load(path)
    assert isinstance(workflow, dict), f"{path.name} is not a YAML mapping"
    assert workflow.get("name"), f"{path.name} has no name"
    _triggers(workflow)
    assert _jobs(workflow), f"{path.name} declares no jobs"

    permissions = workflow.get("permissions")
    assert isinstance(permissions, dict), (
        f"{path.name} must declare an explicit top-level permissions block so it "
        "never inherits the default write token"
    )
    assert permissions.get("contents") == "read", (
        f"{path.name} must default to contents: read"
    )


@pytest.mark.parametrize("path", WORKFLOW_FILES, ids=lambda p: p.name)
def test_every_job_is_runnable_and_resolves_its_dependencies(path: Path) -> None:
    workflow = _load(path)
    jobs = _jobs(workflow)

    for job_id, job in jobs.items():
        assert job.get("runs-on") or job.get("uses"), (
            f"{path.name}: job '{job_id}' has neither runs-on nor a reusable workflow"
        )

        needs = job.get("needs", [])
        if isinstance(needs, str):
            needs = [needs]
        for dependency in needs:
            assert dependency in jobs, (
                f"{path.name}: job '{job_id}' needs unknown job '{dependency}'"
            )


@pytest.mark.parametrize("path", WORKFLOW_FILES, ids=lambda p: p.name)
def test_referenced_job_outputs_are_actually_declared(path: Path) -> None:
    workflow = _load(path)
    jobs = _jobs(workflow)
    text = path.read_text(encoding="utf-8")

    for producer, output in re.findall(r"needs\.([\w-]+)\.outputs\.([\w-]+)", text):
        assert producer in jobs, f"{path.name}: unknown job '{producer}' in a needs expression"
        declared = (jobs[producer].get("outputs") or {}).keys()
        assert output in declared, (
            f"{path.name}: job '{producer}' does not declare the output '{output}'"
        )


@pytest.mark.parametrize("path", WORKFLOW_FILES, ids=lambda p: p.name)
def test_every_action_is_pinned_to_a_commit_sha_with_a_readable_version(path: Path) -> None:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = USES_LINE.match(line)
        if not match:
            continue
        action = match.group("action")
        if action.startswith(("./", "docker://")):
            continue
        ref = match.group("ref")
        assert PINNED_SHA.fullmatch(ref), (
            f"{path.name}:{number} uses {action}@{ref}, which is not a full commit SHA"
        )
        assert "#" in match.group("rest"), (
            f"{path.name}:{number} pins {action} without a trailing '# vX.Y.Z' comment, "
            "so the pin cannot be reviewed or updated safely"
        )


@pytest.mark.parametrize("path", WORKFLOW_FILES, ids=lambda p: p.name)
def test_checkout_never_persists_the_workflow_token(path: Path) -> None:
    workflow = _load(path)
    for job_id, job in _jobs(workflow).items():
        for step in _steps(job):
            uses = step.get("uses", "")
            if not uses.startswith("actions/checkout@"):
                continue
            options = step.get("with") or {}
            assert options.get("persist-credentials") is False, (
                f"{path.name}: the checkout in job '{job_id}' must set "
                "persist-credentials: false"
            )


@pytest.mark.parametrize("path", WORKFLOW_FILES, ids=lambda p: p.name)
def test_run_scripts_never_interpolate_untrusted_context(path: Path) -> None:
    workflow = _load(path)
    for job_id, job in _jobs(workflow).items():
        for step in _steps(job):
            script = step.get("run")
            if not script:
                continue
            for expression in EXPRESSION.finditer(script):
                body = expression.group("body")
                assert not body.startswith(UNTRUSTED_RUN_CONTEXTS), (
                    f"{path.name}: step '{step.get('name', '<unnamed>')}' in job "
                    f"'{job_id}' splices ${{{{ {body} }}}} into a shell script. "
                    "Bind it to an env: variable and reference the variable instead."
                )


@pytest.mark.parametrize("path", WORKFLOW_FILES, ids=lambda p: p.name)
def test_trigger_path_filters_point_at_paths_that_exist(path: Path) -> None:
    triggers = _triggers(_load(path))
    if not isinstance(triggers, dict):
        return

    for event, configuration in triggers.items():
        if not isinstance(configuration, dict):
            continue
        for pattern in configuration.get("paths", []) or []:
            prefix = pattern.split("*", 1)[0].rstrip("/")
            if not prefix:
                continue
            assert (ROOT / prefix).exists(), (
                f"{path.name}: the {event} filter '{pattern}' matches nothing in the "
                "repository, so the workflow silently stops running"
            )


@pytest.mark.parametrize("path", WORKFLOW_FILES, ids=lambda p: p.name)
def test_working_directories_and_referenced_scripts_exist(path: Path) -> None:
    workflow = _load(path)
    for job_id, job in _jobs(workflow).items():
        for step in _steps(job):
            directory = step.get("working-directory") or (job.get("defaults", {}) or {}).get(
                "run", {}
            ).get("working-directory")
            if directory and "${{" not in directory:
                assert (ROOT / directory).is_dir(), (
                    f"{path.name}: job '{job_id}' runs in the missing directory '{directory}'"
                )

            script = step.get("run") or ""
            for referenced in set(REPO_SCRIPT.findall(script)):
                assert (ROOT / referenced).is_file(), (
                    f"{path.name}: job '{job_id}' invokes the missing script '{referenced}'"
                )


def test_ci_change_filters_match_directories_that_still_exist() -> None:
    """A moved component must not silently disable its CI job."""

    for name in ("ci.yml", "ci-build-services.yml"):
        text = (WORKFLOW_DIR / name).read_text(encoding="utf-8")
        filters = EMIT_FILTER.findall(text)
        assert filters, f"{name}: no change filters were found"

        for component, pattern in filters:
            candidates = FILTER_PATH.findall(pattern)
            assert candidates, f"{name}: filter '{component}' matches no path prefix"
            assert any((ROOT / candidate).is_dir() for candidate in candidates), (
                f"{name}: the '{component}' filter only references paths that no longer "
                f"exist ({', '.join(candidates)})"
            )


def test_every_workflow_is_documented() -> None:
    documentation = (ROOT / ".github" / "README.md").read_text(encoding="utf-8")
    for path in WORKFLOW_FILES:
        assert path.name in documentation, (
            f"{path.name} is not described in .github/README.md"
        )
