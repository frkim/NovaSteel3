"""Registry integrity tests.

Verifies that ``build_registry`` returns well-formed Device and Sensor
instances consistent with the catalog.
"""

from __future__ import annotations

from device_simulator.registry import DEVICES, SENSORS, build_registry


def test_build_registry_returns_all_devices():
    devices, _ = build_registry()
    assert len(devices) == 6


def test_build_registry_returns_all_sensors():
    _, sensors = build_registry()
    assert len(sensors) == 34


def test_sensor_id_format():
    """sensorId must be '{deviceId}:{signalCode}'."""
    for sensor_id, sensor in SENSORS.items():
        expected = f"{sensor.deviceId}:{sensor.signalCode}"
        assert sensor_id == expected, f"sensorId mismatch: {sensor_id!r} != {expected!r}"
        assert sensor.sensorId == sensor_id


def test_display_names_are_title_case():
    for sensor in SENSORS.values():
        assert sensor.displayName == sensor.signalCode.replace("_", " ").title()


def test_sensor_ids_are_unique():
    ids = list(SENSORS.keys())
    assert len(ids) == len(set(ids))


def test_all_sensors_map_to_known_device():
    for sensor in SENSORS.values():
        assert sensor.deviceId in DEVICES, (
            f"Sensor {sensor.sensorId!r} references unknown device {sensor.deviceId!r}"
        )


def test_device_sensor_ids_reference_existing_sensors():
    for device in DEVICES.values():
        for sid in device.sensorIds:
            assert sid in SENSORS, (
                f"Device {device.deviceId!r} references non-existent sensor {sid!r}"
            )
