// NovaSteel Azure infrastructure — subscription-scoped orchestrator for ONE environment
// (dev | test | demo | prod). Run this template once per environment via
// infra/scripts/{validate,what-if,deploy}.ps1, using a matching infra/bicep/parameters/<env>.bicepparam.
//
// Scope discipline (implementation-guide.md §9.2 / §10, deployment-topology.md §3.2):
//   * This template provisions only ARM resources. Fabric workspaces, OneLake security roles,
//     Eventstreams, Eventhouse/KQL tables, Lakehouses, pipelines, notebooks, the Direct Lake
//     semantic model, and Power BI reports are Fabric SaaS-plane items and are OUT OF SCOPE —
//     they are owned by fabric/ and provisioned through the Fabric REST API/portal/Git
//     integration, never by Bicep. The only Microsoft.Fabric resource declared anywhere in this
//     repository is Microsoft.Fabric/capacities (see modules/fabric-capacity.bicep).
//   * Microsoft Foundry Agent Service project/agent creation is NOT provisioned here — see
//     modules/foundry-speech.bicep and infra/README.md "Deployment blockers".
//   * Region is Sweden Central by default; West Europe is an explicit, parameter-driven
//     contingency only (deployment-topology.md §1, §2.2) — never a silent secondary replica.
targetScope = 'subscription'

@description('Environment short name.')
@allowed([
  'dev'
  'test'
  'demo'
  'prod'
])
param environment string

@description('Azure region for this environment\'s resources. Sweden Central is the default/primary; West Europe is the only approved EU contingency and must be selected explicitly (deployment-topology.md §2.2) — it is never enabled implicitly as a replica.')
@allowed([
  'swedencentral'
  'westeurope'
])
param location string = 'swedencentral'

@description('Cost-center tag applied to every resource (mandatory, operations-and-cost.md §8.4).')
param costCenter string

@description('Owning team/individual tag applied to every resource (mandatory).')
param owner string

@description('Expiry date (yyyy-MM-dd) for this environment\'s resources. Mandatory (non-empty) for dev/test/demo per deployment-topology.md §3.1; optional for prod.')
param expiryDate string = ''

@description('Default data classification tag for resources that do not set a more specific value.')
param dataClassification string = 'Confidential'

@description('Fabric capacity SKU. F2 is the cost-conscious default, F4 the measured-contention fallback, and F8 the pre-approved demo-day burst tier requestable from the portal capacity dialog (deployment-topology.md §6).')
@allowed([
  'F2'
  'F4'
  'F8'
])
param fabricSkuName string = 'F2'

@description('At least one Fabric capacity administrator UPN/email — required by the Microsoft.Fabric/capacities ARM API.')
param fabricAdminMembers array

@description('Per-plant short names (e.g. [\'plant01\', \'plant02\']) — one Event Hub + OT-gateway managed identity is created per entry.')
param plants array = [
  'plant01'
]

@description('Deploy Azure Firewall in the hub subnet. Disabled by default to control cost (operations-and-cost.md §8.1); enable explicitly for prod after a cost/owner review.')
param deployFirewall bool = false

@description('Onboard Microsoft Sentinel on this environment\'s Log Analytics workspace.')
param deploySentinel bool = true

@description('Apply the subscription-wide NovaSteel policy guardrails from this deployment. Only ONE environment pipeline should set this true (see modules/policy-assignments.bicep header) to avoid redundant/racy concurrent subscription-scoped writes.')
param deployGuardrails bool = false

@description('Log Analytics interactive retention in days.')
param logAnalyticsRetentionDays int = 90

@description('Log Analytics daily ingestion cap in GB (-1 disables the cap).')
param logAnalyticsDailyQuotaGb int = -1

@description('GitHub organization/user that owns the deploying repository (required for GitHub OIDC federation).')
param githubOrg string = ''

@description('GitHub repository name (without org prefix) (required for GitHub OIDC federation).')
param githubRepo string = ''

@description('Monthly budget amount (billing currency) for this environment\'s 6 resource groups combined. Pull the actual figure from the live Azure/Fabric pricing calculator — do not copy an unverified number (deployment-topology.md §6).')
param budgetAmount int = 500

