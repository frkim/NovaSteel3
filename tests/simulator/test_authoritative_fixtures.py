"""Validates the simulator's contract-schema validator itself against the
application-foundation workstream's authoritative fixtures under
`contracts/events/fixtures/*.json`, and confirms the simulator's own
generated payloads structurally match those fixtures (same required keys),
per the 2026-07-25 coordination that finalized contracts/events/*.v1.schema.json
as authoritative."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from simulator.generator import generate_run
from simulator.scenario import load_manifest
from simulator.validators import contract_schema as schema_validator

from _helpers import scratch_dir

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "contracts" / "events" / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@unittest.skipUnless(FIXTURES_DIR.exists(), "contracts/events/fixtures not present in this checkout")
class AuthoritativeFixtureTests(unittest.TestCase):
    """The fixtures themselves must validate against their own schema
    (sanity check on the schema-subset validator)."""

    def test_telemetry_fixture_validates(self):
        fixture = _load_fixture("telemetry.valid.v1.json")
        report = schema_validator.validate_against_schema(fixture, "telemetry.v1.schema.json")
        self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_model_inference_fixture_validates(self):
        fixture = _load_fixture("model-inference.valid.v1.json")
        report = schema_validator.validate_against_schema(fixture, "model-inference.v1.schema.json")
        self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_alarm_fixture_validates(self):
        fixture = _load_fixture("alarm.valid.v1.json")
        report = schema_validator.validate_against_schema(fixture, "alarm.v1.schema.json")
        self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_energy_interval_fixture_validates(self):
        fixture = _load_fixture("energy-interval.valid.v1.json")
        report = schema_validator.validate_against_schema(fixture, "energy-interval.v1.schema.json")
        self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_quality_measurement_fixture_validates(self):
        fixture = _load_fixture("quality-measurement.valid.v1.json")
        report = schema_validator.validate_against_schema(fixture, "quality-measurement.v1.schema.json")
        self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_schemas_are_no_longer_restrictive(self):
        """Confirms the 2026-07-25 correction: none of the five event
        schemas should still be flagged as pre-correction/restrictive."""
        for schema_filename in ["telemetry.v1.schema.json", "model-inference.v1.schema.json",
                                 "alarm.v1.schema.json", "energy-interval.v1.schema.json",
                                 "quality-measurement.v1.schema.json"]:
            self.assertFalse(schema_validator.payload_schema_is_restrictive(schema_filename),
                              f"{schema_filename} still looks pre-correction (additionalProperties: false)")


@unittest.skipUnless(FIXTURES_DIR.exists(), "contracts/events/fixtures not present in this checkout")
class GeneratedPayloadMatchesFixtureShapeTests(unittest.TestCase):
    """The simulator's own generated payloads must carry (at least) the
    same required keys as the authoritative fixtures, and validate
    directly (no projection) against the corrected schemas."""

    @classmethod
    def setUpClass(cls):
        manifest = load_manifest("lining-degradation-21d")
        cls._scratch_cm = scratch_dir("fixture-shape-")
        out_dir = cls._scratch_cm.__enter__()
        cls.result = generate_run(manifest, out_dir=out_dir, fast=True)

    @classmethod
    def tearDownClass(cls):
        cls._scratch_cm.__exit__(None, None, None)

    def test_telemetry_payload_keys_are_superset_of_fixture(self):
        fixture_keys = set(_load_fixture("telemetry.valid.v1.json")["payload"].keys())
        for record in self.result.datasets["telemetry"]:
            self.assertTrue(fixture_keys.issubset(record["payload"].keys()))
            report = schema_validator.validate_against_schema(record, "telemetry.v1.schema.json")
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_model_inference_payload_keys_are_superset_of_fixture(self):
        fixture_keys = set(_load_fixture("model-inference.valid.v1.json")["payload"].keys())
        for record in self.result.datasets["model_inference"]:
            self.assertTrue(fixture_keys.issubset(record["payload"].keys()))
            report = schema_validator.validate_against_schema(record, "model-inference.v1.schema.json")
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_alarm_payload_keys_are_superset_of_fixture(self):
        fixture_keys = set(_load_fixture("alarm.valid.v1.json")["payload"].keys())
        self.assertGreaterEqual(len(self.result.datasets["alarm_event"]), 1)
        for record in self.result.datasets["alarm_event"]:
            self.assertTrue(fixture_keys.issubset(record["payload"].keys()))
            report = schema_validator.validate_against_schema(record, "alarm.v1.schema.json")
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_energy_interval_payload_keys_are_superset_of_fixture(self):
        fixture_keys = set(_load_fixture("energy-interval.valid.v1.json")["payload"].keys())
        for record in self.result.datasets["energy_interval"]:
            self.assertTrue(fixture_keys.issubset(record["payload"].keys()))
            report = schema_validator.validate_against_schema(record, "energy-interval.v1.schema.json")
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_quality_measurement_payload_keys_are_superset_of_fixture(self):
        fixture_keys = set(_load_fixture("quality-measurement.valid.v1.json")["payload"].keys())
        for record in self.result.datasets["quality_measurement"]:
            self.assertTrue(fixture_keys.issubset(record["payload"].keys()))
            report = schema_validator.validate_against_schema(record, "quality-measurement.v1.schema.json")
            self.assertTrue(report.ok, msg="\n".join(report.errors))


if __name__ == "__main__":
    unittest.main()
