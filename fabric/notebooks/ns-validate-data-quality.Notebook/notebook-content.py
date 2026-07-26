# Fabric notebook source

# METADATA ********************
# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************
from datetime import datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import functions as F

ENVIRONMENT = "{{environment}}"
RUN_ID = ""
LANDING_TABLES_URI = "{{onelake.landingTablesUri}}"
CORE_TABLES_URI = "{{onelake.coreTablesUri}}"


def require_resolved(name: str, value: str) -> None:
    if not value or value.startswith("{{"):
        raise ValueError(f"{name} must be resolved to an environment value")


def path(root: str, table_name: str) -> str:
    return f"{root.rstrip('/')}/{table_name}"


def exists(root: str, table_name: str) -> bool:
    return DeltaTable.isDeltaTable(spark, path(root, table_name))


def read(root: str, table_name: str):
    return spark.read.format("delta").load(path(root, table_name))


def result(table_name, rule_id, evaluated_rows, failed_rows, threshold=None, metric=None):
    return (
        RUN_ID,
        datetime.now(timezone.utc).date(),
        table_name,
        rule_id,
        "PASS" if failed_rows == 0 else "FAIL",
        int(evaluated_rows),
        int(failed_rows),
        float(metric) if metric is not None else None,
        float(threshold) if threshold is not None else None,
        datetime.now(timezone.utc),
    )


require_resolved("ENVIRONMENT", ENVIRONMENT)
require_resolved("LANDING_TABLES_URI", LANDING_TABLES_URI)
require_resolved("CORE_TABLES_URI", CORE_TABLES_URI)

if not exists(CORE_TABLES_URI, "pipeline_run_reconciliation"):
    raise RuntimeError("pipeline_run_reconciliation is missing")

reconciliation = read(CORE_TABLES_URI, "pipeline_run_reconciliation")
if not RUN_ID:
    latest = reconciliation.orderBy(F.col("recorded_at").desc()).select("run_id").first()
    RUN_ID = latest["run_id"] if latest else "standalone-dq"

rows = []
selected_reconciliation = reconciliation.where(F.col("run_id") == RUN_ID)
unexplained = selected_reconciliation.agg(
    F.coalesce(F.sum("unexplained_rows"), F.lit(0)).alias("value")
).first()["value"]
rows.append(
    result(
        "pipeline_run_reconciliation",
        "DQ-REC-001",
        selected_reconciliation.count(),
        1 if unexplained != 0 else 0,
        threshold=0,
        metric=unexplained,
    )
)

if ENVIRONMENT == "demo" and exists(LANDING_TABLES_URI, "bronze_event_envelope"):
    bronze = read(LANDING_TABLES_URI, "bronze_event_envelope")
    demo_bad = bronze.where(
        (F.col("data_classification") != "SYNTHETIC")
        | (F.col("privacy_label") != "DEMO-NONPERSONAL")
        | (~F.col("plant_id").startswith("NS-DEMO-"))
    ).count()
    rows.append(
        result(
            "bronze_event_envelope",
            "DQ-ENV-004",
            bronze.count(),
            demo_bad,
            threshold=0,
            metric=demo_bad,
        )
    )

if exists(CORE_TABLES_URI, "fact_furnace_rul"):
    rul = read(CORE_TABLES_URI, "fact_furnace_rul")
    bad_quantiles = rul.where(
        (F.col("rul_days_p10") < 0)
        | (F.col("rul_days_p10") >= F.col("rul_days_p50"))
        | (F.col("rul_days_p50") >= F.col("rul_days_p90"))
    ).count()
    rows.append(
        result(
            "fact_furnace_rul",
            "DQ-RUL-001",
            rul.count(),
            bad_quantiles,
            threshold=0,
            metric=bad_quantiles,
        )
    )
    demo_warning_bad = rul.where(
        (F.col("seed") == 240726)
        & (F.col("component_id") == "HEARTH-SECTOR-07")
        & (
            (F.abs(F.col("rul_days_p50") - 21.0) > 0.001)
            | (F.col("risk_score") < 0.80)
            | (F.col("rul_days_p10") >= F.col("rul_days_p50"))
            | (F.col("rul_days_p50") >= F.col("rul_days_p90"))
        )
    ).count()
    expected_warning_rows = rul.where(
        (F.col("seed") == 240726)
        & (F.col("component_id") == "HEARTH-SECTOR-07")
    ).count()
    missing_warning = 1 if ENVIRONMENT == "demo" and expected_warning_rows == 0 else 0
    rows.append(
        result(
            "fact_furnace_rul",
            "DQ-DEMO-001",
            expected_warning_rows,
            demo_warning_bad + missing_warning,
            threshold=0,
            metric=demo_warning_bad + missing_warning,
        )
    )

