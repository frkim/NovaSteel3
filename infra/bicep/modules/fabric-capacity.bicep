// Microsoft Fabric capacity — the ONE Microsoft.Fabric ARM resource this repository is allowed to
// declare (implementation-guide.md §9.2: "no infra/bicep template in this repository may declare a
// Microsoft.Fabric item type other than capacities"). Workspaces, Eventstreams, Eventhouses,
// Lakehouses, pipelines, notebooks, the Direct Lake semantic model, and Power BI reports are Fabric
// SaaS-plane items and are explicitly OUT OF SCOPE here — they are provisioned via the Fabric REST
// API / portal / Git integration under fabric/ (owned by a different workstream), never by Bicep.
targetScope = 'resourceGroup'

@description('Capacity resource name, e.g. cap-novasteel-<env>-sc.')
param name string

@description('Azure region. Fabric capacity region availability must be re-verified in the target tenant immediately before deployment (research/fabric-platform.md, research/azure-ai-regions.md) — this template does not guarantee tenant-level quota.')
param location string

@description('Common resource tags. The `expiry` tag is mandatory for demo/dev/test per deployment-topology.md §3.1.')
param tags object

@description('Fabric capacity SKU: F2 (cost-conscious initial demo), F4 (measured contention fallback), or F8 (pre-approved demo-day burst tier). Never default to a larger SKU without a measured/owner-approved reason (deployment-topology.md §6).')
@allowed([
  'F2'
  'F4'
  'F8'
  'F16'
  'F32'
  'F64'
])
param skuName string = 'F2'

@description('At least one Fabric capacity administrator UPN/email is required by the ARM API.')
param adminMembers array

@description('Principal ID of mi-ns-capacity-<env>, granted the custom capacity-operator role (read/write/suspend/resume only) scoped to this exact capacity resource.')
param capacityOperatorPrincipalId string

@description('Resource ID of the roles.bicep custom "NovaSteel Fabric Capacity Operator" role definition.')
param capacityOperatorRoleDefinitionId string

@description('Additional principal IDs (e.g. the 01:00 Logic App system-assigned identity) also granted the capacity-operator role on this resource.')
param additionalOperatorPrincipalIds array = []

resource capacity 'Microsoft.Fabric/capacities@2023-11-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: skuName
    tier: 'Fabric'
  }
  properties: {
    administration: {
      members: adminMembers
    }
  }
}

resource capacityOperatorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(capacityOperatorPrincipalId)) {
  name: guid(capacity.id, capacityOperatorPrincipalId, 'capacity-operator')
  scope: capacity
  properties: {
    principalId: capacityOperatorPrincipalId
    roleDefinitionId: capacityOperatorRoleDefinitionId
    principalType: 'ServicePrincipal'
  }
}

resource additionalOperatorRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for principalId in additionalOperatorPrincipalIds: {
    name: guid(capacity.id, principalId, 'capacity-operator-additional')
    scope: capacity
    properties: {
      principalId: principalId
      roleDefinitionId: capacityOperatorRoleDefinitionId
      principalType: 'ServicePrincipal'
    }
  }
]

output capacityId string = capacity.id
output capacityName string = capacity.name
