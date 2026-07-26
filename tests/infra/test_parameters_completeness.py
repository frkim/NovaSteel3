"""Completeness/consistency checks across the 4 environment .bicepparam files.

These are pure text-based checks (a lightweight regex parser for the small subset of Bicep
param-file syntax actually used here) so they run without any Azure/Bicep tooling installed.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import ENVIRONMENTS, PARAMETERS_DIR, read_text

PARAM_RE = re.compile(
    r"^param\s+(?P<name>\w+)\s*=\s*(?P<value>\[[^\]]*\]|'[^']*'|-?\d+|true|false)",
    re.MULTILINE,
)


def parse_params(path: Path) -> dict[str, str]:
    src = read_text(path)
    return {m.group("name"): m.group("value") for m in PARAM_RE.finditer(src)}


def param_file(env: str) -> Path:
    return PARAMETERS_DIR / f"{env}.bicepparam"


@pytest.mark.parametrize("env", ENVIRONMENTS)
def test_each_environment_file_declares_matching_environment_param(env: str) -> None:
    params = parse_params(param_file(env))
    assert params.get("environment") == f"'{env}'", (
        f"{env}.bicepparam must set param environment = '{env}'"
    )


@pytest.mark.parametrize("env", ENVIRONMENTS)
def test_each_environment_file_uses_an_allowed_location(env: str) -> None:
    params = parse_params(param_file(env))
    assert params.get("location") in {"'swedencentral'", "'westeurope'"}, (
        f"{env}.bicepparam location must be 'swedencentral' or 'westeurope'"
    )


@pytest.mark.parametrize("env", ENVIRONMENTS)
def test_each_environment_file_uses_approved_fabric_sku(env: str) -> None:
    params = parse_params(param_file(env))
    assert params.get("fabricSkuName") in {"'F2'", "'F4'"}, (
        f"{env}.bicepparam fabricSkuName must be F2 or F4 without a separate measured/owner "
        "sign-off (deployment-topology.md §6)"
    )


def test_expiry_date_is_mandatory_for_demo() -> None:
    params = parse_params(param_file("demo"))
    expiry = params.get("expiryDate", "''")
    assert expiry not in {"''", ""}, (
        "demo.bicepparam must set a non-empty expiryDate — mandatory for demo resources "
        "(deployment-topology.md §3.1)"
    )


def test_exactly_one_environment_deploys_subscription_wide_guardrails() -> None:
    """policy-assignments.bicep's guardrails are subscription-wide singletons — exactly one
    shipped environment parameter file should be the designated authoritative run."""
    true_envs = [
        env for env in ENVIRONMENTS if parse_params(param_file(env)).get("deployGuardrails") == "true"
    ]
    assert len(true_envs) == 1, (
        "expected exactly one environment's .bicepparam to set deployGuardrails = true (found "
        f"{true_envs}) to avoid redundant/racy concurrent subscription-scoped policy writes "
        "(infra/bicep/modules/policy-assignments.bicep header)"
    )


def test_prod_has_stricter_posture_than_non_prod() -> None:
    prod = parse_params(param_file("prod"))
    assert prod.get("deployFirewall") == "true", "prod should enable the hub Azure Firewall"
    retention = int(prod.get("logAnalyticsRetentionDays", "0"))
    assert retention >= 365, (
        "prod Log Analytics retention must be >= 365 days "
        "(security-governance-and-threat-model.md §9: '>= 1 year hot')"
    )


def test_no_environment_pre_enables_the_foundry_agent_service_gate() -> None:
    for env in ENVIRONMENTS:
        params = parse_params(param_file(env))
        assert params.get("foundryAgentServiceManuallyValidated") == "false", (
            f"{env}.bicepparam must ship with foundryAgentServiceManuallyValidated = false — "
            "this is a manual, tenant-verified gate and must never be pre-enabled by default "
            "(research/azure-ai-regions.md)"
        )


@pytest.mark.parametrize("env", ENVIRONMENTS)
def test_budget_contact_emails_are_non_empty(env: str) -> None:
    params = parse_params(param_file(env))
    value = params.get("budgetContactEmails", "[]")
    assert value.strip("[] \n") != "", f"{env}.bicepparam budgetContactEmails must not be empty"
