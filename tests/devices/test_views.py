"""Frozen response shape contract guard tests.

Each test asserts that the documented key set is exactly present in the view
dict. These act as a contract guard: the BFF and Analytics MFE are being
written against these exact shapes right now.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from device_simulator.engine import DeviceSimulatorEngine
from device_simulator.incidents import INCIDENT_CATALOG, trigger_incident
from device_simulator.registry import DEVICES, SENSORS
from device_simulator.views import (
    active_incident_view,
    device_detail_view,
    device_view,
    incident_catalog_entry_view,
    sensor_view,
    series_view,
    simulator_status_view,
)

_UTC = timezone.utc
_T0 = datetime(2024, 7, 25, 6, tzinfo=_UTC)


def _make_engine():
    clock_val = [0.0]

    def clock():
        return clock_val[0]

    return DeviceSimulatorEngine(tick_interval_seconds=5.0, clock=clock)


_DEVICE_KEYS = sorted([
    "deviceId", "site", "area", "description", "status", "sensorCount",
    "activeIncidents", "lastSampleAt", "healthScore", "uptimePct",
])
_DEVICE_DETAIL_KEYS = sorted(_DEVICE_KEYS + ["sensors"])
_SENSOR_KEYS = sorted([
    "sensorId", "deviceId", "signalCode", "displayName", "area", "unit",
    "low", "high", "samplePeriodMs", "value", "quality", "status", "trend",
    "deviationPct", "clamped", "lastSampleAt",
])
_SERIES_KEYS = sorted([
    "sensorId", "deviceId", "displayName", "unit", "low", "high", "window",
    "pointCount", "points", "normalizedPoints", "stats",
])
_SERIES_STATS_KEYS = sorted(["min", "max", "mean", "stdDev", "last"])
_INCIDENT_CATALOG_KEYS = sorted([
    "incidentId", "label", "description", "severity", "defaultDurationMinutes",
    "targetDeviceIds", "affectedSignalCodes",
])
_ACTIVE_INCIDENT_KEYS = sorted([
    "activeIncidentId", "incidentId", "label", "severity", "deviceId",
    "sensorId", "startedAt", "endsAt", "remainingMinutes", "progress",
])
_STATUS_KEYS = sorted([
    "state", "scenario", "seed", "speedFactor", "tickIntervalSeconds",
    "simulatedClock", "elapsedHours", "tickCount", "deviceCount",
    "sensorCount", "activeIncidents", "availableScenarios",
    "availableIncidents", "startedAt",
])


def test_device_view_exact_keys():
    device = list(DEVICES.values())[0]
    d = device_view(device, [], [], None, 1.0, 1.0, "healthy")
    assert sorted(d.keys()) == _DEVICE_KEYS


def test_device_detail_view_exact_keys():
    device = list(DEVICES.values())[0]
    d = device_detail_view(device, [], [], None, 1.0, 1.0, "healthy", [])
    assert sorted(d.keys()) == _DEVICE_DETAIL_KEYS


def test_sensor_view_exact_keys():
    sensor = list(SENSORS.values())[0]
    s = sensor_view(sensor, 100.0, "good", "normal", "flat", 0.0, False, None)
    assert sorted(s.keys()) == _SENSOR_KEYS


def test_series_view_exact_keys():
    sensor = list(SENSORS.values())[0]
    pts = [{"t": "2024-07-25T06:00:00.000Z", "v": 100.0, "q": "good"}]
    normed = [{"t": "2024-07-25T06:00:00.000Z", "v": 0.5}]
    stats = {"min": 100.0, "max": 100.0, "mean": 100.0, "stdDev": 0.0, "last": 100.0}
    s = series_view(sensor, "1h", pts, normed, stats)
    assert sorted(s.keys()) == _SERIES_KEYS


def test_series_stats_exact_keys():
    sensor = list(SENSORS.values())[0]
    pts = [{"t": "2024-07-25T06:00:00.000Z", "v": 100.0, "q": "good"}]
    normed = [{"t": "2024-07-25T06:00:00.000Z", "v": 0.5}]
    stats = {"min": 100.0, "max": 100.0, "mean": 100.0, "stdDev": 0.0, "last": 100.0}
    s = series_view(sensor, "1h", pts, normed, stats)
    assert sorted(s["stats"].keys()) == _SERIES_STATS_KEYS


def test_incident_catalog_entry_view_exact_keys():
    entry = list(INCIDENT_CATALOG.values())[0]
    v = incident_catalog_entry_view(entry)
    assert sorted(v.keys()) == _INCIDENT_CATALOG_KEYS


def test_active_incident_view_exact_keys():
    inc = trigger_incident("degrading-furnace", _T0)
    v = active_incident_view(inc, _T0 + timedelta(minutes=5))
    assert sorted(v.keys()) == _ACTIVE_INCIDENT_KEYS


def test_simulator_status_view_exact_keys():
    eng = _make_engine()
    st = eng.status()
    assert sorted(st.keys()) == _STATUS_KEYS


def test_sensor_values_within_catalog_bounds():
    """After N ticks all buffered values must stay within physical bounds."""
    eng = _make_engine()
    eng.start(seed=42)
    for _ in range(30):
        eng.tick()
    from device_simulator.registry import SENSORS as S

    for sid, sensor in S.items():
        for pt in eng._buffers[sid]:
            v = pt["v"]
            if v is not None:
                assert sensor.low <= v <= sensor.high, (
                    f"Sensor {sid}: {v} outside [{sensor.low}, {sensor.high}]"
                )


def test_engine_devices_list_returns_correct_key_structure():
    eng = _make_engine()
    eng.start(seed=42)
    for _ in range(5):
        eng.tick()
    devices = eng.devices()
    assert len(devices) == 16
    for d in devices:
        assert sorted(d.keys()) == _DEVICE_KEYS


def test_engine_device_detail_key_structure():
    eng = _make_engine()
    eng.start(seed=42)
    for _ in range(5):
        eng.tick()
    detail = eng.device("LUX-BF-01")
    assert sorted(detail.keys()) == _DEVICE_DETAIL_KEYS
    for s in detail["sensors"]:
        assert sorted(s.keys()) == _SENSOR_KEYS


def test_engine_series_key_structure():
    eng = _make_engine()
    eng.start(seed=42)
    for _ in range(20):
        eng.tick()
    s = eng.series("LUX-BF-01:hearth_shell_temperature", window="1h", points=10)
    assert sorted(s.keys()) == _SERIES_KEYS
