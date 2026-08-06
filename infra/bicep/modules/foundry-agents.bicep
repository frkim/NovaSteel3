// Microsoft Foundry Agent Service — project, BYO ("standard") capability hosts,
// connections and the Application Insights link that makes agent runs observable.
//
// This module is what actually *hosts the NovaSteel agents in Agent Service*. It sits
// on top of the Foundry account created by modules/foundry-speech.bicep and adds:
//
//   1. A Foundry project (`Microsoft.CognitiveServices/accounts/projects`) with a
//      system-assigned identity — the security principal every hosted agent runs as.
//   2. Project connections to the three BYO data resources required by *standard*
//      agent setup: Azure AI Search (vector store), Cosmos DB (thread storage) and a
//      Storage account (file uploads). All three use `authType: 'AAD'` — no keys.
//   3. An account-level connection of category `AppInsights`, which is what makes the
//      Foundry portal's Tracing/Monitoring views and continuous evaluation work: the
//      Agent Service exports OpenTelemetry GenAI spans to that component.
//
// The capability hosts — the step that actually switches Agent Service on — live in
// modules/foundry-agent-capability-host.bicep instead, because the project identity
// must already hold its Cosmos/Storage/Search roles before the platform will
// provision its `enterprise_memory` database and blob containers. main.bicep chains
// this module -> foundry-agent-rbac -> foundry-agent-capability-host in that order.
//
// Why standard (BYO) rather than basic (Microsoft-managed) setup: NovaSteel must be
// able to physically erase an operator's conversation history on a GDPR request
// (knowledge_orchestrator/erasure.py) and must keep interview-derived content inside
// the environment's region. Neither is possible when threads live in Microsoft-managed
// multi-tenant storage.
//
// NOT provisioned here: the agent *definitions* themselves. There is no ARM resource
// type for a Foundry agent — agents, threads and runs are data-plane objects created
// through the Foundry project endpoint. The knowledge-orchestrator does that at
// startup (see `knowledge_orchestrator/agent_service.py`), which is also why this
// module outputs `projectEndpoint`.
targetScope = 'resourceGroup'

@description('Environment short name.')
param environment string

@description('Azure region. Must match the Foundry account region.')
param location string

@description('Common resource tags.')
param tags object

@description('Name of the existing Foundry (AIServices) account created by modules/foundry-speech.bicep.')
param foundryAccountName string

@description('Name of the existing Azure AI Search service that stores the approved procedures.')
param searchServiceName string

@description('Resource ID of the existing Azure AI Search service.')
param searchServiceId string

@description('Name of the existing Cosmos DB account used for agent thread storage.')
param cosmosAccountName string

@description('Resource ID of the existing Cosmos DB account.')
param cosmosAccountId string

@description('Document endpoint of the existing Cosmos DB account.')
param cosmosDocumentEndpoint string

@description('Name of the existing storage account used for agent file uploads.')
param agentStorageAccountName string

@description('Resource ID of the existing agent storage account.')
param agentStorageAccountId string

@description('Blob endpoint of the existing agent storage account.')
param agentStorageBlobEndpoint string

@description('Resource ID of the Application Insights component that receives agent traces.')
param appInsightsId string

var projectName = 'proj-novasteel-${environment}'
var searchConnectionName = 'conn-${searchServiceName}'
var cosmosConnectionName = 'conn-${cosmosAccountName}'
var storageConnectionName = 'conn-${agentStorageAccountName}'

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: foundryAccountName
}

resource searchService 'Microsoft.Search/searchServices@2025-05-01' existing = {
  name: searchServiceName
}

// --- Project ---------------------------------------------------------------

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: foundryAccount
  name: projectName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'NovaSteel ${environment}'
    description: 'Hosts the whole NovaSteel agent roster: the knowledge-capture, procedure and Copilot chat agents, and the tool-calling operations agents whose function tools call the audited deterministic services (ADR-006, ADR-007).'
  }
}

// --- BYO connections (standard agent setup) --------------------------------
// The capability host references these by NAME, so the names below are a contract.

resource searchConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: project
  name: searchConnectionName
  properties: {
    category: 'CognitiveSearch'
    target: 'https://${searchServiceName}.search.windows.net'
    authType: 'AAD'
    metadata: {
      ApiType: 'Azure'
      ResourceId: searchServiceId
      location: location
    }
  }
}

resource cosmosConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: project
  name: cosmosConnectionName
  properties: {
    category: 'CosmosDB'
    target: cosmosDocumentEndpoint
    authType: 'AAD'
    metadata: {
      ApiType: 'Azure'
      ResourceId: cosmosAccountId
      location: location
    }
  }
}

resource storageConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: project
  name: storageConnectionName
  properties: {
    category: 'AzureStorageAccount'
    target: agentStorageBlobEndpoint
    authType: 'AAD'
    metadata: {
      ApiType: 'Azure'
      ResourceId: agentStorageAccountId
      location: location
    }
  }
}

// --- Observability: Application Insights ------------------------------------
// Account-scoped and shared to every project, so agent traces from any project in
// this account land in the same workspace as the Container Apps telemetry. This is
// what lights up the Foundry portal Tracing/Monitoring tabs.
//
// `ProjectManagedIdentity`, not `ApiKey`. The service accepts only those two, and
// `ApiKey` makes the platform persist the connection string through its credential
// service, which requires an associated Key Vault; on a keyless account that has
// none the request fails with an opaque HTTP 500. Managed identity stores no
// secret at all, which is both the working path and the better posture.
resource appInsightsConnection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = {
  parent: foundryAccount
  name: 'conn-appinsights-${environment}'
  properties: {
    category: 'AppInsights'
    target: appInsightsId
    // The ARM enum has not caught up; the service accepts (and requires) this value.
    #disable-next-line BCP036
    authType: 'ProjectManagedIdentity'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: appInsightsId
    }
  }
}

// --- RBAC for the project identity ------------------------------------------
// Search: the Agent Service needs both data-plane write (vector store) and
// service-level access (to create/read the indexes it manages).

resource searchIndexDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: searchService
  name: guid(searchServiceId, project.id, '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
  properties: {
    principalId: project.identity.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
    principalType: 'ServicePrincipal'
  }
}

resource searchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: searchService
  name: guid(searchServiceId, project.id, '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
  properties: {
    principalId: project.identity.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
    principalType: 'ServicePrincipal'
  }
}

// Application Insights reader roles for the project identity are granted by
// modules/appinsights-agent-access.bicep — Application Insights lives in
// rg-ns-<env>-monitoring, and a resource-group-scoped module cannot assign roles
// outside its own scope.

output projectName string = project.name
output projectId string = project.id
@description('Object ID of the project managed identity. Grant it Cosmos DB Operator and Storage Blob Data Owner from the modules that own those resources.')
output projectPrincipalId string = project.identity.principalId
@description('Internal workspace ID of the project, used to scope the container-level storage role assignments Agent Service needs.')
#disable-next-line BCP053
output projectWorkspaceId string = project.properties.internalId
@description('Data-plane endpoint the knowledge-orchestrator uses to create and run agents. There is no ARM resource for an agent — this endpoint is how they are created.')
output projectEndpoint string = 'https://${foundryAccountName}.services.ai.azure.com/api/projects/${projectName}'
output searchConnectionName string = searchConnectionName
output cosmosConnectionName string = cosmosConnectionName
output storageConnectionName string = storageConnectionName
