# Fabric notebook source

# METADATA ********************
# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************
# Materialize the purpose-built serving tables that a Fabric IQ Ontology item
# binds to. The ontology graph has strict physical requirements that the
# medallion silver/gold tables do not satisfy directly:
#
#   * time-series timestamps must be a real Spark TimestampType, never a string
#     (fact_telemetry.event_ts is an ISO-8601 STRING in silver and must be cast);
#   * entity key columns must be a single non-null String (or integer) column,
#     unique per row (dim_sensor is keyed on the PAIR (sensor_id, signal_code),
#     so a composite single-column sensor_uid key is synthesized here);
#   * column names must be plain snake_case (alphanumeric + underscore) so Delta
#     column mapping is never silently enabled, because the graph cannot read a
#     column-mapped table;
#   * the tables must be MANAGED Delta tables in the default schema.
#
# These are derived serving tables: a full rebuild each run is correct and
# simplest, so every table is written with overwrite + overwriteSchema. The
# whole contract (table names and column names) is FROZEN because the ontology
# definition is authored against exactly these names in a separate workstream.
from datetime import datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

# Deployment tokens (resolved by .azure/fabric/Deploy-NovaSteelV3FabricAssets.ps1).
ENVIRONMENT = "{{environment}}"
CORE_TABLES_URI = "{{onelake.coreTablesUri}}"

# Candidate formats tried, in order, when casting the silver STRING event_ts to a
# real timestamp. Plain .cast("timestamp") / the default to_timestamp already
# parse offset-bearing ISO-8601, but the explicit fallbacks keep the cast robust
# against the trailing-Z and space-separated variants the simulator can emit.
TS_FORMATS = (
    "yyyy-MM-dd'T'HH:mm:ss'Z'",
    "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'",
    "yyyy-MM-dd'T'HH:mm:ssXXX",
    "yyyy-MM-dd'T'HH:mm:ss.SSSXXX",
    "yyyy-MM-dd HH:mm:ss",
)


def require_resolved(name: str, value: str) -> None:
    if not value or value.startswith("{{"):
        raise ValueError(f"{name} must be resolved to an environment value")


def path(table_name: str) -> str:
    return f"{CORE_TABLES_URI.rstrip('/')}/{table_name}"


def read(table_name: str) -> DataFrame:
    return spark.read.format("delta").load(path(table_name))


def current_rows(table_name: str) -> DataFrame:
    # Every dim_* is SCD2; only the current version is contextualized.
    return read(table_name).filter(F.col("is_current") == F.lit(True))


def robust_timestamp(column: str):
    # Default parse first (handles offset-bearing ISO-8601), then explicit
    # fallbacks. coalesce keeps the first non-null so a mixed batch still parses.
    candidates = [F.to_timestamp(F.col(column))]
    candidates += [F.to_timestamp(F.col(column), fmt) for fmt in TS_FORMATS]
    return F.coalesce(*candidates)


def sensor_uid(sensor_id_col: str = "sensor_id", signal_code_col: str = "signal_code"):
    # dim_sensor is keyed on the (sensor_id, signal_code) pair; the ontology
    # needs a single-column entity key. concat returns null if either part is
    # null, which the downstream null check then drops.
    return F.concat(
        F.col(sensor_id_col).cast("string"),
        F.lit("|"),
        F.col(signal_code_col).cast("string"),
    )


def write_managed(frame: DataFrame, table_name: str) -> int:
    (
        frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(path(table_name))
    )
    return spark.read.format("delta").load(path(table_name)).count()


require_resolved("ENVIRONMENT", ENVIRONMENT)
require_resolved("CORE_TABLES_URI", CORE_TABLES_URI)

row_counts = {}
notes = {}

# 1. onto_plant (static entity, key plant_id) ------------------------------------
onto_plant = (
    current_rows("dim_plant")
    .select(
        F.col("plant_id").cast("string").alias("plant_id"),
        F.col("plant_name").cast("string").alias("plant_name"),
        F.col("country_code").cast("string").alias("country_code"),
        F.col("time_zone").cast("string").alias("time_zone"),
        F.col("route").cast("string").alias("route"),
    )
    .filter(F.col("plant_id").isNotNull())
    .dropDuplicates(["plant_id"])
)
row_counts["onto_plant"] = write_managed(onto_plant, "onto_plant")

