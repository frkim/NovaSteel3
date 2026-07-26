"""Contract validator tests (docs section 10.1) plus canonical wire-contract
compatibility tests against ``contracts/events/*.schema.json`` (skipped
gracefully if that directory is not present in the checkout)."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from simulator import contract_projection as proj
from simulator.generator import generate_run
from simulator.scenario import load_manifest
from simulator.validators import contract_schema as schema_validator
from simulator.validators.contract import validate_envelopes

from _helpers import scratch_dir


class ContractValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = load_manifest("lining-degradation-21d")
        cls._scratch_cm = scratch_dir("contract-")
        out_dir = cls._scratch_cm.__enter__()
        cls.result = generate_run(manifest, out_dir=out_dir, fast=True)

    @classmethod
    def tearDownClass(cls):
        cls._scratch_cm.__exit__(None, None, None)

    def test_generated_telemetry_passes_contract_validation(self):
        report = validate_envelopes(self.result.datasets["telemetry"])
        self.assertTrue(report.ok, msg="\n".join(report.errors))
        self.assertEqual(report.checked_records, len(self.result.datasets["telemetry"]))

    def test_duplicate_event_id_is_detected(self):
        records = copy.deepcopy(self.result.datasets["telemetry"][:5])
        records.append(copy.deepcopy(records[0]))
        report = validate_envelopes(records)
        self.assertFalse(report.ok)
        self.assertTrue(any("duplicate event_id" in e for e in report.errors))

    def test_non_monotonic_sequence_is_detected(self):
        records = copy.deepcopy(self.result.datasets["telemetry"][:3])
        records[1]["sequence"] = records[0]["sequence"]
        report = validate_envelopes(records)
        self.assertFalse(report.ok)
        self.assertTrue(any("not strictly increasing" in e for e in report.errors))

    def test_invalid_unit_is_rejected(self):
        records = copy.deepcopy(self.result.datasets["telemetry"][:1])
        records[0]["payload"]["unit"] = "not-a-real-unit"
        report = validate_envelopes(records)
        self.assertFalse(report.ok)
        self.assertTrue(any("unit" in e for e in report.errors))

    def test_nan_value_is_rejected(self):
        records = copy.deepcopy(self.result.datasets["telemetry"][:1])
        records[0]["payload"]["value"] = float("nan")
        report = validate_envelopes(records)
        self.assertFalse(report.ok)
        self.assertTrue(any("NaN" in e for e in report.errors))

    def test_wrong_data_classification_is_rejected(self):
        records = copy.deepcopy(self.result.datasets["telemetry"][:1])
        records[0]["data_classification"] = "PRODUCTION"
        report = validate_envelopes(records)
        self.assertFalse(report.ok)


class CanonicalWireContractTests(unittest.TestCase):
    """Verifies the simulator's canonical-contract projection stays
    compatible with contracts/events/*.schema.json owned by the
    application-foundation workstream. Skips (not fails) if that directory
    is absent, so this test suite remains self-contained."""

    @classmethod
    def setUpClass(cls):
        manifest = load_manifest("lining-degradation-21d")
        cls._scratch_cm = scratch_dir("contract-schema-")
        out_dir = cls._scratch_cm.__enter__()
        cls.result = generate_run(manifest, out_dir=out_dir, fast=True)

    @classmethod
    def tearDownClass(cls):
        cls._scratch_cm.__exit__(None, None, None)

    def _skip_if_unavailable(self):
        if not schema_validator.contracts_available():
            self.skipTest("contracts/events not present in this checkout")

    def _skip_if_schema_pending_correction(self, schema_filename: str):
        self._skip_if_unavailable()
        if schema_validator.payload_schema_is_restrictive(schema_filename):
            self.skipTest(
                f"{schema_filename} is still the pre-correction restrictive shape per the "
                "2026-07-25 application-foundation coordination (additionalProperties: false); "
                "rerun once the additive schema lands")

    def test_telemetry_projection_matches_canonical_schema(self):
        self._skip_if_schema_pending_correction("telemetry.v1.schema.json")
        for record in self.result.datasets["telemetry"]:
            report = schema_validator.validate_against_schema(
                proj.project_telemetry(record), "telemetry.v1.schema.json")
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_model_inference_projection_matches_canonical_schema(self):
        self._skip_if_unavailable()
        for record in self.result.datasets["model_inference"]:
            report = schema_validator.validate_against_schema(
                proj.project_model_inference(record), "model-inference.v1.schema.json")
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_alarm_projection_matches_canonical_schema(self):
        self._skip_if_unavailable()
        self.assertTrue(len(self.result.datasets["alarm_event"]) >= 1)
        for record in self.result.datasets["alarm_event"]:
            report = schema_validator.validate_against_schema(
                proj.project_alarm(record), "alarm.v1.schema.json")
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_energy_interval_projection_matches_canonical_schema(self):
        self._skip_if_schema_pending_correction("energy-interval.v1.schema.json")
        for record in self.result.datasets["energy_interval"]:
            self.assertEqual(record["schema_name"], "novasteel.energy-interval.v1")
            report = schema_validator.validate_against_schema(
                proj.project_energy_interval(record), "energy-interval.v1.schema.json")
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_quality_measurement_projection_matches_canonical_schema(self):
        self._skip_if_schema_pending_correction("quality-measurement.v1.schema.json")
        for record in self.result.datasets["quality_measurement"]:
            self.assertEqual(record["schema_name"], "novasteel.quality-measurement.v1")
            report = schema_validator.validate_against_schema(
                proj.project_quality_measurement(record), "quality-measurement.v1.schema.json")
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_native_telemetry_payload_has_rich_docs_fields_and_type_discriminator(self):
        """Regardless of the external schema file's current state, the
        simulator's own native payload must keep the rich docs section 4.2
        fields (never narrowed) and carry the agreed `type` discriminator."""
        from simulator import config

        for record in self.result.datasets["telemetry"]:
            payload = record["payload"]
            for required_field in ["sensor_id", "signal_code", "value", "unit", "quality",
                                    "uncertainty", "sample_period_ms", "type"]:
                self.assertIn(required_field, payload)
            self.assertIn(payload["type"], config.TELEMETRY_EVENT_TYPES)
            self.assertIn(payload["quality"], config.QUALITY_FLAGS)


if __name__ == "__main__":
    unittest.main()
