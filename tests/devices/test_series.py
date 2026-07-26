"""Series window, downsampling, normalisation, and statistics tests."""

from __future__ import annotations

import math

import pytest

from device_simulator.series import (
    compute_stats,
    downsample,
    normalize_points,
    parse_window,
)


def test_parse_window_15m():
    assert parse_window("15m") == 15 * 60


def test_parse_window_1h():
    assert parse_window("1h") == 3600


def test_parse_window_8h():
    assert parse_window("8h") == 8 * 3600


def test_parse_window_24h():
    assert parse_window("24h") == 24 * 3600


def test_parse_window_integer_string():
    assert parse_window("7200") == 7200


def test_parse_window_invalid_raises():
    with pytest.raises(ValueError):
        parse_window("bad-window")


def _make_points(n: int) -> list[dict]:
    return [{"t": f"t{i}", "v": float(i), "q": "good"} for i in range(n)]


def test_downsample_returns_exact_count():
    pts = _make_points(200)
    result = downsample(pts, 50)
    assert len(result) == 50


def test_downsample_fewer_than_target_returns_all():
    pts = _make_points(30)
    result = downsample(pts, 100)
    assert len(result) == 30


def test_downsample_empty_returns_empty():
    assert downsample([], 10) == []


def test_downsample_zero_target_returns_empty():
    assert downsample(_make_points(10), 0) == []


def test_normalize_bounds_0_1():
    pts = [
        {"t": "t0", "v": 75.0, "q": "good"},
        {"t": "t1", "v": 130.0, "q": "good"},
        {"t": "t2", "v": 185.0, "q": "good"},
    ]
    normed = normalize_points(pts, 75.0, 185.0)
    assert normed[0]["v"] == pytest.approx(0.0)
    assert normed[1]["v"] == pytest.approx(0.5)
    assert normed[2]["v"] == pytest.approx(1.0)


def test_normalize_clamps_out_of_range():
    pts = [
        {"t": "t0", "v": 50.0, "q": "good"},
        {"t": "t1", "v": 200.0, "q": "good"},
    ]
    normed = normalize_points(pts, 75.0, 185.0)
    assert normed[0]["v"] == 0.0
    assert normed[1]["v"] == 1.0


def test_stats_correctness():
    pts = [{"t": f"t{i}", "v": float(i + 1), "q": "good"} for i in range(4)]
    # values: 1, 2, 3, 4
    stats = compute_stats(pts)
    assert stats["min"] == pytest.approx(1.0)
    assert stats["max"] == pytest.approx(4.0)
    assert stats["mean"] == pytest.approx(2.5)
    assert stats["last"] == pytest.approx(4.0)
    expected_std = math.sqrt(((1 - 2.5) ** 2 + (2 - 2.5) ** 2 + (3 - 2.5) ** 2 + (4 - 2.5) ** 2) / 4)
    assert stats["stdDev"] == pytest.approx(expected_std)


def test_stats_empty_returns_nones():
    stats = compute_stats([])
    assert stats["min"] is None
    assert stats["max"] is None
    assert stats["mean"] is None
    assert stats["stdDev"] is None
    assert stats["last"] is None