# 2. onto_asset (static entity, key asset_id) ------------------------------------
onto_asset = (
    current_rows("dim_asset")
    .select(
        F.col("asset_id").cast("string").alias("asset_id"),
        F.col("plant_id").cast("string").alias("plant_id"),
        F.col("asset_type").cast("string").alias("asset_type"),
        F.col("area").cast("string").alias("area"),
        F.col("line_id").cast("string").alias("line_id"),
        F.col("criticality").cast("string").alias("criticality"),
        F.col("commissioned_state").cast("string").alias("commissioned_state"),
    )
    .filter(F.col("asset_id").isNotNull())
    .dropDuplicates(["asset_id"])
)
row_counts["onto_asset"] = write_managed(onto_asset, "onto_asset")

# 3. onto_sensor (static entity, key sensor_uid) ---------------------------------
onto_sensor = (
    current_rows("dim_sensor")
    .select(
        sensor_uid().alias("sensor_uid"),
        F.col("sensor_id").cast("string").alias("sensor_id"),
        F.col("signal_code").cast("string").alias("signal_code"),
        F.col("asset_id").cast("string").alias("asset_id"),
        F.col("plant_id").cast("string").alias("plant_id"),
        F.col("canonical_unit").cast("string").alias("canonical_unit"),
        F.col("hard_min").cast("double").alias("hard_min"),
        F.col("hard_max").cast("double").alias("hard_max"),
        F.col("sample_period_ms").cast("bigint").alias("sample_period_ms"),
    )
    .filter(F.col("sensor_uid").isNotNull())
    .dropDuplicates(["sensor_uid"])
)
row_counts["onto_sensor"] = write_managed(onto_sensor, "onto_sensor")

# 4. onto_grade (static entity, key grade_code) ----------------------------------
onto_grade = (
    current_rows("dim_grade")
    .select(
        F.col("grade_code").cast("string").alias("grade_code"),
        F.col("grade_family").cast("string").alias("grade_family"),
        F.col("high_grade_flag").cast("boolean").alias("high_grade_flag"),
    )
    .filter(F.col("grade_code").isNotNull())
    .dropDuplicates(["grade_code"])
)
row_counts["onto_grade"] = write_managed(onto_grade, "onto_grade")

# 5. onto_sensor_reading (time series for Sensor) --------------------------------
telemetry_raw = read("fact_telemetry")
_telemetry_total = telemetry_raw.count()
onto_sensor_reading = (
    telemetry_raw.select(
        sensor_uid().alias("sensor_uid"),
        robust_timestamp("event_ts").alias("reading_ts"),
        F.col("value").cast("double").alias("reading_value"),
        F.col("unit").cast("string").alias("reading_unit"),
        F.col("source_quality").cast("string").alias("source_quality"),
    ).filter(F.col("reading_ts").isNotNull() & F.col("sensor_uid").isNotNull())
)
row_counts["onto_sensor_reading"] = write_managed(onto_sensor_reading, "onto_sensor_reading")
notes["onto_sensor_reading_source_rows"] = int(_telemetry_total)
notes["onto_sensor_reading_dropped"] = int(_telemetry_total - row_counts["onto_sensor_reading"])

# 6. onto_asset_health (time series for Asset) -----------------------------------
onto_asset_health = read("fact_furnace_rul").select(
    F.col("asset_id").cast("string").alias("asset_id"),
    F.col("scored_at").cast("timestamp").alias("scored_at"),
    F.col("rul_days_p50").cast("double").alias("rul_days"),
    F.col("rul_days_p10").cast("double").alias("rul_days_low"),
    F.col("rul_days_p90").cast("double").alias("rul_days_high"),
    F.col("risk_score").cast("double").alias("risk_score"),
    F.col("confidence").cast("double").alias("confidence"),
)
row_counts["onto_asset_health"] = write_managed(onto_asset_health, "onto_asset_health")

