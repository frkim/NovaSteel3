// Foundry Agent Service, Azure AI Search and agent thread storage for the isolated
// NovaSteel v3 demo estate.
//
// This is the cost-capped sibling of `infra/bicep/modules/foundry-agents.bicep` +
// `ai-search.bicep` + `cosmos.bicep`. The production template targets a private,
// hub-and-spoke estate with private endpoints on every data plane; this demo estate
// is deliberately public-with-Entra-only, matching the posture already set by the
// Key Vault, Storage and AI Services resources in `platform.bicep`. Local/key auth
// is still disabled everywhere, so "public" here means "reachable", never "open".
//
// Cost shape (the reason this module is opt-in rather than always-on):
//   * Azure AI Search `basic` is a fixed monthly charge whether or not it is queried.
//     It is the cheapest tier that supports semantic ranking and more than one index.
//   * Cosmos DB is provisioned as **serverless**, so an idle demo pays only for the
//     handful of request units an agent thread actually consumes.
//   * The Foundry project itself is free; the model deployments it uses are billed
//     per token by `platform.bicep`.
//
// Deployment ordering is load-bearing and mirrors the production template: the
// project and its connections must exist before the RBAC, and the RBAC must exist
// before the capability host, because at capability-host creation the platform
// provisions the `enterprise_memory` Cosmos database and the agent blob containers
// *using the project's own managed identity*. Do not pre-create those.
targetScope = 'resourceGroup'

param location string

@minLength(1)
param resourcePrefix string

@minLength(1)
param nameSuffix string

param tags object

@description('Name of the existing AIServices account that will host the Foundry project.')
param aiServicesName string

@description('Name of the existing storage account used for agent file uploads.')
param storageAccountName string

@description('Name of the existing Application Insights component that receives agent traces.')
param appInsightsName string

@description('Search tier. `basic` is the cheapest tier supporting semantic ranking; `free` cannot host this workload (one index, no semantic ranker).')
@allowed([
  'basic'
  'standard'
])
param searchSku string = 'basic'

@description('Create the Agent Service capability hosts. A capability host is IMMUTABLE: once created it cannot be repointed at different Search/Cosmos/Storage accounts, and changing them means recreating the project. Leave false until the three stores above are final.')
param agentServiceManuallyValidated bool = false

@description('Principal ID of the BFF managed identity. The BFF reads and writes the procedure index directly, so it needs its own Search access separate from the project identity.')
param bffPrincipalId string = ''

var searchServiceName = '${resourcePrefix}-srch-${nameSuffix}'
var cosmosAccountName = '${resourcePrefix}-cosmos-${nameSuffix}'
var projectName = '${resourcePrefix}-proj'
var operationsProjectName = '${resourcePrefix}-ops-proj'
var searchConnectionName = '${resourcePrefix}-conn-search'
var cosmosConnectionName = '${resourcePrefix}-conn-cosmos'
var storageConnectionName = '${resourcePrefix}-conn-storage'
// Connection names are unique per Foundry ACCOUNT, not per project: the service
// rejects a second project reusing a name with "already exist, and can only be
// updated by the workspace that created it". The operations project therefore
// needs its own names even though it points at the same three backing stores.
var operationsSearchConnectionName = '${resourcePrefix}-ops-conn-search'
var operationsCosmosConnectionName = '${resourcePrefix}-ops-conn-cosmos'
var operationsStorageConnectionName = '${resourcePrefix}-ops-conn-storage'
var appInsightsConnectionName = '${resourcePrefix}-conn-appinsights'
var accountCapabilityHostName = '${resourcePrefix}-account-caphost'
var projectCapabilityHostName = '${resourcePrefix}-project-caphost'
var operationsProjectCapabilityHostName = '${resourcePrefix}-ops-project-caphost'

var searchIndexDataContributorRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
var searchServiceContributorRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
var cognitiveServicesOpenAiUserRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
var cosmosDbOperatorRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '230815da-be43-4aae-9cb4-875f7bd000aa')
var storageAccountContributorRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '17d1049b-9a84-46fb-8f53-869881c3d3ab')
var storageBlobDataOwnerRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b')
var monitoringMetricsPublisherRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '3913510d-42f4-4e42-8a64-420c390055eb')

// Declared at the project-capable API version to match `platform.bicep`. Older
// versions predate the Foundry project model (`accounts/projects`), so referencing
// the parent at 2024-10-01 here would describe a classic Cognitive Services account.
resource aiServices 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: aiServicesName
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

// ---------------------------------------------------------------------------
// Azure AI Search — the approved-procedure corpus and the Foundry IQ source
// ---------------------------------------------------------------------------

