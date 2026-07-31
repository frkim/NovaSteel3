# Fabric notebook source

# METADATA ********************
# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************
# Loader for the *reference* (dimension) data that the medallion pipeline joins
# every event against.
#
# ns-bronze-to-silver resolves each event to a surrogate key via dim_plant,
# dim_asset, dim_sensor and dim_grade, and quarantines the row as UNKNOWN_ASSET
# (rule DQ-REF-001) when any of those joins misses. ns-initialize-lakehouses
# only creates those tables empty, so without this loader every event is
# quarantined and every silver/gold fact table stays empty.
#
# The simulator owns the reference data, because it also owns the identifiers
# that appear in the generated events:
#
#     python -m simulator generate-reference
#
# tools/fabric/Load-AnalyticalGold.ps1 (with -Layer reference) uploads the CSVs
# to OneLake `Files/reference-data/`; this notebook casts them to the deployed
# core Delta DDL and MERGEs them on their natural key. The load is idempotent:
# re-running it updates matched rows in place and inserts nothing new.
from datetime import datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

# Deployment tokens (resolved by .azure/fabric/Deploy-NovaSteelV3FabricAssets.ps1).
ENVIRONMENT = "{{environment}}"
CORE_TABLES_URI = "{{onelake.coreTablesUri}}"
FILES_SUBPATH = "reference-data"

TIMESTAMP_FORMAT = "yyyy-MM-dd'T'HH:mm:ss'Z'"

# Natural keys used for the idempotent MERGE. These are the business keys, not
# the surrogate *_key columns, so a regenerated pack with the same identifiers
# updates rather than duplicates.
NATURAL_KEYS = {
    "dim_plant": ["plant_id", "valid_from"],
    "dim_asset": ["asset_id", "valid_from"],
    "dim_sensor": ["sensor_id", "signal_code", "valid_from"],
    "dim_grade": ["grade_code", "valid_from"],
    "dim_calendar": ["date_key", "plant_id"],
}

# Per-column casts from the all-string CSV to the deployed core Delta DDL in
# ns-initialize-lakehouses. "date"/"ts" go through explicit format parsing;
# everything else is a plain Spark cast.
CASTS = {
    "dim_plant": {
        "plant_key": "long", "plant_id": "string", "plant_name": "string",
        "country_code": "string", "time_zone": "string", "route": "string",
        "valid_from": "ts", "valid_to": "ts", "is_current": "boolean",
        "version": "int", "change_reason": "string"},
    "dim_asset": {
        "asset_key": "long", "asset_id": "string", "plant_id": "string",
        "parent_asset_id": "string", "area": "string", "line_id": "string",
        "asset_type": "string", "criticality": "string", "commissioned_state": "string",
        "valid_from": "ts", "valid_to": "ts", "is_current": "boolean",
        "version": "int", "change_reason": "string"},
    "dim_sensor": {
        "sensor_key": "long", "sensor_id": "string", "plant_id": "string",
        "asset_id": "string", "signal_code": "string", "canonical_unit": "string",
        "hard_min": "double", "hard_max": "double", "sample_period_ms": "long",
        "calibration_version": "string", "valid_from": "ts", "valid_to": "ts",
        "is_current": "boolean", "version": "int", "change_reason": "string"},
    "dim_grade": {
        "grade_key": "long", "grade_code": "string", "grade_family": "string",
        "high_grade_flag": "boolean", "target_json": "string", "valid_from": "ts",
        "valid_to": "ts", "is_current": "boolean", "version": "int",
        "change_reason": "string"},
    "dim_calendar": {
        "date_key": "date", "plant_id": "string", "local_date": "date", "year": "int",
        "month": "int", "iso_week": "int", "day_of_week": "int", "is_holiday": "boolean"},
}


def require_resolved(name: str, value: str) -> None:
    if not value or value.startswith("{{"):
        raise ValueError(f"{name} must be resolved to an environment value")


def core_files_uri() -> str:
    # Files and Tables are sibling roots under a lakehouse item in OneLake.
    return CORE_TABLES_URI.rstrip("/")[: -len("/Tables")] + "/Files"


