"""Reference (dimension) data export -> Fabric core-lakehouse dimensions.

This is the *third* export layer alongside the two in ``simulator/analytics.py``
(gold facts) and ``simulator/fabric_operational.py`` (operational envelopes).

The medallion ``bronze -> silver`` notebook resolves every incoming event to a
surrogate key by joining against four slowly-changing dimension tables in
``lh_novasteelv3_core`` -- ``dim_plant``, ``dim_asset``, ``dim_sensor``,
``dim_grade`` -- and quarantines the row as ``UNKNOWN_ASSET`` (rule
``DQ-REF-001``) whenever a join misses. ``ns-initialize-lakehouses`` only creates
those tables *empty*, so without this export every event is quarantined and
every silver/gold fact table stays empty.

The simulator owns this reference data because it also owns the identifiers that
appear in the generated events: the ``plant_id``/``asset_id`` estate in
``simulator/config.py`` and -- critically -- the ``sensor_id`` strings that
``simulator/generator.py`` constructs. Those construction rules are reproduced
here exactly (see ``build_sensor_rows``) so every ``sensor_id`` an event carries
has a matching ``dim_sensor`` row.

Output (mirrors the analytical export: one file per table, ``manifest.json`` and
``checksums.json``): all-string CSVs written with Python's :mod:`csv` module
(RFC 4180 quoting -- the loader ``ns-load-reference-data`` reads them with Spark
``escape='"'``), plus a deterministic run manifest and per-file checksums.

Determinism: surrogate ``*_key`` columns are stable sorted-order ordinals over
the natural key, so two runs produce byte-identical CSVs.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from simulator import GENERATOR_VERSION, config
from simulator.checksum import write_checksums
from simulator.process import rolling as rolling_model

# All slowly-changing dimensions are loaded with valid-time semantics; the
# bronze->silver join keeps a row when ``event_ts >= valid_from`` and
# ``valid_to`` is NULL. This timestamp is at or before the earliest possible
# synthetic event, so every event resolves to the INITIAL_LOAD row.
VALID_FROM = "2020-01-01T00:00:00Z"
VALID_TO = ""  # NULL -> current row of the SCD
IS_CURRENT = "true"
VERSION = "1"
CHANGE_REASON = "INITIAL_LOAD"
CALIBRATION_VERSION = "cal-1.0.0"
COMMISSIONED_STATE = "IN_SERVICE"

# Contiguous daily calendar bounds (inclusive). Comfortably brackets both the
# 24-month analytical programme and the streaming event windows.
CALENDAR_START = date(2024, 1, 1)
CALENDAR_END = date(2027, 12, 31)

FILES_SUBPATH = "reference-data"

# Natural (business) keys -- must match ns-load-reference-data.NATURAL_KEYS so
# the idempotent MERGE updates rather than duplicates on a regenerated pack.
NATURAL_KEYS: dict[str, list[str]] = {
    "dim_plant": ["plant_id", "valid_from"],
    "dim_asset": ["asset_id", "valid_from"],
    "dim_sensor": ["sensor_id", "signal_code", "valid_from"],
    "dim_grade": ["grade_code", "valid_from"],
    "dim_calendar": ["date_key", "plant_id"],
}

# Exact column order of the deployed core Delta DDL (ns-initialize-lakehouses).
COLUMNS: dict[str, list[str]] = {
    "dim_plant": [
        "plant_key", "plant_id", "plant_name", "country_code", "time_zone",
        "route", "valid_from", "valid_to", "is_current", "version", "change_reason",
    ],
    "dim_asset": [
        "asset_key", "asset_id", "plant_id", "parent_asset_id", "area", "line_id",
        "asset_type", "criticality", "commissioned_state", "valid_from", "valid_to",
        "is_current", "version", "change_reason",
    ],
    "dim_sensor": [
        "sensor_key", "sensor_id", "plant_id", "asset_id", "signal_code",
        "canonical_unit", "hard_min", "hard_max", "sample_period_ms",
        "calibration_version", "valid_from", "valid_to", "is_current", "version",
        "change_reason",
    ],
    "dim_grade": [
        "grade_key", "grade_code", "grade_family", "high_grade_flag", "target_json",
        "valid_from", "valid_to", "is_current", "version", "change_reason",
    ],
    "dim_calendar": [
        "date_key", "plant_id", "local_date", "year", "month", "iso_week",
        "day_of_week", "is_holiday",
    ],
}

REFERENCE_TABLES: tuple[str, ...] = (
    "dim_plant", "dim_asset", "dim_sensor", "dim_grade", "dim_calendar",
)

# --- config-derived lookups ------------------------------------------------- #

# ISO 3166-1 alpha-2 for the synthetic estate's four host countries.
_COUNTRY_CODE = {
    "Luxembourg": "LU", "Germany": "DE", "Belgium": "BE", "Spain": "ES",
}

# Production-stage ordering used to derive a sensible asset hierarchy: each
# asset's parent is the most-downstream asset in the same plant at an earlier
# stage. Utilities sit outside the metallurgical chain (no parent).
_AREA_STAGE = {"Ironmaking": 1, "Steelmaking": 2, "Casting": 3, "Rolling": 4}

# Criticality by asset type; primary reduction/melting units are HIGH.
_CRITICALITY = {
    "Blast furnace": "HIGH",
    "Electric arc furnace": "HIGH",
    "Basic oxygen furnace": "HIGH",
    "Slab caster": "MEDIUM",
    "Reheat furnace": "MEDIUM",
    "Hot strip mill": "MEDIUM",
    "Energy system": "LOW",
}

# Furnace hearth-sector instruments emit these signals, in this order, per
# sector (generator.py ``values`` dict in ``_generate_furnace_telemetry``). The
# sensor_id is ``f"LUX-BF-01-{signal_code.upper()[:4]}-H{sector}"``, so signals
# sharing a 4-char prefix collapse onto one physical sensor_id:
#   HEAR <- hearth_shell_temperature (+ hearth_refractory_estimate)
#   COOL <- cooling_water_inlet_temperature (+ _outlet_ + _flow)
#   LOCA <- local_heat_flux
# First-wins in this order picks the canonical signal_code/unit for each.
_FURNACE_SECTOR_SIGNAL_ORDER = (
    "hearth_shell_temperature",
    "cooling_water_inlet_temperature",
    "cooling_water_outlet_temperature",
    "cooling_water_flow",
    "local_heat_flux",
    "hearth_refractory_estimate",
)
_FURNACE_ASSET_ID = "LUX-BF-01"

# Rolling stands each emit stand_motor_current (A), rolling_force (MW) and
# strip_speed (m/s) under a single sensor_id ``f"{asset_id}-{stand_id}"``, so the
# registry grain is (sensor_id, signal_code). The coiling pyrometer is a
# dedicated sensor. (generator.py ``_generate_rolling_telemetry``.)
_ROLLING_ASSET_ID = "LUX-HSM-01"
_ROLLING_STAND_SIGNALS = ("stand_motor_current", "rolling_force", "strip_speed")
_COILING_SENSOR_SUFFIX = "COIL-TC-01"
_COILING_SIGNAL = "coiling_temperature"


class ReferenceDataError(ValueError):
    pass


@dataclass
class ReferenceRunResult:
    out_dir: Path
    tables: dict = field(default_factory=dict)
    file_paths: dict = field(default_factory=dict)
    row_counts: dict = field(default_factory=dict)
    run_manifest_path: Path | None = None
    checksums: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Cell formatting / CSV writer                                                #
# --------------------------------------------------------------------------- #

def _fmt(value) -> str:
    """Format one cell as the loader expects: lowercase booleans, empty for
    NULL, plain text otherwise."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _write_csv(path: Path, table_name: str, rows: list[dict]) -> None:
    columns = COLUMNS[table_name]
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="" is required by csv; lineterminator="\n" keeps a run
    # byte-identical across Windows and Linux (these bytes are checksummed).
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow([_fmt(row.get(col)) for col in columns])


