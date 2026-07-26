"""Offline integration test: generated simulator fixture -> BFF -> domain workers."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
for source in (
    ROOT / "services" / "bff-api" / "src",
    ROOT / "services" / "optimizer-worker" / "src",
    ROOT / "services" / "scoring-worker" / "src",
    ROOT / "services" / "knowledge-orchestrator" / "src",
):
    sys.path.insert(0, str(source))

from bff_api.main import create_app  # noqa: E402


def test_local_demo_stack_uses_generated_simulator_fixture_end_to_end() -> None:
    app = create_app()
    client = TestClient(app)
    headers = {
        "X-Demo-User": "integration-demo",
        "X-Demo-Roles": "MaintenanceEngineer.Read,EnergyPlanner.Approve,ProcessEngineer.Contribute",
        "X-Demo-Plants": "NS-DEMO-LUX-01",
    }

    summary = client.get("/v1/command-center/summary", headers=headers)
    forecast = client.get("/v1/furnaces/LUX-BF-01/lining-forecast", headers=headers)
    energy = client.get("/v1/energy/intervals?size=1", headers=headers)
    quality = client.get(
        "/v1/quality/batches?batchId=COIL-LUX-260725-017", headers=headers
    )

    assert app.state.services.repository.source == "simulator-fixture:demo-full"
    assert summary.status_code == forecast.status_code == energy.status_code == quality.status_code == 200
    assert 15.0 <= forecast.json()["data"]["value"] <= 25.0
    assert energy.json()["total"] == 96
    assert quality.json()["total"] == 1
