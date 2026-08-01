"""Tests for M4/M5/M12 implementation:
- Alerts module exists with action group and 10 rules
- Container Apps set the Application Insights connection string
- Zone redundancy is tied to production
- secondaryLocation parameter exists and is EU-only
- Security invariants remain intact
"""
from __future__ import annotations

import re

from conftest import BICEP_DIR, MODULES_DIR, read_text


class TestAlertsModule:
    """M5: alerts.bicep exists and declares the expected resources."""

    def test_alerts_module_exists(self) -> None:
        assert (MODULES_DIR / "alerts.bicep").is_file(), (
            "infra/bicep/modules/alerts.bicep must exist per M5 (operations-and-cost.md §4)"
        )

    def test_alerts_module_declares_action_group(self) -> None:
        src = read_text(MODULES_DIR / "alerts.bicep")
        assert "Microsoft.Insights/actionGroups" in src, (
            "alerts.bicep must declare a Microsoft.Insights/actionGroups resource"
        )

    def test_alerts_module_has_ten_alert_rules(self) -> None:
        src = read_text(MODULES_DIR / "alerts.bicep")
        rule_count = src.count("Microsoft.Insights/scheduledQueryRules")
        assert rule_count >= 10, (
            f"alerts.bicep must declare at least 10 scheduledQueryRules (found {rule_count}); "
            "operations-and-cost.md §4 specifies 10 alert conditions"
        )

    def test_alerts_module_wired_into_main(self) -> None:
        main_src = read_text(BICEP_DIR / "main.bicep")
        assert "modules/alerts.bicep" in main_src, (
            "main.bicep must reference modules/alerts.bicep"
        )

    def test_alert_for_bff_error_rate(self) -> None:
        src = read_text(MODULES_DIR / "alerts.bicep")
        assert "bff-error-rate" in src, "alerts.bicep must include a BFF error rate alert"

    def test_alert_for_data_freshness(self) -> None:
        src = read_text(MODULES_DIR / "alerts.bicep")
        assert "data-freshness" in src, "alerts.bicep must include a data freshness alert"

    def test_alert_for_model_drift(self) -> None:
        src = read_text(MODULES_DIR / "alerts.bicep")
        assert "model-drift" in src, "alerts.bicep must include a model drift alert"
        assert "novasteel.rul.confidence" in src, (
            "model drift alert must reference the novasteel.rul.confidence custom metric"
        )

    def test_alert_for_unauthorized_dispatch(self) -> None:
        src = read_text(MODULES_DIR / "alerts.bicep")
        assert "unauthorized-dispatch" in src, (
            "alerts.bicep must include an unauthorized energy-dispatch alert (Sev-1)"
        )

    def test_alert_severity_1_exists(self) -> None:
        src = read_text(MODULES_DIR / "alerts.bicep")
        assert "severity: 1" in src, (
            "alerts.bicep must have at least one Sev-1 alert (unauthorized dispatch)"
        )


