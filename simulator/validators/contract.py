"""Contract validator (docs section 10.1).

Checks envelope schema conformance, classification/privacy labels,
event-time ordering, per-source sequence monotonicity, unit/registry
membership, and NaN/Infinity rejection -- independent of any particular
scenario's physics.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from simulator import config

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.IGNORECASE)

ENVELOPE_REQUIRED_FIELDS = [
    "schema_name", "schema_version", "event_id", "event_ts", "ingest_ts", "sequence",
    "source_id", "plant_id", "asset_id", "scenario_id", "correlation_id",
    "data_classification", "privacy_label", "generator_version", "seed", "payload",
]


@dataclass
class ValidationReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    checked_records: int = 0

    def add(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_envelopes(records: list[dict], *, known_plants: set[str] | None = None,
                        known_assets: set[str] | None = None,
                        clock_mode: str = "accelerated") -> ValidationReport:
    known_plants = known_plants or set(config.PLANTS)
    known_assets = known_assets or set(config.ASSETS)
    report = ValidationReport(ok=True)
    seen_event_ids: set[str] = set()
    last_sequence_by_source: dict[str, int] = {}

    for i, record in enumerate(records):
        report.checked_records += 1
        missing = [f for f in ENVELOPE_REQUIRED_FIELDS if f not in record]
        if missing:
            report.add(f"record[{i}]: missing envelope fields {missing}")
            continue

        if record["data_classification"] != config.DATA_CLASSIFICATION:
            report.add(f"record[{i}]: unexpected data_classification {record['data_classification']!r}")
        if record["privacy_label"] != config.PRIVACY_LABEL:
            report.add(f"record[{i}]: unexpected privacy_label {record['privacy_label']!r}")

        event_id = record["event_id"]
        if not UUID_RE.match(event_id):
            report.add(f"record[{i}]: event_id {event_id!r} is not a well-formed UUIDv7")
        if event_id in seen_event_ids:
            report.add(f"record[{i}]: duplicate event_id {event_id!r}")
        seen_event_ids.add(event_id)

        try:
            event_ts = _parse_ts(record["event_ts"])
            ingest_ts = _parse_ts(record["ingest_ts"])
        except ValueError as exc:
            report.add(f"record[{i}]: unparsable timestamp ({exc})")
        else:
            if clock_mode != "accelerated" and event_ts > ingest_ts + timedelta(seconds=5):
                report.add(f"record[{i}]: event_ts {event_ts} more than 5s ahead of ingest_ts {ingest_ts}")

        source_id = record["source_id"]
        sequence = record["sequence"]
        if source_id in last_sequence_by_source and sequence <= last_sequence_by_source[source_id]:
            report.add(f"record[{i}]: sequence {sequence} not strictly increasing for source {source_id!r}")
        last_sequence_by_source[source_id] = sequence

        if record["plant_id"] not in known_plants:
            report.add(f"record[{i}]: unknown plant_id {record['plant_id']!r}")
        if record["asset_id"] not in known_assets:
            report.add(f"record[{i}]: unknown asset_id {record['asset_id']!r}")

        payload = record["payload"]
        _check_no_nan_or_inf(payload, path=f"record[{i}].payload", report=report)

        unit = payload.get("unit")
        if unit is not None and unit not in config.UCUM_UNITS:
            report.add(f"record[{i}]: unit {unit!r} not in the canonical unit registry")

        quality = payload.get("quality")
        if quality is not None and quality not in config.QUALITY_FLAGS:
            report.add(f"record[{i}]: quality flag {quality!r} not one of {sorted(config.QUALITY_FLAGS)}")

        event_type = payload.get("type")
        if event_type is not None and event_type not in config.TELEMETRY_EVENT_TYPES:
            report.add(f"record[{i}]: payload type {event_type!r} not one of {sorted(config.TELEMETRY_EVENT_TYPES)}")

    return report


def _check_no_nan_or_inf(value, *, path: str, report: ValidationReport) -> None:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            report.add(f"{path}: NaN/Infinity value is not allowed")
    elif isinstance(value, dict):
        for k, v in value.items():
            _check_no_nan_or_inf(v, path=f"{path}.{k}", report=report)
    elif isinstance(value, list):
        for idx, v in enumerate(value):
            _check_no_nan_or_inf(v, path=f"{path}[{idx}]", report=report)
