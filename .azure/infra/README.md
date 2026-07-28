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
  Fabric F2, Event Hubs, LRS storage, Key Vault, monitoring, optional AI/Speech
  plus their optional GPT-5-series model deployments, and the 01:00
  Europe/Luxembourg capacity-pause Logic App.
- `modules/agent-platform.bicep` provisions the optional agent estate: Azure AI
  Search (procedure corpus and Foundry IQ source), serverless Cosmos DB (agent
  thread storage), the Foundry project with its bring-your-own-storage
  connections, the Application Insights connection that carries agent traces, the
  project RBAC, and the Agent Service capability hosts.
- `modules/apps.bicep` creates external HTTPS portal and BFF Container Apps only
  when `deployApps=true`. Both use port 8080, managed identity registry pulls,
  health probes, and scale-to-zero bounds.
- `modules/budget.bicep` creates an optional budget only after a reviewed amount is
  deliberately enabled.

## AI and agent feature flags

Everything AI-related is opt-in, and each flag is separate because each one carries
a different kind of risk. All default to `false`.

| Flag | Creates | Why it is separate |
|---|---|---|
| `deployAiServices` | AI Services + Speech S0 accounts | Sweden Central availability must be reconfirmed. |
| `deployModelDeployments` | `gpt-5.4-mini`, `gpt-5.5`, `text-embedding-3-large` | Model availability and **quota** are per-subscription and can fail independently of the account. Billed per token, so there is no idle cost. |
| `deployAgentPlatform` | AI Search, Cosmos DB, Foundry project, connections, RBAC | AI Search `basic` is a **fixed monthly charge whether or not it is queried** — the only always-on cost here. Cosmos is serverless and idles near zero. |
| `agentServiceManuallyValidated` | Account + project capability hosts | A capability host is **immutable**: it cannot later be repointed at a different Search/Cosmos/Storage account. Changing them means recreating the project. |

Without `deployModelDeployments` the AI Services account has no deployments, so the
Copilot chat and knowledge features fall back to deterministic local fixtures. That
is a working demo, but it is not exercising Foundry.

`deployAgentPlatform` requires `deployAiServices`, since the Foundry project is a
child of the AI Services account and AI Search needs the embedding deployment for
integrated vectorization.

`onlineSearchMode` defaults to `offline` and must stay there without DPO sign-off:
Web IQ and web search are First Party Consumption Services, so the Microsoft DPA
does not apply and queries leave the Azure compliance and geo boundary.

### Ordering inside the agent module

The project, its RBAC, and the capability hosts deploy in that order, and the order
is load-bearing rather than stylistic: at capability-host creation the platform
provisions the `enterprise_memory` Cosmos database and the agent blob containers
*using the project's own managed identity*, so those role assignments must already
exist. Do not pre-create that database or those containers.

Agents, search indexes and Foundry IQ knowledge bases have no ARM types at all —
they are data-plane objects the knowledge orchestrator creates at runtime through
the project and search endpoints. This template deploys everything underneath them
and exposes the endpoints and index/knowledge-base names as outputs.

### Known drift to check before deploying

The live AI Services account carries a `SecurityControl: Ignore` tag. It is applied
automatically by the subscription-scoped `Add SecurityControl=Ignore tag` Modify
policy, so it is governance-driven rather than manual drift. The template
reapplies it with `union()` so a redeploy neither strips it nor reports it as a
difference.

### The Fabric capacity must be resumed before any deployment

The estate parks `novasteelv3fabric` every night at 01:00 Europe/Luxembourg via
the `novasteelv3-capacity-pause` Logic App, and ARM rejects updates to a paused
capacity with `BadRequest - "Service is not ready to be updated"`. Any redeploy
during the paused window therefore fails on the `novasteelv3-platform`
deployment, regardless of what changed. Resume it first, wait for
`properties.state` to read `Active`, then deploy:

```powershell
$capacityId = "/subscriptions/<sub>/resourceGroups/rg-novasteelv3-demo-sc/providers/Microsoft.Fabric/capacities/novasteelv3fabric"
az resource invoke-action --action resume --ids $capacityId
az resource show --ids $capacityId --query "properties.state" -o tsv
```

Pause it again afterwards (`--action suspend`) so the cost cap is restored,
unless the nightly Logic App run is imminent.

### Cosmos public network access is reverted by policy on every deployment

`cosmosdb_publicnetwork_modify`, a **Modify** policy assigned at management-group
scope (part of *MCAPSGov Deploy and Modify Policies*), forces
`publicNetworkAccess: Disabled` on every write to a Cosmos account. This template
asks for `Enabled`, and the policy overrides it every time.

This matters because the Foundry Agent Service reaches its bring-your-own thread
storage over the **public** endpoint in this estate — there is no VNet-integrated
capability host here. While Cosmos is `Disabled`, creating an agent fails with:

```
cosmos_vnet_blocked: Access to Cosmos DB is blocked due to VNET configuration.
```

The infrastructure is otherwise healthy: the capability hosts, connections and
RBAC are all correct, so the failure appears only at first agent use.

The durable fix is a **policy exemption** for this Cosmos account, requested
through the normal governance process — not a scripted override, which would
silently defeat a corporate security control. Until the exemption exists, an
operator must re-enable public access by hand after each deployment:

```powershell
az cosmosdb update -g rg-novasteelv3-demo-sc -n novasteelv3-cosmos-nofkol6a `
  --public-network-access ENABLED
```

The alternative, and the better long-term answer, is to move the estate to the
private-networking Agent Service topology used by `infra/bicep`, which keeps
Cosmos private and satisfies the policy as written.

### The `SecurityControl: Ignore` tag comes from policy, not from a person

An `Add SecurityControl=Ignore tag` Modify policy is assigned at subscription
scope and applies this tag automatically. The template reapplies it via `union()`
so that a redeploy does not show it as drift; there is no tag owner to consult.

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
  after Sweden Central availability is reconfirmed. The model deployments and the
  agent estate (AI Search, Cosmos, Foundry project) are separately gated again —
  see "AI and agent feature flags" above.
- AI Search and Cosmos DB are keyless (`disableLocalAuth`) and Entra-only, matching
  the posture of the rest of this estate. Unlike the production template in
  `infra/bicep/`, they are reachable over the public endpoint rather than through
  private endpoints; this estate carries synthetic demo data only.

The root deployment outputs resource IDs, names, and non-secret hostnames. It does
not output ACR credentials, storage keys, Key Vault secrets, or Application Insights
connection strings.
