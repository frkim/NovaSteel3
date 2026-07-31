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

# Pipeline parameters. The deployment script renders the defaults, and a
# Fabric Notebook activity can override them per environment/run.
ENVIRONMENT = "{{environment}}"
CORE_TABLES_URI = "{{onelake.coreTablesUri}}"
ONTOLOGY_VERSION = "novasteel-ontology/1.0.0"


def require_resolved(name: str, value: str) -> None:
    if not value or value.startswith("{{"):
        raise ValueError(f"{name} must be resolved to an environment value")


def table_path(root: str, table_name: str) -> str:
    return f"{root.rstrip('/')}/{table_name}"


def ensure_delta_table(root: str, table_name: str, schema_ddl: str, partitions=()) -> None:
    path = table_path(root, table_name)
    if DeltaTable.isDeltaTable(spark, path):
        return
    frame = spark.createDataFrame([], schema_ddl)
    writer = frame.write.format("delta").mode("ignore")
    if partitions:
        writer = writer.partitionBy(*partitions)
    writer.save(path)


require_resolved("ENVIRONMENT", ENVIRONMENT)
require_resolved("CORE_TABLES_URI", CORE_TABLES_URI)

# --- Table schemas ---
_ENTITY_FULL_DDL = (
    "entity_key long, entity_id string, entity_type string, entity_name string, "
    "domain string, description string, parent_entity_id string, is_abstract boolean, "
    "properties_json string, valid_from timestamp, valid_to timestamp, is_current boolean, version int"
)
_RELATIONSHIP_FULL_DDL = (
    "relationship_key long, relationship_id string, source_entity_id string, "
    "target_entity_id string, relationship_type string, cardinality string, "
    "description string, properties_json string, valid_from timestamp, valid_to timestamp, is_current boolean"
)
_PROPERTY_FULL_DDL = (
    "property_key long, property_id string, entity_id string, property_name string, "
    "property_type string, unit string, description string, allowed_values_json string, "
    "is_required boolean, valid_from timestamp, valid_to timestamp, is_current boolean"
)

ensure_delta_table(CORE_TABLES_URI, "ontology_entity", _ENTITY_FULL_DDL)
ensure_delta_table(CORE_TABLES_URI, "ontology_relationship", _RELATIONSHIP_FULL_DDL)
ensure_delta_table(CORE_TABLES_URI, "ontology_property", _PROPERTY_FULL_DDL)

# --- Entity source data ---
# (entity_key, entity_id, entity_type, entity_name, domain, description, parent_entity_id, is_abstract, properties_json)
_ENTITY_SOURCE_DDL = (
    "entity_key long, entity_id string, entity_type string, entity_name string, "
    "domain string, description string, parent_entity_id string, is_abstract boolean, "
    "properties_json string"
)

