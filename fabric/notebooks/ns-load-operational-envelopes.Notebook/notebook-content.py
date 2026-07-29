# Fabric notebook source

# METADATA ********************
# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************
# Loader for the *operational* envelope datasets that the BFF reads from the
# Lakehouse when BFF_DATA_SOURCE=fabric.
#
# The simulator exports the committed demo-full pack into nine NDJSON table
# files plus manifest.ndjson via:
#
#     python -m simulator generate-operational
#
# Each NDJSON line is `{"event_id": "...", "envelope": "<envelope JSON string>"}`.
# tools/fabric/Load-AnalyticalGold.ps1 (with -Layer operational) uploads those
# files to OneLake `Files/<FILES_SUBPATH>/`; this notebook writes each dataset as
# a Delta table named exactly after the dataset (telemetry, energy_interval, ...)
# with the `envelope` column kept as a JSON *string*, which is the shape
# bff_api.fabric_source._reconstruct_envelope round-trips losslessly. The load is
# idempotent: dataset tables MERGE on event_id, and the single-row manifest table
# is overwritten wholesale.
from datetime import datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

ENVIRONMENT = "{{environment}}"
CORE_TABLES_URI = "{{onelake.coreTablesUri}}"
FILES_SUBPATH = "operational-envelopes"

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


def require_resolved(name: str, value: str) -> None:
    if not value or value.startswith("{{"):
        raise ValueError(f"{name} must be resolved to an environment value")


def core_files_uri() -> str:
    return CORE_TABLES_URI.rstrip("/")[: -len("/Tables")] + "/Files"


def table_path(table_name: str) -> str:
    return f"{CORE_TABLES_URI.rstrip('/')}/{table_name}"


def files_path(table_name: str) -> str:
    return f"{core_files_uri()}/{FILES_SUBPATH}/{table_name}.ndjson"


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
require_resolved("CORE_TABLES_URI", CORE_TABLES_URI)
if ENVIRONMENT not in {"dev", "test", "demo"}:
    raise ValueError("Operational demo-data load is hard-disabled outside dev/test/demo")

written = {}
for table_name in OPERATIONAL_DATASETS:
    source_path = files_path(table_name)
    try:
        frame = spark.read.schema(DATASET_SCHEMA).json(source_path)
    except Exception as exc:  # noqa: BLE001 - clear per-table message
        written[table_name] = f"skipped ({exc.__class__.__name__})"
        continue
    written[table_name] = upsert_on_event_id(frame, table_name)

# The manifest is a single row; overwrite it wholesale (idempotent by design).
manifest_path = files_path(MANIFEST_TABLE)
try:
    manifest_frame = spark.read.schema(MANIFEST_SCHEMA).json(manifest_path)
    manifest_frame.write.format("delta").mode("overwrite").option(
        "overwriteSchema", "true").save(table_path(MANIFEST_TABLE))
    written[MANIFEST_TABLE] = manifest_frame.count()
except Exception as exc:  # noqa: BLE001
    written[MANIFEST_TABLE] = f"skipped ({exc.__class__.__name__})"

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
