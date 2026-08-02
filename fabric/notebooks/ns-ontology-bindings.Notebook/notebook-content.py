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
#
# This notebook now materialises BOTH layers the Fabric IQ Ontology graph binds:
#
#   * the INSTANCE layer (ABox) — the real Plant / Asset / Sensor / Grade
#     entities and their telemetry, derived from the medallion tables (below,
#     sections 1-9);
#   * the KNOWLEDGE MODEL (TBox) — the curated EquipmentClass / ProcessStep /
#     ProductType / Signal / AlarmType vocabulary and the abstract edges between
#     them (specializes / feeds / executes / produces / measures / instanceOf /
#     supplies / triggeredBy / halts), sections 10-23. instanceOf (Asset ->
#     EquipmentClass) and measures (Sensor -> Signal) bridge the two layers so
#     the agent can walk from a real asset up to its class, reason abstractly,
#     and come back down.
#
# The TBox is seeded HERE, not in a separate notebook, on purpose. The retired
# `ns-steel-ontology` notebook wrote standalone `ontology_*` Delta tables that
# nothing consumed and that were invisible to the graph. The knowledge model is
# now bound into the Fabric IQ Ontology item as first-class entity/relationship
# types, so it is reachable by GQL alongside the instances. Curated vocabulary
# (classes, steps, products, alarm types and the abstract genealogy edges) is
# written as Python literals; everything a real table can supply (onto_signal,
# measures, instanceOf, supplies, specializes, observed counts) is DERIVED from
# the lakehouse so it never drifts from the fleet. Every relationship table is
# semi-joined against both its endpoint entity tables before writing, because
# the graph rejects dangling edges.
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

# --- Knowledge model (TBox): curated vocabulary + derived bridges ----------------
# From here down we materialise the abstract knowledge model. Curated rows are
# Python literals (steelmaking is a fixed process genealogy, not something the
# data can teach us); the derived tables (onto_signal, measures, instanceOf,
# supplies, specializes) come straight off the lakehouse so they track the fleet.


def keep_edges(edges: DataFrame, edge_col: str, entity: DataFrame, entity_key: str) -> DataFrame:
    # The graph rejects an edge whose endpoint row is missing, so every
    # relationship is left-semi-joined against the entity that owns each end:
    # only edges whose endpoint key actually exists survive.
    valid = entity.select(F.col(entity_key).cast("string").alias(edge_col)).distinct()
    return edges.join(valid, on=edge_col, how="left_semi")


