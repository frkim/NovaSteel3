# NovaSteel v3 isolated demo infrastructure

This directory is a standalone, subscription-scoped Bicep deployment for the approved
`rg-novasteelv3-demo-sc` estate in Contoso Fx
(`3377065c-bf76-4767-a982-32bce4ffb592`). The template only permits
`swedencentral` and the approved resource group; it never targets
`rg-novasteel-dev`.

## Contents

- `main.bicep` creates the resource group, a tightly scoped Fabric pause-only role,
  and composes the modules.
- `modules/platform.bicep` provisions the cost-optimized platform: Basic ACR with
  admin disabled, managed environment, two user-assigned identities and `AcrPull`,
  Fabric F2, Event Hubs, LRS storage, Key Vault, monitoring, optional AI/Speech,
  and the 01:00 Europe/Luxembourg capacity-pause Logic App.
- `modules/apps.bicep` creates external HTTPS portal and BFF Container Apps only
  when `deployApps=true`. Both use port 8080, managed identity registry pulls,
  health probes, and scale-to-zero bounds.
- `modules/budget.bicep` creates an optional budget only after a reviewed amount is
  deliberately enabled.

## Phased workflow

1. Run `..\scripts\Test-NovaSteelDemoInfrastructure.ps1`.
2. Run `..\scripts\Invoke-NovaSteelDemoDeployment.ps1 -Phase Bootstrap` to deploy
   the platform with `deployApps=false`.
3. Build and push immutable portal/BFF images through the separately owned
   packaging workflow. This directory does not create or modify `.azure\docker`.
4. Run `Invoke-NovaSteelDemoDeployment.ps1 -Phase Apps` with full ACR digest image
   references. The script verifies both images exist, deploys the apps, obtains
   their managed HTTPS hostnames, and redeploys their CORS/runtime configuration.

`Invoke-NovaSteelDemoWhatIf.ps1` is read-only and defaults to
`deployApps=false`, so its placeholder image references are never pulled.

### Image contract for the separately owned packaging work

Both images must listen on port `8080`. The BFF must serve `/health/live` and
`/health/ready`; the portal must return `200` at `/`. The portal runtime wrapper
must consume `BFF_BASE_URL` (and may consume the synonymous
`PORTAL_BFF_BASE_URL`) so the Apps phase can inject the managed BFF HTTPS URL.
The BFF receives the exact portal HTTPS origin through `BFF_CORS_ORIGINS`.

## Security and cost choices

- ACR admin credentials and local shared-key access are disabled.
- Container Apps use separate user-assigned identities; the BFF receives only
  resource-scoped Key Vault, Storage Blob, and Event Hubs RBAC.
- The Logic App has a system identity and a custom Fabric-suspend-only role
  assignable solely inside the demo resource group.
- Storage is `Standard_LRS`; Log Analytics uses 30-day retention with a 1 GB/day
  cap; Container Apps scale from zero; Event Hubs uses one Standard capacity unit,
  one partition, and one-day retention.
- AI Services and Speech are disabled by default and must be explicitly enabled
  after Sweden Central availability is reconfirmed.

The root deployment outputs resource IDs, names, and non-secret hostnames. It does
not output ACR credentials, storage keys, Key Vault secrets, or Application Insights
connection strings.
