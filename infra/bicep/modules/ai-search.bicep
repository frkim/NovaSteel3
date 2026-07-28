// Azure AI Search — the system of record for APPROVED NovaSteel procedures.
//
// The knowledge-orchestrator writes only APPROVED procedures into the
// `novasteel-procedures` index (api-contracts §10.2); drafts are unreachable by
// construction because they are never indexed. The index is also the knowledge
// source behind the Foundry IQ knowledge base that the procedure agent queries
// (see modules/foundry-speech.bicep), so this service is a hard dependency of
// the Agent Service project and is deployed into the same AI resource group.
//
// Security posture matches every other data plane in this repository
// (security-governance-and-threat-model.md §4.1, §8):
//   * `disableLocalAuth: true` — admin/query API keys cannot be used at all, so
//     Entra ID + managed identity is the only authentication path. This is also
//     why `authOptions` is never set: the two are mutually exclusive.
//   * `publicNetworkAccess: 'Disabled'` + a private endpoint into the AI subnet.
//   * System-assigned identity so the service can call the Foundry embedding
//     deployment for integrated vectorization without a key.
targetScope = 'resourceGroup'

@description('Environment short name.')
param environment string

@description('Azure region. Must match the Foundry account region so the Agent Service project connection and integrated vectorization stay in-region (deployment-topology.md §2.2).')
param location string

@description('Common resource tags.')
param tags object

@description('Subnet resource ID hosting the private endpoint for Azure AI Search.')
param privateEndpointSubnetId string

@description('Private DNS zone resource ID for privatelink.search.windows.net.')
param searchPrivateDnsZoneId string

@description('Log Analytics workspace resource ID for diagnostic logs.')
param logAnalyticsWorkspaceId string

@description('Search SKU. `basic` is the cost-conscious default and is the lowest tier that supports private endpoints; `standard` adds semantic ranker capacity headroom for prod.')
@allowed([
  'basic'
  'standard'
  'standard2'
])
param skuName string = 'basic'

@description('Replica count. Keep 1 for non-prod; >= 2 is required for a read SLA.')
@minValue(1)
@maxValue(3)
param replicaCount int = 1

@description('Partition count. The approved-procedure corpus is small, so 1 partition is sufficient.')
@minValue(1)
@maxValue(3)
param partitionCount int = 1

@description('Semantic ranker tier. `standard` is required for the semantic reranking used by hybrid procedure retrieval and by the Foundry IQ knowledge base; `free` caps queries and is only for dev.')
@allowed([
  'free'
  'standard'
])
param semanticSearchTier string = 'standard'

@description('Array of { principalId, roleDefinitionId, principalType } objects granted on the search service (e.g. Search Index Data Contributor for mi-ns-knowledge-<env>, Search Index Data Reader for mi-ns-bff-<env>).')
param roleAssignments array = []

var searchName = 'srch-novasteel-${environment}-${toLower(replace(location, ' ', ''))}'

resource searchService 'Microsoft.Search/searchServices@2025-05-01' = {
  name: searchName
  location: location
  tags: tags
  sku: {
    name: skuName
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: replicaCount
    partitionCount: partitionCount
    hostingMode: 'Default'
    // Entra-only. `authOptions` must stay unset while this is true.
    disableLocalAuth: true
    publicNetworkAccess: 'Disabled'
    networkRuleSet: {
      ipRules: []
    }
    semanticSearch: semanticSearchTier
  }
}

resource searchRoleAssignmentResources 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for ra in roleAssignments: {
    name: guid(searchService.id, ra.principalId, ra.roleDefinitionId)
    scope: searchService
    properties: {
      principalId: ra.principalId
      roleDefinitionId: ra.roleDefinitionId
      principalType: ra.?principalType ?? 'ServicePrincipal'
    }
  }
]

resource searchPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-${searchName}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-${searchName}-connection'
        properties: {
          privateLinkServiceId: searchService.id
          groupIds: [
            'searchService'
          ]
        }
      }
    ]
  }
}

resource searchPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: searchPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'privatelink-search-windows-net'
        properties: {
          privateDnsZoneId: searchPrivateDnsZoneId
        }
      }
    ]
  }
}

resource searchDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: searchService
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
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

output searchServiceId string = searchService.id
output searchServiceName string = searchService.name
output searchEndpoint string = 'https://${searchName}.search.windows.net'
@description('System-assigned principal of the search service — grant it Cognitive Services OpenAI User on the Foundry account so integrated vectorization can call the embedding deployment without a key.')
output searchPrincipalId string = searchService.identity.principalId
@description('Name of the index the knowledge-orchestrator creates and maintains at the data plane. Bicep cannot create indexes (they are a data-plane artifact), so this is the agreed contract between infrastructure and application code.')
output procedureIndexName string = 'novasteel-procedures'
@description('Name of the Foundry IQ knowledge base built over the procedure index. Like the index, it is a Search data-plane object created by the orchestrator; the procedure agent attaches to it through its MCP endpoint.')
output knowledgeBaseName string = 'novasteel-procedures-kb'
