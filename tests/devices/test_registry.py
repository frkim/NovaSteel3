"""Registry integrity tests.

Verifies that ``build_registry`` returns well-formed Device and Sensor
instances consistent with the catalog.
"""

from __future__ import annotations

from device_simulator.registry import DEVICES, SENSORS, build_registry


def test_build_registry_returns_all_devices():
    devices, _ = build_registry()
    assert len(devices) == 16


def test_build_registry_returns_all_sensors():
    _, sensors = build_registry()
    assert len(sensors) == 86


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


def test_different_sites_return_different_device_sets():
    """Two different sites have non-overlapping device sets."""
    lux_devices = [d for d in DEVICES.values() if d.site == "NS-DEMO-LUX-01"]
    de_devices = [d for d in DEVICES.values() if d.site == "NS-DEMO-DE-01"]
    be_devices = [d for d in DEVICES.values() if d.site == "NS-DEMO-BE-01"]
    es_devices = [d for d in DEVICES.values() if d.site == "NS-DEMO-ES-01"]
    assert len(lux_devices) == 6
    assert len(de_devices) == 4
    assert len(be_devices) == 3
    assert len(es_devices) == 3
    lux_ids = {d.deviceId for d in lux_devices}
    de_ids = {d.deviceId for d in de_devices}
    assert lux_ids.isdisjoint(de_ids), "LUX and DE should have no shared devices"


def test_sites_have_distinct_sensor_counts():
    """Each site has a genuinely different number of sensors."""
    from device_simulator.catalog import SIGNALS_BY_ASSET, CATALOG_ASSETS

    site_sensor_counts: dict[str, int] = {}
    for asset_id, asset in CATALOG_ASSETS.items():
        site = asset.plant_id
        site_sensor_counts[site] = site_sensor_counts.get(site, 0) + len(
            SIGNALS_BY_ASSET.get(asset_id, [])
        )
    counts = list(site_sensor_counts.values())
    # All 4 sites have different counts
    assert len(set(counts)) == len(counts), f"Sensor counts should differ: {site_sensor_counts}"
