# Automation support and manual gates

The catalog deliberately distinguishes an API being available from a solution
being safe to automate.

## Automated by `scripts/Deploy-FabricAssets.ps1`

1. Acquire a Fabric API token from the existing Azure CLI user/managed-identity
   context.
2. Find or create the four environment workspaces and assign the configured
   Fabric capacity GUID.
3. Find or create REST-supported items by `(workspace, type, displayName)`.
4. Base64-encode source definition parts and replace only catalogued
   `{{...}}` identifiers.
5. Update existing definitions rather than creating duplicate items.
6. Poll Fabric long-running operations and respect `Retry-After`.
7. Write an identifier-only deployment state file under
   `fabric/deployment-state/`.

The script never deletes an item, source data, audit fact, or workspace.

## Optional Fabric CLI automation

`Deploy-FabricDefinitionsWithCli.ps1` imports already-rendered, definition-capable
items with `fab import`, then verifies them with `fab exists`. It is an
alternative definition transport after REST workspace/container bootstrap. It
supports an existing `fab` login or `fab auth login --identity`; it has no
secret/client-password mode.

`fab acl set` can apply the configured ingress publisher object ID as
`contributor` to the RTI-Ingress workspace. The script contains no code path
that applies that publisher to DataCore, ML, Analytics, or production.

## Portal or tenant-admin gates

- Enable the tenant settings that permit the selected service principal or
  managed identity to use Fabric APIs and, when required, create workspaces.
- Assign capacity permissions and ensure the F capacity is running.
- Approve OneLake security roles, sensitivity labels, Purview lineage, and
  tenant DLP policy.
- Retrieve/test the Eventstream Custom Endpoint connection details. These are
  runtime-generated endpoint details and are not committed here.
- Create and permission source connections for MES/LIMS/CMMS/market copies.
  Only connection IDs belong in environment parameters; credentials remain in
  the tenant connection/Key Vault boundary.
- Validate a tenant-bound Direct Lake binding and RLS before semantic model
  deployment is enabled.
- Build/import KQL Dashboard, Activator, and PBIR definitions only after a
  tenant export proves the current definition format.

## Bicep non-claim

No file under `fabric/` claims that Bicep deploys Fabric SaaS-plane items.
Bicep remains appropriate for the Azure Fabric capacity, managed identities,
Logic App resource, networking, Event Hubs, monitoring, and policy resources
owned by the infrastructure workstream.
