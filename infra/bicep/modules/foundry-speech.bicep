// Microsoft Foundry (Cognitive Services "AIServices" account) and Azure Speech resource accounts.
// Per research/azure-ai-regions.md: this module provisions ONLY the base Cognitive
// Services/Foundry resource account and Speech account — it does NOT create a Foundry Agent
// Service project/agent, and does NOT assume Agent Service, a specific model deployment, or tool
// availability. Enabling Agent Service is a manual, quota-gated post-deployment step (see
// infra/README.md "Deployment blockers" and the `deployFoundryAgentServiceGate` output below).
targetScope = 'resourceGroup'

@description('Environment short name.')
param environment string

@description('Azure region. Sweden Central primary; West Europe only after a separately approved recovery/data-transfer review (deployment-topology.md §2.2).')
param location string

@description('Common resource tags.')
param tags object

@description('Subnet resource ID hosting private endpoints for Foundry/Speech.')
param privateEndpointSubnetId string

@description('Private DNS zone resource ID for privatelink.cognitiveservices.azure.com.')
param cognitiveServicesPrivateDnsZoneId string

@description('Private DNS zone resource ID for privatelink.openai.azure.com (used by some Foundry model deployment routes).')
param openAiPrivateDnsZoneId string

@description('Log Analytics workspace resource ID for diagnostic logs.')
param logAnalyticsWorkspaceId string

@description('Array of { principalId, roleDefinitionId, principalType } objects granted on the Foundry account (e.g. Cognitive Services User for mi-ns-bff-<env> / mi-ns-worker-<env>).')
param foundryRoleAssignments array = []

@description('Array of { principalId, roleDefinitionId, principalType } objects granted on the Speech account (e.g. Cognitive Services Speech User for mi-ns-knowledge-<env>).')
param speechRoleAssignments array = []

@description('MANUAL/QUOTA GATE: set true only after the deployment validation checklist in research/azure-ai-regions.md has been executed in the target tenant (Agent Service availability, model/tool/quota, Data Zone vs. regional deployment decision). This flag does not itself provision an Agent Service project — Bicep cannot; it only records operator intent for the manual step and gates whether this module even emits a "ready" output.')
param foundryAgentServiceManuallyValidated bool = false

var foundryName = 'aif-novasteel-${environment}-${toLower(replace(location, ' ', ''))}'
var speechName = 'spe-novasteel-${environment}-${toLower(replace(location, ' ', ''))}'

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: foundryName
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: foundryName
    publicNetworkAccess: 'Disabled'
    disableLocalAuth: true
    networkAcls: {
      defaultAction: 'Deny'
    }
  }
}

resource speechAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: speechName
  location: location
  tags: tags
  kind: 'SpeechServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: speechName
    publicNetworkAccess: 'Disabled'
    disableLocalAuth: true
    networkAcls: {
      defaultAction: 'Deny'
    }
  }
}

resource foundryRoleAssignmentResources 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for ra in foundryRoleAssignments: {
    name: guid(foundryAccount.id, ra.principalId, ra.roleDefinitionId)
    scope: foundryAccount
    properties: {
      principalId: ra.principalId
      roleDefinitionId: ra.roleDefinitionId
      principalType: ra.?principalType ?? 'ServicePrincipal'
    }
  }
]

resource speechRoleAssignmentResources 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for ra in speechRoleAssignments: {
    name: guid(speechAccount.id, ra.principalId, ra.roleDefinitionId)
    scope: speechAccount
    properties: {
      principalId: ra.principalId
      roleDefinitionId: ra.roleDefinitionId
      principalType: ra.?principalType ?? 'ServicePrincipal'
    }
  }
]

resource foundryPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-${foundryName}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-${foundryName}-connection'
        properties: {
          privateLinkServiceId: foundryAccount.id
          groupIds: [
            'account'
          ]
        }
      }
    ]
  }
}

resource foundryPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: foundryPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'privatelink-cognitiveservices-azure-com'
        properties: {
          privateDnsZoneId: cognitiveServicesPrivateDnsZoneId
        }
      }
      {
        name: 'privatelink-openai-azure-com'
        properties: {
          privateDnsZoneId: openAiPrivateDnsZoneId
        }
      }
    ]
  }
}

resource speechPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-${speechName}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-${speechName}-connection'
        properties: {
          privateLinkServiceId: speechAccount.id
          groupIds: [
            'account'
          ]
        }
      }
    ]
  }
}

resource speechPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: speechPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'privatelink-cognitiveservices-azure-com'
        properties: {
          privateDnsZoneId: cognitiveServicesPrivateDnsZoneId
        }
      }
    ]
  }
}

resource foundryDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: foundryAccount
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

resource speechDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: speechAccount
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

output foundryAccountId string = foundryAccount.id
output foundryAccountName string = foundryAccount.name
output foundryEndpoint string = foundryAccount.properties.?endpoint ?? ''
output speechAccountId string = speechAccount.id
output speechAccountName string = speechAccount.name
output speechEndpoint string = speechAccount.properties.?endpoint ?? ''
@description('True only when the manual Agent Service validation gate has been recorded as complete. Application deployment automation should treat Agent Service features as unavailable until this is true AND the corresponding tenant-side project/agent has actually been created.')
output foundryAgentServiceGateCleared bool = foundryAgentServiceManuallyValidated