# 10. onto_equipment_class (entity 1005, key class_id) ---------------------------
# Curated class taxonomy. asset_type_match holds the literal dim_asset.asset_type
# string a class types ("" for abstract / not-in-fleet classes) and is the join
# key the instanceOf bridge (section 20) uses to attach real assets to a class.
EQUIPMENT_CLASSES = [
    ("ProductionUnit", "Production Unit", "", True, "Manufacturing", "", "ALL",
     "Abstract parent for any physical production unit on the steelmaking route.", ""),
    ("BlastFurnace", "Blast Furnace", "ProductionUnit", False, "Manufacturing", "Ironmaking", "BF-BOF",
     "Iron-making shaft furnace that reduces iron ore and coke into liquid hot metal.", "Blast furnace"),
    ("BasicOxygenFurnace", "Basic Oxygen Furnace", "ProductionUnit", False, "Manufacturing", "Steelmaking", "BF-BOF",
     "Primary steelmaking vessel that blows oxygen through hot metal to refine it into liquid steel.",
     "Basic oxygen furnace"),
    ("ElectricArcFurnace", "Electric Arc Furnace", "ProductionUnit", False, "Manufacturing", "Steelmaking", "EAF",
     "Primary steelmaking furnace that melts scrap and DRI into liquid steel with a high-power electric arc.",
     "Electric arc furnace"),
    ("ContinuousCaster", "Continuous Caster", "ProductionUnit", True, "Manufacturing", "Casting", "ALL",
     "Abstract continuous casting machine that solidifies liquid steel into semi-finished shapes.", ""),
    ("SlabCaster", "Slab Caster", "ContinuousCaster", False, "Manufacturing", "Casting", "BF-BOF",
     "Continuous caster that solidifies liquid steel into flat slabs for downstream flat rolling.", "Slab caster"),
    ("BilletCaster", "Billet Caster", "ContinuousCaster", False, "Manufacturing", "Casting", "EAF",
     "Continuous caster that solidifies liquid steel into square billets for long-product rolling.", ""),
    ("ReheatFurnace", "Reheat Furnace", "ProductionUnit", False, "Manufacturing", "Rolling", "ALL",
     "Gas-fired furnace that reheats cast slabs to rolling temperature before the mill.", "Reheat furnace"),
    ("RollingMill", "Rolling Mill", "ProductionUnit", True, "Manufacturing", "Rolling", "ALL",
     "Abstract rolling mill that reduces reheated steel into finished flat or long products.", ""),
    ("HotStripMill", "Hot Strip Mill", "RollingMill", False, "Manufacturing", "Rolling", "ALL",
     "Hot rolling mill that rolls reheated slabs into hot-rolled steel strip and coils.", "Hot strip mill"),
    ("WireRodMill", "Wire Rod Mill", "RollingMill", False, "Manufacturing", "Rolling", "EAF",
     "Rolling mill that rolls billets into coiled steel wire rod.", ""),
    ("EnergySystem", "Energy System", "ProductionUnit", False, "Energy", "Utilities", "ALL",
     "Plant energy and utilities system that supplies power, fuel and cooling to the production units.",
     "Energy system"),
]
onto_equipment_class = spark.createDataFrame(
    EQUIPMENT_CLASSES,
    "class_id string, class_name string, parent_class_id string, is_abstract boolean, "
    "domain string, process_stage string, route_scope string, class_description string, "
    "asset_type_match string",
).dropDuplicates(["class_id"])
row_counts["onto_equipment_class"] = write_managed(onto_equipment_class, "onto_equipment_class")

# 11. onto_process_step (entity 1006, key step_id) -------------------------------
PROCESS_STEPS = [
    ("Ironmaking", "Ironmaking", "primary",
     "Reduction of iron ore and coke into liquid hot metal in the blast furnace."),
    ("PrimarySteelmaking", "Primary Steelmaking", "primary",
     "Refining of hot metal or melted scrap into liquid crude steel."),
    ("SecondaryMetallurgy", "Secondary Metallurgy", "secondary",
     "Ladle treatment that trims steel chemistry and temperature before casting."),
    ("ContinuousCasting", "Continuous Casting", "secondary",
     "Solidification of liquid steel into semi-finished slabs or billets."),
    ("Reheating", "Reheating", "finishing",
     "Reheating of cast semi-finished steel back up to rolling temperature."),
    ("HotRolling", "Hot Rolling", "finishing",
     "Hot reduction of reheated steel into coils, strip or rod."),
    ("ColdRollingAndCoating", "Cold Rolling and Coating", "finishing",
     "Cold reduction and surface coating of hot-rolled coil into finished product."),
]
onto_process_step = spark.createDataFrame(
    PROCESS_STEPS,
    "step_id string, step_name string, stage string, step_description string",
).dropDuplicates(["step_id"])
row_counts["onto_process_step"] = write_managed(onto_process_step, "onto_process_step")

# 12. onto_product (entity 1007, key product_id) ---------------------------------
PRODUCTS = [
    ("HotMetal", "Hot Metal", "liquid", True,
     "Molten iron tapped from the blast furnace that feeds primary steelmaking."),
    ("LiquidSteel", "Liquid Steel", "liquid", True,
     "Refined molten steel ready for continuous casting."),
    ("SteelSlab", "Steel Slab", "slab", True,
     "Semi-finished flat cast product rolled into strip and plate."),
    ("SteelBillet", "Steel Billet", "billet", True,
     "Semi-finished square cast product rolled into long products."),
    ("HotRolledCoil", "Hot-Rolled Coil", "coil", False,
     "Finished coil of hot-rolled steel strip."),
    ("ColdRolledCoil", "Cold-Rolled Coil", "coil", False,
     "Finished coil of cold-rolled, often coated, steel strip."),
    ("WireRod", "Wire Rod", "rod", False,
     "Finished coiled steel wire rod for drawing and forming."),
]
onto_product = spark.createDataFrame(
    PRODUCTS,
    "product_id string, product_name string, product_form string, semifinished boolean, "
    "product_description string",
).dropDuplicates(["product_id"])
row_counts["onto_product"] = write_managed(onto_product, "onto_product")

