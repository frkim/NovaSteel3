"""Every infra/policy/definitions/*.json file must be well-formed Azure Policy definition JSON
and must actually be wired into infra/bicep/modules/policy-assignments.bicep via loadJsonContent.
"""
from __future__ import annotations

from pathlib import Path

from conftest import BICEP_DIR, load_json, read_text

REQUIRED_TOP_LEVEL_KEYS = {"properties"}
REQUIRED_PROPERTY_KEYS = {"displayName", "description", "policyType", "mode", "policyRule"}


def test_policy_definition_files_exist(policy_definition_files: list[Path]) -> None:
    assert len(policy_definition_files) >= 3, (
        "expected at least the 3 documented custom policy definitions under "
        "infra/policy/definitions (see infra/policy/README.md)"
    )


def test_policy_definitions_are_well_formed(policy_definition_files: list[Path]) -> None:
    for f in policy_definition_files:
        data = load_json(f)
        missing_top = REQUIRED_TOP_LEVEL_KEYS - data.keys()
        assert not missing_top, f"{f.name} is missing top-level key(s): {missing_top}"
        props = data["properties"]
        missing_props = REQUIRED_PROPERTY_KEYS - props.keys()
        assert not missing_props, f"{f.name} properties missing key(s): {missing_props}"
        assert props["policyType"] == "Custom", f"{f.name} should be a Custom policy type"
        assert "if" in props["policyRule"], f"{f.name} policyRule must have an 'if' condition"
        assert "then" in props["policyRule"], f"{f.name} policyRule must have a 'then' effect"


def test_policy_definitions_document_their_source_requirement(
    policy_definition_files: list[Path],
) -> None:
    for f in policy_definition_files:
        data = load_json(f)
        metadata = data["properties"].get("metadata", {})
        assert metadata.get("source"), (
            f"{f.name} should cite the requirement doc/section it operationalizes in "
            "properties.metadata.source (see infra/policy/README.md convention)"
        )


def test_every_policy_definition_file_is_loaded_by_bicep(
    policy_definition_files: list[Path],
) -> None:
    assignments_src = read_text(BICEP_DIR / "modules" / "policy-assignments.bicep")
    for f in policy_definition_files:
        expected_reference = f"policy/definitions/{f.name}"
        assert expected_reference in assignments_src, (
            f"{f.name} exists under infra/policy/definitions but is not referenced via "
            f"loadJsonContent(...) in infra/bicep/modules/policy-assignments.bicep — "
            "every definition file must be wired in, or removed if unused"
        )


def test_fabric_sku_guardrail_matches_deployment_topology_default_allow_list() -> None:
    definitions_dir = BICEP_DIR.parent / "policy" / "definitions"
    data = load_json(definitions_dir / "restrict-fabric-capacity-sku.json")
    allowed = data["properties"]["parameters"]["allowedSkus"]["defaultValue"]
    assert set(allowed) == {"F2", "F4", "F8"}, (
        "the Fabric capacity SKU guardrail's default allow-list should match "
        "deployment-topology.md §6 (F2 initial, F4 measured fallback, F8 demo-day burst) "
        "and must stay in step with the SKUs the portal capacity dialog offers"
    )
