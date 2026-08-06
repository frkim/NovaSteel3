targetScope = 'subscription'

@description('The approved Azure region for the isolated NovaSteel v3 demo.')
@allowed([
  'swedencentral'
])
param location string = 'swedencentral'

@description('The only resource group this deployment is allowed to create or update.')
@allowed([
  'rg-novasteelv3-demo-sc'
])
param resourceGroupName string = 'rg-novasteelv3-demo-sc'

@description('Required prefix for resources where Azure naming rules permit it.')
@allowed([
  'novasteelv3'
])
param resourcePrefix string = 'novasteelv3'

@description('Owner tag applied to every taggable demo resource.')
param owner string = 'frkim@microsoft.com'

@description('Cost-center tag applied to every taggable demo resource.')
param costCenter string = 'novasteel-demo'

@description('Expiry tag for this non-production estate (yyyy-MM-dd).')
param expiryDate string = '2026-12-31'

@description('Fabric capacity administrator UPN required by the Microsoft.Fabric ARM resource.')
param fabricAdministrator string = 'dd0e874e-c9d8-494f-b7ac-3a182952e628'

@description('Create Container Apps only after immutable portal and BFF images are present in the new ACR.')
param deployApps bool = false

@description('Full immutable portal image reference. This is ignored while deployApps is false.')
param portalImage string

@description('Full immutable BFF image reference. This is ignored while deployApps is false.')
param bffImage string

@description('HTTPS portal origin permitted by the BFF CORS allowlist. The app phase replaces the bootstrap placeholder with the deployed portal URL.')
param portalOrigin string = 'https://placeholder.invalid'

@description('HTTPS BFF base URL exposed to the portal container runtime. The app phase replaces the bootstrap placeholder with the deployed BFF URL.')
param portalBffBaseUrl string = 'https://placeholder.invalid'

@description('Full immutable operator-capture PWA image reference. Empty skips the capture Container App, keeping the estate deployable before that image exists.')
param captureImage string = ''

@description('HTTPS origin of the deployed capture PWA, added to the BFF CORS allowlist. The app phase replaces this with the deployed capture URL.')
param captureOrigin string = ''

@description('HTTPS BFF base URL injected into the capture PWA at container start.')
param captureBffBaseUrl string = ''

@description('Create the base Azure AI Services and Speech S0 accounts only after their Sweden Central availability has been reconfirmed.')
param deployAiServices bool = false

@description('Create the GPT-5-series chat/reasoning and embedding model deployments. Separate from deployAiServices because model availability and quota must be reconfirmed in Sweden Central first. Without these the Copilot and knowledge features run on offline fixtures.')
param deployModelDeployments bool = false

@description('Create Azure AI Search, Cosmos DB agent-thread storage and the Foundry project. AI Search bills a fixed monthly amount whether or not it is queried, so this stays opt-in for a cost-capped demo estate.')
param deployAgentPlatform bool = false

@description('Create the Agent Service capability hosts. A capability host is IMMUTABLE — it cannot later be repointed at different Search/Cosmos/Storage accounts. Leave false until those three are final.')
param agentServiceManuallyValidated bool = false

@description('Online-search backend for Copilot chat. Web IQ and web search are First Party Consumption Services: the Microsoft DPA does not apply and queries leave the Azure compliance boundary, so anything other than offline needs DPO sign-off.')
@allowed([
  'offline'
  'web_iq'
  'web_search'
])
param onlineSearchMode string = 'offline'

@description('Create the optional resource-group budget and notifications. Disabled until an owner validates the monthly amount.')
param deployBudget bool = false

@minValue(1)
@description('Monthly budget amount used only when deployBudget is true. It is a guardrail, not a pricing estimate.')
param monthlyBudgetAmount int = 250

@description('First day of the budget period in UTC.')
param budgetStartDate string = '2026-08-01T00:00:00Z'

@description('Email recipients for optional budget alerts.')
param budgetContactEmails array = [
  'frkim@microsoft.com'
]

