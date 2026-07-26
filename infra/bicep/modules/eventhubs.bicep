// Event Hubs namespace for OT telemetry ingestion (deployment-topology.md §3, §3.2). Standard tier
// (minimum SKU that supports Private Endpoints and per-plant consumer groups). One Event Hub per
// plant so each mi-ns-otgw-<plant> identity can be scoped, via a data-plane role assignment on the
// individual Event Hub (not the whole namespace), to only its own plant's data — no SAS keys.
targetScope = 'resourceGroup'

@description('Event Hubs namespace name, e.g. evh-novasteel-<env>-sc.')
param name string

@description('Azure region.')
param location string

@description('Common resource tags.')
param tags object

@description('Per-plant short names; one Event Hub + consumer group is created per entry.')
param plants array

@description('Array of { plant, principalId } for the per-plant OT-gateway managed identities. Each is granted Azure Event Hubs Data Sender scoped to its own plant\'s Event Hub only.')
param otGatewayIdentities array = []

@description('Principal ID of mi-ns-ingest-relay-<env>, granted Azure Event Hubs Data Receiver at the namespace scope (it must read every plant\'s hub to relay into the Fabric Eventstream Custom Endpoint).')
param ingestRelayPrincipalId string

@description('Throughput units / capacity sized from observed load; keep small for demo/dev/test per operations-and-cost.md §8.1.')
param capacityUnits int = 1

@description('Message retention in days per Event Hub (store-and-forward replay window).')
param messageRetentionInDays int = 1

@description('Partition count per Event Hub.')
param partitionCount int = 4

@description('Subnet resource ID hosting the private endpoint.')
param privateEndpointSubnetId string

@description('Private DNS zone resource ID for privatelink.servicebus.windows.net.')
param privateDnsZoneId string

@description('Log Analytics workspace resource ID for diagnostic logs.')
param logAnalyticsWorkspaceId string

var eventHubsDataSenderRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2b629674-e913-4c01-ae53-ef4638d8f975')
var eventHubsDataReceiverRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a638d3c7-ab3a-418d-83e6-5f17a39d4fde')

resource namespace 'Microsoft.EventHub/namespaces@2024-01-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Standard'
    tier: 'Standard'
    capacity: capacityUnits
  }
  properties: {
    disableLocalAuth: true
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Disabled'
    zoneRedundant: false
  }
}

resource eventHubs 'Microsoft.EventHub/namespaces/eventhubs@2024-01-01' = [
  for plant in plants: {
    parent: namespace
    name: 'eh-telemetry-${plant}'
    properties: {
      messageRetentionInDays: messageRetentionInDays
      partitionCount: partitionCount
    }
  }
]

resource consumerGroups 'Microsoft.EventHub/namespaces/eventhubs/consumergroups@2024-01-01' = [
  for (plant, i) in plants: {
    parent: eventHubs[i]
    name: 'cg-ingest-relay'
  }
]

// Per-plant scoped data-sender role assignment — the OT-gateway identity can send only to its own hub.
resource otGatewaySenderRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for og in otGatewayIdentities: {
    name: guid(namespace.id, og.plant, 'data-sender')
    scope: eventHubs[indexOf(plants, og.plant)]
    properties: {
      principalId: og.principalId
      roleDefinitionId: eventHubsDataSenderRoleId
      principalType: 'ServicePrincipal'
    }
  }
]

resource ingestRelayReceiverRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(ingestRelayPrincipalId)) {
  name: guid(namespace.id, 'ingest-relay', 'data-receiver')
  scope: namespace
  properties: {
    principalId: ingestRelayPrincipalId
    roleDefinitionId: eventHubsDataReceiverRoleId
    principalType: 'ServicePrincipal'
  }
}

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-${name}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-${name}-connection'
        properties: {
          privateLinkServiceId: namespace.id
          groupIds: [
            'namespace'
          ]
        }
      }
    ]
  }
}

resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'privatelink-servicebus-windows-net'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: namespace
  name: 'diag-log-analytics'
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

output namespaceId string = namespace.id
output namespaceName string = namespace.name
output eventHubNames array = [for plant in plants: 'eh-telemetry-${plant}']
