"""PowerShell script sanity checks: every infra/scripts/*.ps1 file must parse without syntax
errors, and none may embed a static credential.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import SCRIPTS_DIR, read_text

PWSH_AVAILABLE = shutil.which("pwsh") is not None or shutil.which("powershell") is not None
PWSH_EXE = "pwsh" if shutil.which("pwsh") else "powershell"

FORBIDDEN_PATTERNS = [
    re.compile(r"AZURE_CREDENTIALS\s*="),
    re.compile(r"client-secret\s*:", re.IGNORECASE),
    re.compile(r"password\s*=\s*['\"]\S"),
]


@pytest.fixture(scope="session")
def script_files() -> list[Path]:
    files = sorted(SCRIPTS_DIR.glob("*.ps1"))
    assert files, "expected at least one .ps1 script under infra/scripts"
    return files


def test_expected_scripts_exist() -> None:
    expected = {
        "validate.ps1",
        "what-if.ps1",
        "deploy.ps1",
        "setup-github-oidc-managed-identity.ps1",
        "setup-github-oidc-app-registration.ps1",
    }
    actual = {f.name for f in SCRIPTS_DIR.glob("*.ps1")}
    missing = expected - actual
    assert not missing, f"infra/scripts is missing expected script(s): {missing}"


@pytest.mark.skipif(not PWSH_AVAILABLE, reason="pwsh/powershell is not installed")
def test_every_script_parses_without_syntax_errors(script_files: list[Path]) -> None:
    parse_snippet = (
        "$errors = $null; $tokens = $null; "
        "[void][System.Management.Automation.Language.Parser]::ParseFile('{path}', [ref]$tokens, [ref]$errors); "
        "if ($errors.Count -gt 0) {{ $errors | ForEach-Object {{ Write-Error $_ }}; exit 1 }} else {{ exit 0 }}"
    )
    failures = []
    for f in script_files:
        cmd = parse_snippet.format(path=str(f).replace("'", "''"))
        result = subprocess.run(
            [PWSH_EXE, "-NoProfile", "-NonInteractive", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            failures.append((f, result.stderr))
    if failures:
        details = "\n\n".join(f"{f}:\n{err}" for f, err in failures)
        pytest.fail(f"{len(failures)} script(s) failed to parse:\n\n{details}")


def test_no_script_embeds_a_static_azure_credential(script_files: list[Path]) -> None:
    for f in script_files:
        src = read_text(f)
        for pattern in FORBIDDEN_PATTERNS:
            assert not pattern.search(src), (
                f"{f.name} appears to reference a static credential pattern ({pattern.pattern}) "
                "— this repository's convention is OIDC/Workload Identity Federation only "
                "(security-governance-and-threat-model.md §3.2)"
            )


def test_deploy_script_refuses_static_credentials_in_environment() -> None:
    src = read_text(SCRIPTS_DIR / "deploy.ps1")
    assert "AZURE_CLIENT_SECRET" in src and "AZURE_CREDENTIALS" in src, (
        "deploy.ps1 should actively check for and refuse to run when "
        "AZURE_CLIENT_SECRET/AZURE_CREDENTIALS environment variables are set"
    )


def test_app_registration_script_defaults_to_dry_run() -> None:
    src = read_text(SCRIPTS_DIR / "setup-github-oidc-app-registration.ps1")
    assert "[bool]$Confirm = $false" in src, (
        "the tenant-admin-gated app-registration script must default to a dry run "
        "(-Confirm:$false) so it cannot execute a tenant-level Graph action unattended"
    )