resource searchService 'Microsoft.Search/searchServices@2025-05-01' = {
  name: searchServiceName
  location: location
  tags: tags
  sku: {
    name: searchSku
  }
  identity: {
    // Needed so the service can call the embedding deployment for integrated
    // vectorization without a key changing hands.
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'Default'
    publicNetworkAccess: 'Enabled'
    // Mutually exclusive with authOptions, which is why authOptions is never set.
    disableLocalAuth: true
    semanticSearch: 'free'
  }
}

resource searchOpenAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiServices.id, searchService.id, cognitiveServicesOpenAiUserRoleDefinitionId)
  scope: aiServices
  properties: {
    principalId: searchService.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: cognitiveServicesOpenAiUserRoleDefinitionId
  }
}

// ---------------------------------------------------------------------------
// Cosmos DB — agent thread storage
// ---------------------------------------------------------------------------

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-12-01-preview' = {
  name: cosmosAccountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    databaseAccountOfferType: 'Standard'
    // Serverless keeps an idle demo close to zero. It is not appropriate for the
    // production estate, which uses provisioned throughput.
    // Expressed as `capacityMode` rather than the `EnableServerless` capability:
    // the control plane rejects that capability on any API version after
    // 2024-05-15-preview.
    #disable-next-line BCP037
    capacityMode: 'Serverless'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    // Pinned to the value the live account already carries. It is a no-op on a
    // single-region account, but leaving it unset makes every deployment of this
    // module flip it back to false — gratuitous churn on an account shared with
    // the agent thread storage.
    enableAutomaticFailover: true
    publicNetworkAccess: 'Enabled'
    // Requested, but NOT guaranteed: the management-group Modify policy
    // `cosmosdb_publicnetwork_modify` overwrites this with 'Disabled' on every
    // write. The Agent Service reaches its thread storage over the public
    // endpoint in this estate, so while it is disabled, agent creation fails with
    // `cosmos_vnet_blocked` even though every resource here reports Succeeded.
    // A policy exemption is the durable fix; see README.md.
    disableLocalAuth: true
    disableKeyBasedMetadataWriteAccess: true
  }
}

// ---------------------------------------------------------------------------
// Foundry project and its bring-your-own-storage connections
// ---------------------------------------------------------------------------

#disable-next-line BCP081
resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: aiServices
  name: projectName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'NovaSteel v3 demo agents'
    description: 'Hosts the procedure agent and its Foundry IQ knowledge base.'
  }
}

#disable-next-line BCP081
resource searchConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: project
  name: searchConnectionName
  properties: {
    category: 'CognitiveSearch'
    target: 'https://${searchService.name}.search.windows.net'
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: searchService.id
      location: location
    }
  }
}

#disable-next-line BCP081
resource cosmosConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: project
  name: cosmosConnectionName
  properties: {
    // The Foundry sample spells this category `CosmosDB` even though the generic
    // ARM enum documents `CosmosDb`. Follow the sample: the service matches on it.
    category: 'CosmosDB'
    target: cosmosAccount.properties.documentEndpoint
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: cosmosAccount.id
      location: location
    }
  }
}

#disable-next-line BCP081
resource storageConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: project
  name: storageConnectionName
  properties: {
    category: 'AzureStorageAccount'
    target: storageAccount.properties.primaryEndpoints.blob
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: storageAccount.id
      location: location
    }
  }
}

// ---------------------------------------------------------------------------
// Operations project — the tool-calling trust boundary
// ---------------------------------------------------------------------------
// A Foundry agent can only call the tools declared on its own definition, and a
// definition belongs to exactly one project. The project above hosts the agents that
// read untrusted content (approved procedures, interview transcripts, web results)
// and hold no tool that can reach a NovaSteel calculation. This second project hosts
// the agents that do call function tools — energy dispatch simulation, lining RUL
// forecasts. Keeping them apart means a prompt injected into a retrieved procedure
// has no path to `simulate_energy_dispatch`, because no agent that reads procedures
// was ever given that tool.
//
// Everything else is shared with the knowledge project: same account, same Search,
// Cosmos, Storage and Application Insights. The boundary being bought here is over
// tool reachability, not data at rest, and a second set of backing stores would
// double the demo cost for no gain. The Search connection exists only because the
// capability-host contract requires a vector store; no agent in this project uses it.
resource operationsProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: aiServices
  name: operationsProjectName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'NovaSteel v3 demo operations agents'
    description: 'Hosts the tool-calling operations agents. Their tools call the audited deterministic services; every result is a proposal requiring human approval (ADR-006, ADR-007).'
  }
}

#disable-next-line BCP081
resource operationsSearchConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: operationsProject
  name: operationsSearchConnectionName
  properties: {
    category: 'CognitiveSearch'
    target: 'https://${searchService.name}.search.windows.net'
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: searchService.id
      location: location
    }
  }
}

