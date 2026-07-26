"""Canonical wire-contract alignment for ``contracts/events/*.schema.json``
(owned by the ``app-scaffold`` / application-foundation workstream).

Per direct coordination with that workstream (2026-07-25, confirmed with
the corrected schema files the same day): the *rich*, docs-native payload
(``sensor_id``, ``signal_code``, ``value``, ``unit``, ``quality`` with the
full ``GOOD|UNCERTAIN|BAD|STALE|SUBSTITUTED`` enum, ``uncertainty``,
``sample_period_ms``, and for model-inference/alarm events the full
``docs/data/synthetic-data-and-simulators.md`` section 4.4 shapes
including the 5-state alarm lifecycle) is the agreed canonical shape for
every event type -- it is **not** narrowed for the wire, and the schemas
now declare additive fields explicitly allowed within v1 (no
``additionalProperties: false``). The only addition on top of the docs
payload is a closed ``type`` discriminator
(``simulator.config.TELEMETRY_EVENT_TYPES`` for telemetry/energy/quality;
``model.inference``/``alarm.event`` constants for the other two), which
the generator stamps directly onto the native payload (see
``simulator/generator.py``).

Every function below is therefore a near-identity passthrough: it only
backfills ``type`` if it is somehow missing (e.g. hand-built test
fixtures), and never drops or renames a field.
``simulator/validators/contract_schema.py::payload_schema_is_restrictive``
can still detect a stale/pre-correction schema file (``additionalProperties:
false``) so validators/tests degrade to a skip instead of a hard failure
if a future schema revision temporarily regresses.
"""
from __future__ import annotations

from simulator import config


def project_telemetry(record: dict) -> dict:
    """Ensure the canonical `type` discriminator is present; otherwise
    pass the rich native payload through unchanged."""
    payload = record["payload"]
    if "type" in payload:
        return record
    signal_code = payload.get("signal_code")
    projected_payload = {"type": config.telemetry_event_type(signal_code), **payload}
    return {**record, "payload": projected_payload}


def project_energy_interval(record: dict) -> dict:
    """Stamp the `energy.interval` classification token if missing;
    otherwise pass through. Validates directly against the dedicated
    ``contracts/events/energy-interval.v1.schema.json`` (added 2026-07-25),
    which requires exactly this payload's fields (`meter_id`,
    `interval_start`, `price`, `demand`, ...)."""
    payload = record["payload"]
    if "type" in payload:
        return record
    return {**record, "payload": {"type": "energy.interval", **payload}}


def project_quality_measurement(record: dict) -> dict:
    """Stamp the `quality.measurement` classification token if missing;
    otherwise pass through. Validates directly against the dedicated
    ``contracts/events/quality-measurement.v1.schema.json`` (added
    2026-07-25), which requires exactly this payload's fields
    (`material_id`, `heat_id`, `grade_code`, `sample_id`,
    `characteristic_code`, `value`, `unit`, spec limits,
    `measurement_method`, `result_status`)."""
    payload = record["payload"]
    if "type" in payload:
        return record
    return {**record, "payload": {"type": "quality.measurement", **payload}}


def project_model_inference(record: dict) -> dict:
    """Ensure the canonical `type` discriminator is present; otherwise
    pass the rich native payload (docs section 4.4 shape) through
    unchanged -- the corrected ``model-inference.v1.schema.json`` accepts
    it as-is."""
    payload = record["payload"]
    if "type" in payload:
        return record
    return {**record, "payload": {"type": "model.inference", **payload}}


def project_alarm(record: dict) -> dict:
    """Ensure the canonical `type` discriminator is present; otherwise
    pass the rich native payload (docs section 4.4 alert lifecycle, 5
    states) through unchanged -- the corrected ``alarm.v1.schema.json``
    accepts it as-is."""
    payload = record["payload"]
    if "type" in payload:
        return record
    return {**record, "payload": {"type": "alarm.event", **payload}}
