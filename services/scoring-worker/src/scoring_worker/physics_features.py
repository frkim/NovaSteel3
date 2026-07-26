"""Physics-informed feature extraction for furnace-lining degradation.

Performs pure-Python least-squares regression on thermal time-series and
extracts slope, fit quality, and health-index features used by the RUL
estimator. No external numerical libraries required.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, Iterable, Mapping


# Physics thresholds for lining state (mm refractory remaining).
DEFAULT_MIN_SAFE_THICKNESS_MM = 300.0
# Healthy baseline for normalized health index computation.
DEFAULT_HEALTHY_THICKNESS_MM = 400.0


@dataclass(frozen=True)
class LinearFit:
    """Result of an ordinary-least-squares linear fit."""

    slope: float
    intercept: float
    r_squared: float
    residual_std_err: float
    n_points: int


def linear_fit(xs: list[float], ys: list[float]) -> LinearFit:
    """Pure-Python OLS linear regression returning slope, intercept, r², and
    the standard error of the slope estimate."""
    n = len(xs)
    if n != len(ys):
        raise ValueError("xs and ys must be the same length")
    if n < 2:
        return LinearFit(
            slope=0.0,
            intercept=ys[0] if ys else 0.0,
            r_squared=0.0,
            residual_std_err=0.0,
            n_points=n,
        )
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    ss_xx = sum((x - x_mean) ** 2 for x in xs)
    if ss_xx == 0.0:
        return LinearFit(slope=0.0, intercept=y_mean, r_squared=0.0, residual_std_err=0.0, n_points=n)
    ss_xy = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r_squared = 1.0 if ss_tot == 0.0 else max(0.0, min(1.0, 1.0 - ss_res / ss_tot))
    # Standard error of slope: se(b) = sqrt(ss_res / (n-2)) / sqrt(ss_xx)
    if n > 2 and ss_xx > 0.0:
        residual_variance = ss_res / (n - 2)
        residual_std_err = sqrt(residual_variance / ss_xx)
    else:
        residual_std_err = 0.0
    return LinearFit(
        slope=slope,
        intercept=intercept,
        r_squared=r_squared,
        residual_std_err=residual_std_err,
        n_points=n,
    )


@dataclass(frozen=True)
class ThermalFeatures:
    """Extracted physics features from a telemetry observation window."""

    window_span_days: float
    n_observations: int
    # Refractory thickness regression
    thickness_current_mm: float
    thickness_slope_mm_per_day: float
    thickness_r_squared: float
    thickness_slope_std_err: float
    # Heat flux trend (corroborating signal)
    heat_flux_current: float
    heat_flux_slope_per_day: float
    heat_flux_r_squared: float
    # Cooling efficiency
    cooling_delta_c: float
    cooling_flow_m3h: float
    water_heat_proxy_kw: float
    apparent_thermal_resistance: float
    # Normalized health index (1 = healthy, 0 = at threshold)
    normalized_health_index: float


def _parse_iso_to_days(ts_str: str, reference: str) -> float:
    """Convert ISO timestamp string to fractional days since reference."""
    # Parse simplified ISO 8601 (YYYY-MM-DDTHH:MM:SS.sssZ)
    from datetime import datetime, timezone

    def _parse(s: str) -> datetime:
        s = s.replace("Z", "+00:00")
        # Handle various ISO formats
        if "." in s:
            # Has fractional seconds
            return datetime.fromisoformat(s)
        return datetime.fromisoformat(s)

    ref_dt = _parse(reference)
    cur_dt = _parse(ts_str)
    delta = (cur_dt - ref_dt).total_seconds()
    return delta / 86_400.0


def extract_thermal_features(
    telemetry: Iterable[Mapping[str, Any]],
    sector: str,
    *,
    min_safe_thickness_mm: float = DEFAULT_MIN_SAFE_THICKNESS_MM,
    healthy_thickness_mm: float = DEFAULT_HEALTHY_THICKNESS_MM,
) -> ThermalFeatures | None:
    """Extract time-series features from raw Project B telemetry for a sector.

    Groups readings by timestamp, fits linear regressions on refractory
    thickness and heat flux, and computes corroborating thermal features.
    Returns None if insufficient data is available.
    """
    # Collect time-series per signal for the target sector
    thickness_series: list[tuple[str, float]] = []  # (timestamp, value)
    heat_flux_series: list[tuple[str, float]] = []
    latest_signals: dict[str, float] = {}
    latest_ts: str = ""

    for row in telemetry:
        payload = row.get("payload", row)
        sensor_id = str(payload.get("sensor_id", payload.get("sensorId", "")))
        if f"H{sector}" not in sensor_id:
            continue
        signal = str(payload.get("signal_code", payload.get("signalCode", "")))
        value = payload.get("value")
        try:
            val = float(value)
        except (TypeError, ValueError):
            continue
        ts = str(row.get("event_ts", row.get("eventTs", "")))
        if ts > latest_ts:
            latest_ts = ts
        latest_signals[signal] = val

        if signal == "hearth_refractory_estimate":
            thickness_series.append((ts, val))
        elif signal == "local_heat_flux":
            heat_flux_series.append((ts, val))

    if len(thickness_series) < 3:
        return None

    # Sort by timestamp
    thickness_series.sort(key=lambda t: t[0])
    heat_flux_series.sort(key=lambda t: t[0])

    # Build day-offset x-axis relative to first observation
    ref_ts = thickness_series[0][0]
    thickness_xs = [_parse_iso_to_days(ts, ref_ts) for ts, _ in thickness_series]
    thickness_ys = [val for _, val in thickness_series]

    thickness_fit = linear_fit(thickness_xs, thickness_ys)

    # Heat flux regression (corroborating signal)
    if len(heat_flux_series) >= 3:
        hf_ref = heat_flux_series[0][0]
        hf_xs = [_parse_iso_to_days(ts, hf_ref) for ts, _ in heat_flux_series]
        hf_ys = [val for _, val in heat_flux_series]
        hf_fit = linear_fit(hf_xs, hf_ys)
    else:
        hf_fit = LinearFit(0.0, 0.0, 0.0, 0.0, 0)

    # Current values (most recent observation)
    current_thickness = thickness_ys[-1]
    current_heat_flux = float(latest_signals.get("local_heat_flux", 0.0))
    inlet = float(latest_signals.get("cooling_water_inlet_temperature", 28.0))
    outlet = float(latest_signals.get("cooling_water_outlet_temperature", inlet + 8.0))
    flow = float(latest_signals.get("cooling_water_flow", 200.0))
    cooling_delta = max(0.0, outlet - inlet)
    water_heat_proxy = flow * cooling_delta * 1.163 / 10
    thermal_resistance = max(0.0, (1180.0 - 150.0) / max(current_heat_flux, 0.1))

    # Normalized health index
    span = max(healthy_thickness_mm - min_safe_thickness_mm, 1.0)
    health_index = (current_thickness - min_safe_thickness_mm) / span
    health_index = max(0.0, min(1.0, health_index))

    window_span = thickness_xs[-1] - thickness_xs[0] if len(thickness_xs) > 1 else 0.0

    return ThermalFeatures(
        window_span_days=window_span,
        n_observations=len(thickness_series),
        thickness_current_mm=current_thickness,
        thickness_slope_mm_per_day=thickness_fit.slope,
        thickness_r_squared=thickness_fit.r_squared,
        thickness_slope_std_err=thickness_fit.residual_std_err,
        heat_flux_current=current_heat_flux,
        heat_flux_slope_per_day=hf_fit.slope,
        heat_flux_r_squared=hf_fit.r_squared,
        cooling_delta_c=cooling_delta,
        cooling_flow_m3h=flow,
        water_heat_proxy_kw=water_heat_proxy,
        apparent_thermal_resistance=round(thermal_resistance, 4),
        normalized_health_index=health_index,
    )