#disable-next-line BCP081
resource operationsCosmosConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: operationsProject
  name: operationsCosmosConnectionName
  properties: {
    category: 'CosmosDB'
    target: cosmosAccount.properties.documentEndpoint
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: cosmosAccount.id
      location: location
    }
  }
}

#disable-next-line BCP081
resource operationsStorageConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: operationsProject
  name: operationsStorageConnectionName
  properties: {
    category: 'AzureStorageAccount'
    target: storageAccount.properties.primaryEndpoints.blob
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: storageAccount.id
      location: location
    }
  }
}

// The Application Insights connection is deliberately on the ACCOUNT, not the
// project: that is what lights up the Foundry portal's Tracing and Monitoring
// blades and lets Agent Service export GenAI spans to the same component the rest
// of the platform already writes to.
#disable-next-line BCP081
// `ProjectManagedIdentity`, not `ApiKey`. The service accepts only those two, and
// `ApiKey` makes the platform persist the connection string through its credential
// service, which requires an associated Key Vault; this keyless account has none,
// so that path fails with an opaque HTTP 500. Managed identity stores no secret.
resource appInsightsConnection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = {
  parent: aiServices
  name: appInsightsConnectionName
  properties: {
    category: 'AppInsights'
    target: applicationInsights.id
    // The ARM enum has not caught up; the service accepts (and requires) this value.
    #disable-next-line BCP036
    authType: 'ProjectManagedIdentity'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: applicationInsights.id
      location: location
    }
  }
}

// The connection authenticates as the project identity, so that identity needs to
// be able to publish telemetry into the component.
resource projectMonitoringMetricsPublisher 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(applicationInsights.id, project.id, monitoringMetricsPublisherRoleDefinitionId)
  scope: applicationInsights
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: monitoringMetricsPublisherRoleDefinitionId
  }
}

// The BFF creates the procedure index and writes documents into it under its own
// identity (search_store.py), so it needs both index management and document
// access. Without these the AI Search path returns 403 and the orchestrator
// silently degrades to the bundled corpus, which looks like a working demo.
resource bffSearchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(bffPrincipalId)) {
  name: guid(searchService.id, bffPrincipalId, searchServiceContributorRoleDefinitionId)
  scope: searchService
  properties: {
    principalId: bffPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: searchServiceContributorRoleDefinitionId
  }
}

resource bffSearchIndexDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(bffPrincipalId)) {
  name: guid(searchService.id, bffPrincipalId, searchIndexDataContributorRoleDefinitionId)
  scope: searchService
  properties: {
    principalId: bffPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: searchIndexDataContributorRoleDefinitionId
  }
}

// ---------------------------------------------------------------------------
// RBAC for the project identity — must land before the capability host
// ---------------------------------------------------------------------------

resource projectSearchIndexDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, project.id, searchIndexDataContributorRoleDefinitionId)
  scope: searchService
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: searchIndexDataContributorRoleDefinitionId
  }
}

resource projectSearchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, project.id, searchServiceContributorRoleDefinitionId)
  scope: searchService
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: searchServiceContributorRoleDefinitionId
  }
}

resource projectCosmosOperator 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmosAccount.id, project.id, cosmosDbOperatorRoleDefinitionId)
  scope: cosmosAccount
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: cosmosDbOperatorRoleDefinitionId
  }
}

// Cosmos data-plane access is not an ARM role. This is scoped to the whole account
// rather than to individual containers because the containers Agent Service uses do
// not exist until the capability host creates them — scoping tighter would be a
// chicken-and-egg problem inside a single deployment.
resource projectCosmosDataContributor 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-12-01-preview' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, project.id, 'sql-data-contributor')
  properties: {
    principalId: project.identity.principalId
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    scope: cosmosAccount.id
  }
}

resource projectStorageAccountContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, project.id, storageAccountContributorRoleDefinitionId)
  scope: storageAccount
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: storageAccountContributorRoleDefinitionId
  }
}

resource projectStorageBlobDataOwner 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, project.id, storageBlobDataOwnerRoleDefinitionId)
  scope: storageAccount
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: storageBlobDataOwnerRoleDefinitionId
  }
}

// ---------------------------------------------------------------------------
// Capability hosts — the switch that actually turns Agent Service on
// ---------------------------------------------------------------------------

// The same six grants as the knowledge project, for the operations identity. The
// capability host provisions its own enterprise_memory database and blob containers
// as this identity, so they must exist before it is created.
resource operationsProjectSearchIndexDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, operationsProject.id, searchIndexDataContributorRoleDefinitionId)
  scope: searchService
  properties: {
    principalId: operationsProject.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: searchIndexDataContributorRoleDefinitionId
  }
}

resource operationsProjectSearchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, operationsProject.id, searchServiceContributorRoleDefinitionId)
  scope: searchService
  properties: {
    principalId: operationsProject.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: searchServiceContributorRoleDefinitionId
  }
}