def _scd_fields() -> dict:
    return {
        "valid_from": VALID_FROM,
        "valid_to": VALID_TO,
        "is_current": IS_CURRENT,
        "version": VERSION,
        "change_reason": CHANGE_REASON,
    }


def _assign_keys(rows: list[dict], key_column: str, *natural_key: str) -> None:
    """Assign a stable, deterministic surrogate key: the 1-based ordinal of the
    row's natural key in sorted order."""
    ordered = sorted(rows, key=lambda r: tuple(r[column] for column in natural_key))
    for ordinal, row in enumerate(ordered, start=1):
        row[key_column] = ordinal


# --------------------------------------------------------------------------- #
# Dimension builders                                                          #
# --------------------------------------------------------------------------- #

def build_plant_rows() -> list[dict]:
    rows: list[dict] = []
    for plant in config.PLANTS.values():
        route = "BF-BOF" if "blast furnace" in plant.process_focus.lower() else "EAF"
        rows.append({
            "plant_id": plant.plant_id,
            "plant_name": plant.name,
            "country_code": _COUNTRY_CODE.get(plant.country, plant.country),
            "time_zone": plant.time_zone,
            "route": route,
            **_scd_fields(),
        })
    _assign_keys(rows, "plant_key", "plant_id")
    return rows


