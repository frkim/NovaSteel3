# NovaSteel Azure infrastructure (`infra/`)

Modular Bicep IaC for the NovaSteel platform's Azure control-plane resources, implementing
`docs/architecture/deployment-topology.md`, `docs/architecture/solution-architecture.md` §11–13,
`docs/security/security-governance-and-threat-model.md`, `docs/research/azure-ai-regions.md`, and
`docs/research/fabric-platform.md`. This folder and `tests/infra` are the only paths this
workstream owns — it does not modify `apps/`, `services/`, `simulator/`, `fabric/`, or any
presentation asset.

## Scope discipline

- **Only `Microsoft.Fabric/capacities` is declared.** Fabric workspaces, Eventstreams,
  Eventhouse/KQL, Lakehouses, pipelines, notebooks, the Direct Lake semantic model, and Power BI
  reports are Fabric SaaS-plane items with no supported ARM type — they belong to `fabric/` and
  the Fabric REST API/portal/Git integration (`docs/implementation/implementation-guide.md` §9.2),
  never to this folder. `infra/policy/definitions/deny-unsupported-fabric-items.json` enforces
  this as a policy guardrail.
- **The Foundry Agent Service project is provisioned; only its capability host is gated.**
  `foundry-agents.bicep` creates the Foundry **project**, its BYO ("standard setup")
  connections to AI Search, Cosmos DB and Storage, and the Application Insights connection that
  lights up agent tracing. `foundry-agent-capability-host.bicep` — the resource that actually
  turns Agent Service on — is deployed only when `foundryAgentServiceManuallyValidated=true`,
  because a capability host is **immutable** once created and cannot be repointed at different
  stores. See "Deployment blockers" below. The GPT-5-series chat/reasoning and text-embedding
  model **deployments** the knowledge orchestrator calls live in
  `infra/bicep/modules/foundry-speech.bicep`. Data-plane access is granted as
  `Cognitive Services OpenAI User` (not `Cognitive Services User`), which is the role the
  inference API requires; `disableLocalAuth: true` means there is no key fallback if it is wrong.
- **Agents, search indexes and knowledge bases are data-plane objects.** There is no ARM type
  for a Foundry agent definition, an AI Search index, or a Foundry IQ knowledge base. Bicep
  provisions the accounts, projects, connections, capability hosts, model deployments and RBAC;
  the objects themselves are created at runtime by the knowledge orchestrator against the
  project endpoint and the search endpoint. The index and knowledge-base **names** are outputs of
  `ai-search.bicep` and are the contract between the two halves.
- **Container Apps/Jobs take their images from the `serviceImages` parameter.** When a service
  has no entry, the app falls back to a public sample image
  (`mcr.microsoft.com/k8se/quickstart`). `.github/workflows/ci-build-services.yml` builds the
  real images from each `services/*/Dockerfile`.

## Repository layout

```text
infra/
├── bicep/
│   ├── main.bicep                        # Subscription-scoped orchestrator, one env per run
│   ├── parameters/
│   │   ├── dev.bicepparam
│   │   ├── test.bicepparam
│   │   ├── demo.bicepparam
│   │   └── prod.bicepparam
│   └── modules/
│       ├── roles.bicep                   # Custom "Fabric Capacity Operator" RBAC role
│       ├── network.bicep                 # Hub+spoke VNet, subnets, NSGs, private DNS zones
│       ├── identity.bicep                # Per-service managed identities + GitHub OIDC federation
│       ├── keyvault.bicep                # RBAC-only, private-endpoint-only Key Vault (reusable)
│       ├── storage.bicep                 # Audio/fallback-artifact storage account + Tables (reusable)
│       ├── eventhubs.bicep               # Per-plant Event Hubs + scoped data-plane RBAC
│       ├── fabric-capacity.bicep         # Microsoft.Fabric/capacities (the only Fabric ARM type)
│       ├── containerapps.bicep           # Container Apps environment + placeholder apps/jobs
│       ├── foundry-speech.bicep          # Foundry/Speech accounts + GPT-5-series deployments
│       ├── foundry-agents.bicep          # Foundry project, BYO connections, App Insights link
│       ├── foundry-agent-rbac.bicep      # Cosmos/Storage RBAC for the project identity
│       ├── foundry-agent-capability-host.bicep # Agent Service switch (immutable, quota-gated)
│       ├── appinsights-agent-access.bicep # Cross-RG App Insights reader roles for the project
│       ├── ai-search.bicep               # AI Search service (procedure corpus + Foundry IQ source)
│       ├── cosmos.bicep                  # Cosmos DB for NoSQL — agent thread storage
│       ├── monitoring.bicep              # Log Analytics + App Insights + Sentinel onboarding
│       ├── alerts.bicep                  # Metric/log alert rules + action group
│       ├── logicapp-capacity-lifecycle.bicep  # 01:00 Europe/Luxembourg pause workflow (non-prod)
│       ├── policy-assignments.bicep      # Custom + built-in policy assignments (subscription)
│       └── budget.bicep                  # Per-environment cost budget/alerts
├── policy/
│   ├── README.md
│   └── definitions/*.json                # Custom Azure Policy rule definitions
├── scripts/
│   ├── validate.ps1                      # bicep build + build-params + az deployment sub validate
│   ├── what-if.ps1                       # az deployment sub what-if (PR diff)
│   ├── deploy.ps1                        # az deployment sub create (OIDC only, no secrets)
│   ├── setup-github-oidc-managed-identity.ps1  # RBAC grant for the Bicep-created CI identity
│   └── setup-github-oidc-app-registration.ps1  # TENANT-ADMIN-GATED alternative (manual/dry-run by default)
└── README.md                             # This file
```

