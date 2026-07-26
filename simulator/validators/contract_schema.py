"""Minimal JSON Schema (subset) validator for the canonical wire contract
under ``contracts/events/*.schema.json``.

This intentionally implements only the subset of JSON Schema draft 2020-12
actually used by those files (``type``, ``required``, ``properties``,
``additionalProperties``, ``enum``, ``const``, ``pattern``, ``format``
date-time/uuid, ``minLength``/``maxLength``, ``minimum``, ``allOf``,
``if``/``then``, and local ``$ref`` to a sibling file) rather than
depending on a third-party ``jsonschema`` package, per the "standard
library where practical" rule. It is intended purely as a self-check that
the simulator's canonical-contract *projection*
(``simulator.contract_projection``) stays compatible with whatever the
application-foundation workstream publishes under ``contracts/events``.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_EVENTS_DIR = REPO_ROOT / "contracts" / "events"


@dataclass
class SchemaValidationReport:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    skipped_reason: str | None = None

    def add(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False


def contracts_available() -> bool:
    return CONTRACTS_EVENTS_DIR.exists()


def _load_schema(name: str) -> dict:
    return json.loads((CONTRACTS_EVENTS_DIR / name).read_text(encoding="utf-8"))


def payload_schema_is_restrictive(schema_filename: str) -> bool:
    """True if the checked-in schema's payload sub-schema still sets
    ``additionalProperties: false`` (i.e. it has not yet been corrected to
    the agreed additive shape -- see ``simulator/contract_projection.py``
    module docstring for the 2026-07-25 application-foundation
    coordination). Used so validators/tests can treat a known-transitional
    mismatch as "pending upstream fix" instead of a hard failure.
    """
    if not contracts_available():
        return False
    schema = _load_schema(schema_filename)
    for sub in schema.get("allOf", [schema]):
        payload_schema = sub.get("properties", {}).get("payload", {})
        if payload_schema.get("additionalProperties") is False:
            return True
    return False


def _is_uuid_v7(value: str) -> bool:
    return bool(re.match(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-7[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$", value))


def _is_date_time(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError):
        return False


def _check_node(instance, schema: dict, *, path: str, report: SchemaValidationReport, root_dir: Path) -> None:
    if "$ref" in schema:
        ref_schema = _load_schema(schema["$ref"])
        _check_node(instance, ref_schema, path=path, report=report, root_dir=root_dir)
        return

    if "allOf" in schema:
        for sub in schema["allOf"]:
            _check_node(instance, sub, path=path, report=report, root_dir=root_dir)

    if "if" in schema and "then" in schema:
        probe = SchemaValidationReport()
        _check_node(instance, schema["if"], path=path, report=probe, root_dir=root_dir)
        if probe.ok:
            _check_node(instance, schema["then"], path=path, report=report, root_dir=root_dir)

    schema_type = schema.get("type")
    if schema_type == "object" and not isinstance(instance, dict):
        report.add(f"{path}: expected object, got {type(instance).__name__}")
        return
    if schema_type == "string" and not isinstance(instance, str):
        report.add(f"{path}: expected string, got {type(instance).__name__}")
        return
    if schema_type == "integer" and not isinstance(instance, int):
        report.add(f"{path}: expected integer, got {type(instance).__name__}")
        return
    if schema_type == "number" and not isinstance(instance, (int, float)):
        report.add(f"{path}: expected number, got {type(instance).__name__}")
        return

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for field_name in required:
            if field_name not in instance:
                report.add(f"{path}: missing required field {field_name!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            allowed = set(properties)
            for key in instance:
                if key not in allowed:
                    report.add(f"{path}: unexpected additional property {key!r}")

        for key, sub_schema in properties.items():
            if key in instance:
                _check_node(instance[key], sub_schema, path=f"{path}.{key}", report=report, root_dir=root_dir)

    if isinstance(instance, str):
        if "const" in schema and instance != schema["const"]:
            report.add(f"{path}: expected const {schema['const']!r}, got {instance!r}")
        if "enum" in schema and instance not in schema["enum"]:
            report.add(f"{path}: value {instance!r} not in enum {schema['enum']}")
        if "pattern" in schema and not re.match(schema["pattern"], instance):
            report.add(f"{path}: value {instance!r} does not match pattern {schema['pattern']!r}")
        if schema.get("format") == "uuid" and not _is_uuid_v7(instance):
            report.add(f"{path}: value {instance!r} is not a well-formed UUID")
        if schema.get("format") == "date-time" and not _is_date_time(instance):
            report.add(f"{path}: value {instance!r} is not a valid date-time")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            report.add(f"{path}: string shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            report.add(f"{path}: string longer than maxLength {schema['maxLength']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "const" in schema and instance != schema["const"]:
            report.add(f"{path}: expected const {schema['const']!r}, got {instance!r}")
        if "minimum" in schema and instance < schema["minimum"]:
            report.add(f"{path}: value {instance} below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            report.add(f"{path}: value {instance} above maximum {schema['maximum']}")


def validate_against_schema(instance: dict, schema_filename: str) -> SchemaValidationReport:
    """Validate one record against a schema file in ``contracts/events``.

    Returns a report with ``skipped_reason`` set (and ``ok=True``) if the
    ``contracts/events`` directory is not present in this checkout, so
    tests remain self-contained even without the sibling workstream's
    output.
    """
    report = SchemaValidationReport()
    if not contracts_available():
        report.skipped_reason = f"contracts/events not found under {REPO_ROOT}"
        return report
    schema = _load_schema(schema_filename)
    _check_node(instance, schema, path="$", report=report, root_dir=CONTRACTS_EVENTS_DIR)
    return report
