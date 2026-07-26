// Log Analytics workspace + Application Insights (workspace-based) + Microsoft Sentinel
// onboarding for one environment (security-governance-and-threat-model.md §9: "Central Log
// Analytics workspace per environment ... Microsoft Sentinel is the SIEM of record").
targetScope = 'resourceGroup'

@description('Environment short name.')
param environment string

@description('Azure region.')
param location string

@description('Common resource tags.')
param tags object

@description('Interactive (hot) retention in days. Security doc §9 requires >= 1 year hot for production; keep shorter for dev/test/demo to control cost.')
param retentionInDays int = 90

@description('Daily ingestion cap in GB to bound cost (-1 disables the cap). Set explicitly per environment/FinOps review (operations-and-cost.md §8.4).')
param dailyQuotaGb int = -1

@description('Onboard Microsoft Sentinel onto this workspace. Requires the Microsoft.SecurityInsights resource provider to be registered in the subscription — verify before enabling in a new subscription.')
param deploySentinel bool = true

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-ns-${environment}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionInDays
    workspaceCapping: dailyQuotaGb >= 0 ? {
      dailyQuotaGb: dailyQuotaGb
    } : null
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-ns-${environment}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    DisableIpMasking: false
  }
}

resource sentinelOnboarding 'Microsoft.SecurityInsights/onboardingStates@2024-03-01' = if (deploySentinel) {
  scope: logAnalytics
  name: 'default'
  properties: {}
}

output logAnalyticsWorkspaceId string = logAnalytics.id
output logAnalyticsWorkspaceName string = logAnalytics.name
output logAnalyticsCustomerId string = logAnalytics.properties.customerId
output appInsightsId string = appInsights.id
output appInsightsName string = appInsights.name
output appInsightsConnectionString string = appInsights.properties.ConnectionString
