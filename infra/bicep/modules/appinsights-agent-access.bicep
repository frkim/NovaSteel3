// Grants the Foundry project identity read access to the Application Insights
// component that receives its agent traces.
//
// Separate from modules/foundry-agents.bicep because Application Insights lives in
// rg-ns-<env>-monitoring while the Foundry project lives in rg-ns-<env>-ai, and a
// resource-group-scoped module can only assign roles inside its own scope.
//
// Two roles, both needed for different halves of observability:
//   * Log Analytics Reader — lets the Foundry portal render the project's Tracing
//     and Monitoring blades by querying the workspace behind the component.
//   * Privileged Monitoring Data Reader — lets Foundry evaluation read the GenAI
//     *message content* attached to those spans. Without it, evaluators can see that
//     a run happened but not what was said, so groundedness/relevance scoring fails.
//
// Plus Monitoring Metrics Publisher for the write direction: the AppInsights
// connection authenticates as the project identity (`ProjectManagedIdentity`), so
// that identity must be able to publish telemetry into the component.
//
// Because the second role exposes prompt and completion text, it is granted only to
// the project's own managed identity — never to operators — which keeps interview
// content inside the same trust boundary as the rest of the pipeline
// (security-governance-and-threat-model.md §4.1).
targetScope = 'resourceGroup'

@description('Name of the Application Insights component that receives Foundry agent traces.')
param appInsightsName string

@description('Object ID of the Foundry project managed identity.')
param projectPrincipalId string

var logAnalyticsReaderRoleId = '73c42c96-874c-492b-b04d-ab87d138a893'
var privilegedMonitoringDataReaderRoleId = 'dbc9c667-e97f-4491-aee6-90b9cf960190'
var monitoringMetricsPublisherRoleId = '3913510d-42f4-4e42-8a64-420c390055eb'

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource readerRoles 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for roleId in [logAnalyticsReaderRoleId, privilegedMonitoringDataReaderRoleId, monitoringMetricsPublisherRoleId]: {
    scope: appInsights
    name: guid(appInsights.id, projectPrincipalId, roleId)
    properties: {
      principalId: projectPrincipalId
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleId)
      principalType: 'ServicePrincipal'
    }
  }
]

output appInsightsId string = appInsights.id
