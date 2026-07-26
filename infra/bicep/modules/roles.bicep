// Custom RBAC role definitions for NovaSteel.
// Subscription-scoped (role definitions must be defined above the scopes they can be assigned to).
// Deployed once per subscription; role ASSIGNMENTS (which resource-group/resource each identity
// actually gets) happen in the consuming modules (fabric-capacity.bicep, logicapp-capacity-lifecycle.bicep).
targetScope = 'subscription'

@description('Short environment token used to keep role definition names/GUIDs stable per environment while still unique per subscription (dev/test/demo/prod each get their own definition so assignableScopes can be scoped tightly).')
param environment string

@description('Resource ID of the rg-ns-<env>-fabric resource group. The capacity-operator role is assignable only inside this resource group.')
param fabricResourceGroupId string

// Deterministic GUID so re-deploying does not create duplicate role definitions.
var capacityOperatorRoleName = 'NovaSteel Fabric Capacity Operator (${environment})'
var capacityOperatorRoleGuid = guid(subscription().id, 'novasteel-fabric-capacity-operator', environment)

@description('Custom role: capacity-only ARM lifecycle actions. No Fabric workspace/OneLake/Key Vault/subscription-wide access is granted by this role — matches security-governance-and-threat-model.md §3 and deployment-topology.md §5.2 ("Capacity ARM permissions do not grant data-plane access").')
resource capacityOperatorRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: capacityOperatorRoleGuid
  properties: {
    roleName: capacityOperatorRoleName
    description: 'Read/write/suspend/resume a single Microsoft.Fabric capacity resource only. Used by mi-ns-capacity-<env> and the 01:00 lifecycle Logic App. Never grants Fabric workspace, OneLake, Key Vault secret, or subscription Contributor access.'
    type: 'CustomRole'
    permissions: [
      {
        actions: [
          'Microsoft.Fabric/capacities/read'
          'Microsoft.Fabric/capacities/write'
          'Microsoft.Fabric/capacities/suspend/action'
          'Microsoft.Fabric/capacities/resume/action'
        ]
        notActions: []
        dataActions: []
        notDataActions: []
      }
    ]
    assignableScopes: [
      fabricResourceGroupId
    ]
  }
}

output capacityOperatorRoleId string = capacityOperatorRole.id
output capacityOperatorRoleName string = capacityOperatorRoleName
