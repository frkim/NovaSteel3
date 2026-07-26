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
from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, LongType, StringType, StructField, StructType

ENVIRONMENT = "{{environment}}"
RUN_ID = ""
CORE_TABLES_URI = "{{onelake.coreTablesUri}}"
CALCULATION_VERSION = "novasteel-gold/1.0.0"


def require_resolved(name: str, value: str) -> None:
    if not value or value.startswith("{{"):
        raise ValueError(f"{name} must be resolved to an environment value")


def path(table_name: str) -> str:
    return f"{CORE_TABLES_URI.rstrip('/')}/{table_name}"


def exists(table_name: str) -> bool:
    return DeltaTable.isDeltaTable(spark, path(table_name))


def read(table_name: str) -> DataFrame:
    return spark.read.format("delta").load(path(table_name))


def upsert(frame: DataFrame, table_name: str, keys) -> int:
    if frame.rdd.isEmpty():
        return 0
    source = frame.dropDuplicates(list(keys))
    target_path = path(table_name)
    if not DeltaTable.isDeltaTable(spark, target_path):
        writer = source.write.format("delta").mode("overwrite")
        partitions = [
            column
            for column in ("date_key", "scored_date", "recorded_date", "plant_id", "domain")
            if column in source.columns
        ][:2]
        if partitions:
            writer = writer.partitionBy(*partitions)
        writer.save(target_path)
        return source.count()
    target = DeltaTable.forPath(spark, target_path)
    condition = " AND ".join([f"target.`{key}` = source.`{key}`" for key in keys])
    (
        target.alias("target")
        .merge(source.alias("source"), condition)
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    return source.count()


require_resolved("ENVIRONMENT", ENVIRONMENT)
require_resolved("CORE_TABLES_URI", CORE_TABLES_URI)
RUN_ID = RUN_ID or f"silver-gold-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
written = {}

production_daily = None
if exists("fact_production_shift"):
    production_daily = (
        read("fact_production_shift")
        .groupBy(F.col("shift_date").alias("date_key"), "plant_id")
        .agg(F.sum("crude_steel_tons").alias("crude_steel_tons"))
    )

if exists("fact_energy_interval"):
    energy = read("fact_energy_interval")
    energy_daily = energy.groupBy(
        F.col("event_date").alias("date_key"), "plant_id"
    ).agg(
        F.sum("energy_gj").alias("energy_gj"),
        F.sum("energy_mwh").alias("electricity_mwh"),
        F.sum("cost_eur").alias("energy_cost_eur"),
    )
    if production_daily is not None:
        energy_daily = energy_daily.join(
            production_daily, ["date_key", "plant_id"], "left"
        )
    else:
        energy_daily = energy_daily.withColumn(
            "crude_steel_tons", F.lit(None).cast("double")
        )
    energy_daily = (
        energy_daily.withColumn(
            "baseline_energy_gj",
            F.when(
                (F.lit(ENVIRONMENT) == "demo") & F.col("energy_gj").isNotNull(),
                F.col("energy_gj") / F.lit(0.86),
            ),
        )
        .withColumn(
            "baseline_cost_eur",
            F.when(
                (F.lit(ENVIRONMENT) == "demo")
                & F.col("energy_cost_eur").isNotNull(),
                F.col("energy_cost_eur") / F.lit(0.90),
            ),
        )
        .withColumn("calculation_version", F.lit(CALCULATION_VERSION))
        .select(
            "date_key",
            "plant_id",
            "energy_gj",
            "electricity_mwh",
            "energy_cost_eur",
            "baseline_energy_gj",
            "baseline_cost_eur",
            "crude_steel_tons",
            "calculation_version",
        )
    )
    written["fact_energy_daily"] = upsert(
        energy_daily, "fact_energy_daily", ["date_key", "plant_id"]
    )

    emissions_daily = energy.groupBy(
        F.col("event_date").alias("date_key"), "plant_id"
    ).agg(
        F.sum(
            F.when(F.col("energy_type") != "electricity", F.col("co2e_t")).otherwise(
                F.lit(0.0)
            )
        ).alias("scope1_co2e_t"),
        F.sum(
            F.when(F.col("energy_type") == "electricity", F.col("co2e_t")).otherwise(
                F.lit(0.0)
            )
        ).alias("scope2_co2e_t"),
        F.max("spot_price_eur_per_mwh").alias("_price_proxy"),
    )
    if production_daily is not None:
        emissions_daily = emissions_daily.join(
            production_daily, ["date_key", "plant_id"], "left"
        )
    else:
        emissions_daily = emissions_daily.withColumn(
            "crude_steel_tons", F.lit(None).cast("double")
        )
    emissions_daily = (
        emissions_daily.withColumn(
            "total_co2e_t", F.col("scope1_co2e_t") + F.col("scope2_co2e_t")
        )
        .withColumn(
            "baseline_co2e_t",
            F.when(
                F.lit(ENVIRONMENT) == "demo", F.col("total_co2e_t") / F.lit(0.78)
            ),
        )
        .withColumn(
            "free_allocation_t",
            F.when(
                F.col("crude_steel_tons").isNotNull(),
                F.col("crude_steel_tons") * F.lit(1.50),
            ),
        )
        .withColumn(
            "ets_allowance_price_eur_per_t",
            F.when(F.col("_price_proxy").isNotNull(), F.lit(82.0)),
        )
        .withColumn(
            "ets_exposure_eur",
            F.greatest(
                F.col("total_co2e_t") - F.coalesce(F.col("free_allocation_t"), F.lit(0.0)),
                F.lit(0.0),
            )
            * F.coalesce(F.col("ets_allowance_price_eur_per_t"), F.lit(0.0)),
        )
        .withColumn("calculation_version", F.lit(CALCULATION_VERSION))
        .select(
            "date_key",
            "plant_id",
            "scope1_co2e_t",
            "scope2_co2e_t",
            "total_co2e_t",
            "baseline_co2e_t",
            "crude_steel_tons",
            "free_allocation_t",
            "ets_allowance_price_eur_per_t",
            "ets_exposure_eur",
            "calculation_version",
        )
    )
    written["fact_emissions_daily"] = upsert(
        emissions_daily, "fact_emissions_daily", ["date_key", "plant_id"]
    )

if exists("fact_quality_measurement"):
    quality = read("fact_quality_measurement")
    grade = read("dim_grade").where(F.col("is_current") == F.lit(True)).select(
        "grade_code", "high_grade_flag"
    )
    quality_yield = (
        quality.join(grade, "grade_code", "left")
        .groupBy(F.col("event_date").alias("date_key"), "plant_id", "grade_code")
        .agg(
            F.max(F.coalesce("high_grade_flag", F.lit(False))).alias("high_grade_flag"),
            F.sum(F.coalesce("tons", F.lit(0.0))).alias("attempted_tons"),
            F.sum(
                F.when(
                    F.col("first_pass_flag") & (F.col("result_status") == "PASS"),
                    F.coalesce("tons", F.lit(0.0)),
                ).otherwise(F.lit(0.0))
            ).alias("first_pass_good_tons"),
            F.sum(
                F.when(
                    F.col("result_status") == "REWORK", F.coalesce("tons", F.lit(0.0))
                ).otherwise(F.lit(0.0))
            ).alias("rework_tons"),
            F.sum(
                F.when(
                    F.col("result_status") == "DOWNGRADE",
                    F.coalesce("tons", F.lit(0.0)),
                ).otherwise(F.lit(0.0))
            ).alias("downgrade_tons"),
            F.sum(
                F.when(
                    F.col("result_status") == "SCRAP", F.coalesce("tons", F.lit(0.0))
                ).otherwise(F.lit(0.0))
            ).alias("scrap_tons"),
            F.sum(F.when(F.col("result_status") != "PASS", 1).otherwise(0)).cast(
                "long"
            ).alias("defect_count"),
            F.countDistinct("material_id").cast("long").alias("produced_units"),
            F.sum(F.when(F.col("result_status") == "FAIL", 1).otherwise(0)).cast(
                "long"
            ).alias("open_ncr_count"),
        )
        .withColumn("calculation_version", F.lit(CALCULATION_VERSION))
    )
    written["fact_quality_yield"] = upsert(
        quality_yield,
        "fact_quality_yield",
        ["date_key", "plant_id", "grade_code"],
    )

if exists("fact_model_inference"):
    model = read("fact_model_inference")
    furnace_rul = (
        model.where(F.col("prediction_type") == "rul")
        .withColumn("scored_date", F.to_date("scored_at"))
        .withColumn("predicted_failure_date", F.date_add(F.to_date("scored_at"), F.round("p50").cast("int")))
        .withColumn(
            "alert_issued_at",
            F.when(F.col("p50") <= F.lit(21.0), F.col("scored_at")),
        )
        .withColumn("actual_reline_or_failure_at", F.lit(None).cast("timestamp"))
        .withColumn("unplanned_outage_flag", F.lit(False))
        .select(
            "inference_id",
            "scored_date",
            "scored_at",
            "plant_id",
            F.col("entity_id").alias("asset_id"),
            F.coalesce("component_id", F.lit("UNKNOWN")).alias("component_id"),
            F.col("p10").alias("rul_days_p10"),
            F.col("p50").alias("rul_days_p50"),
            F.col("p90").alias("rul_days_p90"),
            "risk_score",
            "confidence",
            "predicted_failure_date",
            "alert_issued_at",
            "actual_reline_or_failure_at",
            "unplanned_outage_flag",
            "model_version",
            "top_factors_json",
            "scenario_id",
            "seed",
        )
    )
    written["fact_furnace_rul"] = upsert(
        furnace_rul, "fact_furnace_rul", ["inference_id"]
    )

if exists("fact_ai_decision"):
    decisions = read("fact_ai_decision")
    status_rank = (
        F.when(F.col("recommendation_status") == "ACCEPTED", 4)
        .when(F.col("recommendation_status") == "MODIFIED", 3)
        .when(F.col("recommendation_status") == "REJECTED", 2)
        .when(F.col("recommendation_status") == "ISSUED", 1)
        .otherwise(0)
    )
    latest_status = (
        decisions.withColumn("_status_rank", status_rank)
        .withColumn(
            "_rank",
            F.row_number().over(
                Window.partitionBy("audit_id").orderBy(
                    F.col("event_ts").desc(), F.col("_status_rank").desc()
                )
            ),
        )
        .where(F.col("_rank") == 1)
        .select(
            "audit_id",
            F.to_date("event_ts").alias("recorded_date"),
            F.col("event_ts").alias("recorded_at"),
            "domain",
            "entity_id",
            F.coalesce("recommendation_status", F.lit("ISSUED")).alias(
                "recommendation_status"
            ),
            "input_snapshot_ref",
            "model_version",
            "confidence",
            F.when(
                F.col("recommendation_status").isin("ACCEPTED", "MODIFIED", "REJECTED"),
                F.col("event_ts"),
            ).alias("human_decision_at"),
            F.when(F.col("event_type") == "OUTCOME", F.col("event_ts")).alias(
                "outcome_recorded_at"
            ),
            "complete_audit_flag",
            "correlation_id",
        )
        .withColumn("projection_version", F.lit(CALCULATION_VERSION))
    )
    written["fact_ai_decision_audit"] = upsert(
        latest_status, "fact_ai_decision_audit", ["audit_id"]
    )

    dispatch_payload = StructType(
        [
            StructField("baseline_cost_eur", DoubleType()),
            StructField("optimized_cost_eur", DoubleType()),
            StructField("as_run_cost_eur", DoubleType()),
            StructField("expected_co2_avoided_t", DoubleType()),
            StructField("shiftable_mw", DoubleType()),
            StructField("hard_constraint_violations", LongType()),
            StructField("plant_id", StringType()),
        ]
    )
    dispatch = (
        decisions.where(
            (F.col("domain") == "energy") & (F.col("event_type") == "RECOMMENDATION")
        )
        .withColumn("_output", F.from_json("output_json", dispatch_payload))
        .select(
            F.col("audit_id").alias("recommendation_id"),
            F.to_date("event_ts").alias("recommendation_date"),
            F.col("event_ts").alias("issued_at"),
            F.col("_output.plant_id").alias("plant_id"),
            F.coalesce("recommendation_status", F.lit("ISSUED")).alias("status"),
            F.col("_output.baseline_cost_eur").alias("baseline_cost_eur"),
            F.col("_output.optimized_cost_eur").alias("optimized_cost_eur"),
            F.col("_output.as_run_cost_eur").alias("as_run_cost_eur"),
            (
                F.col("_output.baseline_cost_eur")
                - F.col("_output.optimized_cost_eur")
            ).alias("expected_cost_avoidance_eur"),
            F.when(
                F.col("_output.as_run_cost_eur").isNotNull(),
                F.col("_output.baseline_cost_eur") - F.col("_output.as_run_cost_eur"),
            ).alias("realized_cost_avoidance_eur"),
            F.col("_output.expected_co2_avoided_t").alias("expected_co2_avoided_t"),
            F.col("_output.shiftable_mw").alias("shiftable_mw"),
            F.coalesce(
                F.col("_output.hard_constraint_violations"), F.lit(0)
            ).alias("hard_constraint_violations"),
            F.coalesce("model_version", F.lit("unknown")).alias("model_version"),
            "correlation_id",
        )
        .where(F.col("plant_id").isNotNull())
    )
    written["fact_dispatch_recommendation"] = upsert(
        dispatch, "fact_dispatch_recommendation", ["recommendation_id"]
    )

print(
    {
        "run_id": RUN_ID,
        "environment": ENVIRONMENT,
        "calculation_version": CALCULATION_VERSION,
        "written": written,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
)

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
