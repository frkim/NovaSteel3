using './main.bicep'

param location = 'swedencentral'
param resourceGroupName = 'rg-novasteelv3-demo-sc'
param resourcePrefix = 'novasteelv3'
param owner = 'frkim@microsoft.com'
param costCenter = 'novasteel-demo'
param expiryDate = '2026-12-31'
param fabricAdministrator = 'dd0e874e-c9d8-494f-b7ac-3a182952e628'

// Reserved placeholder digests are valid image references but never pulled while deployApps is false.
param deployApps = false
param portalImage = 'placeholder.invalid/novasteelv3/portal@sha256:0000000000000000000000000000000000000000000000000000000000000000'
param bffImage = 'placeholder.invalid/novasteelv3/bff@sha256:1111111111111111111111111111111111111111111111111111111111111111'
param portalOrigin = 'https://placeholder.invalid'
param portalBffBaseUrl = 'https://placeholder.invalid'

// Operator capture PWA. An empty image skips the Container App entirely, so the
// estate stays deployable before that image exists; the app phase supplies the
// immutable digest and the deployed capture/BFF URLs.
param captureImage = ''
param captureOrigin = ''
param captureBffBaseUrl = ''

// AI/Speech and budget require an explicit operator opt-in.
param deployAiServices = false

// Model deployments are gated separately from the accounts: availability and quota
// for the GPT-5 series are per-subscription and can fail independently.
param deployModelDeployments = false

// AI Search bills a fixed monthly amount whether or not it is queried, so the agent
// estate stays opt-in for this cost-capped demo.
param deployAgentPlatform = false

// A capability host is IMMUTABLE once created and cannot be repointed at different
// Search/Cosmos/Storage accounts. Leave false until those three are final.
param agentServiceManuallyValidated = false

// Web IQ and web search are First Party Consumption Services: the Microsoft DPA does
// not apply and queries leave the Azure compliance boundary. Offline needs no gate.
param onlineSearchMode = 'offline'

param deployBudget = false
param monthlyBudgetAmount = 250
param budgetStartDate = '2026-08-01T00:00:00Z'
param budgetContactEmails = [
  'frkim@microsoft.com'
]
