# NovaSteel infra/policy — guardrail definitions

This folder holds the **source-of-truth JSON** for NovaSteel's custom Azure Policy definitions.
They are loaded into Bicep via `loadJsonContent()` from
`infra/bicep/modules/policy-assignments.bicep`, which also assigns them (plus relevant built-in
policies) at subscription scope. Keeping the `policyRule` JSON here — rather than inlined in
Bicep — lets a security/compliance reviewer read and diff the actual policy logic without also
reading Bicep module wiring.

## Definitions

| File | Guardrail | Default effect | Rationale |
|---|---|---|---|
| `definitions/deny-unsupported-fabric-items.json` | Denies any `Microsoft.Fabric/*` ARM resource type other than `Microsoft.Fabric/capacities`. | `Deny` | Fabric workspaces, Eventstreams, Eventhouses, Lakehouses, pipelines, notebooks, the Direct Lake semantic model, and Power BI reports are Fabric **SaaS-plane** items with no supported ARM resource type today (`docs/implementation/implementation-guide.md` §9.2). This policy is defense-in-depth: if a future preview ARM type appears under `Microsoft.Fabric`, it cannot be silently deployed without a deliberate policy update. |
| `definitions/deny-public-network-access.json` | Denies `publicNetworkAccess != 'Disabled'` on Key Vault, Storage, Event Hubs namespaces, and Cognitive Services (Foundry/Speech) accounts. | `Deny` | `docs/security/security-governance-and-threat-model.md` §4.1: "Public network access is disabled on Azure resources except where a documented exception exists." |
| `definitions/restrict-fabric-capacity-sku.json` | Restricts `Microsoft.Fabric/capacities` SKU to an approved list (default `F2`, `F4`). | `Audit` (see note below) | `docs/architecture/deployment-topology.md` §6: "F4 only on measured contention; production SKU after pilot load test." Kept as `Audit` rather than `Deny` by default because `Microsoft.Fabric/capacities` does not publish resource-provider-declared policy aliases at authoring time (verified via `az provider show --namespace Microsoft.Fabric`) — **re-verify `sku.name` alias support in the target tenant before switching this to `Deny`.** |

Built-in policies referenced (not reinvented) by `policy-assignments.bicep`:

- **Allowed locations** (`e56962a6-4747-49cd-b67b-bf8b01975c4c`) — restricts every resource to `swedencentral`/`westeurope` only, operationalizing the "Sweden Central default, explicit West Europe contingency" rule.
- **Require a tag on resources** (`1e30110a-5ceb-460c-a204-c1c3969c6d62`) — assigned once per mandatory tag key (`environment`, `dataClassification`, `owner`, `costCenter`, and `expiry` for non-prod).

## Deployment-time singleton

Policy **definitions and assignments in this folder are subscription-wide, not per-environment**.
`policy-assignments.bicep` exposes a `deployGuardrails` parameter; **only one environment's
pipeline should set it `true`** (see `infra/bicep/parameters/prod.bicepparam`, which is the
designated authoritative run in the shipped parameter files) to avoid redundant/racy concurrent
writes to the same subscription-scoped assignment from multiple environment deployments.

## Adding a new guardrail

1. Author the policy definition as a plain ARM `policyRule` JSON file under `definitions/`, with a
   `metadata.source` field citing the requirement doc/section it operationalizes.
2. Add a `Microsoft.Authorization/policyDefinitions` resource in `policy-assignments.bicep` that
   loads it via `loadJsonContent('../../policy/definitions/<file>.json').properties`.
3. Add a corresponding `Microsoft.Authorization/policyAssignments` resource, defaulting to
   `Audit` unless the underlying resource-provider alias support has been positively verified for
   `Deny`.
4. Validate with `infra/scripts/validate.ps1 -Environment <env>` (runs `bicep build` on this
   module) and `tests/infra` (asserts every `definitions/*.json` file is well-formed and every
   referenced file actually exists).
