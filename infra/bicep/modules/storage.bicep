// Storage account for permitted audio/fallback artifacts (solution-architecture.md §8.2,
// deployment-topology.md §2.2). Call this module twice per environment:
//   1. st-ns-<env>-audio<region>    — Highly Confidential operator-interview audio/transcript
//      store; no cross-region replication without DPO approval; CMK-eligible.
//   2. st-ns-<env>-fallback<region> — DEMO-NONPERSONAL offline demo pack / cached fallback assets.
// Both are private-endpoint-only, RBAC-only (no shared keys for application access), TLS 1.2+.
targetScope = 'resourceGroup'

@description('Storage account name (lowercase, 3-24 chars, globally unique).')
@minLength(3)
@maxLength(24)
param name string

@description('Azure region.')
param location string

@description('Common resource tags.')
param tags object

@description('Data classification tag value for this specific account, e.g. HighlyConfidential or DEMO-NONPERSONAL.')
param dataClassification string

@description('Blob containers to create, e.g. [\'raw-audio\', \'transcripts\'] or [\'fallback-pack\', \'proof-pack\'].')
param containers array

@description('Subnet resource ID hosting the private endpoint.')
param privateEndpointSubnetId string

@description('Private DNS zone resource ID for privatelink.blob.core.windows.net.')
param privateDnsZoneId string

@description('Log Analytics workspace resource ID for diagnostic logs.')
param logAnalyticsWorkspaceId string

@description('Array of { principalId, roleDefinitionId, principalType } objects to grant on this account (e.g. Storage Blob Data Contributor for the owning service identity).')
param roleAssignments array = []

@description('Blob soft-delete/versioning retention in days.')
param blobRetentionDays int = 30

@description('Disable local (shared-key) authentication so only Entra ID/RBAC can access data — matches the "no SAS/keys" rule used elsewhere in this architecture.')
param disableSharedKeyAccess bool = true

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: name
  location: location
  tags: union(tags, {
    dataClassification: dataClassification
  })
  sku: {
    name: 'Standard_GRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: !disableSharedKeyAccess
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
    supportsHttpsTrafficOnly: true
    accessTier: 'Hot'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: blobRetentionDays
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: blobRetentionDays
    }
    isVersioningEnabled: true
    changeFeed: {
      enabled: true
    }
  }
}

resource blobContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [
  for c in containers: {
    parent: blobService
    name: c
    properties: {
      publicAccess: 'None'
    }
  }
]

resource storageRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for ra in roleAssignments: {
    name: guid(storage.id, ra.principalId, ra.roleDefinitionId)
    scope: storage
    properties: {
      principalId: ra.principalId
      roleDefinitionId: ra.roleDefinitionId
      principalType: ra.?principalType ?? 'ServicePrincipal'
    }
  }
]

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-${name}-blob'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-${name}-blob-connection'
        properties: {
          privateLinkServiceId: storage.id
          groupIds: [
            'blob'
          ]
        }
      }
    ]
  }
}

resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'privatelink-blob-core-windows-net'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: blobService
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
        category: 'Transaction'
        enabled: true
      }
    ]
  }
}

output storageAccountId string = storage.id
output storageAccountName string = storage.name
output primaryBlobEndpoint string = storage.properties.?primaryEndpoints.?blob ?? ''