# 13. onto_signal (entity 1008, key signal_code) --------------------------------
# Derived, not seeded: the signal vocabulary must be exactly the signal_codes the
# real sensors carry. signal_type is classified from the code by first-matching
# substring so the agent can group heterogeneous codes into physical families.
_sensors_current = current_rows("dim_sensor").filter(F.col("signal_code").isNotNull())
_code = F.lower(F.col("signal_code"))
_signal_type = (
    F.when(_code.contains("temperature"), F.lit("temperature"))
    .when(_code.contains("pressure"), F.lit("pressure"))
    .when(_code.contains("flow"), F.lit("flow"))
    .when(_code.contains("vibration"), F.lit("vibration"))
    .when(_code.contains("current") | _code.contains("voltage") | _code.contains("power"), F.lit("electrical"))
    .when(_code.contains("speed"), F.lit("kinematic"))
    .when(_code.contains("force"), F.lit("mechanical"))
    .when(_code.contains("level"), F.lit("level"))
    .otherwise(F.lit("derived"))
)
onto_signal = (
    _sensors_current.groupBy(F.col("signal_code").cast("string").alias("signal_code"))
    .agg(
        F.first(F.col("canonical_unit"), ignorenulls=True).cast("string").alias("canonical_unit"),
        F.countDistinct(F.col("sensor_id")).cast("bigint").alias("sensor_count"),
    )
    .withColumn("signal_type", _signal_type)
    .withColumn(
        "signal_description",
        F.concat(
            F.col("signal_code"),
            F.lit(" ("),
            F.col("signal_type"),
            F.lit(") measured in "),
            F.col("canonical_unit"),
            F.lit(" by "),
            F.col("sensor_count").cast("string"),
            F.lit(" sensor(s)."),
        ),
    )
    .select("signal_code", "signal_type", "canonical_unit", "sensor_count", "signal_description")
)
row_counts["onto_signal"] = write_managed(onto_signal, "onto_signal")

# 14. onto_alarm_type (entity 1009, key alarm_type_id) ---------------------------
# Curated catalogue enriched with a live observed_count. fact_alarm_event may be
# absent or empty in a fresh environment, so the read is guarded and every count
# defaults to 0 rather than failing the run.
ALARM_TYPES = [
    ("lining_rul_below_21d_threshold", "Lining RUL Below Threshold", "HIGH", "Maintenance",
     "Predicted refractory lining remaining useful life has fallen below the 21-day maintenance threshold."),
    ("hearth_shell_overtemperature", "Hearth Shell Over-temperature", "CRITICAL", "Operations",
     "Blast furnace hearth shell temperature has exceeded its safe operating limit."),
    ("cooling_water_flow_low", "Cooling Water Flow Low", "HIGH", "Operations",
     "Cooling water flow has dropped below the minimum needed to protect the furnace."),
    ("stand_motor_overcurrent", "Stand Motor Over-current", "MEDIUM", "Operations",
     "A rolling-mill stand drive motor is drawing current above its rated limit."),
    ("coiling_temperature_deviation", "Coiling Temperature Deviation", "MEDIUM", "Quality",
     "Strip coiling temperature has drifted outside its target window, putting coil quality at risk."),
    ("energy_price_spike", "Energy Price Spike", "LOW", "Energy",
     "Wholesale energy price has spiked above the configured cost threshold."),
]
onto_alarm_type_seed = spark.createDataFrame(
    ALARM_TYPES,
    "alarm_type_id string, alarm_type_name string, default_severity string, domain string, "
    "alarm_description string",
).dropDuplicates(["alarm_type_id"])