raw_entities = [
    # Plant hierarchy
    (1,  "NS:Plant",             "Class", "Plant",             "Manufacturing",
     "Abstract steel manufacturing facility.",                       None,          True,
     "{}"),
    (2,  "NS:LuxembourgPlant",   "Class", "Luxembourg Plant",  "Manufacturing",
     "Steel plant in Luxembourg (NS-DEMO-LUX-01).",                 "NS:Plant",    False,
     '{"country":"LU","plantCode":"NS-DEMO-LUX-01"}'),
    (3,  "NS:BelgiumPlant",      "Class", "Belgium Plant",     "Manufacturing",
     "Steel plant in Belgium (NS-DEMO-BE-01).",                     "NS:Plant",    False,
     '{"country":"BE","plantCode":"NS-DEMO-BE-01"}'),
    (4,  "NS:NetherlandsPlant",  "Class", "Netherlands Plant", "Manufacturing",
     "Steel plant in the Netherlands (NS-DEMO-NL-01).",            "NS:Plant",    False,
     '{"country":"NL","plantCode":"NS-DEMO-NL-01"}'),
    (5,  "NS:GermanyPlant",      "Class", "Germany Plant",     "Manufacturing",
     "Steel plant in Germany (NS-DEMO-DE-01).",                    "NS:Plant",    False,
     '{"country":"DE","plantCode":"NS-DEMO-DE-01"}'),
    # Production unit hierarchy
    (6,  "NS:ProductionUnit",    "Class", "Production Unit",   "Manufacturing",
     "Abstract steel production unit.",                             None,          True,
     "{}"),
    (7,  "NS:BlastFurnace",      "Class", "Blast Furnace",     "Manufacturing",
     "Iron-making blast furnace (BF-BOF route).",                  "NS:ProductionUnit", False,
     '{"assetType":"BF","route":"BF-BOF"}'),
    (8,  "NS:ElectricArcFurnace","Class", "Electric Arc Furnace","Manufacturing",
     "Electric arc steelmaking furnace (EAF route).",              "NS:ProductionUnit", False,
     '{"assetType":"EAF","route":"EAF"}'),
    (9,  "NS:ReheatingFurnace",  "Class", "Reheating Furnace", "Manufacturing",
     "Slab or billet reheating furnace before rolling.",           "NS:ProductionUnit", False,
     '{"assetType":"RHF"}'),
    (10, "NS:ContinuousCaster",  "Class", "Continuous Caster", "Manufacturing",
     "Continuously casts liquid steel into slabs or billets.",     "NS:ProductionUnit", False,
     '{"assetType":"CC"}'),
    (11, "NS:RollingMill",       "Class", "Rolling Mill",      "Manufacturing",
     "Hot or cold rolling mill for flat or long products.",        "NS:ProductionUnit", False,
     '{"assetType":"RM"}'),
    # Sensor hierarchy
    (12, "NS:Sensor",            "Class", "Sensor",            "Telemetry",
     "Abstract IoT sensor measuring process variables.",           None,          True,
     "{}"),
    (13, "NS:TemperatureSensor", "Class", "Temperature Sensor","Telemetry",
     "Measures temperature in degrees Celsius.",                   "NS:Sensor",   False,
     '{"signalType":"temperature","unit":"degC"}'),
    (14, "NS:PressureSensor",    "Class", "Pressure Sensor",   "Telemetry",
     "Measures pressure in bar or kPa.",                          "NS:Sensor",   False,
     '{"signalType":"pressure","unit":"bar"}'),
    (15, "NS:FlowSensor",        "Class", "Flow Sensor",       "Telemetry",
     "Measures volumetric or mass flow rate.",                    "NS:Sensor",   False,
     '{"signalType":"flow","unit":"m3/h"}'),
    (16, "NS:VibrationSensor",   "Class", "Vibration Sensor",  "Telemetry",
     "Measures mechanical vibration amplitude and frequency.",    "NS:Sensor",   False,
     '{"signalType":"vibration","unit":"mm/s"}'),
    # Product hierarchy
    (17, "NS:Product",           "Class", "Product",           "Manufacturing",
     "Abstract steel product.",                                   None,          False,
     "{}"),
    (18, "NS:SteelSlab",         "Class", "Steel Slab",        "Manufacturing",
     "Rectangular semi-finished flat steel product.",             "NS:Product",  False,
     '{"shape":"rectangular","semifinished":true}'),
    (19, "NS:SteelBillet",       "Class", "Steel Billet",      "Manufacturing",
     "Long semi-finished product with square cross-section.",     "NS:Product",  False,
     '{"shape":"square_section","semifinished":true}'),
    (20, "NS:SteelCoil",         "Class", "Steel Coil",        "Manufacturing",
     "Hot- or cold-rolled steel strip wound into a coil.",        "NS:Product",  False,
     '{"shape":"coil","semifinished":false}'),
    # Process hierarchy
    (21, "NS:Process",           "Class", "Process",           "Manufacturing",
     "Abstract steel production process.",                        None,          False,
     "{}"),
    (22, "NS:SmeltingProcess",   "Class", "Smelting Process",  "Manufacturing",
     "Iron ore reduction and steelmaking in blast furnace or EAF.","NS:Process", False,
     '{"stage":"primary"}'),
    (23, "NS:CastingProcess",    "Class", "Casting Process",   "Manufacturing",
     "Liquid steel solidification via continuous caster.",        "NS:Process",  False,
     '{"stage":"secondary"}'),
    (24, "NS:RollingProcess",    "Class", "Rolling Process",   "Manufacturing",
     "Hot or cold rolling of reheated steel semi-products.",      "NS:Process",  False,
     '{"stage":"finishing"}'),
    # Standalone entities
    (25, "NS:EnergySource",      "Class", "Energy Source",     "Energy",
     "Energy supply entity (electricity, gas, coal, coke, hydrogen).", None,     False,
     "{}"),
    (26, "NS:AlarmEvent",        "Class", "Alarm Event",       "Operations",
     "Process or safety alarm event raised by a sensor or control system.", None, False,
     "{}"),
    (27, "NS:MaintenanceOrder",  "Class", "Maintenance Order", "Maintenance",
     "Planned, corrective, or predictive maintenance work order.", None,          False,
     "{}"),
    (28, "NS:QualityControl",    "Class", "Quality Control",   "Quality",
     "Quality inspection, test, or conformance gate.",            None,          False,
     "{}"),
    (29, "NS:Signal",            "Class", "Signal",            "Telemetry",
     "Named physical signal time-series measured by one or more sensors.", None,  False,
     "{}"),
]

