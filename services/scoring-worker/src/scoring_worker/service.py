"""Deterministic advisory scoring for lining RUL and quality what-if analysis."""

from __future__ import annotations

from datetime import UTC, datetime
from math import isfinite
from typing import Any, Iterable, Mapping

from .physics_features import extract_thermal_features
from .rul_model import estimate_rul


class ScoringError(ValueError):
    """Raised when a requested score cannot be calculated safely."""


class ScoringWorker:
    """Computes explainable, bounded predictions from synthetic feature snapshots.

    The lining model performs least-squares regression on the refractory-
    thickness time-series, extrapolates time-to-failure to the minimum-safe
    threshold (300 mm), and derives P10/P50/P90 from the standard error of
    the fitted slope (delta-method uncertainty propagation).
    """

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
        # Materialize telemetry so we can iterate twice (features + timestamp)
        telemetry_list = list(telemetry)
        scored_at = self._latest_timestamp(telemetry_list)

        features = extract_thermal_features(telemetry_list, sector)
        if features is None:
            raise ScoringError("Insufficient thermal telemetry for physics regression.")
        if not isfinite(features.thickness_current_mm) or features.thickness_current_mm <= 0:
            raise ScoringError("Lining thickness feature is invalid.")

        rul_result = estimate_rul(features)
        if rul_result is None:
            raise ScoringError("Unable to estimate RUL from current telemetry.")

        return {
            "assetId": asset_id,
            "componentId": component_id,
            "value": rul_result["p50"],
            "unit": "d",
            "confidence": {
                "p10": rul_result["p10"],
                "p50": rul_result["p50"],
                "p90": rul_result["p90"],
            },
            "riskScore": rul_result["riskScore"],
            "riskLevel": rul_result["riskLevel"],
            "estimatedMinimumLiningMm": rul_result["estimatedMinimumLiningMm"],
            "modelVersion": self.lining_model_version,
            "scoredAt": scored_at,
            "drivers": rul_result["drivers"],
            "featureSnapshot": rul_result["featureSnapshot"],
            "sourceRefs": [source_ref],
            "modelConfidence": rul_result["confidence"],
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
