"""Deterministic advisory scoring for lining RUL and quality what-if analysis."""

from __future__ import annotations

from datetime import UTC, datetime
from math import isfinite
from typing import Any, Iterable, Mapping


class ScoringError(ValueError):
    """Raised when a requested score cannot be calculated safely."""


class ScoringWorker:
    """Computes explainable, bounded predictions from synthetic feature snapshots."""

    lining_model_version = "lining-rul-piml:1.3.0-demo"
    quality_model_version = "quality-risk:1.0.0-demo"

    def score_lining(
        self,
        *,
        asset_id: str,
        component_id: str,
        telemetry: Iterable[Mapping[str, Any]],
        source_ref: str,
    ) -> dict[str, Any]:
        sector = component_id.rsplit("-", 1)[-1]
        values = self._latest_by_signal(telemetry, sector)
        thickness = float(values.get("hearth_refractory_estimate", 363.0))
        if not isfinite(thickness) or thickness <= 0:
            raise ScoringError("Lining thickness feature is invalid.")
        minimum_safe = 300.0
        degradation_rate = 3.0 if sector == "07" else 0.02
        p50 = max(0.0, round((thickness - minimum_safe) / degradation_rate, 2))
        p10 = round(max(0.0, p50 * 0.8), 2)
        p90 = round(max(p50, p50 * 1.3095238), 2)
        risk = self._risk_for_rul(p50)
        risk_level = "HIGH" if risk >= 0.8 else "MEDIUM" if risk >= 0.45 else "LOW"
        scored_at = self._latest_timestamp(telemetry)
        inlet = float(values.get("cooling_water_inlet_temperature", 28.0))
        outlet = float(values.get("cooling_water_outlet_temperature", inlet + 8.0))
        flow = float(values.get("cooling_water_flow", 200.0))
        heat_flux = float(values.get("local_heat_flux", 100.0))
        cooling_delta = max(0.0, outlet - inlet)
        # A simple water-side energy proxy keeps the advisory model tied to
        # measurable thermal behavior as well as its monotonic lining state.
        water_heat_proxy = flow * cooling_delta * 1.163 / 10
        thermal_resistance = round(max(0.0, (1180.0 - 150.0) / max(heat_flux, 0.1)), 4)
        drivers = [
            {"name": "heat_flux_6h_slope", "contribution": 0.29},
            {"name": "sector_to_ring_temp_delta", "contribution": 0.24},
            {"name": "cooling_efficiency_residual", "contribution": 0.18},
        ]
        return {
            "assetId": asset_id,
            "componentId": component_id,
            "value": p50,
            "unit": "d",
            "confidence": {"p10": p10, "p50": p50, "p90": p90},
            "riskScore": risk,
            "riskLevel": risk_level,
            "estimatedMinimumLiningMm": minimum_safe,
            "modelVersion": self.lining_model_version,
            "scoredAt": scored_at,
            "drivers": drivers,
            "featureSnapshot": {
                "liningThicknessMm": thickness,
                "coolingDeltaC": round(cooling_delta, 3),
                "coolingFlowM3h": flow,
                "heatFluxKwM2": heat_flux,
                "waterHeatProxyKw": round(water_heat_proxy, 3),
                "apparentThermalResistance": thermal_resistance,
            },
            "sourceRefs": [source_ref],
        }

    def score_quality(self, batch: Mapping[str, Any]) -> dict[str, Any]:
        bias = abs(float(batch.get("coilingTempBiasC", 0.0)))
        status = str(batch.get("resultStatus", "PASS"))
        base_yield = 0.95 if bias < 4 else max(0.88, round(0.95 - bias * 0.004, 3))
        if status == "FAIL":
            base_yield = min(base_yield, 0.88)
        risk = round(min(0.95, max(0.05, 1.0 - base_yield + bias * 0.01)), 3)
        return {
            "value": round(risk, 3),
            "unit": "probability",
            "confidence": {
                "p10": round(max(0.0, risk - 0.08), 3),
                "p50": risk,
                "p90": round(min(1.0, risk + 0.1), 3),
            },
            "modelVersion": self.quality_model_version,
            "scoredAt": str(batch.get("eventTs", self._now())),
            "drivers": [
                {"name": "coiling_temperature_bias_c", "contribution": round(bias / 25, 3)},
                {"name": "carbon_equivalent", "contribution": 0.18},
                {"name": "result_status", "contribution": 0.12 if status == "FAIL" else 0.03},
            ],
            "sourceRefs": [f"batch:{batch.get('batchId', '')}"],
            "predictedFirstPassYield": round(base_yield, 3),
        }

    def quality_what_if(
        self, *, batch: Mapping[str, Any], adjustments: Mapping[str, float]
    ) -> dict[str, Any]:
        allowed = {
            "coilingTempDeltaC": (-20.0, 20.0),
            "forceBalanceDeltaPct": (-10.0, 10.0),
            "carbonEquivalentDeltaPct": (-0.05, 0.05),
        }
        unknown = set(adjustments) - set(allowed)
        if unknown:
            raise ScoringError(f"Unsupported bounded adjustment: {sorted(unknown)[0]}.")
        for name, value in adjustments.items():
            lower, upper = allowed[name]
            number = float(value)
            if not isfinite(number) or not lower <= number <= upper:
                raise ScoringError(f"{name} must be between {lower} and {upper}.")

        current = self.score_quality(batch)
        current_yield = float(current["predictedFirstPassYield"])
        correction = abs(float(adjustments.get("coilingTempDeltaC", 0.0))) * 0.00875
        force_correction = abs(float(adjustments.get("forceBalanceDeltaPct", 0.0))) * 0.002
        proposed_yield = round(min(0.95, current_yield + correction + force_correction), 3)
        return {
            "value": proposed_yield * 100,
            "unit": "%",
            "confidence": {
                "p10": round(max(0.0, proposed_yield * 100 - 3.0), 2),
                "p50": round(proposed_yield * 100, 2),
                "p90": round(min(100.0, proposed_yield * 100 + 2.0), 2),
            },
            "modelVersion": self.quality_model_version,
            "scoredAt": self._now(),
            "drivers": [
                {"name": "coiling_temperature_correction", "contribution": round(correction, 3)},
                {"name": "force_balance_correction", "contribution": round(force_correction, 3)},
            ],
            "sourceRefs": [f"batch:{batch.get('batchId', '')}"],
            "current": {
                "predictedFirstPassYieldPct": round(current_yield * 100, 2),
                "riskScore": current["value"],
            },
            "proposed": {
                "predictedFirstPassYieldPct": round(proposed_yield * 100, 2),
                "adjustments": dict(adjustments),
                "operationalWrite": False,
            },
        }

    @staticmethod
    def _risk_for_rul(rul_days: float) -> float:
        if rul_days <= 30:
            return round(min(0.99, 0.6 + (30 - rul_days) * 0.03), 4)
        return 0.02

    @staticmethod
    def _latest_by_signal(
        telemetry: Iterable[Mapping[str, Any]], sector: str
    ) -> dict[str, float]:
        selected: dict[str, float] = {}
        for row in telemetry:
            payload = row.get("payload", row)
            sensor_id = str(payload.get("sensor_id", payload.get("sensorId", "")))
            if f"H{sector}" not in sensor_id:
                continue
            signal = str(payload.get("signal_code", payload.get("signalCode", "")))
            value = payload.get("value")
            try:
                selected[signal] = float(value)
            except (TypeError, ValueError):
                continue
        return selected

    @staticmethod
    def _latest_timestamp(telemetry: Iterable[Mapping[str, Any]]) -> str:
        values = [
            str(row.get("event_ts", row.get("eventTs", "")))
            for row in telemetry
            if row.get("event_ts", row.get("eventTs"))
        ]
        return max(values) if values else ScoringWorker._now()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")
