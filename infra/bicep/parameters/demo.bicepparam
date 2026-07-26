using '../main.bicep'

// demo environment — 100% SYNTHETIC / DEMO-NONPERSONAL data only (deployment-topology.md §2.1).
// `expiryDate` is MANDATORY for demo (never leave empty) per deployment-topology.md §3.1.
param environment = 'demo'
param location = 'swedencentral'

param owner = 'platform-team@example.invalid'
param costCenter = 'CC-NOVASTEEL-DEMO'
param expiryDate = '2026-12-31' // update to the actual planned teardown/rehearsal-window date

param dataClassification = 'Confidential'

param fabricSkuName = 'F2' // F4 only after a measured contention decision (deployment-topology.md §6)
param fabricAdminMembers = [
  'fabric-admins-demo@example.invalid'
]

param plants = [
  'plant01'
]

param deployFirewall = false
param deploySentinel = true
param deployGuardrails = false

param logAnalyticsRetentionDays = 30
param logAnalyticsDailyQuotaGb = 5

param githubOrg = ''
param githubRepo = ''

param budgetAmount = 350
param budgetContactEmails = [
  'finops@example.invalid'
]
param budgetStartDate = '2026-08-01T00:00:00Z'

param foundryAgentServiceManuallyValidated = false
param deployContainerAppsPlaceholders = true