var nameSuffix = substring(uniqueString(subscription().id, resourceGroupName), 0, 8)
var portalAppName = '${resourcePrefix}-portal'
var bffAppName = '${resourcePrefix}-bff'
var captureAppName = '${resourcePrefix}-capture'
var commonTags = {
  application: 'NovaSteel v3'
  environment: 'demo'
  owner: owner
  costCenter: costCenter
  expiry: expiryDate
  managedBy: 'bicep'
  dataClassification: 'synthetic-demo'
}

resource demoResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: commonTags
}

// This custom role is subscription-scoped because role definitions must be created above
// the resource scope where they are assigned. Its assignable scope is limited to this demo RG.
resource fabricCapacityLifecycleRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: guid(subscription().id, 'novasteelv3-fabric-capacity-lifecycle-operator')
  properties: {
    roleName: 'NovaSteel v3 Fabric Capacity Pause Operator'
    description: 'Suspend the isolated NovaSteel v3 demo Fabric capacity.'
    type: 'CustomRole'
    permissions: [
      {
        actions: [
          'Microsoft.Fabric/capacities/suspend/action'
        ]
        notActions: []
        dataActions: []
        notDataActions: []
      }
    ]
    assignableScopes: [
      demoResourceGroup.id
    ]
  }
}

module platform './modules/platform.bicep' = {
  name: '${resourcePrefix}-platform'
  scope: demoResourceGroup
  params: {
    location: location
    resourcePrefix: resourcePrefix
    nameSuffix: nameSuffix
    tags: commonTags
    fabricAdministrator: fabricAdministrator
    fabricCapacityLifecycleRoleDefinitionId: fabricCapacityLifecycleRole.id
    deployAiServices: deployAiServices
    deployModelDeployments: deployModelDeployments
  }
}

// Requires deployAiServices: the project is a child of the AIServices account and
// the search service needs the embedding deployment for integrated vectorization.
module agentPlatform './modules/agent-platform.bicep' = if (deployAiServices && deployAgentPlatform) {
  name: '${resourcePrefix}-agents'
  scope: demoResourceGroup
  params: {
    location: location
    resourcePrefix: resourcePrefix
    nameSuffix: nameSuffix
    tags: commonTags
    aiServicesName: platform.outputs.aiServicesName
    storageAccountName: platform.outputs.storageAccountName
    appInsightsName: platform.outputs.appInsightsName
    agentServiceManuallyValidated: agentServiceManuallyValidated
    bffPrincipalId: platform.outputs.bffIdentityPrincipalId
  }
}

module apps './modules/apps.bicep' = if (deployApps) {
  name: '${resourcePrefix}-apps'
  scope: demoResourceGroup
  params: {
    location: location
    resourcePrefix: resourcePrefix
    nameSuffix: nameSuffix
    tags: commonTags
    appInsightsName: '${resourcePrefix}-appi'
    portalImage: portalImage
    bffImage: bffImage
    portalOrigin: portalOrigin
    portalBffBaseUrl: portalBffBaseUrl
    captureImage: captureImage
    captureOrigin: captureOrigin
    captureBffBaseUrl: captureBffBaseUrl
    foundryEndpoint: platform.outputs.aiServicesEndpoint
    foundryChatDeployment: platform.outputs.chatDeploymentName
    foundryReasoningDeployment: platform.outputs.reasoningDeploymentName
    foundryEmbedDeployment: platform.outputs.embeddingDeploymentName
    foundryProjectEndpoint: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?projectEndpoint ?? '') : ''
    searchEndpoint: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?searchEndpoint ?? '') : ''
    searchIndexName: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?procedureIndexName ?? '') : ''
    knowledgeBaseName: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?knowledgeBaseName ?? '') : ''
    onlineSearchMode: onlineSearchMode
  }
}

module budget './modules/budget.bicep' = if (deployBudget) {
  name: '${resourcePrefix}-budget'
  scope: demoResourceGroup
  params: {
    name: '${resourcePrefix}-demo-budget'
    amount: monthlyBudgetAmount
    startDate: budgetStartDate
    contactEmails: budgetContactEmails
  }
}

