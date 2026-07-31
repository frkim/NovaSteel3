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
from pyspark.sql.types import (
    ArrayType,
    BooleanType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

ENVIRONMENT = "{{environment}}"
RUN_ID = ""
LANDING_TABLES_URI = "{{onelake.landingTablesUri}}"
CORE_TABLES_URI = "{{onelake.coreTablesUri}}"
LATE_WATERMARK_HOURS = 24
SUPPORTED_SCHEMA_VERSION = 1

QUARANTINE_REASONS = {
    "SCHEMA_INVALID",
    "UNKNOWN_ASSET",
    "LATE_BEYOND_POLICY",
    "DUPLICATE_CONFLICT",
    "INVALID_UNIT",
}
UUID7_REGEX = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-7[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
KNOWN_SCHEMA_NAMES = {
    "novasteel.telemetry.v1",
    "novasteel.energy-interval.v1",
    "novasteel.quality-measurement.v1",
    "novasteel.material-event.v1",
    "novasteel.maintenance-event.v1",
    "novasteel.alarm.v1",
    "novasteel.gateway-health.v1",
    "novasteel.model-inference.v1",
    "novasteel.ai-decision.v1",
    "novasteel.quarantine.v1",
}


def require_resolved(name: str, value: str) -> None:
    if not value or value.startswith("{{"):
        raise ValueError(f"{name} must be resolved to an environment value")


def path(root: str, table_name: str) -> str:
    return f"{root.rstrip('/')}/{table_name}"


def read_delta(root: str, table_name: str) -> DataFrame:
    return spark.read.format("delta").load(path(root, table_name))


def merge_delta(frame: DataFrame, root: str, table_name: str, keys) -> int:
    if frame.rdd.isEmpty():
        return 0
    clean = frame.dropDuplicates(list(keys))
    target_path = path(root, table_name)
    if not DeltaTable.isDeltaTable(spark, target_path):
        writer = clean.write.format("delta").mode("overwrite")
        partition_columns = [
            column
            for column in ("event_date", "recorded_date", "plant_id", "domain")
            if column in clean.columns
        ][:2]
        if partition_columns:
            writer = writer.partitionBy(*partition_columns)
        writer.save(target_path)
        return clean.count()
    target = DeltaTable.forPath(spark, target_path)
    condition = " AND ".join([f"target.`{key}` = source.`{key}`" for key in keys])
    (
        target.alias("target")
        .merge(clean.alias("source"), condition)
        .whenNotMatchedInsertAll()
        .execute()
    )
    return clean.count()


def payload_column(frame: DataFrame):
    # Bronze can carry the payload in either shape: the Eventstream lands a
    # `payload` struct/string, while file-seeded rows carry `payload_json`. Both
    # columns coexist once the two paths have written to the table, so coalesce
    # rather than picking one. `payload_json` wins because the Eventstream's
    # inferred struct only has the telemetry-shaped fields - serialising it for
    # an energy or alarm event silently drops everything except `type`.
    candidates = []
    if "payload_json" in frame.columns:
        candidates.append(F.col("payload_json"))
    if "payload" in frame.columns:
        payload_type = dict(frame.dtypes).get("payload", "")
        candidates.append(
            F.col("payload").cast("string") if payload_type == "string"
            else F.to_json(F.col("payload"))
        )
    if not candidates:
        return F.lit("{}")
    return F.coalesce(*candidates) if len(candidates) > 1 else candidates[0]


def quarantine_rows(frame: DataFrame, condition, reason: str, rule_id: str, detail: str) -> DataFrame:
    if reason not in QUARANTINE_REASONS:
        raise ValueError(f"Unknown quarantine reason: {reason}")
    return (
        frame.where(condition)
        .select(
            F.sha2(
                F.concat_ws(
                    "|",
                    F.coalesce(F.col("event_id"), F.lit("NO_EVENT_ID")),
                    F.lit(reason),
                    F.coalesce(F.col("payload_hash"), F.lit("NO_HASH")),
                ),
                256,
            ).alias("quarantine_id"),
            "event_id",
            "event_ts",
            "plant_id",
            "asset_id",
            F.lit(reason).alias("quarantine_reason"),
            F.lit(rule_id).alias("rule_id"),
            F.lit(detail).alias("detail"),
            "payload_json",
            "payload_hash",
            "correlation_id",
            F.current_timestamp().alias("quarantined_at"),
            F.current_date().alias("quarantine_date"),
        )
    )


require_resolved("ENVIRONMENT", ENVIRONMENT)
require_resolved("LANDING_TABLES_URI", LANDING_TABLES_URI)
require_resolved("CORE_TABLES_URI", CORE_TABLES_URI)
RUN_ID = RUN_ID or f"bronze-silver-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

bronze = read_delta(LANDING_TABLES_URI, "bronze_event_envelope")
bronze = bronze.withColumn("payload_json", payload_column(bronze))
if "payload_hash" not in bronze.columns:
    bronze = bronze.withColumn("payload_hash", F.sha2(F.col("payload_json"), 256))
if "landed_at" not in bronze.columns:
    bronze = bronze.withColumn("landed_at", F.coalesce(F.col("ingest_ts"), F.current_timestamp()))
if "clock_mode" not in bronze.columns:
    bronze = bronze.withColumn("clock_mode", F.lit(None).cast("string"))
if "privacy_label" not in bronze.columns:
    bronze = bronze.withColumn("privacy_label", F.lit(None).cast("string"))

required_missing = (
    F.col("event_id").isNull()
    | F.col("event_ts").isNull()
    | F.col("ingest_ts").isNull()
    | F.col("source_id").isNull()
    | F.col("plant_id").isNull()
    | F.col("sequence").isNull()
    | F.col("schema_name").isNull()
    | F.col("schema_version").isNull()
    | F.col("correlation_id").isNull()
    | F.col("data_classification").isNull()
    | F.col("payload_json").isNull()
)
bad_uuid = ~F.col("event_id").rlike(UUID7_REGEX)
bad_version = F.col("schema_version") != F.lit(SUPPORTED_SCHEMA_VERSION)
unknown_schema = ~F.col("schema_name").isin(*sorted(KNOWN_SCHEMA_NAMES))
future_time = (
    (F.col("event_ts").cast("long") > F.col("ingest_ts").cast("long") + F.lit(5))
    & (F.coalesce(F.col("clock_mode"), F.lit("")) != F.lit("accelerated"))
)
demo_boundary = F.lit(False)
if ENVIRONMENT == "demo":
    demo_boundary = (
        (F.col("data_classification") != F.lit("SYNTHETIC"))
        | (F.col("privacy_label") != F.lit("DEMO-NONPERSONAL"))
        | (~F.col("plant_id").startswith("NS-DEMO-"))
    )

envelope_quarantine = [
    quarantine_rows(
        bronze,
        required_missing | bad_version,
        "SCHEMA_INVALID",
        "DQ-ENV-001",
        "Required envelope field missing or unsupported schema version.",
    ),
    quarantine_rows(
        bronze,
        bad_uuid,
        "SCHEMA_INVALID",
        "DQ-ENV-002",
        "event_id is not UUIDv7.",
    ),
    quarantine_rows(
        bronze,
        unknown_schema,
        "SCHEMA_INVALID",
        "DQ-ENV-001",
        "schema_name is not in the v1 supported schema registry.",
    ),
    quarantine_rows(
        bronze,
        future_time,
        "SCHEMA_INVALID",
        "DQ-ENV-003",
        "Future event time is allowed only in accelerated clock mode.",
    ),
    quarantine_rows(
        bronze,
        demo_boundary,
        "SCHEMA_INVALID",
        "DQ-ENV-004",
        "Demo row violates SYNTHETIC/DEMO-NONPERSONAL/NS-DEMO boundary.",
    ),
]

duplicate_stats = bronze.groupBy("event_id").agg(
    F.count("*").alias("arrival_count"),
    F.countDistinct("payload_hash").alias("payload_versions"),
)
conflicting_ids = duplicate_stats.where(F.col("payload_versions") > 1).select("event_id")
conflicting = bronze.join(conflicting_ids, "event_id", "inner")
envelope_quarantine.append(
    quarantine_rows(
        conflicting,
        F.lit(True),
        "DUPLICATE_CONFLICT",
        "DQ-DUP-001",
        "Same event_id has conflicting payload hashes.",
    )
)

bad_envelope = envelope_quarantine[0]
for frame in envelope_quarantine[1:]:
    bad_envelope = bad_envelope.unionByName(frame)
bad_envelope = bad_envelope.dropDuplicates(["quarantine_id"])

invalid_keys = bad_envelope.select("event_id", "payload_hash").dropDuplicates()
window = Window.partitionBy("event_id", "payload_hash").orderBy(
    F.col("landed_at").asc(), F.col("ingest_ts").asc()
)
deduplicated = (
    bronze.withColumn("_arrival_rank", F.row_number().over(window))
    .where(F.col("_arrival_rank") == 1)
    .drop("_arrival_rank")
    .join(invalid_keys, ["event_id", "payload_hash"], "left_anti")
)

telemetry_schema = StructType(
    [
        StructField("sensor_id", StringType()),
        StructField("signal_code", StringType()),
        StructField("value", DoubleType()),
        StructField("unit", StringType()),
        StructField("quality", StringType()),
        StructField("uncertainty", DoubleType()),
        StructField("sample_period_ms", LongType()),
    ]
)
telemetry = (
    deduplicated.where(F.col("schema_name") == "novasteel.telemetry.v1")
    .withColumn("_payload", F.from_json("payload_json", telemetry_schema))
    .select("*", "_payload.*")
    .drop("_payload")
)

plant_dim = read_delta(CORE_TABLES_URI, "dim_plant").alias("plant")
asset_dim = read_delta(CORE_TABLES_URI, "dim_asset").alias("asset")
sensor_dim = read_delta(CORE_TABLES_URI, "dim_sensor").alias("sensor")

telemetry_resolved = (
    telemetry.alias("event")
    .join(
        plant_dim,
        (F.col("event.plant_id") == F.col("plant.plant_id"))
        & (F.col("event.event_ts") >= F.col("plant.valid_from"))
        & (F.col("plant.valid_to").isNull() | (F.col("event.event_ts") < F.col("plant.valid_to"))),
        "left",
    )
    .join(
        asset_dim,
        (F.col("event.asset_id") == F.col("asset.asset_id"))
        & (F.col("event.event_ts") >= F.col("asset.valid_from"))
        & (F.col("asset.valid_to").isNull() | (F.col("event.event_ts") < F.col("asset.valid_to"))),
        "left",
    )
    .join(
        sensor_dim,
        # The registry grain is (sensor_id, signal_code): the generator truncates
        # the signal code to four characters when building a furnace sensor_id, so
        # one sensor_id carries several channels with different canonical units.
        (F.col("event.sensor_id") == F.col("sensor.sensor_id"))
        & (F.col("event.signal_code") == F.col("sensor.signal_code"))
        & (F.col("event.event_ts") >= F.col("sensor.valid_from"))
        & (F.col("sensor.valid_to").isNull() | (F.col("event.event_ts") < F.col("sensor.valid_to"))),
        "left",
    )
    .select(
        F.col("event.*"),
        F.col("plant.plant_key").alias("plant_key"),
        F.col("asset.asset_key").alias("asset_key"),
        F.col("sensor.sensor_key").alias("sensor_key"),
        F.col("sensor.canonical_unit").alias("canonical_unit"),
    )
)

unknown_reference = (
    F.col("plant_key").isNull() | F.col("asset_key").isNull() | F.col("sensor_key").isNull()
)
invalid_unit = F.col("canonical_unit").isNotNull() & (F.col("unit") != F.col("canonical_unit"))
invalid_quality = ~F.col("quality").isin("GOOD", "UNCERTAIN", "BAD", "STALE", "SUBSTITUTED")
non_finite = F.isnan("value") | (F.abs(F.col("value")) == F.lit(float("inf")))
late_beyond = (
    F.col("ingest_ts").cast("long") - F.col("event_ts").cast("long")
    > F.lit(LATE_WATERMARK_HOURS * 3600)
)

telemetry_quarantine = [
    quarantine_rows(
        telemetry_resolved,
        unknown_reference,
        "UNKNOWN_ASSET",
        "DQ-REF-001",
        "No valid-time plant, asset, or sensor reference row.",
    ),
    quarantine_rows(
        telemetry_resolved,
        invalid_unit,
        "INVALID_UNIT",
        "DQ-UNIT-001",
        "Event unit does not match the event-time sensor registry.",
    ),
    quarantine_rows(
        telemetry_resolved,
        invalid_quality | non_finite,
        "SCHEMA_INVALID",
        "DQ-NUM-001",
        "Quality enumeration or numeric value is invalid.",
    ),
    quarantine_rows(
        telemetry_resolved,
        late_beyond,
        "LATE_BEYOND_POLICY",
        "DQ-LATE-001",
        "Event exceeds the configured late-data watermark.",
    ),
]
all_telemetry_quarantine = telemetry_quarantine[0]
for frame in telemetry_quarantine[1:]:
    all_telemetry_quarantine = all_telemetry_quarantine.unionByName(frame)

telemetry_invalid_keys = all_telemetry_quarantine.select("event_id", "payload_hash").dropDuplicates()
telemetry_valid = (
    telemetry_resolved.join(telemetry_invalid_keys, ["event_id", "payload_hash"], "left_anti")
    .select(
        "event_id",
        "event_ts",
        "ingest_ts",
        F.to_date("event_ts").alias("event_date"),
        "plant_key",
        "asset_key",
        "sensor_key",
        "plant_id",
        "asset_id",
        "sensor_id",
        "signal_code",
        "value",
        F.col("canonical_unit").alias("unit"),
        F.col("quality").alias("source_quality"),
        "uncertainty",
        (
            F.col("ingest_ts").cast("long") - F.col("event_ts").cast("long") > F.lit(2)
        ).alias("late_flag"),
        "scenario_id",
        "seed",
        "correlation_id",
        "data_classification",
    )
)
telemetry_written = merge_delta(
    telemetry_valid, CORE_TABLES_URI, "fact_telemetry", ["event_id"]
)

quality_schema = StructType(
    [
        StructField("sample_id", StringType()),
        StructField("characteristic_code", StringType()),
        StructField("material_id", StringType()),
        StructField("heat_id", StringType()),
        StructField("grade_code", StringType()),
        StructField("value", DoubleType()),
        StructField("unit", StringType()),
        StructField("lower_spec_limit", DoubleType()),
        StructField("upper_spec_limit", DoubleType()),
        StructField("measurement_method", StringType()),
        StructField("result_status", StringType()),
        StructField("first_pass_flag", BooleanType()),
        StructField("tons", DoubleType()),
    ]
)
quality = (
    deduplicated.where(F.col("schema_name") == "novasteel.quality-measurement.v1")
    .withColumn("_payload", F.from_json("payload_json", quality_schema))
    .select("*", "_payload.*")
    .drop("_payload")
)
grade_dim = read_delta(CORE_TABLES_URI, "dim_grade").alias("grade")
quality_resolved = (
    quality.alias("event")
    .join(
        grade_dim,
        (F.col("event.grade_code") == F.col("grade.grade_code"))
        & (F.col("event.event_ts") >= F.col("grade.valid_from"))
        & (F.col("grade.valid_to").isNull() | (F.col("event.event_ts") < F.col("grade.valid_to"))),
        "left",
    )
    .select(F.col("event.*"), F.col("grade.grade_key").alias("grade_key"))
)
quality_unknown = quality_resolved.where(F.col("grade_key").isNull())
quality_parse_invalid = (
    F.col("sample_id").isNull()
    | F.col("characteristic_code").isNull()
    | F.col("material_id").isNull()
    | F.col("grade_code").isNull()
    | F.col("value").isNull()
    | F.col("unit").isNull()
)
quality_quarantine = quarantine_rows(
    quality_resolved,
    F.col("grade_key").isNull(),
    "UNKNOWN_ASSET",
    "DQ-REF-001",
    "No valid-time grade reference row.",
).unionByName(
    quarantine_rows(
        quality_resolved,
        quality_parse_invalid,
        "SCHEMA_INVALID",
        "DQ-ENV-001",
        "Quality payload is missing a required field.",
    )
)
quality_valid = (
    quality_resolved.where(F.col("grade_key").isNotNull() & ~quality_parse_invalid)
    .select(
        "sample_id",
        "characteristic_code",
        "event_ts",
        F.to_date("event_ts").alias("event_date"),
        "plant_id",
        "asset_id",
        "material_id",
        "heat_id",
        "grade_key",
        "grade_code",
        "value",
        "unit",
        "lower_spec_limit",
        "upper_spec_limit",
        "measurement_method",
        "result_status",
        F.coalesce("first_pass_flag", F.lit(True)).alias("first_pass_flag"),
        "tons",
    )
)
quality_written = merge_delta(
    quality_valid,
    CORE_TABLES_URI,
    "fact_quality_measurement",
    ["sample_id", "characteristic_code"],
)

alarm_schema = StructType(
    [
        StructField("alarm_id", StringType()),
        StructField("transition_id", StringType()),
        StructField("severity", StringType()),
        StructField("state", StringType()),
        StructField("alarm_type", StringType()),
        StructField("confidence", DoubleType()),
        # Field names the simulator actually emits (see the alarm payload built
        # alongside the demo RUL alert): alert_id/status/reason instead of
        # alarm_id/state/alarm_type, and no transition identifier at all.
        StructField("alert_id", StringType()),
        StructField("status", StringType()),
        StructField("reason", StringType()),
        StructField("transitioned_at", StringType()),
    ]
)
alarm_envelopes = (
    deduplicated.where(F.col("schema_name") == "novasteel.alarm.v1")
    .withColumn("_payload", F.from_json("payload_json", alarm_schema))
    .select("*", "_payload.*")
    .drop("_payload")
    .withColumn("alarm_id", F.coalesce("alarm_id", "alert_id"))
    .withColumn("state", F.coalesce("state", "status"))
    .withColumn("alarm_type", F.coalesce("alarm_type", "reason"))
    .withColumn(
        # A transition is identified by the alarm plus the moment it changed
        # state; hash them so re-ingesting the same envelope is idempotent.
        "transition_id",
        F.coalesce(
            "transition_id",
            F.sha2(
                F.concat_ws(
                    "|",
                    F.col("alarm_id"),
                    F.col("state"),
                    F.coalesce(F.col("transitioned_at"), F.col("event_ts").cast("string")),
                ),
                256,
            ),
        ),
    )
)
alarms = alarm_envelopes.select(
    "alarm_id",
    "transition_id",
    "event_ts",
    F.to_date("event_ts").alias("event_date"),
    "plant_id",
    "asset_id",
    "severity",
    "state",
    "alarm_type",
    "confidence",
    "correlation_id",
)
alarm_parse_invalid = (
    F.col("alarm_id").isNull()
    | F.col("transition_id").isNull()
    | F.col("severity").isNull()
    | F.col("state").isNull()
    | F.col("alarm_type").isNull()
)
alarm_quarantine = quarantine_rows(
    alarm_envelopes,
    alarm_parse_invalid,
    "SCHEMA_INVALID",
    "DQ-ENV-001",
    "Alarm payload is missing a required field.",
)
alarms = alarms.where(~alarm_parse_invalid)
alarm_written = merge_delta(
    alarms, CORE_TABLES_URI, "fact_alarm_event", ["alarm_id", "transition_id"]
)

energy_schema = StructType(
    [
        StructField("meter_id", StringType()),
        StructField("interval_start", TimestampType()),
        StructField("interval_end", TimestampType()),
        StructField("energy_type", StringType()),
        StructField("energy_mwh", DoubleType()),
        StructField("energy_gj", DoubleType()),
        StructField("spot_price_eur_per_mwh", DoubleType()),
        StructField("grid_carbon_kg_per_mwh", DoubleType()),
        StructField("cost_eur", DoubleType()),
        StructField("co2e_t", DoubleType()),
        StructField("source_version", StringType()),
        # contracts/events/energy-interval.v1.schema.json is the authority for
        # what the simulator actually emits; the silver column names above are
        # the warehouse-side vocabulary, so read both and normalise below.
        StructField("consumption_mwh", DoubleType()),
        StructField("price", DoubleType()),
        StructField("demand", DoubleType()),
        StructField("demand_unit", StringType()),
        StructField("grid_carbon_intensity_kgco2e_per_mwh", DoubleType()),
    ]
)
energy_envelopes = (
    deduplicated.where(F.col("schema_name") == "novasteel.energy-interval.v1")
    .withColumn("_payload", F.from_json("payload_json", energy_schema))
    .select("*", "_payload.*")
    .drop("_payload")
    .withColumn("energy_mwh", F.coalesce("energy_mwh", "consumption_mwh"))
    .withColumn(
        "spot_price_eur_per_mwh", F.coalesce("spot_price_eur_per_mwh", "price")
    )
    .withColumn(
        "grid_carbon_kg_per_mwh",
        F.coalesce("grid_carbon_kg_per_mwh", "grid_carbon_intensity_kgco2e_per_mwh"),
    )
    .withColumn(
        "energy_gj", F.coalesce("energy_gj", F.col("energy_mwh") * F.lit(3.6))
    )
    .withColumn(
        "cost_eur",
        F.coalesce("cost_eur", F.col("energy_mwh") * F.col("spot_price_eur_per_mwh")),
    )
    .withColumn(
        "co2e_t",
        F.coalesce(
            "co2e_t",
            F.col("energy_mwh") * F.col("grid_carbon_kg_per_mwh") / F.lit(1000.0),
        ),
    )
    .withColumn(
        "energy_type",
        F.coalesce(
            "energy_type",
            F.when(F.col("demand_unit") == "MW", F.lit("ELECTRICITY")),
            F.lit("ELECTRICITY"),
        ),
    )
)
energy_parse_invalid = F.col("meter_id").isNull() | F.col("energy_mwh").isNull()
energy_quarantine = quarantine_rows(
    energy_envelopes,
    energy_parse_invalid,
    "SCHEMA_INVALID",
    "DQ-ENV-001",
    "Energy payload is missing meter_id or a consumption reading.",
)
energy_valid = energy_envelopes.where(~energy_parse_invalid).select(
    "meter_id",
    "plant_id",
    F.coalesce("interval_start", "event_ts").alias("interval_start"),
    F.coalesce(
        "interval_end",
        F.col("event_ts") + F.expr("INTERVAL 1 MINUTE"),
    ).alias("interval_end"),
    F.to_date(F.coalesce("interval_start", "event_ts")).alias("event_date"),
    "energy_type",
    "energy_mwh",
    "energy_gj",
    "spot_price_eur_per_mwh",
    "grid_carbon_kg_per_mwh",
    "cost_eur",
    "co2e_t",
    F.coalesce("source_version", F.lit("v1")).alias("source_version"),
    "data_classification",
)
energy_written = merge_delta(
    energy_valid,
    CORE_TABLES_URI,
    "fact_energy_interval",
    ["meter_id", "interval_start", "source_version"],
)

maintenance_schema = StructType(
    [
        StructField("work_order_id", StringType()),
        StructField("component_id", StringType()),
        StructField("event_type", StringType()),
        StructField("failure_mode", StringType()),
        StructField("action_code", StringType()),
        StructField("planned_flag", BooleanType()),
        StructField("downtime_hours", DoubleType()),
        StructField("linked_inference_id", StringType()),
    ]
)
maintenance_envelopes = (
    deduplicated.where(F.col("schema_name") == "novasteel.maintenance-event.v1")
    .withColumn("_payload", F.from_json("payload_json", maintenance_schema))
    .select("*", "_payload.*")
    .drop("_payload")
)
maintenance_parse_invalid = (
    F.col("work_order_id").isNull()
    | F.col("event_type").isNull()
    | F.col("action_code").isNull()
)
maintenance_quarantine = quarantine_rows(
    maintenance_envelopes,
    maintenance_parse_invalid,
    "SCHEMA_INVALID",
    "DQ-ENV-001",
    "Maintenance payload is missing a required field.",
)
maintenance_valid = maintenance_envelopes.where(~maintenance_parse_invalid).select(
    "work_order_id",
    "event_ts",
    F.to_date("event_ts").alias("event_date"),
    "plant_id",
    "asset_id",
    "component_id",
    "event_type",
    "failure_mode",
    "action_code",
    F.coalesce("planned_flag", F.lit(True)).alias("planned_flag"),
    "downtime_hours",
    "linked_inference_id",
)
maintenance_written = merge_delta(
    maintenance_valid,
    CORE_TABLES_URI,
    "fact_maintenance_event",
    ["work_order_id", "event_ts", "action_code"],
)

model_schema = StructType(
    [
        StructField("inference_id", StringType()),
        StructField("feature_snapshot_ts", TimestampType()),
        StructField("scored_at", TimestampType()),
        StructField("entity_id", StringType()),
        StructField("component_id", StringType()),
        StructField("model_id", StringType()),
        StructField("model_version", StringType()),
        StructField("prediction_type", StringType()),
        StructField("prediction_value", DoubleType()),
        StructField("unit", StringType()),
        StructField("p10", DoubleType()),
        StructField("p50", DoubleType()),
        StructField("p90", DoubleType()),
        StructField("risk_score", DoubleType()),
        StructField("confidence", DoubleType()),
        StructField("top_factors_json", StringType()),
        StructField("feature_snapshot_ref", StringType()),
        # The simulator nests the quantiles under `prediction` and emits the
        # drivers as a `top_factors` array; there is no flat prediction_type /
        # prediction_value / p50 in the envelope.
        StructField("label", StringType()),
        StructField(
            "prediction",
            StructType([
                StructField("estimated_minimum_lining_mm", DoubleType()),
                StructField("remaining_useful_life_days_p10", DoubleType()),
                StructField("remaining_useful_life_days_p50", DoubleType()),
                StructField("remaining_useful_life_days_p90", DoubleType()),
                StructField("risk_score", DoubleType()),
                StructField("severity", StringType()),
            ]),
        ),
        StructField(
            "top_factors",
            ArrayType(
                StructType([
                    StructField("feature", StringType()),
                    StructField("contribution", DoubleType()),
                ])
            ),
        ),
    ]
)
model_envelopes = (
    deduplicated.where(F.col("schema_name") == "novasteel.model-inference.v1")
    .withColumn("_payload", F.from_json("payload_json", model_schema))
    .select("*", "_payload.*")
    .drop("_payload")
    .withColumn("p10", F.coalesce("p10", "prediction.remaining_useful_life_days_p10"))
    .withColumn("p50", F.coalesce("p50", "prediction.remaining_useful_life_days_p50"))
    .withColumn("p90", F.coalesce("p90", "prediction.remaining_useful_life_days_p90"))
    .withColumn("risk_score", F.coalesce("risk_score", "prediction.risk_score"))
    .withColumn(
        "prediction_type",
        F.coalesce(
            "prediction_type",
            F.when(
                F.col("prediction.remaining_useful_life_days_p50").isNotNull(),
                F.lit("remaining_useful_life"),
            ),
        ),
    )
    .withColumn("prediction_value", F.coalesce("prediction_value", F.col("p50")))
    .withColumn(
        "unit",
        F.coalesce(
            "unit",
            F.when(F.col("prediction_type") == "remaining_useful_life", F.lit("d")),
        ),
    )
    .withColumn(
        "top_factors_json", F.coalesce("top_factors_json", F.to_json("top_factors"))
    )
)
model_parse_invalid = (
    F.col("inference_id").isNull()
    | F.col("model_id").isNull()
    | F.col("model_version").isNull()
    | F.col("prediction_type").isNull()
)
model_quarantine = quarantine_rows(
    model_envelopes,
    model_parse_invalid,
    "SCHEMA_INVALID",
    "DQ-ENV-001",
    "Model-inference payload is missing a required field.",
)
model_valid = model_envelopes.where(~model_parse_invalid).select(
    "inference_id",
    F.to_date(F.coalesce("feature_snapshot_ts", "event_ts")).alias("event_date"),
    F.coalesce("feature_snapshot_ts", "event_ts").alias("feature_snapshot_ts"),
    F.coalesce("scored_at", "ingest_ts").alias("scored_at"),
    "plant_id",
    F.coalesce("entity_id", "asset_id").alias("entity_id"),
    "component_id",
    "model_id",
    "model_version",
    "prediction_type",
    "prediction_value",
    "unit",
    "p10",
    "p50",
    "p90",
    "risk_score",
    "confidence",
    F.coalesce("top_factors_json", F.lit("[]")).alias("top_factors_json"),
    F.coalesce(
        "feature_snapshot_ref",
        F.concat(F.lit("bronze:event:"), "event_id"),
    ).alias("feature_snapshot_ref"),
    "scenario_id",
    "seed",
)
model_written = merge_delta(
    model_valid, CORE_TABLES_URI, "fact_model_inference", ["inference_id"]
)

decision_schema = StructType(
    [
        StructField("audit_event_id", StringType()),
        StructField("audit_id", StringType()),
        StructField("domain", StringType()),
        StructField("entity_id", StringType()),
        StructField("event_type", StringType()),
        StructField("recommendation_status", StringType()),
        StructField("input_snapshot_ref", StringType()),
        StructField("model_version", StringType()),
        StructField("output_json", StringType()),
        StructField("confidence", DoubleType()),
        StructField("actor_id", StringType()),
        StructField("reason_code", StringType()),
        StructField("complete_audit_flag", BooleanType()),
    ]
)
decision_envelopes = (
    deduplicated.where(F.col("schema_name") == "novasteel.ai-decision.v1")
    .withColumn("_payload", F.from_json("payload_json", decision_schema))
    .select("*", "_payload.*")
    .drop("_payload")
)
decision_parse_invalid = (
    F.col("audit_event_id").isNull()
    | F.col("audit_id").isNull()
    | F.col("domain").isNull()
    | F.col("entity_id").isNull()
    | F.col("event_type").isNull()
    | F.col("input_snapshot_ref").isNull()
)
decision_quarantine = quarantine_rows(
    decision_envelopes,
    decision_parse_invalid,
    "SCHEMA_INVALID",
    "DQ-AUD-001",
    "AI decision payload is missing mandatory lineage.",
)
decision_valid = decision_envelopes.where(~decision_parse_invalid).select(
    "audit_event_id",
    "audit_id",
    "event_ts",
    F.to_date("event_ts").alias("event_date"),
    "domain",
    "entity_id",
    "event_type",
    "recommendation_status",
    "input_snapshot_ref",
    "model_version",
    "output_json",
    "confidence",
    "actor_id",
    "reason_code",
    "correlation_id",
    F.coalesce("complete_audit_flag", F.lit(False)).alias("complete_audit_flag"),
)
decision_written = merge_delta(
    decision_valid, CORE_TABLES_URI, "fact_ai_decision", ["audit_event_id"]
)

quarantine = (
    bad_envelope.unionByName(all_telemetry_quarantine)
    .unionByName(quality_quarantine)
    .unionByName(alarm_quarantine)
    .unionByName(energy_quarantine)
    .unionByName(maintenance_quarantine)
    .unionByName(model_quarantine)
    .unionByName(decision_quarantine)
    .dropDuplicates(["quarantine_id"])
)
quarantine_written = merge_delta(
    quarantine, LANDING_TABLES_URI, "quarantine_event", ["quarantine_id"]
)

bronze_count = bronze.count()
unique_arrivals = bronze.select("event_id", "payload_hash").dropDuplicates().count()
exact_duplicates = bronze_count - unique_arrivals
quarantined_inputs = quarantine.select("event_id", "payload_hash").dropDuplicates().count()
accepted_inputs = (
    deduplicated.where(F.col("schema_name").isin(*sorted(KNOWN_SCHEMA_NAMES)))
    .select("event_id", "payload_hash")
    .join(
        quarantine.select("event_id", "payload_hash").dropDuplicates(),
        ["event_id", "payload_hash"],
        "left_anti",
    )
    .count()
)
unexplained = max(0, unique_arrivals - accepted_inputs - quarantined_inputs)
reconciliation = spark.createDataFrame(
    [
        (
            RUN_ID,
            datetime.now(timezone.utc).date(),
            "event_envelope",
            bronze_count,
            accepted_inputs,
            quarantined_inputs,
            exact_duplicates,
            unexplained,
            "PASS" if unexplained == 0 else "FAIL",
            datetime.now(timezone.utc),
        )
    ],
    "run_id string, run_date date, dataset string, bronze_rows long, silver_rows long, "
    "quarantine_rows long, duplicate_rows long, unexplained_rows long, status string, "
    "recorded_at timestamp",
)
merge_delta(
    reconciliation,
    CORE_TABLES_URI,
    "pipeline_run_reconciliation",
    ["run_id", "dataset"],
)

if unexplained != 0:
    raise RuntimeError(f"Unexplained bronze-to-silver rows: {unexplained}")

print(
    {
        "run_id": RUN_ID,
        "bronze_rows": bronze_count,
        "exact_duplicates": exact_duplicates,
        "quarantined_inputs": quarantined_inputs,
        "telemetry_written": telemetry_written,
        "quality_written": quality_written,
        "alarm_written": alarm_written,
        "energy_written": energy_written,
        "maintenance_written": maintenance_written,
        "model_written": model_written,
        "decision_written": decision_written,
        "quarantine_written": quarantine_written,
        "unexplained_rows": unexplained,
    }
)

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
