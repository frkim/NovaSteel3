"""Sensor status, trend, and deviation derivation for the device simulator.

All functions are pure (no side effects) and operate on lists of recent sample
values or a single current reading together with catalog range bounds.

See ``docs/data/synthetic-data-and-simulators.md`` section 6 and the frozen
response shapes in ``views.py``.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone


_APPROACH_BAND_PCT = 0.05
_EXCEEDANCE_BAND_PCT = 0.05
_TREND_WINDOW = 10
_TREND_EPSILON = 1e-4


def sensor_status(
    value: float | None,
    quality: str,
    low: float,
    high: float,
    sample_period_ms: int,
    last_sample_at: datetime | None,
    now: datetime,
) -> str:
    """Derive sensor status from current value, quality, and recency.

    Rules (applied in order):
    1. ``quality == "bad"`` → ``"stale"``
    2. No sample within ``3 x samplePeriodMs`` → ``"stale"``
       (disabled when ``samplePeriodMs == 0``, i.e. event/batch-driven signals).
    3. Value in the inner band, more than 5 % of span away from both operating
       limits → ``"normal"``
    4. Value within 5 % of span of a limit, on either side → ``"warning"``
    5. Value more than 5 % of span beyond a limit → ``"alarm"``

    The approach band matters because the waveform generator clamps samples to
    ``[low, high]``: without an in-range warning band a clamped, saturated
    sensor would still report ``normal``.
    """
    if quality == "bad":
        return "stale"

    if sample_period_ms > 0 and last_sample_at is not None:
        if last_sample_at.tzinfo is None:
            last_sample_at = last_sample_at.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        age_ms = (now - last_sample_at).total_seconds() * 1000.0
        if age_ms > 3 * sample_period_ms:
            return "stale"

    if value is None:
        return "stale"

    span = high - low
    approach = span * _APPROACH_BAND_PCT
    exceedance = span * _EXCEEDANCE_BAND_PCT
    if (low + approach) < value < (high - approach):
        return "normal"
    if (low - exceedance) <= value <= (high + exceedance):
        return "warning"
    return "alarm"


def sensor_trend(history: list[float]) -> str:
    """Linear-fit trend over up to the last ``_TREND_WINDOW`` samples.

    Returns ``"rising"``, ``"falling"``, or ``"flat"``. Flat when fewer than
    two points are available or |slope| < ``_TREND_EPSILON``.
    """
    pts = history[-_TREND_WINDOW:]
    n = len(pts)
    if n < 2:
        return "flat"

    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(pts) / n
    numerator = sum((x - mx) * (y - my) for x, y in zip(xs, pts))
    denominator = sum((x - mx) ** 2 for x in xs)
    if denominator == 0.0:
        return "flat"
    slope = numerator / denominator
    if slope > _TREND_EPSILON:
        return "rising"
    if slope < -_TREND_EPSILON:
        return "falling"
    return "flat"


def deviation_pct(value: float, low: float, high: float) -> float:
    """Signed percentage distance from the mid-band.

    Positive means above mid; negative means below. Expressed as a percentage
    of the full span.
    """
    span = high - low
    if span == 0.0:
        return 0.0
    mid = (low + high) / 2.0
    return ((value - mid) / span) * 100.0


def device_health_score(statuses: list[str]) -> float:
    """Health score in ``[0, 1]`` from a list of sensor status strings.

    Weighting: alarm = 1.0 penalty, warning = 0.4 penalty. Score is
    ``1 - weighted_bad_fraction``, clamped to ``[0, 1]``.
    """
    if not statuses:
        return 1.0
    weights = {"alarm": 1.0, "stale": 1.0, "warning": 0.4, "normal": 0.0}
    total = sum(weights.get(s, 0.0) for s in statuses)
    worst_possible = len(statuses) * 1.0
    return max(0.0, 1.0 - total / worst_possible)


def device_status_from_sensors(statuses: list[str]) -> str:
    """Aggregate device status from individual sensor status strings.

    Mapping:
    - any ``"stale"`` → ``"offline"``
    - any ``"alarm"`` → ``"fault"``
    - any ``"warning"`` → ``"degraded"``
    - all ``"normal"`` → ``"healthy"``
    """
    if not statuses:
        return "healthy"
    if "stale" in statuses:
        return "offline"
    if "alarm" in statuses:
        return "fault"
    if "warning" in statuses:
        return "degraded"
    return "healthy"
