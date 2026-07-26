// Azure Container Apps environment + placeholder apps/jobs (implementation-guide.md §11's
// `cd-services.yml` deploys real images later). These are infra-only placeholders using a public
// sample image so `what-if`/deploy can be exercised before any application container is built;
// swap `image` via parameter once services/* produces real images. No secrets are embedded —
// Key Vault references use the app's own managed identity.
targetScope = 'resourceGroup'

@description('Environment short name.')
param environment string

@description('Azure region.')
param location string

@description('Common resource tags.')
param tags object

@description('Log Analytics workspace resource ID for the Container Apps environment.')
param logAnalyticsWorkspaceId string

@description('Log Analytics workspace customer ID (GUID) and shared key are not used; workspace-based Container Apps environments use the resource ID + AAD-based ingestion.')
param logAnalyticsCustomerId string

@description('Container Apps environment infrastructure subnet resource ID (VNet-integrated for private ingress/egress).')
param infrastructureSubnetId string

@description('Placeholder container image for every service until services/* publishes real images via cd-services.yml.')
param placeholderImage string = 'mcr.microsoft.com/k8se/quickstart:latest'

@description('Per-service container image overrides. Keys match serviceNames (bff-api, optimizer-worker, scoring-worker, ingest-relay, knowledge-orchestrator). Unset services use placeholderImage.')
param serviceImages object = {}

@description('Map of serviceName -> { identityId, keyVaultUri } used to wire each Container App to its own managed identity and Key Vault. Expected keys: bffApi, optimizerWorker, scoringWorker, ingestRelay, knowledgeOrchestrator.')
param services object

@description('Deploy the demo/dev/test simulator Container Apps Job (SIM-004). Never deployed for prod.')
param deploySimulatorJob bool = true

@description('Simulator job managed identity resource ID (mi-ns-demo-simulator).')
param simulatorIdentityId string = ''

@description('Internal-only ingress for the Container Apps environment (no public internet ingress) per security-governance-and-threat-model.md §4.1. Set to false only for a component that must be reachable directly, e.g. behind an approved WAF/App Gateway.')
param internalOnly bool = true

@description('Application Insights connection string for OpenTelemetry telemetry export (azure-monitor-opentelemetry).')
param appInsightsConnectionString string

@description('Whether the environment is production — drives zone redundancy.')
param isProduction bool = false

@description('Table endpoint for the BFF audit log / idempotency store (Azure Table Storage). Empty string disables — BFF degrades to in-memory.')
param bffTableEndpoint string = ''

@description('Storage account name for the BFF audit log / idempotency store.')
param bffStorageAccountName string = ''

@description('Foundry (Cognitive Services) endpoint for knowledge extraction and RAG. Empty string disables — services degrade to offline/fallback.')
param foundryEndpoint string = ''

@description('GPT model deployment name from foundry-speech module (wired, not hardcoded).')
param foundryChatDeployment string = ''

@description('Embedding model deployment name from foundry-speech module (wired, not hardcoded).')
param foundryEmbedDeployment string = ''

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-ns-${environment}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
      }
    }
    vnetConfiguration: {
      infrastructureSubnetId: infrastructureSubnetId
      internal: internalOnly
    }
    zoneRedundant: isProduction
  }
}

resource containerAppsEnvironmentDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: containerAppsEnvironment
  name: 'diag-log-analytics'
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
  }
}

var serviceNames = [
  'bff-api'
  'optimizer-worker'
  'scoring-worker'
  'ingest-relay'
  'knowledge-orchestrator'
]

var serviceKeys = [
  'bffApi'
  'optimizerWorker'
  'scoringWorker'
  'ingestRelay'
  'knowledgeOrchestrator'
]

// bff-api is the only service exposed via ingress (internal only); workers/relay are ingress-less.
resource placeholderApps 'Microsoft.App/containerApps@2024-03-01' = [
  for (svc, i) in serviceNames: {
    name: 'ca-ns-${svc}-${environment}'
    location: location
    tags: tags
    identity: {
      type: 'UserAssigned'
      userAssignedIdentities: {
        '${services[serviceKeys[i]].identityId}': {}
      }
    }
    properties: {
      environmentId: containerAppsEnvironment.id
      configuration: {
        activeRevisionsMode: 'Single'
        ingress: svc == 'bff-api' ? {
          external: false
          targetPort: 8000
          transport: 'auto'
        } : null
        registries: []
      }
      template: {
        containers: [
          {
            name: svc
            image: serviceImages[?svc] ?? placeholderImage
            resources: {
              cpu: json('0.5')
              memory: '1Gi'
            }
            env: concat([
              {
                name: 'NOVASTEEL_ENVIRONMENT'
                value: environment
              }
              {
                name: 'NOVASTEEL_KEY_VAULT_URI'
                value: services[serviceKeys[i]].keyVaultUri
              }
              {
                name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
                value: appInsightsConnectionString
              }
              {
                name: 'OTEL_SERVICE_NAME'
                value: 'novasteel-${svc}'
              }
              {
                name: 'NOVASTEEL_LOG_FORMAT'
                value: 'json'
              }
            ], svc == 'bff-api' && !empty(bffTableEndpoint) ? [
              {
                name: 'NOVASTEEL_TABLE_ENDPOINT'
                value: bffTableEndpoint
              }
              {
                name: 'NOVASTEEL_STORAGE_ACCOUNT_NAME'
                value: bffStorageAccountName
              }
            ] : [], (svc == 'bff-api' || svc == 'knowledge-orchestrator') && !empty(foundryEndpoint) ? [
              {
                name: 'FOUNDRY_ENDPOINT'
                value: foundryEndpoint
              }
              {
                name: 'KNOWLEDGE_AGENT_MODE'
                value: 'azure'
              }
            ] : [], svc == 'knowledge-orchestrator' && !empty(foundryChatDeployment) ? [
              {
                name: 'FOUNDRY_CHAT_DEPLOYMENT'
                value: foundryChatDeployment
              }
              {
                name: 'FOUNDRY_EMBED_DEPLOYMENT'
                value: foundryEmbedDeployment
              }
            ] : [])
          }
        ]
        scale: {
          minReplicas: 0
          maxReplicas: 3
        }
      }
    }
  }
]

resource simulatorJob 'Microsoft.App/jobs@2024-03-01' = if (deploySimulatorJob && !empty(simulatorIdentityId)) {
  name: 'caj-ns-demo-simulator-${environment}'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${simulatorIdentityId}': {}
    }
  }
  properties: {
    environmentId: containerAppsEnvironment.id
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 1800
      replicaRetryLimit: 1
      manualTriggerConfig: {
        parallelism: 1
        replicaCompletionCount: 1
      }
    }
    template: {
      containers: [
        {
          name: 'simulator'
          image: placeholderImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'NOVASTEEL_ENVIRONMENT'
              value: environment
            }
            {
              name: 'NOVASTEEL_LOG_FORMAT'
              value: 'json'
            }
          ]
        }
      ]
    }
  }
}

output environmentId string = containerAppsEnvironment.id
output environmentName string = containerAppsEnvironment.name
output appNames array = [for svc in serviceNames: 'ca-ns-${svc}-${environment}']
output appIds array = [for (svc, i) in serviceNames: placeholderApps[i].id]
