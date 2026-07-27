"""NovaSteel device-simulator service.

Deterministic live device simulator for the NovaSteel synthetic industrial-steel
demo estate. Provides a FastAPI micro-service and importable Python library.

Public API surface:
- ``DeviceSimulatorEngine`` — main runtime (state machine, ring buffer, auto-advance)
- ``INCIDENT_CATALOG`` — dict of ``IncidentCatalogEntry``
- ``CATALOG_ASSETS`` / ``CATALOG_SIGNALS`` — static reference data
- ``DEVICES`` / ``SENSORS`` — runtime ``Device``/``Sensor`` registries
"""

from __future__ import annotations

from .catalog import CATALOG_ASSETS, CATALOG_SIGNALS, SITE_ID, SITE_IDS, ALL_SITE_IDS
from .engine import DeviceSimulatorEngine, IllegalTransitionError
from .incidents import INCIDENT_CATALOG, ActiveIncident, IncidentCatalogEntry
from .registry import DEVICES, SENSORS, Device, Sensor

__version__ = "0.1.0"

__all__ = [
    "DeviceSimulatorEngine",
    "IllegalTransitionError",
    "INCIDENT_CATALOG",
    "ActiveIncident",
    "IncidentCatalogEntry",
    "CATALOG_ASSETS",
    "CATALOG_SIGNALS",
    "SITE_ID",
    "SITE_IDS",
    "ALL_SITE_IDS",
    "DEVICES",
    "SENSORS",
    "Device",
    "Sensor",
]