if exists(CORE_TABLES_URI, "fact_dispatch_recommendation"):
    dispatch = read(CORE_TABLES_URI, "fact_dispatch_recommendation")
    constraint_failures = dispatch.where(
        F.col("hard_constraint_violations") != 0
    ).count()
    rows.append(
        result(
            "fact_dispatch_recommendation",
            "DQ-OPT-001",
            dispatch.count(),
            constraint_failures,
            threshold=0,
            metric=constraint_failures,
        )
    )

if exists(CORE_TABLES_URI, "fact_ai_decision_audit"):
    audit = read(CORE_TABLES_URI, "fact_ai_decision_audit")
    incomplete = audit.where(~F.col("complete_audit_flag")).count()
    rows.append(
        result(
            "fact_ai_decision_audit",
            "DQ-AUD-001",
            audit.count(),
            incomplete,
            threshold=0,
            metric=incomplete,
        )
    )

if exists(CORE_TABLES_URI, "dim_asset"):
    asset = read(CORE_TABLES_URI, "dim_asset")
    current_counts = (
        asset.where(F.col("is_current"))
        .groupBy("asset_id")
        .count()
        .where(F.col("count") != 1)
        .count()
    )
    overlaps = (
        asset.alias("left")
        .join(
            asset.alias("right"),
            (F.col("left.asset_id") == F.col("right.asset_id"))
            & (F.col("left.version") < F.col("right.version"))
            & (
                F.coalesce(F.col("left.valid_to"), F.to_timestamp(F.lit("9999-12-31")))
                > F.col("right.valid_from")
            )
            & (
                F.coalesce(F.col("right.valid_to"), F.to_timestamp(F.lit("9999-12-31")))
                > F.col("left.valid_from")
            ),
            "inner",
        )
        .count()
    )
    rows.append(
        result(
            "dim_asset",
            "DQ-REF-002",
            asset.count(),
            current_counts + overlaps,
            threshold=0,
            metric=current_counts + overlaps,
        )
    )

if exists(CORE_TABLES_URI, "fact_quality_measurement") and exists(
    CORE_TABLES_URI, "fact_model_inference"
):
    quality = read(CORE_TABLES_URI, "fact_quality_measurement")
    inference = read(CORE_TABLES_URI, "fact_model_inference").where(
        (F.col("prediction_type") == "quality-risk") & (F.col("seed") == 240728)
    )
    first_failure = quality.where(F.col("result_status") != "PASS").agg(
        F.min("event_ts").alias("first_failure")
    ).first()["first_failure"]
    first_warning = inference.agg(F.min("scored_at").alias("first_warning")).first()[
        "first_warning"
    ]
    ordering_failure = (
        1
        if ENVIRONMENT == "demo"
        and (
            first_warning is None
            or (first_failure is not None and first_warning >= first_failure)
        )
        else 0
    )
    rows.append(
        result(
            "fact_model_inference",
            "DQ-DEMO-003",
            inference.count(),
            ordering_failure,
            threshold=0,
            metric=ordering_failure,
        )
    )

result_frame = spark.createDataFrame(
    rows,
    "run_id string, run_date date, table_name string, rule_id string, status string, "
    "evaluated_rows long, failed_rows long, metric_value double, threshold double, "
    "recorded_at timestamp",
)
target_path = path(CORE_TABLES_URI, "dq_run_result")
if not DeltaTable.isDeltaTable(spark, target_path):
    result_frame.write.format("delta").mode("overwrite").partitionBy("run_date").save(
        target_path
    )
else:
    (
        DeltaTable.forPath(spark, target_path)
        .alias("target")
        .merge(
            result_frame.alias("source"),
            "target.run_id = source.run_id AND "
            "target.table_name = source.table_name AND "
            "target.rule_id = source.rule_id",
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )

failed = result_frame.where(F.col("status") == "FAIL").count()
summary = {
    "run_id": RUN_ID,
    "rules_evaluated": result_frame.count(),
    "rules_failed": failed,
    "status": "PASS" if failed == 0 else "FAIL",
}
print(summary)
if failed:
    raise RuntimeError(f"Data-quality gate failed: {summary}")

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
