// Hub-and-spoke networking for one NovaSteel environment.
// Deployed into the rg-ns-<env>-hub resource group. The hub VNet carries both the shared hub
// subnet AND the workload spoke subnets (integration/apps/ai-private-endpoints) in a single VNet
// to keep this template's blast radius small for a cost-conscious demo/dev/test footprint; the
// functional resource groups referenced in deployment-topology.md §3.2 (integration/apps/ai) still
// host their own PaaS resources and private endpoints — those resources simply attach to a subnet
// ID that lives in this shared network resource group, which is a supported, common Azure pattern
// (a subnet's resource group need not match the private endpoint's resource group).
// A true multi-VNet hub+peered-spoke topology with Azure Firewall is offered behind
// `deployFirewall`/`deploySpokeVnetPeering` for environments (typically prod) that require it.
targetScope = 'resourceGroup'

@description('Environment short name: dev, test, demo, prod.')
param environment string

@description('Azure region for all network resources (Sweden Central by default, West Europe as the documented contingency).')
param location string

@description('Common resource tags.')
param tags object

@description('Address space for the shared hub+spoke VNet.')
param vnetAddressPrefix string = '10.20.0.0/16'

@description('Subnet address prefixes, keyed by subnet purpose.')
param subnetPrefixes object = {
  hubServices: '10.20.0.0/24'
  integration: '10.20.1.0/24'
  apps: '10.20.2.0/24'
  aiPrivateEndpoints: '10.20.3.0/24'
  containerAppsInfra: '10.20.4.0/23'
}

@description('Deploy Azure Firewall in the hub subnet for egress allow-listing. Disabled by default to control cost for demo/dev/test; enable explicitly for prod after a cost/owner review (operations-and-cost.md §8).')
param deployFirewall bool = false

@description('Log Analytics workspace resource ID for NSG diagnostic settings.')
param logAnalyticsWorkspaceId string

var nsgRules = {
  denyInternetInbound: {
    name: 'Deny-Internet-Inbound'
    properties: {
      priority: 4096
      direction: 'Inbound'
      access: 'Deny'
      protocol: '*'
      sourceAddressPrefix: 'Internet'
      sourcePortRange: '*'
      destinationAddressPrefix: '*'
      destinationPortRange: '*'
    }
  }
}

resource nsgHubServices 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: 'nsg-ns-${environment}-hub-services'
  location: location
  tags: tags
  properties: {
    securityRules: [
      nsgRules.denyInternetInbound
    ]
  }
}

resource nsgIntegration 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: 'nsg-ns-${environment}-integration'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'Allow-OT-Gateway-EventHubs-Outbound-443'
        properties: {
          priority: 100
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: subnetPrefixes.integration
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '443'
        }
      }
      nsgRules.denyInternetInbound
    ]
  }
}

resource nsgApps 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: 'nsg-ns-${environment}-apps'
  location: location
  tags: tags
  properties: {
    securityRules: [
      nsgRules.denyInternetInbound
    ]
  }
}

resource nsgAi 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: 'nsg-ns-${environment}-ai-private-endpoints'
  location: location
  tags: tags
  properties: {
    securityRules: [
      nsgRules.denyInternetInbound
    ]
  }
}

resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: 'vnet-ns-${environment}-hub'
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressPrefix
      ]
    }
    subnets: [
      {
        name: 'snet-hub-services'
        properties: {
          addressPrefix: subnetPrefixes.hubServices
          networkSecurityGroup: {
            id: nsgHubServices.id
          }
        }
      }
      {
        name: 'snet-integration'
        properties: {
          addressPrefix: subnetPrefixes.integration
          networkSecurityGroup: {
            id: nsgIntegration.id
          }
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'snet-apps'
        properties: {
          addressPrefix: subnetPrefixes.apps
          networkSecurityGroup: {
            id: nsgApps.id
          }
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'snet-ai-private-endpoints'
        properties: {
          addressPrefix: subnetPrefixes.aiPrivateEndpoints
          networkSecurityGroup: {
            id: nsgAi.id
          }
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'snet-container-apps-infra'
        properties: {
          addressPrefix: subnetPrefixes.containerAppsInfra
          networkSecurityGroup: {
            id: nsgApps.id
          }
        }
      }
    ]
  }
}

// Azure Firewall (optional, cost-gated). Provides egress allow-listing for the protected package
// feed and any approved external SaaS endpoint per security-governance-and-threat-model.md §4.1.
resource firewallPip 'Microsoft.Network/publicIPAddresses@2023-11-01' = if (deployFirewall) {
  name: 'pip-ns-${environment}-firewall'
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource firewallSubnet 'Microsoft.Network/virtualNetworks/subnets@2023-11-01' = if (deployFirewall) {
  parent: vnet
  name: 'AzureFirewallSubnet'
  properties: {
    addressPrefix: '10.20.255.0/26'
  }
}

resource firewall 'Microsoft.Network/azureFirewalls@2023-11-01' = if (deployFirewall) {
  name: 'fw-ns-${environment}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'AZFW_VNet'
      tier: 'Standard'
    }
    ipConfigurations: [
      {
        name: 'fw-ipconfig'
        properties: {
          subnet: {
            id: firewallSubnet.id
          }
          publicIPAddress: {
            id: firewallPip.id
          }
        }
      }
    ]
  }
}

// Private DNS zones for every PaaS private endpoint used across modules (Key Vault, Storage,
// Event Hubs, Cognitive Services/Speech/Foundry, Azure AI Search, Cosmos DB) — centralized in the hub per
// security-governance-and-threat-model.md §4.1 ("Centralized Private DNS zones"). These are
// Microsoft's fixed private-link DNS zone names (identical across environments), not
// environment-specific endpoints, so they are intentionally hardcoded rather than derived from
// the environment() function.
#disable-next-line no-hardcoded-env-urls
var privateDnsZoneNames = [
  'privatelink.vaultcore.azure.net'
  #disable-next-line no-hardcoded-env-urls
  'privatelink.blob.core.windows.net'
  'privatelink.servicebus.windows.net'
  'privatelink.cognitiveservices.azure.com'
  'privatelink.openai.azure.com'
  // A Foundry (AIServices) account private endpoint registers records in all three
  // Cognitive Services zones. This one carries the Foundry-model hostname
  // `<account>.services.ai.azure.com`, which is what serves the project endpoint
  // (`/api/projects/<project>`) and the OpenAI v1 route. Without it the account is
  // reachable only on its legacy `cognitiveservices.azure.com` name and every
  // Agent Service call from the VNet fails to resolve.
  'privatelink.services.ai.azure.com'
  'privatelink.azurecr.io'
  #disable-next-line no-hardcoded-env-urls
  'privatelink.table.core.windows.net'
  'privatelink.search.windows.net'
  'privatelink.documents.azure.com'
]

resource privateDnsZones 'Microsoft.Network/privateDnsZones@2024-06-01' = [
  for zoneName in privateDnsZoneNames: {
    name: zoneName
    location: 'global'
    tags: tags
  }
]

resource privateDnsZoneLinks 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = [
  for (zoneName, i) in privateDnsZoneNames: {
    parent: privateDnsZones[i]
    name: 'link-${vnet.name}'
    location: 'global'
    properties: {
      registrationEnabled: false
      virtualNetwork: {
        id: vnet.id
      }
    }
  }
]

resource nsgDiagHubServices 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: nsgHubServices
  name: 'diag-log-analytics'
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
  }
}

output vnetId string = vnet.id
output vnetName string = vnet.name
output subnetIds object = {
  hubServices: vnet.properties.subnets[0].id
  integration: vnet.properties.subnets[1].id
  apps: vnet.properties.subnets[2].id
  aiPrivateEndpoints: vnet.properties.subnets[3].id
  containerAppsInfra: vnet.properties.subnets[4].id
}
output privateDnsZoneIds object = {
  keyVault: privateDnsZones[0].id
  blob: privateDnsZones[1].id
  serviceBus: privateDnsZones[2].id
  cognitiveServices: privateDnsZones[3].id
  openAi: privateDnsZones[4].id
  aiServices: privateDnsZones[5].id
  containerRegistry: privateDnsZones[6].id
  table: privateDnsZones[7].id
  search: privateDnsZones[8].id
  cosmosDb: privateDnsZones[9].id
}
