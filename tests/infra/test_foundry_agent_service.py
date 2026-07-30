"""Infra assertions for Foundry Agent Service, AI Search and the observability link.

These are source-text assertions rather than deployments: the point is to catch the
handful of things that would compile perfectly and then fail at deploy time or, worse,
succeed while quietly breaking an invariant — a public search endpoint, a key-based
connection, a capability host deployed before its RBAC, or a model deployment that
silently drifts back off the 5-series.
"""

from __future__ import annotations

import re

import pytest

from conftest import BICEP_DIR, MODULES_DIR, read_text


def code_of(path) -> str:
    """Return a module's source with whole-line `//` comments removed.

    These modules carry long explanatory headers that name the very things the
    assertions below look for (`enterprise_memory`, `authOptions`, `authType: 'AAD'`),
    so matching against raw text would pass or fail on prose rather than on Bicep.
    """
    lines = read_text(path).splitlines()
    return "\n".join(line for line in lines if not line.lstrip().startswith("//"))


@pytest.fixture(scope="module")
def ai_search() -> str:
    return code_of(MODULES_DIR / "ai-search.bicep")


@pytest.fixture(scope="module")
def cosmos() -> str:
    return code_of(MODULES_DIR / "cosmos.bicep")


@pytest.fixture(scope="module")
def foundry_speech() -> str:
    return code_of(MODULES_DIR / "foundry-speech.bicep")


@pytest.fixture(scope="module")
def foundry_agents() -> str:
    return code_of(MODULES_DIR / "foundry-agents.bicep")


@pytest.fixture(scope="module")
def capability_host() -> str:
    return code_of(MODULES_DIR / "foundry-agent-capability-host.bicep")


@pytest.fixture(scope="module")
def agent_rbac() -> str:
    return code_of(MODULES_DIR / "foundry-agent-rbac.bicep")


@pytest.fixture(scope="module")
def appinsights_access() -> str:
    return code_of(MODULES_DIR / "appinsights-agent-access.bicep")


@pytest.fixture(scope="module")
def main() -> str:
    return code_of(BICEP_DIR / "main.bicep")


# ---------------------------------------------------------------------------
# AI Search — the procedure store
# ---------------------------------------------------------------------------


def test_search_service_is_private_and_keyless(ai_search: str) -> None:
    assert "publicNetworkAccess: 'Disabled'" in ai_search
    assert "disableLocalAuth: true" in ai_search
    # authOptions is mutually exclusive with disableLocalAuth; setting both fails deploy.
    assert "authOptions" not in ai_search


def test_search_service_has_a_private_endpoint(ai_search: str) -> None:
    assert "'searchService'" in ai_search
    assert "searchPrivateDnsZoneId" in ai_search


def test_search_service_has_managed_identity_for_vectorization(ai_search: str) -> None:
    assert "SystemAssigned" in ai_search
    assert "output searchPrincipalId" in ai_search


def test_search_exposes_the_index_and_knowledge_base_name_contract(ai_search: str) -> None:
    """Indexes and knowledge bases are data-plane objects; the names are the contract."""
    assert "output procedureIndexName string = 'novasteel-procedures'" in ai_search
    assert "output knowledgeBaseName" in ai_search


def test_search_private_dns_zone_is_registered(main: str) -> None:
    network = code_of(MODULES_DIR / "network.bicep")
    assert "privatelink.search.windows.net" in network
    assert "privatelink.documents.azure.com" in network
    assert "search: privateDnsZones" in network
    assert "cosmosDb: privateDnsZones" in network


# ---------------------------------------------------------------------------
# Cosmos — agent thread storage
# ---------------------------------------------------------------------------


def test_cosmos_is_private_and_keyless(cosmos: str) -> None:
    assert "publicNetworkAccess: 'Disabled'" in cosmos
    assert "disableLocalAuth: true" in cosmos
    assert "disableKeyBasedMetadataWriteAccess: true" in cosmos


def test_cosmos_does_not_precreate_agent_databases(cosmos: str) -> None:
    """Agent Service creates `enterprise_memory` itself at capability-host creation."""
    assert "enterprise_memory" not in cosmos
    assert "sqlDatabases" not in cosmos


# ---------------------------------------------------------------------------
# Model deployments — GPT-5 series
# ---------------------------------------------------------------------------


def test_chat_deployment_is_a_five_series_mini_model(foundry_speech: str) -> None:
    match = re.search(r"param gptModelName string = '([^']+)'", foundry_speech)
    assert match, "gptModelName parameter not found"
    model = match.group(1)
    assert model.startswith("gpt-5"), f"expected a 5-series model, got {model}"
    assert "mini" in model


