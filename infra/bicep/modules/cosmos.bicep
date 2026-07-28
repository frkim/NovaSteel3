// Azure Cosmos DB for NoSQL — agent thread storage for the Foundry Agent Service project.
//
// Foundry Agent Service "standard setup" stores agent definitions and conversation
// threads in a customer-owned Cosmos DB account rather than in Microsoft-managed
// multi-tenant storage. NovaSteel requires the customer-owned variant for two
// independent reasons:
//   1. GDPR erasure (services/knowledge-orchestrator/src/knowledge_orchestrator/erasure.py):
//      an erasure request must be able to physically delete an operator's conversation
//      history. That is only possible when the thread store is ours.
//   2. Data residency: the account is pinned to the environment region and reachable
//      only through a private endpoint, so thread content never leaves the VNet.
//
// The Agent Service creates its own `enterprise_memory` database and containers inside
// this account at capability-host creation time — do NOT pre-create them here.
targetScope = 'resourceGroup'

@description('Environment short name.')
param environment string

@description('Azure region. Must match the Foundry account region.')
param location string

@description('Common resource tags.')
param tags object

@description('Subnet resource ID hosting the private endpoint.')
param privateEndpointSubnetId string

@description('Private DNS zone resource ID for privatelink.documents.azure.com.')
param cosmosPrivateDnsZoneId string

@description('Log Analytics workspace resource ID for diagnostic logs.')
param logAnalyticsWorkspaceId string

@description('Enable zone redundancy for the write region. Production only — it raises cost and is not available in every region.')
param zoneRedundant bool = false

@description('Array of { principalId, roleDefinitionId, principalType } objects granted control-plane roles on the account (e.g. Cosmos DB Operator for the Foundry project identity).')
param roleAssignments array = []

var cosmosName = 'cosmos-novasteel-${environment}-${toLower(replace(location, ' ', ''))}'

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-12-01-preview' = {
  name: cosmosName
  location: location
  tags: union(tags, {
    dataClassification: 'Confidential'
  })
  kind: 'GlobalDocumentDB'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    databaseAccountOfferType: 'Standard'
    // Entra-only: the Agent Service and the orchestrator both authenticate with a
    // managed identity, so account keys are switched off entirely.
    disableLocalAuth: true
    disableKeyBasedMetadataWriteAccess: true
    publicNetworkAccess: 'Disabled'
    minimalTlsVersion: 'Tls12'
    isVirtualNetworkFilterEnabled: false
    enableAutomaticFailover: false
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    capabilities: []
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: zoneRedundant
      }
    ]
    backupPolicy: {
      type: 'Continuous'
      continuousModeProperties: {
        tier: 'Continuous7Days'
      }
    }
  }
}

resource cosmosRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for ra in roleAssignments: {
    name: guid(cosmosAccount.id, ra.principalId, ra.roleDefinitionId)
    scope: cosmosAccount
    properties: {
      principalId: ra.principalId
      roleDefinitionId: ra.roleDefinitionId
      principalType: ra.?principalType ?? 'ServicePrincipal'
    }
  }
]

resource cosmosPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-${cosmosName}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-${cosmosName}-connection'
        properties: {
          privateLinkServiceId: cosmosAccount.id
          groupIds: [
            'Sql'
          ]
        }
      }
    ]
  }
}

resource cosmosPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: cosmosPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'privatelink-documents-azure-com'
        properties: {
          privateDnsZoneId: cosmosPrivateDnsZoneId
        }
      }
    ]
  }
}

resource cosmosDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: cosmosAccount
  name: 'diag-log-analytics'
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'Requests'
        enabled: true
      }
    ]
  }
}

output cosmosAccountId string = cosmosAccount.id
output cosmosAccountName string = cosmosAccount.name
output cosmosDocumentEndpoint string = cosmosAccount.properties.documentEndpoint