@description('Email addresses notified on budget thresholds.')
param budgetContactEmails array

@description('Budget start date, first day of a month, e.g. 2026-08-01T00:00:00Z.')
param budgetStartDate string = '2026-08-01T00:00:00Z'

@description('MANUAL/QUOTA GATE — set true only after the research/azure-ai-regions.md deployment validation checklist has been executed in the target tenant. Also gates creation of the Agent Service capability host, which is immutable once created.')
param foundryAgentServiceManuallyValidated bool = false

@description('Backend for the Copilot "Online search" toggle. web_iq uses the Foundry IQ web knowledge source, web_search uses the Agent Service web search tool, offline uses the curated in-repo public-context corpus. Defaults to offline: both web backends are First Party Consumption Services, so queries leave the Azure compliance and geo boundary and the Microsoft DPA does not cover them — enabling either is a deliberate, documented decision (security-governance-and-threat-model.md §4.1).')
@allowed([
  'web_iq'
  'web_search'
  'offline'
])
param onlineSearchMode string = 'offline'

@description('Deploy the placeholder Container Apps (bff-api, workers, ingest-relay, knowledge-orchestrator) and, for non-prod, the simulator publisher Job. Set false to provision only the platform (network/identity/data/monitoring) layer first.')
param deployContainerAppsPlaceholders bool = true

@description('Secondary EU region for disaster recovery validation (ADR-003). Never silently enabled as a replica — requires DPO approval and tested restore runbook before production use.')
@allowed([
  'westeurope'
  'northeurope'
  'francecentral'
])
param secondaryLocation string = 'westeurope'

@description('Email address for operational alert notifications.')
param alertEmail string = ''

@description('Optional webhook URI for PagerDuty/Teams alert integration.')
param alertWebhookUri string = ''

var isProd = environment == 'prod'
var regionAbbrev = location == 'swedencentral' ? 'sc' : 'we'
// Computed (not module-output-derived) so the Fabric capacity module and the Logic App lifecycle
// module can both reference the same resource ID without a circular module dependency between them.
var fabricCapacityName = 'cap-novasteel-${environment}-${regionAbbrev}'
var fabricCapacityResourceId = resourceId(rgFabric.name, 'Microsoft.Fabric/capacities', fabricCapacityName)

var commonTags = union(
  {
    environment: environment
    owner: owner
    costCenter: costCenter
    dataClassification: dataClassification
    recoveryTier: isProd ? 'primary' : 'non-production'
  },
  empty(expiryDate) ? {} : {
    expiry: expiryDate
  }
)

// ---------------------------------------------------------------------------
// Resource groups (deployment-topology.md §3.2)
// ---------------------------------------------------------------------------
resource rgHub 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-ns-${environment}-hub'
  location: location
  tags: commonTags
}

resource rgIntegration 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-ns-${environment}-integration'
  location: location
  tags: commonTags
}

resource rgApps 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-ns-${environment}-apps'
  location: location
  tags: commonTags
}

resource rgAi 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-ns-${environment}-ai'
  location: location
  tags: commonTags
}

resource rgFabric 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-ns-${environment}-fabric'
  location: location
  tags: commonTags
}

resource rgMonitoring 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-ns-${environment}-monitoring'
  location: location
  tags: commonTags
}

// ---------------------------------------------------------------------------
// Subscription-scoped guardrails: custom RBAC role + policy definitions/assignments
// ---------------------------------------------------------------------------
module roles 'modules/roles.bicep' = {
  name: 'ns-${environment}-roles'
  params: {
    environment: environment
    fabricResourceGroupId: rgFabric.id
  }
}

module guardrails 'modules/policy-assignments.bicep' = {
  name: 'ns-${environment}-guardrails'
  params: {
    deployGuardrails: deployGuardrails
    enforceExpiryTag: !isProd
  }
}

// ---------------------------------------------------------------------------
// Monitoring (must exist before every other module's diagnostic settings)
// ---------------------------------------------------------------------------
module monitoring 'modules/monitoring.bicep' = {
  name: 'ns-${environment}-monitoring'
  scope: rgMonitoring
  params: {
    environment: environment
    location: location
    tags: commonTags
    retentionInDays: logAnalyticsRetentionDays
    dailyQuotaGb: logAnalyticsDailyQuotaGb
    deploySentinel: deploySentinel
  }
}

