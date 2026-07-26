"""Determinism tests (docs section 6.1): the same manifest and root seed
must produce byte-identical output; a different seed must not."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from simulator.generator import generate_run
from simulator.scenario import load_manifest
from simulator.validators.determinism import compare_checksums, compare_datasets

from _helpers import scratch_dir


class DeterminismTests(unittest.TestCase):
    def test_same_seed_same_manifest_produces_identical_checksums(self):
        manifest = load_manifest("lining-degradation-21d")
        with scratch_dir("det-a-") as dir_a, scratch_dir("det-b-") as dir_b:
            result_a = generate_run(manifest, out_dir=dir_a, fast=True)
            result_b = generate_run(manifest, out_dir=dir_b, fast=True)

            report = compare_checksums(result_a.checksums, result_b.checksums)
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_same_seed_produces_identical_records_field_by_field(self):
        manifest = load_manifest("lining-degradation-21d")
        with scratch_dir("det-c-") as dir_a, scratch_dir("det-d-") as dir_b:
            result_a = generate_run(manifest, out_dir=dir_a, fast=True)
            result_b = generate_run(manifest, out_dir=dir_b, fast=True)

            for dataset_name in result_a.datasets:
                report = compare_datasets(result_a.datasets[dataset_name], result_b.datasets[dataset_name],
                                           dataset_name=dataset_name)
                self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_different_root_seed_diverges(self):
        manifest_a = load_manifest("healthy-baseline")   # seed 240725
        manifest_b = load_manifest("lining-degradation-21d")  # seed 240726, different physics too
        with scratch_dir("det-e-") as dir_a, scratch_dir("det-f-") as dir_b:
            result_a = generate_run(manifest_a, out_dir=dir_a, fast=True)
            result_b = generate_run(manifest_b, out_dir=dir_b, fast=True)

            report = compare_checksums(result_a.checksums, result_b.checksums)
            self.assertFalse(report.ok, "different seeds/scenarios should not produce identical output")

    def test_event_ids_are_stable_across_runs(self):
        """event_id (UUIDv7) must reproduce exactly, not just be well-formed,
        since it is the transport idempotency key (docs section 4.1)."""
        manifest = load_manifest("healthy-baseline")
        with scratch_dir("det-g-") as dir_a, scratch_dir("det-h-") as dir_b:
            result_a = generate_run(manifest, out_dir=dir_a, fast=True)
            result_b = generate_run(manifest, out_dir=dir_b, fast=True)

            ids_a = [r["event_id"] for r in result_a.datasets["telemetry"]]
            ids_b = [r["event_id"] for r in result_b.datasets["telemetry"]]
            self.assertEqual(ids_a, ids_b)
            self.assertEqual(len(ids_a), len(set(ids_a)), "event_id must be unique within a run")


if __name__ == "__main__":
    unittest.main()
