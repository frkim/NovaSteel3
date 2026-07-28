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


# ---------------------------------------------------------------------------
# Site identifiers
# ---------------------------------------------------------------------------
SITE_IDS: dict[str, str] = {
    "lu": "NS-DEMO-LUX-01",
    "de": "NS-DEMO-DE-01",
    "be": "NS-DEMO-BE-01",
    "es": "NS-DEMO-ES-01",
}
ALL_SITE_IDS: list[str] = list(SITE_IDS.values())

CATALOG_ASSETS: dict[str, CatalogAsset] = {
    a.asset_id: a
    for a in [
        # --- LUX: Integrated steelworks (BF + BOF + caster + rolling + utilities)
        CatalogAsset("LUX-BF-01", SITE_ID, "Ironmaking", "Blast furnace"),
        CatalogAsset("LUX-BOF-01", SITE_ID, "Steelmaking", "Basic oxygen furnace"),
        CatalogAsset("LUX-CC-01", SITE_ID, "Casting", "Slab caster"),
        CatalogAsset("LUX-RHF-01", SITE_ID, "Rolling", "Reheat furnace"),
        CatalogAsset("LUX-HSM-01", SITE_ID, "Rolling", "Hot strip mill"),
        CatalogAsset("LUX-UTIL-01", SITE_ID, "Utilities", "Energy system"),
        # --- DE: Electric-arc-furnace steelmaking + ladle + billet caster
        CatalogAsset("DE-EAF-01", SITE_IDS["de"], "Steelmaking", "Electric arc furnace"),
        CatalogAsset("DE-LF-01", SITE_IDS["de"], "Steelmaking", "Ladle furnace"),
        CatalogAsset("DE-BCM-01", SITE_IDS["de"], "Casting", "Billet caster"),
        CatalogAsset("DE-UTIL-01", SITE_IDS["de"], "Utilities", "Energy system"),
        # --- BE: EAF melt shop + cold rolling + galvanizing line
        CatalogAsset("BE-EAF-01", SITE_IDS["be"], "Steelmaking", "Electric arc furnace"),
        CatalogAsset("BE-CRM-01", SITE_IDS["be"], "Rolling", "Cold rolling mill"),
        CatalogAsset("BE-GAL-01", SITE_IDS["be"], "Coating", "Hot-dip galvanizing line"),
        CatalogAsset("BE-UTIL-01", SITE_IDS["be"], "Utilities", "Energy system"),
        # --- ES: EAF mini-mill + wire rod mill
        CatalogAsset("ES-EAF-01", SITE_IDS["es"], "Steelmaking", "Electric arc furnace"),
        CatalogAsset("ES-WRM-01", SITE_IDS["es"], "Rolling", "Wire rod mill"),
        CatalogAsset("ES-UTIL-01", SITE_IDS["es"], "Utilities", "Energy system"),
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
# Extended demo registry — fills remaining assets with plausible signals
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
    # --- DE-EAF-01: Electric arc furnace (6 signals)
    CatalogSignal("arc_current", "kA", 30.0, 80.0, 1_000, "DE-EAF-01", extended=True),
    CatalogSignal("electrode_position", "mm", 200.0, 900.0, 1_000, "DE-EAF-01", extended=True),
    CatalogSignal("bath_temperature", "Cel", 1550.0, 1680.0, 10_000, "DE-EAF-01", extended=True),
    CatalogSignal("off_gas_temperature", "Cel", 800.0, 1400.0, 2_000, "DE-EAF-01", extended=True),
    CatalogSignal("oxygen_injection_rate", "Nm3/min", 20.0, 120.0, 2_000, "DE-EAF-01", extended=True),
    CatalogSignal("power_on_time", "min", 35.0, 65.0, 60_000, "DE-EAF-01", extended=True),
    # --- DE-LF-01: Ladle furnace (5 signals)
    CatalogSignal("ladle_temperature", "Cel", 1540.0, 1640.0, 5_000, "DE-LF-01", extended=True),
    CatalogSignal("argon_flow_rate", "Nl/min", 100.0, 600.0, 2_000, "DE-LF-01", extended=True),
    CatalogSignal("slag_height", "mm", 50.0, 200.0, 10_000, "DE-LF-01", extended=True),
    CatalogSignal("heating_power", "MW", 5.0, 30.0, 1_000, "DE-LF-01", extended=True),
    CatalogSignal("desulfurization_rate", "ppm/min", 0.5, 4.0, 60_000, "DE-LF-01", extended=True),
    # --- DE-BCM-01: Billet caster (5 signals)
    CatalogSignal("mould_level", "mm", 55.0, 130.0, 1_000, "DE-BCM-01", extended=True),
    CatalogSignal("casting_speed", "m/min", 2.0, 5.5, 1_000, "DE-BCM-01", extended=True),
    CatalogSignal("secondary_cooling_flow", "m3/h", 30.0, 180.0, 2_000, "DE-BCM-01", extended=True),
    CatalogSignal("strand_temperature", "Cel", 900.0, 1200.0, 5_000, "DE-BCM-01", extended=True),
    CatalogSignal("billet_length_deviation", "mm", -4.0, 4.0, 5_000, "DE-BCM-01", extended=True),
    # --- DE-UTIL-01: Energy system (6 signals)
    CatalogSignal("site_active_power", "MW", 45.0, 220.0, 1_000, "DE-UTIL-01", extended=True),
    CatalogSignal("power_factor", "ratio", 0.88, 1.0, 5_000, "DE-UTIL-01", extended=True),
    CatalogSignal("grid_frequency", "Hz", 49.8, 50.2, 1_000, "DE-UTIL-01", extended=True),
    CatalogSignal("compressed_air_pressure", "bar", 6.0, 8.5, 2_000, "DE-UTIL-01", extended=True),
    CatalogSignal("spot_price", "EUR/MWh", -10.0, 380.0, 900_000, "DE-UTIL-01", extended=True),
    CatalogSignal("grid_carbon_intensity", "gCO2/kWh", 60.0, 520.0, 900_000, "DE-UTIL-01", extended=True),
    # --- BE-EAF-01: Electric arc furnace, the flexible load of the energy-eaf-flex
    # scenario (simulator/manifests/energy-eaf-flex.json). Five signals, so every
    # site keeps a distinct sensor count (LUX 34, DE 22, BE 21, ES 14).
    CatalogSignal("arc_current", "kA", 30.0, 80.0, 1_000, "BE-EAF-01", extended=True),
    CatalogSignal("bath_temperature", "Cel", 1550.0, 1680.0, 10_000, "BE-EAF-01", extended=True),
    CatalogSignal("heat_active_power", "MW", 80.0, 150.0, 1_000, "BE-EAF-01", extended=True),
    CatalogSignal("power_on_time", "min", 35.0, 65.0, 60_000, "BE-EAF-01", extended=True),
    CatalogSignal("tap_to_tap_time", "min", 45.0, 75.0, 60_000, "BE-EAF-01", extended=True),
    # --- BE-CRM-01: Cold rolling mill (5 signals)
    CatalogSignal("strip_tension", "kN", 20.0, 180.0, 1_000, "BE-CRM-01", extended=True),
    CatalogSignal("roll_force", "MN", 2.0, 18.0, 1_000, "BE-CRM-01", extended=True),
    CatalogSignal("strip_speed", "m/min", 200.0, 1800.0, 1_000, "BE-CRM-01", extended=True),
    CatalogSignal("strip_thickness", "mm", 0.2, 3.0, 2_000, "BE-CRM-01", extended=True),
    CatalogSignal("coolant_temperature", "Cel", 30.0, 65.0, 5_000, "BE-CRM-01", extended=True),
    # --- BE-GAL-01: Hot-dip galvanizing (5 signals)
    CatalogSignal("zinc_bath_temperature", "Cel", 445.0, 465.0, 5_000, "BE-GAL-01", extended=True),
    CatalogSignal("line_speed", "m/min", 60.0, 200.0, 1_000, "BE-GAL-01", extended=True),
    CatalogSignal("coating_weight", "g/m2", 40.0, 350.0, 10_000, "BE-GAL-01", extended=True),
    CatalogSignal("air_knife_pressure", "kPa", 3.0, 20.0, 2_000, "BE-GAL-01", extended=True),
    CatalogSignal("strip_temperature_exit", "Cel", 200.0, 320.0, 5_000, "BE-GAL-01", extended=True),
    # --- BE-UTIL-01: Energy system (6 signals)
    CatalogSignal("site_active_power", "MW", 12.0, 55.0, 1_000, "BE-UTIL-01", extended=True),
    CatalogSignal("power_factor", "ratio", 0.90, 1.0, 5_000, "BE-UTIL-01", extended=True),
    CatalogSignal("grid_frequency", "Hz", 49.8, 50.2, 1_000, "BE-UTIL-01", extended=True),
    CatalogSignal("compressed_air_pressure", "bar", 5.5, 7.8, 2_000, "BE-UTIL-01", extended=True),
    CatalogSignal("spot_price", "EUR/MWh", -12.0, 400.0, 900_000, "BE-UTIL-01", extended=True),
    CatalogSignal("grid_carbon_intensity", "gCO2/kWh", 30.0, 280.0, 900_000, "BE-UTIL-01", extended=True),
    # --- ES-EAF-01: Electric arc furnace (4 signals)
    CatalogSignal("arc_current", "kA", 28.0, 75.0, 1_000, "ES-EAF-01", extended=True),
    CatalogSignal("bath_temperature", "Cel", 1560.0, 1690.0, 10_000, "ES-EAF-01", extended=True),
    CatalogSignal("electrode_position", "mm", 180.0, 850.0, 1_000, "ES-EAF-01", extended=True),
    CatalogSignal("tap_to_tap_time", "min", 40.0, 70.0, 60_000, "ES-EAF-01", extended=True),
    # --- ES-WRM-01: Wire rod mill (5 signals)
    CatalogSignal("stand_motor_current", "A", 800.0, 6000.0, 1_000, "ES-WRM-01", extended=True),
    CatalogSignal("rod_speed", "m/s", 30.0, 110.0, 1_000, "ES-WRM-01", extended=True),
    CatalogSignal("laying_head_temperature", "Cel", 780.0, 1050.0, 5_000, "ES-WRM-01", extended=True),
    CatalogSignal("cooling_conveyor_speed", "m/min", 10.0, 60.0, 2_000, "ES-WRM-01", extended=True),
    CatalogSignal("rod_diameter_deviation", "mm", -0.3, 0.3, 5_000, "ES-WRM-01", extended=True),
    # --- ES-UTIL-01: Energy system (5 signals)
    CatalogSignal("site_active_power", "MW", 25.0, 130.0, 1_000, "ES-UTIL-01", extended=True),
    CatalogSignal("power_factor", "ratio", 0.87, 1.0, 5_000, "ES-UTIL-01", extended=True),
    CatalogSignal("grid_frequency", "Hz", 49.8, 50.2, 1_000, "ES-UTIL-01", extended=True),
    CatalogSignal("compressed_air_pressure", "bar", 5.5, 8.0, 2_000, "ES-UTIL-01", extended=True),
    CatalogSignal("spot_price", "EUR/MWh", -5.0, 350.0, 900_000, "ES-UTIL-01", extended=True),
]

CATALOG_SIGNALS: dict[str, CatalogSignal] = {}
for _s in _CORE_SIGNALS + _EXTENDED_SIGNALS:
    _key = f"{_s.asset_id}:{_s.signal_code}"
    CATALOG_SIGNALS[_key] = _s

CORE_SIGNAL_CODES: frozenset[str] = frozenset(s.signal_code for s in _CORE_SIGNALS)

SIGNALS_BY_ASSET: dict[str, list[CatalogSignal]] = {}
for _s in list(CATALOG_SIGNALS.values()):
    SIGNALS_BY_ASSET.setdefault(_s.asset_id, []).append(_s)
