"""CLI tests: list-scenarios, generate, the one-command fast `demo`
subcommand, publish, validate, checksum, and reset."""
from __future__ import annotations

import io
import sys
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from simulator.cli import build_parser
from simulator.checksum import verify_checksums

from _helpers import scratch_dir


def run_cli(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = args.func(args)
    return rc, buf.getvalue()


class CliGenerateAndValidateTests(unittest.TestCase):
    def test_list_scenarios_reports_all_five_required_scenarios(self):
        rc, out = run_cli(["list-scenarios"])
        self.assertEqual(rc, 0)
        for scenario_id in ["healthy-baseline", "lining-degradation-21d", "energy-price-spike",
                             "quality-drift", "demo-full"]:
            self.assertIn(scenario_id, out)

    def test_generate_then_validate_round_trip(self):
        with scratch_dir("cli-gen-") as out_dir:
            rc, out = run_cli(["generate", "--scenario", "lining-degradation-21d", "--out", str(out_dir),
                                "--fast"])
            self.assertEqual(rc, 0)
            self.assertIn("telemetry:", out)

            rc, out = run_cli(["validate", "--run-dir", str(out_dir)])
            self.assertEqual(rc, 0, msg=out)
            self.assertIn("PASS", out)

    def test_checksum_verify_detects_tampering(self):
        with scratch_dir("cli-chk-") as out_dir:
            run_cli(["generate", "--scenario", "healthy-baseline", "--out", str(out_dir), "--fast"])
            ok, problems = verify_checksums(out_dir)
            self.assertTrue(ok, msg=problems)

            (out_dir / "telemetry.ndjson").write_text("tampered", encoding="utf-8")
            ok, problems = verify_checksums(out_dir)
            self.assertFalse(ok)
            self.assertTrue(any("telemetry.ndjson" in p for p in problems))

    def test_reset_removes_generated_output_only(self):
        with scratch_dir("cli-reset-") as out_dir:
            run_cli(["generate", "--scenario", "healthy-baseline", "--out", str(out_dir), "--fast"])
            self.assertTrue((out_dir / "manifest.json").exists())

            rc, out = run_cli(["reset", "--out", str(out_dir)])
            self.assertEqual(rc, 0)
            self.assertFalse((out_dir / "manifest.json").exists())
            self.assertFalse(any(out_dir.iterdir()))


class OneCommandFastDemoTests(unittest.TestCase):
    def test_demo_command_generates_quickly_and_validates(self):
        with scratch_dir("cli-demo-") as out_dir:
            start = time.monotonic()
            rc, out = run_cli(["demo", "--out", str(out_dir)])
            elapsed = time.monotonic() - start

            self.assertEqual(rc, 0)
            self.assertLess(elapsed, 15.0, "one-command demo should generate quickly")
            for dataset in ["telemetry", "energy_interval", "quality_measurement", "heat_batch",
                             "maintenance_event", "operator_knowledge", "model_inference", "truth_ledger"]:
                self.assertTrue((out_dir / f"{dataset}.ndjson").exists(), f"missing {dataset}.ndjson")

            rc, out = run_cli(["validate", "--run-dir", str(out_dir)])
            self.assertEqual(rc, 0, msg=out)


if __name__ == "__main__":
    unittest.main()
