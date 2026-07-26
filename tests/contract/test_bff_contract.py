"""Contract-level checks for the implemented BFF surface."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml
from openapi_spec_validator import validate


ROOT = Path(__file__).resolve().parents[2]
for source in (
    ROOT / "services" / "bff-api" / "src",
    ROOT / "services" / "optimizer-worker" / "src",
    ROOT / "services" / "scoring-worker" / "src",
    ROOT / "services" / "knowledge-orchestrator" / "src",
):
    sys.path.insert(0, str(source))

from bff_api.main import create_app  # noqa: E402


def _normalize(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", path)


def test_canonical_openapi_is_valid_and_routes_are_implemented() -> None:
    contract_path = ROOT / "contracts" / "openapi" / "bff-api-v1.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    validate(contract)

    implemented = {_normalize(route.path) for route in create_app().routes}
    missing = {
        _normalize(path)
        for path in contract["paths"]
        if _normalize(path) not in implemented
    }
    assert missing == set()


def test_contract_declares_reconnect_poll_and_new_operational_projections() -> None:
    contract = yaml.safe_load(
        (ROOT / "contracts" / "openapi" / "bff-api-v1.yaml").read_text(encoding="utf-8")
    )
    paths = contract["paths"]

    assert "/v1/realtime/alerts:poll" in paths
    assert "/v1/dashboard/kpis" in paths
    assert "/v1/telemetry" in paths
    assert "/v1/energy/intervals" in paths
    assert "/v1/sustainability/summary" in paths
    assert contract["components"]["schemas"]["ErrorEnvelope"]["required"] == [
        "code",
        "message",
        "correlationId",
        "retryable",
    ]