resource operationsProjectCosmosOperator 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmosAccount.id, operationsProject.id, cosmosDbOperatorRoleDefinitionId)
  scope: cosmosAccount
  properties: {
    principalId: operationsProject.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: cosmosDbOperatorRoleDefinitionId
  }
}

resource operationsProjectCosmosDataContributor 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-12-01-preview' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, operationsProject.id, 'sql-data-contributor')
  properties: {
    principalId: operationsProject.identity.principalId
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    scope: cosmosAccount.id
  }
}

resource operationsProjectStorageAccountContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, operationsProject.id, storageAccountContributorRoleDefinitionId)
  scope: storageAccount
  properties: {
    principalId: operationsProject.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: storageAccountContributorRoleDefinitionId
  }
}

resource operationsProjectStorageBlobDataOwner 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, operationsProject.id, storageBlobDataOwnerRoleDefinitionId)
  scope: storageAccount
  properties: {
    principalId: operationsProject.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: storageBlobDataOwnerRoleDefinitionId
  }
}

resource operationsProjectMonitoringMetricsPublisher 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(applicationInsights.id, operationsProject.id, monitoringMetricsPublisherRoleDefinitionId)
  scope: applicationInsights
  properties: {
    principalId: operationsProject.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: monitoringMetricsPublisherRoleDefinitionId
  }
}

#disable-next-line BCP081
resource accountCapabilityHost 'Microsoft.CognitiveServices/accounts/capabilityHosts@2025-04-01-preview' = if (agentServiceManuallyValidated) {
  parent: aiServices
  name: accountCapabilityHostName
  properties: {
    capabilityHostKind: 'Agents'
  }
}

#disable-next-line BCP081
resource projectCapabilityHost 'Microsoft.CognitiveServices/accounts/projects/capabilityHosts@2025-04-01-preview' = if (agentServiceManuallyValidated) {
  parent: project
  name: projectCapabilityHostName
  properties: {
    // Connections are referenced by NAME here, not by ARM resource ID.
    #disable-next-line BCP037
    capabilityHostKind: 'Agents'
    vectorStoreConnections: [
      searchConnectionName
    ]
    threadStorageConnections: [
      cosmosConnectionName
    ]
    storageConnections: [
      storageConnectionName
    ]
  }
  dependsOn: [
    accountCapabilityHost
    searchConnection
    cosmosConnection
    storageConnection
    projectSearchIndexDataContributor
    projectSearchServiceContributor
    projectCosmosOperator
    projectCosmosDataContributor
    projectStorageAccountContributor
    projectStorageBlobDataOwner
  ]
}

// Serialised behind the knowledge project's host: both share the account-level
// capability host, and provisioning them concurrently races on it.
#disable-next-line BCP081
resource operationsProjectCapabilityHost 'Microsoft.CognitiveServices/accounts/projects/capabilityHosts@2025-04-01-preview' = if (agentServiceManuallyValidated) {
  parent: operationsProject
  name: operationsProjectCapabilityHostName
  properties: {
    #disable-next-line BCP037
    capabilityHostKind: 'Agents'
    vectorStoreConnections: [
      operationsSearchConnectionName
    ]
    threadStorageConnections: [
      operationsCosmosConnectionName
    ]
    storageConnections: [
      operationsStorageConnectionName
    ]
  }
  dependsOn: [
    accountCapabilityHost
    projectCapabilityHost
    operationsSearchConnection
    operationsCosmosConnection
    operationsStorageConnection
    operationsProjectSearchIndexDataContributor
    operationsProjectSearchServiceContributor
    operationsProjectCosmosOperator
    operationsProjectCosmosDataContributor
    operationsProjectStorageAccountContributor
    operationsProjectStorageBlobDataOwner
  ]
}

output searchServiceId string = searchService.id
output searchServiceName string = searchService.name
output searchEndpoint string = 'https://${searchService.name}.search.windows.net'
output cosmosAccountId string = cosmosAccount.id
output cosmosAccountName string = cosmosAccount.name
output projectId string = project.id
output projectName string = project.name
// The data-plane endpoint the knowledge orchestrator uses to create agents, threads
// and runs. There is no ARM type for an agent definition.
output projectEndpoint string = 'https://${aiServicesName}.services.ai.azure.com/api/projects/${projectName}'
output operationsProjectId string = operationsProject.id
output operationsProjectName string = operationsProject.name
output operationsProjectEndpoint string = 'https://${aiServicesName}.services.ai.azure.com/api/projects/${operationsProjectName}'
output procedureIndexName string = 'novasteel-procedures'
output knowledgeBaseName string = 'novasteel-procedures-kb'
output agentServiceReady bool = agentServiceManuallyValidated
