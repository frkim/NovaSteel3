"""Static Bicep validation: every .bicep file under infra/bicep must compile with zero errors.

This mirrors infra/scripts/validate.ps1 step 1 so the same check runs in a plain pytest suite
(e.g. from a pre-commit hook or a lighter-weight CI job that doesn't want to invoke PowerShell).
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BICEP_DIR = REPOSITORY_ROOT / "infra" / "bicep"
AZ_CLI_AVAILABLE = shutil.which("az") is not None


def _az_bicep_build(bicep_file: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["az", "bicep", "build", "--file", str(bicep_file), "--stdout"],
        capture_output=True,
        text=True,
        timeout=120,
        shell=(os.name == "nt"),
    )

pytestmark = pytest.mark.skipif(
    not AZ_CLI_AVAILABLE, reason="az CLI (with the bicep extension) is not installed"
)


def test_every_bicep_file_builds_clean(bicep_files: list[Path]) -> None:
    assert bicep_files, "expected at least one .bicep file under infra/bicep"
    failures = []
    for f in bicep_files:
        result = _az_bicep_build(f)
        if result.returncode != 0:
            failures.append((f, result.stdout + result.stderr))
    if failures:
        details = "\n\n".join(f"{f}:\n{out}" for f, out in failures)
        pytest.fail(f"{len(failures)} .bicep file(s) failed to build:\n\n{details}")


@pytest.mark.parametrize(
    "relative_path",
    [
        "main.bicep",
        "modules/roles.bicep",
        "modules/network.bicep",
        "modules/identity.bicep",
        "modules/keyvault.bicep",
        "modules/storage.bicep",
        "modules/eventhubs.bicep",
        "modules/fabric-capacity.bicep",
        "modules/containerapps.bicep",
        "modules/foundry-speech.bicep",
        "modules/foundry-agents.bicep",
        "modules/foundry-agent-rbac.bicep",
        "modules/foundry-agent-capability-host.bicep",
        "modules/appinsights-agent-access.bicep",
        "modules/ai-search.bicep",
        "modules/cosmos.bicep",
        "modules/monitoring.bicep",
        "modules/logicapp-capacity-lifecycle.bicep",
        "modules/policy-assignments.bicep",
        "modules/budget.bicep",
    ],
)
def test_expected_module_files_exist(relative_path: str) -> None:
    assert (BICEP_DIR / relative_path).is_file(), (
        f"expected infra/bicep/{relative_path} to exist per the documented module inventory "
        "(implementation-guide.md §10, infra/README.md)"
    )