def test_high_reasoning_deployment_is_an_advanced_five_series_model(
    foundry_speech: str,
) -> None:
    match = re.search(r"param reasoningModelName string = '([^']+)'", foundry_speech)
    assert match, "reasoningModelName parameter not found"
    model = match.group(1)
    assert model.startswith("gpt-5")
    assert "mini" not in model, "the high-reasoning tier must not be a mini model"


def test_reasoning_deployment_is_exposed_to_the_apps(
    foundry_speech: str, main: str
) -> None:
    assert "output reasoningDeploymentModelName" in foundry_speech
    assert "foundryReasoningDeployment: foundrySpeech.outputs.reasoningDeploymentModelName" in main


def test_foundry_account_allows_project_management(foundry_speech: str) -> None:
    """Without this the account cannot host a project, so Agent Service is impossible."""
    assert "allowProjectManagement: true" in foundry_speech


# ---------------------------------------------------------------------------
# Foundry project, connections and observability
# ---------------------------------------------------------------------------


def test_project_has_a_system_assigned_identity(foundry_agents: str) -> None:
    assert "Microsoft.CognitiveServices/accounts/projects@" in foundry_agents
    assert "SystemAssigned" in foundry_agents


@pytest.mark.parametrize(
    "category", ["CognitiveSearch", "CosmosDB", "AzureStorageAccount"]
)
def test_byo_connections_exist_for_standard_agent_setup(
    foundry_agents: str, category: str
) -> None:
    assert f"category: '{category}'" in foundry_agents


def test_byo_connections_use_entra_not_keys(foundry_agents: str) -> None:
    assert "authType: 'AAD'" in foundry_agents
    assert foundry_agents.count("authType: 'AAD'") == 3


def test_application_insights_connection_links_agent_telemetry(
    foundry_agents: str,
) -> None:
    """This connection is what makes agent runs show up in the Foundry Tracing blade."""
    assert "category: 'AppInsights'" in foundry_agents
    assert "isSharedToAll: true" in foundry_agents
    assert "authType: 'ProjectManagedIdentity'" in foundry_agents


def test_app_insights_connection_stores_no_secret(foundry_agents: str) -> None:
    """The service accepts only ProjectManagedIdentity or ApiKey for this category.

    ApiKey makes the platform persist the connection string via its credential
    service, which needs an associated Key Vault; on a keyless account the request
    fails with an opaque HTTP 500. Managed identity keeps the connection secretless.
    """
    connection = foundry_agents.split("category: 'AppInsights'", 1)[1]
    assert "credentials:" not in connection
    assert "authType: 'ApiKey'" not in foundry_agents


def test_project_can_read_back_its_own_traces(appinsights_access: str) -> None:
    # Log Analytics Reader + Privileged Monitoring Data Reader.
    assert "73c42c96-874c-492b-b04d-ab87d138a893" in appinsights_access
    assert "dbc9c667-e97f-4491-aee6-90b9cf960190" in appinsights_access


def test_project_can_publish_its_own_traces(appinsights_access: str) -> None:
    """ProjectManagedIdentity auth means the project identity does the writing."""
    # Monitoring Metrics Publisher.
    assert "3913510d-42f4-4e42-8a64-420c390055eb" in appinsights_access


def test_project_holds_search_data_and_service_roles(foundry_agents: str) -> None:
    assert "8ebe5a00-799e-43f5-93ac-243d3dce84a7" in foundry_agents  # Index Data Contributor
    assert "7ca78c08-252a-4471-8644-bb5ff32d4ba0" in foundry_agents  # Service Contributor


def test_project_holds_cosmos_and_storage_roles(agent_rbac: str) -> None:
    assert "230815da-be43-4aae-9cb4-875f7bd000aa" in agent_rbac  # Cosmos DB Operator
    assert "17d1049b-9a84-46fb-8f53-869881c3d3ab" in agent_rbac  # Storage Acct Contributor
    assert "b7e6dc6d-f1e8-4753-8033-0f276bb0955b" in agent_rbac  # Blob Data Owner
    assert "00000000-0000-0000-0000-000000000002" in agent_rbac  # Cosmos data contributor


# ---------------------------------------------------------------------------
# Capability hosts — ordering and the quota gate
# ---------------------------------------------------------------------------


def test_capability_hosts_are_declared_for_agents(capability_host: str) -> None:
    assert "capabilityHostKind: 'Agents'" in capability_host
    assert capability_host.count("capabilityHostKind: 'Agents'") == 2


def test_project_capability_host_binds_all_three_byo_stores(
    capability_host: str,
) -> None:
    assert "vectorStoreConnections" in capability_host
    assert "threadStorageConnections" in capability_host
    assert "storageConnections" in capability_host