alarm_observed = None
try:
    if DeltaTable.isDeltaTable(spark, path("fact_alarm_event")):
        alarm_observed = (
            read("fact_alarm_event")
            .filter(F.col("alarm_type").isNotNull())
            .groupBy(F.col("alarm_type").cast("string").alias("alarm_type_id"))
            .agg(F.count(F.lit(1)).cast("bigint").alias("observed_count"))
        )
except Exception:
    # A missing or unreadable alarm fact must not sink the whole binding run.
    alarm_observed = None

if alarm_observed is not None:
    onto_alarm_type = onto_alarm_type_seed.join(alarm_observed, on="alarm_type_id", how="left").withColumn(
        "observed_count", F.coalesce(F.col("observed_count"), F.lit(0)).cast("bigint")
    )
else:
    onto_alarm_type = onto_alarm_type_seed.withColumn("observed_count", F.lit(0).cast("bigint"))
onto_alarm_type = onto_alarm_type.select(
    "alarm_type_id",
    "alarm_type_name",
    "default_severity",
    "domain",
    "observed_count",
    "alarm_description",
)
row_counts["onto_alarm_type"] = write_managed(onto_alarm_type, "onto_alarm_type")

# 15. onto_rel_class_specializes (rel 2003, EquipmentClass -> EquipmentClass) ----
# Derived from the taxonomy itself: every class with a parent specializes it.
onto_rel_class_specializes = (
    onto_equipment_class.filter(F.col("parent_class_id") != F.lit(""))
    .select(
        F.col("class_id").alias("child_class_id"),
        F.col("parent_class_id").alias("parent_class_id"),
    )
    .distinct()
)
onto_rel_class_specializes = keep_edges(
    onto_rel_class_specializes, "child_class_id", onto_equipment_class, "class_id"
)
onto_rel_class_specializes = keep_edges(
    onto_rel_class_specializes, "parent_class_id", onto_equipment_class, "class_id"
).select("child_class_id", "parent_class_id")
row_counts["onto_rel_class_specializes"] = write_managed(
    onto_rel_class_specializes, "onto_rel_class_specializes"
)

# 16. onto_rel_class_feeds (rel 2004, EquipmentClass -> EquipmentClass) ----------
# Curated process genealogy. This is the metallurgically correct chain: a blast
# furnace makes hot metal that goes to the BOF, and only then to the caster, so
# BlastFurnace feeds BasicOxygenFurnace (not the caster directly).
FEEDS = [
    ("BlastFurnace", "BasicOxygenFurnace"),
    ("BasicOxygenFurnace", "ContinuousCaster"),
    ("ElectricArcFurnace", "ContinuousCaster"),
    ("ContinuousCaster", "ReheatFurnace"),
    ("ContinuousCaster", "RollingMill"),
    ("ReheatFurnace", "RollingMill"),
]
onto_rel_class_feeds = spark.createDataFrame(FEEDS, "from_class_id string, to_class_id string").distinct()
onto_rel_class_feeds = keep_edges(onto_rel_class_feeds, "from_class_id", onto_equipment_class, "class_id")
onto_rel_class_feeds = keep_edges(
    onto_rel_class_feeds, "to_class_id", onto_equipment_class, "class_id"
).select("from_class_id", "to_class_id")
row_counts["onto_rel_class_feeds"] = write_managed(onto_rel_class_feeds, "onto_rel_class_feeds")

# 17. onto_rel_class_executes (rel 2005, EquipmentClass -> ProcessStep) ----------
EXECUTES = [
    ("BlastFurnace", "Ironmaking"),
    ("BasicOxygenFurnace", "PrimarySteelmaking"),
    ("ElectricArcFurnace", "PrimarySteelmaking"),
    ("ContinuousCaster", "ContinuousCasting"),
    ("ReheatFurnace", "Reheating"),
    ("RollingMill", "HotRolling"),
    ("HotStripMill", "HotRolling"),
    ("WireRodMill", "HotRolling"),
]
onto_rel_class_executes = spark.createDataFrame(EXECUTES, "class_id string, step_id string").distinct()
onto_rel_class_executes = keep_edges(onto_rel_class_executes, "class_id", onto_equipment_class, "class_id")
onto_rel_class_executes = keep_edges(
    onto_rel_class_executes, "step_id", onto_process_step, "step_id"
).select("class_id", "step_id")
row_counts["onto_rel_class_executes"] = write_managed(onto_rel_class_executes, "onto_rel_class_executes")