def build_asset_rows() -> list[dict]:
    by_plant: dict[str, list] = {}
    for asset in config.ASSETS.values():
        by_plant.setdefault(asset.plant_id, []).append(asset)

    rows: list[dict] = []
    for asset in config.ASSETS.values():
        stage = _AREA_STAGE.get(asset.area)
        parent_asset_id = ""
        if stage is not None:
            # Most-downstream same-plant asset at an earlier stage.
            candidates = [
                other for other in by_plant[asset.plant_id]
                if _AREA_STAGE.get(other.area) is not None
                and _AREA_STAGE[other.area] < stage
            ]
            if candidates:
                parent = max(candidates, key=lambda a: (_AREA_STAGE[a.area], a.asset_id))
                # Break same-stage ties toward the lowest asset_id.
                best_stage = _AREA_STAGE[parent.area]
                parent = min(
                    (a for a in candidates if _AREA_STAGE[a.area] == best_stage),
                    key=lambda a: a.asset_id,
                )
                parent_asset_id = parent.asset_id
        line_id = "" if asset.area == "Utilities" else asset.asset_id
        rows.append({
            "asset_id": asset.asset_id,
            "plant_id": asset.plant_id,
            "parent_asset_id": parent_asset_id,
            "area": asset.area,
            "line_id": line_id,
            "asset_type": asset.asset_type,
            "criticality": _CRITICALITY.get(asset.asset_type, "MEDIUM"),
            "commissioned_state": COMMISSIONED_STATE,
            **_scd_fields(),
        })
    _assign_keys(rows, "asset_key", "asset_id")
    return rows


def _sensor_row(sensor_id: str, plant_id: str, asset_id: str, signal_code: str) -> dict:
    signal = config.SIGNAL_REGISTRY[signal_code]
    return {
        "sensor_id": sensor_id,
        "plant_id": plant_id,
        "asset_id": asset_id,
        "signal_code": signal_code,
        "canonical_unit": signal.unit,
        "hard_min": signal.low,
        "hard_max": signal.high,
        "sample_period_ms": signal.sample_period_ms,
        "calibration_version": CALIBRATION_VERSION,
        **_scd_fields(),
    }


def build_sensor_rows() -> list[dict]:
    """Reproduce every ``sensor_id`` construction rule from generator.py.

    The generator truncates the signal code to four characters when it builds a
    furnace sensor_id (``LUX-BF-01-COOL-H07``), so one sensor_id legitimately
    carries several signals with different canonical units. The registry grain is
    therefore (sensor_id, signal_code): one calibration row per measured channel.

    All furnace/rolling telemetry is emitted for the Luxembourg estate assets
    (``LUX-BF-01`` / ``LUX-HSM-01``) regardless of scenario plant, so the
    sensors are plant-independent; the LUX plant owns them.
    """
    plant_id = config.ASSETS[_FURNACE_ASSET_ID].plant_id
    seen: dict[tuple[str, str], dict] = {}

    def add(sensor_id: str, asset_id: str, signal_code: str) -> None:
        seen.setdefault(
            (sensor_id, signal_code),
            _sensor_row(sensor_id, plant_id, asset_id, signal_code),
        )

    # 1. Furnace hearth-sector instruments (all 12 sectors, superset of any
    #    single scenario's active sectors).
    for sector in config.HEARTH_SECTORS:
        for signal_code in _FURNACE_SECTOR_SIGNAL_ORDER:
            add(f"{_FURNACE_ASSET_ID}-{signal_code.upper()[:4]}-H{sector}",
                _FURNACE_ASSET_ID, signal_code)

    # 2. Rolling-mill stands (three channels per stand, one sensor_id).
    for stand_id in rolling_model.STAND_IDS:
        for signal_code in _ROLLING_STAND_SIGNALS:
            add(f"{_ROLLING_ASSET_ID}-{stand_id}", _ROLLING_ASSET_ID, signal_code)

    # 3. Coiling-line thermocouple.
    add(f"{_ROLLING_ASSET_ID}-{_COILING_SENSOR_SUFFIX}", _ROLLING_ASSET_ID, _COILING_SIGNAL)

    rows = list(seen.values())
    _assign_keys(rows, "sensor_key", "sensor_id", "signal_code")
    return rows


