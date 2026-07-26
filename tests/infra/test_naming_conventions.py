"""Naming-convention and hard-requirement checks driven by static source inspection of the Bicep
templates (no Azure calls needed — these are pure text/regex assertions against the committed
source, so they run everywhere, unlike the `az bicep build` tests).
"""
from __future__ import annotations

import re

from conftest import BICEP_DIR, MODULES_DIR, read_text


def test_resource_group_naming_matches_deployment_topology() -> None:
    main_src = read_text(BICEP_DIR / "main.bicep")
    for suffix in ["hub", "integration", "apps", "ai", "fabric", "monitoring"]:
        pattern = rf"name:\s*'rg-ns-\$\{{environment\}}-{suffix}'"
        assert re.search(pattern, main_src), (
            f"expected a resource group named 'rg-ns-<env>-{suffix}' in main.bicep "
            "(deployment-topology.md §3.2 naming convention)"
        )


def test_location_parameter_defaults_to_sweden_central_with_west_europe_contingency() -> None:
    main_src = read_text(BICEP_DIR / "main.bicep")
    location_param_match = re.search(
        r"@allowed\(\[\s*'swedencentral'\s*'westeurope'\s*\]\)\s*param location string = 'swedencentral'",
        main_src,
    )
    assert location_param_match, (
        "expected `location` parameter in main.bicep to be @allowed(['swedencentral', "
        "'westeurope']) with a default of 'swedencentral' — deployment-topology.md §1/§2.2 "
        "requires Sweden Central as default with West Europe as the only explicit contingency"
    )


def test_fabric_capacity_naming_convention() -> None:
    main_src = read_text(BICEP_DIR / "main.bicep")
    assert "var fabricCapacityName = 'cap-novasteel-${environment}-${regionAbbrev}'" in main_src, (
        "Fabric capacity name should follow the 'cap-novasteel-<env>-<region-abbrev>' convention "
        "from deployment-topology.md §3.2 (example: cap-novasteel-demo-sc)"
    )


def test_event_hubs_namespace_naming_convention() -> None:
    main_src = read_text(BICEP_DIR / "main.bicep")
    assert "name: 'evh-novasteel-${environment}-${regionAbbrev}'" in main_src, (
        "Event Hubs namespace name should follow the 'evh-novasteel-<env>-<region-abbrev>' "
        "convention from deployment-topology.md §3.2 (example: evh-novasteel-prod-sc)"
    )


def test_only_fabric_capacities_resource_type_is_declared() -> None:
    """No infra/bicep template may declare a Microsoft.Fabric/<item> type other than capacities
    (implementation-guide.md §9.2)."""
    for f in BICEP_DIR.rglob("*.bicep"):
        src = read_text(f)
        for match in re.finditer(r"'Microsoft\.Fabric/([A-Za-z0-9]+)@", src):
            assert match.group(1) == "capacities", (
                f"{f} declares Microsoft.Fabric/{match.group(1)}, which is a Fabric SaaS-plane "
                "item type with no ARM support — only Microsoft.Fabric/capacities may be "
                "declared in this repository (implementation-guide.md §9.2)"
            )


def test_no_data_plane_access_keys_or_connection_strings_are_read() -> None:
    """The whole architecture relies on managed identity + RBAC; nothing should call
    listKeys()/listSecrets()/listConnectionStrings() to hand an app a shared key or SAS."""
    forbidden_calls = ["listKeys(", "listSecrets(", "listConnectionStrings(", "listSAS("]
    for f in BICEP_DIR.rglob("*.bicep"):
        src = read_text(f)
        for call in forbidden_calls:
            assert call not in src, (
                f"{f} calls {call} — this architecture uses managed identity/RBAC only, never "
                "shared keys/SAS/connection strings with embedded secrets "
                "(security-governance-and-threat-model.md §3.1)"
            )


def test_public_network_access_is_disabled_for_data_plane_resources() -> None:
    for name in ["keyvault.bicep", "storage.bicep", "eventhubs.bicep", "foundry-speech.bicep"]:
        src = read_text(MODULES_DIR / name)
        assert "publicNetworkAccess: 'Disabled'" in src, (
            f"{name} must set publicNetworkAccess to 'Disabled' by default "
            "(security-governance-and-threat-model.md §4.1)"
        )


def test_key_vaults_use_rbac_authorization_not_access_policies() -> None:
    src = read_text(MODULES_DIR / "keyvault.bicep")
    assert "enableRbacAuthorization: true" in src
    assert "enableSoftDelete: true" in src


def test_capacity_lifecycle_logic_app_is_never_deployed_for_prod() -> None:
    main_src = read_text(BICEP_DIR / "main.bicep")
    assert re.search(
        r"module logicAppCapacityLifecycle 'modules/logicapp-capacity-lifecycle\.bicep' = if \(!isProd\)",
        main_src,
    ), (
        "the 01:00 capacity lifecycle Logic App must only be conditionally deployed for "
        "non-production environments (deployment-topology.md §5.3: 'Production is hard-denied')"
    )


def test_logic_app_uses_w_europe_standard_time_for_luxembourg() -> None:
    src = read_text(MODULES_DIR / "logicapp-capacity-lifecycle.bicep")
    assert "'W. Europe Standard Time'" in src, (
        "the recurrence trigger must use the Windows time zone ID that maps to Europe/Luxembourg "
        "('W. Europe Standard Time') for the 01:00 local-time schedule "
        "(deployment-topology.md §5.3)"
    )
    assert "'1'" in src or '"1"' in src, "expected the recurrence schedule hour to be 1 (01:00)"
