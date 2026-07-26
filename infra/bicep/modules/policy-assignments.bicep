// NovaSteel custom policy definitions + assignments — both SUBSCRIPTION-scoped and therefore
// subscription-wide singletons, independent of any single environment. Definitions load their
// policyRule/parameters from infra/policy/definitions/*.json so the JSON stays reviewable
// independent of Bicep. Built-in policies (allowed locations, required tags) are referenced by ID
// rather than reinvented.
//
// IMPORTANT: only ONE environment pipeline should set `deployGuardrails = true` (typically the
// governance/platform deployment, or the first environment stood up) to avoid redundant/racy
// concurrent writes to the same subscription-scoped assignment from multiple environment
// pipelines running in parallel. Re-running it is idempotent (last writer wins on identical
// content), but concurrent *different* content would race — coordinate via change process.
targetScope = 'subscription'

@description('Whether this deployment should (re-)apply the subscription-wide guardrails. Set false for every environment pipeline except the one designated as authoritative for governance.')
param deployGuardrails bool = true

@description('Allowed Azure regions: Sweden Central primary, West Europe explicit contingency only (deployment-topology.md §1, §2.2). No other region is permitted by policy.')
param allowedLocations array = [
  'swedencentral'
  'westeurope'
]

@description('Mandatory tag keys enforced on every resource in scope (deployment-topology.md §3.1).')
param mandatoryTags array = [
  'environment'
  'dataClassification'
  'owner'
  'costCenter'
]

@description('Enforce the `expiry` tag as well — mandatory for demo/dev/test (deployment-topology.md §3.1), optional for prod.')
param enforceExpiryTag bool = true

@description('Effect for the Fabric SaaS-item guardrail policy.')
@allowed([
  'Deny'
  'Audit'
  'Disabled'
])
param fabricItemGuardrailEffect string = 'Deny'

@description('Effect for the public-network-access guardrail policy.')
@allowed([
  'Deny'
  'Audit'
  'Disabled'
])
param publicNetworkGuardrailEffect string = 'Deny'

@description('Effect for the Fabric capacity SKU guardrail policy. Kept as Audit by default because Azure Policy alias support for Microsoft.Fabric/capacities/sku.name should be reverified in the target tenant before switching to Deny (this resource type does not publish RP-declared aliases at authoring time).')
@allowed([
  'Deny'
  'Audit'
  'Disabled'
])
param fabricSkuGuardrailEffect string = 'Audit'

@description('Fabric capacity SKUs allowed before a reviewed change is required.')
param allowedFabricSkus array = [
  'F2'
  'F4'
]

var builtInAllowedLocationsPolicyId = '/providers/Microsoft.Authorization/policyDefinitions/e56962a6-4747-49cd-b67b-bf8b01975c4c'
var builtInRequireTagPolicyId = '/providers/Microsoft.Authorization/policyDefinitions/1e30110a-5ceb-460c-a204-c1c3969c6d62'

resource denyUnsupportedFabricItems 'Microsoft.Authorization/policyDefinitions@2021-06-01' = if (deployGuardrails) {
  name: 'novasteel-deny-unsupported-fabric-items'
  properties: loadJsonContent('../../policy/definitions/deny-unsupported-fabric-items.json').properties
}

resource denyPublicNetworkAccess 'Microsoft.Authorization/policyDefinitions@2021-06-01' = if (deployGuardrails) {
  name: 'novasteel-deny-public-network-access'
  properties: loadJsonContent('../../policy/definitions/deny-public-network-access.json').properties
}

resource restrictFabricCapacitySku 'Microsoft.Authorization/policyDefinitions@2021-06-01' = if (deployGuardrails) {
  name: 'novasteel-restrict-fabric-capacity-sku'
  properties: loadJsonContent('../../policy/definitions/restrict-fabric-capacity-sku.json').properties
}

resource allowedLocationsAssignment 'Microsoft.Authorization/policyAssignments@2022-06-01' = if (deployGuardrails) {
  name: 'novasteel-allowed-locations'
  properties: {
    displayName: 'NovaSteel: allowed locations (Sweden Central / West Europe)'
    policyDefinitionId: builtInAllowedLocationsPolicyId
    parameters: {
      listOfAllowedLocations: {
        value: allowedLocations
      }
    }
  }
}

resource requiredTagAssignments 'Microsoft.Authorization/policyAssignments@2022-06-01' = [
  for tagName in mandatoryTags: if (deployGuardrails) {
    name: 'novasteel-require-tag-${tagName}'
    properties: {
      displayName: 'NovaSteel: require tag "${tagName}"'
      policyDefinitionId: builtInRequireTagPolicyId
      parameters: {
        tagName: {
          value: tagName
        }
      }
    }
  }
]

resource requireExpiryTagAssignment 'Microsoft.Authorization/policyAssignments@2022-06-01' = if (deployGuardrails && enforceExpiryTag) {
  name: 'novasteel-require-tag-expiry'
  properties: {
    displayName: 'NovaSteel: require tag "expiry" (mandatory for non-prod)'
    policyDefinitionId: builtInRequireTagPolicyId
    parameters: {
      tagName: {
        value: 'expiry'
      }
    }
  }
}

resource fabricItemGuardrailAssignment 'Microsoft.Authorization/policyAssignments@2022-06-01' = if (deployGuardrails) {
  name: 'novasteel-fabric-items'
  properties: {
    displayName: 'NovaSteel: no unsupported Microsoft.Fabric ARM item types'
    policyDefinitionId: denyUnsupportedFabricItems.id
    parameters: {
      effect: {
        value: fabricItemGuardrailEffect
      }
    }
  }
}

resource publicNetworkGuardrailAssignment 'Microsoft.Authorization/policyAssignments@2022-06-01' = if (deployGuardrails) {
  name: 'novasteel-no-public-network'
  properties: {
    displayName: 'NovaSteel: deny public network access on data-plane PaaS'
    policyDefinitionId: denyPublicNetworkAccess.id
    parameters: {
      effect: {
        value: publicNetworkGuardrailEffect
      }
    }
  }
}

resource fabricSkuGuardrailAssignment 'Microsoft.Authorization/policyAssignments@2022-06-01' = if (deployGuardrails) {
  name: 'novasteel-fabric-sku'
  properties: {
    displayName: 'NovaSteel: restrict Fabric capacity SKU'
    policyDefinitionId: restrictFabricCapacitySku.id
    parameters: {
      effect: {
        value: fabricSkuGuardrailEffect
      }
      allowedSkus: {
        value: allowedFabricSkus
      }
    }
  }
}

output policyDefinitionIds object = deployGuardrails ? {
  fabricItems: denyUnsupportedFabricItems.id
  publicNetworkAccess: denyPublicNetworkAccess.id
  fabricSku: restrictFabricCapacitySku.id
} : {}
