"""Offline cross-component validation from deterministic simulator to local services."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
for source in (
    ROOT / "services" / "bff-api" / "src",
    ROOT / "services" / "optimizer-worker" / "src",
    ROOT / "services" / "scoring-worker" / "src",
    ROOT / "services" / "ingest-relay" / "src",
    ROOT / "services" / "knowledge-orchestrator" / "src",
    ROOT,
):
    sys.path.insert(0, str(source))

from bff_api.main import create_app  # noqa: E402
from ingest_relay import InMemoryEventstreamPublisher, IngestRelay  # noqa: E402
from optimizer_worker import EnergyDispatchOptimizer  # noqa: E402
from scoring_worker import ScoringWorker  # noqa: E402
from simulator.generator import generate_run  # noqa: E402
from simulator.scenario import load_manifest  # noqa: E402
from simulator.validators.contract import validate_envelopes  # noqa: E402
from simulator.validators.physics import validate_furnace_physics  # noqa: E402


def test_deterministic_demo_flows_through_relay_workers_and_bff() -> None:
    scratch_root = ROOT / "tests" / "simulator" / ".tmp"
    with tempfile.TemporaryDirectory(dir=scratch_root) as directory:
        run = generate_run(
            load_manifest("demo-full"),
            out_dir=Path(directory),
            fast=True,
        )

    telemetry = run.datasets["telemetry"]
    assert validate_envelopes(telemetry).ok
    assert validate_furnace_physics(telemetry).ok

    publisher = InMemoryEventstreamPublisher()
    relay = IngestRelay(publisher)
    outcomes = [relay.relay(event) for event in telemetry]
    assert {outcome.status for outcome in outcomes} == {"ACCEPTED"}
    assert len(publisher.published) == len(telemetry)

    score = ScoringWorker().score_lining(
        asset_id="LUX-BF-01",
        component_id=run.summary["lining_component_id"],
        telemetry=telemetry,
        source_ref="simulator:demo-full",
    )
    recommendation = EnergyDispatchOptimizer().simulate(
        site="NS-DEMO-LUX-01",
        horizon_hours=24,
        scenario="evening-scarcity",
        energy_intervals=run.datasets["energy_interval"],
        batches=run.datasets["heat_batch"],
        constraints={},
    )

    assert score["value"] == run.summary["lining_rul_p50_days"] == 21.0
    assert score["confidence"]["p10"] < score["value"] < score["confidence"]["p90"]
    assert recommendation["hardConstraintViolations"] == 0
    assert recommendation["baseline"]["tonnage"] == recommendation["optimized"]["tonnage"]

    response = TestClient(create_app()).get(
        "/v1/furnaces/LUX-BF-01/lining-forecast",
        headers={
            "X-Demo-User": "integration-engineer",
            "X-Demo-Roles": "MaintenanceEngineer.Read",
            "X-Demo-Plants": "NS-DEMO-LUX-01",
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["value"] == score["value"]
