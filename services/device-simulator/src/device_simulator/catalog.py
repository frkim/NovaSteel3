"""Asset and signal registry for the device-simulator package.

Contains two registries:

* **Core registry** (18 signals) — byte-faithful mirror of
  ``simulator/config.py``'s ``SIGNAL_REGISTRY``.  Covers LUX-BF-01 (11),
  LUX-RHF-01 (3), and LUX-HSM-01 (4).  The sync test in
  ``tests/devices/test_catalog.py`` asserts these 18 match exactly whenever the
  upstream ``simulator`` package is importable.

* **Extended demo registry** (16 signals, ``extended=True``) — physically
  plausible signals for LUX-BOF-01, LUX-CC-01 and LUX-UTIL-01 so all six demo
  assets have live sensors.  These are EXCLUDED from the upstream sync check.

Total: 6 devices, 34 sensors.

See ``docs/data/synthetic-data-and-simulators.md`` sections 1-3.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SITE_ID = "NS-DEMO-LUX-01"
DATA_CLASSIFICATION = "SYNTHETIC"
PRIVACY_LABEL = "DEMO-NONPERSONAL"

SCENARIO_SEEDS: dict[str, int] = {
    "healthy-baseline": 240725,
    "lining-degradation-21d": 240726,
    "energy-price-spike": 240727,
    "quality-drift": 240728,
    "edge-outage-recovery": 240729,
    "demo-full": 240725,
}

AVAILABLE_SCENARIOS: list[str] = sorted(SCENARIO_SEEDS)


@dataclass(frozen=True)
class CatalogAsset:
    """Static descriptor for one physical asset in the demo estate."""

    asset_id: str
    plant_id: str
    area: str
    asset_type: str


@dataclass(frozen=True)
class CatalogSignal:
    """One row of the sensor/signal registry.

    ``extended=True`` marks signals added beyond the upstream
    ``simulator/config.py`` registry for demo completeness.
    """

    signal_code: str
    unit: str
    low: float
    high: float
    sample_period_ms: int
    asset_id: str
    extended: bool = False


CATALOG_ASSETS: dict[str, CatalogAsset] = {
    a.asset_id: a
    for a in [
        CatalogAsset("LUX-BF-01", SITE_ID, "Ironmaking", "Blast furnace"),
        CatalogAsset("LUX-BOF-01", SITE_ID, "Steelmaking", "Basic oxygen furnace"),
        CatalogAsset("LUX-CC-01", SITE_ID, "Casting", "Slab caster"),
        CatalogAsset("LUX-RHF-01", SITE_ID, "Rolling", "Reheat furnace"),
        CatalogAsset("LUX-HSM-01", SITE_ID, "Rolling", "Hot strip mill"),
        CatalogAsset("LUX-UTIL-01", SITE_ID, "Utilities", "Energy system"),
    ]
}

# ---------------------------------------------------------------------------
# Core registry — exact mirror of simulator/config.py SIGNAL_REGISTRY (18 signals)
# ---------------------------------------------------------------------------
_CORE_SIGNALS: list[CatalogSignal] = [
    # LUX-BF-01 — Blast furnace (11 signals)
    CatalogSignal("hearth_shell_temperature", "Cel", 75.0, 185.0, 5_000, "LUX-BF-01"),
    CatalogSignal("cooling_water_inlet_temperature", "Cel", 20.0, 36.0, 5_000, "LUX-BF-01"),
    CatalogSignal("cooling_water_outlet_temperature", "Cel", 28.0, 58.0, 5_000, "LUX-BF-01"),
    CatalogSignal("cooling_water_flow", "m3/h", 110.0, 310.0, 5_000, "LUX-BF-01"),
    CatalogSignal("local_heat_flux", "kW/m2", 35.0, 190.0, 5_000, "LUX-BF-01"),
    CatalogSignal("hearth_refractory_estimate", "mm", 280.0, 950.0, 900_000, "LUX-BF-01"),
    CatalogSignal("hot_blast_temperature", "Cel", 1050.0, 1250.0, 10_000, "LUX-BF-01"),
    CatalogSignal("top_pressure", "bar", 1.4, 2.6, 1_000, "LUX-BF-01"),
    CatalogSignal("pulverized_coal_injection", "kg/t", 100.0, 190.0, 60_000, "LUX-BF-01"),
    CatalogSignal("hot_metal_temperature", "Cel", 1440.0, 1530.0, 0, "LUX-BF-01"),
    CatalogSignal("production_rate", "t/h", 180.0, 360.0, 60_000, "LUX-BF-01"),
    # LUX-RHF-01 — Reheat furnace (3 signals)
    CatalogSignal("reheat_zone_temperature", "Cel", 850.0, 1285.0, 2_000, "LUX-RHF-01"),
    CatalogSignal("furnace_gas_flow", "m3/h", 4000.0, 42000.0, 2_000, "LUX-RHF-01"),
    CatalogSignal("furnace_excess_o2", "%", 0.8, 4.5, 2_000, "LUX-RHF-01"),
    # LUX-HSM-01 — Hot strip mill (4 signals)
    CatalogSignal("stand_motor_current", "A", 1000.0, 12000.0, 1_000, "LUX-HSM-01"),
    CatalogSignal("rolling_force", "MW", 4.0, 38.0, 1_000, "LUX-HSM-01"),
    CatalogSignal("strip_speed", "m/s", 0.2, 22.0, 1_000, "LUX-HSM-01"),
    CatalogSignal("coiling_temperature", "Cel", 520.0, 720.0, 0, "LUX-HSM-01"),
]

# ---------------------------------------------------------------------------
# Extended demo registry — fills LUX-BOF-01, LUX-CC-01, LUX-UTIL-01 (16 signals)
# ---------------------------------------------------------------------------
_EXTENDED_SIGNALS: list[CatalogSignal] = [
    # LUX-BOF-01 — Basic oxygen furnace (5 signals)
    CatalogSignal("oxygen_lance_flow", "Nm3/min", 180.0, 920.0, 1_000, "LUX-BOF-01", extended=True),
    CatalogSignal("vessel_shell_temperature", "Cel", 180.0, 420.0, 5_000, "LUX-BOF-01", extended=True),
    CatalogSignal("bath_temperature", "Cel", 1580.0, 1700.0, 10_000, "LUX-BOF-01", extended=True),
    CatalogSignal("slag_basicity_index", "ratio", 2.4, 4.2, 60_000, "LUX-BOF-01", extended=True),
    CatalogSignal("tap_to_tap_time", "min", 32.0, 58.0, 60_000, "LUX-BOF-01", extended=True),
    # LUX-CC-01 — Slab caster (5 signals)
    CatalogSignal("mould_level", "mm", 60.0, 140.0, 1_000, "LUX-CC-01", extended=True),
    CatalogSignal("casting_speed", "m/min", 0.6, 1.8, 1_000, "LUX-CC-01", extended=True),
    CatalogSignal("secondary_cooling_flow", "m3/h", 40.0, 220.0, 2_000, "LUX-CC-01", extended=True),
    CatalogSignal("superheat", "Cel", 10.0, 45.0, 10_000, "LUX-CC-01", extended=True),
    CatalogSignal("slab_width_deviation", "mm", -6.0, 6.0, 5_000, "LUX-CC-01", extended=True),
    # LUX-UTIL-01 — Energy system (6 signals)
    CatalogSignal("site_active_power", "MW", 38.0, 180.0, 1_000, "LUX-UTIL-01", extended=True),
    CatalogSignal("power_factor", "ratio", 0.86, 1.0, 5_000, "LUX-UTIL-01", extended=True),
    CatalogSignal("grid_frequency", "Hz", 49.8, 50.2, 1_000, "LUX-UTIL-01", extended=True),
    CatalogSignal("compressed_air_pressure", "bar", 5.8, 8.2, 2_000, "LUX-UTIL-01", extended=True),
    CatalogSignal("spot_price", "EUR/MWh", -15.0, 420.0, 900_000, "LUX-UTIL-01", extended=True),
    CatalogSignal("grid_carbon_intensity", "gCO2/kWh", 40.0, 480.0, 900_000, "LUX-UTIL-01", extended=True),
]

CATALOG_SIGNALS: dict[str, CatalogSignal] = {
    s.signal_code: s for s in _CORE_SIGNALS + _EXTENDED_SIGNALS
}

CORE_SIGNAL_CODES: frozenset[str] = frozenset(s.signal_code for s in _CORE_SIGNALS)

SIGNALS_BY_ASSET: dict[str, list[CatalogSignal]] = {}
for _s in CATALOG_SIGNALS.values():
    SIGNALS_BY_ASSET.setdefault(_s.asset_id, []).append(_s)