def _grade_target_json(grade_code: str, grade_family: str, high_grade: bool) -> str:
    """Versioned specification targets for the grade (dim_grade.target_json is
    NOT NULL). Deterministic: sorted keys, compact separators."""
    characteristics = {
        code: {"unit": unit, "lower_spec_limit": lsl, "upper_spec_limit": usl}
        for code, (unit, lsl, usl) in config.QUALITY_CHARACTERISTICS.items()
    }
    payload = {
        "spec_version": 1,
        "grade_family": grade_family,
        "high_grade": high_grade,
        "characteristics": characteristics,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def build_grade_rows() -> list[dict]:
    rows: list[dict] = []
    for grade_code in config.GRADES:
        # Family/high-grade derived from the grade code namespace:
        # NS-AUTO-* are high-grade automotive sheet; NS-LONG-* are long products.
        high_grade = grade_code.startswith("NS-AUTO-")
        grade_family = "automotive" if high_grade else "long"
        rows.append({
            "grade_code": grade_code,
            "grade_family": grade_family,
            "high_grade_flag": high_grade,
            "target_json": _grade_target_json(grade_code, grade_family, high_grade),
            **_scd_fields(),
        })
    _assign_keys(rows, "grade_key", "grade_code")
    return rows


def build_calendar_rows() -> list[dict]:
    """One contiguous daily row per (date, plant) across all four plants."""
    plant_ids = sorted(config.PLANTS)
    rows: list[dict] = []
    day = CALENDAR_START
    while day <= CALENDAR_END:
        iso_year, iso_week, iso_weekday = day.isocalendar()
        iso_date = day.isoformat()
        for plant_id in plant_ids:
            rows.append({
                "date_key": iso_date,
                "plant_id": plant_id,
                "local_date": iso_date,
                "year": day.year,
                "month": day.month,
                "iso_week": iso_week,
                "day_of_week": iso_weekday,
                "is_holiday": False,
            })
        day += timedelta(days=1)
    return rows


def build_tables() -> dict[str, list[dict]]:
    return {
        "dim_plant": build_plant_rows(),
        "dim_asset": build_asset_rows(),
        "dim_sensor": build_sensor_rows(),
        "dim_grade": build_grade_rows(),
        "dim_calendar": build_calendar_rows(),
    }


# --------------------------------------------------------------------------- #
# Orchestration                                                               #
# --------------------------------------------------------------------------- #

def export_reference_data(out_dir: Path) -> ReferenceRunResult:
    """Build every dimension and write the CSV pack + manifest + checksums."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tables = build_tables()
    file_paths: dict[str, Path] = {}
    row_counts: dict[str, int] = {}
    for name in REFERENCE_TABLES:
        path = out_dir / f"{name}.csv"
        _write_csv(path, name, tables[name])
        file_paths[name] = path
        row_counts[name] = len(tables[name])

    run_manifest = {
        "kind": "reference-data",
        "generator_version": GENERATOR_VERSION,
        "child_seed_derivation_version": 1,
        "data_classification": config.DATA_CLASSIFICATION,
        "privacy_label": config.PRIVACY_LABEL,
        "entity_prefix": config.ENTITY_PREFIX,
        "files_subpath": FILES_SUBPATH,
        "valid_from": VALID_FROM,
        "calendar_start": CALENDAR_START.isoformat(),
        "calendar_end": CALENDAR_END.isoformat(),
        "tables": list(REFERENCE_TABLES),
        "natural_keys": NATURAL_KEYS,
        "columns": COLUMNS,
        "row_counts": row_counts,
    }
    run_manifest_path = out_dir / "manifest.json"
    with run_manifest_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(run_manifest, indent=2, sort_keys=True))

    filenames = [p.name for p in file_paths.values()] + ["manifest.json"]
    write_checksums(out_dir, filenames)
    checksums = json.loads((out_dir / "checksums.json").read_text(encoding="utf-8"))

    return ReferenceRunResult(
        out_dir=out_dir, tables=tables, file_paths=file_paths, row_counts=row_counts,
        run_manifest_path=run_manifest_path, checksums=checksums,
    )
