# Fabric notebook source

# METADATA ********************
# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************
from delta.tables import DeltaTable
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

ENVIRONMENT = "{{environment}}"
CORE_TABLES_URI = "{{onelake.coreTablesUri}}"
MODEL_VERSION = "novasteel-demo-deterministic/1.0.0"
QUALITY_SCENARIO_ID = "quality-drift"
QUALITY_SEED = 240728


def require_resolved(name: str, value: str) -> None:
    if not value or value.startswith("{{"):
        raise ValueError(f"{name} must be resolved to an environment value")


def path(table_name: str) -> str:
    return f"{CORE_TABLES_URI.rstrip('/')}/{table_name}"


def read(table_name: str) -> DataFrame:
    return spark.read.format("delta").load(path(table_name))


def upsert(frame: DataFrame, table_name: str, keys) -> int:
    if frame.rdd.isEmpty():
        return 0
    source = frame.dropDuplicates(list(keys))
    target_path = path(table_name)
    if not DeltaTable.isDeltaTable(spark, target_path):
        source.write.format("delta").mode("overwrite").save(target_path)
        return source.count()
    condition = " AND ".join([f"target.`{key}` = source.`{key}`" for key in keys])
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
        "Deterministic demo scoring is hard-disabled outside dev/test/demo "
        f"(got ENVIRONMENT={ENVIRONMENT!r})"
    )

telemetry = read("fact_telemetry")
if telemetry.where(F.col("data_classification") != "SYNTHETIC").limit(1).count() > 0:
    raise ValueError("Deterministic demo scoring refuses non-SYNTHETIC telemetry")

features = telemetry.groupBy("plant_id", "asset_id", "scenario_id", "seed").agg(
    F.max("event_ts").alias("feature_snapshot_ts"),
    F.avg(
        F.when(F.col("signal_code") == "hearth_shell_temperature", F.col("value"))
    ).alias("shell_temp_avg"),
    F.avg(
        F.when(F.col("signal_code") == "local_heat_flux", F.col("value"))
    ).alias("heat_flux_avg"),
    F.avg(
        F.when(F.col("signal_code") == "cooling_water_flow", F.col("value"))
    ).alias("cooling_flow_avg"),
    F.max(
        F.when(F.col("signal_code") == "hearth_shell_temperature", F.col("value"))
    ).alias("shell_temp_max"),
)
features = features.where(F.col("asset_id").like("%-BF-%"))
if features.rdd.isEmpty():
    raise RuntimeError("No synthetic furnace telemetry is available for demo scoring")

risk_raw = (
    F.lit(0.20)
    + F.greatest(F.coalesce(F.col("shell_temp_avg"), F.lit(140.0)) - 140.0, F.lit(0.0))
    / 100.0
    * 0.35
    + F.greatest(F.coalesce(F.col("heat_flux_avg"), F.lit(90.0)) - 90.0, F.lit(0.0))
    / 160.0
    * 0.30
    + F.greatest(180.0 - F.coalesce(F.col("cooling_flow_avg"), F.lit(180.0)), F.lit(0.0))
    / 180.0
    * 0.15
)
scored = (
    features.withColumn("risk_score", F.least(F.greatest(risk_raw, F.lit(0.01)), F.lit(0.99)))
    .withColumn(
        "rul_p50",
        F.greatest(F.lit(3.0), F.lit(90.0) * (F.lit(1.0) - F.col("risk_score")))
    )
    .withColumn("rul_p10", F.col("rul_p50") * 0.80)
    .withColumn("rul_p90", F.col("rul_p50") * 1.30)
    .withColumn("component_id", F.lit("HEARTH-SECTOR-07"))
    .withColumn(
        "inference_id",
        F.concat(
            F.lit("INF-"),
            F.substring(
                F.sha2(
                    F.concat_ws(
                        "|",
                        "plant_id",
                        "asset_id",
                        "component_id",
                        F.col("feature_snapshot_ts").cast("string"),
                        F.coalesce(F.col("seed").cast("string"), F.lit("NO-SEED")),
                        F.lit(MODEL_VERSION),
                    ),
                    256,
                ),
                1,
                28,
            ),
        ),
    )
    .withColumn("scored_at", F.col("feature_snapshot_ts"))
    .withColumn("confidence", F.lit(0.84))
    .withColumn(
        "top_factors_json",
        F.to_json(
            F.array(
                F.struct(
                    F.lit("heat_flux_6h_slope").alias("feature"),
                    F.lit(0.29).alias("contribution"),
                ),
                F.struct(
                    F.lit("sector_to_ring_temp_delta").alias("feature"),
                    F.lit(0.24).alias("contribution"),
                ),
                F.struct(
                    F.lit("cooling_efficiency_residual").alias("feature"),
                    F.lit(0.18).alias("contribution"),
                ),
            )
        ),
    )
)

