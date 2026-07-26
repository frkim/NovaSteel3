"""Sensor status, trend, and deviation derivation tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from device_simulator.status import (
    deviation_pct,
    device_health_score,
    device_status_from_sensors,
    sensor_status,
    sensor_trend,
)

_UTC = timezone.utc
_NOW = datetime(2024, 7, 25, 6, 0, 0, tzinfo=_UTC)
_RECENT = _NOW - timedelta(seconds=1)


def test_status_normal_within_range():
    st = sensor_status(100.0, "good", 75.0, 185.0, 5_000, _RECENT, _NOW)
    assert st == "normal"


def test_status_warning_just_outside_low():
    low, high = 75.0, 185.0
    span = high - low
    # 3 % outside low — within the 5 % exceedance band
    v = low - span * 0.03
    st = sensor_status(v, "good", low, high, 5_000, _RECENT, _NOW)
    assert st == "warning"


def test_status_warning_when_approaching_high_from_inside():
    low, high = 75.0, 185.0
    span = high - low
    # 2 % inside the high limit — a clamped sensor must not report "normal"
    v = high - span * 0.02
    st = sensor_status(v, "good", low, high, 5_000, _RECENT, _NOW)
    assert st == "warning"


def test_status_warning_when_approaching_low_from_inside():
    low, high = 75.0, 185.0
    span = high - low
    v = low + span * 0.02
    st = sensor_status(v, "good", low, high, 5_000, _RECENT, _NOW)
    assert st == "warning"


def test_status_alarm_beyond_warning_band():
    low, high = 75.0, 185.0
    span = high - low
    # 10 % outside high — beyond 5 % warning band
    v = high + span * 0.10
    st = sensor_status(v, "good", low, high, 5_000, _RECENT, _NOW)
    assert st == "alarm"


def test_status_stale_quality_bad():
    st = sensor_status(100.0, "bad", 75.0, 185.0, 5_000, _RECENT, _NOW)
    assert st == "stale"


def test_status_stale_old_sample():
    old_sample = _NOW - timedelta(seconds=20)  # 20 s ago, period=5 000 ms → stale after 15 s
    st = sensor_status(100.0, "good", 75.0, 185.0, 5_000, old_sample, _NOW)
    assert st == "stale"


def test_status_not_stale_zero_period_even_after_long_gap():
    """sample_period_ms == 0 (event-driven / per-heat) must NEVER be flagged stale
    due to timing — a 3 × 0 threshold is undefined and must be skipped entirely."""
    very_old = _NOW - timedelta(hours=8)
    for value in (1440.0, 1530.0, 1480.0):
        st = sensor_status(value, "good", 1440.0, 1530.0, 0, very_old, _NOW)
        assert st != "stale", (
            f"Event-driven sensor (period=0) must not be stale regardless of age; got {st!r}"
        )


def test_status_not_stale_zero_period_none_last_sample():
    """Before the first event-driven sample arrives, quality is good (not stale)."""
    st = sensor_status(1480.0, "good", 1440.0, 1530.0, 0, None, _NOW)
    assert st != "stale"


def test_trend_rising():
    history = list(range(10))  # strictly increasing
    assert sensor_trend(history) == "rising"


def test_trend_falling():
    history = list(range(10, 0, -1))  # strictly decreasing
    assert sensor_trend(history) == "falling"


def test_trend_flat():
    history = [5.0] * 10  # constant
    assert sensor_trend(history) == "flat"


def test_trend_flat_with_fewer_than_two_points():
    assert sensor_trend([]) == "flat"
    assert sensor_trend([42.0]) == "flat"


def test_deviation_pct_at_midpoint():
    assert deviation_pct(130.0, 75.0, 185.0) == pytest.approx(0.0)


def test_deviation_pct_at_high():
    """At high bound deviation should be +50 %."""
    assert deviation_pct(185.0, 75.0, 185.0) == pytest.approx(50.0)


def test_deviation_pct_at_low():
    assert deviation_pct(75.0, 75.0, 185.0) == pytest.approx(-50.0)


def test_device_health_score_all_normal():
    assert device_health_score(["normal", "normal", "normal"]) == pytest.approx(1.0)


def test_device_health_score_all_alarm():
    score = device_health_score(["alarm", "alarm"])
    assert score == pytest.approx(0.0)


def test_device_health_score_mixed():
    score = device_health_score(["normal", "warning", "alarm"])
    assert 0.0 < score < 1.0


def test_device_status_all_normal():
    assert device_status_from_sensors(["normal", "normal"]) == "healthy"


def test_device_status_warning():
    assert device_status_from_sensors(["normal", "warning"]) == "degraded"


def test_device_status_alarm():
    assert device_status_from_sensors(["normal", "alarm"]) == "fault"


def test_device_status_stale():
    assert device_status_from_sensors(["stale", "normal"]) == "offline"


def test_device_status_empty():
    assert device_status_from_sensors([]) == "healthy"
