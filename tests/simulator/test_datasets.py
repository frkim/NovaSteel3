"""Dataset-coverage tests: electricity, production/genealogy, quality,
maintenance, and operator-knowledge datasets all exist with plausible
content; local NDJSON/CSV/JSON writers round-trip; the 21-day RUL truth
ledger carries the documented ground-truth labels (docs section 3, 9.1)."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from simulator import config
from simulator.generator import generate_run
from simulator.scenario import load_manifest
from simulator.writer import read_ndjson

from _helpers import scratch_dir


class DatasetCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = load_manifest("demo-full")
        cls._scratch_cm = scratch_dir("datasets-")
        out_dir = cls._scratch_cm.__enter__()
        cls.out_dir = out_dir
        cls.result = generate_run(manifest, out_dir=out_dir, fast=True, fmt="ndjson")

    @classmethod
    def tearDownClass(cls):
        cls._scratch_cm.__exit__(None, None, None)

    def test_electricity_dataset_present_and_plausible(self):
        energy = self.result.datasets["energy_interval"]
        self.assertEqual(len(energy), 96)
        for record in energy:
            payload = record["payload"]
            self.assertEqual(payload["price_unit"], "EUR/MWh")
            self.assertEqual(payload["demand_unit"], "MW")
            self.assertGreaterEqual(payload["price"], -60.0)
            self.assertLessEqual(payload["price"], 310.0)
            self.assertGreater(payload["grid_carbon_intensity_kgco2e_per_mwh"], 0.0)

    def test_production_genealogy_dataset_present(self):
        heat_batch = self.result.datasets["heat_batch"]
        self.assertGreater(len(heat_batch), 0)
        for record in heat_batch:
            payload = record["payload"]
            self.assertTrue(payload["material_id"].startswith("COIL-LUX-"))
            self.assertTrue(payload["heat_id"].startswith("H-LUX-"))
            self.assertIn(payload["grade_code"], config.GRADES)

    def test_quality_dataset_present_with_spec_limits(self):
        quality = self.result.datasets["quality_measurement"]
        self.assertEqual(len(quality), 20)
        for record in quality:
            payload = record["payload"]
            self.assertIn(payload["result_status"], {"PASS", "FAIL"})
            self.assertLess(payload["lower_spec_limit"], payload["upper_spec_limit"])

    def test_maintenance_dataset_present_for_degraded_scenario(self):
        maintenance = self.result.datasets["maintenance_event"]
        self.assertGreaterEqual(len(maintenance), 1)
        for record in maintenance:
            self.assertIn(record["failure_mode"], config.FAILURE_MODES)
            self.assertLess(record["detected_ts"], record["completed_ts"])

    def test_operator_knowledge_dataset_present_and_synthetic(self):
        knowledge = self.result.datasets["operator_knowledge"]
        self.assertGreaterEqual(len(knowledge), 2)
        session = knowledge[0]
        self.assertEqual(session["consent_state"], "SYNTHETIC-CONSENT-GRANTED")
        for segment in knowledge[1:]:
            self.assertIn("Demo synthetic transcript", segment["transcript"])
            self.assertEqual(segment["procedure_draft"]["reviewer_status"], "PENDING_EXPERT_REVIEW")

    def test_truth_ledger_carries_21_day_rul_and_documented_labels(self):
        truth = self.result.datasets["truth_ledger"]
        self.assertEqual(len(truth), 1)
        record = truth[0]
        for field_name in ["lining_state", "rul_days", "failure_within_21d", "sensor_fault_type",
                            "quality_outcome", "quality_drift_active", "energy_schedule_optimality_gap",
                            "anomaly_id"]:
            self.assertIn(field_name, record)
        self.assertGreaterEqual(record["rul_days"], 0.0)
        self.assertIn(record["lining_state"], {"healthy", "watch", "degraded", "critical"})

    def test_all_datasets_written_as_local_ndjson_files(self):
        for name in self.result.datasets:
            path = self.out_dir / f"{name}.ndjson"
            self.assertTrue(path.exists(), f"expected {path} to exist")
            records = read_ndjson(path)
            self.assertEqual(len(records), len(self.result.datasets[name]))

    def test_run_manifest_and_checksums_are_written(self):
        manifest_path = self.out_dir / "manifest.json"
        checksums_path = self.out_dir / "checksums.json"
        self.assertTrue(manifest_path.exists())
        self.assertTrue(checksums_path.exists())
        run_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(run_manifest["data_classification"], "SYNTHETIC")
        self.assertEqual(run_manifest["privacy_label"], "DEMO-NONPERSONAL")
        checksums = json.loads(checksums_path.read_text(encoding="utf-8"))
        self.assertIn("telemetry.ndjson", checksums)


class OutputFormatTests(unittest.TestCase):
    def test_csv_and_json_formats_are_writable(self):
        manifest = load_manifest("healthy-baseline")
        for fmt, ext in [("csv", "csv"), ("json", "json")]:
            with scratch_dir(f"format-{fmt}-") as out_dir:
                result = generate_run(manifest, out_dir=out_dir, fast=True, fmt=fmt)
                path = out_dir / f"telemetry.{ext}"
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 0)
                self.assertEqual(result.fmt, fmt)


if __name__ == "__main__":
    unittest.main()
