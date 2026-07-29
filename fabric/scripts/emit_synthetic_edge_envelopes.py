"""Emit synthetic gateway-health and quarantine envelopes for Eventstream route verification.

The NovaSteel simulator (``simulator/generator.py``) emits ``novasteel.telemetry.v1``,
``novasteel.alarm.v1`` and ``novasteel.model-inference.v1`` envelopes, but it does *not*
currently emit ``novasteel.gateway-health.v1`` or ``novasteel.quarantine.v1`` events.
Those two ``schema_name`` values are nonetheless routed by the Eventstream
``route-hot-schemas`` operator into the ``gateway_health_hot`` and ``ingest_quarantine_hot``
KQL tables. This helper hand-crafts a small, deterministic batch of those two envelope
shapes so the *infrastructure* path (route -> derived stream -> DirectIngestion -> KQL
table + named JSON mapping) can be proven end to end without a live simulator change.

Every record honours the synthetic-data guardrails (docs/data/synthetic-data-and-simulators.md):
``data_classification="SYNTHETIC"``, ``privacy_label="DEMO-NONPERSONAL"``,
``generator_version``/``scenario_id``/``seed`` present, and every synthetic entity id is
prefixed ``NS-DEMO-``. The field layout matches the live KQL ingestion mappings:
``gateway_health_v1_json`` reads its metrics from ``$.payload.*`` (payload-wrapped envelope),
whereas ``quarantine_v1_json`` reads its fields from the top level (flat envelope).

Output is written as ``<dataset>.ndjson`` files consumable by ``publish_to_eventstream.py``.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

GENERATOR_VERSION = "edge-verify-1"
SCENARIO_ID = "NS-DEMO-edge-verify"
SEED = 424242
PLANT_ID = "NS-DEMO-PLANT-LUX"
GATEWAY_ID = "NS-DEMO-GATEWAY-01"
ASSET_ID = "NS-DEMO-BF-01"


def _iso(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def build_gateway_health(count: int, base_ts: datetime) -> list[dict]:
    records = []
    for i in range(count):
        ts = base_ts + timedelta(seconds=15 * i)
        records.append(
            {
                "schema_name": "novasteel.gateway-health.v1",
                "schema_version": 1,
                "event_id": f"NS-DEMO-GH-{i:04d}",
                "event_ts": _iso(ts),
                "ingest_ts": _iso(ts + timedelta(milliseconds=8)),
                "sequence": 1000 + i,
                "source_id": GATEWAY_ID,
                "plant_id": PLANT_ID,
                "asset_id": ASSET_ID,
                "scenario_id": SCENARIO_ID,
                "correlation_id": f"NS-DEMO-CORR-GH-{i:04d}",
                "data_classification": "SYNTHETIC",
                "privacy_label": "DEMO-NONPERSONAL",
                "generator_version": GENERATOR_VERSION,
                "seed": SEED,
                "payload": {
                    "heartbeat_ts": _iso(ts),
                    "gateway_id": GATEWAY_ID,
                    "connection_state": "connected" if i % 5 else "reconnecting",
                    "partition_id": str(i % 4),
                    "last_sequence": 1000 + i,
                    "queue_depth": i % 3,
                    "oldest_buffered_event": _iso(ts - timedelta(seconds=2)),
                    "event_time_lag_ms": 12 + (i % 7),
                    "clock_offset_ms": 3 + (i % 2),
                    "duplicate_count": 0,
                    "publish_retry_count": i % 2,
                },
            }
        )
    return records


def build_quarantine(count: int, base_ts: datetime) -> list[dict]:
    records = []
    reasons = ["unit_mismatch", "schema_violation", "duplicate_event"]
    for i in range(count):
        ts = base_ts + timedelta(seconds=20 * i)
        reason = reasons[i % len(reasons)]
        records.append(
            {
                "schema_name": "novasteel.quarantine.v1",
                "schema_version": 1,
                "quarantine_id": f"NS-DEMO-Q-{i:04d}",
                "quarantined_at": _iso(ts + timedelta(milliseconds=20)),
                "event_id": f"NS-DEMO-EVT-Q-{i:04d}",
                "event_ts": _iso(ts),
                "ingest_ts": _iso(ts + timedelta(milliseconds=5)),
                "source_id": GATEWAY_ID,
                "plant_id": PLANT_ID,
                "asset_id": ASSET_ID,
                "quarantine_reason": reason,
                "quarantine_detail": f"synthetic {reason} injected for route verification",
                "expected_unit": "degC",
                "observed_unit": "degF" if reason == "unit_mismatch" else "degC",
                "duplicate_of_event_id": (
                    f"NS-DEMO-EVT-Q-{i - 1:04d}" if reason == "duplicate_event" and i else ""
                ),
                "original_payload": {
                    "sensor_id": "NS-DEMO-SENSOR-01",
                    "signal_code": "HEARTH_TEMP",
                    "value": 1450.0 + i,
                },
                "correlation_id": f"NS-DEMO-CORR-Q-{i:04d}",
                "data_classification": "SYNTHETIC",
                "privacy_label": "DEMO-NONPERSONAL",
                "generator_version": GENERATOR_VERSION,
                "scenario_id": SCENARIO_ID,
                "seed": SEED,
            }
        )
    return records


def _write_ndjson(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in records),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True, help="Directory to write <dataset>.ndjson files")
    parser.add_argument("--gateway-health", type=int, default=6, help="Number of gateway-health envelopes")
    parser.add_argument("--quarantine", type=int, default=6, help="Number of quarantine envelopes")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base_ts = datetime(2026, 6, 10, 1, 0, 0, tzinfo=timezone.utc)

    gh = build_gateway_health(args.gateway_health, base_ts)
    qz = build_quarantine(args.quarantine, base_ts)
    _write_ndjson(out_dir / "gateway_health.ndjson", gh)
    _write_ndjson(out_dir / "quarantine.ndjson", qz)

    print(f"wrote gateway_health.ndjson: {len(gh)} envelopes")
    print(f"wrote quarantine.ndjson: {len(qz)} envelopes")
    print(f"out-dir: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
