"""Offline validation of the NovaSteel real-time Eventstream path.

These checks run without a live Fabric capacity. They assert that the authored
``es-ns-telemetry-v1`` Eventstream definition, the ``kql-ns-operations`` KQL
database schema, the item catalogue and the single-workspace deployment
parameters are mutually consistent, and that the KQL ingestion mappings line up
with the envelope the simulator actually emits.

Why this matters: the hot KQL tables silently stayed empty in the live workspace
because the Eventhouse destinations were authored with ``ProcessedIngestion`` (a
no-op without an explicit inline schema) instead of ``DirectIngestion`` with a
named JSON mapping, and because the ``model_inference`` mapping read its fields
from the top level when the simulator nests them under ``payload``. Both classes
of bug are now guarded here so they cannot silently regress.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from conftest import REPO_ROOT

FABRIC_ROOT = REPO_ROOT / "fabric"
EVENTSTREAM_JSON = FABRIC_ROOT / "items" / "es-ns-telemetry-v1.Eventstream" / "eventstream.json"
KQL_SCHEMA = FABRIC_ROOT / "items" / "kql-ns-operations.KQLDatabase" / "DatabaseSchema.kql"
CATALOG = FABRIC_ROOT / "catalog" / "fabric-items.json"
PARAMETERS = FABRIC_ROOT / "deployment-parameters" / "novasteelv3.parameters.json"
ENVELOPE_PY = REPO_ROOT / "simulator" / "envelope.py"

# tableName -> (mapping rule, routed schema_name, derived stream feeding the table)
ROUTE_CONTRACT = {
    "telemetry_hot": ("telemetry_v1_json", "novasteel.telemetry.v1", "telemetry-stream"),
    "alarm_hot": ("alarm_v1_json", "novasteel.alarm.v1", "alarm-stream"),
    "gateway_health_hot": ("gateway_health_v1_json", "novasteel.gateway-health.v1", "gateway-health-stream"),
    "model_inference_hot": ("model_inference_v1_json", "novasteel.model-inference.v1", "model-inference-stream"),
    "ingest_quarantine_hot": ("quarantine_v1_json", "novasteel.quarantine.v1", "quarantine-stream"),
}

# Fields the model-inference simulator payload nests under ``payload`` (generator.py
# ``_generate_model_inference``). Their KQL mapping paths must be ``$.payload.*``.
MODEL_INFERENCE_PAYLOAD_COLUMNS = {
    "inference_id",
    "model_id",
    "model_version",
    "feature_snapshot_ts",
    "component_id",
    "prediction_type",
    "remaining_useful_life_days_p10",
    "remaining_useful_life_days_p50",
    "remaining_useful_life_days_p90",
    "estimated_minimum_lining_mm",
    "risk_score",
    "severity",
    "top_factors",
    "label",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def eventstream() -> dict:
    return _load_json(EVENTSTREAM_JSON)


@pytest.fixture(scope="module")
def kql_source() -> str:
    return KQL_SCHEMA.read_text(encoding="utf-8")


def _kql_destinations(eventstream: dict) -> list[dict]:
    return [d for d in eventstream["destinations"] if d.get("type") == "Eventhouse"]


def test_eventstream_has_single_custom_endpoint_source(eventstream: dict) -> None:
    sources = [s for s in eventstream["sources"] if s.get("type") == "CustomEndpoint"]
    assert len(sources) == 1, "Exactly one CustomEndpoint ingress source is expected."


def test_eventstream_has_bronze_and_five_hot_destinations(eventstream: dict) -> None:
    names = {d["name"] for d in eventstream["destinations"]}
    assert "landing-bronze-envelope" in names
    assert len(_kql_destinations(eventstream)) == 5


@pytest.mark.parametrize("table", sorted(ROUTE_CONTRACT))
def test_kql_destination_uses_direct_ingestion(eventstream: dict, table: str) -> None:
    dest = next(d for d in _kql_destinations(eventstream) if d["properties"]["tableName"] == table)
    props = dest["properties"]
    assert props["dataIngestionMode"] == "DirectIngestion", (
        f"{table} must use DirectIngestion; ProcessedIngestion silently drops hot-table rows."
    )
    expected_mapping = ROUTE_CONTRACT[table][0]
    assert props["mappingRuleName"] == expected_mapping
    conn = props.get("connectionName", "")
    assert conn and len(conn) <= 40, f"{table} needs a connectionName (<=40 chars); got {conn!r}."


def test_connection_names_are_unique(eventstream: dict) -> None:
    conns = [d["properties"]["connectionName"] for d in _kql_destinations(eventstream)]
    assert len(conns) == len(set(conns)), f"connectionNames must be unique: {conns}"


@pytest.mark.parametrize("table", sorted(ROUTE_CONTRACT))
def test_derived_stream_feeds_expected_table(eventstream: dict, table: str) -> None:
    dest = next(d for d in _kql_destinations(eventstream) if d["properties"]["tableName"] == table)
    stream = dest["inputNodes"][0]["name"]
    assert stream == ROUTE_CONTRACT[table][2]


def test_routing_operator_fans_every_schema_name(eventstream: dict) -> None:
    sql_ops = [o for o in eventstream["operators"] if o.get("type") == "SQL"]
    assert len(sql_ops) == 1, "Exactly one SQL routing operator is expected."
    query = sql_ops[0]["properties"]["query"]
    for _table, (_mapping, schema_name, stream) in ROUTE_CONTRACT.items():
        assert f"INTO [{stream}]" in query, f"Routing must fan into [{stream}]."
        assert f"schema_name = '{schema_name}'" in query, (
            f"Routing must filter schema_name '{schema_name}'."
        )


@pytest.mark.parametrize("table", sorted(ROUTE_CONTRACT))
def test_named_json_mapping_defined_in_kql_schema(kql_source: str, table: str) -> None:
    mapping = ROUTE_CONTRACT[table][0]
    pattern = (
        rf"\.create-or-alter\s+table\s+{re.escape(table)}\s+ingestion\s+json\s+mapping\s+'{re.escape(mapping)}'"
    )
    assert re.search(pattern, kql_source), (
        f"DatabaseSchema.kql must define json mapping '{mapping}' on {table}."
    )


def _model_inference_mapping(kql_source: str) -> list[dict]:
    marker = "'model_inference_v1_json'"
    idx = kql_source.index(marker)
    start = kql_source.index("[", idx)
    end = kql_source.index("]", start)
    return json.loads(kql_source[start : end + 1])


def test_model_inference_mapping_reads_payload_nested_fields(kql_source: str) -> None:
    """Regression guard: model-inference payload fields must map from ``$.payload.*``."""
    mapping = {m["column"]: m["path"] for m in _model_inference_mapping(kql_source)}
    for column in MODEL_INFERENCE_PAYLOAD_COLUMNS:
        assert column in mapping, f"model_inference mapping missing column {column}."
        assert mapping[column].startswith("$.payload"), (
            f"{column} must read from $.payload.* (was {mapping[column]}); the simulator nests it under payload."
        )


def _envelope_top_level_keys() -> set[str]:
    """Extract the canonical envelope top-level keys from simulator/envelope.py."""
    src = ENVELOPE_PY.read_text(encoding="utf-8")
    start = src.index("def build_envelope")
    body = src[start : src.index("\ndef ", start + 1)] if "\ndef " in src[start + 1 :] else src[start:]
    return set(re.findall(r'"(\w+)":', body))


def test_top_level_envelope_columns_do_not_read_from_payload(kql_source: str) -> None:
    """Envelope-level fields (schema_name, event_ts, plant_id, ...) must map from ``$.<field>``."""
    top_level = _envelope_top_level_keys()
    assert {"schema_name", "event_ts", "plant_id", "payload"} <= top_level
    mapping = {m["column"]: m["path"] for m in _model_inference_mapping(kql_source)}
    for column in ("schema_name", "event_ts", "ingest_ts", "plant_id", "asset_id", "correlation_id"):
        assert mapping[column] == f"$.{column}", (
            f"{column} is an envelope-level field and must map from $.{column}."
        )


def test_all_placeholder_tokens_resolve_from_parameters(eventstream: dict) -> None:
    """Every ``{{...}}`` token must resolve exactly as Deploy-FabricEventstream.ps1 resolves it."""
    catalog = _load_json(CATALOG)
    params = _load_json(PARAMETERS)
    resolvable = {"{{environment}}"}
    for ws in catalog["workspaces"]:
        resolvable.add(f"{{{{workspace.{ws['key']}.id}}}}")
        resolvable.add(f"{{{{workspace.{ws['key']}.displayName}}}}")
    for key in params["items"]:
        resolvable.add(f"{{{{item.{key}.id}}}}")
        resolvable.add(f"{{{{item.{key}.displayName}}}}")
    for key in params.get("retention", {}):
        resolvable.add(f"{{{{retention.{key}}}}}")

    raw = EVENTSTREAM_JSON.read_text(encoding="utf-8")
    tokens = set(re.findall(r"\{\{[^}]+\}\}", raw))
    unresolved = sorted(t for t in tokens if t not in resolvable)
    assert not unresolved, f"Unresolvable eventstream placeholders: {unresolved}"


def test_kql_item_tokens_target_deployed_items(eventstream: dict) -> None:
    """KQL destinations must point at the eventhouse/KQL item ids present in parameters."""
    params = _load_json(PARAMETERS)
    item_ids = {k: v.get("id") for k, v in params["items"].items()}
    raw = EVENTSTREAM_JSON.read_text(encoding="utf-8")
    # itemId must reference the KQL database item (holds the hot tables), not the empty default DB.
    assert "{{item.kqlOperations.id}}" in raw
    assert item_ids.get("kqlOperations"), "parameters.items.kqlOperations.id must be populated."


def test_eventstream_definition_contains_no_secret_material() -> None:
    raw = EVENTSTREAM_JSON.read_text(encoding="utf-8")
    assert not re.search(r"(?i)(sas|password|secret|connectionstring|accesskey)", raw), (
        "Eventstream definition must contain identifiers only, never credentials."
    )
