targetScope = 'resourceGroup'

param location string
param resourcePrefix string
param nameSuffix string
param tags object
param appInsightsName string
param portalImage string
param bffImage string
param portalOrigin string
param portalBffBaseUrl string

@description('Foundry account inference endpoint. Empty keeps the knowledge/Copilot agents on deterministic local fallbacks.')
param foundryEndpoint string = ''

@description('Foundry project endpoint for Agent Service. Empty means agents are not hosted.')
param foundryProjectEndpoint string = ''

param foundryChatDeployment string = ''
param foundryReasoningDeployment string = ''
param foundryEmbedDeployment string = ''

@description('Azure AI Search endpoint. Empty keeps procedures in the in-memory store.')
param searchEndpoint string = ''

param searchIndexName string = ''
param knowledgeBaseName string = ''

@description('Web IQ and web search are First Party Consumption Services: the Microsoft DPA does not apply and data leaves the Azure compliance boundary. Offline is the only default this estate may ship.')
@allowed([
  'offline'
  'web_iq'
  'web_search'
])
param onlineSearchMode string = 'offline'

var acrLoginServer = '${resourcePrefix}acr${nameSuffix}.azurecr.io'
var keyVaultUri = 'https://${resourcePrefix}-kv-${nameSuffix}${environment().suffixes.keyvaultDns}/'
var storageAccountName = '${resourcePrefix}st${nameSuffix}'
var eventHubsNamespace = '${resourcePrefix}-eh-${nameSuffix}'
var fabricCapacityName = '${resourcePrefix}fabric'

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: '${resourcePrefix}-cae'
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource portalIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: '${resourcePrefix}-portal-mi'
}

resource bffIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: '${resourcePrefix}-bff-mi'
}

resource portalApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${resourcePrefix}-portal'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${portalIdentity.id}': {}
    }
  }
  properties: {
    environmentId: containerAppsEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8080
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: acrLoginServer
          identity: portalIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'portal'
          image: portalImage
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'AZURE_CLIENT_ID'
              value: portalIdentity.properties.clientId
            }
            {
              name: 'BFF_BASE_URL'
              value: portalBffBaseUrl
            }
            {
              name: 'PORTAL_BFF_BASE_URL'
              value: portalBffBaseUrl
            }
          ]
          probes: [
            {
              type: 'startup'
              httpGet: {
                path: '/'
                port: 8080
              }
              initialDelaySeconds: 0
              periodSeconds: 10
              failureThreshold: 30
            }
            {
              type: 'liveness'
              httpGet: {
                path: '/'
                port: 8080
              }
              initialDelaySeconds: 10
              periodSeconds: 30
              failureThreshold: 3
            }
            {
              type: 'readiness'
              httpGet: {
                path: '/'
                port: 8080
              }
              initialDelaySeconds: 5
              periodSeconds: 10
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
        rules: [
          {
            name: 'http'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
    }
  }
}

resource bffApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${resourcePrefix}-bff'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${bffIdentity.id}': {}
    }
  }
  properties: {
    environmentId: containerAppsEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8080
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: acrLoginServer
          identity: bffIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'bff'
          image: bffImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'AZURE_CLIENT_ID'
              value: bffIdentity.properties.clientId
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: applicationInsights.properties.ConnectionString
            }
            {
              name: 'BFF_CORS_ORIGINS'
              value: portalOrigin
            }
            {
              name: 'BFF_ENVIRONMENT'
              value: 'demo'
            }
            {
              name: 'BFF_DATA_NAMESPACE'
              value: 'NS-DEMO-LUX-01'
            }
            {
              name: 'DEMO_MODE'
              value: 'local'
            }
            {
              name: 'BFF_AUTH_MODE'
              value: 'demo'
            }
            {
              name: 'BFF_CAPACITY_MODE'
              value: 'local'
            }
            {
              name: 'BFF_CAPACITY_ALLOWLIST'
              value: fabricCapacityName
            }
            {
              name: 'KEY_VAULT_URL'
              value: keyVaultUri
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT'
              value: storageAccountName
            }
            {
              name: 'EVENTHUB_NAMESPACE'
              value: eventHubsNamespace
            }
            // AI configuration. Every one of these is empty unless the matching
            // deployment flag was set, and the services treat an empty value as
            // "stay offline" — so the demo keeps working on deterministic fixtures
            // rather than failing when the AI estate is not deployed.
            {
              name: 'FOUNDRY_ENDPOINT'
              value: foundryEndpoint
            }
            {
              name: 'FOUNDRY_PROJECT_ENDPOINT'
              value: foundryProjectEndpoint
            }
            {
              name: 'FOUNDRY_CHAT_DEPLOYMENT'
              value: foundryChatDeployment
            }
            {
              name: 'FOUNDRY_REASONING_DEPLOYMENT'
              value: foundryReasoningDeployment
            }
            {
              name: 'FOUNDRY_EMBED_DEPLOYMENT'
              value: foundryEmbedDeployment
            }
            {
              name: 'AI_SEARCH_ENDPOINT'
              value: searchEndpoint
            }
            {
              name: 'AI_SEARCH_INDEX'
              value: searchIndexName
            }
            {
              name: 'FOUNDRY_KNOWLEDGE_BASE'
              value: knowledgeBaseName
            }
            {
              name: 'ONLINE_SEARCH_MODE'
              value: onlineSearchMode
            }
          ]
          probes: [
            {
              type: 'startup'
              httpGet: {
                path: '/health/live'
                port: 8080
              }
              initialDelaySeconds: 0
              periodSeconds: 10
              failureThreshold: 30
            }
            {
              type: 'liveness'
              httpGet: {
                path: '/health/live'
                port: 8080
              }
              initialDelaySeconds: 10
              periodSeconds: 30
              failureThreshold: 3
            }
            {
              type: 'readiness'
              httpGet: {
                path: '/health/ready'
                port: 8080
              }
              initialDelaySeconds: 5
              periodSeconds: 10
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
    }
  }
}

output portalAppId string = portalApp.id
output portalFqdn string = portalApp.properties.configuration.ingress.fqdn
output bffAppId string = bffApp.id
output bffFqdn string = bffApp.properties.configuration.ingress.fqdn