## Region model

`main.bicep`'s `location` parameter defaults to `swedencentral` and only otherwise accepts
`westeurope` — the two-value `@allowed()` list is the mechanism satisfying "Sweden Central
default, explicit West Europe contingency" (`deployment-topology.md` §1, §2.2). West Europe is
never silently enabled as a replica; switching to it is a deliberate, reviewed parameter change,
and cross-region replication of `HighlyConfidential` audio/transcript data additionally requires
DPO approval regardless of this parameter (`deployment-topology.md` §2.3).

## Resource groups (per environment)

| Resource group | Contents |
|---|---|
| `rg-ns-<env>-hub` | Hub+spoke VNet, subnets, NSGs, private DNS zones, optional Azure Firewall |
| `rg-ns-<env>-integration` | Event Hubs, OT-gateway Key Vault |
| `rg-ns-<env>-apps` | Managed identities, platform Key Vault, fallback-pack storage, Container Apps environment/apps/jobs |
| `rg-ns-<env>-ai` | Foundry/Speech accounts, Foundry project + Agent Service, AI Search, Cosmos DB agent threads, audio/transcript/agent storage |
| `rg-ns-<env>-fabric` | Fabric capacity, capacity-lifecycle Logic App (non-prod) |
| `rg-ns-<env>-monitoring` | Log Analytics, Application Insights, Sentinel onboarding |

## Usage

```powershell
# 1. Static + ARM validation (safe, read-only)
./infra/scripts/validate.ps1 -Environment dev

# 2. What-if diff (attach to PR per implementation-guide.md §10)
./infra/scripts/what-if.ps1 -Environment dev -OutFile whatif-dev.txt

# 3. Deploy (requires az login or CI OIDC context; confirms before applying)
./infra/scripts/deploy.ps1 -Environment dev
```

All three scripts use whatever Azure CLI/OIDC session is already active — a developer's
`az login`, or the `azure/login@v2` GitHub Action using Workload Identity Federation
(`security-governance-and-threat-model.md` §3.2). **None of them accept or require a client
secret**; `deploy.ps1` actively refuses to run if `AZURE_CLIENT_SECRET`/`AZURE_CREDENTIALS` is set,
to fail closed against an accidental non-OIDC credential path.

### Suggested `cd-infra.yml` shape (documentation only — this repository's `.github/workflows`
is owned by a separate workstream and is not created by this folder)

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    environment: ${{ inputs.environment }}   # dev | test | demo | prod — GitHub Environment gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - run: pwsh ./infra/scripts/validate.ps1 -Environment ${{ inputs.environment }}
      - run: pwsh ./infra/scripts/what-if.ps1 -Environment ${{ inputs.environment }}
      - run: pwsh ./infra/scripts/deploy.ps1 -Environment ${{ inputs.environment }} -Force
