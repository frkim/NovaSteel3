# Fabric notebook source

# METADATA ********************
# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************
# Seed the bronze landing table and load the operational envelope tables from the
# committed operational envelope pack.
#
# The Eventstream only carries whatever was streamed while a device simulator was
# running, which for a demo workspace is a thin telemetry-only slice. The
# medallion story needs every event family in bronze so that bronze-to-silver can
# populate fact_energy_interval, fact_quality_measurement, fact_alarm_event and
# fact_model_inference as well as fact_telemetry. The application story also
# needs the operational Lakehouse tables that the BFF reads directly when
# BFF_DATA_SOURCE=fabric.
#
# `python -m simulator generate-operational` writes one NDJSON file per dataset,
# each line `{"event_id": "...", "envelope": "<envelope JSON string>"}`, plus
# manifest.ndjson. tools/fabric/Load-AnalyticalGold.ps1 -Layer operational
# uploads them to OneLake `Files/<FILES_SUBPATH>/`. This notebook now does both:
# it expands true event envelopes into landing.bronze_event_envelope and it loads
# the BFF-facing core tables named exactly after each operational dataset.
from datetime import datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.types import (
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)

ENVIRONMENT = "{{environment}}"
LANDING_TABLES_URI = "{{onelake.landingTablesUri}}"
CORE_TABLES_URI = "{{onelake.coreTablesUri}}"
FILES_SUBPATH = "operational-envelopes"
BRONZE_TABLE = "bronze_event_envelope"
RUN_ID = ""

# Only true event envelopes belong in bronze. heat_batch, maintenance_event,
# operator_knowledge and truth_ledger are operational documents served straight
# to the BFF by the operational-envelope load below; they have no silver handler,
# so seeding them would only produce quarantine noise.
ENVELOPE_DATASETS = [
    "telemetry",
    "energy_interval",
    "quality_measurement",
    "alarm_event",
    "model_inference",
]

# Dataset table names — must match simulator/fabric_operational.OPERATIONAL_DATASETS
# and bff_api.fabric_source.KNOWN_DATASETS.
OPERATIONAL_DATASETS = [
    "telemetry",
    "energy_interval",
    "heat_batch",
    "quality_measurement",
    "model_inference",
    "alarm_event",
    "maintenance_event",
    "operator_knowledge",
    "truth_ledger",
]
MANIFEST_TABLE = "manifest"
EVENT_ID_COLUMN = "event_id"
ENVELOPE_COLUMN = "envelope"

# Explicit schema so `envelope` is always read as a STRING (a JSON document),
# never inferred into a struct — the BFF requires a string to json.loads.
DATASET_SCHEMA = StructType([
    StructField(EVENT_ID_COLUMN, StringType(), False),
    StructField(ENVELOPE_COLUMN, StringType(), False),
])
MANIFEST_SCHEMA = StructType([
    StructField(ENVELOPE_COLUMN, StringType(), False),
])

# The envelope fields, minus `payload` - that stays raw JSON text and is lifted
# out with get_json_object so a nested object survives as a string.
ENVELOPE_SCHEMA = StructType([
    StructField(EVENT_ID_COLUMN, StringType()),
    StructField("event_ts", StringType()),
    StructField("ingest_ts", StringType()),
    StructField("sequence", LongType()),
    StructField("source_id", StringType()),
    StructField("plant_id", StringType()),
    StructField("asset_id", StringType()),
    StructField("schema_name", StringType()),
    StructField("schema_version", IntegerType()),
    StructField("correlation_id", StringType()),
    StructField("data_classification", StringType()),
    StructField("privacy_label", StringType()),
    StructField("scenario_id", StringType()),
    StructField("seed", LongType()),
    StructField("generator_version", StringType()),
])

# The generator emits RFC 3339 with milliseconds and a literal Z.
TS_FORMATS = ["yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", "yyyy-MM-dd'T'HH:mm:ss'Z'"]


def require_resolved(name: str, value: str) -> None:
    if not value or value.startswith("{{"):
        raise ValueError(f"{name} must be resolved to an environment value")


def core_files_uri() -> str:
    return CORE_TABLES_URI.rstrip("/")[: -len("/Tables")] + "/Files"


def bronze_path() -> str:
    return f"{LANDING_TABLES_URI.rstrip('/')}/{BRONZE_TABLE}"


def table_path(table_name: str) -> str:
    return f"{CORE_TABLES_URI.rstrip('/')}/{table_name}"


def files_path(table_name: str) -> str:
    return f"{core_files_uri()}/{FILES_SUBPATH}/{table_name}.ndjson"


def parse_ts(column):
    return F.coalesce(*[F.to_timestamp(column, fmt) for fmt in TS_FORMATS])


