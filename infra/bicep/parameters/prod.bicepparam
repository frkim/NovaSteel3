using '../main.bicep'

// prod environment — real EU operational/personal data only AFTER all production gates in
// deployment-topology.md §9 ("Before non-synthetic pilot/production") and solution-architecture.md
// §13 step 8 are signed. Do NOT deploy this file until that governance gate has cleared — see
// infra/README.md "Deployment blockers".
param environment = 'prod'
param location = 'swedencentral'

param owner = 'platform-sre@example.invalid'
param costCenter = 'CC-NOVASTEEL-PROD'
param expiryDate = '' // production capacity is never automatically expired/paused (deployment-topology.md §2.1)

param dataClassification = 'Confidential'

// Production Fabric SKU is a measured, pilot-load-tested decision, never guessed
// (deployment-topology.md §6, solution-architecture.md §13 step 8). F2 is kept here ONLY as a
// safe non-destructive placeholder; update after the load test evidence exists.
param fabricSkuName = 'F2'
param fabricAdminMembers = [
  'fabric-admins-prod@example.invalid'
]

param plants = [
  'plant01'
]

// Production posture is stricter than non-prod by default.
param deployFirewall = true
param deploySentinel = true
param deployGuardrails = true // prod is the designated authoritative pipeline for subscription-wide guardrails

param logAnalyticsRetentionDays = 365 // security-governance-and-threat-model.md §9: >= 1 year hot
param logAnalyticsDailyQuotaGb = -1 // no ingestion cap in prod; monitor cost via budgets instead

param githubOrg = ''
param githubRepo = ''

param budgetAmount = 1500
param budgetContactEmails = [
  'finops@example.invalid'
  'platform-sre@example.invalid'
]
param budgetStartDate = '2026-08-01T00:00:00Z'

// Never true until research/azure-ai-regions.md's deployment validation gate has actually been
// executed against the production tenant/subscription.
param foundryAgentServiceManuallyValidated = false

// Placeholder container images still apply in prod until services/* publishes real, scanned,
// SBOM-tracked images through cd-services.yml with the required release approvals.
param deployContainerAppsPlaceholders = true
