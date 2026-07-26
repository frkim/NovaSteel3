"""Business KPI metric emission for the energy dispatch path.

Emits:
  - novasteel.energy.kwh_per_tonne  (from dispatch result)
  - novasteel.emissions.co2_kg      (whole-dispatch CO₂ in kg)

These are side-effect-free observations recorded after the optimizer
produces a result. They do not alter computed values or API responses.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from . import telemetry

logger = logging.getLogger(__name__)


def record_dispatch_metrics(result: Mapping[str, Any]) -> None:
    """Record energy KPI metrics from an optimization result.

    Called after the optimizer produces a result. No-op when telemetry
    is inactive (offline/demo mode).
    """
    meter = telemetry.get_meter()
    if meter is None:
        return

    try:
        # Energy intensity: total MWh from optimized schedule / total tonnage
        optimized = result.get("optimized", {})
        schedule = optimized.get("schedule", [])
        total_mwh = sum(row.get("energyMwh", 0.0) for row in schedule)
        total_tonnage = optimized.get("tonnage", 0.0)

        if total_tonnage > 0:
            kwh_per_tonne = (total_mwh * 1000.0) / total_tonnage
            gauge = meter.create_gauge(
                "novasteel.energy.kwh_per_tonne",
                unit="kWh/t",
                description="Energy intensity of optimized dispatch schedule",
            )
            gauge.set(kwh_per_tonne, {"site": result.get("site", "unknown")})

        # CO₂: whole-dispatch basis (co2KgOptimized from the savings block)
        savings = result.get("savings", {})
        co2_kg = savings.get("co2KgOptimized")
        if co2_kg is not None:
            co2_gauge = meter.create_gauge(
                "novasteel.emissions.co2_kg",
                unit="kg",
                description="Whole-dispatch CO₂ emissions (optimized schedule)",
            )
            co2_gauge.set(float(co2_kg), {"site": result.get("site", "unknown")})

    except Exception as exc:
        logger.debug("Failed to record dispatch metrics: %s", exc)