// ---------------------------------------------------------------------------
// Networking (hub + spoke subnets + private DNS, all in rg-ns-<env>-hub — see network.bicep header)
// ---------------------------------------------------------------------------
module network 'modules/network.bicep' = {
  name: 'ns-${environment}-network'
  scope: rgHub
  params: {
    environment: environment
    location: location
    tags: commonTags
    deployFirewall: deployFirewall
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

// ---------------------------------------------------------------------------
// Identities (including GitHub OIDC federation)
// ---------------------------------------------------------------------------
module identity 'modules/identity.bicep' = {
  name: 'ns-${environment}-identity'
  scope: rgApps
  params: {
    environment: environment
    location: location
    tags: commonTags
    plants: plants
    deploySimulatorIdentity: !isProd
    deployGitHubOidcIdentity: true
    githubOrg: githubOrg
    githubRepo: githubRepo
    githubEnvironmentName: environment
  }
}

// ---------------------------------------------------------------------------
// Key Vaults — one per bounded context (security-governance-and-threat-model.md §5)
// ---------------------------------------------------------------------------
module keyVaultPlatform 'modules/keyvault.bicep' = {
  name: 'ns-${environment}-kv-platform'
  scope: rgApps
  params: {
    name: 'kv-ns-${environment}-platform'
    location: location
    tags: commonTags
    privateEndpointSubnetId: network.outputs.subnetIds.apps
    privateDnsZoneId: network.outputs.privateDnsZoneIds.keyVault
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    enablePurgeProtection: true
    roleAssignments: [
      {
        principalId: identity.outputs.bffPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
      }
      {
        principalId: identity.outputs.workerPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
      }
      {
        principalId: identity.outputs.knowledgeOrchestratorPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
      }
    ]
  }
}

module keyVaultOtGateway 'modules/keyvault.bicep' = {
  name: 'ns-${environment}-kv-otgw'
  scope: rgIntegration
  params: {
    name: 'kv-ns-${environment}-otgw'
    location: location
    tags: commonTags
    privateEndpointSubnetId: network.outputs.subnetIds.integration
    privateDnsZoneId: network.outputs.privateDnsZoneIds.keyVault
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    enablePurgeProtection: true
    roleAssignments: [
      {
        principalId: identity.outputs.ingestRelayPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// Storage for permitted audio/fallback artifacts (solution-architecture.md §8.2)
// ---------------------------------------------------------------------------
module storageAudio 'modules/storage.bicep' = {
  name: 'ns-${environment}-storage-audio'
  scope: rgAi
  params: {
    name: 'stnsaudio${environment}${regionAbbrev}'
    location: location
    tags: commonTags
    dataClassification: 'HighlyConfidential'
    containers: [
      'raw-audio'
      'transcripts'
    ]
    privateEndpointSubnetId: network.outputs.subnetIds.aiPrivateEndpoints
    privateDnsZoneId: network.outputs.privateDnsZoneIds.blob
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    roleAssignments: [
      {
        principalId: identity.outputs.knowledgeOrchestratorPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
      }
    ]
  }
}

module storageFallback 'modules/storage.bicep' = {
  name: 'ns-${environment}-storage-fallback'
  scope: rgApps
  params: {
    name: 'stnsfallback${environment}${regionAbbrev}'
    location: location
    tags: commonTags
    dataClassification: 'DEMO-NONPERSONAL'
    containers: [
      'fallback-pack'
      'proof-pack'
    ]
    tables: [
      'bffauditlog'
      'bffidempotency'
    ]
    privateEndpointSubnetId: network.outputs.subnetIds.apps
    privateDnsZoneId: network.outputs.privateDnsZoneIds.blob
    tablePrivateDnsZoneId: network.outputs.privateDnsZoneIds.table
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    roleAssignments: [
      {
        principalId: identity.outputs.bffPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
      }
      {
        // Storage Table Data Contributor for BFF audit log + idempotency store (M10)
        principalId: identity.outputs.bffPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3')
      }
      {
        principalId: identity.outputs.simulatorPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// Event Hubs (per-plant OT telemetry ingestion)
// ---------------------------------------------------------------------------
module eventHubs 'modules/eventhubs.bicep' = {
  name: 'ns-${environment}-eventhubs'
  scope: rgIntegration
  params: {
    name: 'evh-novasteel-${environment}-${regionAbbrev}'
    location: location
    tags: commonTags
    plants: plants
    otGatewayIdentities: identity.outputs.otGatewayIdentities
    ingestRelayPrincipalId: identity.outputs.ingestRelayPrincipalId
    privateEndpointSubnetId: network.outputs.subnetIds.integration
    privateDnsZoneId: network.outputs.privateDnsZoneIds.serviceBus
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    isProduction: isProd
  }
}

// ---------------------------------------------------------------------------
// Fabric capacity — the only Microsoft.Fabric ARM resource in this repository
// ---------------------------------------------------------------------------
module fabricCapacity 'modules/fabric-capacity.bicep' = {
  name: 'ns-${environment}-fabric-capacity'
  scope: rgFabric
  params: {
    name: fabricCapacityName
    location: location
    tags: commonTags
    skuName: fabricSkuName
    adminMembers: fabricAdminMembers
    capacityOperatorPrincipalId: identity.outputs.capacityPrincipalId
    capacityOperatorRoleDefinitionId: roles.outputs.capacityOperatorRoleId
    additionalOperatorPrincipalIds: isProd ? [] : [
      logicAppCapacityLifecycle.?outputs.?principalId ?? ''
    ]
  }
}

// ---------------------------------------------------------------------------
// 01:00 Europe/Luxembourg capacity lifecycle Logic App — dev/test/demo only, never prod
// ---------------------------------------------------------------------------
module logicAppCapacityLifecycle 'modules/logicapp-capacity-lifecycle.bicep' = if (!isProd) {
  name: 'ns-${environment}-capacity-lifecycle'
  scope: rgFabric
  params: {
    environment: environment
    location: location
    tags: commonTags
    capacityResourceId: fabricCapacityResourceId
    capacityName: fabricCapacityName
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

// ---------------------------------------------------------------------------
// Foundry + Speech (base resource accounts only — no Agent Service project/agent)
// ---------------------------------------------------------------------------
module foundrySpeech 'modules/foundry-speech.bicep' = {
  name: 'ns-${environment}-foundry-speech'
  scope: rgAi
  params: {
    environment: environment
    location: location
    tags: commonTags
    privateEndpointSubnetId: network.outputs.subnetIds.aiPrivateEndpoints
    cognitiveServicesPrivateDnsZoneId: network.outputs.privateDnsZoneIds.cognitiveServices
    openAiPrivateDnsZoneId: network.outputs.privateDnsZoneIds.openAi
    aiServicesPrivateDnsZoneId: network.outputs.privateDnsZoneIds.aiServices
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    foundryAgentServiceManuallyValidated: foundryAgentServiceManuallyValidated
    foundryRoleAssignments: [
      {
        // Cognitive Services OpenAI User — required for data-plane chat/embedding inference
        principalId: identity.outputs.bffPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
      }
      {
        // Cognitive Services OpenAI User — required for data-plane chat/embedding inference
        principalId: identity.outputs.workerPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
      }
      {
        // Cognitive Services OpenAI User — knowledge-orchestrator makes live GPT-5 calls (M3)
        principalId: identity.outputs.knowledgeOrchestratorPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
      }
      {
        // Cognitive Services OpenAI User for the AI Search service identity. Required
        // for integrated vectorization: Search calls the embedding deployment itself
        // when indexing a procedure and when vectorizing an incoming query, so no
        // embedding keys ever leave the Foundry account.
        principalId: aiSearch.outputs.searchPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
      }
    ]
    speechRoleAssignments: [
      {
        principalId: identity.outputs.knowledgeOrchestratorPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'f2dc8367-1007-4938-bd23-fe263f013447')
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// Procedure knowledge store + Foundry Agent Service backing resources
// ---------------------------------------------------------------------------
// Azure AI Search holds the approved procedures (the corpus the Copilot cites from,
// and the knowledge source behind the Foundry IQ knowledge base). Cosmos DB and the
// agents storage account are the BYO thread/file stores that Foundry Agent Service
// "standard" setup requires — see modules/foundry-agents.bicep for why we take the
// BYO route rather than Microsoft-managed storage.
module aiSearch 'modules/ai-search.bicep' = {
  name: 'ns-${environment}-ai-search'
  scope: rgAi
  params: {
    environment: environment
    location: location
    tags: commonTags
    privateEndpointSubnetId: network.outputs.subnetIds.aiPrivateEndpoints
    searchPrivateDnsZoneId: network.outputs.privateDnsZoneIds.search
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    skuName: isProd ? 'standard' : 'basic'
    roleAssignments: [
      {
        // Search Index Data Contributor — knowledge-orchestrator writes approved
        // procedures into the index and deletes them on GDPR erasure.
        principalId: identity.outputs.knowledgeOrchestratorPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
      }
      {
        // Search Service Contributor — the orchestrator creates/updates the index,
        // the knowledge source and the knowledge base at startup (data-plane objects
        // that Bicep cannot express).
        principalId: identity.outputs.knowledgeOrchestratorPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
      }
      {
        // Search Index Data Reader — the BFF only ever queries.
        principalId: identity.outputs.bffPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '1407120a-92aa-4202-b7e9-c0e197c71c8f')
      }
    ]
  }
}

module cosmosAgentThreads 'modules/cosmos.bicep' = {
  name: 'ns-${environment}-cosmos-threads'
  scope: rgAi
  params: {
    environment: environment
    location: location
    tags: commonTags
    privateEndpointSubnetId: network.outputs.subnetIds.aiPrivateEndpoints
    cosmosPrivateDnsZoneId: network.outputs.privateDnsZoneIds.cosmosDb
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    zoneRedundant: isProd
  }
}

module storageAgents 'modules/storage.bicep' = {
  name: 'ns-${environment}-storage-agents'
  scope: rgAi
  params: {
    name: 'stnsagents${environment}${regionAbbrev}'
    location: location
    tags: commonTags
    // Agent file uploads can contain interview-derived content, same class as the
    // audio/transcript store.
    dataClassification: 'HighlyConfidential'
    // Deliberately empty: Agent Service creates and names its own containers when the
    // project capability host is provisioned.
    containers: []
    privateEndpointSubnetId: network.outputs.subnetIds.aiPrivateEndpoints
    privateDnsZoneId: network.outputs.privateDnsZoneIds.blob
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

// ---------------------------------------------------------------------------
// Foundry Agent Service — project, connections, observability link, capability host
// ---------------------------------------------------------------------------
// Deployed as a four-step chain because the ordering is load-bearing:
//   foundryAgents          -> project + BYO connections + App Insights connection
//   appInsightsAgentAccess -> project identity can read back its own traces
//   foundryAgentRbac       -> project identity can write to Cosmos/Storage/Search
//   foundryAgentCapability -> switches Agent Service on (needs all of the above)
// The last step is behind the manual quota gate because a capability host is
// immutable once created.
module foundryAgents 'modules/foundry-agents.bicep' = {
  name: 'ns-${environment}-foundry-agents'
  scope: rgAi
  params: {
    environment: environment
    location: location
    tags: commonTags
    foundryAccountName: foundrySpeech.outputs.foundryAccountName
    searchServiceName: aiSearch.outputs.searchServiceName
    searchServiceId: aiSearch.outputs.searchServiceId
    cosmosAccountName: cosmosAgentThreads.outputs.cosmosAccountName
    cosmosAccountId: cosmosAgentThreads.outputs.cosmosAccountId
    cosmosDocumentEndpoint: cosmosAgentThreads.outputs.cosmosDocumentEndpoint
    agentStorageAccountName: storageAgents.outputs.storageAccountName
    agentStorageAccountId: storageAgents.outputs.storageAccountId
    agentStorageBlobEndpoint: storageAgents.outputs.primaryBlobEndpoint
    appInsightsId: monitoring.outputs.appInsightsId
  }
}

module appInsightsAgentAccess 'modules/appinsights-agent-access.bicep' = {
  name: 'ns-${environment}-appi-agent-access'
  scope: rgMonitoring
  params: {
    appInsightsName: monitoring.outputs.appInsightsName
    projectPrincipalId: foundryAgents.outputs.projectPrincipalId
  }
}

module foundryAgentRbac 'modules/foundry-agent-rbac.bicep' = {
  name: 'ns-${environment}-foundry-agent-rbac'
  scope: rgAi
  params: {
    cosmosAccountName: cosmosAgentThreads.outputs.cosmosAccountName
    agentStorageAccountName: storageAgents.outputs.storageAccountName
    projectPrincipalId: foundryAgents.outputs.projectPrincipalId
  }
}

module foundryAgentCapabilityHost 'modules/foundry-agent-capability-host.bicep' = if (foundryAgentServiceManuallyValidated) {
  name: 'ns-${environment}-foundry-caphost'
  scope: rgAi
  params: {
    foundryAccountName: foundrySpeech.outputs.foundryAccountName
    projectName: foundryAgents.outputs.projectName
    searchConnectionName: foundryAgents.outputs.searchConnectionName
    cosmosConnectionName: foundryAgents.outputs.cosmosConnectionName
    storageConnectionName: foundryAgents.outputs.storageConnectionName
  }
  dependsOn: [
    foundryAgentRbac
  ]
}

// ---------------------------------------------------------------------------
// Container Apps environment + placeholder apps/jobs
// ---------------------------------------------------------------------------
module containerApps 'modules/containerapps.bicep' = if (deployContainerAppsPlaceholders) {
  name: 'ns-${environment}-containerapps'
  scope: rgApps
  params: {
    environment: environment
    location: location
    tags: commonTags
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    logAnalyticsCustomerId: monitoring.outputs.logAnalyticsCustomerId
    infrastructureSubnetId: network.outputs.subnetIds.containerAppsInfra
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    isProduction: isProd
    bffTableEndpoint: storageFallback.outputs.primaryTableEndpoint
    bffStorageAccountName: storageFallback.outputs.storageAccountName
    foundryEndpoint: foundrySpeech.outputs.foundryEndpoint
    foundryChatDeployment: foundrySpeech.outputs.gptDeploymentModelName
    foundryEmbedDeployment: foundrySpeech.outputs.embeddingDeploymentModelName
    foundryReasoningDeployment: foundrySpeech.outputs.reasoningDeploymentModelName
    foundryProjectEndpoint: foundryAgents.outputs.projectEndpoint
    searchEndpoint: aiSearch.outputs.searchEndpoint
    searchIndexName: aiSearch.outputs.procedureIndexName
    knowledgeBaseName: aiSearch.outputs.knowledgeBaseName
    onlineSearchMode: onlineSearchMode
    deploySimulatorJob: !isProd
    simulatorIdentityId: isProd ? '' : identity.outputs.simulatorIdentityId
    services: {
      bffApi: {
        identityId: identity.outputs.bffIdentityId
        keyVaultUri: keyVaultPlatform.outputs.vaultUri
      }
      optimizerWorker: {
        identityId: identity.outputs.workerIdentityId
        keyVaultUri: keyVaultPlatform.outputs.vaultUri
      }
      scoringWorker: {
        identityId: identity.outputs.workerIdentityId
        keyVaultUri: keyVaultPlatform.outputs.vaultUri
      }
      ingestRelay: {
        identityId: identity.outputs.ingestRelayIdentityId
        keyVaultUri: keyVaultOtGateway.outputs.vaultUri
      }
      knowledgeOrchestrator: {
        identityId: identity.outputs.knowledgeOrchestratorIdentityId
        keyVaultUri: keyVaultPlatform.outputs.vaultUri
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Budget / cost alerts (operations-and-cost.md §8.4)
// ---------------------------------------------------------------------------
module budget 'modules/budget.bicep' = {
  name: 'ns-${environment}-budget'
  params: {
    environment: environment
    resourceGroupNames: [
      rgHub.name
      rgIntegration.name
      rgApps.name
      rgAi.name
      rgFabric.name
      rgMonitoring.name
    ]
    amount: budgetAmount
    contactEmails: budgetContactEmails
    startDate: budgetStartDate
  }
}

// ---------------------------------------------------------------------------
// Operational alerts (operations-and-cost.md §4 — 10 alert rules)
// ---------------------------------------------------------------------------
module alerts 'modules/alerts.bicep' = {
  name: 'ns-${environment}-alerts'
  scope: rgMonitoring
  params: {
    environment: environment
    location: location
    tags: commonTags
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    appInsightsId: monitoring.outputs.appInsightsId
    alertEmail: alertEmail
    webhookUri: alertWebhookUri
    enableAlerts: isProd || environment == 'demo'
  }
}

// ---------------------------------------------------------------------------
// Outputs consumed by app/Fabric setup automation (fabric/deployment-parameters/<env>.json,
// infra/scripts, and CI/CD) — implementation-guide.md §9.3.
// ---------------------------------------------------------------------------
output resourceGroups object = {
  hub: rgHub.name
  integration: rgIntegration.name
  apps: rgApps.name
  ai: rgAi.name
  fabric: rgFabric.name
  monitoring: rgMonitoring.name
}
output fabricCapacityId string = fabricCapacity.outputs.capacityId
output fabricCapacityName string = fabricCapacity.outputs.capacityName
output eventHubsNamespaceId string = eventHubs.outputs.namespaceId
output eventHubsNamespaceName string = eventHubs.outputs.namespaceName
output eventHubNames array = eventHubs.outputs.eventHubNames
output keyVaultPlatformUri string = keyVaultPlatform.outputs.vaultUri
output keyVaultOtGatewayUri string = keyVaultOtGateway.outputs.vaultUri
output logAnalyticsWorkspaceId string = monitoring.outputs.logAnalyticsWorkspaceId
output appInsightsConnectionString string = monitoring.outputs.appInsightsConnectionString
output foundryEndpoint string = foundrySpeech.outputs.foundryEndpoint
output speechEndpoint string = foundrySpeech.outputs.speechEndpoint
output foundryAgentServiceGateCleared bool = foundrySpeech.outputs.foundryAgentServiceGateCleared
output gitHubOidcClientId string = identity.outputs.gitHubOidcClientId
output gitHubFederationConfigured bool = identity.outputs.gitHubFederationConfigured
output containerAppsEnvironmentId string = deployContainerAppsPlaceholders ? (containerApps.?outputs.?environmentId ?? '') : ''
output capacityLifecycleLogicAppId string = isProd ? '' : (logicAppCapacityLifecycle.?outputs.?workflowId ?? '')
output audioStorageAccountName string = storageAudio.outputs.storageAccountName
output fallbackStorageAccountName string = storageFallback.outputs.storageAccountName
output agentStorageAccountName string = storageAgents.outputs.storageAccountName
output searchEndpoint string = aiSearch.outputs.searchEndpoint
output searchServiceName string = aiSearch.outputs.searchServiceName
output procedureIndexName string = aiSearch.outputs.procedureIndexName
output knowledgeBaseName string = aiSearch.outputs.knowledgeBaseName
output cosmosAgentThreadsAccountName string = cosmosAgentThreads.outputs.cosmosAccountName
@description('Foundry project data-plane endpoint. Agent definitions are created here by the knowledge-orchestrator at startup; ARM has no agent resource type.')
output foundryProjectEndpoint string = foundryAgents.outputs.projectEndpoint
output foundryProjectName string = foundryAgents.outputs.projectName
@description('True once the Agent Service capability host has been provisioned. Until then the project exists but cannot run agents, and the orchestrator stays on its local fallback.')
output agentServiceReady bool = foundryAgentServiceManuallyValidated
output foundryChatDeployment string = foundrySpeech.outputs.gptDeploymentModelName
output foundryReasoningDeployment string = foundrySpeech.outputs.reasoningDeploymentModelName
output onlineSearchMode string = onlineSearchMode
output secondaryLocation string = secondaryLocation
output alertsActionGroupId string = alerts.outputs.actionGroupId
