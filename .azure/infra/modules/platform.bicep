targetScope = 'resourceGroup'

param location string

@minLength(1)
param resourcePrefix string

@minLength(1)
param nameSuffix string
param tags object
param fabricAdministrator string
param fabricCapacityLifecycleRoleDefinitionId string
param deployAiServices bool

@description('Create the GPT-5-series chat/reasoning and embedding model deployments on the AI Services account. Kept separate from deployAiServices because model availability and quota must be reconfirmed in Sweden Central before the first deployment attempt.')
param deployModelDeployments bool = false

@description('Chat/extraction deployment. A 5-series mini model: fast and cheap enough for ordinary turns.')
param chatModelName string = 'gpt-5.4-mini'

param chatModelVersion string = '2026-03-17'

@description('High-reasoning deployment used by the Copilot chat "high" tier.')
param reasoningModelName string = 'gpt-5.5'

param reasoningModelVersion string = '2026-04-24'

param embeddingModelName string = 'text-embedding-3-large'

param embeddingModelVersion string = '1'

@description('Neither GPT-5-series model is offered on regional Standard in Sweden Central, so GlobalStandard is the default. DataZoneStandard is the escape hatch when policy requires EU-zone-bounded inference.')
@allowed([
  'GlobalStandard'
  'DataZoneStandard'
])
param modelDeploymentSku string = 'GlobalStandard'

@description('Thousands of tokens per minute for each deployment. Deliberately small for a cost-capped demo estate.')
param chatCapacity int = 30
param reasoningCapacity int = 10
param embeddingCapacity int = 30

var acrName = '${resourcePrefix}acr${nameSuffix}'
var containerAppsEnvironmentName = '${resourcePrefix}-cae'
var portalIdentityName = '${resourcePrefix}-portal-mi'
var bffIdentityName = '${resourcePrefix}-bff-mi'
// Fabric capacity names accept only alphanumeric characters.
var fabricCapacityName = '${resourcePrefix}fabric'
var capacityPauseLogicAppName = '${resourcePrefix}-capacity-pause'
var eventHubsNamespaceName = '${resourcePrefix}-eh-${nameSuffix}'
var telemetryEventHubName = 'telemetry'
var storageAccountName = '${resourcePrefix}st${nameSuffix}'
var keyVaultName = '${resourcePrefix}-kv-${nameSuffix}'
var logAnalyticsWorkspaceName = '${resourcePrefix}-law'
var appInsightsName = '${resourcePrefix}-appi'
var aiServicesName = '${resourcePrefix}-ai-${nameSuffix}'
var speechName = '${resourcePrefix}-speech-${nameSuffix}'

var acrPullRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
var keyVaultSecretsUserRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
var storageBlobDataContributorRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
var eventHubsDataSenderRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2b629674-e913-4c01-ae53-ef4638d8f975')
var cognitiveServicesUserRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
var cognitiveServicesSpeechUserRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'f2dc8367-1007-4938-bd23-fe263f013447')

resource portalIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: portalIdentityName
  location: location
  tags: tags
}

resource bffIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: bffIdentityName
  location: location
  tags: tags
}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    workspaceCapping: {
      dailyQuotaGb: 1
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    IngestionMode: 'LogAnalytics'
    DisableIpMasking: false
  }
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
  }
}

resource portalAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, portalIdentity.id, acrPullRoleDefinitionId)
  scope: containerRegistry
  properties: {
    principalId: portalIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrPullRoleDefinitionId
  }
}

resource bffAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, bffIdentity.id, acrPullRoleDefinitionId)
  scope: containerRegistry
  properties: {
    principalId: bffIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrPullRoleDefinitionId
  }
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppsEnvironmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
    zoneRedundant: false
  }
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    publicNetworkAccess: 'Enabled'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    isVersioningEnabled: false
  }
}

resource demoArtifactsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'demo-artifacts'
  properties: {
    publicAccess: 'None'
  }
}

resource bffStorageBlobDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(demoArtifactsContainer.id, bffIdentity.id, storageBlobDataContributorRoleDefinitionId)
  scope: demoArtifactsContainer
  properties: {
    principalId: bffIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: storageBlobDataContributorRoleDefinitionId
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
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
    softDeleteRetentionInDays: 7
    enablePurgeProtection: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

resource bffKeyVaultSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, bffIdentity.id, keyVaultSecretsUserRoleDefinitionId)
  scope: keyVault
  properties: {
    principalId: bffIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: keyVaultSecretsUserRoleDefinitionId
  }
}