class TestAppInsightsConnectionString:
    """M4: Container Apps receive the Application Insights connection string."""

    def test_containerapps_has_appinsights_connection_string_param(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "param appInsightsConnectionString string" in src, (
            "containerapps.bicep must accept appInsightsConnectionString as a parameter"
        )

    def test_containerapps_sets_appinsights_env_var(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "APPLICATIONINSIGHTS_CONNECTION_STRING" in src, (
            "containerapps.bicep must set APPLICATIONINSIGHTS_CONNECTION_STRING in container env"
        )

    def test_containerapps_sets_otel_service_name(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "OTEL_SERVICE_NAME" in src, (
            "containerapps.bicep must set OTEL_SERVICE_NAME per container app for telemetry correlation"
        )

    def test_main_passes_appinsights_connection_string_to_containerapps(self) -> None:
        main_src = read_text(BICEP_DIR / "main.bicep")
        assert "appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString" in main_src, (
            "main.bicep must pass the App Insights connection string from monitoring module to containerApps module"
        )


class TestZoneRedundancy:
    """M12: zoneRedundant is tied to production environment."""

    def test_containerapps_zone_redundant_tied_to_prod(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "zoneRedundant: isProduction" in src, (
            "containerapps.bicep must set zoneRedundant based on the isProduction parameter"
        )

    def test_eventhubs_zone_redundant_tied_to_prod(self) -> None:
        src = read_text(MODULES_DIR / "eventhubs.bicep")
        assert "zoneRedundant: isProduction" in src, (
            "eventhubs.bicep must set zoneRedundant based on the isProduction parameter"
        )

    def test_containerapps_has_isproduction_param(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "param isProduction bool" in src, (
            "containerapps.bicep must accept an isProduction parameter"
        )

    def test_eventhubs_has_isproduction_param(self) -> None:
        src = read_text(MODULES_DIR / "eventhubs.bicep")
        assert "param isProduction bool" in src, (
            "eventhubs.bicep must accept an isProduction parameter"
        )

    def test_secondary_location_parameter_exists_in_main(self) -> None:
        main_src = read_text(BICEP_DIR / "main.bicep")
        assert "param secondaryLocation string" in main_src, (
            "main.bicep must declare a secondaryLocation parameter for ADR-003 contingency"
        )

    def test_secondary_location_is_eu_only(self) -> None:
        main_src = read_text(BICEP_DIR / "main.bicep")
        match = re.search(
            r"@allowed\(\[\s*'westeurope'\s*'northeurope'\s*'francecentral'\s*\]\)\s*param secondaryLocation",
            main_src,
        )
        assert match, (
            "secondaryLocation must be @allowed with EU-only regions "
            "(westeurope, northeurope, francecentral) per ADR-003"
        )


class TestSecurityInvariantsPreserved:
    """Regression: security hardening must not be weakened by M4/M5/M12 changes."""

    def test_containerapps_still_uses_user_assigned_identity(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "type: 'UserAssigned'" in src, (
            "containerapps.bicep must still use UserAssigned managed identity (per-service MI)"
        )

    def test_eventhubs_still_disables_local_auth(self) -> None:
        src = read_text(MODULES_DIR / "eventhubs.bicep")
        assert "disableLocalAuth: true" in src, (
            "eventhubs.bicep must retain disableLocalAuth: true"
        )

    def test_eventhubs_still_disables_public_network(self) -> None:
        src = read_text(MODULES_DIR / "eventhubs.bicep")
        assert "publicNetworkAccess: 'Disabled'" in src, (
            "eventhubs.bicep must retain publicNetworkAccess: 'Disabled'"
        )

    def test_containerapps_still_internal_only(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "internal: internalOnly" in src or "param internalOnly bool = true" in src, (
            "containerapps.bicep must retain internal-only VNet configuration"
        )

    def test_no_data_plane_keys_in_alerts(self) -> None:
        src = read_text(MODULES_DIR / "alerts.bicep")
        forbidden = ["listKeys(", "listSecrets(", "listConnectionStrings("]
        for call in forbidden:
            assert call not in src, (
                f"alerts.bicep must not call {call} — managed identity/RBAC only"
            )

    def test_storage_still_disables_public_network(self) -> None:
        src = read_text(MODULES_DIR / "storage.bicep")
        assert "publicNetworkAccess: 'Disabled'" in src, (
            "storage.bicep must retain publicNetworkAccess: 'Disabled'"
        )

    def test_storage_still_disables_shared_key(self) -> None:
        src = read_text(MODULES_DIR / "storage.bicep")
        assert "param disableSharedKeyAccess bool = true" in src, (
            "storage.bicep must default to disableSharedKeyAccess=true"
        )


class TestBffTableStorage:
    """M10 infra: BFF audit log + idempotency store uses Azure Table Storage."""

    def test_storage_module_supports_tables_param(self) -> None:
        src = read_text(MODULES_DIR / "storage.bicep")
        assert "param tables array" in src, (
            "storage.bicep must accept a tables parameter for Table Storage provisioning"
        )

    def test_main_provisions_bffauditlog_table(self) -> None:
        main_src = read_text(BICEP_DIR / "main.bicep")
        assert "'bffauditlog'" in main_src, (
            "main.bicep must provision the bffauditlog table"
        )

    def test_main_provisions_bffidempotency_table(self) -> None:
        main_src = read_text(BICEP_DIR / "main.bicep")
        assert "'bffidempotency'" in main_src, (
            "main.bicep must provision the bffidempotency table"
        )

    def test_bff_has_storage_table_data_contributor_role(self) -> None:
        main_src = read_text(BICEP_DIR / "main.bicep")
        # Storage Table Data Contributor role ID
        assert "0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3" in main_src, (
            "main.bicep must assign Storage Table Data Contributor "
            "(0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3) to the BFF identity"
        )

    def test_table_private_endpoint_in_storage_module(self) -> None:
        src = read_text(MODULES_DIR / "storage.bicep")
        assert "pe-${name}-table" in src, (
            "storage.bicep must declare a table private endpoint"
        )

    def test_table_private_dns_zone_in_network_module(self) -> None:
        src = read_text(MODULES_DIR / "network.bicep")
        assert re.search(r"privatelink\.table\.core\.windows\.net", src), (
            "network.bicep must declare the privatelink.table.core.windows.net DNS zone"
        )

    def test_network_outputs_table_dns_zone_id(self) -> None:
        src = read_text(MODULES_DIR / "network.bicep")
        # Index-agnostic on purpose: the zone list grows (e.g. when
        # privatelink.services.ai.azure.com was added for the Foundry project
        # endpoint), and pinning an ordinal here turns an unrelated addition into a
        # false failure. What matters is that the table zone is exported at all.
        assert re.search(r"table: privateDnsZones\[\d+\]\.id", src), (
            "network.bicep must output the table private DNS zone ID"
        )

    def test_containerapps_sets_table_endpoint_for_bff(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "NOVASTEEL_TABLE_ENDPOINT" in src, (
            "containerapps.bicep must set NOVASTEEL_TABLE_ENDPOINT env var for the BFF"
        )

    def test_containerapps_sets_storage_account_name_for_bff(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "NOVASTEEL_STORAGE_ACCOUNT_NAME" in src, (
            "containerapps.bicep must set NOVASTEEL_STORAGE_ACCOUNT_NAME env var for the BFF"
        )

    def test_table_endpoint_only_set_for_bff(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "svc == 'bff-api'" in src and "bffTableEndpoint" in src, (
            "Table endpoint env vars should only be set for bff-api, not all services"
        )


class TestFoundryIntegration:
    """Foundry / knowledge-orchestrator: correct role, env vars, and deployment name wiring."""

    def test_foundry_endpoint_env_var_exists(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "FOUNDRY_ENDPOINT" in src, (
            "containerapps.bicep must set FOUNDRY_ENDPOINT env var for BFF and knowledge-orchestrator"
        )

    def test_foundry_endpoint_set_for_bff_and_knowledge_orchestrator(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "svc == 'bff-api' || svc == 'knowledge-orchestrator'" in src, (
            "FOUNDRY_ENDPOINT should be set for bff-api and knowledge-orchestrator only"
        )

    def test_foundry_endpoint_param_exists(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "param foundryEndpoint string" in src, (
            "containerapps.bicep must accept a foundryEndpoint parameter"
        )

    def test_main_passes_foundry_endpoint(self) -> None:
        main_src = read_text(BICEP_DIR / "main.bicep")
        assert "foundryEndpoint: foundrySpeech.outputs.foundryEndpoint" in main_src, (
            "main.bicep must pass the Foundry endpoint to the containerApps module"
        )

    def test_cognitive_services_openai_user_role_assigned(self) -> None:
        main_src = read_text(BICEP_DIR / "main.bicep")
        # Cognitive Services OpenAI User role ID: 5e0bd9bd-7b93-4f28-af87-19fc36ad61bd
        assert "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" in main_src, (
            "main.bicep must assign Cognitive Services OpenAI User "
            "(5e0bd9bd-7b93-4f28-af87-19fc36ad61bd) — required for data-plane inference"
        )

    def test_old_cognitive_services_user_role_not_on_foundry(self) -> None:
        main_src = read_text(BICEP_DIR / "main.bicep")
        # The general Cognitive Services User role (a97b65f3-...) should NOT appear in
        # foundryRoleAssignments — it is insufficient for OpenAI inference
        assert "a97b65f3-24c7-4388-baec-2e87135dc908" not in main_src, (
            "main.bicep must NOT use Cognitive Services User (a97b65f3-...) on the Foundry "
            "account — that role cannot perform OpenAI inference; use Cognitive Services "
            "OpenAI User (5e0bd9bd-...) instead"
        )

    def test_knowledge_orchestrator_gets_openai_user_role(self) -> None:
        main_src = read_text(BICEP_DIR / "main.bicep")
        # Verify knowledge-orchestrator principal is in the role assignments block
        assert "identity.outputs.knowledgeOrchestratorPrincipalId" in main_src and \
               "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" in main_src, (
            "main.bicep must assign Cognitive Services OpenAI User to knowledge-orchestrator MI"
        )

    def test_knowledge_agent_mode_set_to_azure(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "'KNOWLEDGE_AGENT_MODE'" in src and "'azure'" in src, (
            "containerapps.bicep must set KNOWLEDGE_AGENT_MODE=azure so the deployed "
            "knowledge-orchestrator uses the live Foundry adapter, not the local fixture"
        )

    def test_foundry_chat_deployment_wired_from_output(self) -> None:
        main_src = read_text(BICEP_DIR / "main.bicep")
        assert "foundryChatDeployment: foundrySpeech.outputs.gptDeploymentModelName" in main_src, (
            "main.bicep must wire foundryChatDeployment from the module output, not a literal"
        )

    def test_foundry_embed_deployment_wired_from_output(self) -> None:
        main_src = read_text(BICEP_DIR / "main.bicep")
        assert "foundryEmbedDeployment: foundrySpeech.outputs.embeddingDeploymentModelName" in main_src, (
            "main.bicep must wire foundryEmbedDeployment from the module output, not a literal"
        )

    def test_foundry_chat_deployment_env_var_exists(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "FOUNDRY_CHAT_DEPLOYMENT" in src, (
            "containerapps.bicep must set FOUNDRY_CHAT_DEPLOYMENT for knowledge-orchestrator"
        )

    def test_foundry_embed_deployment_env_var_exists(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "FOUNDRY_EMBED_DEPLOYMENT" in src, (
            "containerapps.bicep must set FOUNDRY_EMBED_DEPLOYMENT for knowledge-orchestrator"
        )

    def test_foundry_account_disables_local_auth(self) -> None:
        src = read_text(MODULES_DIR / "foundry-speech.bicep")
        assert "disableLocalAuth: true" in src, (
            "foundry-speech.bicep must disable local auth (managed identity only)"
        )

    def test_foundry_account_disables_public_network(self) -> None:
        src = read_text(MODULES_DIR / "foundry-speech.bicep")
        assert "publicNetworkAccess: 'Disabled'" in src, (
            "foundry-speech.bicep must disable public network access"
        )


class TestLogFormatAndPlaceholder:
    """NOVASTEEL_LOG_FORMAT=json on all services; NOVASTEEL_PLACEHOLDER removed."""

    def test_log_format_json_set(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "'NOVASTEEL_LOG_FORMAT'" in src and "'json'" in src, (
            "containerapps.bicep must set NOVASTEEL_LOG_FORMAT=json on all services "
            "so structured JSON logs are queryable in Log Analytics"
        )

    def test_novasteel_placeholder_removed(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "NOVASTEEL_PLACEHOLDER" not in src, (
            "NOVASTEEL_PLACEHOLDER env var should be removed — it served no runtime purpose "
            "and is a leftover from the initial scaffold"
        )


class TestContainerImageParameterization:
    """Container images should be parameterized for CI/CD to pass real image tags."""

    def test_service_images_param_exists(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "param serviceImages object" in src, (
            "containerapps.bicep must accept a serviceImages parameter for per-service image overrides"
        )

    def test_image_uses_service_images_lookup(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "serviceImages[?svc] ?? placeholderImage" in src, (
            "Container image selection should look up serviceImages via safe access "
            "before falling back to placeholderImage"
        )

    def test_placeholder_image_is_still_default(self) -> None:
        src = read_text(MODULES_DIR / "containerapps.bicep")
        assert "mcr.microsoft.com/k8se/quickstart:latest" in src, (
            "placeholderImage default should remain for environments without real images"
        )
