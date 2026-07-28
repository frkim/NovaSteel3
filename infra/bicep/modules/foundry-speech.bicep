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

// Declared at 2025-04-01-preview rather than 2024-10-01: older API versions do
// not know `allowProjectManagement`, and ARM silently ignores properties it does
// not recognise. At 2024-10-01 this account deploys successfully but the flag
// never takes effect, so project creation later fails with
// "Project can only be created under AIServices Kind account with
// allowProjectManagement set to true." Confirmed against the live control plane.
resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
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
    // Required for Microsoft Foundry projects (and therefore for Agent Service):
    // without it the account cannot host a Microsoft.CognitiveServices/accounts/projects
    // child resource at all. The ARM type definition has not caught up yet.
    #disable-next-line BCP037
    allowProjectManagement: true
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

// --- Model Deployments ------------------------------------------------------
// Three deployments, each with a distinct job:
//   * gpt-5.4-mini  — the workhorse. Backs every hosted Foundry agent (knowledge
//     capture, the procedure agent) and the Copilot chat "default" reasoning tier.
//     A 5-series *mini* is the deliberate choice: it is a reasoning model, so
//     `reasoning_effort` is available, but at a fraction of the cost per token of
//     the full model — and agent turns are high-volume.
//   * gpt-5.5       — the advanced model behind the Copilot chat "high" reasoning
//     tier only. Low volume, high value: multi-step questions where the operator
//     explicitly asked for more thinking.
//   * text-embedding-3-large — vector embeddings for the procedure index in
//     Azure AI Search (integrated vectorization + client-side embedding).
//
// Content Safety is enforced via the RAI policy on each deployment.
// Authentication: managed identity only (disableLocalAuth: true on parent account).
//
// Deployment SKU: GPT-5-series models are NOT offered on the regional `Standard`
// SKU in Sweden Central / West Europe, so `GlobalStandard` is the default. Global
// deployments may process inference in any region hosting the model. Set
// `modelDeploymentSku` to `DataZoneStandard` where the model offers it and the
// EU-data-zone processing boundary is contractually required — verify the exact
// model/version/SKU tuple with `az cognitiveservices account list-models` first
// (see docs/research/azure-ai-regions.md).

@description('Primary (mini) GPT deployment name — used by the hosted Foundry agents and the default Copilot chat tier.')
param gptDeploymentName string = 'gpt-5.4-mini'

@description('Primary GPT model name in the Foundry catalog.')
param gptModelName string = 'gpt-5.4-mini'

@description('Primary GPT model version.')
param gptModelVersion string = '2026-03-17'

@description('Advanced reasoning deployment name — used only by the Copilot chat "high" reasoning tier.')
param reasoningDeploymentName string = 'gpt-5.5'

@description('Advanced reasoning model name in the Foundry catalog.')
param reasoningModelName string = 'gpt-5.5'

@description('Advanced reasoning model version.')
param reasoningModelVersion string = '2026-04-24'

@description('Embedding model deployment name.')
param embeddingDeploymentName string = 'text-embedding-3-large'

@description('Embedding model version.')
param embeddingModelVersion string = '1'

@description('Deployment SKU for the two GPT-5 deployments. See the note above before changing.')
@allowed([
  'GlobalStandard'
  'DataZoneStandard'
  'Standard'
])
param modelDeploymentSku string = 'GlobalStandard'

@description('Tokens-per-minute capacity for the primary (mini) GPT deployment (in thousands).')
param gptCapacity int = 50

@description('Tokens-per-minute capacity for the advanced reasoning deployment (in thousands). Deliberately smaller than the mini deployment: the high tier is opt-in and low-volume.')
param reasoningCapacity int = 20

@description('Tokens-per-minute capacity for embedding deployment (in thousands).')
param embeddingCapacity int = 120

// Model deployments on one Cognitive Services account must be created serially —
// concurrent PUTs against the same account race and fail. The dependsOn chain below
// is load-bearing, not cosmetic.
resource gptDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundryAccount
  name: gptDeploymentName
  sku: {
    name: modelDeploymentSku
    capacity: gptCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: gptModelName
      version: gptModelVersion
    }
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

resource reasoningDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundryAccount
  name: reasoningDeploymentName
  dependsOn: [gptDeployment]
  sku: {
    name: modelDeploymentSku
    capacity: reasoningCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: reasoningModelName
      version: reasoningModelVersion
    }
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundryAccount
  name: embeddingDeploymentName
  dependsOn: [reasoningDeployment]
  sku: {
    name: 'Standard'
    capacity: embeddingCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-large'
      version: embeddingModelVersion
    }
  }
}

output foundryAccountId string = foundryAccount.id
output foundryAccountName string = foundryAccount.name
output foundryEndpoint string = foundryAccount.properties.?endpoint ?? ''
output speechAccountId string = speechAccount.id
output speechAccountName string = speechAccount.name
output speechEndpoint string = speechAccount.properties.?endpoint ?? ''
output gptDeploymentId string = gptDeployment.id
output gptDeploymentModelName string = gptDeploymentName
output reasoningDeploymentId string = reasoningDeployment.id
output reasoningDeploymentModelName string = reasoningDeploymentName
output embeddingDeploymentId string = embeddingDeployment.id
output embeddingDeploymentModelName string = embeddingDeploymentName
@description('True only when the manual Agent Service validation gate has been recorded as complete. Application deployment automation should treat Agent Service features as unavailable until this is true AND the corresponding tenant-side project/agent has actually been created.')
output foundryAgentServiceGateCleared bool = foundryAgentServiceManuallyValidated
