"""Physics-informed RUL model tests.

Tests cover: monotonicity (steeper slope → shorter RUL), residual-derived
uncertainty bands, determinism, and confidence vs. fit quality.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from scoring_worker import ScoringWorker
from scoring_worker.physics_features import (
    LinearFit,
    ThermalFeatures,
    extract_thermal_features,
    linear_fit,
)
from scoring_worker.rul_model import confidence_score, estimate_rul, risk_for_rul


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "services" / "bff-api" / "fixtures" / "demo-full"


def _records() -> list[dict]:
    return [
        json.loads(line)
        for line in (FIXTURE / "telemetry.ndjson").read_text(encoding="utf-8").splitlines()
    ]


# --- Linear regression tests ---


class TestLinearFit:
    def test_perfect_fit(self) -> None:
        xs = [0.0, 1.0, 2.0, 3.0, 4.0]
        ys = [10.0, 8.0, 6.0, 4.0, 2.0]
        fit = linear_fit(xs, ys)
        assert fit.slope == pytest.approx(-2.0, abs=1e-10)
        assert fit.intercept == pytest.approx(10.0, abs=1e-10)
        assert fit.r_squared == pytest.approx(1.0, abs=1e-10)
        assert fit.residual_std_err == pytest.approx(0.0, abs=1e-10)

    def test_noisy_fit_has_nonzero_std_err(self) -> None:
        xs = [0.0, 1.0, 2.0, 3.0, 4.0]
        ys = [10.0, 8.5, 5.5, 4.0, 2.0]
        fit = linear_fit(xs, ys)
        assert fit.slope < 0
        assert 0.0 < fit.r_squared < 1.0
        assert fit.residual_std_err > 0.0

    def test_single_point(self) -> None:
        fit = linear_fit([1.0], [5.0])
        assert fit.slope == 0.0
        assert fit.intercept == 5.0


# --- Monotonicity: steeper slope → shorter RUL ---


class TestMonotonicity:
    def test_steeper_slope_gives_shorter_rul(self) -> None:
        """A steeper decline in thickness must produce a shorter RUL."""
        base = ThermalFeatures(
            window_span_days=1.0,
            n_observations=50,
            thickness_current_mm=363.0,
            thickness_slope_mm_per_day=-3.0,
            thickness_r_squared=0.9,
            thickness_slope_std_err=0.1,
            heat_flux_current=1000.0,
            heat_flux_slope_per_day=500.0,
            heat_flux_r_squared=0.8,
            cooling_delta_c=8.0,
            cooling_flow_m3h=200.0,
            water_heat_proxy_kw=93.0,
            apparent_thermal_resistance=0.5,
            normalized_health_index=0.63,
        )
        steep = ThermalFeatures(
            window_span_days=1.0,
            n_observations=50,
            thickness_current_mm=363.0,
            thickness_slope_mm_per_day=-6.0,
            thickness_r_squared=0.9,
            thickness_slope_std_err=0.1,
            heat_flux_current=1000.0,
            heat_flux_slope_per_day=500.0,
            heat_flux_r_squared=0.8,
            cooling_delta_c=8.0,
            cooling_flow_m3h=200.0,
            water_heat_proxy_kw=93.0,
            apparent_thermal_resistance=0.5,
            normalized_health_index=0.63,
        )
        result_base = estimate_rul(base)
        result_steep = estimate_rul(steep)
        assert result_base is not None and result_steep is not None
        assert result_steep["p50"] < result_base["p50"]

    def test_thinner_lining_gives_shorter_rul(self) -> None:
        """Less remaining material → shorter RUL (same wear rate)."""
        thick = ThermalFeatures(
            window_span_days=1.0, n_observations=50,
            thickness_current_mm=380.0, thickness_slope_mm_per_day=-3.0,
            thickness_r_squared=0.9, thickness_slope_std_err=0.1,
            heat_flux_current=800.0, heat_flux_slope_per_day=200.0,
            heat_flux_r_squared=0.8, cooling_delta_c=8.0,
            cooling_flow_m3h=200.0, water_heat_proxy_kw=93.0,
            apparent_thermal_resistance=0.5, normalized_health_index=0.8,
        )
        thin = ThermalFeatures(
            window_span_days=1.0, n_observations=50,
            thickness_current_mm=320.0, thickness_slope_mm_per_day=-3.0,
            thickness_r_squared=0.9, thickness_slope_std_err=0.1,
            heat_flux_current=2000.0, heat_flux_slope_per_day=200.0,
            heat_flux_r_squared=0.8, cooling_delta_c=8.0,
            cooling_flow_m3h=200.0, water_heat_proxy_kw=93.0,
            apparent_thermal_resistance=0.3, normalized_health_index=0.2,
        )
        r_thick = estimate_rul(thick)
        r_thin = estimate_rul(thin)
        assert r_thick is not None and r_thin is not None
        assert r_thin["p50"] < r_thick["p50"]


# --- Uncertainty band from residuals ---


class TestUncertaintyBand:
    def test_p10_lt_p50_lt_p90(self) -> None:
        """Residual-derived bands must maintain P10 < P50 < P90."""
        features = ThermalFeatures(
            window_span_days=1.0, n_observations=50,
            thickness_current_mm=363.0, thickness_slope_mm_per_day=-3.0,
            thickness_r_squared=0.85, thickness_slope_std_err=0.2,
            heat_flux_current=1000.0, heat_flux_slope_per_day=500.0,
            heat_flux_r_squared=0.8, cooling_delta_c=8.0,
            cooling_flow_m3h=200.0, water_heat_proxy_kw=93.0,
            apparent_thermal_resistance=0.5, normalized_health_index=0.63,
        )
        result = estimate_rul(features)
        assert result is not None
        assert result["p10"] < result["p50"] < result["p90"]

    def test_wider_band_with_worse_fit(self) -> None:
        """Larger slope standard error → wider P10-P90 band."""
        good_fit = ThermalFeatures(
            window_span_days=1.0, n_observations=50,
            thickness_current_mm=363.0, thickness_slope_mm_per_day=-3.0,
            thickness_r_squared=0.95, thickness_slope_std_err=0.05,
            heat_flux_current=1000.0, heat_flux_slope_per_day=500.0,
            heat_flux_r_squared=0.8, cooling_delta_c=8.0,
            cooling_flow_m3h=200.0, water_heat_proxy_kw=93.0,
            apparent_thermal_resistance=0.5, normalized_health_index=0.63,
        )
        bad_fit = ThermalFeatures(
            window_span_days=1.0, n_observations=50,
            thickness_current_mm=363.0, thickness_slope_mm_per_day=-3.0,
            thickness_r_squared=0.5, thickness_slope_std_err=0.8,
            heat_flux_current=1000.0, heat_flux_slope_per_day=500.0,
            heat_flux_r_squared=0.8, cooling_delta_c=8.0,
            cooling_flow_m3h=200.0, water_heat_proxy_kw=93.0,
            apparent_thermal_resistance=0.5, normalized_health_index=0.63,
        )
        r_good = estimate_rul(good_fit)
        r_bad = estimate_rul(bad_fit)
        assert r_good is not None and r_bad is not None
        band_good = r_good["p90"] - r_good["p10"]
        band_bad = r_bad["p90"] - r_bad["p10"]
        assert band_bad > band_good


# --- Determinism ---


class TestDeterminism:
    def test_identical_input_produces_identical_output(self) -> None:
        """Two runs with identical telemetry must produce byte-identical results."""
        worker = ScoringWorker()
        telemetry = _records()
        kwargs = dict(
            asset_id="LUX-BF-01",
            component_id="HEARTH-SECTOR-07",
            telemetry=telemetry,
            source_ref="simulator:test",
        )
        first = worker.score_lining(**kwargs)
        second = worker.score_lining(**kwargs)
        assert first == second

    def test_model_version_stable(self) -> None:
        worker = ScoringWorker()
        result = worker.score_lining(
            asset_id="LUX-BF-01",
            component_id="HEARTH-SECTOR-07",
            telemetry=_records(),
            source_ref="simulator:test",
        )
        assert result["modelVersion"] == "lining-rul-piml:1.3.0-demo"


# --- Confidence rises with r² ---


class TestConfidence:
    def test_higher_r_squared_gives_higher_confidence(self) -> None:
        low_r2 = ThermalFeatures(
            window_span_days=1.0, n_observations=50,
            thickness_current_mm=363.0, thickness_slope_mm_per_day=-3.0,
            thickness_r_squared=0.3, thickness_slope_std_err=0.5,
            heat_flux_current=1000.0, heat_flux_slope_per_day=500.0,
            heat_flux_r_squared=0.3, cooling_delta_c=8.0,
            cooling_flow_m3h=200.0, water_heat_proxy_kw=93.0,
            apparent_thermal_resistance=0.5, normalized_health_index=0.63,
        )
        high_r2 = ThermalFeatures(
            window_span_days=1.0, n_observations=50,
            thickness_current_mm=363.0, thickness_slope_mm_per_day=-3.0,
            thickness_r_squared=0.95, thickness_slope_std_err=0.05,
            heat_flux_current=1000.0, heat_flux_slope_per_day=500.0,
            heat_flux_r_squared=0.95, cooling_delta_c=8.0,
            cooling_flow_m3h=200.0, water_heat_proxy_kw=93.0,
            apparent_thermal_resistance=0.5, normalized_health_index=0.63,
        )
        assert confidence_score(high_r2) > confidence_score(low_r2)


# --- Integration with fixture data ---


class TestFixtureIntegration:
    def test_demo_fixture_produces_actionable_rul(self) -> None:
        """The demo fixture must produce a plausible RUL in the 15-25 day range."""
        worker = ScoringWorker()
        result = worker.score_lining(
            asset_id="LUX-BF-01",
            component_id="HEARTH-SECTOR-07",
            telemetry=_records(),
            source_ref="simulator:test",
        )
        assert 15.0 <= result["value"] <= 25.0
        assert result["riskLevel"] == "HIGH"
        assert result["confidence"]["p10"] < result["value"] < result["confidence"]["p90"]

    def test_response_contract_keys_present(self) -> None:
        """Verify the response shape has all required keys."""
        worker = ScoringWorker()
        result = worker.score_lining(
            asset_id="LUX-BF-01",
            component_id="HEARTH-SECTOR-07",
            telemetry=_records(),
            source_ref="simulator:test",
        )
        required_keys = {
            "assetId", "componentId", "value", "unit", "confidence",
            "riskScore", "riskLevel", "estimatedMinimumLiningMm",
            "modelVersion", "scoredAt", "drivers", "featureSnapshot", "sourceRefs",
        }
        assert required_keys.issubset(result.keys())
        assert {"p10", "p50", "p90"} == set(result["confidence"].keys())

    def test_changing_thermal_trace_changes_output(self) -> None:
        """Modified input must produce different RUL (key acceptance criterion)."""
        worker = ScoringWorker()
        original = _records()
        modified = deepcopy(original)
        for r in modified:
            if (r.get("payload", {}).get("signal_code") == "hearth_refractory_estimate"
                    and "H07" in r.get("payload", {}).get("sensor_id", "")):
                r["payload"]["value"] -= 10.0

        r_original = worker.score_lining(
            asset_id="LUX-BF-01", component_id="HEARTH-SECTOR-07",
            telemetry=original, source_ref="simulator:test",
        )
        r_modified = worker.score_lining(
            asset_id="LUX-BF-01", component_id="HEARTH-SECTOR-07",
            telemetry=modified, source_ref="simulator:test",
        )
        assert r_original["value"] != r_modified["value"]


# --- Risk function ---


class TestRiskFunction:
    def test_risk_monotonically_decreases_with_rul(self) -> None:
        risks = [risk_for_rul(d) for d in range(0, 100, 5)]
        for i in range(1, len(risks)):
            assert risks[i] <= risks[i - 1]

    def test_risk_high_for_short_rul(self) -> None:
        assert risk_for_rul(20.0) >= 0.8

    def test_risk_low_for_long_rul(self) -> None:
        assert risk_for_rul(60.0) < 0.45
