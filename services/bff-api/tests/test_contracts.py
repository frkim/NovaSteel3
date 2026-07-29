import json
from pathlib import Path

import yaml
from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from openapi_spec_validator import validate
from referencing import Registry, Resource


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_openapi_contract_is_valid() -> None:
    contract = yaml.safe_load(
        (REPOSITORY_ROOT / "contracts" / "openapi" / "bff-api-v1.yaml").read_text(
            encoding="utf-8"
        )
    )

    validate(contract)


def test_event_schemas_are_valid_json_schema() -> None:
    schema_directory = REPOSITORY_ROOT / "contracts" / "events"

    for schema_path in schema_directory.glob("*.schema.json"):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator_for(schema).check_schema(schema)


def test_event_fixtures_have_a_valid_and_invalid_case_per_schema() -> None:
    schema_directory = REPOSITORY_ROOT / "contracts" / "events"
    schemas = {
        schema_path.name: json.loads(schema_path.read_text(encoding="utf-8"))
        for schema_path in schema_directory.glob("*.schema.json")
    }
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
    )
    fixture_schema_pairs = [
        ("telemetry.valid.v1.json", "event-envelope.v1.schema.json"),
        ("telemetry.valid.v1.json", "telemetry.v1.schema.json"),
        ("energy-interval.valid.v1.json", "energy-interval.v1.schema.json"),
        ("quality-measurement.valid.v1.json", "quality-measurement.v1.schema.json"),
        ("alarm.valid.v1.json", "alarm.v1.schema.json"),
        ("model-inference.valid.v1.json", "model-inference.v1.schema.json"),
        ("quarantine.valid.v1.json", "quarantine.v1.schema.json"),
    ]

    for fixture_name, schema_name in fixture_schema_pairs:
        instance = json.loads(
            (schema_directory / "fixtures" / fixture_name).read_text(encoding="utf-8")
        )
        validator_class = validator_for(schemas[schema_name])
        validator = validator_class(
            schemas[schema_name],
            registry=registry,
            format_checker=FormatChecker(),
        )

        assert list(validator.iter_errors(instance)) == []
        invalid_instance = dict(instance)
        invalid_instance.pop(next(iter(instance)))
        assert list(validator.iter_errors(invalid_instance))


def test_data_contract_manifests_are_versioned_and_parseable() -> None:
    """The major version in the filename must match ``contractVersion``.

    Globbing only ``*.v1.json`` would silently stop covering a contract the day
    it is bumped, which is exactly when the check matters most: ``gold`` moved to
    v2 when its keys changed from surrogate to natural, and the rename to
    ``gold.v2.json`` is what keeps the declared version and the filename honest.
    """
    contract_paths = sorted((REPOSITORY_ROOT / "contracts" / "data").glob("*.v*.json"))
    assert contract_paths

    for contract_path in contract_paths:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        declared_major = int(contract_path.name.rsplit(".v", 1)[1].split(".", 1)[0])

        assert contract["contractVersion"] == declared_major
        assert contract["tables"]


def test_ui_contract_schemas_are_valid_json_schema() -> None:
    for schema_path in (REPOSITORY_ROOT / "contracts" / "ui").glob("*.schema.json"):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator_for(schema).check_schema(schema)


def test_blazor_token_projection_matches_shared_contract() -> None:
    shared_tokens = (
        REPOSITORY_ROOT / "contracts" / "ui" / "design-tokens.v1.css"
    ).read_text(encoding="utf-8")
    shell_tokens = (
        REPOSITORY_ROOT
        / "apps"
        / "portal-shell"
        / "wwwroot"
        / "css"
        / "tokens.css"
    ).read_text(encoding="utf-8")

    assert shell_tokens == shared_tokens