rul_inference = scored.select(
    "inference_id",
    F.to_date("feature_snapshot_ts").alias("event_date"),
    "feature_snapshot_ts",
    "scored_at",
    "plant_id",
    F.col("asset_id").alias("entity_id"),
    "component_id",
    F.lit("lining-rul-piml-demo").alias("model_id"),
    F.lit(MODEL_VERSION).alias("model_version"),
    F.lit("rul").alias("prediction_type"),
    F.col("rul_p50").alias("prediction_value"),
    F.lit("d").alias("unit"),
    F.col("rul_p10").alias("p10"),
    F.col("rul_p50").alias("p50"),
    F.col("rul_p90").alias("p90"),
    "risk_score",
    "confidence",
    "top_factors_json",
    F.concat(
        F.lit("silver:fact_telemetry@"),
        F.col("feature_snapshot_ts").cast("string"),
    ).alias("feature_snapshot_ref"),
    "scenario_id",
    "seed",
)
rul_silver_written = upsert(
    rul_inference, "fact_model_inference", ["inference_id"]
)

rul_gold = scored.select(
    "inference_id",
    F.to_date("scored_at").alias("scored_date"),
    "scored_at",
    "plant_id",
    "asset_id",
    "component_id",
    F.col("rul_p10").alias("rul_days_p10"),
    F.col("rul_p50").alias("rul_days_p50"),
    F.col("rul_p90").alias("rul_days_p90"),
    "risk_score",
    "confidence",
    F.date_add(F.to_date("scored_at"), F.round("rul_p50").cast("int")).alias(
        "predicted_failure_date"
    ),
    F.when(F.col("rul_p50") <= 21.0, F.col("scored_at")).alias("alert_issued_at"),
    F.lit(None).cast("timestamp").alias("actual_reline_or_failure_at"),
    F.lit(False).alias("unplanned_outage_flag"),
    F.lit(MODEL_VERSION).alias("model_version"),
    "top_factors_json",
    "scenario_id",
    "seed",
)
rul_gold_written = upsert(rul_gold, "fact_furnace_rul", ["inference_id"])

quality_written = 0
if DeltaTable.isDeltaTable(spark, path("fact_quality_measurement")):
    quality = read("fact_quality_measurement")
    quality_features = quality.groupBy("plant_id", "material_id", "grade_code").agg(
        F.max("event_ts").alias("feature_snapshot_ts"),
        F.avg(
            F.when(
                F.col("upper_spec_limit").isNotNull(),
                F.abs(F.col("value") - F.col("upper_spec_limit"))
                / F.greatest(F.abs(F.col("upper_spec_limit")), F.lit(1.0)),
            )
        ).alias("normalized_deviation"),
        F.max(F.when(F.col("result_status") != "PASS", 1).otherwise(0)).alias(
            "observed_nonconformance"
        ),
    )
    quality_score = (
        quality_features.withColumn(
            "risk_score",
            F.least(
                F.lit(0.95),
                F.lit(0.15)
                + F.coalesce(F.col("normalized_deviation"), F.lit(0.0)) * 3.0
                + F.col("observed_nonconformance") * 0.25,
            ),
        )
        .withColumn(
            "inference_id",
            F.concat(
                F.lit("INF-Q-"),
                F.substring(
                    F.sha2(
                        F.concat_ws(
                            "|",
                            "plant_id",
                            "material_id",
                            "grade_code",
                            F.col("feature_snapshot_ts").cast("string"),
                            F.lit(str(QUALITY_SEED)),
                        ),
                        256,
                    ),
                    1,
                    26,
                ),
            ),
        )
        .withColumn(
            "predicted_yield",
            F.when(F.col("risk_score") >= 0.50, F.lit(0.88)).otherwise(F.lit(0.95)),
        )
        .withColumn(
            "top_factors_json",
            F.to_json(
                F.array(
                    F.struct(
                        F.lit("coiling_temperature_residual").alias("feature"),
                        F.lit(0.34).alias("contribution"),
                    ),
                    F.struct(
                        F.lit("grade_normalized_force_imbalance").alias("feature"),
                        F.lit(0.27).alias("contribution"),
                    ),
                )
            ),
        )
    )
    quality_inference = quality_score.select(
        "inference_id",
        F.to_date("feature_snapshot_ts").alias("event_date"),
        "feature_snapshot_ts",
        F.col("feature_snapshot_ts").alias("scored_at"),
        "plant_id",
        F.col("material_id").alias("entity_id"),
        F.lit(None).cast("string").alias("component_id"),
        F.lit("quality-risk-demo").alias("model_id"),
        F.lit(MODEL_VERSION).alias("model_version"),
        F.lit("quality-risk").alias("prediction_type"),
        F.col("risk_score").alias("prediction_value"),
        F.lit("ratio").alias("unit"),
        F.lit(None).cast("double").alias("p10"),
        F.col("predicted_yield").alias("p50"),
        F.lit(None).cast("double").alias("p90"),
        "risk_score",
        F.lit(0.86).alias("confidence"),
        "top_factors_json",
        F.concat(F.lit("silver:fact_quality_measurement@"), "material_id").alias(
            "feature_snapshot_ref"
        ),
        F.lit(QUALITY_SCENARIO_ID).alias("scenario_id"),
        F.lit(QUALITY_SEED).cast("long").alias("seed"),
    )
    quality_written = upsert(
        quality_inference, "fact_model_inference", ["inference_id"]
    )

print(
    {
        "status": "scored",
        "model_version": MODEL_VERSION,
        "rul_silver_written": rul_silver_written,
        "rul_gold_written": rul_gold_written,
        "quality_inference_written": quality_written,
    }
)

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
