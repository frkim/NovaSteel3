// Azure Monitor alerting: action group + 10 scheduled-query / metric alert rules defined in
// docs/operations/operations-and-cost.md §4. Alerts are advisory; they never actuate plant
// equipment. Pattern based on Project A's monitoring-alerts.bicep but expanded to the full
// ten-alert catalogue.
targetScope = 'resourceGroup'

@description('Environment short name.')
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

@description('Resource ID of the Log Analytics workspace the alerts query.')
param logAnalyticsWorkspaceId string

@description('Resource ID of the Application Insights instance.')
param appInsightsId string

@description('Email address for alert notifications (operations team).')
param alertEmail string = ''

@description('Optional webhook URI for PagerDuty/Teams incident channel integration.')
param webhookUri string = ''

@description('Enable all alert rules. Disable for dev/cost control.')
param enableAlerts bool = true

var isProd = environment == 'prod'
var actionGroupName = 'ag-ns-${environment}'
var hasEmail = !empty(alertEmail)
var hasWebhook = !empty(webhookUri)

// Severity and frequency are environment-tiered: prod is stricter.
var sev2Frequency = isProd ? 'PT5M' : 'PT15M'
var sev2Window = isProd ? 'PT5M' : 'PT15M'
var sev3Frequency = isProd ? 'PT15M' : 'PT30M'
var sev3Window = isProd ? 'PT1H' : 'PT6H'

// ---------------------------------------------------------------------------
// Action Group
// ---------------------------------------------------------------------------
resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: actionGroupName
  location: 'global'
  tags: tags
  properties: {
    groupShortName: take('ns${environment}', 12)
    enabled: true
    emailReceivers: hasEmail ? [
      {
        name: 'ops-email'
        emailAddress: alertEmail
        useCommonAlertSchema: true
      }
    ] : []
    webhookReceivers: hasWebhook ? [
      {
        name: 'ops-webhook'
        serviceUri: webhookUri
        useCommonAlertSchema: true
      }
    ] : []
  }
}

