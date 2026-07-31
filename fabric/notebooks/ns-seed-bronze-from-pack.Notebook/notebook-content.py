# Fabric notebook source

# METADATA ********************
# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************
# Seed the bronze landing table from the committed operational envelope pack.
#
# The Eventstream only carries whatever was streamed while a device simulator was
# running, which for a demo workspace is a thin telemetry-only slice. The
# medallion story needs every event family in bronze so that bronze-to-silver can
# populate fact_energy_interval, fact_quality_measurement, fact_alarm_event and
# fact_model_inference as well as fact_telemetry.
#
# `python -m simulator generate-operational` writes one NDJSON file per dataset,
# each line `{"event_id": "...", "envelope": "<envelope JSON string>"}`.
# tools/fabric/Load-AnalyticalGold.ps1 -Layer operational uploads them to
# OneLake `Files/<FILES_SUBPATH>/`. This notebook expands the envelope JSON into
# the declared bronze_event_envelope columns and MERGEs on event_id, so it is
# idempotent and additive: rows already landed by the Eventstream keep their
# `payload` column and are simply matched, never duplicated.
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

# Only true event envelopes belong in bronze. heat_batch, operator_knowledge and
# truth_ledger are reference/ledger documents served straight to the BFF by
# ns-load-operational-envelopes; they carry no event envelope and no silver
# handler, so seeding them would only produce quarantine noise.
ENVELOPE_DATASETS = [
    "telemetry",
    "energy_interval",
    "quality_measurement",
    "alarm_event",
    "model_inference",
]

# The envelope fields, minus `payload` - that stays raw JSON text and is lifted
# out with get_json_object so a nested object survives as a string.
ENVELOPE_SCHEMA = StructType([
    StructField("event_id", StringType()),
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
FILE_SCHEMA = StructType([
    StructField("event_id", StringType(), False),
    StructField("envelope", StringType(), False),
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


def files_path(dataset: str) -> str:
    return f"{core_files_uri()}/{FILES_SUBPATH}/{dataset}.ndjson"


def parse_ts(column):
    return F.coalesce(*[F.to_timestamp(column, fmt) for fmt in TS_FORMATS])


require_resolved("ENVIRONMENT", ENVIRONMENT)
require_resolved("LANDING_TABLES_URI", LANDING_TABLES_URI)
require_resolved("CORE_TABLES_URI", CORE_TABLES_URI)
_ENV_ALLOWED_SUFFIXES = ("dev", "test", "demo")
_env_normalized = ENVIRONMENT.strip().lower()
if not any(_env_normalized == t or _env_normalized.endswith("-" + t) for t in _ENV_ALLOWED_SUFFIXES):
    raise ValueError(
        "Bronze seeding from the demo pack is hard-disabled outside dev/test/demo "
        f"(got ENVIRONMENT={ENVIRONMENT!r})"
    )

RUN_ID = RUN_ID or f"bronze-seed-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

frames = []
read_counts = {}
for dataset in ENVELOPE_DATASETS:
    try:
        raw = spark.read.schema(FILE_SCHEMA).json(files_path(dataset))
        count = raw.count()
    except Exception as exc:  # noqa: BLE001 - a missing dataset must not fail the run
        read_counts[dataset] = f"skipped ({exc.__class__.__name__})"
        continue
    if count == 0:
        read_counts[dataset] = 0
        continue
    read_counts[dataset] = count
    payload_json = F.get_json_object(F.col("envelope"), "$.payload")
    parsed = raw.select(
        F.from_json(F.col("envelope"), ENVELOPE_SCHEMA).alias("e"),
        payload_json.alias("payload_json"),
    )
    frames.append(
        parsed.select(
            F.col("e.event_id").alias("event_id"),
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
    seeded.where(F.col("event_id").isNotNull())
    .withColumn("event_date", F.to_date("event_ts"))
    .withColumn("landed_at", F.coalesce(F.col("ingest_ts"), F.current_timestamp()))
    .dropDuplicates(["event_id"])
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
written = seeded.count()

print(
    {
        "status": "seeded",
        "environment": ENVIRONMENT,
        "run_id": RUN_ID,
        "files_subpath": FILES_SUBPATH,
        "read_counts": read_counts,
        "rows_merged": written,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
)

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