```

## GitHub OIDC (Workload Identity Federation)

Two paths are provided; **prefer the first**:

1. **`identity.bicep` (default, no tenant-admin gate)** — creates a user-assigned managed
   identity (`mi-ns-cicd-<env>`) plus a `federatedIdentityCredentials` child resource trusting
   `repo:<githubOrg>/<githubRepo>:environment:<env>`. Both are plain ARM resources; creating them
   requires only Contributor on the resource group, not any Entra tenant-admin/Graph permission.
   After the first (human-run) deployment, run
   `infra/scripts/setup-github-oidc-managed-identity.ps1 -Environment <env>` once to grant that
   identity Contributor on its own environment's 6 resource groups (this RBAC-grant step itself
   requires Owner/User Access Administrator — a privileged but subscription-scoped, not
   tenant-scoped, permission).
2. **`infra/scripts/setup-github-oidc-app-registration.ps1` (tenant-admin-gated alternative)** —
   only if policy specifically requires an Entra App Registration instead of a managed identity.
   Requires the Application Administrator/Cloud Application Administrator Entra role. Runs as a
   dry run by default and only executes Graph calls when invoked with `-Confirm:$true`; never run
   by any automated pipeline.

## Cost tags

Every resource group receives `environment`, `owner`, `costCenter`, `dataClassification`, and
`recoveryTier` tags; `expiry` is additionally required for `dev`/`test`/`demo` (mandatory per
`deployment-topology.md` §3.1) and is enforced both by convention (see the `.bicepparam` files)
and by the `require-tag-expiry` policy assignment when `deployGuardrails=true`. A monthly
`Microsoft.Consumption/budgets` resource (`budget.bicep`) with 50%/80%/100% email alerts covers
each environment's 6 resource groups. **No currency figure in this template is a real price** —
`deployment-topology.md` §6 is explicit that exact regional pricing must be pulled live from the
Azure/Fabric pricing calculator at deployment time, never copied from a document.

## Outputs consumed downstream

`main.bicep` outputs (resource group names, Fabric capacity ID/name, Event Hubs namespace/hub
names, Key Vault URIs, Log Analytics/App Insights IDs, Foundry/Speech endpoints, the Foundry
project endpoint and name, the chat/reasoning deployment names, the AI Search endpoint plus its
procedure index and knowledge-base names, the agent-thread Cosmos account, the GitHub OIDC
client ID, and the Container Apps environment ID) are intended to populate
`fabric/deployment-parameters/<env>.json` (owned by the Fabric workstream) and application
configuration — never a secret value, only resource identifiers/endpoints, consistent with
`implementation-guide.md` §9.3's "no secrets, only identifiers" rule.

## Agent Service and Foundry IQ topology

The "standard" (bring-your-own-storage) Agent Service setup is used rather than the basic one,
so that every byte an agent persists lands in a NovaSteel-owned, private, EU-resident account —
a prerequisite for GDPR erasure and for the residency commitments in
`deployment-topology.md` §2.3. Three modules deploy in a fixed order because the ordering is
load-bearing:

1. `foundry-agents.bicep` — the project, its `CognitiveSearch`/`CosmosDB`/`AzureStorageAccount`
   connections (all `authType: 'AAD'`, no keys) and the account-level `AppInsights` connection.
2. `foundry-agent-rbac.bicep` — Cosmos DB Operator, Cosmos SQL data contributor, Storage Account
   Contributor and Storage Blob Data Owner for the **project's** managed identity.
3. `foundry-agent-capability-host.bicep` — the account- and project-level capability hosts.

Step 2 cannot be merged into step 1 (the project principal ID is only known after step 1) and
must not be merged into step 3: at capability-host creation the platform provisions the
`enterprise_memory` Cosmos database and the agent blob containers *as the project identity*, so
those roles have to exist first. Do not pre-create `enterprise_memory` or its containers.

Observability is wired through the `AppInsights` connection on the **account** (not the project),
which is what populates the Foundry portal's Tracing and Monitoring blades, plus
`appinsights-agent-access.bicep`, which grants the project identity Log Analytics Reader and
Privileged Monitoring Data Reader on the component so the portal can read the traces back. The
component lives in `rg-ns-<env>-monitoring` while the project lives in `rg-ns-<env>-ai`, and a
resource-group-scoped module may only assign roles inside its own resource group — hence the
separate module rather than a few more lines in `foundry-agents.bicep`.

## Deployment blockers / manual gates (must be cleared before go-live, not assumed)

| Gate | Why it cannot be automated here | Where to act |
|---|---|---|
| **Fabric tenant capacity quota/region proof** | `Microsoft.Fabric/capacities` ARM creation can still fail on tenant-level quota/feature availability even though Sweden Central/West Europe are listed regions. | Re-verify in the target tenant immediately before deployment (`docs/research/fabric-platform.md`). |
| **Fabric SaaS-item provisioning** (workspaces, Eventstream, Eventhouse/KQL, Lakehouse, pipelines, notebooks, semantic model, Power BI) | Not ARM resources; Bicep cannot create them by design. | Fabric REST API / portal / Git integration, owned by the `fabric/` workstream, after this template's capacity resource exists. |
| **Microsoft Foundry Agent Service capability host** | The project, its BYO connections and RBAC deploy unconditionally, but a `capabilityHosts` resource is **immutable** — it cannot later be repointed at a different Cosmos/Search/Storage account, so creating it before the stores are final means recreating the project. Regional/tool/model/quota availability is also not guaranteed (`docs/research/azure-ai-regions.md`). | Execute the deployment validation checklist in `azure-ai-regions.md`, confirm the AI Search, Cosmos and agent storage accounts are the ones you intend to keep, then set `foundryAgentServiceManuallyValidated=true`. |
| **AI Search index, Foundry IQ knowledge base, and the agents themselves** | No ARM types exist for these; they are data-plane objects created through the search and project endpoints. | The knowledge orchestrator provisions them at startup (`search_store.py`, `foundry_iq.py`, `agent_service.py`) using its managed identity. Nothing to do in Bicep. |
| **Web IQ / web search grounding** | Web knowledge sources are a First Party Consumption Service: the Microsoft DPA does not apply, data leaves the Azure compliance and geo boundary, and they are unavailable in sovereign clouds — incompatible with NovaSteel's default EU-residency posture. | `onlineSearchMode` defaults to `offline`. Setting `web_iq`/`web_search` requires DPO sign-off; the allowed-domain list is restricted to standards bodies in the orchestrator's configuration. |
| **GitHub repository/environment configuration** | `githubOrg`/`githubRepo` parameters default to empty; the federated credential is only created once both are supplied. | Set the real org/repo in the target environment's `.bicepparam` before deploying, or use `setup-github-oidc-app-registration.ps1` for the alternative path. |
| **Subscription-wide policy guardrails** | `deployGuardrails` defaults to `false` in dev/test/demo parameter files to avoid racy concurrent subscription-scoped writes if multiple environments deploy in parallel. | Deploy exactly one environment (the shipped `prod.bicepparam` sets `deployGuardrails=true`) as the designated governance run, or adjust which environment owns it per your rollout order. |
| **Production onboarding** | Real EU operational/personal data must not flow until DPO/legal, OT, security/RAI, capacity/DR, and source/market-license gates are signed (`deployment-topology.md` §9, `solution-architecture.md` §13 step 8). | Manual governance sign-off; this template does not and cannot certify legal/DPO approval. |
| **Fabric capacity SKU for production** | F2/F4/F8 are the only pre-approved SKUs — F2 is the committed default, F4/F8 are audited demo-day burst tiers reachable from the portal capacity dialog. A production SKU is a measured, pilot-load-tested decision (`deployment-topology.md` §6). | Re-run the measurement described in `docs/research/fabric-platform.md`, then update `fabricSkuName` (and `infra/policy/definitions/restrict-fabric-capacity-sku.json`'s allow-list, `bff_api.capacity.SCALABLE_SKUS`, and `CapacityState.DefaultSkuOptions` — `tests/infra/test_capacity_sku_allow_list.py` pins all four together) as a reviewed change. |
| **West Europe recovery copy** | Any cross-region replication of `HighlyConfidential` data needs DPO approval, retention/encryption controls, and a tested restore runbook — not just a parameter flip. | DPO/legal review per `deployment-topology.md` §2.3, before setting `location=westeurope` for any resource carrying that data class. |
| **First deployment identity** | The very first `main.bicep` run for a new environment must use a human/admin (or already-privileged pipeline) identity, since `mi-ns-cicd-<env>` does not exist yet to bootstrap itself. | Run `deploy.ps1` once as a privileged human/admin, then hand off via `setup-github-oidc-managed-identity.ps1`. |

## Validation performed

- `az bicep build` on every `.bicep` file (zero errors/warnings) — see `infra/scripts/validate.ps1`
  step 1, reproduced in `tests/infra`.
- `az bicep build-params` on every `.bicepparam` file — step 2.
- `tests/infra` (pytest) additionally asserts naming-convention compliance, tag/parameter
  completeness, and that every custom policy JSON file is well-formed and wired into
  `policy-assignments.bicep`.
- `az deployment sub validate` / `what-if` require a live Azure/OIDC session and are therefore
  exercised by the CI pipeline (`cd-infra.yml`), not by this offline task — see "Deployment
  blockers" above for what must additionally be confirmed in the target tenant.
