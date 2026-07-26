"""Tests for the MILP solver, physics-derived CO₂, and Strategy fallback."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from optimizer_worker import EnergyDispatchOptimizer


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "services" / "bff-api" / "fixtures" / "demo-full"


def _records(name: str) -> list[dict]:
    return [
        json.loads(line)
        for line in (FIXTURE / f"{name}.ndjson").read_text(encoding="utf-8").splitlines()
    ]


def _simulate_default() -> dict:
    return EnergyDispatchOptimizer().simulate(
        site="NS-DEMO-LUX-01",
        horizon_hours=24,
        scenario="evening-scarcity",
        energy_intervals=_records("energy_interval"),
        batches=_records("heat_batch"),
        constraints={},
    )


class TestMILPProducesFeasibleSchedule:
    """MILP produces a feasible zero-violation schedule."""

    def test_milp_solver_is_used(self) -> None:
        result = _simulate_default()
        assert result["solver"] == "MILP_CBC"

    def test_zero_hard_constraint_violations(self) -> None:
        result = _simulate_default()
        assert result["hardConstraintViolations"] == 0

    def test_all_constraints_satisfied(self) -> None:
        result = _simulate_default()
        for constraint in result["constraintReport"]:
            assert constraint["status"] == "SATISFIED"

    def test_equal_tonnage_preserved(self) -> None:
        result = _simulate_default()
        assert result["baseline"]["tonnage"] == result["optimized"]["tonnage"]

    def test_urgent_batches_stay_fixed(self) -> None:
        result = _simulate_default()
        for row in result["optimized"]["schedule"]:
            if row["urgent"]:
                assert row["shiftMinutes"] == 0

    def test_max_hold_time_respected(self) -> None:
        result = _simulate_default()
        for row in result["optimized"]["schedule"]:
            assert row["holdMinutes"] <= 180  # default maxHoldMinutes


class TestCO2TracesToCarbonIntensity:
    """CO₂ figures are traceable to per-slot carbon intensity (whole-dispatch basis)."""

    def test_co2_pct_is_physics_derived(self) -> None:
        result = _simulate_default()
        co2_pct = result["savings"]["co2Pct"]
        assert co2_pct > 0
        # Verify it equals (baseline - optimized) / baseline * 100
        co2_baseline = result["savings"]["co2KgBaseline"]
        co2_optimized = result["savings"]["co2KgOptimized"]
        expected = round((co2_baseline - co2_optimized) / co2_baseline * 100, 2)
        assert co2_pct == expected

    def test_co2_kg_values_are_positive(self) -> None:
        result = _simulate_default()
        assert result["savings"]["co2KgBaseline"] > 0
        assert result["savings"]["co2KgOptimized"] > 0
        assert result["savings"]["co2KgOptimized"] < result["savings"]["co2KgBaseline"]

    def test_co2_and_cost_use_same_whole_dispatch_basis(self) -> None:
        """CO₂ pct must be on whole-dispatch basis (diluted by fixed load), same as cost."""
        result = _simulate_default()
        # The flexible-only CO₂ saving is larger than the whole-dispatch figure.
        assert result["savings"]["rawFlexibleCo2Pct"] > result["savings"]["co2Pct"]
        # Same relationship holds for cost: flexible-only > whole-dispatch.
        assert result["savings"]["rawFlexibleCostPct"] > result["savings"]["costPct"]

    def test_flexible_co2_field_exposed(self) -> None:
        result = _simulate_default()
        assert "rawFlexibleCo2Pct" in result["savings"]
        assert result["savings"]["rawFlexibleCo2Pct"] > 0


class TestPeakIsDispatchAttributable:
    """Peak figures are derived from the optimizer's own load profile."""

    def test_peak_matches_reported_figures(self) -> None:
        result = _simulate_default()
        peak_pct = result["savings"]["peakPct"]
        baseline_peak = result["baseline"]["peakDemandMw"]
        optimized_peak = result["optimized"]["peakDemandMw"]
        expected_reduction = (baseline_peak - optimized_peak) / baseline_peak
        assert abs(peak_pct - (-expected_reduction * 100)) < 0.01

    def test_peak_changes_when_schedule_changes(self) -> None:
        """Different constraints produce different schedules → different peakPct."""
        result_default = _simulate_default()
        # With maxShiftMinutes=0, all batches stay put → schedule == baseline.
        result_no_shift = EnergyDispatchOptimizer().simulate(
            site="NS-DEMO-LUX-01",
            horizon_hours=24,
            scenario="evening-scarcity",
            energy_intervals=_records("energy_interval"),
            batches=_records("heat_batch"),
            constraints={"maxShiftMinutes": 0},
        )
        # The MILP with shift freedom should produce a different peak than no-shift.
        assert result_default["savings"]["peakPct"] != result_no_shift["savings"]["peakPct"]

    def test_peak_is_zero_when_no_shift_allowed(self) -> None:
        """When batches cannot move, baseline == optimized → peakPct == 0."""
        result = EnergyDispatchOptimizer().simulate(
            site="NS-DEMO-LUX-01",
            horizon_hours=24,
            scenario="evening-scarcity",
            energy_intervals=_records("energy_interval"),
            batches=_records("heat_batch"),
            constraints={"maxShiftMinutes": 0},
        )
        assert result["savings"]["peakPct"] == 0.0
        assert result["baseline"]["peakDemandMw"] == result["optimized"]["peakDemandMw"]


