"""Scenario acceptance-threshold tests (docs section 10.3): the three
scenario-specific assertions the specification calls out by seed."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from simulator.generator import generate_run
from simulator.scenario import load_manifest
from simulator.validators.scenario_assertions import validate_scenario

from _helpers import scratch_dir


class LiningScenarioAssertionTests(unittest.TestCase):
    """seed 240726: 21-day P50 warning for HEARTH-SECTOR-07, P10 < P50 <
    P90, risk >= 0.80 (docs 10.3)."""

    def test_lining_degradation_hits_21_day_p50_warning(self):
        manifest = load_manifest("lining-degradation-21d")
        self.assertEqual(manifest.root_seed, 240726)
        with scratch_dir("lining-assert-") as out_dir:
            result = generate_run(manifest, out_dir=out_dir, fast=False)
            summary = result.summary

            self.assertEqual(summary["lining_component_id"], "HEARTH-SECTOR-07")
            self.assertAlmostEqual(summary["lining_rul_p50_days"], 21.0, delta=2.0)
            self.assertLess(summary["lining_rul_p10_days"], summary["lining_rul_p50_days"])
            self.assertLess(summary["lining_rul_p50_days"], summary["lining_rul_p90_days"])
            self.assertGreaterEqual(summary["lining_risk_score"], 0.80)

            report = validate_scenario(summary, manifest.expected_assertions)
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_healthy_baseline_does_not_trigger_a_lining_warning(self):
        manifest = load_manifest("healthy-baseline")
        with scratch_dir("baseline-assert-") as out_dir:
            result = generate_run(manifest, out_dir=out_dir, fast=True)
            self.assertEqual(result.summary["lining_state"], "healthy")
            self.assertGreaterEqual(result.summary["lining_rul_p50_days"], 100.0)


class EnergyScenarioAssertionTests(unittest.TestCase):
    """seed 240727: optimized schedule costs less than baseline with equal
    planned tonnage and zero hard-constraint violations (docs 10.3)."""

    def test_energy_price_spike_optimizer_reduces_cost_without_violations(self):
        manifest = load_manifest("energy-price-spike")
        self.assertEqual(manifest.root_seed, 240727)
        with scratch_dir("energy-assert-") as out_dir:
            result = generate_run(manifest, out_dir=out_dir, fast=True)
            summary = result.summary

            self.assertLess(summary["energy_optimized_cost_eur"], summary["energy_baseline_cost_eur"])
            self.assertEqual(summary["energy_tonnage_before"], summary["energy_tonnage_after"])
            self.assertEqual(summary["energy_hard_constraint_violations"], 0)
            self.assertLessEqual(summary["energy_peak_demand_during_spike_after_mw"],
                                  summary["energy_peak_demand_during_spike_before_mw"])

            report = validate_scenario(summary, manifest.expected_assertions)
            self.assertTrue(report.ok, msg="\n".join(report.errors))


class QualityScenarioAssertionTests(unittest.TestCase):
    """seed 240728: the quality warning precedes the first off-spec result
    and the recommended correction improves predicted first-pass yield
    (docs 10.3)."""

    def test_quality_drift_warning_precedes_first_off_spec_and_yield_improves(self):
        manifest = load_manifest("quality-drift")
        self.assertEqual(manifest.root_seed, 240728)
        with scratch_dir("quality-assert-") as out_dir:
            result = generate_run(manifest, out_dir=out_dir, fast=False)
            summary = result.summary

            self.assertIsNotNone(summary["quality_warning_ts"])
            self.assertIsNotNone(summary["quality_first_off_spec_ts"])
            self.assertLess(summary["quality_warning_ts"], summary["quality_first_off_spec_ts"])
            self.assertLessEqual(summary["quality_predicted_yield_before"], 0.90)
            self.assertGreaterEqual(summary["quality_predicted_yield_after"], 0.93)
            self.assertGreater(summary["quality_predicted_yield_after"], summary["quality_predicted_yield_before"])

            report = validate_scenario(summary, manifest.expected_assertions)
            self.assertTrue(report.ok, msg="\n".join(report.errors))


class FullDemoNarrativeTests(unittest.TestCase):
    """The combined demo-full manifest should still satisfy every
    sub-scenario's assertion when run at full (non-fast) duration."""

    def test_demo_full_normal_duration_satisfies_all_assertions(self):
        manifest = load_manifest("demo-full")
        with scratch_dir("demo-full-assert-") as out_dir:
            result = generate_run(manifest, out_dir=out_dir, fast=False)
            report = validate_scenario(result.summary, manifest.expected_assertions)
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_demo_full_fast_mode_is_quick_and_contract_valid(self):
        from simulator.validators.contract import validate_envelopes
        from simulator.validators.physics import validate_furnace_physics
        import time

        manifest = load_manifest("demo-full")
        with scratch_dir("demo-full-fast-") as out_dir:
            start = time.monotonic()
            result = generate_run(manifest, out_dir=out_dir, fast=True)
            elapsed = time.monotonic() - start

            self.assertLess(elapsed, 15.0, "fast demo generation should complete in well under 15s")
            contract_report = validate_envelopes(result.datasets["telemetry"])
            self.assertTrue(contract_report.ok, msg="\n".join(contract_report.errors))
            physics_report = validate_furnace_physics(result.datasets["telemetry"])
            self.assertTrue(physics_report.ok, msg="\n".join(physics_report.errors))


class EafFlexScenarioAssertionTests(unittest.TestCase):
    """seed 240730: EAF flexible load scheduling at the Belgium Liège Melt & Rolling Works.
    Optimized schedule costs less than baseline with equal tonnage and zero
    hard-constraint violations."""

    def test_eaf_flex_optimizer_reduces_cost_without_violations(self):
        manifest = load_manifest("energy-eaf-flex")
        self.assertEqual(manifest.root_seed, 240730)
        with scratch_dir("eaf-flex-assert-") as out_dir:
            result = generate_run(manifest, out_dir=out_dir, fast=True)
            summary = result.summary

            self.assertLess(summary["energy_optimized_cost_eur"], summary["energy_baseline_cost_eur"])
            self.assertEqual(summary["energy_tonnage_before"], summary["energy_tonnage_after"])
            self.assertEqual(summary["energy_hard_constraint_violations"], 0)

            report = validate_scenario(summary, manifest.expected_assertions)
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_eaf_flex_determinism(self):
        """Two generation runs produce identical results."""
        manifest = load_manifest("energy-eaf-flex")
        with scratch_dir("eaf-flex-det-a-") as dir_a, scratch_dir("eaf-flex-det-b-") as dir_b:
            result_a = generate_run(manifest, out_dir=dir_a, fast=True)
            result_b = generate_run(manifest, out_dir=dir_b, fast=True)
            self.assertEqual(result_a.checksums, result_b.checksums)

    def test_eaf_flex_heat_batch_payloads(self):
        """EAF heat batches carry tonnage and energyMwh in the payload."""
        manifest = load_manifest("energy-eaf-flex")
        with scratch_dir("eaf-flex-payload-") as out_dir:
            result = generate_run(manifest, out_dir=out_dir, fast=True)
            for record in result.datasets["heat_batch"]:
                payload = record["payload"]
                self.assertTrue(payload["operation_id"].startswith("EAF-"))
                self.assertIn("tonnage", payload)
                self.assertIn("energyMwh", payload)
                self.assertGreaterEqual(payload["tonnage"], 100.0)
                self.assertLessEqual(payload["tonnage"], 140.0)
                self.assertGreater(payload["energyMwh"], 14.0)  # much larger than reheat batches


if __name__ == "__main__":
    unittest.main()