output resourceGroupId string = demoResourceGroup.id
output resourceGroupNameOutput string = demoResourceGroup.name
output resourceIds object = {
  containerRegistry: platform.outputs.acrId
  containerAppsEnvironment: platform.outputs.containerAppsEnvironmentId
  portalManagedIdentity: platform.outputs.portalIdentityId
  bffManagedIdentity: platform.outputs.bffIdentityId
  portalContainerApp: deployApps ? (apps.?outputs.?portalAppId ?? '') : ''
  bffContainerApp: deployApps ? (apps.?outputs.?bffAppId ?? '') : ''
  captureContainerApp: deployApps ? (apps.?outputs.?captureAppId ?? '') : ''
  fabricCapacity: platform.outputs.fabricCapacityId
  fabricCapacityLifecycleRole: fabricCapacityLifecycleRole.id
  capacityPauseLogicApp: platform.outputs.capacityPauseLogicAppId
  eventHubsNamespace: platform.outputs.eventHubsNamespaceId
  telemetryEventHub: platform.outputs.telemetryEventHubId
  storageAccount: platform.outputs.storageAccountId
  keyVault: platform.outputs.keyVaultId
  logAnalyticsWorkspace: platform.outputs.logAnalyticsWorkspaceId
  applicationInsights: platform.outputs.appInsightsId
  aiServices: platform.outputs.aiServicesId
  speech: platform.outputs.speechId
  searchService: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?searchServiceId ?? '') : ''
  cosmosAccount: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?cosmosAccountId ?? '') : ''
  foundryProject: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?projectId ?? '') : ''
  budget: deployBudget ? (budget.?outputs.?budgetId ?? '') : ''
}
output resourceNames object = {
  containerRegistry: platform.outputs.acrName
  containerAppsEnvironment: platform.outputs.containerAppsEnvironmentName
  portalManagedIdentity: platform.outputs.portalIdentityName
  bffManagedIdentity: platform.outputs.bffIdentityName
  portalContainerApp: portalAppName
  bffContainerApp: bffAppName
  captureContainerApp: captureAppName
  fabricCapacity: platform.outputs.fabricCapacityName
  capacityPauseLogicApp: platform.outputs.capacityPauseLogicAppName
  eventHubsNamespace: platform.outputs.eventHubsNamespaceName
  telemetryEventHub: platform.outputs.telemetryEventHubName
  storageAccount: platform.outputs.storageAccountName
  keyVault: platform.outputs.keyVaultName
  logAnalyticsWorkspace: platform.outputs.logAnalyticsWorkspaceName
  applicationInsights: platform.outputs.appInsightsName
  aiServices: platform.outputs.aiServicesName
  speech: platform.outputs.speechName
  searchService: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?searchServiceName ?? '') : ''
  cosmosAccount: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?cosmosAccountName ?? '') : ''
  foundryProject: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?projectName ?? '') : ''
}
output hostnames object = {
  containerRegistry: platform.outputs.acrLoginServer
  portal: deployApps ? (apps.?outputs.?portalFqdn ?? '') : ''
  bff: deployApps ? (apps.?outputs.?bffFqdn ?? '') : ''
  capture: deployApps ? (apps.?outputs.?captureFqdn ?? '') : ''
  storageBlob: platform.outputs.storageBlobEndpoint
  keyVault: platform.outputs.keyVaultUri
  eventHubs: platform.outputs.eventHubsHostName
  aiServices: platform.outputs.aiServicesEndpoint
  speech: platform.outputs.speechEndpoint
  search: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?searchEndpoint ?? '') : ''
  foundryProject: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?projectEndpoint ?? '') : ''
}
output modelDeployments object = {
  chat: platform.outputs.chatDeploymentName
  reasoning: platform.outputs.reasoningDeploymentName
  embedding: platform.outputs.embeddingDeploymentName
}
output agentPlatformNames object = {
  procedureIndex: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?procedureIndexName ?? '') : ''
  knowledgeBase: deployAiServices && deployAgentPlatform ? (agentPlatform.?outputs.?knowledgeBaseName ?? '') : ''
}
output deploymentFlags object = {
  deployApps: deployApps
  deployAiServices: deployAiServices
  deployModelDeployments: deployModelDeployments
  deployAgentPlatform: deployAgentPlatform
  agentServiceReady: deployAiServices && deployAgentPlatform && agentServiceManuallyValidated
  deployBudget: deployBudget
}