entity_frame = (
    spark.createDataFrame(raw_entities, _ENTITY_SOURCE_DDL)
    .withColumn("valid_from", F.lit("2026-07-25 00:00:00").cast("timestamp"))
    .withColumn("valid_to",   F.lit(None).cast("timestamp"))
    .withColumn("is_current", F.lit(True))
    .withColumn("version",    F.lit(1))
)

entity_path = table_path(CORE_TABLES_URI, "ontology_entity")
(
    DeltaTable.forPath(spark, entity_path)
    .alias("target")
    .merge(
        entity_frame.alias("source"),
        "target.entity_id = source.entity_id",
    )
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)

# --- Relationship source data ---
# (relationship_key, relationship_id, source_entity_id, target_entity_id,
#  relationship_type, cardinality, description, properties_json)
_RELATIONSHIP_SOURCE_DDL = (
    "relationship_key long, relationship_id string, source_entity_id string, "
    "target_entity_id string, relationship_type string, cardinality string, "
    "description string, properties_json string"
)

raw_relationships = [
    (1,  "NS:REL-001", "NS:Plant",          "NS:ProductionUnit",  "hasUnit",       "ONE_TO_MANY",
     "A plant contains one or more production units.",                                      "{}"),
    (2,  "NS:REL-002", "NS:ProductionUnit", "NS:Sensor",          "hasSensor",     "ONE_TO_MANY",
     "A production unit has one or more sensors attached.",                                "{}"),
    (3,  "NS:REL-003", "NS:ProductionUnit", "NS:Process",         "executes",      "MANY_TO_MANY",
     "A production unit can execute various production processes.",                        "{}"),
    (4,  "NS:REL-004", "NS:Process",        "NS:Product",         "produces",      "ONE_TO_ONE",
     "A production process step produces a steel product.",                                "{}"),
    (5,  "NS:REL-005", "NS:Sensor",         "NS:Signal",          "measures",      "ONE_TO_MANY",
     "A sensor measures one or more physical signals.",                                    "{}"),
    (6,  "NS:REL-006", "NS:AlarmEvent",     "NS:Sensor",          "triggeredBy",   "MANY_TO_ONE",
     "An alarm event is triggered by a sensor reading crossing a threshold.",              "{}"),
    (7,  "NS:REL-007", "NS:MaintenanceOrder","NS:ProductionUnit", "appliesTo",     "MANY_TO_ONE",
     "A maintenance order applies to a specific production unit.",                        "{}"),
    (8,  "NS:REL-008", "NS:QualityControl", "NS:Product",         "tests",         "ONE_TO_MANY",
     "A quality control inspection tests one or more products.",                          "{}"),
    (9,  "NS:REL-009", "NS:ProductionUnit", "NS:EnergySource",    "consumes",      "MANY_TO_MANY",
     "A production unit consumes multiple energy sources.",                               "{}"),
    (10, "NS:REL-010", "NS:Plant",          "NS:Product",         "produces",      "ONE_TO_MANY",
     "A plant produces one or more product types.",                                       "{}"),
    (11, "NS:REL-011", "NS:BlastFurnace",   "NS:ContinuousCaster","feeds",         "ONE_TO_ONE",
     "A blast furnace feeds hot metal to the continuous caster.",                         "{}"),
    (12, "NS:REL-012", "NS:ContinuousCaster","NS:SteelSlab",      "casts",         "ONE_TO_MANY",
     "A continuous caster casts liquid steel into slabs.",                                "{}"),
    (13, "NS:REL-013", "NS:RollingMill",    "NS:SteelSlab",       "processes",     "ONE_TO_MANY",
     "A rolling mill processes steel slabs into finished products.",                      "{}"),
    (14, "NS:REL-014", "NS:QualityControl", "NS:Process",         "monitors",      "ONE_TO_MANY",
     "Quality control monitors one or more production processes.",                        "{}"),
    (15, "NS:REL-015", "NS:AlarmEvent",     "NS:MaintenanceOrder","blocks",        "MANY_TO_MANY",
     "A critical alarm can block or trigger a maintenance order.",                        "{}"),
    (16, "NS:REL-016", "NS:AlarmEvent",     "NS:ProductionUnit",  "halts",         "MANY_TO_ONE",
     "A critical alarm can halt a production unit.",                                      "{}"),
]

