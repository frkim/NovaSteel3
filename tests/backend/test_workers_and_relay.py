from __future__ import annotations

import json
from pathlib import Path

from ingest_relay import InMemoryEventstreamPublisher, IngestRelay
from optimizer_worker import EnergyDispatchOptimizer
from scoring_worker import ScoringWorker


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "services" / "bff-api" / "fixtures" / "demo-full"


def _records(name: str) -> list[dict]:
    return [
        json.loads(line)
        for line in (FIXTURE / f"{name}.ndjson").read_text(encoding="utf-8").splitlines()
    ]


def test_optimizer_is_deterministic_and_preserves_hard_constraints() -> None:
    optimizer = EnergyDispatchOptimizer()
    args = {
        "site": "NS-DEMO-LUX-01",
        "horizon_hours": 24,
        "scenario": "evening-scarcity",
        "energy_intervals": _records("energy_interval"),
        "batches": _records("heat_batch"),
        "constraints": {},
    }
    first = optimizer.simulate(**args)
    second = optimizer.simulate(**args)

    assert first == second
    assert first["baseline"]["tonnage"] == first["optimized"]["tonnage"] == 960.0
    assert first["hardConstraintViolations"] == 0


def test_scoring_worker_keeps_uncertainty_ordered_and_bounded() -> None:
    worker = ScoringWorker()
    result = worker.score_lining(
        asset_id="LUX-BF-01",
        component_id="HEARTH-SECTOR-07",
        telemetry=_records("telemetry"),
        source_ref="simulator:test",
    )

    # Physics model derives RUL from regression on refractory thickness
    assert 15.0 <= result["value"] <= 25.0, f"RUL {result['value']} outside expected range"
    assert result["confidence"]["p10"] < result["value"] <= result["confidence"]["p90"]
    assert result["riskScore"] >= 0.8


def test_ingest_relay_quarantines_invalid_and_conflicting_duplicates() -> None:
    publisher = InMemoryEventstreamPublisher()
    relay = IngestRelay(publisher)
    valid = _records("telemetry")[0]

    assert relay.relay(valid).status == "ACCEPTED"
    assert relay.relay(valid).status == "DUPLICATE"
    conflicting = dict(valid)
    conflicting["payload"] = dict(valid["payload"]) | {"value": 999.0}
    assert relay.relay(conflicting).status == "QUARANTINED"
    assert relay.relay({"event_id": "bad"}).status == "QUARANTINED"
    assert len(publisher.published) == 1
    assert relay.health() == {"accepted": 1, "duplicates": 1, "quarantined": 2}
