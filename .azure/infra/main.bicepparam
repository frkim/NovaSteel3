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

// AI/Speech and budget require an explicit operator opt-in.
param deployAiServices = false
param deployBudget = false
param monthlyBudgetAmount = 250
param budgetStartDate = '2026-08-01T00:00:00Z'
param budgetContactEmails = [
  'frkim@microsoft.com'
]
