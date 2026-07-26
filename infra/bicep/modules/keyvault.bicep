// One Key Vault per environment per bounded context (security-governance-and-threat-model.md §5:
// "One Key Vault per environment per bounded context ... not one shared vault"). Call this module
// once for the platform vault and once for the OT-gateway vault. RBAC-only (no access policies),
// private endpoint only, soft-delete + purge-protection mandatory, public network access disabled.
targetScope = 'resourceGroup'

@description('Key Vault name, e.g. kv-ns-<env>-platform or kv-ns-<env>-otgw. Must be globally unique <=24 chars.')
@maxLength(24)
param name string

@description('Azure region.')
param location string

@description('Common resource tags.')
param tags object

@description('Subnet resource ID hosting the private endpoint (typically the ai or apps spoke subnet).')
param privateEndpointSubnetId string

@description('Private DNS zone resource ID for privatelink.vaultcore.azure.net.')
param privateDnsZoneId string

@description('Log Analytics workspace resource ID for AuditEvent diagnostic logs.')
param logAnalyticsWorkspaceId string

@description('Array of { principalId, roleDefinitionId, principalType } objects to grant on this vault (e.g. Key Vault Secrets User for each service managed identity).')
param roleAssignments array = []

@description('Enable customer-managed key support (soft-delete + purge protection are always on regardless of this flag).')
param enablePurgeProtection bool = true

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: enablePurgeProtection
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}

resource kvRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for ra in roleAssignments: {
    name: guid(vault.id, ra.principalId, ra.roleDefinitionId)
    scope: vault
    properties: {
      principalId: ra.principalId
      roleDefinitionId: ra.roleDefinitionId
      principalType: ra.?principalType ?? 'ServicePrincipal'
    }
  }
]

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-${name}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-${name}-connection'
        properties: {
          privateLinkServiceId: vault.id
          groupIds: [
            'vault'
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
        name: 'privatelink-vaultcore-azure-net'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: vault
  name: 'diag-log-analytics'
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        categoryGroup: 'audit'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

output vaultId string = vault.id
output vaultName string = vault.name
output vaultUri string = vault.properties.?vaultUri ?? ''
