"""Incident catalog and active-incident lifecycle for the device simulator.

Defines seven injectable fault/anomaly scenarios and the ``ActiveIncident``
dataclass that tracks a triggered instance. Effects are applied in
``signals.py``; the catalog entries here carry only the metadata needed by
the API contract (id, label, description, severity, duration, targets).

See ``docs/data/synthetic-data-and-simulators.md`` section 8.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass(frozen=True)
class IncidentCatalogEntry:
    """Static descriptor for one incident type."""

    incidentId: str
    label: str
    description: str
    severity: str
    defaultDurationMinutes: int
    targetDeviceIds: list[str]
    affectedSignalCodes: list[str]


@dataclass
class ActiveIncident:
    """A triggered, time-bounded incident instance."""

    activeIncidentId: str
    incidentId: str
    label: str
    severity: str
    deviceId: str
    sensorId: Optional[str]
    startedAt: datetime
    endsAt: datetime

    def progress(self, now: datetime) -> float:
        """Fraction of incident duration elapsed; clamped to ``[0, 1]``."""
        total = (self.endsAt - self.startedAt).total_seconds()
        if total <= 0:
            return 1.0
        elapsed = (now - self.startedAt).total_seconds()
        return max(0.0, min(1.0, elapsed / total))

    def remaining_minutes(self, now: datetime) -> float:
        delta = (self.endsAt - now).total_seconds()
        return max(0.0, delta / 60.0)

    def is_expired(self, now: datetime) -> bool:
        return now >= self.endsAt


INCIDENT_CATALOG: dict[str, IncidentCatalogEntry] = {
    e.incidentId: e
    for e in [
        IncidentCatalogEntry(
            incidentId="degrading-furnace",
            label="Accelerated hearth lining wear",
            description=(
                "Simulates accelerated hearth refractory wear on LUX-BF-01: "
                "local_heat_flux ramps up, hearth_refractory_estimate ramps down, "
                "hearth_shell_temperature rises."
            ),
            severity="high",
            defaultDurationMinutes=30,
            targetDeviceIds=["LUX-BF-01"],
            affectedSignalCodes=[
                "local_heat_flux",
                "hearth_refractory_estimate",
                "hearth_shell_temperature",
            ],
        ),
        IncidentCatalogEntry(
            incidentId="cooling-water-loss",
            label="Cooling water circuit loss",
            description=(
                "Simulates partial loss of blast-furnace cooling-water supply: "
                "cooling_water_flow drops sharply, "
                "cooling_water_outlet_temperature rises."
            ),
            severity="critical",
            defaultDurationMinutes=15,
            targetDeviceIds=["LUX-BF-01"],
            affectedSignalCodes=[
                "cooling_water_flow",
                "cooling_water_outlet_temperature",
            ],
        ),
        IncidentCatalogEntry(
            incidentId="sensor-drift",
            label="Sensor measurement drift",
            description=(
                "Injects a slow additive bias on the target sensor, simulating "
                "thermocouple or transmitter calibration drift."
            ),
            severity="medium",
            defaultDurationMinutes=60,
            targetDeviceIds=["LUX-BF-01", "DE-EAF-01", "BE-CRM-01", "ES-EAF-01"],
            affectedSignalCodes=[],
        ),
        IncidentCatalogEntry(
            incidentId="sensor-dropout",
            label="Sensor dropout / communication loss",
            description=(
                "Target sensor stops updating; quality becomes 'bad' and "
                "status transitions to 'stale'."
            ),
            severity="medium",
            defaultDurationMinutes=10,
            targetDeviceIds=["LUX-BF-01", "DE-EAF-01", "BE-CRM-01", "ES-EAF-01"],
            affectedSignalCodes=[],
        ),
        IncidentCatalogEntry(
            incidentId="energy-price-spike",
            label="Day-ahead energy price spike",
            description=(
                "Simulates a scarcity event on LUX-UTIL-01: spot_price "
                "spikes toward the high bound, site_active_power rises."
            ),
            severity="medium",
            defaultDurationMinutes=45,
            targetDeviceIds=["LUX-UTIL-01"],
            affectedSignalCodes=["spot_price", "site_active_power"],
        ),
        IncidentCatalogEntry(
            incidentId="quality-drift",
            label="Product dimensional quality drift",
            description=(
                "Dimensional signals on LUX-CC-01 (slab_width_deviation, mould_level) "
                "and LUX-HSM-01 (coiling_temperature) drift out of the in-band "
                "specification window."
            ),
            severity="high",
            defaultDurationMinutes=45,
            targetDeviceIds=["LUX-CC-01", "LUX-HSM-01"],
            affectedSignalCodes=[
                "slab_width_deviation",
                "mould_level",
                "coiling_temperature",
            ],
        ),
        IncidentCatalogEntry(
            incidentId="edge-outage-recovery",
            label="Edge node outage and catch-up recovery",
            description=(
                "All sensors on the target device go stale (quality 'bad') for "
                "the first half of the incident, then deliver a simulated "
                "catch-up burst."
            ),
            severity="low",
            defaultDurationMinutes=20,
            targetDeviceIds=["LUX-UTIL-01", "DE-UTIL-01", "BE-UTIL-01", "ES-UTIL-01"],
            affectedSignalCodes=[],
        ),
    ]
}


def trigger_incident(
    incident_id: str,
    simulated_now: datetime,
    device_id: Optional[str] = None,
    sensor_id: Optional[str] = None,
    duration_minutes: Optional[float] = None,
) -> ActiveIncident:
    """Create and return a new ``ActiveIncident`` for the given catalog entry.

    If ``device_id`` is omitted the first entry in
    ``IncidentCatalogEntry.targetDeviceIds`` is used (where applicable).
    """
    entry = INCIDENT_CATALOG.get(incident_id)
    if entry is None:
        raise KeyError(f"Unknown incident id: {incident_id!r}")

    resolved_device = device_id or (entry.targetDeviceIds[0] if entry.targetDeviceIds else "")
    if not resolved_device:
        raise ValueError(
            f"Incident {incident_id!r} requires an explicit device_id because "
            "it has no default target device."
        )

    duration = duration_minutes if duration_minutes is not None else float(entry.defaultDurationMinutes)
    if simulated_now.tzinfo is None:
        simulated_now = simulated_now.replace(tzinfo=timezone.utc)

    return ActiveIncident(
        activeIncidentId=str(uuid.uuid4()),
        incidentId=incident_id,
        label=entry.label,
        severity=entry.severity,
        deviceId=resolved_device,
        sensorId=sensor_id,
        startedAt=simulated_now,
        endsAt=simulated_now + timedelta(minutes=duration),
    )
