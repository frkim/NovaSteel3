// BYO data-plane RBAC for the Foundry project identity.
//
// Foundry Agent Service ("standard" setup) does not just *read* the Cosmos DB and
// storage account we hand it — at capability-host creation time the platform, acting
// as the project's managed identity, creates its own `enterprise_memory` database,
// its containers, and two blob containers. So these roles must already be in place
// before modules/foundry-agent-capability-host.bicep runs, which is why this is a
// separate module chained between the two in main.bicep rather than folded into
// either of them.
//
// Everything here is granted to a managed identity; no keys are involved and both
// backing accounts keep `disableLocalAuth: true`.
targetScope = 'resourceGroup'

@description('Name of the Cosmos DB account used for agent thread storage.')
param cosmosAccountName string

@description('Name of the storage account used for agent file uploads.')
param agentStorageAccountName string

@description('Object ID of the Foundry project managed identity.')
param projectPrincipalId string

// Control-plane: lets Agent Service create the enterprise_memory database/containers.
var cosmosOperatorRoleId = '230815da-be43-4aae-9cb4-875f7bd000aa'
// Control-plane: lets Agent Service create its two blob containers.
var storageAccountContributorRoleId = '17d1049b-9a84-46fb-8f53-869881c3d3ab'
// Data-plane: read/write of the agent file blobs it then puts in those containers.
var storageBlobDataOwnerRoleId = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
// Cosmos SQL built-in Data Contributor. Not an ARM role — Cosmos has its own
// data-plane role system, assigned through sqlRoleAssignments below.
var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002'

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-12-01-preview' existing = {
  name: cosmosAccountName
}

resource agentStorage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: agentStorageAccountName
}

resource cosmosOperator 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: cosmosAccount
  name: guid(cosmosAccount.id, projectPrincipalId, cosmosOperatorRoleId)
  properties: {
    principalId: projectPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cosmosOperatorRoleId)
    principalType: 'ServicePrincipal'
  }
}

// Account-scoped rather than scoped to the individual enterprise_memory containers.
// The container-scoped form used by the Foundry sample cannot be expressed until the
// capability host has created those containers, which is a chicken-and-egg problem in
// a single deployment; the account is dedicated to agent threads and nothing else, so
// the wider scope does not widen the blast radius in practice.
resource cosmosDataContributor 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-12-01-preview' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, projectPrincipalId, cosmosDataContributorRoleId)
  properties: {
    principalId: projectPrincipalId
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/${cosmosDataContributorRoleId}'
    scope: cosmosAccount.id
  }
}

resource storageContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: agentStorage
  name: guid(agentStorage.id, projectPrincipalId, storageAccountContributorRoleId)
  properties: {
    principalId: projectPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageAccountContributorRoleId)
    principalType: 'ServicePrincipal'
  }
}

resource storageBlobDataOwner 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: agentStorage
  name: guid(agentStorage.id, projectPrincipalId, storageBlobDataOwnerRoleId)
  properties: {
    principalId: projectPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataOwnerRoleId)
    principalType: 'ServicePrincipal'
  }
}

@description('Emitted so the capability-host module can take a dependency on this module completing.')
output rbacComplete bool = true