def upsert_on_event_id(frame, table_name: str) -> int:
    source = frame.dropDuplicates([EVENT_ID_COLUMN])
    target_path = table_path(table_name)
    if not DeltaTable.isDeltaTable(spark, target_path):
        source.write.format("delta").mode("overwrite").save(target_path)
        return source.count()
    (
        DeltaTable.forPath(spark, target_path)
        .alias("target")
        .merge(source.alias("source"), f"target.`{EVENT_ID_COLUMN}` = source.`{EVENT_ID_COLUMN}`")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    return source.count()


require_resolved("ENVIRONMENT", ENVIRONMENT)
require_resolved("LANDING_TABLES_URI", LANDING_TABLES_URI)
require_resolved("CORE_TABLES_URI", CORE_TABLES_URI)
_ENV_ALLOWED_SUFFIXES = ("dev", "test", "demo")
_env_normalized = ENVIRONMENT.strip().lower()
if not any(_env_normalized == t or _env_normalized.endswith("-" + t) for t in _ENV_ALLOWED_SUFFIXES):
    raise ValueError(
        "Operational demo-data bronze seed/load is hard-disabled outside dev/test/demo "
        f"(got ENVIRONMENT={ENVIRONMENT!r})"
    )

RUN_ID = RUN_ID or f"bronze-seed-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************
# Bronze landing seed: expand true event envelopes into bronze_event_envelope and
# MERGE by event_id so the cell stays additive and re-runnable.
frames = []
read_counts = {}
for dataset in ENVELOPE_DATASETS:
    try:
        raw = spark.read.schema(DATASET_SCHEMA).json(files_path(dataset))
        count = raw.count()
    except Exception as exc:  # noqa: BLE001 - a missing dataset must not fail the run
        read_counts[dataset] = f"skipped ({exc.__class__.__name__})"
        continue
    if count == 0:
        read_counts[dataset] = 0
        continue
    read_counts[dataset] = count
    payload_json = F.get_json_object(F.col(ENVELOPE_COLUMN), "$.payload")
    parsed = raw.select(
        F.from_json(F.col(ENVELOPE_COLUMN), ENVELOPE_SCHEMA).alias("e"),
        payload_json.alias("payload_json"),
    )
    frames.append(
        parsed.select(
            F.col(f"e.{EVENT_ID_COLUMN}").alias(EVENT_ID_COLUMN),
            parse_ts(F.col("e.event_ts")).alias("event_ts"),
            parse_ts(F.col("e.ingest_ts")).alias("ingest_ts"),
            F.col("e.sequence").alias("sequence"),
            F.col("e.source_id").alias("source_id"),
            F.col("e.plant_id").alias("plant_id"),
            F.col("e.asset_id").alias("asset_id"),
            F.col("e.schema_name").alias("schema_name"),
            F.col("e.schema_version").alias("schema_version"),
            F.col("e.correlation_id").alias("correlation_id"),
            F.col("e.data_classification").alias("data_classification"),
            F.col("e.privacy_label").alias("privacy_label"),
            F.col("e.scenario_id").alias("scenario_id"),
            F.col("e.seed").alias("seed"),
            F.col("e.generator_version").alias("generator_version"),
            F.lit(None).cast("string").alias("clock_mode"),
            F.col("payload_json"),
            F.sha2(F.col("payload_json"), 256).alias("payload_hash"),
            F.lit(RUN_ID).alias("run_id"),
        )
    )

if not frames:
    raise RuntimeError(
        f"No envelope datasets found under Files/{FILES_SUBPATH}; run "
        "tools/fabric/Load-AnalyticalGold.ps1 -Layer operational first"
    )

seeded = frames[0]
for frame in frames[1:]:
    seeded = seeded.unionByName(frame)
seeded = (
    seeded.where(F.col(EVENT_ID_COLUMN).isNotNull())
    .withColumn("event_date", F.to_date("event_ts"))
    .withColumn("landed_at", F.coalesce(F.col("ingest_ts"), F.current_timestamp()))
    .dropDuplicates([EVENT_ID_COLUMN])
)

target_path = bronze_path()
if not DeltaTable.isDeltaTable(spark, target_path):
    seeded.write.format("delta").mode("overwrite").partitionBy(
        "event_date", "plant_id"
    ).save(target_path)
else:
    # The Eventstream-created table has its own column set, so let the MERGE add
    # the declared bronze columns rather than failing on the difference.
    spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")
    (
        DeltaTable.forPath(spark, target_path)
        .alias("target")
        .merge(seeded.alias("source"), "target.`event_id` = source.`event_id`")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
bronze_seed_summary = {
    "status": "seeded",
    "run_id": RUN_ID,
    "target_table": BRONZE_TABLE,
    "target_path": target_path,
    "read_counts": read_counts,
    "rows_merged": seeded.count(),
}

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************
# Operational BFF tables: preserve the previous standalone loader's write shape
# exactly — nine core Delta tables keyed by event_id plus a wholesale
# overwrite of the single-row manifest table.
operational_written = {}
for table_name in OPERATIONAL_DATASETS:
    source_path = files_path(table_name)
    try:
        frame = spark.read.schema(DATASET_SCHEMA).json(source_path)
    except Exception as exc:  # noqa: BLE001 - clear per-table message
        operational_written[table_name] = f"skipped ({exc.__class__.__name__})"
        continue
    operational_written[table_name] = upsert_on_event_id(frame, table_name)

# The manifest is a single row; overwrite it wholesale (idempotent by design).
manifest_path = files_path(MANIFEST_TABLE)
try:
    manifest_frame = spark.read.schema(MANIFEST_SCHEMA).json(manifest_path)
    manifest_frame.write.format("delta").mode("overwrite").option(
        "overwriteSchema", "true").save(table_path(MANIFEST_TABLE))
    operational_written[MANIFEST_TABLE] = manifest_frame.count()
except Exception as exc:  # noqa: BLE001
    operational_written[MANIFEST_TABLE] = f"skipped ({exc.__class__.__name__})"

print(
    {
        "status": "seeded_and_loaded",
        "environment": ENVIRONMENT,
        "files_subpath": FILES_SUBPATH,
        "core_files_uri": core_files_uri(),
        "bronze_seed": bronze_seed_summary,
        "operational_envelope_tables": operational_written,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
)

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
