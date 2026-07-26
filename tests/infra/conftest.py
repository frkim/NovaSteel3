"""Shared fixtures/paths for infra-focused validation tests.

These tests validate infra/ Bicep, parameter, and policy artifacts. They do not deploy anything —
network-touching steps (az deployment sub validate/what-if) belong to CI (cd-infra.yml), not this
suite, since they require a live Azure/OIDC session. Tests that shell out to the `az`/`bicep` CLI
skip gracefully (not fail) when the tool is unavailable, so this suite also runs in a minimal
environment.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INFRA_DIR = REPO_ROOT / "infra"
BICEP_DIR = INFRA_DIR / "bicep"
MODULES_DIR = BICEP_DIR / "modules"
PARAMETERS_DIR = BICEP_DIR / "parameters"
POLICY_DEFINITIONS_DIR = INFRA_DIR / "policy" / "definitions"
SCRIPTS_DIR = INFRA_DIR / "scripts"

ENVIRONMENTS = ["dev", "test", "demo", "prod"]

AZ_CLI_AVAILABLE = shutil.which("az") is not None


def _az_bicep_build(bicep_file: Path) -> subprocess.CompletedProcess:
    """Run `az bicep build --stdout` on a single .bicep file, returning the completed process."""
    return subprocess.run(
        ["az", "bicep", "build", "--file", str(bicep_file), "--stdout"],
        capture_output=True,
        text=True,
        timeout=120,
        shell=(os.name == "nt"),
    )


def _az_bicep_build_params(bicepparam_file: Path) -> subprocess.CompletedProcess:
    """Run `az bicep build-params --stdout` on a single .bicepparam file."""
    return subprocess.run(
        ["az", "bicep", "build-params", "--file", str(bicepparam_file), "--stdout"],
        capture_output=True,
        text=True,
        timeout=120,
        shell=(os.name == "nt"),
    )


@pytest.fixture(scope="session")
def bicep_files() -> list[Path]:
    return sorted(BICEP_DIR.rglob("*.bicep"))


@pytest.fixture(scope="session")
def bicepparam_files() -> list[Path]:
    return sorted(PARAMETERS_DIR.glob("*.bicepparam"))


@pytest.fixture(scope="session")
def policy_definition_files() -> list[Path]:
    return sorted(POLICY_DEFINITIONS_DIR.glob("*.json"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(read_text(path))
