"""Device and Sensor registry built from the static catalog.

Provides the ``Device`` and ``Sensor`` dataclasses and the ``build_registry``
factory that maps every ``CatalogAsset`` / ``CatalogSignal`` pair into the
runtime domain model used by the engine, status, and view layers.

See ``docs/data/synthetic-data-and-simulators.md`` sections 1-3.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .catalog import CATALOG_ASSETS, CATALOG_SIGNALS, SIGNALS_BY_ASSET, SITE_ID


def _display_name(signal_code: str) -> str:
    """Convert snake_case signal code to Title Case display name."""
    return signal_code.replace("_", " ").title()


@dataclass(frozen=True)
class Sensor:
    """Runtime descriptor for one physical sensor in the demo estate."""

    sensorId: str
    deviceId: str
    signalCode: str
    displayName: str
    area: str
    unit: str
    low: float
    high: float
    samplePeriodMs: int


@dataclass(frozen=True)
class Device:
    """Runtime descriptor for one asset/device in the demo estate."""

    deviceId: str
    site: str
    area: str
    description: str
    sensorIds: list[str] = field(default_factory=list)


def build_registry() -> tuple[dict[str, Device], dict[str, Sensor]]:
    """Build Device and Sensor registries from the static catalog.

    Returns a ``(devices, sensors)`` pair where every key is the respective
    identifier string and every value is a frozen dataclass instance.
    ``sensorId`` format: ``"{deviceId}:{signalCode}"``.
    """
    sensors: dict[str, Sensor] = {}
    for signal in CATALOG_SIGNALS.values():
        asset = CATALOG_ASSETS[signal.asset_id]
        sensor_id = f"{signal.asset_id}:{signal.signal_code}"
        sensors[sensor_id] = Sensor(
            sensorId=sensor_id,
            deviceId=signal.asset_id,
            signalCode=signal.signal_code,
            displayName=_display_name(signal.signal_code),
            area=asset.area,
            unit=signal.unit,
            low=signal.low,
            high=signal.high,
            samplePeriodMs=signal.sample_period_ms,
        )

    devices: dict[str, Device] = {}
    for asset in CATALOG_ASSETS.values():
        asset_signals = SIGNALS_BY_ASSET.get(asset.asset_id, [])
        sensor_ids = [f"{asset.asset_id}:{s.signal_code}" for s in asset_signals]
        devices[asset.asset_id] = Device(
            deviceId=asset.asset_id,
            site=SITE_ID,
            area=asset.area,
            description=asset.asset_type,
            sensorIds=sensor_ids,
        )

    return devices, sensors


DEVICES, SENSORS = build_registry()
