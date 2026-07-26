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

@description('Create the base Azure AI Services and Speech S0 accounts only after their Sweden Central availability has been reconfirmed.')
param deployAiServices bool = false

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
  }
}

module apps './modules/apps.bicep' = if (deployApps) {
  name: '${resourcePrefix}-apps'
  scope: demoResourceGroup
  dependsOn: [
    platform
  ]
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
  budget: deployBudget ? (budget.?outputs.?budgetId ?? '') : ''
}
output resourceNames object = {
  containerRegistry: platform.outputs.acrName
  containerAppsEnvironment: platform.outputs.containerAppsEnvironmentName
  portalManagedIdentity: platform.outputs.portalIdentityName
  bffManagedIdentity: platform.outputs.bffIdentityName
  portalContainerApp: portalAppName
  bffContainerApp: bffAppName
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
}
output hostnames object = {
  containerRegistry: platform.outputs.acrLoginServer
  portal: deployApps ? (apps.?outputs.?portalFqdn ?? '') : ''
  bff: deployApps ? (apps.?outputs.?bffFqdn ?? '') : ''
  storageBlob: platform.outputs.storageBlobEndpoint
  keyVault: platform.outputs.keyVaultUri
  eventHubs: platform.outputs.eventHubsHostName
  aiServices: platform.outputs.aiServicesEndpoint
  speech: platform.outputs.speechEndpoint
}
output deploymentFlags object = {
  deployApps: deployApps
  deployAiServices: deployAiServices
  deployBudget: deployBudget
}
