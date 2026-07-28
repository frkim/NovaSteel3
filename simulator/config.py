"""Static reference/configuration data for the NovaSteel synthetic estate.

Mirrors ``docs/data/synthetic-data-and-simulators.md`` sections 1-3: plants,
asset hierarchy, and the signal registry (unit, plausible range, and
sampling period) used by the process/observation models. This module
contains no live logic -- it is the "reference data" fed into the
deterministic generation pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field

DATA_CLASSIFICATION = "SYNTHETIC"
PRIVACY_LABEL = "DEMO-NONPERSONAL"
ENTITY_PREFIX = "NS-DEMO-"

ROOT_SEED = 240725

SCENARIO_SEEDS = {
    "healthy-baseline": 240725,
    "lining-degradation-21d": 240726,
    "energy-price-spike": 240727,
    "quality-drift": 240728,
    "edge-outage-recovery": 240729,
    "demo-full": 240725,
    "energy-eaf-flex": 240730,
}


@dataclass(frozen=True)
class Plant:
    plant_id: str
    name: str
    country: str
    time_zone: str
    process_focus: str


@dataclass(frozen=True)
class Asset:
    asset_id: str
    plant_id: str
    area: str
    asset_type: str


PLANTS = {
    p.plant_id: p
    for p in [
        Plant("NS-DEMO-LUX-01", "Moselle Integrated Works", "Luxembourg",
              "Europe/Luxembourg", "Blast furnace, basic oxygen furnace, hot strip mill"),
        Plant("NS-DEMO-DE-01", "Rhine Flat Products", "Germany",
              "Europe/Berlin", "Reheat furnace, hot/cold rolling, galvanizing"),
        Plant("NS-DEMO-BE-01", "Meuse Melt Shop", "Belgium",
              "Europe/Brussels", "Electric arc furnace, caster"),
        Plant("NS-DEMO-ES-01", "Ebro Long Products", "Spain",
              "Europe/Madrid", "Electric arc furnace, billet caster, bar mill"),
    ]
}

DEFAULT_PLANT_ID = "NS-DEMO-LUX-01"

ASSETS = {
    a.asset_id: a
    for a in [
        Asset("LUX-BF-01", "NS-DEMO-LUX-01", "Ironmaking", "Blast furnace"),
        Asset("LUX-BOF-01", "NS-DEMO-LUX-01", "Steelmaking", "Basic oxygen furnace"),
        Asset("LUX-CC-01", "NS-DEMO-LUX-01", "Casting", "Slab caster"),
        Asset("LUX-RHF-01", "NS-DEMO-LUX-01", "Rolling", "Reheat furnace"),
        Asset("LUX-HSM-01", "NS-DEMO-LUX-01", "Rolling", "Hot strip mill"),
        Asset("LUX-UTIL-01", "NS-DEMO-LUX-01", "Utilities", "Energy system"),
        Asset("BE-EAF-01", "NS-DEMO-BE-01", "Steelmaking", "Electric arc furnace"),
        Asset("BE-UTIL-01", "NS-DEMO-BE-01", "Utilities", "Energy system"),
    ]
}

# Hearth lining sectors modeled explicitly for LUX-BF-01 (section 2.2/8.1).
HEARTH_SECTORS = [f"{i:02d}" for i in range(1, 13)]
DEGRADED_SECTOR = "07"


@dataclass(frozen=True)
class Signal:
    """One row of the sensor/signal registry (docs section 3.2-3.4)."""

    signal_code: str
    unit: str
    low: float
    high: float
    sample_period_ms: int
    asset_id: str


SIGNAL_REGISTRY = {
    s.signal_code: s
    for s in [
        Signal("hearth_shell_temperature", "Cel", 75, 185, 5_000, "LUX-BF-01"),
        Signal("cooling_water_inlet_temperature", "Cel", 20, 36, 5_000, "LUX-BF-01"),
        Signal("cooling_water_outlet_temperature", "Cel", 28, 58, 5_000, "LUX-BF-01"),
        Signal("cooling_water_flow", "m3/h", 110, 310, 5_000, "LUX-BF-01"),
        Signal("local_heat_flux", "kW/m2", 35, 190, 5_000, "LUX-BF-01"),
        Signal("hearth_refractory_estimate", "mm", 280, 950, 900_000, "LUX-BF-01"),
        Signal("hot_blast_temperature", "Cel", 1050, 1250, 10_000, "LUX-BF-01"),
        Signal("top_pressure", "bar", 1.4, 2.6, 1_000, "LUX-BF-01"),
        Signal("pulverized_coal_injection", "kg/t", 100, 190, 60_000, "LUX-BF-01"),
        Signal("hot_metal_temperature", "Cel", 1440, 1530, 0, "LUX-BF-01"),
        Signal("production_rate", "t/h", 180, 360, 60_000, "LUX-BF-01"),
        # Rolling mill (section 3.3), attached to LUX-HSM-01.
        Signal("reheat_zone_temperature", "Cel", 850, 1285, 2_000, "LUX-RHF-01"),
        Signal("furnace_gas_flow", "m3/h", 4000, 42000, 2_000, "LUX-RHF-01"),
        Signal("furnace_excess_o2", "%", 0.8, 4.5, 2_000, "LUX-RHF-01"),
        Signal("stand_motor_current", "A", 1000, 12000, 1_000, "LUX-HSM-01"),
        Signal("rolling_force", "MW", 4, 38, 1_000, "LUX-HSM-01"),
        Signal("strip_speed", "m/s", 0.2, 22, 1_000, "LUX-HSM-01"),
        Signal("coiling_temperature", "Cel", 520, 720, 0, "LUX-HSM-01"),
    ]
}

# Hearth-sector-scoped thermocouples/heat-flux/cooling instruments (docs 2.2).
FURNACE_SECTOR_SIGNALS = [
    "hearth_shell_temperature",
    "cooling_water_inlet_temperature",
    "cooling_water_outlet_temperature",
    "cooling_water_flow",
    "local_heat_flux",
]

UCUM_UNITS = {
    "Cel", "bar", "m3/h", "kW/m2", "MW", "MWh", "EUR/MWh", "kg/t", "mm", "A",
    "%", "t/h", "m/s", "d", "kgCO2e/MWh", "kgCO2e/t", "MPa", "1",
}

# Closed "type" discriminator enum shared with the canonical wire contract
# (contracts/events/telemetry.v1.schema.json), agreed with the
# application-foundation workstream: a rich signal-level payload (sensor_id,
# signal_code, quality, uncertainty, sample_period_ms, ...) still carries
# this coarse `type` field so consumers can route without parsing signal_code.
TELEMETRY_EVENT_TYPES = {
    "telemetry.furnace.thermal", "telemetry.rolling.mill", "energy.interval", "quality.measurement",
}

FURNACE_TELEMETRY_SIGNALS = {
    "hearth_shell_temperature", "cooling_water_inlet_temperature",
    "cooling_water_outlet_temperature", "cooling_water_flow", "local_heat_flux",
    "hearth_refractory_estimate", "hot_blast_temperature", "top_pressure",
    "pulverized_coal_injection", "hot_metal_temperature", "production_rate",
    "reheat_zone_temperature", "furnace_gas_flow", "furnace_excess_o2",
}
ROLLING_TELEMETRY_SIGNALS = {
    "stand_motor_current", "rolling_force", "strip_speed", "coiling_temperature",
}


def telemetry_event_type(signal_code: str) -> str:
    """Map a signal_code to the closed `type` discriminator."""
    if signal_code in ROLLING_TELEMETRY_SIGNALS:
        return "telemetry.rolling.mill"
    return "telemetry.furnace.thermal"


QUALITY_CHARACTERISTICS = {
    "tensile_strength": ("MPa", 780.0, 930.0),
    "yield_strength": ("MPa", 450.0, 620.0),
    "elongation": ("%", 12.0, 20.0),
    "coiling_temperature_actual": ("Cel", 520.0, 720.0),
    "carbon_equivalent": ("%", 0.30, 0.45),
    "flatness": ("1", -20.0, 20.0),
}

GRADES = {
    "NS-AUTO-DP780": "Automotive dual-phase sheet",
    "NS-AUTO-HSLA420": "Automotive structural sheet",
    "NS-LONG-B500": "Reinforcing bar",
}

FAILURE_MODES = [
    "refractory_wear",
    "cooling_circuit_restriction",
    "bearing_vibration",
    "roll_wear",
    "burner_imbalance",
    "thermocouple_bias",
    "hydraulic_leakage",
]

MAINTENANCE_NOTE_TEMPLATES = [
    "Demo inspection found localized warm zone near hearth sector {sector}; "
    "verify circuit flow and schedule ultrasound survey.",
    "Demo condition check flagged rising vibration RMS on {asset}; "
    "recommend bearing inspection at next planned stop.",
    "Demo review of cooling circuit on {asset} shows reduced flow margin; "
    "schedule strainer cleaning.",
    "Demo thermocouple drift detected on {asset}; recommend calibration check.",
]

OPERATOR_ROLES = ["Furnace Operator", "Process Engineer", "Maintenance Engineer"]

KNOWLEDGE_FACT_TEMPLATES = [
    {
        "trigger": "hearth shell temperature rising near sector {sector}",
        "observation": "Localized warm patch observed on sector {sector} shell plating.",
        "action": "Increase cooling-circuit monitoring frequency and request ultrasound survey.",
        "rationale": "Sustained local rise combined with falling cooling efficiency is an early "
        "refractory-wear signature in the synthetic operating envelope.",
        "cautions": "Synthetic training draft; requires expert review before use as a work instruction.",
    },
    {
        "trigger": "day-ahead price interval flagged as scarcity",
        "observation": "Spot price forecast exceeds the demo scarcity threshold.",
        "action": "Evaluate eligible reheat batches for a bounded schedule shift within hold-time limits.",
        "rationale": "Shifting non-urgent batches earlier reduces displayed peak demand cost without "
        "changing committed tonnage.",
        "cautions": "Synthetic training draft; scheduling changes must respect approved windows only.",
    },
]

CLOCK_MODES = {"real", "accelerated", "paused", "replay"}
CONNECTIVITY_STATES = {"ONLINE", "DEGRADED", "OFFLINE", "RECOVERING"}
QUALITY_FLAGS = {"GOOD", "UNCERTAIN", "BAD", "STALE", "SUBSTITUTED"}
ALERT_STATES = ["OPEN", "ACKNOWLEDGED", "WORK_ORDER_LINKED", "MITIGATED", "CLOSED"]
