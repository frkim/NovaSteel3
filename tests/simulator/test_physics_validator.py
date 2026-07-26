"""Physics validator tests (docs section 9.2/10.2): generated telemetry
must satisfy conductive heat-flux, cooling ΔT, monotonic thickness, and
rolling mass-balance constraints; injected violations must be caught."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from simulator.generator import generate_run
from simulator.scenario import load_manifest
from simulator.validators.physics import validate_furnace_physics

from _helpers import scratch_dir


class PhysicsValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = load_manifest("lining-degradation-21d")
        cls._scratch_cm = scratch_dir("physics-")
        out_dir = cls._scratch_cm.__enter__()
        cls.result = generate_run(manifest, out_dir=out_dir, fast=True)
        cls.telemetry = cls.result.datasets["telemetry"]

    @classmethod
    def tearDownClass(cls):
        cls._scratch_cm.__exit__(None, None, None)

    def test_generated_furnace_and_rolling_telemetry_passes_physics_checks(self):
        report = validate_furnace_physics(self.telemetry)
        self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_healthy_baseline_also_passes_physics_checks(self):
        manifest = load_manifest("healthy-baseline")
        with scratch_dir("physics-baseline-") as out_dir:
            result = generate_run(manifest, out_dir=out_dir, fast=True)
            report = validate_furnace_physics(result.datasets["telemetry"])
            self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_cooling_outlet_below_inlet_is_detected(self):
        records = copy.deepcopy(self.telemetry)
        outlet_record = next(r for r in records if r["payload"]["signal_code"] == "cooling_water_outlet_temperature")
        outlet_record["payload"]["value"] = -999.0
        report = validate_furnace_physics(records)
        self.assertFalse(report.ok)
        self.assertTrue(any("below inlet" in e for e in report.errors))

    def test_negative_heat_flux_is_detected(self):
        records = copy.deepcopy(self.telemetry)
        flux_record = next(r for r in records if r["payload"]["signal_code"] == "local_heat_flux")
        flux_record["payload"]["value"] = -5.0
        report = validate_furnace_physics(records)
        self.assertFalse(report.ok)
        self.assertTrue(any("negative heat flux" in e for e in report.errors))

    def test_thickness_increase_without_repair_is_detected(self):
        records = copy.deepcopy(self.telemetry)
        thickness_records = [r for r in records if r["payload"]["signal_code"] == "hearth_refractory_estimate"
                              and r["payload"]["hearth_sector"] == "07"]
        thickness_records.sort(key=lambda r: r["event_ts"])
        # Force an impossible jump upward on the last sample.
        thickness_records[-1]["payload"]["value"] = thickness_records[0]["payload"]["value"] + 500.0
        report = validate_furnace_physics(records)
        self.assertFalse(report.ok)
        self.assertTrue(any("increased" in e for e in report.errors))

    def test_rolling_mass_balance_violation_is_detected(self):
        records = copy.deepcopy(self.telemetry)
        speed_records = [r for r in records if r["payload"].get("signal_code") == "strip_speed"]
        self.assertGreater(len(speed_records), 0)
        speed_records[0]["payload"]["value"] *= 10.0
        report = validate_furnace_physics(records)
        self.assertFalse(report.ok)
        self.assertTrue(any("mass balance" in e for e in report.errors))


if __name__ == "__main__":
    unittest.main()