# 18. onto_rel_step_produces (rel 2006, ProcessStep -> ProductType) ------------------
PRODUCES = [
    ("Ironmaking", "HotMetal"),
    ("PrimarySteelmaking", "LiquidSteel"),
    ("SecondaryMetallurgy", "LiquidSteel"),
    ("ContinuousCasting", "SteelSlab"),
    ("ContinuousCasting", "SteelBillet"),
    ("HotRolling", "HotRolledCoil"),
    ("HotRolling", "WireRod"),
    ("ColdRollingAndCoating", "ColdRolledCoil"),
]
onto_rel_step_produces = spark.createDataFrame(PRODUCES, "step_id string, product_id string").distinct()
onto_rel_step_produces = keep_edges(onto_rel_step_produces, "step_id", onto_process_step, "step_id")
onto_rel_step_produces = keep_edges(
    onto_rel_step_produces, "product_id", onto_product, "product_id"
).select("step_id", "product_id")
row_counts["onto_rel_step_produces"] = write_managed(onto_rel_step_produces, "onto_rel_step_produces")

# 19. onto_rel_sensor_measures (rel 2007, Sensor -> Signal) ----------------------
# Real bridge from the physical sensor to the abstract signal it emits. Both ends
# are filtered to entities that actually exist (onto_sensor / onto_signal).
onto_rel_sensor_measures = (
    current_rows("dim_sensor")
    .select(
        sensor_uid().alias("sensor_uid"),
        F.col("signal_code").cast("string").alias("signal_code"),
    )
    .filter(F.col("sensor_uid").isNotNull() & F.col("signal_code").isNotNull())
    .distinct()
)
onto_rel_sensor_measures = keep_edges(onto_rel_sensor_measures, "sensor_uid", onto_sensor, "sensor_uid")
onto_rel_sensor_measures = keep_edges(
    onto_rel_sensor_measures, "signal_code", onto_signal, "signal_code"
).select("sensor_uid", "signal_code")
row_counts["onto_rel_sensor_measures"] = write_managed(onto_rel_sensor_measures, "onto_rel_sensor_measures")

# 20. onto_rel_asset_class (rel 2008, Asset -> EquipmentClass) -------------------
# instanceOf bridge: attach every real asset to the class whose asset_type_match
# equals its asset_type. Empty asset_type_match (abstract classes) is ignored;
# the inner joins guarantee both endpoints exist.
_class_match = onto_equipment_class.filter(F.col("asset_type_match") != F.lit("")).select(
    F.col("class_id"), F.col("asset_type_match")
)
onto_rel_asset_class = (
    onto_asset.join(_class_match, onto_asset["asset_type"] == _class_match["asset_type_match"], how="inner")
    .select(onto_asset["asset_id"].alias("asset_id"), _class_match["class_id"].alias("class_id"))
    .filter(F.col("asset_id").isNotNull() & F.col("class_id").isNotNull())
    .distinct()
)
row_counts["onto_rel_asset_class"] = write_managed(onto_rel_asset_class, "onto_rel_asset_class")

# 21. onto_rel_asset_supplies (rel 2009, Asset -> Asset) -------------------------
# Instance-level genealogy. parent_asset_id is an EMPTY STRING (not null) for a
# root asset, so both the null and "" cases are excluded. Both ends are semi-
# joined against onto_asset so a parent id with no matching asset row is dropped.
onto_rel_asset_supplies = (
    current_rows("dim_asset")
    .filter(
        F.col("parent_asset_id").isNotNull()
        & (F.col("parent_asset_id") != F.lit(""))
        & F.col("asset_id").isNotNull()
    )
    .select(
        F.col("parent_asset_id").cast("string").alias("from_asset_id"),
        F.col("asset_id").cast("string").alias("to_asset_id"),
    )
    .distinct()
)
onto_rel_asset_supplies = keep_edges(onto_rel_asset_supplies, "from_asset_id", onto_asset, "asset_id")
onto_rel_asset_supplies = keep_edges(
    onto_rel_asset_supplies, "to_asset_id", onto_asset, "asset_id"
).select("from_asset_id", "to_asset_id")
row_counts["onto_rel_asset_supplies"] = write_managed(onto_rel_asset_supplies, "onto_rel_asset_supplies")

