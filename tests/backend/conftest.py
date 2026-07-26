"""Shared backend test setup for the Python service sources."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
for source in (
    ROOT / "services" / "bff-api" / "src",
    ROOT / "services" / "optimizer-worker" / "src",
    ROOT / "services" / "scoring-worker" / "src",
    ROOT / "services" / "ingest-relay" / "src",
    ROOT / "services" / "knowledge-orchestrator" / "src",
):
    sys.path.insert(0, str(source))

from bff_api.main import create_app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {
        "X-Demo-User": "demo-admin",
        "X-Demo-Roles": (
            "Operator.Read,ProcessEngineer.Contribute,EnergyPlanner.Approve,"
            "MaintenanceEngineer.Read,Compliance.Auditor,"
            "Platform.Capacity.Manage,Knowledge.Publisher"
        ),
        "X-Demo-Plants": "NS-DEMO-LUX-01",
    }