def test_project_capability_host_follows_the_account_one(capability_host: str) -> None:
    assert "dependsOn" in capability_host
    assert "accountCapabilityHost" in capability_host


def test_capability_host_is_behind_the_manual_quota_gate(main: str) -> None:
    """A capability host is immutable, so it must not deploy unreviewed."""
    assert (
        "module foundryAgentCapabilityHost 'modules/foundry-agent-capability-host.bicep' "
        "= if (foundryAgentServiceManuallyValidated)" in main
    )


def test_capability_host_deploys_after_the_byo_rbac(main: str) -> None:
    """The platform provisions Cosmos/blob containers as the project identity."""
    block_start = main.index("module foundryAgentCapabilityHost")
    block = main[block_start : block_start + 1200]
    assert "dependsOn" in block
    assert "foundryAgentRbac" in block


# ---------------------------------------------------------------------------
# Project model — Foundry resource + project, never a classic hub
# ---------------------------------------------------------------------------


def test_no_classic_hub_workspaces_anywhere() -> None:
    """A hub-based ("classic") project is `MachineLearningServices/workspaces`.

    The whole estate is on the Foundry project model
    (`CognitiveServices/accounts` + `accounts/projects`), so a hub appearing
    anywhere means something was authored against the old shape.
    """
    for path in sorted(BICEP_DIR.rglob("*.bicep")):
        assert "Microsoft.MachineLearningServices" not in read_text(path), (
            f"{path.name} declares a classic AI hub workspace; the Foundry project "
            "model uses Microsoft.CognitiveServices/accounts/projects"
        )


def test_project_resources_use_a_project_capable_api_version(
    foundry_agents: str, capability_host: str
) -> None:
    """`accounts/projects` does not exist before 2025-04-01-preview."""
    for source in (foundry_agents, capability_host):
        for match in re.finditer(r"'Microsoft\.CognitiveServices/[^@]+@([^']+)'", source):
            assert match.group(1) >= "2025-04-01-preview", (
                f"{match.group(0)} predates the Foundry project model"
            )


def test_foundry_endpoint_is_the_project_model_host(foundry_speech: str) -> None:
    """`properties.endpoint` returns the classic `cognitiveservices.azure.com` host.

    The Foundry project model — project endpoint and the OpenAI v1 route — is served
    from `services.ai.azure.com`, and that is what the apps are configured with.
    """
    assert (
        "output foundryEndpoint string = 'https://${foundryName}.services.ai.azure.com'"
        in foundry_speech
    )


def test_foundry_private_endpoint_resolves_the_project_model_host(
    foundry_speech: str,
) -> None:
    """Without this zone the project endpoint is unreachable from the VNet."""
    network = code_of(MODULES_DIR / "network.bicep")
    assert "privatelink.services.ai.azure.com" in network
    assert re.search(r"aiServices: privateDnsZones\[\d+\]\.id", network)
    assert "aiServicesPrivateDnsZoneId" in foundry_speech
    assert "privatelink-services-ai-azure-com" in foundry_speech


def test_project_endpoint_output_targets_the_project_not_the_account(
    foundry_agents: str,
) -> None:
    assert "/api/projects/${projectName}" in foundry_agents
    assert ".services.ai.azure.com" in foundry_agents


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------


def test_project_endpoint_reaches_the_orchestrator(main: str) -> None:
    """There is no ARM resource for an agent — the endpoint is how they get created."""
    assert "foundryProjectEndpoint: foundryAgents.outputs.projectEndpoint" in main
    containerapps = code_of(MODULES_DIR / "containerapps.bicep")
    assert "FOUNDRY_PROJECT_ENDPOINT" in containerapps
    assert "AI_SEARCH_ENDPOINT" in containerapps
    assert "FOUNDRY_KNOWLEDGE_BASE" in containerapps
    assert "ONLINE_SEARCH_MODE" in containerapps


def test_search_identity_can_call_the_embedding_deployment(main: str) -> None:
    """Integrated vectorization needs Cognitive Services OpenAI User on the account."""
    block_start = main.index("module foundrySpeech")
    block = main[block_start : block_start + 3000]
    assert "aiSearch.outputs.searchPrincipalId" in block
    assert "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" in block


def test_online_search_defaults_to_offline_in_infrastructure(main: str) -> None:
    """Web backends leave the Azure compliance boundary; opting in must be explicit."""
    assert re.search(r"param onlineSearchMode string = 'offline'", main)


def test_online_search_mode_is_constrained(main: str) -> None:
    block_start = main.index("param onlineSearchMode")
    block = main[max(0, block_start - 400) : block_start]
    for mode in ("web_iq", "web_search", "offline"):
        assert f"'{mode}'" in block