relationship_frame = (
    spark.createDataFrame(raw_relationships, _RELATIONSHIP_SOURCE_DDL)
    .withColumn("valid_from", F.lit("2026-07-25 00:00:00").cast("timestamp"))
    .withColumn("valid_to",   F.lit(None).cast("timestamp"))
    .withColumn("is_current", F.lit(True))
)

relationship_path = table_path(CORE_TABLES_URI, "ontology_relationship")
(
    DeltaTable.forPath(spark, relationship_path)
    .alias("target")
    .merge(
        relationship_frame.alias("source"),
        "target.relationship_id = source.relationship_id",
    )
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)

# --- Property source data ---
# (property_key, property_id, entity_id, property_name, property_type,
#  unit, description, allowed_values_json, is_required)
_PROPERTY_SOURCE_DDL = (
    "property_key long, property_id string, entity_id string, property_name string, "
    "property_type string, unit string, description string, allowed_values_json string, "
    "is_required boolean"
)

raw_properties = [
    # NS:Plant
    (1,  "NS:PROP-001", "NS:Plant",             "country",
     "string",  "",         "ISO 3166-1 alpha-2 country code.",
     '["LU","BE","NL","DE"]',                                                     True),
    (2,  "NS:PROP-002", "NS:Plant",             "timezone",
     "string",  "",         "IANA timezone identifier (e.g. Europe/Luxembourg).",
     "null",                                                                       True),
    (3,  "NS:PROP-003", "NS:Plant",             "maxCapacityTonnesPerDay",
     "double",  "t/day",    "Maximum crude steel production capacity per day.",
     "null",                                                                       False),
    (4,  "NS:PROP-004", "NS:Plant",             "currencyCode",
     "string",  "",         "ISO 4217 currency code for local cost reporting.",
     '["EUR"]',                                                                    True),
    # NS:BlastFurnace
    (5,  "NS:PROP-005", "NS:BlastFurnace",      "innerVolumeCubicMeters",
     "double",  "m3",       "Inner working volume of the blast furnace.",
     "null",                                                                       False),
    (6,  "NS:PROP-006", "NS:BlastFurnace",      "campaignDaysRemaining",
     "int",     "days",     "Remaining days in the current furnace campaign before reline.",
     "null",                                                                       False),
    (7,  "NS:PROP-007", "NS:BlastFurnace",      "liningThicknessMm",
     "double",  "mm",       "Current refractory lining thickness measured by probes.",
     "null",                                                                       False),
    (8,  "NS:PROP-008", "NS:BlastFurnace",      "targetTemperatureCelsius",
     "double",  "degC",     "Target hot metal temperature at the taphole.",
     "null",                                                                       False),
    # NS:ElectricArcFurnace
    (9,  "NS:PROP-009", "NS:ElectricArcFurnace","powerRatingMW",
     "double",  "MW",       "Installed transformer power rating in megawatts.",
     "null",                                                                       False),
    (10, "NS:PROP-010", "NS:ElectricArcFurnace","tapToTapTimeMinutes",
     "double",  "min",      "Cycle time between successive taps.",
     "null",                                                                       False),
    (11, "NS:PROP-011", "NS:ElectricArcFurnace","electrodeConsumptionKgPerTonne",
     "double",  "kg/t",     "Graphite electrode consumption per tonne of liquid steel.",
     "null",                                                                       False),
    # NS:Sensor
    (12, "NS:PROP-012", "NS:Sensor",            "sensorType",
     "string",  "",
     "Classification of the sensor by measured variable.",
     '["temperature","pressure","flow","vibration","current","voltage","level"]',  True),
    (13, "NS:PROP-013", "NS:Sensor",            "measurementUnit",
     "string",  "",         "SI unit of the measured signal (e.g. degC, bar, m3/h).",
     "null",                                                                       True),
    (14, "NS:PROP-014", "NS:Sensor",            "samplingFrequencyHz",
     "double",  "Hz",       "Signal sampling frequency in hertz.",
     "null",                                                                       False),
    (15, "NS:PROP-015", "NS:Sensor",            "accuracyPct",
     "double",  "%",        "Sensor measurement accuracy as percentage of full scale.",
     "null",                                                                       False),
    (16, "NS:PROP-016", "NS:Sensor",            "calibrationDate",
     "date",    "",         "Date of last sensor calibration.",
     "null",                                                                       False),
    # NS:Product
    (17, "NS:PROP-017", "NS:Product",           "gradeCode",
     "string",  "",         "Steel grade identifier conforming to EN or ASTM standard.",
     "null",                                                                       True),
    (18, "NS:PROP-018", "NS:Product",           "weightKg",
     "double",  "kg",       "Product weight in kilograms.",
     "null",                                                                       False),
    (19, "NS:PROP-019", "NS:Product",           "widthMm",
     "double",  "mm",       "Product width in millimetres.",
     "null",                                                                       False),
    (20, "NS:PROP-020", "NS:Product",           "thicknessMm",
     "double",  "mm",       "Product thickness in millimetres.",
     "null",                                                                       False),
    (21, "NS:PROP-021", "NS:Product",           "lengthMm",
     "double",  "mm",       "Product length in millimetres.",
     "null",                                                                       False),
    (22, "NS:PROP-022", "NS:Product",           "co2KgPerTonne",
     "double",  "kg CO2/t", "Embodied CO2 equivalent emissions per tonne of product.",
     "null",                                                                       False),
    # NS:AlarmEvent
    (23, "NS:PROP-023", "NS:AlarmEvent",        "severity",
     "string",  "",         "Alarm severity level.",
     '["LOW","MEDIUM","HIGH","CRITICAL"]',                                         True),
    (24, "NS:PROP-024", "NS:AlarmEvent",        "alarmCode",
     "string",  "",         "Unique alarm code from the alarm management system.",
     "null",                                                                       True),
    (25, "NS:PROP-025", "NS:AlarmEvent",        "threshold",
     "double",  "",         "Configured sensor trigger threshold.",
     "null",                                                                       False),
    (26, "NS:PROP-026", "NS:AlarmEvent",        "observedValue",
     "double",  "",         "Sensor value that triggered the alarm.",
     "null",                                                                       False),
    # NS:Process
    (27, "NS:PROP-027", "NS:Process",           "processVersion",
     "string",  "",         "Version identifier of the process recipe or operating standard.",
     "null",                                                                       False),
    (28, "NS:PROP-028", "NS:Process",           "targetYieldPct",
     "double",  "%",        "Target material yield percentage for the process step.",
     "null",                                                                       False),
    (29, "NS:PROP-029", "NS:Process",           "plannedDurationMinutes",
     "double",  "min",      "Planned duration of the process step in minutes.",
     "null",                                                                       False),
    # NS:QualityControl
    (30, "NS:PROP-030", "NS:QualityControl",    "testMethod",
     "string",  "",         "Laboratory or inline test method used.",
     "null",                                                                       True),
    (31, "NS:PROP-031", "NS:QualityControl",    "testResult",
     "string",  "",         "Outcome of the quality test.",
     '["PASS","FAIL","CONDITIONAL"]',                                              True),
    (32, "NS:PROP-032", "NS:QualityControl",    "laboratoryId",
     "string",  "",         "Identifier of the laboratory performing the test.",
     "null",                                                                       False),
    # NS:EnergySource
    (33, "NS:PROP-033", "NS:EnergySource",      "energyType",
     "string",  "",         "Type of energy source.",
     '["ELECTRICITY","NATURAL_GAS","COAL","COKE","HYDROGEN","BIOMASS"]',           True),
    (34, "NS:PROP-034", "NS:EnergySource",      "capacityMW",
     "double",  "MW",       "Available or contracted capacity in megawatts.",
     "null",                                                                       False),
    (35, "NS:PROP-035", "NS:EnergySource",      "carbonIntensityKgPerMWh",
     "double",  "kg CO2/MWh","Lifecycle carbon intensity of the energy source.",
     "null",                                                                       False),
    # NS:MaintenanceOrder
    (36, "NS:PROP-036", "NS:MaintenanceOrder",  "orderType",
     "string",  "",         "Maintenance order classification.",
     '["PREVENTIVE","CORRECTIVE","PREDICTIVE","INSPECTION"]',                      True),
    (37, "NS:PROP-037", "NS:MaintenanceOrder",  "plannedDurationHours",
     "double",  "h",        "Planned duration of the maintenance activity in hours.",
     "null",                                                                       False),
    (38, "NS:PROP-038", "NS:MaintenanceOrder",  "maintenanceTeam",
     "string",  "",         "Team or contractor responsible for the maintenance work.",
     "null",                                                                       False),
]

property_frame = (
    spark.createDataFrame(raw_properties, _PROPERTY_SOURCE_DDL)
    .withColumn("valid_from", F.lit("2026-07-25 00:00:00").cast("timestamp"))
    .withColumn("valid_to",   F.lit(None).cast("timestamp"))
    .withColumn("is_current", F.lit(True))
)

property_path = table_path(CORE_TABLES_URI, "ontology_property")
(
    DeltaTable.forPath(spark, property_path)
    .alias("target")
    .merge(
        property_frame.alias("source"),
        "target.property_id = source.property_id",
    )
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)

entity_count       = spark.read.format("delta").load(entity_path).count()
relationship_count = spark.read.format("delta").load(relationship_path).count()
property_count     = spark.read.format("delta").load(property_path).count()

print(
    {
        "status": "ontology_loaded",
        "environment": ENVIRONMENT,
        "entity_count": entity_count,
        "relationship_count": relationship_count,
        "property_count": property_count,
        "ontology_version": ONTOLOGY_VERSION,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
)

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