class TestHeuristicFallback:
    """Heuristic fallback triggers when PuLP is missing."""

    def test_fallback_when_pulp_import_fails(self, caplog: pytest.LogCaptureFixture) -> None:
        with patch.dict("sys.modules", {"pulp": None}):
            with caplog.at_level(logging.WARNING):
                result = EnergyDispatchOptimizer().simulate(
                    site="NS-DEMO-LUX-01",
                    horizon_hours=24,
                    scenario="evening-scarcity",
                    energy_intervals=_records("energy_interval"),
                    batches=_records("heat_batch"),
                    constraints={},
                )
        assert result["solver"] == "DETERMINISTIC_HEURISTIC"
        assert result["hardConstraintViolations"] == 0
        assert result["baseline"]["tonnage"] == result["optimized"]["tonnage"]
        assert any("falling back to heuristic" in msg for msg in caplog.messages)

    def test_fallback_still_satisfies_constraints(self, caplog: pytest.LogCaptureFixture) -> None:
        with patch.dict("sys.modules", {"pulp": None}):
            with caplog.at_level(logging.WARNING):
                result = EnergyDispatchOptimizer().simulate(
                    site="NS-DEMO-LUX-01",
                    horizon_hours=24,
                    scenario="evening-scarcity",
                    energy_intervals=_records("energy_interval"),
                    batches=_records("heat_batch"),
                    constraints={},
                )
        for constraint in result["constraintReport"]:
            assert constraint["status"] == "SATISFIED"


class TestDeterminism:
    """The optimizer produces byte-for-byte reproducible results."""

    def test_milp_determinism_across_runs(self) -> None:
        first = _simulate_default()
        second = _simulate_default()
        assert first == second

    def test_heuristic_determinism_across_runs(self) -> None:
        with patch.dict("sys.modules", {"pulp": None}):
            first = EnergyDispatchOptimizer().simulate(
                site="NS-DEMO-LUX-01",
                horizon_hours=24,
                scenario="evening-scarcity",
                energy_intervals=_records("energy_interval"),
                batches=_records("heat_batch"),
                constraints={},
            )
        with patch.dict("sys.modules", {"pulp": None}):
            second = EnergyDispatchOptimizer().simulate(
                site="NS-DEMO-LUX-01",
                horizon_hours=24,
                scenario="evening-scarcity",
                energy_intervals=_records("energy_interval"),
                batches=_records("heat_batch"),
                constraints={},
            )
        assert first == second


class TestResponseContractPreserved:
    """Existing JSON response shape is unchanged (additive fields only)."""

    REQUIRED_KEYS = {
        "recommendationId", "version", "status", "modelVersion",
        "site", "scenario", "baseline", "optimized",
        "constraintReport", "hardConstraintViolations", "savings",
    }
    REQUIRED_SAVINGS_KEYS = {"costPct", "costEur", "peakPct", "co2Pct", "rawFlexibleCostPct"}
    REQUIRED_SCHEDULE_KEYS = {
        "costEur", "flexibleCostEur", "fixedLoadCostEur",
        "peakDemandMw", "tonnage", "schedule",
    }

    def test_top_level_keys_present(self) -> None:
        result = _simulate_default()
        assert self.REQUIRED_KEYS.issubset(result.keys())

    def test_savings_keys_present(self) -> None:
        result = _simulate_default()
        assert self.REQUIRED_SAVINGS_KEYS.issubset(result["savings"].keys())

    def test_baseline_and_optimized_keys_present(self) -> None:
        result = _simulate_default()
        assert self.REQUIRED_SCHEDULE_KEYS.issubset(result["baseline"].keys())
        assert self.REQUIRED_SCHEDULE_KEYS.issubset(result["optimized"].keys())

    def test_additive_solver_field_present(self) -> None:
        result = _simulate_default()
        assert "solver" in result
        assert result["solver"] in ("MILP_CBC", "DETERMINISTIC_HEURISTIC")