resource eventHubsNamespace 'Microsoft.EventHub/namespaces@2024-01-01' = {
  name: eventHubsNamespaceName
  location: location
  tags: tags
  sku: {
    name: 'Standard'
    tier: 'Standard'
    capacity: 1
  }
  properties: {
    disableLocalAuth: true
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    zoneRedundant: false
  }
}

resource telemetryEventHub 'Microsoft.EventHub/namespaces/eventhubs@2024-01-01' = {
  parent: eventHubsNamespace
  name: telemetryEventHubName
  properties: {
    messageRetentionInDays: 1
    partitionCount: 1
  }
}

resource bffEventHubsDataSender 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(telemetryEventHub.id, bffIdentity.id, eventHubsDataSenderRoleDefinitionId)
  scope: telemetryEventHub
  properties: {
    principalId: bffIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: eventHubsDataSenderRoleDefinitionId
  }
}

resource fabricCapacity 'Microsoft.Fabric/capacities@2023-11-01' = {
  name: fabricCapacityName
  location: location
  tags: tags
  sku: {
    name: 'F2'
    tier: 'Fabric'
  }
  properties: {
    administration: {
      members: [
        fabricAdministrator
        bffIdentity.properties.principalId
      ]
    }
  }
}

var fabricSuspendUrl = '${az.environment().resourceManager}${fabricCapacity.id}/suspend?api-version=2023-11-01'

resource capacityPauseLogicApp 'Microsoft.Logic/workflows@2019-05-01' = {
  name: capacityPauseLogicAppName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    state: 'Enabled'
    definition: {
      '$schema': 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#'
      contentVersion: '1.0.0.0'
      parameters: {}
      triggers: {
        Daily_at_0100_Europe_Luxembourg: {
          type: 'Recurrence'
          recurrence: {
            frequency: 'Day'
            interval: 1
            timeZone: 'W. Europe Standard Time'
            schedule: {
              hours: [
                1
              ]
              minutes: [
                0
              ]
            }
          }
        }
      }
      actions: {
        Pause_Fabric_capacity: {
          type: 'Http'
          inputs: {
            method: 'POST'
            uri: fabricSuspendUrl
            authentication: {
              type: 'ManagedServiceIdentity'
              audience: az.environment().resourceManager
            }
          }
          runAfter: {}
        }
      }
      outputs: {}
    }
  }
}

resource logicAppFabricCapacityLifecycleOperator 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(fabricCapacity.id, capacityPauseLogicApp.id, fabricCapacityLifecycleRoleDefinitionId)
  scope: fabricCapacity
  properties: {
    principalId: capacityPauseLogicApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: fabricCapacityLifecycleRoleDefinitionId
  }
}

// The account is declared at 2025-04-01-preview, not 2024-10-01: older API
// versions do not know `allowProjectManagement` and ARM silently drops unknown
// properties, so the account would deploy successfully but never become able to
// host a Foundry project.
resource aiServices 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = if (deployAiServices) {
  name: aiServicesName
  location: location
  // `SecurityControl: Ignore` is applied by a subscription-scoped Modify policy
  // (`Add SecurityControl=Ignore tag`), not by hand. Reapplied here so a redeploy
  // manages tags declaratively without reporting the policy's tag as drift.
  tags: union(tags, {
    SecurityControl: 'Ignore'
  })
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  // The account-level Agents capability host requires the account to have an
  // identity of its own; without it the capability host fails to provision.
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: aiServicesName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
    // Required before the account can host a Foundry project (and therefore Agent
    // Service). The ARM type definition lags the service, so Bicep does not yet
    // know this property exists.
    #disable-next-line BCP037
    allowProjectManagement: true
  }
}

// Model deployments are serial: the Cognitive Services control plane rejects
// concurrent deployment writes against the same account with a 409, and Bicep
// otherwise fans these out in parallel.
resource chatDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (deployAiServices && deployModelDeployments) {
  parent: aiServices
  name: chatModelName
  sku: {
    name: modelDeploymentSku
    capacity: chatCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: chatModelName
      version: chatModelVersion
    }
    versionUpgradeOption: 'NoAutoUpgrade'
  }
}

