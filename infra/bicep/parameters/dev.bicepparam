using '../main.bicep'

// dev environment — synthetic/masked test data only (deployment-topology.md §2.1).
// Replace placeholder values (owner, fabricAdminMembers, budgetContactEmails, githubOrg/githubRepo)
// before running infra/scripts/deploy.ps1. Placeholder emails intentionally use the
// example.invalid domain so an unedited file cannot be deployed against a real tenant by accident.
param environment = 'dev'
param location = 'swedencentral'

param owner = 'platform-team@example.invalid'
param costCenter = 'CC-NOVASTEEL-PLATFORM'
param expiryDate = '' // set a yyyy-MM-dd date before deploying dev if it should auto-expire

param dataClassification = 'Confidential'

param fabricSkuName = 'F2'
param fabricAdminMembers = [
  'fabric-admins-dev@example.invalid'
]

param plants = [
  'plant01'
]

param deployFirewall = false
param deploySentinel = true
param deployGuardrails = false // set true only on the one pipeline designated authoritative for subscription-wide guardrails

param logAnalyticsRetentionDays = 30
param logAnalyticsDailyQuotaGb = 5

param githubOrg = ''
param githubRepo = ''

param budgetAmount = 300
param budgetContactEmails = [
  'finops@example.invalid'
]
param budgetStartDate = '2026-08-01T00:00:00Z'

param foundryAgentServiceManuallyValidated = false
param deployContainerAppsPlaceholders = true
