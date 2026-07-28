"""Reset/manifest/truth-ledger control tests: reset never touches the
checked-in scenario manifests, and the truth ledger is itself
deterministic across runs (docs demo-runbook section 9, docs 9.1)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from simulator.generator import generate_run
from simulator.reset import reset_run_directory
from simulator.scenario import MANIFEST_DIR, list_scenarios, load_manifest

from _helpers import scratch_dir


class ResetControlTests(unittest.TestCase):
    def test_reset_never_touches_checked_in_manifests(self):
        manifests_before = {p.name: p.read_text(encoding="utf-8") for p in MANIFEST_DIR.glob("*.json")}
        with scratch_dir("reset-scope-") as out_dir:
            manifest = load_manifest("healthy-baseline")
            generate_run(manifest, out_dir=out_dir, fast=True)
            reset_run_directory(out_dir)

        manifests_after = {p.name: p.read_text(encoding="utf-8") for p in MANIFEST_DIR.glob("*.json")}
        self.assertEqual(manifests_before, manifests_after)
        self.assertEqual(set(list_scenarios()),
                          {"healthy-baseline", "lining-degradation-21d", "energy-price-spike",
                           "quality-drift", "demo-full", "energy-eaf-flex"})

    def test_reset_on_missing_directory_is_a_no_op(self):
        missing_dir = MANIFEST_DIR.parent / "definitely-does-not-exist-12345"
        removed = reset_run_directory(missing_dir)
        self.assertEqual(removed, [])


class TruthLedgerControlTests(unittest.TestCase):
    def test_truth_ledger_is_deterministic_across_runs(self):
        manifest = load_manifest("lining-degradation-21d")
        with scratch_dir("truth-a-") as dir_a, scratch_dir("truth-b-") as dir_b:
            result_a = generate_run(manifest, out_dir=dir_a, fast=True)
            result_b = generate_run(manifest, out_dir=dir_b, fast=True)
            self.assertEqual(result_a.datasets["truth_ledger"], result_b.datasets["truth_ledger"])

    def test_truth_ledger_failure_within_21d_flag_matches_rul(self):
        manifest = load_manifest("lining-degradation-21d")
        with scratch_dir("truth-c-") as out_dir:
            result = generate_run(manifest, out_dir=out_dir, fast=True)
            record = result.datasets["truth_ledger"][0]
            expected_flag = 1 if record["rul_days"] <= 21 else 0
            self.assertEqual(record["failure_within_21d"], expected_flag)
            self.assertEqual(record["failure_within_21d"], 1)  # this scenario is calibrated to ~21 days


if __name__ == "__main__":
    unittest.main()
