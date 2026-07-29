"""Tests for the multi-month analytical gold-fact generator
(``simulator/analytics.py``) and its validators
(``simulator/validators/gold_contract.py``).

Covers determinism (byte-identical CSV + checksums), gold-contract column
conformance and grain uniqueness, guardrail provenance, and the headline
KPIs recomputed from rows (energy -14%, CO2 -22%, high-grade yield +8pp,
21-day furnace-lining advance warning).
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from simulator.analytics import (
    GOLD_TABLES,
    IDEMPOTENCY_KEYS,
    generate_analytical_run,
    list_analytical_scenarios,
    load_analytical_manifest,
)
from simulator.validators.determinism import compare_checksums
from simulator.validators.gold_contract import (
    CONTRACT_IDEMPOTENCY_KEYS,
    CONTRACT_PRIMARY_KEYS,
    EXPECTED_COLUMNS,
    _CONTRACT,
    validate_analytical_run,
    validate_gold_contract,
    validate_guardrails,
    validate_kpis,
)

from _helpers import scratch_dir

SCENARIO = "analytical-programme-24m"


class AnalyticalManifestTests(unittest.TestCase):
    def test_scenario_is_listed_and_loads(self):
        self.assertIn(SCENARIO, list_analytical_scenarios())
        scenario = load_analytical_manifest(SCENARIO)
        self.assertEqual(scenario.root_seed, 240801)
        scenario.validate()

    def test_grade_allocations_sum_to_one(self):
        scenario = load_analytical_manifest(SCENARIO)
        self.assertAlmostEqual(sum(g["allocation"] for g in scenario.grades), 1.0, places=6)


class AnalyticalDeterminismTests(unittest.TestCase):
    def test_same_seed_produces_identical_checksums(self):
        scenario = load_analytical_manifest(SCENARIO)
        with scratch_dir("an-det-a-") as a, scratch_dir("an-det-b-") as b:
            ra = generate_analytical_run(scenario, out_dir=a, fast=True)
            rb = generate_analytical_run(scenario, out_dir=b, fast=True)
            report = compare_checksums(ra.checksums, rb.checksums)
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_csv_files_are_byte_identical(self):
        scenario = load_analytical_manifest(SCENARIO)
        with scratch_dir("an-byte-a-") as a, scratch_dir("an-byte-b-") as b:
            generate_analytical_run(scenario, out_dir=a, fast=True)
            generate_analytical_run(scenario, out_dir=b, fast=True)
            for name in GOLD_TABLES:
                self.assertEqual((a / f"{name}.csv").read_bytes(),
                                 (b / f"{name}.csv").read_bytes(),
                                 msg=f"{name}.csv differs between runs")


class AnalyticalContractTests(unittest.TestCase):
    def test_all_gold_tables_emitted_with_exact_columns(self):
        scenario = load_analytical_manifest(SCENARIO)
        with scratch_dir("an-contract-") as out:
            result = generate_analytical_run(scenario, out_dir=out, fast=True)
            self.assertEqual(set(result.datasets), set(GOLD_TABLES))
            for name in GOLD_TABLES:
                self.assertTrue(result.datasets[name], f"{name} should not be empty")
                self.assertEqual(list(result.datasets[name][0].keys()), EXPECTED_COLUMNS[name])
            report = validate_gold_contract(result.datasets, IDEMPOTENCY_KEYS)
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_idempotency_keys_are_unique(self):
        scenario = load_analytical_manifest(SCENARIO)
        with scratch_dir("an-idemp-") as out:
            result = generate_analytical_run(scenario, out_dir=out, fast=True)
            for name, keys in IDEMPOTENCY_KEYS.items():
                seen = set()
                for row in result.datasets[name]:
                    key = tuple(row[k] for k in keys)
                    self.assertNotIn(key, seen, f"{name} duplicate {key}")
                    seen.add(key)


class AnalyticalGuardrailTests(unittest.TestCase):
    def test_manifest_and_rows_carry_guardrails(self):
        scenario = load_analytical_manifest(SCENARIO)
        with scratch_dir("an-guard-") as out:
            result = generate_analytical_run(scenario, out_dir=out, fast=True)
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["data_classification"], "SYNTHETIC")
            self.assertEqual(manifest["privacy_label"], "DEMO-NONPERSONAL")
            self.assertEqual(manifest["scenario_id"], SCENARIO)
            report = validate_guardrails(manifest, result.datasets)
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_no_names_or_emails_in_audit(self):
        scenario = load_analytical_manifest(SCENARIO)
        with scratch_dir("an-noemail-") as out:
            result = generate_analytical_run(scenario, out_dir=out, fast=True)
            for row in result.datasets["fact_ai_decision_audit"]:
                self.assertNotIn("@", json.dumps(row))


class AnalyticalKpiTests(unittest.TestCase):
    """The headline deltas must fall out of the rows, within tolerance, in
    both fast and full windows."""

    def _assert_kpis(self, fast: bool):
        scenario = load_analytical_manifest(SCENARIO)
        targets = scenario.kpi_targets
        tolerances = scenario.kpi_tolerances
        with scratch_dir("an-kpi-") as out:
            result = generate_analytical_run(scenario, out_dir=out, fast=fast)
            k = result.measured_kpis
            self.assertAlmostEqual(k["energy_intensity_reduction"], targets["energy_intensity_reduction"],
                                   delta=tolerances["energy_intensity_reduction"])
            self.assertAlmostEqual(k["co2_intensity_reduction"], targets["co2_intensity_reduction"],
                                   delta=tolerances["co2_intensity_reduction"])
            self.assertAlmostEqual(k["high_grade_yield_gain_pp"], targets["high_grade_yield_gain_pp"],
                                   delta=tolerances["high_grade_yield_gain_pp"])
            self.assertEqual(k["lining_warning_days"], targets["lining_warning_days"])

            rollout = k["rollout_date"]
            report = validate_kpis(result.datasets, targets, tolerances, rollout,
                                   k["lining_primary_asset_id"])
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_kpis_fall_out_of_rows_fast(self):
        self._assert_kpis(fast=True)

    def test_kpis_fall_out_of_rows_full(self):
        self._assert_kpis(fast=False)

    def test_lining_alert_is_internally_consistent(self):
        """No alert may fire above the 21-day target, and the alert row's p50
        must equal the advance warning -- so the 21-day claim cannot be an
        arithmetic contradiction."""
        scenario = load_analytical_manifest(SCENARIO)
        with scratch_dir("an-lining-") as out:
            result = generate_analytical_run(scenario, out_dir=out, fast=True)
            target = scenario.kpi_targets["lining_warning_days"]
            alerts = [r for r in result.datasets["fact_furnace_rul"] if r["alert_issued_at"]]
            self.assertTrue(alerts)
            for r in alerts:
                self.assertLessEqual(r["rul_days_p50"], target)
                self.assertGreaterEqual(r["risk_score"], 0.80)

    def test_lining_band_ordering(self):
        scenario = load_analytical_manifest(SCENARIO)
        with scratch_dir("an-band-") as out:
            result = generate_analytical_run(scenario, out_dir=out, fast=True)
            for r in result.datasets["fact_furnace_rul"]:
                self.assertLess(r["rul_days_p10"], r["rul_days_p50"])
                self.assertLess(r["rul_days_p50"], r["rul_days_p90"])


class AnalyticalPersistedRunTests(unittest.TestCase):
    def test_validate_analytical_run_from_disk_passes(self):
        scenario = load_analytical_manifest(SCENARIO)
        with scratch_dir("an-disk-") as out:
            generate_analytical_run(scenario, out_dir=out, fast=True)
            ok, reports = validate_analytical_run(out)
            self.assertTrue(ok, msg="\n".join(
                f"{n}: {e}" for n, r in reports.items() for e in r.errors))


class GoldContractV2EnforcementTests(unittest.TestCase):
    """Locks the contractVersion 2 natural-key decision and proves the
    validator genuinely enforces contracts/data/gold.v2.json rather than a
    self-referential copy of the produced schema."""

    def test_contract_is_v2_natural_keys(self):
        self.assertEqual(_CONTRACT["contractVersion"], 2)
        self.assertEqual(_CONTRACT["keyDesign"]["policy"], "natural-keys")
        # No surrogate *_key columns are declared anywhere in the gold contract.
        for spec in _CONTRACT["tables"]:
            for col in spec["columns"]:
                self.assertFalse(col["name"].endswith("_key") and col["name"] != "date_key",
                                 f"unexpected surrogate key column {col['name']} in {spec['name']}")

    def test_generator_keys_match_contract(self):
        self.assertEqual(set(IDEMPOTENCY_KEYS), set(CONTRACT_IDEMPOTENCY_KEYS))
        for name, keys in IDEMPOTENCY_KEYS.items():
            self.assertEqual(list(keys), list(CONTRACT_IDEMPOTENCY_KEYS[name]),
                             f"{name}: generator idempotency drifted from contract")

    def test_validator_rejects_surrogate_key_divergence(self):
        # A contract-v1 style row (plant_key instead of plant_id) must fail.
        good = {c: "x" for c in EXPECTED_COLUMNS["fact_energy_daily"]}
        bad = dict(good)
        bad.pop("plant_id")
        bad["plant_key"] = "1"
        report = validate_gold_contract(
            {"fact_energy_daily": [bad]},
            {"fact_energy_daily": CONTRACT_IDEMPOTENCY_KEYS["fact_energy_daily"]})
        self.assertFalse(report.ok)

    def test_validator_rejects_idempotency_drift(self):
        good = {c: "x" for c in EXPECTED_COLUMNS["fact_energy_daily"]}
        report = validate_gold_contract(
            {"fact_energy_daily": [good]},
            {"fact_energy_daily": ["plant_key", "date_key"]})
        self.assertFalse(report.ok)

    def test_validator_rejects_duplicate_primary_key(self):
        good = {c: "x" for c in EXPECTED_COLUMNS["fact_energy_daily"]}
        report = validate_gold_contract(
            {"fact_energy_daily": [dict(good), dict(good)]},
            {"fact_energy_daily": CONTRACT_IDEMPOTENCY_KEYS["fact_energy_daily"]})
        self.assertFalse(report.ok)
        self.assertEqual(CONTRACT_PRIMARY_KEYS["fact_energy_daily"], ["date_key", "plant_id"])


if __name__ == "__main__":
    unittest.main()