# 7. onto_plant_daily (time series for Plant) ------------------------------------
# Outer-join the daily energy and emissions facts and the shift production fact
# (aggregated to plant/day) so a day present in only one source still appears.
# The list-column join form coalesces the join keys, so there is exactly one
# plant_id / date_key pair per output row.
energy = read("fact_energy_daily").select(
    F.col("date_key"),
    F.col("plant_id"),
    F.col("energy_gj").cast("double").alias("energy_gj"),
    F.col("electricity_mwh").cast("double").alias("electricity_mwh"),
    F.col("energy_cost_eur").cast("double").alias("energy_cost_eur"),
    F.col("crude_steel_tons").cast("double").alias("crude_steel_tons_energy"),
)
emissions = read("fact_emissions_daily").select(
    F.col("date_key"),
    F.col("plant_id"),
    F.col("total_co2e_t").cast("double").alias("total_co2e_t"),
    F.col("crude_steel_tons").cast("double").alias("crude_steel_tons_emis"),
)
production = (
    read("fact_production_shift")
    .groupBy(F.col("shift_date").alias("date_key"), F.col("plant_id"))
    .agg(F.sum(F.col("good_tons").cast("double")).alias("good_tons"))
)

plant_daily_joined = energy.join(
    emissions, on=["date_key", "plant_id"], how="fullouter"
).join(production, on=["date_key", "plant_id"], how="fullouter")

onto_plant_daily = plant_daily_joined.select(
    F.col("plant_id").cast("string").alias("plant_id"),
    F.col("date_key").cast("timestamp").alias("metric_ts"),
    F.col("energy_gj"),
    F.col("electricity_mwh"),
    F.col("energy_cost_eur"),
    F.col("total_co2e_t"),
    F.coalesce(F.col("crude_steel_tons_energy"), F.col("crude_steel_tons_emis")).alias(
        "crude_steel_tons"
    ),
    F.col("good_tons"),
).filter(F.col("plant_id").isNotNull() & F.col("metric_ts").isNotNull())

# Assert one row per (plant_id, metric_ts) before persisting.
_pd_total = onto_plant_daily.count()
_pd_distinct = onto_plant_daily.select("plant_id", "metric_ts").distinct().count()
if _pd_total != _pd_distinct:
    raise ValueError(
        f"onto_plant_daily is not unique per (plant_id, metric_ts): "
        f"{_pd_total} rows vs {_pd_distinct} distinct keys"
    )
row_counts["onto_plant_daily"] = write_managed(onto_plant_daily, "onto_plant_daily")

# 8. onto_rel_plant_asset (relationship contextualization) -----------------------
onto_rel_plant_asset = (
    current_rows("dim_asset")
    .select(
        F.col("plant_id").cast("string").alias("plant_id"),
        F.col("asset_id").cast("string").alias("asset_id"),
    )
    .filter(F.col("plant_id").isNotNull() & F.col("asset_id").isNotNull())
    .distinct()
)
row_counts["onto_rel_plant_asset"] = write_managed(onto_rel_plant_asset, "onto_rel_plant_asset")

# 9. onto_rel_asset_sensor (relationship contextualization) ----------------------
onto_rel_asset_sensor = (
    current_rows("dim_sensor")
    .select(
        F.col("asset_id").cast("string").alias("asset_id"),
        sensor_uid().alias("sensor_uid"),
    )
    .filter(F.col("asset_id").isNotNull() & F.col("sensor_uid").isNotNull())
    .distinct()
)
row_counts["onto_rel_asset_sensor"] = write_managed(onto_rel_asset_sensor, "onto_rel_asset_sensor")

# Summary + non-empty assertions -------------------------------------------------
ORDERED_TABLES = [
    "onto_plant",
    "onto_asset",
    "onto_sensor",
    "onto_grade",
    "onto_sensor_reading",
    "onto_asset_health",
    "onto_plant_daily",
    "onto_rel_plant_asset",
    "onto_rel_asset_sensor",
]
summary_rows = [(name, int(row_counts[name])) for name in ORDERED_TABLES]
spark.createDataFrame(summary_rows, "table_name string, row_count long").show(
    n=len(summary_rows), truncate=False
)

print(
    {
        "status": "materialized",
        "environment": ENVIRONMENT,
        "row_counts": row_counts,
        "notes": notes,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
)

empty = [name for name in ORDERED_TABLES if row_counts[name] == 0]
# onto_sensor_reading is allowed to be empty (telemetry may not be seeded); warn.
if "onto_sensor_reading" in empty:
    print("WARNING: onto_sensor_reading is empty (telemetry not seeded?).")
hard_empty = [name for name in empty if name != "onto_sensor_reading"]
if hard_empty:
    raise ValueError(f"Ontology binding tables are unexpectedly empty: {hard_empty}")

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
