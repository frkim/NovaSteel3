// Managed identities and GitHub OIDC (Workload Identity Federation) for one NovaSteel environment.
// Deployed into the rg-ns-<env>-apps resource group (or an equivalent identity-owning RG) so all
// per-service identities live in one place. Each logical service gets its own user-assigned managed
// identity per security-governance-and-threat-model.md §3.1 ("no shared god identity"). Role
// ASSIGNMENTS granting these identities access to Key Vault/Event Hubs/Fabric/etc. happen in the
// resource-specific modules (keyvault.bicep, eventhubs.bicep, fabric-capacity.bicep, ...), each of
// which accepts the relevant principalId as a parameter.
targetScope = 'resourceGroup'

@description('Environment short name: dev, test, demo, prod.')
param environment string

@description('Azure region.')
param location string

@description('Common resource tags.')
param tags object

@description('Per-plant short names used to mint one dedicated OT-gateway identity per plant (mi-ns-otgw-<plant>), scoped later to that plant\'s Event Hub only.')
param plants array = []

@description('Deploy the demo-only simulator publisher identity (mi-ns-demo-simulator). Only meaningful for dev/test/demo.')
param deploySimulatorIdentity bool = true

@description('Deploy the GitHub OIDC deployment identity + federated credential for this environment. This is the Bicep-native, ARM-only alternative to an Entra app registration: a user-assigned managed identity plus a federatedIdentityCredentials child resource, which does NOT require tenant-admin/Graph permissions to create (only Contributor on this resource group) — see infra/scripts/setup-github-oidc-*.ps1 and infra/README.md for the tenant-admin-gated app-registration alternative.')
param deployGitHubOidcIdentity bool = true

@description('GitHub organization/user that owns the repository allowed to federate as this identity. Required (non-empty) when deployGitHubOidcIdentity is true.')
param githubOrg string = ''

@description('GitHub repository name (without the org prefix). Required (non-empty) when deployGitHubOidcIdentity is true.')
param githubRepo string = ''

@description('GitHub Environment name that must match this Azure environment 1:1 for the federated credential subject (never a wildcard branch ref for prod, per security-governance-and-threat-model.md §3.2).')
param githubEnvironmentName string = environment

resource miBff 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'mi-ns-bff-${environment}'
  location: location
  tags: tags
}

resource miWorker 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'mi-ns-worker-${environment}'
  location: location
  tags: tags
}

resource miIngestRelay 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'mi-ns-ingest-relay-${environment}'
  location: location
  tags: tags
}

resource miKnowledgeOrchestrator 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'mi-ns-knowledge-${environment}'
  location: location
  tags: tags
}

@description('Capacity-lifecycle identity: capacity-scoped ARM read/write/suspend/resume only (role assignment happens in fabric-capacity.bicep against roles.bicep\'s custom role). Shared by the BFF capacity-operator adapter and the 01:00 Logic App per deployment-topology.md §5.2.')
resource miCapacity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'mi-ns-capacity-${environment}'
  location: location
  tags: tags
}

resource miOtGateway 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = [
  for plant in plants: {
    name: 'mi-ns-otgw-${plant}-${environment}'
    location: location
    tags: tags
  }
]

resource miSimulator 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = if (deploySimulatorIdentity) {
  name: 'mi-ns-demo-simulator-${environment}'
  location: location
  tags: tags
}

resource miGitHubOidc 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = if (deployGitHubOidcIdentity) {
  name: 'mi-ns-cicd-${environment}'
  location: location
  tags: tags
}

// Federated identity credential: trusts only this exact repo + GitHub Environment, never a
// wildcard branch ref. RBAC granted to this identity (in main.bicep) is scoped to this
// environment's resource groups only — never subscription Owner.
resource federatedCredential 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = if (deployGitHubOidcIdentity && !empty(githubOrg) && !empty(githubRepo)) {
  parent: miGitHubOidc
  name: 'github-${githubEnvironmentName}'
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:${githubOrg}/${githubRepo}:environment:${githubEnvironmentName}'
    audiences: [
      'api://AzureADTokenExchange'
    ]
  }
}

output bffPrincipalId string = miBff.properties.principalId
output bffIdentityId string = miBff.id
output workerPrincipalId string = miWorker.properties.principalId
output workerIdentityId string = miWorker.id
output ingestRelayPrincipalId string = miIngestRelay.properties.principalId
output ingestRelayIdentityId string = miIngestRelay.id
output knowledgeOrchestratorPrincipalId string = miKnowledgeOrchestrator.properties.principalId
output knowledgeOrchestratorIdentityId string = miKnowledgeOrchestrator.id
output capacityPrincipalId string = miCapacity.properties.principalId
output capacityIdentityId string = miCapacity.id
output otGatewayIdentities array = [
  for (plant, i) in plants: {
    plant: plant
    principalId: miOtGateway[i].properties.principalId
    identityId: miOtGateway[i].id
  }
]
output simulatorPrincipalId string = deploySimulatorIdentity ? (miSimulator.?properties.?principalId ?? '') : ''
output simulatorIdentityId string = deploySimulatorIdentity ? (miSimulator.?id ?? '') : ''
output gitHubOidcClientId string = deployGitHubOidcIdentity ? (miGitHubOidc.?properties.?clientId ?? '') : ''
output gitHubOidcPrincipalId string = deployGitHubOidcIdentity ? (miGitHubOidc.?properties.?principalId ?? '') : ''
output gitHubOidcIdentityId string = deployGitHubOidcIdentity ? (miGitHubOidc.?id ?? '') : ''
output gitHubFederationConfigured bool = deployGitHubOidcIdentity && !empty(githubOrg) && !empty(githubRepo)
