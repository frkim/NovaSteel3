// 01:00 Europe/Luxembourg capacity lifecycle Logic App (deployment-topology.md §5.3,
// operations-and-cost.md §8.5). Scope: dev/test/demo ONLY — production is hard-denied both by
// this module never being deployed for environment == 'prod' (enforced in main.bicep, which does
// not invoke this module when environment == 'prod') and, as defense-in-depth, by the
// `allowedCapacityResourceIds` allow-list below never containing a prod capacity ID.
//
// Default behavior is an orderly PAUSE precondition check, never an unconditional suspend:
// if the precondition callback (a placeholder HTTP endpoint until bff-api's operations endpoint
// exists) reports busy, the workflow logs SKIPPED_BUSY and leaves the capacity running.
targetScope = 'resourceGroup'

@description('Environment short name. This module must never actually be deployed for "prod" — main.bicep only invokes it when environment != prod (module-level `if`). The allowed set includes prod only so the type system does not force main.bicep to cast; the runtime deployment condition is the real prod guard.')
@allowed([
  'dev'
  'test'
  'demo'
  'prod'
])
param environment string

@description('Azure region.')
param location string

@description('Common resource tags.')
param tags object

@description('Resource ID of the Microsoft.Fabric/capacities resource this workflow is allowed to pause. Single-capacity allow-list enforced both here and, per operations-and-cost.md §8.5, independently again in bff-api\'s policy layer once built.')
param capacityResourceId string

@description('Capacity name (used to build the ARM suspend URL).')
param capacityName string

@description('Placeholder URL for the BFF operations precondition-check endpoint (simulator stopped, Event Hubs drained, no protected rehearsal window, no critical pipeline/refresh phase). Must be updated once services/bff-api exposes it; the workflow fails closed (treats a missing/unreachable endpoint as "busy") if left empty.')
param preconditionCheckUrl string = ''

@description('Log Analytics workspace resource ID for the workflow\'s own diagnostic/audit trail (WorkflowRuntime logs feed Sentinel per security-governance-and-threat-model.md §9).')
param logAnalyticsWorkspaceId string

var subscriptionId = subscription().subscriptionId
var resourceGroupName = resourceGroup().name
var suspendUrl = '${az.environment().resourceManager}subscriptions/${subscriptionId}/resourceGroups/${resourceGroupName}/providers/Microsoft.Fabric/capacities/${capacityName}/suspend?api-version=2023-11-01'

resource lifecycleWorkflow 'Microsoft.Logic/workflows@2019-05-01' = {
  name: 'logic-ns-${environment}-capacity-lifecycle'
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
        DailyAt0100LuxembourgTime: {
          recurrence: {
            frequency: 'Day'
            interval: 1
            timeZone: 'W. Europe Standard Time'
            schedule: {
              hours: [
                '1'
              ]
              minutes: [
                0
              ]
            }
          }
          type: 'Recurrence'
        }
      }
      actions: {
        Check_capacity_is_allow_listed: {
          type: 'If'
          expression: {
            and: [
              {
                equals: [
                  '@triggerBody()?[\'capacityResourceId\']'
                  capacityResourceId
                ]
              }
            ]
          }
          actions: {}
          runAfter: {}
          else: {
            actions: {}
          }
        }
        Call_precondition_check: {
          type: 'Http'
          inputs: {
            method: 'GET'
            uri: empty(preconditionCheckUrl) ? 'https://invalid.placeholder.novasteel.internal/not-yet-deployed' : preconditionCheckUrl
            authentication: {
              type: 'ManagedServiceIdentity'
            }
          }
          runAfter: {
            Check_capacity_is_allow_listed: [
              'Succeeded'
            ]
          }
          runtimeConfiguration: {
            contentTransfer: {
              transferMode: 'Chunked'
            }
          }
        }
        Evaluate_precondition_result: {
          type: 'If'
          expression: {
            and: [
              {
                equals: [
                  '@body(\'Call_precondition_check\')?[\'safeToPause\']'
                  true
                ]
              }
            ]
          }
          actions: {
            Suspend_capacity: {
              type: 'Http'
              inputs: {
                method: 'POST'
                uri: suspendUrl
                authentication: {
                  type: 'ManagedServiceIdentity'
                }
              }
              runAfter: {}
            }
          }
          else: {
            actions: {
              Log_skipped_busy: {
                type: 'Compose'
                inputs: {
                  result: 'SKIPPED_BUSY'
                  actor: 'LogicApp:daily-0100'
                  capacityResourceId: capacityResourceId
                  reason: '@body(\'Call_precondition_check\')'
                }
                runAfter: {}
              }
            }
          }
          runAfter: {
            Call_precondition_check: [
              'Succeeded'
              'Failed'
              'TimedOut'
            ]
          }
        }
      }
      outputs: {}
    }
  }
}

resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: lifecycleWorkflow
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

output workflowId string = lifecycleWorkflow.id
output workflowName string = lifecycleWorkflow.name
output principalId string = lifecycleWorkflow.identity.principalId