resource reasoningDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (deployAiServices && deployModelDeployments) {
  parent: aiServices
  name: reasoningModelName
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
    versionUpgradeOption: 'NoAutoUpgrade'
  }
  dependsOn: [
    chatDeployment
  ]
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (deployAiServices && deployModelDeployments) {
  parent: aiServices
  name: embeddingModelName
  sku: {
    name: 'Standard'
    capacity: embeddingCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: embeddingModelName
      version: embeddingModelVersion
    }
    versionUpgradeOption: 'NoAutoUpgrade'
  }
  dependsOn: [
    reasoningDeployment
  ]
}

resource speech 'Microsoft.CognitiveServices/accounts@2024-10-01' = if (deployAiServices) {
  name: speechName
  location: location
  // Same policy-applied tag as the AI Services account above.
  tags: union(tags, {
    SecurityControl: 'Ignore'
  })
  kind: 'SpeechServices'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: speechName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
  }
}

resource bffAiServicesUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployAiServices) {
  name: guid(aiServices.id, bffIdentity.id, cognitiveServicesUserRoleDefinitionId)
  scope: aiServices
  properties: {
    principalId: bffIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: cognitiveServicesUserRoleDefinitionId
  }
}

resource bffSpeechUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployAiServices) {
  name: guid(speech.id, bffIdentity.id, cognitiveServicesSpeechUserRoleDefinitionId)
  scope: speech
  properties: {
    principalId: bffIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: cognitiveServicesSpeechUserRoleDefinitionId
  }
}

output acrId string = containerRegistry.id
output acrName string = containerRegistry.name
output acrLoginServer string = containerRegistry.properties.loginServer
output containerAppsEnvironmentId string = containerAppsEnvironment.id
output containerAppsEnvironmentName string = containerAppsEnvironment.name
output portalIdentityId string = portalIdentity.id
output portalIdentityName string = portalIdentity.name
output portalIdentityClientId string = portalIdentity.properties.clientId
output bffIdentityId string = bffIdentity.id
output bffIdentityName string = bffIdentity.name
output bffIdentityClientId string = bffIdentity.properties.clientId
output bffIdentityPrincipalId string = bffIdentity.properties.principalId
output fabricCapacityId string = fabricCapacity.id
output fabricCapacityName string = fabricCapacity.name
output capacityPauseLogicAppId string = capacityPauseLogicApp.id
output capacityPauseLogicAppName string = capacityPauseLogicApp.name
output eventHubsNamespaceId string = eventHubsNamespace.id
output eventHubsNamespaceName string = eventHubsNamespace.name
output eventHubsHostName string = '${eventHubsNamespace.name}.servicebus.windows.net'
output telemetryEventHubId string = telemetryEventHub.id
output telemetryEventHubName string = telemetryEventHub.name
output storageAccountId string = storageAccount.id
output storageAccountName string = storageAccount.name
output storageBlobEndpoint string = storageAccount.properties.?primaryEndpoints.?blob ?? ''
output keyVaultId string = keyVault.id
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.?vaultUri ?? ''
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id
output logAnalyticsWorkspaceName string = logAnalyticsWorkspace.name
output appInsightsId string = applicationInsights.id
output appInsightsName string = applicationInsights.name
output aiServicesId string = deployAiServices ? (aiServices.?id ?? '') : ''
output aiServicesName string = deployAiServices ? (aiServices.?name ?? '') : ''
@description('Foundry-model account endpoint. Deliberately NOT `properties.endpoint`, which returns the legacy `<name>.cognitiveservices.azure.com` host from the classic Azure OpenAI surface: the Foundry project model is served from `<name>.services.ai.azure.com`, the host that carries both the project endpoint and the versionless OpenAI v1 inference route.')
output aiServicesEndpoint string = deployAiServices ? 'https://${aiServicesName}.services.ai.azure.com' : ''
@description('Legacy Azure OpenAI-compatible endpoint. Diagnostics only — application configuration uses `aiServicesEndpoint`.')
output aiServicesLegacyOpenAiEndpoint string = deployAiServices ? (aiServices.?properties.?endpoint ?? '') : ''
output chatDeploymentName string = deployAiServices && deployModelDeployments ? chatModelName : ''
output reasoningDeploymentName string = deployAiServices && deployModelDeployments ? reasoningModelName : ''
output embeddingDeploymentName string = deployAiServices && deployModelDeployments ? embeddingModelName : ''
output speechId string = deployAiServices ? (speech.?id ?? '') : ''
output speechName string = deployAiServices ? (speech.?name ?? '') : ''
output speechEndpoint string = deployAiServices ? (speech.?properties.?endpoint ?? '') : ''