# 22. onto_rel_alarm_signal (rel 2010, AlarmType -> Signal) ----------------------
# triggeredBy: curated links, then filtered to the signals that actually exist in
# onto_signal. If that telemetry reference data is not seeded the target signals
# are absent and this table is legitimately empty (see the allowed-empty set).
TRIGGERED_BY = [
    ("lining_rul_below_21d_threshold", "hearth_refractory_estimate"),
    ("hearth_shell_overtemperature", "hearth_shell_temperature"),
    ("cooling_water_flow_low", "cooling_water_flow"),
    ("stand_motor_overcurrent", "stand_motor_current"),
    ("coiling_temperature_deviation", "coiling_temperature"),
]
onto_rel_alarm_signal = spark.createDataFrame(
    TRIGGERED_BY, "alarm_type_id string, signal_code string"
).distinct()
onto_rel_alarm_signal = keep_edges(onto_rel_alarm_signal, "alarm_type_id", onto_alarm_type, "alarm_type_id")
onto_rel_alarm_signal = keep_edges(
    onto_rel_alarm_signal, "signal_code", onto_signal, "signal_code"
).select("alarm_type_id", "signal_code")
row_counts["onto_rel_alarm_signal"] = write_managed(onto_rel_alarm_signal, "onto_rel_alarm_signal")

# 23. onto_rel_alarm_class (rel 2011, AlarmType -> EquipmentClass) ---------------
# halts: which class each alarm takes down. Curated, then both ends filtered.
HALTS = [
    ("lining_rul_below_21d_threshold", "BlastFurnace"),
    ("hearth_shell_overtemperature", "BlastFurnace"),
    ("cooling_water_flow_low", "BlastFurnace"),
    ("stand_motor_overcurrent", "HotStripMill"),
    ("coiling_temperature_deviation", "HotStripMill"),
    ("energy_price_spike", "EnergySystem"),
]
onto_rel_alarm_class = spark.createDataFrame(HALTS, "alarm_type_id string, class_id string").distinct()
onto_rel_alarm_class = keep_edges(onto_rel_alarm_class, "alarm_type_id", onto_alarm_type, "alarm_type_id")
onto_rel_alarm_class = keep_edges(
    onto_rel_alarm_class, "class_id", onto_equipment_class, "class_id"
).select("alarm_type_id", "class_id")
row_counts["onto_rel_alarm_class"] = write_managed(onto_rel_alarm_class, "onto_rel_alarm_class")

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
    "onto_equipment_class",
    "onto_process_step",
    "onto_product",
    "onto_signal",
    "onto_alarm_type",
    "onto_rel_class_specializes",
    "onto_rel_class_feeds",
    "onto_rel_class_executes",
    "onto_rel_step_produces",
    "onto_rel_sensor_measures",
    "onto_rel_asset_class",
    "onto_rel_asset_supplies",
    "onto_rel_alarm_signal",
    "onto_rel_alarm_class",
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
# onto_sensor_reading may be empty when telemetry is not seeded; onto_rel_alarm_signal
# may be empty when the telemetry reference signals it triggers on do not exist yet.
ALLOWED_EMPTY = {"onto_sensor_reading", "onto_rel_alarm_signal"}
for name in empty:
    if name in ALLOWED_EMPTY:
        print(f"WARNING: {name} is empty (reference data may not be seeded).")
hard_empty = [name for name in empty if name not in ALLOWED_EMPTY]
if hard_empty:
    raise ValueError(f"Ontology binding tables are unexpectedly empty: {hard_empty}")

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
