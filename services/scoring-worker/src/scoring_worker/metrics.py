"""Business KPI metric emission for the scoring (RUL + quality) path.

Emits:
  - novasteel.rul.days_p50          (predicted remaining useful life)
  - novasteel.rul.confidence        (model confidence score)
  - novasteel.quality.high_grade_yield_pct (predicted first-pass yield)

These are side-effect-free observations recorded after the scoring worker
produces results. They do not alter computed values or API responses.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from . import telemetry

logger = logging.getLogger(__name__)


def record_rul_metrics(result: Mapping[str, Any]) -> None:
    """Record RUL KPI metrics from a lining score result.

    Called after the scorer produces a result. No-op when telemetry
    is inactive (offline/demo mode).
    """
    meter = telemetry.get_meter()
    if meter is None:
        return

    try:
        p50 = result.get("value")  # RUL P50 in days
        if p50 is not None:
            gauge = meter.create_gauge(
                "novasteel.rul.days_p50",
                unit="d",
                description="Predicted remaining useful life (P50) in days",
            )
            gauge.set(float(p50), {"asset_id": result.get("assetId", "unknown")})

        confidence = result.get("modelConfidence")
        if confidence is not None:
            conf_gauge = meter.create_gauge(
                "novasteel.rul.confidence",
                unit="1",
                description="RUL model confidence score (0-1)",
            )
            conf_gauge.set(
                float(confidence), {"asset_id": result.get("assetId", "unknown")}
            )

    except Exception as exc:
        logger.debug("Failed to record RUL metrics: %s", exc)


def record_quality_metrics(result: Mapping[str, Any]) -> None:
    """Record quality KPI metrics from a quality score result.

    Called after the scorer produces a quality result. No-op when
    telemetry is inactive (offline/demo mode).
    """
    meter = telemetry.get_meter()
    if meter is None:
        return

    try:
        yield_pct = result.get("predictedFirstPassYield")
        if yield_pct is not None:
            gauge = meter.create_gauge(
                "novasteel.quality.high_grade_yield_pct",
                unit="%",
                description="Predicted first-pass high-grade yield percentage",
            )
            gauge.set(float(yield_pct) * 100.0, {})

    except Exception as exc:
        logger.debug("Failed to record quality metrics: %s", exc)
