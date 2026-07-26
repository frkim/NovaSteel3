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

@description('Fabric capacity SKU. F2 is the cost-conscious default; F4 is the only pre-approved measurement fallback (deployment-topology.md §6).')
@allowed([
  'F2'
  'F4'
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

@description('MANUAL/QUOTA GATE — set true only after the research/azure-ai-regions.md deployment validation checklist has been executed in the target tenant. Does not itself enable Agent Service.')
param foundryAgentServiceManuallyValidated bool = false

@description('Deploy the placeholder Container Apps (bff-api, workers, ingest-relay, knowledge-orchestrator) and, for non-prod, the simulator publisher Job. Set false to provision only the platform (network/identity/data/monitoring) layer first.')
param deployContainerAppsPlaceholders bool = true

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
    privateEndpointSubnetId: network.outputs.subnetIds.apps
    privateDnsZoneId: network.outputs.privateDnsZoneIds.blob
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    roleAssignments: [
      {
        principalId: identity.outputs.bffPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
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
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    foundryAgentServiceManuallyValidated: foundryAgentServiceManuallyValidated
    foundryRoleAssignments: [
      {
        principalId: identity.outputs.bffPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
      }
      {
        principalId: identity.outputs.workerPrincipalId
        roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
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
