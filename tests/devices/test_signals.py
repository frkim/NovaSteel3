"""Signal generation determinism and range tests."""

from __future__ import annotations

from device_simulator.signals import generate_value


_SENSOR_ID = "LUX-BF-01:hearth_shell_temperature"
_DEVICE_ID = "LUX-BF-01"
_SIGNAL_CODE = "hearth_shell_temperature"
_LOW = 75.0
_HIGH = 185.0


def test_generate_value_within_range():
    for tick in range(20):
        v, q, clamped = generate_value(
            _SENSOR_ID, _DEVICE_ID, _SIGNAL_CODE, tick, 42, "healthy-baseline", _LOW, _HIGH, []
        )
        assert _LOW <= v <= _HIGH, f"tick={tick}: value {v} outside [{_LOW}, {_HIGH}]"


def test_determinism_same_seed():
    results_a = [
        generate_value(_SENSOR_ID, _DEVICE_ID, _SIGNAL_CODE, t, 99, "healthy-baseline", _LOW, _HIGH, [])
        for t in range(30)
    ]
    results_b = [
        generate_value(_SENSOR_ID, _DEVICE_ID, _SIGNAL_CODE, t, 99, "healthy-baseline", _LOW, _HIGH, [])
        for t in range(30)
    ]
    assert results_a == results_b


def test_determinism_different_seeds_differ():
    v1, _, _ = generate_value(_SENSOR_ID, _DEVICE_ID, _SIGNAL_CODE, 5, 1111, "healthy-baseline", _LOW, _HIGH, [])
    v2, _, _ = generate_value(_SENSOR_ID, _DEVICE_ID, _SIGNAL_CODE, 5, 9999, "healthy-baseline", _LOW, _HIGH, [])
    assert v1 != v2, "Different seeds should produce different values at same tick"


def test_generate_value_is_pure_function():
    """Calling twice with same args returns same result (no side effects)."""
    args = (_SENSOR_ID, _DEVICE_ID, _SIGNAL_CODE, 7, 42, "healthy-baseline", _LOW, _HIGH, [])
    assert generate_value(*args) == generate_value(*args)


def test_generate_value_different_scenarios_differ():
    v1, _, _ = generate_value(
        _SENSOR_ID, _DEVICE_ID, _SIGNAL_CODE, 3, 240725, "healthy-baseline", _LOW, _HIGH, []
    )
    v2, _, _ = generate_value(
        _SENSOR_ID, _DEVICE_ID, _SIGNAL_CODE, 3, 240726, "lining-degradation-21d", _LOW, _HIGH, []
    )
    assert v1 != v2