def table_path(table_name: str) -> str:
    return f"{CORE_TABLES_URI.rstrip('/')}/{table_name}"


def files_path(table_name: str) -> str:
    return f"{core_files_uri()}/{FILES_SUBPATH}/{table_name}.csv"


def cast_frame(raw: DataFrame, table_name: str) -> DataFrame:
    exprs = []
    for column, kind in CASTS[table_name].items():
        col = F.col(column)
        if kind == "date":
            expr = F.to_date(col)
        elif kind == "ts":
            expr = F.to_timestamp(col, TIMESTAMP_FORMAT)
        else:
            # Empty CSV cells become NULL before the cast so numeric/boolean
            # nullable columns parse cleanly.
            expr = F.when(col == F.lit(""), F.lit(None)).otherwise(col).cast(kind)
        exprs.append(expr.alias(column))
    return raw.select(*exprs)


def upsert(frame: DataFrame, table_name: str, keys) -> int:
    source = frame.dropDuplicates(list(keys))
    target_path = table_path(table_name)
    if not DeltaTable.isDeltaTable(spark, target_path):
        source.write.format("delta").mode("overwrite").save(target_path)
        return source.count()
    # `<=>` is null-safe: valid_to is NULL for the current row of every
    # slowly-changing dimension, and `=` would never match it.
    condition = " AND ".join([f"target.`{k}` <=> source.`{k}`" for k in keys])
    (
        DeltaTable.forPath(spark, target_path)
        .alias("target")
        .merge(source.alias("source"), condition)
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    return source.count()


require_resolved("ENVIRONMENT", ENVIRONMENT)
require_resolved("CORE_TABLES_URI", CORE_TABLES_URI)
_ENV_ALLOWED_SUFFIXES = ("dev", "test", "demo")
_env_normalized = ENVIRONMENT.strip().lower()
if not any(_env_normalized == t or _env_normalized.endswith("-" + t) for t in _ENV_ALLOWED_SUFFIXES):
    raise ValueError(
        "Reference demo-data load is hard-disabled outside dev/test/demo "
        f"(got ENVIRONMENT={ENVIRONMENT!r})"
    )

written = {}
failures = {}
for table_name, keys in NATURAL_KEYS.items():
    source_path = files_path(table_name)
    try:
        # `escape` must be the double-quote: the packs are written by Python's
        # csv.writer, which escapes a quote inside a quoted field by doubling
        # it (RFC 4180), whereas Spark defaults `escape` to a backslash.
        raw = (
            spark.read.option("header", True)
            .option("quote", '"')
            .option("escape", '"')
            .option("mode", "FAILFAST")
            .csv(source_path)
        )
        frame = cast_frame(raw, table_name)
        written[table_name] = upsert(frame, table_name, keys)
    except Exception as exc:  # noqa: BLE001 - surface a clear per-table message
        detail = f"{exc.__class__.__name__}: {exc}"
        failures[table_name] = detail
        written[table_name] = f"failed ({exc.__class__.__name__})"

# Persist the per-table outcome so it can be read straight from OneLake: the
# Fabric Jobs API only reports a generic session-cancelled error with no Python
# detail when a statement raises.
audit_rows = [
    (
        table_name,
        "failed" if table_name in failures else "loaded",
        int(written[table_name]) if isinstance(written[table_name], int) else None,
        failures.get(table_name, "")[:4000],
        datetime.now(timezone.utc).isoformat(),
    )
    for table_name in NATURAL_KEYS
]
spark.createDataFrame(
    audit_rows,
    "table_name string, status string, row_count long, error string, recorded_at string",
).write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(
    table_path("reference_load_audit")
)

print(
    {
        "status": "loaded" if not failures else "partial",
        "environment": ENVIRONMENT,
        "files_subpath": FILES_SUBPATH,
        "core_files_uri": core_files_uri(),
        "written": written,
        "failures": failures,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
)

if failures:
    raise RuntimeError(
        f"Reference data load failed for {sorted(failures)}; see reference_load_audit"
    )

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
