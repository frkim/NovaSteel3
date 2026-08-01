// The switch that turns Foundry Agent Service on for the NovaSteel project.
//
// A capability host is what binds a Foundry project to the compute and storage that
// runs agents. Creating the project-level one causes the platform to provision its
// `enterprise_memory` Cosmos database and its agent blob containers using the project
// managed identity, and from that point the project endpoint will accept
// agent/thread/run calls.
//
// Two hard constraints drive the shape of this module:
//
//   * A capability host is immutable. It cannot be repointed at different connections
//     after creation — changing the vector store or thread storage means deleting and
//     recreating it, which destroys existing threads. That is why it is behind the
//     `foundryAgentServiceManuallyValidated` gate rather than deployed by default.
//   * The BYO role assignments must already exist (modules/foundry-agent-rbac.bicep),
//     otherwise provisioning fails partway and leaves an unusable host behind.
//
// Connections are referenced by NAME, not by resource ID — that is the API contract,
// and the names come straight from modules/foundry-agents.bicep outputs.
targetScope = 'resourceGroup'

@description('Name of the Foundry (AIServices) account.')
param foundryAccountName string

@description('Name of the Foundry project that will host the agents.')
param projectName string

@description('Name of the project connection to Azure AI Search (vector store).')
param searchConnectionName string

@description('Name of the project connection to Cosmos DB (thread storage).')
param cosmosConnectionName string

@description('Name of the project connection to the agent storage account (file uploads).')
param storageConnectionName string

@description('''Create the account-level capability host. Exactly one invocation of this
module per Foundry account must set this to true; the account host is shared by every
project on the account, so the second and later invocations pass false and take an
ordering dependency on the first.''')
param deployAccountCapabilityHost bool = true

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: foundryAccountName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' existing = {
  parent: foundryAccount
  name: projectName
}

resource accountCapabilityHost 'Microsoft.CognitiveServices/accounts/capabilityHosts@2025-04-01-preview' = if (deployAccountCapabilityHost) {
  parent: foundryAccount
  name: 'caphost-account'
  properties: {
    capabilityHostKind: 'Agents'
  }
}

resource projectCapabilityHost 'Microsoft.CognitiveServices/accounts/projects/capabilityHosts@2025-04-01-preview' = {
  parent: project
  name: 'caphost-project'
  properties: {
    // The ARM type definition lags the service here; capabilityHostKind is required
    // by the Agent Service standard-setup contract.
    #disable-next-line BCP037
    capabilityHostKind: 'Agents'
    vectorStoreConnections: [
      searchConnectionName
    ]
    threadStorageConnections: [
      cosmosConnectionName
    ]
    storageConnections: [
      storageConnectionName
    ]
  }
  dependsOn: [
    accountCapabilityHost
  ]
}

output projectCapabilityHostId string = projectCapabilityHost.id