// ---------------------------------------------------------------------------
// Alert 1: BFF API error rate > 5% over 5 minutes (Sev-2)
// ---------------------------------------------------------------------------
resource alertBffErrorRate 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = if (enableAlerts) {
  name: 'alert-ns-${environment}-bff-error-rate'
  location: location
  tags: tags
  properties: {
    displayName: 'NovaSteel BFF API error rate > 5%'
    description: 'bff-api error rate exceeds 5% over the evaluation window; investigate service health.'
    severity: 2
    enabled: true
    scopes: [appInsightsId]
    evaluationFrequency: sev2Frequency
    windowSize: sev2Window
    criteria: {
      allOf: [
        {
          query: 'requests\n| summarize Total = count(), Failed = countif(success == false)\n| extend ErrorPct = iff(Total > 0, (Failed * 100.0) / Total, 0.0)\n| project ErrorPct'
          timeAggregation: 'Maximum'
          metricMeasureColumn: 'ErrorPct'
          operator: 'GreaterThan'
          threshold: 5
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    autoMitigate: true
    actions: {
      actionGroups: [actionGroup.id]
    }
  }
}

// ---------------------------------------------------------------------------
// Alert 2: Data freshness stale > 60s during active ingestion (Sev-2)
// ---------------------------------------------------------------------------
resource alertDataFreshness 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = if (enableAlerts) {
  name: 'alert-ns-${environment}-data-freshness'
  location: location
  tags: tags
  properties: {
    displayName: 'NovaSteel data freshness SLO breach (>60s stale)'
    description: 'No telemetry ingestion observed within 60 seconds during expected active ingestion; pipeline may be stalled.'
    severity: 2
    enabled: true
    scopes: [logAnalyticsWorkspaceId]
    evaluationFrequency: sev2Frequency
    windowSize: isProd ? 'PT5M' : 'PT15M'
    criteria: {
      allOf: [
        {
          query: 'customMetrics\n| where name == "novasteel.energy.kwh_per_tonne" or name has "telemetry"\n| summarize LastEvent = max(timestamp)\n| extend StalenessSeconds = datetime_diff("second", now(), LastEvent)\n| project StalenessSeconds'
          timeAggregation: 'Maximum'
          metricMeasureColumn: 'StalenessSeconds'
          operator: 'GreaterThan'
          threshold: 60
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    autoMitigate: true
    actions: {
      actionGroups: [actionGroup.id]
    }
  }
}

// ---------------------------------------------------------------------------
// Alert 3: Quarantine rate > 2% of ingested events over 15 minutes (Sev-2)
// ---------------------------------------------------------------------------
resource alertQuarantineRate 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = if (enableAlerts) {
  name: 'alert-ns-${environment}-quarantine-rate'
  location: location
  tags: tags
  properties: {
    displayName: 'NovaSteel quarantine rate > 2%'
    description: 'More than 2% of ingested events are landing in quarantine over the evaluation window.'
    severity: 2
    enabled: true
    scopes: [logAnalyticsWorkspaceId]
    evaluationFrequency: sev2Frequency
    windowSize: 'PT15M'
    criteria: {
      allOf: [
        {
          query: 'customMetrics\n| where name has "telemetry" or name has "quarantine"\n| summarize Total = countif(name has "telemetry"), Quarantined = countif(name has "quarantine")\n| extend QuarantinePct = iff(Total > 0, (Quarantined * 100.0) / Total, 0.0)\n| project QuarantinePct'
          timeAggregation: 'Maximum'
          metricMeasureColumn: 'QuarantinePct'
          operator: 'GreaterThan'
          threshold: 2
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    autoMitigate: true
    actions: {
      actionGroups: [actionGroup.id]
    }
  }
}

// ---------------------------------------------------------------------------
// Alert 4: Capacity ARM operation failure (resume/suspend) (Sev-2)
// ---------------------------------------------------------------------------
resource alertCapacityArmFailure 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = if (enableAlerts) {
  name: 'alert-ns-${environment}-capacity-arm-failure'
  location: location
  tags: tags
  properties: {
    displayName: 'NovaSteel Fabric capacity ARM operation failure'
    description: 'A Fabric capacity resume or suspend ARM operation failed; capacity may be stuck in an unknown state.'
    severity: 2
    enabled: true
    scopes: [logAnalyticsWorkspaceId]
    evaluationFrequency: sev2Frequency
    windowSize: sev2Window
    criteria: {
      allOf: [
        {
          query: 'AzureActivity\n| where ResourceProviderValue == "MICROSOFT.FABRIC"\n| where OperationNameValue has_any ("suspend", "resume")\n| where ActivityStatusValue == "Failed"\n| summarize FailureCount = count()'
          timeAggregation: 'Total'
          metricMeasureColumn: 'FailureCount'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    autoMitigate: true
    actions: {
      actionGroups: [actionGroup.id]
    }
  }
}

// ---------------------------------------------------------------------------
// Alert 5: Capacity budget alert threshold reached (Sev-3)
// ---------------------------------------------------------------------------
resource alertBudgetThreshold 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = if (enableAlerts) {
  name: 'alert-ns-${environment}-budget-threshold'
  location: location
  tags: tags
  properties: {
    displayName: 'NovaSteel capacity budget threshold reached'
    description: 'Fabric capacity utilisation or cost has reached a budget alert threshold; review FinOps controls.'
    severity: 3
    enabled: true
    scopes: [logAnalyticsWorkspaceId]
    evaluationFrequency: sev3Frequency
    windowSize: sev3Window
    criteria: {
      allOf: [
        {
          query: 'AzureActivity\n| where ResourceProviderValue == "MICROSOFT.FABRIC"\n| where Properties has "throttl" or Properties has "capacity" and Properties has "limit"\n| summarize ThrottleCount = count()'
          timeAggregation: 'Total'
          metricMeasureColumn: 'ThrottleCount'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    autoMitigate: true
    actions: {
      actionGroups: [actionGroup.id]
    }
  }
}

// ---------------------------------------------------------------------------
// Alert 6: Energy-dispatch agent tool call without human-approval audit (Sev-1)
// ---------------------------------------------------------------------------
resource alertUnauthorizedDispatch 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = if (enableAlerts) {
  name: 'alert-ns-${environment}-unauthorized-dispatch'
  location: location
  tags: tags
  properties: {
    displayName: 'NovaSteel energy-dispatch without human approval (Sev-1)'
    description: 'An energy-dispatch agent tool call was detected without a matching human-approval audit event. Potential unauthorized scheduling action.'
    severity: 1
    enabled: true
    scopes: [logAnalyticsWorkspaceId]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    criteria: {
      allOf: [
        {
          query: 'customEvents\n| where name == "energy_dispatch_executed"\n| join kind=leftanti (\n    customEvents\n    | where name == "energy_dispatch_approved"\n    | project approval_correlation = tostring(customDimensions.correlation_id)\n) on $left.customDimensions.correlation_id == $right.approval_correlation\n| summarize UnauthorizedCount = count()'
          timeAggregation: 'Total'
          metricMeasureColumn: 'UnauthorizedCount'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    autoMitigate: false
    actions: {
      actionGroups: [actionGroup.id]
    }
  }
}

// ---------------------------------------------------------------------------
// Alert 7: Key Vault secret access outside expected managed identity (Sev-2)
// ---------------------------------------------------------------------------
resource alertKeyVaultAnomalousAccess 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = if (enableAlerts) {
  name: 'alert-ns-${environment}-keyvault-anomalous'
  location: location
  tags: tags
  properties: {
    displayName: 'NovaSteel Key Vault access outside expected managed identity'
    description: 'A Key Vault secret/key was accessed by an identity not in the expected managed identity set.'
    severity: 2
    enabled: true
    scopes: [logAnalyticsWorkspaceId]
    evaluationFrequency: sev2Frequency
    windowSize: sev2Window
    criteria: {
      allOf: [
        {
          query: 'AzureDiagnostics\n| where ResourceProvider == "MICROSOFT.KEYVAULT"\n| where OperationName has_any ("SecretGet", "SecretList", "KeySign")\n| where identity_claim_oid_g !in ("expected-mi-object-ids-placeholder")\n| where ResultSignature != "Forbidden"\n| summarize AnomalousCount = count()'
          timeAggregation: 'Total'
          metricMeasureColumn: 'AnomalousCount'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    autoMitigate: false
    actions: {
      actionGroups: [actionGroup.id]
    }
  }
}

// ---------------------------------------------------------------------------
// Alert 8: Anomalous OneLake export volume (Sev-2)
// ---------------------------------------------------------------------------
resource alertOneLakeExport 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = if (enableAlerts) {
  name: 'alert-ns-${environment}-onelake-export'
  location: location
  tags: tags
  properties: {
    displayName: 'NovaSteel anomalous OneLake export volume'
    description: 'An unusually large volume of data was exported from a Confidential/Highly Confidential OneLake item.'
    severity: 2
    enabled: true
    scopes: [logAnalyticsWorkspaceId]
    evaluationFrequency: sev2Frequency
    windowSize: 'PT15M'
    criteria: {
      allOf: [
        {
          query: 'AzureActivity\n| where ResourceProviderValue has "FABRIC" or ResourceProviderValue has "ONELAKE"\n| where OperationNameValue has "read" or OperationNameValue has "export"\n| summarize TotalBytes = sum(toint(Properties_d.bytes))\n| extend TotalMB = TotalBytes / (1024 * 1024)\n| project TotalMB'
          timeAggregation: 'Maximum'
          metricMeasureColumn: 'TotalMB'
          operator: 'GreaterThan'
          threshold: isProd ? 500 : 1000
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    autoMitigate: false
    actions: {
      actionGroups: [actionGroup.id]
    }
  }
}

// ---------------------------------------------------------------------------
// Alert 9: Model drift or failed evaluation (Sev-3)
// Uses custom metric novasteel.rul.confidence from OpenTelemetry instrumentation.
// ---------------------------------------------------------------------------
resource alertModelDrift 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = if (enableAlerts) {
  name: 'alert-ns-${environment}-model-drift'
  location: location
  tags: tags
  properties: {
    displayName: 'NovaSteel model drift (RUL confidence drop)'
    description: 'Mean RUL prediction confidence has dropped below the drift threshold; triggers RAI review, not silent redeploy.'
    severity: 3
    enabled: true
    scopes: [appInsightsId]
    evaluationFrequency: sev3Frequency
    windowSize: sev3Window
    criteria: {
      allOf: [
        {
          query: 'customMetrics\n| where name == "novasteel.rul.confidence"\n| summarize AvgConfidence = avg(value)'
          timeAggregation: 'Average'
          metricMeasureColumn: 'AvgConfidence'
          operator: 'LessThan'
          threshold: json('0.5')
          failingPeriods: {
            numberOfEvaluationPeriods: 2
            minFailingPeriodsToAlert: 2
          }
        }
      ]
    }
    autoMitigate: false
    actions: {
      actionGroups: [actionGroup.id]
    }
  }
}

// ---------------------------------------------------------------------------
// Alert 10: 01:00 lifecycle SKIPPED_BUSY > 3 consecutive days (Sev-4)
// ---------------------------------------------------------------------------
resource alertLifecycleSkipped 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = if (enableAlerts) {
  name: 'alert-ns-${environment}-lifecycle-skipped'
  location: location
  tags: tags
  properties: {
    displayName: 'NovaSteel 01:00 lifecycle SKIPPED_BUSY 3+ consecutive days'
    description: 'The nightly capacity lifecycle check has been SKIPPED_BUSY for 3+ consecutive days; investigate why capacity never drains.'
    severity: 4
    enabled: true
    scopes: [logAnalyticsWorkspaceId]
    evaluationFrequency: 'PT6H'
    windowSize: 'P3D'
    criteria: {
      allOf: [
        {
          query: 'AzureDiagnostics\n| where ResourceType == "WORKFLOWS"\n| where resource_workflowName_s has "capacity-lifecycle"\n| where status_s == "Succeeded"\n| extend RunResult = tostring(parse_json(tostring(resource_runProperties_s)).outputs.result)\n| where RunResult has "SKIPPED_BUSY"\n| summarize ConsecutiveSkips = dcount(bin(timestamp, 1d))'
          timeAggregation: 'Maximum'
          metricMeasureColumn: 'ConsecutiveSkips'
          operator: 'GreaterThanOrEqual'
          threshold: 3
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    autoMitigate: true
    actions: {
      actionGroups: [actionGroup.id]
    }
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------
output actionGroupId string = actionGroup.id
output actionGroupName string = actionGroup.name
