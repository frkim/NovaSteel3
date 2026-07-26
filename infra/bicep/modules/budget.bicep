// Azure Consumption Budget + cost alerts, one per environment, scoped to the subscription and
// filtered to that environment's resource groups (operations-and-cost.md §8.4: "Azure budgets and
// cost alerts on every resource group, tagged costCenter and expiry").
targetScope = 'subscription'

@description('Environment short name.')
param environment string

@description('Resource group names belonging to this environment, used as the budget cost filter.')
param resourceGroupNames array

@description('Monthly budget amount in the billing currency. Exact regional pricing is not encoded here (deployment-topology.md §6) — set from an actual Azure pricing calculator/FinOps estimate.')
param amount int

@description('Email addresses notified at 50/80/100% of budget (FinOps + Platform Admin per operations-and-cost.md §8.4).')
param contactEmails array

@description('Budget start date (first day of a month, UTC, format yyyy-MM-01T00:00:00Z).')
param startDate string

resource budget 'Microsoft.Consumption/budgets@2023-11-01' = {
  name: 'budget-ns-${environment}'
  properties: {
    category: 'Cost'
    amount: amount
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: startDate
    }
    filter: {
      dimensions: {
        name: 'ResourceGroupName'
        operator: 'In'
        values: resourceGroupNames
      }
    }
    notifications: {
      Actual_50: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 50
        contactEmails: contactEmails
        thresholdType: 'Actual'
      }
      Actual_80: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 80
        contactEmails: contactEmails
        thresholdType: 'Actual'
      }
      Forecasted_100: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 100
        contactEmails: contactEmails
        thresholdType: 'Forecasted'
      }
    }
  }
}

output budgetId string = budget.id
