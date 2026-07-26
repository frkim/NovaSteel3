"""Frozen JSON-serialisable response shapes for the device-simulator API.

ALL dict keys and structures in this module are part of the wire contract
between this service, the BFF, and the Analytics MFE. Do NOT rename or
remove keys without a coordinated version bump across all three.

See ``docs/api-contracts.md`` §6 and the frozen shapes in ``README.md``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .incidents import ActiveIncident, IncidentCatalogEntry
from .registry import Device, Sensor
from .status import deviation_pct as _deviation_pct


def _iso(dt: datetime | None) -> str | None:
    """Format a datetime as UTC ISO-8601 with trailing ``Z``, or ``None``."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def sensor_view(
    sensor: Sensor,
    value: float | None,
    quality: str,
    status: str,
    trend: str,
    dev_pct: float,
    clamped: bool,
    last_sample_at: datetime | None,
) -> dict:
    """Build the frozen ``sensor`` response shape."""
    return {
        "sensorId": sensor.sensorId,
        "deviceId": sensor.deviceId,
        "signalCode": sensor.signalCode,
        "displayName": sensor.displayName,
        "area": sensor.area,
        "unit": sensor.unit,
        "low": sensor.low,
        "high": sensor.high,
        "samplePeriodMs": sensor.samplePeriodMs,
        "value": value,
        "quality": quality,
        "status": status,
        "trend": trend,
        "deviationPct": dev_pct,
        "clamped": clamped,
        "lastSampleAt": _iso(last_sample_at),
    }


def device_view(
    device: Device,
    sensors_status: list[str],
    active_incident_ids: list[str],
    last_sample_at: datetime | None,
    health_score: float,
    uptime_pct: float,
    status: str,
) -> dict:
    """Build the frozen ``device`` response shape."""
    return {
        "deviceId": device.deviceId,
        "site": device.site,
        "area": device.area,
        "description": device.description,
        "status": status,
        "sensorCount": len(device.sensorIds),
        "activeIncidents": active_incident_ids,
        "lastSampleAt": _iso(last_sample_at),
        "healthScore": health_score,
        "uptimePct": uptime_pct,
    }


def device_detail_view(
    device: Device,
    sensors_status: list[str],
    active_incident_ids: list[str],
    last_sample_at: datetime | None,
    health_score: float,
    uptime_pct: float,
    status: str,
    sensors: list[dict],
) -> dict:
    """Build the frozen ``deviceDetail`` response shape (device + sensors list)."""
    base = device_view(
        device=device,
        sensors_status=sensors_status,
        active_incident_ids=active_incident_ids,
        last_sample_at=last_sample_at,
        health_score=health_score,
        uptime_pct=uptime_pct,
        status=status,
    )
    base["sensors"] = sensors
    return base


def series_view(
    sensor: Sensor,
    window: str,
    points: list[dict],
    normalized_points: list[dict],
    stats: dict,
) -> dict:
    """Build the frozen ``series`` response shape."""
    return {
        "sensorId": sensor.sensorId,
        "deviceId": sensor.deviceId,
        "displayName": sensor.displayName,
        "unit": sensor.unit,
        "low": sensor.low,
        "high": sensor.high,
        "window": window,
        "pointCount": len(points),
        "points": points,
        "normalizedPoints": normalized_points,
        "stats": stats,
    }


def incident_catalog_entry_view(entry: IncidentCatalogEntry) -> dict:
    """Build the frozen ``incidentCatalogEntry`` response shape."""
    return {
        "incidentId": entry.incidentId,
        "label": entry.label,
        "description": entry.description,
        "severity": entry.severity,
        "defaultDurationMinutes": entry.defaultDurationMinutes,
        "targetDeviceIds": list(entry.targetDeviceIds),
        "affectedSignalCodes": list(entry.affectedSignalCodes),
    }


def active_incident_view(incident: ActiveIncident, now: datetime) -> dict:
    """Build the frozen ``activeIncident`` response shape."""
    return {
        "activeIncidentId": incident.activeIncidentId,
        "incidentId": incident.incidentId,
        "label": incident.label,
        "severity": incident.severity,
        "deviceId": incident.deviceId,
        "sensorId": incident.sensorId,
        "startedAt": _iso(incident.startedAt),
        "endsAt": _iso(incident.endsAt),
        "remainingMinutes": incident.remaining_minutes(now),
        "progress": incident.progress(now),
    }


def simulator_status_view(
    state: str,
    scenario: str,
    seed: int,
    speed_factor: float,
    tick_interval_seconds: float,
    simulated_clock: datetime | None,
    elapsed_hours: float,
    tick_count: int,
    device_count: int,
    sensor_count: int,
    active_incidents: list[dict],
    available_scenarios: list[str],
    available_incidents: list[dict],
    started_at: datetime | None,
) -> dict:
    """Build the frozen ``simulatorStatus`` response shape."""
    return {
        "state": state,
        "scenario": scenario,
        "seed": seed,
        "speedFactor": speed_factor,
        "tickIntervalSeconds": tick_interval_seconds,
        "simulatedClock": _iso(simulated_clock),
        "elapsedHours": elapsed_hours,
        "tickCount": tick_count,
        "deviceCount": device_count,
        "sensorCount": sensor_count,
        "activeIncidents": active_incidents,
        "availableScenarios": available_scenarios,
        "availableIncidents": available_incidents,
        "startedAt": _iso(started_at),
    }
