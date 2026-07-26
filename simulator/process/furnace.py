"""Blast furnace hearth-lining physics model (docs section 8.1, 9.1, 9.2).

The *process state* (hidden truth) is generated first; sensors only ever
*observe* it (docs section 6.2), so telemetry values are never sampled
independently of one another. This module implements the analytic hidden
state for one hearth sector: effective refractory thickness ``L``,
inner/shell temperature, cooling boundary, and the conductive heat-flux
relation ``q = k * (T_i - T_s) / L``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

WATER_DENSITY_KG_M3 = 1000.0
WATER_CP_KJ_PER_KGK = 4.186
COOLING_AREA_M2 = 3.0  # per hearth-sector cooling circuit, synthetic constant
THERMAL_CONDUCTIVITY_K = 1.9  # W/m.K, synthetic refractory constant


@dataclass
class LiningState:
    thickness_mm: float
    inner_temp_c: float
    shell_temp_c: float
    cooling_inlet_c: float
    cooling_outlet_c: float
    cooling_flow_m3h: float
    heat_flux_kw_m2: float


def hidden_thickness_mm(*, thickness_at_eval_mm: float, degradation_rate_mm_per_day: float,
                         hours_before_eval: float) -> float:
    """Monotonic non-increasing thickness trajectory.

    ``thickness_at_eval_mm`` is the true thickness at the scenario's
    evaluation timestamp (the most recent sample). Earlier samples are
    *higher* by ``degradation_rate_mm_per_day`` times elapsed days, which
    guarantees the series never increases and never steps discontinuously.
    """
    days_before_eval = max(hours_before_eval, 0.0) / 24.0
    return thickness_at_eval_mm + degradation_rate_mm_per_day * days_before_eval


def remaining_useful_life_days(thickness_mm: float, min_safe_thickness_mm: float,
                                degradation_rate_mm_per_day: float) -> float:
    """RUL (days) until hidden thickness reaches the minimum safe value.

    Never negative; a rate of zero (or below) is treated as "very long" life
    rather than divide-by-zero/negative RUL.
    """
    remaining_mm = max(thickness_mm - min_safe_thickness_mm, 0.0)
    if degradation_rate_mm_per_day <= 1e-9:
        return 3650.0
    return remaining_mm / degradation_rate_mm_per_day


def rul_confidence_band(rul_p50_days: float) -> tuple[float, float]:
    """P10/P90 band calibrated so a 21-day P50 reproduces the worked
    example in docs section 4.4 (16.8 / 21.0 / 27.5)."""
    p10 = round(rul_p50_days * 0.8, 1)
    p90 = round(rul_p50_days * (27.5 / 21.0), 1)
    return p10, p90


def risk_score(rul_p50_days: float) -> float:
    """Risk score decreasing with RUL, calibrated to 0.87 at RUL=21 days
    (docs section 4.4 worked example)."""
    raw = 1.32 - 0.0214 * rul_p50_days
    return round(min(max(raw, 0.02), 0.99), 4)


def severity_for_rul(rul_p50_days: float) -> str:
    if rul_p50_days <= 21:
        return "HIGH"
    if rul_p50_days <= 45:
        return "MEDIUM"
    return "LOW"


def sector_shell_excursion_c(*, elapsed_fraction: float, target_delta_c: float,
                              rng) -> float:
    """Localized shell-temperature rise for the degraded sector.

    Intermittent 2-5 degC excursions during the first 30% of the window,
    then a sustained ramp toward ``target_delta_c`` (docs section 8.1).
    """
    if elapsed_fraction < 0.30:
        bump = (2.0 + 3.0 * abs(math.sin(elapsed_fraction * 40.0))) * rng.uniform(0.6, 1.0)
        return bump if rng.random() < 0.35 else 0.0
    ramp_fraction = (elapsed_fraction - 0.30) / 0.70
    return target_delta_c * min(ramp_fraction, 1.0)


def cooling_delta_t(*, base_delta_t_c: float, excursion_c: float,
                     efficiency_loss_fraction: float) -> float:
    """Cooling-water outlet-minus-inlet temperature.

    Degradation reduces cooling efficiency, so a larger fraction of the
    extra heat shows up as delta-T rather than being carried away, which is
    exactly the "reduced cooling-efficiency residual" signature in section
    8.1.
    """
    return base_delta_t_c + excursion_c * (1.0 + efficiency_loss_fraction)


def heat_flux_kw_m2(*, flow_m3h: float, delta_t_c: float) -> float:
    """Heat flux derived from water mass flow, heat capacity, and cooling
    ΔT (docs section 9.2 physics-informed feature), not sampled
    independently of flow/ΔT."""
    mass_flow_kg_s = flow_m3h * WATER_DENSITY_KG_M3 / 3600.0
    power_kw = mass_flow_kg_s * WATER_CP_KJ_PER_KGK * delta_t_c
    return power_kw / COOLING_AREA_M2


def apparent_thermal_resistance(inner_temp_c: float, shell_temp_c: float,
                                 heat_flux: float) -> float:
    if heat_flux <= 1e-9:
        return float("nan")
    return (inner_temp_c - shell_temp_c) / heat_flux


def conductive_heat_flux_check(thickness_mm: float, inner_temp_c: float,
                                shell_temp_c: float,
                                k: float = THERMAL_CONDUCTIVITY_K) -> float:
    """``q = k * (T_i - T_s) / L`` in kW/m^2 (L in metres)."""
    thickness_m = thickness_mm / 1000.0
    if thickness_m <= 1e-9:
        return float("nan")
    q_w_m2 = k * (inner_temp_c - shell_temp_c) / thickness_m
    return q_w_m2 / 1000.0
