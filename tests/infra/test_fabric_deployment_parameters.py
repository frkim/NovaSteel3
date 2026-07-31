"""Every Fabric deployment-parameter file must satisfy the schema it declares.

Each file under ``fabric/deployment-parameters`` names its own contract through
``$schema``, but nothing was checking that it actually honoured it. The drift
this guards against was real and silent: ``novasteelv3.parameters.json`` — the
single source of truth for the live ``NovaSteelV3-Demo`` workspace — carried
Kusto ``SoftDeletePeriod`` values in .NET timespan form (``90.00:00:00``), which
is what the KQL retention policy JSON expects, while the schema demanded the
``90d`` shorthand. All five retention fields failed, and the deployed estate was
correct while the schema was wrong.

A schema that its own canonical instance violates is worse than no schema: it
teaches the reader to distrust it. These tests make the two move together.

Template files are excluded by name because they carry deliberate placeholders
(``<dev|test|demo|prod>``) that are meant to be substituted, not validated.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from conftest import REPO_ROOT

PARAMETERS_ROOT = REPO_ROOT / "fabric" / "deployment-parameters"


def _instance_files() -> list[Path]:
    return sorted(
        path
        for path in PARAMETERS_ROOT.glob("*.json")
        if not path.name.endswith(".schema.json")
        and not path.name.endswith(".template.json")
    )


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("instance_path", _instance_files(), ids=lambda p: p.name)
def test_parameter_file_matches_its_declared_schema(instance_path: Path) -> None:
    instance = _load(instance_path)
    schema_ref = instance.get("$schema")

    assert isinstance(schema_ref, str) and schema_ref.startswith("./"), (
        f"{instance_path.name} must declare a sibling $schema so this check can "
        "resolve the contract it claims to satisfy."
    )

    schema_path = PARAMETERS_ROOT / schema_ref[2:]
    assert schema_path.is_file(), f"{instance_path.name} points at a missing schema: {schema_ref}"

    errors = sorted(
        Draft202012Validator(_load(schema_path)).iter_errors(instance),
        key=lambda error: list(error.path),
    )
    formatted = "\n".join(f"  {list(error.path)}: {error.message}" for error in errors)
    assert not errors, f"{instance_path.name} violates {schema_path.name}:\n{formatted}"


def test_live_workspace_parameters_record_every_deployed_item_id() -> None:
    """The live parameter file is the map back to the real estate.

    An item with a blank id cannot be re-targeted by a redeployment or torn down
    by a cleanup script, so a blank here is a loose end rather than a detail.
    Every item in the novasteelv3 workspace, semantic model included, is now
    deployed, so there is no legitimate blank left.
    """
    parameters = _load(PARAMETERS_ROOT / "novasteelv3.parameters.json")
    items = parameters["items"]

    unresolved = {key for key, value in items.items() if not value["id"].strip()}

    assert not unresolved, f"Items without a deployed id: {sorted(unresolved)}"
    assert parameters["deploymentOptions"]["deploySemanticModel"] is True


def test_eventstream_parameters_match_the_authored_item() -> None:
    """The Eventstream is deployed, so its identity must be pinned here.

    Its Eventhouse destinations resolve ``{{item.kqlOperations.displayName}}``
    from this file rather than from the catalogue, so the two must name the same
    database. If they ever drift apart the stream routes into a database that
    does not exist and the hot tables stay empty without erroring.
    """
    parameters = _load(PARAMETERS_ROOT / "novasteelv3.parameters.json")
    eventstream = parameters["items"]["eventstreamTelemetry"]

    authored_dir = REPO_ROOT / "fabric" / "items" / "es-ns-telemetry-v1.Eventstream"
    assert authored_dir.is_dir()
    assert eventstream["displayName"] == "es-ns-telemetry-v1"

    definition = json.dumps(_load(authored_dir / "eventstream.json"))
    if "{{item.kqlOperations.displayName}}" in definition:
        catalogue = _load(PARAMETERS_ROOT / "novasteelv3.items-manifest.json")
        catalogued = next(
            item["displayName"]
            for item in catalogue["supportedItems"]
            if item["key"] == "kqlOperations"
        )
        assert parameters["items"]["kqlOperations"]["displayName"] == catalogued
