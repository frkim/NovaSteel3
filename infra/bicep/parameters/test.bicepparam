using '../main.bicep'

// test environment — synthetic and approved test fixtures only (deployment-topology.md §2.1).
param environment = 'test'
param location = 'swedencentral'

param owner = 'platform-team@example.invalid'
param costCenter = 'CC-NOVASTEEL-PLATFORM'
param expiryDate = ''

param dataClassification = 'Confidential'

param fabricSkuName = 'F2'
param fabricAdminMembers = [
  'fabric-admins-test@example.invalid'
]

param plants = [
  'plant01'
  'plant02'
]

param deployFirewall = false
param deploySentinel = true
param deployGuardrails = false

param logAnalyticsRetentionDays = 30
param logAnalyticsDailyQuotaGb = 5

param githubOrg = ''
param githubRepo = ''

param budgetAmount = 400
param budgetContactEmails = [
  'finops@example.invalid'
]
param budgetStartDate = '2026-08-01T00:00:00Z'

param foundryAgentServiceManuallyValidated = false
param deployContainerAppsPlaceholders = true
