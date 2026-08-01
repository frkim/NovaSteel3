"""Generate the NovaSteel V3 GraphModel item definition from the Ontology tree.

Fabric auto-creates a GraphModel when an Ontology is first published, but it does
NOT re-project that graph when the ontology schema later changes: the
``Refresh`` job only reloads rows for the node and edge tables that already
exist. Adding entity types or relationship types therefore leaves the graph
silently on the old schema, and every GQL query against a new label fails with
"syntax error or access rule violation".

So the graph projection is authored here instead of being left implicit. This
script reads ``fabric/items/onto-novasteelv3.Ontology`` - the same tree
Deploy-Ontology.ps1 publishes - and derives the six definition parts the
GraphModel item expects, so the ontology stays the single source of truth and
the two can never drift.

Only NonTimeSeries data bindings become node tables: a graph node carries the
static properties of an entity, while its time series stay in the lakehouse and
are reached through the semantic model.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
import uuid

WORKSPACE_ID = "3d9c0b49-5201-4914-8149-06071b529918"
CORE_LAKEHOUSE_ID = "623b4455-5c28-4235-8138-883d69a5810d"
GRAPH_DISPLAY_NAME = "onto_novasteelv3_graph_851e6dd07bb1441fa9e879bb6d2bb3b1"

# Stable node/edge table GUIDs so a redeploy does not churn the definition.
NS = uuid.UUID("6f2b1c40-0000-4000-8000-000000000001")

# Ontology value types -> graph property types (as emitted by the service).
TYPE_MAP = {
    "String": "STRING",
    "Boolean": "BOOLEAN",
    "Double": "FLOAT",
    "BigInt": "INT",
    "Int": "INT",
    "DateTime": "DATETIME",
}

REPO = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
ONTOLOGY = REPO / "fabric" / "items" / "onto-novasteelv3.Ontology"
OUT = REPO / "fabric" / "items" / "onto-novasteelv3-graph.GraphModel"

SCHEMA_BASE = "https://developer.microsoft.com/json-schemas/fabric/item"


def guid(name: str) -> str:
    return str(uuid.uuid5(NS, name))


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def only_child(directory: pathlib.Path) -> pathlib.Path | None:
    files = sorted(p for p in directory.glob("*.json")) if directory.exists() else []
    return files[0] if files else None


def data_source_name(table: str) -> str:
    return f"{CORE_LAKEHOUSE_ID}_{table}"


def data_source(table: str) -> dict:
    return {
        "name": data_source_name(table),
        "type": "DeltaTable",
        "properties": {
            "path": (
                f"abfss://{WORKSPACE_ID}@onelake.pbidedicated.windows.net/"
                f"{CORE_LAKEHOUSE_ID}/Tables/{table}"
            )
        },
    }


def read_ontology() -> tuple[list[dict], list[dict]]:
    """Return (entity types, relationship types), each enriched with its binding."""
    entities = []
    for directory in sorted(
        (ONTOLOGY / "EntityTypes").iterdir(), key=lambda p: int(p.name)
    ):
        definition = load(directory / "definition.json")
        properties = {p["id"]: p for p in definition["properties"]}

        # A node table is built from the single non-time-series binding; the
        # time-series binding feeds the ontology overview charts, not the graph.
        static_binding = None
        for binding_file in sorted((directory / "DataBindings").glob("*.json")):
            configuration = load(binding_file)["dataBindingConfiguration"]
            if configuration["dataBindingType"] == "NonTimeSeries":
                static_binding = configuration
                break
        if static_binding is None:
            raise ValueError(f"Entity type {definition['name']} has no static binding")

        entities.append(
            {
                "alias": definition["id"],
                "label": definition["name"],
                "key_property": properties[definition["entityIdParts"][0]]["name"],
                "properties": properties,
                "table": static_binding["sourceTableProperties"]["sourceTableName"],
                "bindings": static_binding["propertyBindings"],
            }
        )

    relationships = []
    for directory in sorted(
        (ONTOLOGY / "RelationshipTypes").iterdir(), key=lambda p: int(p.name)
    ):
        definition = load(directory / "definition.json")
        contextualization_file = only_child(directory / "Contextualizations")
        if contextualization_file is None:
            raise ValueError(f"Relationship {definition['name']} has no contextualization")
        contextualization = load(contextualization_file)
        relationships.append(
            {
                "alias": definition["id"],
                "label": definition["name"],
                "source_alias": definition["source"]["entityTypeId"],
                "target_alias": definition["target"]["entityTypeId"],
                "table": contextualization["dataBindingTable"]["sourceTableName"],
                "source_columns": [
                    b["sourceColumnName"] for b in contextualization["sourceKeyRefBindings"]
                ],
                "target_columns": [
                    b["sourceColumnName"] for b in contextualization["targetKeyRefBindings"]
                ],
            }
        )

    return entities, relationships


def build(entities: list[dict], relationships: list[dict]) -> dict[str, dict]:
    tables = [e["table"] for e in entities] + [r["table"] for r in relationships]

    node_tables = []
    node_types = []
    for entity in entities:
        node_tables.append(
            {
                "nodeTypeAlias": entity["alias"],
                "id": guid(f"node-{entity['label']}"),
                "dataSourceName": data_source_name(entity["table"]),
                "propertyMappings": [
                    {
                        "propertyName": entity["properties"][b["targetPropertyId"]]["name"],
                        "sourceColumn": b["sourceColumnName"],
                    }
                    for b in entity["bindings"]
                ],
            }
        )
        node_types.append(
            {
                "primaryKeyProperties": [entity["key_property"]],
                "alias": entity["alias"],
                "labels": [entity["label"]],
                "properties": [
                    {
                        "name": entity["properties"][b["targetPropertyId"]]["name"],
                        "type": TYPE_MAP[
                            entity["properties"][b["targetPropertyId"]]["valueType"]
                        ],
                    }
                    for b in entity["bindings"]
                ],
            }
        )

    edge_tables = []
    edge_types = []
    for relationship in relationships:
        # An edge row carries exactly its two key columns; the service maps each
        # straight through under its own column name.
        columns = relationship["source_columns"] + relationship["target_columns"]
        edge_tables.append(
            {
                "edgeTypeAlias": relationship["alias"],
                "id": guid(f"edge-{relationship['label']}"),
                "edgeIdMapping": None,
                "dataSourceName": data_source_name(relationship["table"]),
                "sourceNodeKeyColumns": relationship["source_columns"],
                "propertyMappings": [
                    {"propertyName": column, "sourceColumn": column} for column in columns
                ],
                "destinationNodeKeyColumns": relationship["target_columns"],
            }
        )
        edge_types.append(
            {
                "sourceNodeType": {"alias": relationship["source_alias"]},
                "alias": relationship["alias"],
                "destinationNodeType": {"alias": relationship["target_alias"]},
                "labels": [relationship["label"]],
                "properties": [
                    {"name": column, "type": "STRING"} for column in columns
                ],
            }
        )

    return {
        ".platform": {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": "GraphModel", "displayName": GRAPH_DISPLAY_NAME},
            "config": {
                "version": "2.0",
                "logicalId": "00000000-0000-0000-0000-000000000000",
            },
        },
        "dataSources.json": {
            "$schema": f"{SCHEMA_BASE}/graphInstance/definition/dataSources/1.0.0/schema.json",
            "dataSources": [data_source(table) for table in tables],
        },
        "graphDefinition.json": {
            "$schema": f"{SCHEMA_BASE}/graphInstance/definition/graphDefinition/1.0.0/schema.json",
            "nodeTables": node_tables,
            "edgeTables": edge_tables,
        },
        "graphType.json": {
            "$schema": f"{SCHEMA_BASE}/graphInstance/definition/graphType/1.0.0/schema.json",
            "nodeTypes": node_types,
            "edgeTypes": edge_types,
        },
        "graphSettings.json": {
            "$schema": f"{SCHEMA_BASE}/graphIndex/definition/graphSettings/1.0.0/schema.json"
        },
        "stylingConfiguration.json": {
            "$schema": f"{SCHEMA_BASE}/graphInstance/definition/stylingConfiguration/1.0.0/schema.json",
            "modelLayout": {
                "positions": {},
                "styles": {},
                "pan": {"x": 0.0, "y": 0.0},
                "zoomLevel": 1.0,
            },
        },
    }


def main() -> None:
    entities, relationships = read_ontology()
    parts = build(entities, relationships)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for name, payload in parts.items():
        (OUT / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {len(parts)} parts under {OUT}")
    print(f"  {len(entities)} node types: " + ", ".join(e["label"] for e in entities))
    print(
        f"  {len(relationships)} edge types: "
        + ", ".join(r["label"] for r in relationships)
    )


if __name__ == "__main__":
    main()
