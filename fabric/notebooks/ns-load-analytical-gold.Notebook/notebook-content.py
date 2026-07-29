# Fabric notebook source

# METADATA ********************
# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************
# Loader for the multi-month *analytical* gold dataset produced by
# `python -m simulator generate-analytics --scenario analytical-programme-24m`.
#
# The simulator writes eight gold-grain CSVs plus a manifest.json. A thin
# upload step (see tools/fabric/Load-AnalyticalGold.ps1) lands those CSVs in
# OneLake under `Files/<FILES_SUBPATH>/`; this notebook reads them, casts the
# all-string CSV columns to the deployed core Delta schema, and MERGEs them
# into `Tables/<fact>` keyed by each fact's idempotency key. It is fully
# idempotent and re-runnable: re-loading the same dataset is a no-op, and a
# recomputed dataset (new calculation_version) updates matched rows in place.
from datetime import datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

# Deployment tokens (resolved by fabric/scripts/Deploy-FabricAssets.ps1, or
# overridable per run from a Notebook activity).
ENVIRONMENT = "{{environment}}"
CORE_TABLES_URI = "{{onelake.coreTablesUri}}"
# Sub-folder under the core lakehouse `Files/` where the CSVs were uploaded.
FILES_SUBPATH = "analytical-gold/analytical-programme-24m"

TIMESTAMP_FORMAT = "yyyy-MM-dd'T'HH:mm:ss'Z'"

# Idempotency keys mirror simulator/analytics.py::IDEMPOTENCY_KEYS and the
# grains declared in contracts/data/gold.v2.json.
IDEMPOTENCY_KEYS = {
    "fact_production_shift": ["shift_id"],
    "fact_energy_daily": ["date_key", "plant_id"],
    "fact_emissions_daily": ["date_key", "plant_id"],
    "fact_quality_yield": ["date_key", "plant_id", "grade_code"],
    "fact_furnace_rul": ["inference_id"],
    "fact_dispatch_recommendation": ["recommendation_id"],
    "fact_knowledge_procedure": ["procedure_id", "version"],
    "fact_ai_decision_audit": ["audit_id"],
}

# Per-column casts from the all-string CSV to the deployed core Delta DDL.
# "date"/"ts" go through explicit format parsing; everything else is a plain
# Spark cast (Spark parses "true"/"false" for boolean and numeric strings).
CASTS = {
    "fact_production_shift": {
        "shift_id": "string", "shift_date": "date", "plant_id": "string", "line_id": "string",
        "planned_minutes": "double", "runtime_minutes": "double", "ideal_rate_tph": "double",
        "total_tons": "double", "good_tons": "double", "crude_steel_tons": "double",
        "on_time_orders": "long", "total_orders": "long", "calculation_version": "string"},
    "fact_energy_daily": {
        "date_key": "date", "plant_id": "string", "energy_gj": "double", "electricity_mwh": "double",
        "energy_cost_eur": "double", "baseline_energy_gj": "double", "baseline_cost_eur": "double",
        "crude_steel_tons": "double", "calculation_version": "string"},
    "fact_emissions_daily": {
        "date_key": "date", "plant_id": "string", "scope1_co2e_t": "double", "scope2_co2e_t": "double",
        "total_co2e_t": "double", "baseline_co2e_t": "double", "crude_steel_tons": "double",
        "free_allocation_t": "double", "ets_allowance_price_eur_per_t": "double",
        "ets_exposure_eur": "double", "calculation_version": "string"},
    "fact_quality_yield": {
        "date_key": "date", "plant_id": "string", "grade_code": "string", "high_grade_flag": "boolean",
        "attempted_tons": "double", "first_pass_good_tons": "double", "rework_tons": "double",
        "downgrade_tons": "double", "scrap_tons": "double", "defect_count": "long",
        "produced_units": "long", "open_ncr_count": "long", "calculation_version": "string"},
    "fact_furnace_rul": {
        "inference_id": "string", "scored_date": "date", "scored_at": "ts", "plant_id": "string",
        "asset_id": "string", "component_id": "string", "rul_days_p10": "double",
        "rul_days_p50": "double", "rul_days_p90": "double", "risk_score": "double",
        "confidence": "double", "predicted_failure_date": "date", "alert_issued_at": "ts",
        "actual_reline_or_failure_at": "ts", "unplanned_outage_flag": "boolean",
        "model_version": "string", "top_factors_json": "string", "scenario_id": "string",
        "seed": "long"},
    "fact_dispatch_recommendation": {
        "recommendation_id": "string", "recommendation_date": "date", "issued_at": "ts",
        "plant_id": "string", "status": "string", "baseline_cost_eur": "double",
        "optimized_cost_eur": "double", "as_run_cost_eur": "double",
        "expected_cost_avoidance_eur": "double", "realized_cost_avoidance_eur": "double",
        "expected_co2_avoided_t": "double", "shiftable_mw": "double",
        "hard_constraint_violations": "long", "model_version": "string", "correlation_id": "string"},
    "fact_knowledge_procedure": {
        "procedure_id": "string", "version": "int", "topic_id": "string", "equipment_id": "string",
        "review_status": "string", "approved_flag": "boolean", "published_date": "date",
        "source_citation_count": "long", "content_hash": "string"},
    "fact_ai_decision_audit": {
        "audit_id": "string", "recorded_date": "date", "recorded_at": "ts", "domain": "string",
        "entity_id": "string", "recommendation_status": "string", "input_snapshot_ref": "string",
        "model_version": "string", "confidence": "double", "human_decision_at": "ts",
        "outcome_recorded_at": "ts", "complete_audit_flag": "boolean", "correlation_id": "string",
        "projection_version": "string"},
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
        writer = source.write.format("delta").mode("overwrite")
        partitions = [c for c in ("date_key", "shift_date", "scored_date", "recommendation_date",
                                  "recorded_date", "published_date", "plant_id")
                      if c in source.columns][:2]
        if partitions:
            writer = writer.partitionBy(*partitions)
        writer.save(target_path)
        return source.count()
    condition = " AND ".join([f"target.`{k}` = source.`{k}`" for k in keys])
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
if ENVIRONMENT not in {"dev", "test", "demo"}:
    raise ValueError("Analytical demo-data load is hard-disabled outside dev/test/demo")

written = {}
for table_name, keys in IDEMPOTENCY_KEYS.items():
    source_path = files_path(table_name)
    try:
        raw = spark.read.option("header", True).option("mode", "FAILFAST").csv(source_path)
    except Exception as exc:  # noqa: BLE001 - surface a clear per-table message
        written[table_name] = f"skipped ({exc.__class__.__name__})"
        continue
    frame = cast_frame(raw, table_name)
    written[table_name] = upsert(frame, table_name, keys)

print(
    {
        "status": "loaded",
        "environment": ENVIRONMENT,
        "files_subpath": FILES_SUBPATH,
        "core_files_uri": core_files_uri(),
        "written": written,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
)

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
