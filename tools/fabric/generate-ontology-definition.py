"""Generate the authored NovaSteel V3 Fabric IQ Ontology item tree.

The ontology is committed as readable JSON (one file per entity type, data
binding, relationship type and contextualization) exactly mirroring the shape
the Fabric item-definition API expects. Deploy-Ontology.ps1 walks this tree and
base64-encodes each file into a definition part, so what is in git is exactly
what is deployed.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import uuid

WORKSPACE_ID = "3d9c0b49-5201-4914-8149-06071b529918"
CORE_LAKEHOUSE_ID = "623b4455-5c28-4235-8138-883d69a5810d"

import sys

REPO = pathlib.Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else r"D:\work\_Default GH Repos\copilot-worktrees\20260724 - Novasteel 3\frkim-studious-engine"
)
OUT = REPO / "fabric" / "items" / "onto-novasteelv3.Ontology"

# Stable binding/contextualization GUIDs so redeploys are idempotent.
NS = uuid.UUID("6f2b1c40-0000-4000-8000-000000000000")


def guid(name: str) -> str:
    return str(uuid.uuid5(NS, name))


def prop(pid: int, name: str, value_type: str) -> dict:
    return {
        "id": str(pid),
        "name": name,
        "redefines": None,
        "baseTypeNamespaceType": None,
        "valueType": value_type,
    }


def lakehouse_source(table: str) -> dict:
    # The core lakehouse is not schema-enabled: tables live directly under
    # Tables/, so sourceSchema is deliberately omitted.
    return {
        "sourceType": "LakehouseTable",
        "workspaceId": WORKSPACE_ID,
        "itemId": CORE_LAKEHOUSE_ID,
        "sourceTableName": table,
    }


ENTITY_TYPES = [
    {
        "id": 1001,
        "name": "Plant",
        "key": 30011,
        "displayName": 30012,
        "properties": [
            prop(30011, "PlantId", "String"),
            prop(30012, "PlantName", "String"),
            prop(30013, "CountryCode", "String"),
            prop(30014, "TimeZone", "String"),
            prop(30015, "ProcessRoute", "String"),
        ],
        "timeseriesProperties": [
            prop(30021, "PlantMetricTs", "DateTime"),
            prop(30022, "EnergyGj", "Double"),
            prop(30023, "ElectricityMwh", "Double"),
            prop(30024, "EnergyCostEur", "Double"),
            prop(30025, "TotalCo2eT", "Double"),
            prop(30026, "CrudeSteelTons", "Double"),
            prop(30027, "GoodTons", "Double"),
        ],
        "bindings": [
            {
                "name": "plant-static",
                "type": "NonTimeSeries",
                "table": "onto_plant",
                "map": [
                    ("plant_id", 30011),
                    ("plant_name", 30012),
                    ("country_code", 30013),
                    ("time_zone", 30014),
                    ("route", 30015),
                ],
            },
            {
                "name": "plant-daily",
                "type": "TimeSeries",
                "table": "onto_plant_daily",
                "timestamp": "metric_ts",
                "map": [
                    ("plant_id", 30011),
                    ("metric_ts", 30021),
                    ("energy_gj", 30022),
                    ("electricity_mwh", 30023),
                    ("energy_cost_eur", 30024),
                    ("total_co2e_t", 30025),
                    ("crude_steel_tons", 30026),
                    ("good_tons", 30027),
                ],
            },
        ],
        "overview": {"title": "Daily energy (GJ)", "yAxisPropertyId": "30022"},
    },
    {
        "id": 1002,
        "name": "Asset",
        "key": 30031,
        "displayName": 30031,
        "properties": [
            prop(30031, "AssetId", "String"),
            prop(30032, "AssetPlantId", "String"),
            prop(30033, "AssetType", "String"),
            prop(30034, "AssetArea", "String"),
            prop(30035, "LineId", "String"),
            prop(30036, "Criticality", "String"),
            prop(30037, "CommissionedState", "String"),
        ],
        "timeseriesProperties": [
            prop(30041, "HealthScoredAt", "DateTime"),
            prop(30042, "RulDays", "Double"),
            prop(30043, "RulDaysLow", "Double"),
            prop(30044, "RulDaysHigh", "Double"),
            prop(30045, "RiskScore", "Double"),
            prop(30046, "HealthConfidence", "Double"),
        ],
        "bindings": [
            {
                "name": "asset-static",
                "type": "NonTimeSeries",
                "table": "onto_asset",
                "map": [
                    ("asset_id", 30031),
                    ("plant_id", 30032),
                    ("asset_type", 30033),
                    ("area", 30034),
                    ("line_id", 30035),
                    ("criticality", 30036),
                    ("commissioned_state", 30037),
                ],
            },
            {
                "name": "asset-health",
                "type": "TimeSeries",
                "table": "onto_asset_health",
                "timestamp": "scored_at",
                "map": [
                    ("asset_id", 30031),
                    ("scored_at", 30041),
                    ("rul_days", 30042),
                    ("rul_days_low", 30043),
                    ("rul_days_high", 30044),
                    ("risk_score", 30045),
                    ("confidence", 30046),
                ],
            },
        ],
        "overview": {
            "title": "Remaining useful life (days)",
            "yAxisPropertyId": "30042",
        },
    },
    {
        "id": 1003,
        "name": "Sensor",
        "key": 30051,
        "displayName": 30051,
        "properties": [
            prop(30051, "SensorUid", "String"),
            prop(30052, "SensorId", "String"),
            prop(30053, "SignalCode", "String"),
            prop(30054, "SensorAssetId", "String"),
            prop(30055, "SensorPlantId", "String"),
            prop(30056, "CanonicalUnit", "String"),
            prop(30057, "HardMin", "Double"),
            prop(30058, "HardMax", "Double"),
            prop(30059, "SamplePeriodMs", "BigInt"),
        ],
        "timeseriesProperties": [
            prop(30061, "ReadingTs", "DateTime"),
            prop(30062, "ReadingValue", "Double"),
            prop(30063, "ReadingUnit", "String"),
            prop(30064, "SourceQuality", "String"),
        ],
        "bindings": [
            {
                "name": "sensor-static",
                "type": "NonTimeSeries",
                "table": "onto_sensor",
                "map": [
                    ("sensor_uid", 30051),
                    ("sensor_id", 30052),
                    ("signal_code", 30053),
                    ("asset_id", 30054),
                    ("plant_id", 30055),
                    ("canonical_unit", 30056),
                    ("hard_min", 30057),
                    ("hard_max", 30058),
                    ("sample_period_ms", 30059),
                ],
            },
            {
                "name": "sensor-reading",
                "type": "TimeSeries",
                "table": "onto_sensor_reading",
                "timestamp": "reading_ts",
                "map": [
                    ("sensor_uid", 30051),
                    ("reading_ts", 30061),
                    ("reading_value", 30062),
                    ("reading_unit", 30063),
                    ("source_quality", 30064),
                ],
            },
        ],
        "overview": {"title": "Sensor reading", "yAxisPropertyId": "30062"},
    },
    {
        "id": 1004,
        "name": "Grade",
        "key": 30071,
        "displayName": 30071,
        "properties": [
            prop(30071, "GradeCode", "String"),
            prop(30072, "GradeFamily", "String"),
            prop(30073, "HighGradeFlag", "Boolean"),
        ],
        "timeseriesProperties": [],
        "bindings": [
            {
                "name": "grade-static",
                "type": "NonTimeSeries",
                "table": "onto_grade",
                "map": [
                    ("grade_code", 30071),
                    ("grade_family", 30072),
                    ("high_grade_flag", 30073),
                ],
            }
        ],
        "overview": None,
    },
]

RELATIONSHIP_TYPES = [
    {
        "id": 2001,
        "name": "hasAsset",
        "source": 1001,
        "target": 1002,
        "table": "onto_rel_plant_asset",
        "sourceKey": [("plant_id", 30011)],
        "targetKey": [("asset_id", 30031)],
    },
    {
        "id": 2002,
        "name": "hasSensor",
        "source": 1002,
        "target": 1003,
        "table": "onto_rel_asset_sensor",
        "sourceKey": [("asset_id", 30031)],
        "targetKey": [("sensor_uid", 30051)],
    },
]


def write(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    # Regenerate from scratch so renamed entity/relationship types never leave
    # a stale definition or contextualization file behind.
    if OUT.exists():
        shutil.rmtree(OUT)

    write(
        OUT / ".platform",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {
                "type": "Ontology",
                "displayName": "onto_novasteelv3",
                "description": "NovaSteel V3 enterprise vocabulary: the AI-facing semantic layer that grounds the data agent in plants, assets, sensors and grades.",
            },
            "config": {
                "version": "2.0",
                "logicalId": "00000000-0000-0000-0000-000000000016",
            },
        },
    )
    write(OUT / "definition.json", {})

    for et in ENTITY_TYPES:
        base = OUT / "EntityTypes" / str(et["id"])
        write(
            base / "definition.json",
            {
                "id": str(et["id"]),
                "namespace": "usertypes",
                "baseEntityTypeId": None,
                "name": et["name"],
                "entityIdParts": [str(et["key"])],
                "displayNamePropertyId": str(et["displayName"]),
                "namespaceType": "Custom",
                "visibility": "Visible",
                "properties": et["properties"],
                "timeseriesProperties": et["timeseriesProperties"],
            },
        )
        for b in et["bindings"]:
            cfg = {
                "dataBindingType": b["type"],
                "propertyBindings": [
                    {"sourceColumnName": c, "targetPropertyId": str(p)}
                    for c, p in b["map"]
                ],
                "sourceTableProperties": lakehouse_source(b["table"]),
            }
            if b["type"] == "TimeSeries":
                cfg = {
                    "dataBindingType": b["type"],
                    "timestampColumnName": b["timestamp"],
                    "propertyBindings": cfg["propertyBindings"],
                    "sourceTableProperties": cfg["sourceTableProperties"],
                }
            bid = guid(b["name"])
            write(
                base / "DataBindings" / f"{bid}.json",
                {"id": bid, "dataBindingConfiguration": cfg},
            )
        if et["overview"]:
            write(
                base / "Overviews" / "definition.json",
                {
                    "widgets": [
                        {
                            "type": "lineChart",
                            "yAxisPropertyId": et["overview"]["yAxisPropertyId"],
                            "id": guid(f"widget-{et['name']}"),
                            "title": et["overview"]["title"],
                        }
                    ],
                    "settings": {
                        "type": "fixedTime",
                        "fixedTimeRange": "Last30Days",
                        "interval": "OneDay",
                        "aggregation": "Average",
                    },
                },
            )

    for rt in RELATIONSHIP_TYPES:
        base = OUT / "RelationshipTypes" / str(rt["id"])
        write(
            base / "definition.json",
            {
                "namespace": "usertypes",
                "id": str(rt["id"]),
                "name": rt["name"],
                "namespaceType": "Custom",
                "source": {"entityTypeId": str(rt["source"])},
                "target": {"entityTypeId": str(rt["target"])},
            },
        )
        cid = guid(f"ctx-{rt['name']}")
        write(
            base / "Contextualizations" / f"{cid}.json",
            {
                "id": cid,
                "dataBindingTable": lakehouse_source(rt["table"]),
                "sourceKeyRefBindings": [
                    {"sourceColumnName": c, "targetPropertyId": str(p)}
                    for c, p in rt["sourceKey"]
                ],
                "targetKeyRefBindings": [
                    {"sourceColumnName": c, "targetPropertyId": str(p)}
                    for c, p in rt["targetKey"]
                ],
            },
        )

    files = sorted(p for p in OUT.rglob("*") if p.is_file())
    print(f"wrote {len(files)} files under {OUT}")
    for f in files:
        print("  " + f.relative_to(OUT).as_posix())


if __name__ == "__main__":
    main()
