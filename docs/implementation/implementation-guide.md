# NovaSteel — Implementation Guide

> **Status:** Implemented local baseline and deployment guide v1.1
> **Date:** 2026-07-25
> **Authoritative source:** [`solution-architecture.md`](../architecture/solution-architecture.md) and [`deployment-topology.md`](../architecture/deployment-topology.md). Where any other document (UX, security, data, demo, research) appears to conflict with those two files, the architecture wins. This guide operationalizes the architecture into a buildable repository, backlog, CI/CD pipeline, and delivery sequence. It introduces no new architectural decisions.
> **Owning todo:** `implementation-pack`
> **Companions:** [`api-contracts.md`](api-contracts.md), [`../operations/operations-and-cost.md`](../operations/operations-and-cost.md)

## 0. How to use this guide

This document originated as the engineering-fleet build plan. Its local
implementation scope is now delivered: application, simulator, contracts,
tests/CI, IaC, Fabric source assets, and the deterministic defense are present.
Retain the numbered contracts and backlog as traceability for maintenance and
cloud rollout. The remaining forward-looking work is tenant deployment and the
production gates in Sections 9, 15, and 16—not a missing local implementation.

Every command, config snippet, and package reference in this document uses **only** the Microsoft-protected package feeds mandated by `docs/tech/security_requirement.md` and operationalized in `docs/security/security-governance-and-threat-model.md` §19:

- Python/pip: `https://packagefeedproxy.microsoft.io/pypi/simple`
- .NET/NuGet: `https://packagefeedproxy.microsoft.io/nuget/v3/index.json`

**No command in this document may fall back to `pypi.org`, `files.pythonhosted.org`, `nuget.org`, or `api.nuget.org`.** JavaScript/npm package acquisition must use the equivalent organization-approved protected feed configured by the same convention (an `.npmrc` pointing only at the approved proxy registry); this guide does not invent an npm feed URL because none is documented in the source material — the CI/CD template in §11 leaves an explicit placeholder that must be filled from the same Central Feed Services (CFS) guidance before the frontend pipeline is enabled.

---

## 1. Monorepo topology

The repository is a single monorepo, matching the buildable repository topology approved in `solution-architecture.md` §11, reproduced here with exact ownership and language per folder:

```text
/
├── apps/
│   ├── portal-shell/                 # C# / Blazor WebAssembly host: MSAL, routing, theme/locale, typed interop bridge
│   └── analytics-mfe/                # TypeScript / React: MUI + D3, virtualized tables, optional Power BI embed
├── services/
│   ├── bff-api/                      # Python / FastAPI: authz, query adapters, SSE, audit initiation, capacity mediation
│   ├── optimizer-worker/             # Python: deterministic constraint solver, energy dispatch recommendation
│   ├── scoring-worker/               # Python: RUL + quality inference, model-version capture, drift metrics
│   ├── ingest-relay/                 # Python: Event Hubs consumer -> Eventstream Custom Endpoint publisher
│   └── knowledge-orchestrator/       # Python: consent workflow, STT request, Foundry tool mediation, draft/review state
├── simulator/
│   ├── manifests/                    # Seeded JSON scenarios, no personal data
│   ├── cli.py, generator.py          # Scenario CLI and process/observation orchestration
│   ├── process/                      # Furnace, rolling, energy, quality models
│   └── validators/                   # Contract, physics, scenario, checksum/schema checks
├── contracts/
│   ├── events/                       # JSON Schema: telemetry, quality, inference, alert envelopes
│   ├── openapi/                      # Versioned BFF and Foundry-tool OpenAPI definitions (source of truth for clients)
│   └── data/                         # Delta schema / SCD / KPI contract definitions (bronze/silver/gold)
├── fabric/
│   ├── items/                        # Git-integrated Fabric item definitions where Fabric Git integration supports the item type
│   ├── notebooks/
│   ├── pipelines/
│   ├── semantic-model/
│   └── deployment-parameters/        # Per-environment workspace IDs, capacity IDs, connection references (no secrets)
├── infra/
│   ├── bicep/                        # ARM/Bicep: resource groups, capacity, networking, identities, Key Vault, monitoring
│   ├── policy/                       # Azure Policy definitions/assignments (public-network denial, tag enforcement, etc.)
│   └── scripts/                      # Idempotent deployment/validation scripts; no credentials; PowerShell + az/fab CLI
├── tests/
│   ├── contract/                     # Schema/OpenAPI contract tests (producer + consumer)
│   ├── integration/                  # Cross-service integration tests (ingest -> Fabric -> BFF)
│   ├── simulator/                    # Scenario determinism, physics-plausibility, and truth-ledger assertions
│   └── e2e/                          # Browser-driven persona journeys against demo/test environment
├── .github/workflows/                # OIDC-only pipelines; protected feeds; SBOM/scan gates (§11)
├── docs/                             # This documentation set (authoritative architecture lives in docs/architecture)
├── pip.conf / NuGet.Config           # Repository-root protected-feed configuration (§2)
└── .npmrc                            # Placeholder protected-feed configuration for the frontend toolchain (§2.3)
```

The delivered build followed **contract → simulator/validators → Fabric item
definitions → Python services → shell/MFE → integration tests**, exactly as fixed
in `deployment-topology.md` §11. Generated OpenAPI/event-schema clients are
produced from `contracts/`, never hand-duplicated as parallel DTOs — this remains
a hard rule enforced by the contract-drift CI check (§11).

### 1.1 Why a monorepo

- A single `contracts/` package lets `bff-api`, `optimizer-worker`, `scoring-worker`, `ingest-relay`, `knowledge-orchestrator`, `analytics-mfe`, and `portal-shell` all consume the same versioned schema without cross-repo release choreography during the demo-critical build phase.
- Fabric item definitions, simulator manifests, and infra Bicep live next to the services that depend on their exact contract version, which keeps the "no guessed runtime/API versions" rule (`solution-architecture.md` ADR-009) auditable in one PR diff.
- Per-service CI jobs are still independent (path-filtered GitHub Actions triggers), so the monorepo does not force a single deploy cadence.

---

## 2. Protected feed configuration (mandatory, repository-wide)

These files must exist at the repository root **before any package restore is attempted**, and must be referenced identically by every workflow, container image, and developer setup script.

### 2.1 `pip.conf` (repository root, used via `PIP_CONFIG_FILE`)

```ini
[global]
index-url = https://packagefeedproxy.microsoft.io/pypi/simple
; No [global] extra-index-url is permitted.
```

Every Python dependency file is exact-version pinned and resolved exclusively
against this feed. The implemented local/CI security gate verifies those pins
and rejects an extra index. Hash-locked requirements are a future supply-chain
hardening gate; do not claim `--require-hashes` enforcement until the committed
requirements contain hashes.

### 2.2 `NuGet.Config` (repository root)

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <clear />
    <add key="MicrosoftProtectedFeed" value="https://packagefeedproxy.microsoft.io/nuget/v3/index.json" />
  </packageSources>
  <packageSourceMapping>
    <packageSource key="MicrosoftProtectedFeed">
      <package pattern="*" />
    </packageSource>
  </packageSourceMapping>
</configuration>
```

`apps/portal-shell` (the Blazor WASM host) resolves every NuGet package (MSAL.NET/`Microsoft.Authentication.WebAssembly.Msal`, Blazor SDK packages) through this file only. `dotnet nuget list source` must show exactly one source in CI (§11 gate).

### 2.3 `.npmrc` — explicit open item

The security document only names approved PyPI/NuGet feeds; no JavaScript-ecosystem protected feed URL is present in any completed document. This guide does **not** invent one. The repository ships a placeholder:

```ini
; PLACEHOLDER — replace with the CFS-approved protected npm feed before enabling analytics-mfe CI.
; A public npm registry is explicitly prohibited by the CISO policy.
registry=REPLACE_WITH_APPROVED_NPM_PROTECTED_FEED
```

**Remaining restore/CI gate:** obtain the exact npm protected-feed URL from
Central Feed Services/EngHub before a clean frontend restore or npm vulnerability
audit runs in CI. The analytics implementation and currently restored local
dependencies are present; CI must still not silently default to a public npm
registry.

### 2.4 Verification gate

A required CI job (`verify-protected-feeds`, detailed in §11.4) scans the full repository (config files, Dockerfiles, workflow YAML, developer setup scripts) for every endpoint in the CISO blocked-registry catalog. It fails if an endpoint appears in executable configuration; policy prose is allow-listed only to explain the prohibition.

---

## 3. Exact component responsibilities

This restates and operationalizes `solution-architecture.md` §5.2 and §6 as build-time responsibility contracts, so each service's owning team knows precisely what it must (and must not) implement.

| Component | Language/runtime | Must implement | Must never implement | Talks to |
|---|---|---|---|---|
| `portal-shell` | C# / Blazor WebAssembly | MSAL sign-in, token acquisition, global chrome (top bar, nav, theme, locale), routing between persona sections, typed host↔MFE interop bridge, Fabric-capacity control panel UI (calls BFF only) | Business/domain logic, direct Fabric/Foundry calls, storing any workload credential | `analytics-mfe` (interop), `bff-api` (HTTPS) |
| `analytics-mfe` | TypeScript / React + MUI + D3 | KPI cards, D3 charts, `TBL-STD` virtualized/filterable tables (see `api-contracts.md` §5), optional Power BI embed, SSE alert consumption, the Dockview Copilot chat dock (`dashboard-specification.md` §9.6) | Authentication, storing a service/API token beyond a host-brokered short-lived reference, direct Fabric/Foundry calls, floating/undocked chat windows | `portal-shell` (interop), `bff-api` (HTTPS, token via host broker) |
| `bff-api` | Python / FastAPI | Entra token validation, persona/plant authorization, `/v1` route surface (`api-contracts.md`), response shaping, SSE fan-out, audit-event initiation, capacity request mediation, Power BI embed token mediation | Direct browser-to-Fabric credentials, direct PLC/MES control, authorization decisions based only on hidden UI state | Fabric query adapters, `optimizer-worker`, `scoring-worker`, `knowledge-orchestrator`, `capacity-operator` logic, Key Vault |
| `optimizer-worker` | Python | Price/constraint validation, deterministic feasible energy schedule, what-if simulation, recommendation persistence to gold facts | Autonomous schedule commit, relaxing a hard constraint silently | Gold Lakehouse tables, `bff-api` |
| `scoring-worker` | Python | Approved RUL/quality scoring, model-version capture, drift metrics, evaluation logging | Retraining/promotion without Responsible-AI review-board sign-off | Silver/gold features, model registry, `bff-api` |
| `ingest-relay` | Python | Event Hubs consumer under scoped managed identity, canonical envelope validation, Eventstream Custom Endpoint publish, replay/health metrics | Any curated-data access or user-facing API surface | Event Hubs, Eventstream Custom Endpoint |
| `knowledge-orchestrator` | Python | Consent/workflow state machine, Speech Fast Transcription request, draft-writing tool mediation, review-state tracking, Copilot chat grounding (screen profiles, glossary, curated public-context corpus) and in-process conversation state | Publishing an unreviewed procedure, bypassing the Knowledge Engineer approval gate, giving a chat agent a tool or a data-plane connection, persisting conversations to Fabric | Azure Speech, Foundry Agent Service, restricted storage/search, `bff-api` |
| `capacity-operator` (logical role inside `bff-api` + a dedicated Logic App) | Python (BFF) + Azure Logic App | ARM long-running-operation mediation for the demo/non-prod Fabric capacity, after policy checks | Any browser-exposed capacity credential, production auto-pause | ARM `management.azure.com`, `bff-api` |
| `simulator/*` | Python | Deterministic scenario compilation, physics/contract validation, cloud publish (Container Apps Job) or local NDJSON/Parquet replay | Any write to a non-demo namespace, any personal data | Demo Eventstream Custom Endpoint, local BFF/UI |

This table is the canonical cross-reference for PR review: a change that adds a "must never implement" behavior to a component is a blocking finding regardless of test coverage.

---

## 4. Auth model and application roles (build-time contract)

The authoritative RBAC matrix is `security-governance-and-threat-model.md` §2.3. This section restates it strictly as an implementation contract — **do not rename roles in code; map any future persona label onto these role strings**.

### 4.1 App roles (Entra app-registration manifest values)

| App role value | Who | `bff-api` enforcement |
|---|---|---|
| `Operator.Read` | Furnace/Rolling-Mill Operator | Read-only, plant-scoped dashboards; no mutation route reachable |
| `ProcessEngineer.Contribute` | Process/Quality Engineer | Read/contribute on quality+process routes for assigned plant(s) only |
| `EnergyPlanner.Approve` | Energy Dispatch Planner | Read energy routes; **only** role permitted to call `POST /v1/energy/recommendations/{id}:approve` |
| `MaintenanceEngineer.Read` | Maintenance/Reliability Engineer | Read furnace/prediction routes for assigned plant(s) |
| `DataScientist.ML` | Data Scientist / ML Engineer | Read/write training-data routes; never a production OT-sourced raw-table write path |
| `PlatformAdmin` | Platform/Cloud Administrator | Fabric/OneLake/Key Vault administrative actions outside the BFF's user-facing surface (via PIM, not app token) |
| `Compliance.Auditor` | Compliance/DPO/Auditor | Read-only `/v1/audit/decisions` and lineage views only |
| `OTEngineer.Gateway` | OT/ICS Engineer | No Fabric/BFF application access; scoped only to the OT-gateway managed identity plane |
| `Platform.Capacity.Manage` | Named platform operators | **Only** role permitted to call `/v1/platform/capacity/{start,pause}-requests` outside Demo Mode |
| `Knowledge.Publisher` | Knowledge Engineer/Admin | **Only** role permitted to call `/v1/knowledge/procedures/{id}:approve` |

Every app role is declared once per app registration (`bff-api`, `energy-agent-tools`, `knowledge-service`, `admin-portal` — never a single shared registration, per the security document §2.1) and assigned only to Entra security groups, never directly to individual users.

Plant Manager receives a plant-scoped union of the applicable read/approval policies; Executive receives a portfolio read projection; Sustainability Officer receives scoped reporting/audit projections. Neither business persona receives `PlatformAdmin` or capacity-management authority merely by selecting a persona tab.

### 4.2 Enforcement pattern in `bff-api`

1. Validate the Entra-issued JWT `aud`, `iss`, signature, and expiry on every request (standard FastAPI dependency, no custom crypto).
2. Read the `roles` claim; map to the table above via a single `authz.py` policy module — this is the **only** place role-to-permission mapping is decided.
3. Apply plant/site scope from a second claim or a first-party mapping table (`user_id -> plant_ids`) stored in a governed reference table, not from client-supplied headers.
4. Every mutating route additionally requires the specific role in §4.1 **and** an `Idempotency-Key` header (§7 of `api-contracts.md`) **and** emits an append-only audit event before returning success.
5. The frontend (`portal-shell`/`analytics-mfe`) may hide a control for a role that lacks permission, but hiding is a UX courtesy only — `bff-api` is the sole enforcement point, per `solution-architecture.md` §5.3 ("the frontend can hide an action but cannot authorize it").

### 4.3 Conditional Access and PIM

CA-01 through CA-06 (security doc §2.2) and PIM 8-hour max activation (§2.4) are tenant-level Entra configuration, not application code — track them as infrastructure backlog item `SEC-010` (§6.7), owned by Platform Admin, verified by a monthly access-review runbook (`operations-and-cost.md` §7).

---

## 5. Local demo mode (offline-first developer and presenter experience)

Local demo mode is the second level of the binding fallback ladder (`solution-architecture.md` §9.1: live cloud → local deterministic replay → cached interactive → recorded flow → static proof pack) and **must** work with zero network access.

### 5.1 What "local" means concretely

- `simulator\cli.py` generates the same versioned event envelope
  (`contracts/events`) intended for the cloud Eventstream Custom Endpoint, but
  writes deterministic local NDJSON/CSV/JSON output instead.
- `bff-api` runs with a `DEMO_MODE=local` environment flag that swaps its Fabric/KQL/Foundry/Speech adapters for **file-backed fakes** implementing the exact same internal adapter interface used in cloud mode (dependency-inversion boundary, not a parallel code path with different behavior). This keeps contract tests valid in both modes.
- `analytics-mfe`/`portal-shell` run against `bff-api`'s local mode with no code change — the API contract is identical; only the data source behind it differs.
- The BFF's primary local fixture is
  `services\bff-api\fixtures\demo-full`; checksums are verified before it is
  served, and an in-code synthetic fallback remains available if the fixture is
  absent.

### 5.2 Local bring-up sequence

```powershell
# 1. Configure protected feeds for this shell session (never public registries)
$env:PIP_INDEX_URL = "https://packagefeedproxy.microsoft.io/pypi/simple"
$env:PIP_CONFIG_FILE = "$PWD\pip.conf"
$env:PIP_EXTRA_INDEX_URL = ""

# 2. Install exact-version-pinned Python dependencies through the protected feed.
& .\services\bff-api\.venv\Scripts\python.exe -m pip install `
    --disable-pip-version-check `
    -r .\services\bff-api\requirements.txt

# 3. Start bff-api in local demo mode (no Azure calls).
npm run run:bff

# 4. Optional: generate/validate a separate deterministic simulator output.
& .\services\bff-api\.venv\Scripts\python.exe -m simulator.cli demo --out .\output\demo
& .\services\bff-api\.venv\Scripts\python.exe -m simulator.cli validate --run-dir .\output\demo

# 5. Build and serve the frontend against the local BFF (contract-identical to cloud mode)
npm run build:analytics
dotnet restore .\apps\portal-shell\PortalShell.csproj --configfile .\NuGet.Config --locked-mode
dotnet run --project .\apps\portal-shell\PortalShell.csproj --launch-profile http --no-restore
```

No step above contacts `management.azure.com`, Fabric, Foundry, or Speech. This is the mode developers use for day-to-day iteration and the mode the demo runbook falls back to at fallback-ladder level 2.

### 5.3 Guardrails specific to local mode

- Local mode refuses to start if any configured endpoint resolves to a non-`NS-DEMO-*` namespace — a startup assertion, not a manual reminder.
- Local mode always renders the **Synthetic demo data — not for operational control** banner; this is not conditionally hidden.
- Local mode never accepts a real Entra token bound to a production app registration; it uses a separate `demo`-environment app registration with no production-scope role assignment.

---

## 6. Phased backlog with dependencies and acceptance criteria

The backlog records the delivered local-workstream scope
(`app-scaffold`, `simulator-implementation`, `backend-implementation`,
`frontend-implementation`, `ai-agent-implementation`, `fabric-assets`,
`azure-infrastructure`, `cicd-testing`). Those todos are complete. Each item
retains a stable ID (`<AREA>-<NNN>`), dependency list, and acceptance criteria
for maintenance and cloud rollout; tenant-dependent production evidence remains
outside the completed local baseline.

### 6.1 Phase A — Foundations (contracts, infra skeleton, CI gate)

| ID | Title | Depends on | Acceptance criteria |
|---|---|---|---|
| `FOUND-001` | Scaffold monorepo topology (§1) and root config | — | Directory tree matches §1 exactly; `pip.conf`, `NuGet.Config`, `.npmrc` placeholder present; `verify-protected-feeds` CI job present and passing on an empty repo |
| `FOUND-002` | Author `contracts/events` JSON Schemas for telemetry, alarm, model-inference, quarantine envelopes | `FOUND-001` | Schemas validate the exact envelope fields listed in `solution-architecture.md` §3.3 (`event_id` UUIDv7, UTC timestamps, sequence, asset/plant IDs, correlation ID, schema version, classification, scenario/seed); a schema-conformance test suite passes for at least one valid and one intentionally invalid fixture per schema |
| `FOUND-003` | Author `contracts/openapi/bff-api-v1.yaml` skeleton (routes, shared response envelopes, error model) | `FOUND-002` | OpenAPI document matches every route in `api-contracts.md` §4; `total`/`page`/`size`/`asOf`/`correlationId` list envelope and the AI-derived-value envelope are defined as reusable components; lints clean under an OpenAPI linter |
| `FOUND-004` | Author `contracts/data` bronze/silver/gold table contracts | `FOUND-002` | Table/column definitions match `solution-architecture.md` §3.3 zone tables; each table has a documented grain, keys, and idempotency key |
| `FOUND-005` | Bicep skeleton: resource groups, tags, budgets, hub/spoke networking, Key Vault, Log Analytics, managed identities (no Fabric items) | `FOUND-001` | `az deployment group what-if` succeeds for `dev` environment; every resource carries `environment`, `dataClassification`, `owner`, `costCenter`, `expiry` (demo) tags; no public network access left enabled without a documented exception |
| `FOUND-006` | GitHub Actions OIDC trust + environment protection rules (`dev`, `test`, `demo`, `prod`) | `FOUND-005` | Federated credential subject is `repo:<org>/<repo>:environment:<env>` per environment, no wildcard branch ref for `prod`; a workflow run using `azure/login@v2` succeeds with zero `creds:`/client-secret usage; the `creds:`-grep required check is active |

### 6.2 Phase B — Simulator and data contracts (todo: `simulator-implementation`)

| ID | Title | Depends on | Acceptance criteria |
|---|---|---|---|
| `SIM-001` | Scenario compiler reads a seeded manifest and produces a deterministic truth ledger | `FOUND-002`, `FOUND-004` | Two runs with the same manifest produce byte-identical event sequences and an identical truth-ledger checksum; output checksum validation rejects a tampered generated run |
| `SIM-002` | Process/observation simulators for furnace, rolling, energy/market, quality/genealogy per `synthetic-data-and-simulators.md` §3 | `SIM-001` | Generated signals stay within the documented normal ranges and relationships (e.g., cooling-water ΔT vs. heat flux, mass conservation ±0.8% in rolling); a physics-assertion test suite fails the build if a relationship is violated |
| `SIM-003` | Contract + physics + scenario validator gate | `SIM-002`, `FOUND-002` | A run is not marked presentable unless all three validator classes pass; validator output is a machine-readable report consumed by `tests/simulator` |
| `SIM-004` | Cloud demo publisher (Container Apps Job, `mi-ns-demo-simulator` managed identity) to Eventstream Custom Endpoint | `SIM-003`, `INFRA-003` | Publisher authenticates via Entra managed identity only (no SAS key); duplicate/late/out-of-order injected test events are visibly quarantined, not silently dropped |
| `SIM-005` | Local NDJSON/Parquet replay sink for offline demo mode | `SIM-003` | Matches §5 local demo mode bring-up exactly; runs with zero outbound network calls (verified by a network-call-assertion test) |
| `SIM-006` | Fallback pack manifest + checksum verification tool | `SIM-003`, `SIM-005` | Reproduces the exact fallback-pack contents list in `demo-runbook.md` §6.2; checksum mismatch blocks demo-readiness sign-off |

### 6.3 Phase C — Backend/Fabric core (todos: `backend-implementation`, `fabric-assets`)

| ID | Title | Depends on | Acceptance criteria |
|---|---|---|---|
| `FAB-001` | Provision demo/dev Fabric F capacity (ARM `Microsoft.Fabric/capacities`) via Bicep | `FOUND-005` | Capacity resource exists in Sweden Central with an F2 SKU tag; **note:** this is the only Fabric-related item provisionable by Bicep (see §9.2) |
| `FAB-002` | Create Fabric workspaces (`NS-<env>-RTI-Ingress`, `-DataCore`, `-ML`, `-Analytics`, `NS-DEMO-*`) via Fabric REST API/portal, assign to capacity | `FAB-001` | Workspace isolation matches `solution-architecture.md` §3.2 exactly; no shortcut crosses the `NS-DEMO-*`/non-demo boundary (manual + automated check, §9.2) |
| `FAB-003` | Deploy Eventstream `es-ns-telemetry-v1` with Custom Endpoint source, dual destination (KQL + landing Lakehouse) | `FAB-002` | Publisher identity is Contributor **only** in `NS-<env>-RTI-Ingress`; no Contributor grant on any other workspace |
| `FAB-004` | Create Eventhouse/KQL database `kql-ns-operations` with `telemetry_hot`, `alarm_hot`, `gateway_health_hot`, `model_inference_hot`, `ingest_quarantine_hot` tables | `FAB-003` | Each table's retention matches `solution-architecture.md` §3.4; a KQL query smoke test returns rows within 5 minutes of a test publish |
| `FAB-005` | Create landing (`lh-ns-landing`) and core (`lh-ns-core`) Lakehouses with bronze/silver/gold Delta contracts | `FAB-002`, `FOUND-004` | Reconciliation test: row counts and idempotent `event_id` dedup match between bronze and silver for a fixed test batch |
| `FAB-006` | Author Fabric pipelines/notebooks for batch ingestion (MES/ERP/LIMS/CMMS synthetic feeds) and bronze→silver→gold transforms | `FAB-005` | Late/duplicate/invalid-unit/unknown-asset records are quarantined and visible, never silently repaired |
| `FAB-007` | Direct Lake semantic model `sm-ns-operations` over gold tables + Power BI reports (`rpt-ns-executive`, `rpt-ns-sustainability`, persona reports) | `FAB-005`, `FAB-006` | Semantic model refresh succeeds; RLS/persona scoping verified against §4 app roles |
| `BE-001` | `bff-api` skeleton: FastAPI app, Entra token validation, `/v1/me` route | `FOUND-003` | Contract test against `contracts/openapi/bff-api-v1.yaml` passes; unauthenticated request returns `401` with the standard error envelope |
| `BE-002` | `bff-api` KQL/OneLake read adapters (dedicated read identity) | `FAB-004`, `FAB-005`, `BE-001` | Adapter interface has both a cloud implementation and a local file-backed fake (§5.1); swapping implementations changes zero call-site code |
| `BE-003` | `bff-api` SSE alert stream (`/v1/realtime/alerts`) | `BE-002` | Reconnect/poll fallback exposes a `stale=true` flag per `api-contracts.md` §6; a client that never reconnects still receives correct state via poll |
| `BE-004` | `optimizer-worker`: deterministic energy dispatch solver + `/v1/energy/schedules:simulate` | `FAB-005`, `BE-001` | Given a fixed manifest, output is byte-for-byte reproducible; a solver run exceeding 5 seconds falls back to the cached signed result per `demo-runbook.md` |
| `BE-005` | `scoring-worker`: RUL model serving + `/v1/furnaces/{assetId}/lining-forecast` | `FAB-006`, `BE-001` | Response matches the AI-derived-value envelope (`solution-architecture.md` §5.3): `value`, `unit`, `confidence.p10/p50/p90`, `modelVersion`, `scoredAt`, `drivers`, `sourceRefs` |
| `BE-006` | Audit/decision ledger (`/v1/audit/decisions`) as append-only path | `BE-001` | Every mutating route in §4.2 writes a correlated audit event before returning; direct row edit/delete is impossible through any application code path |
| `BE-007` | `capacity-operator` logic in `bff-api` (`/v1/platform/capacity/*`) | `FAB-001`, `BE-006`, `INFRA-004` | Matches the state machine in `deployment-topology.md` §5.1 exactly; Demo Mode always simulates; real action requires `Platform.Capacity.Manage` and is denied outside allow-listed non-prod capacities |

### 6.4 Phase D — AI agent workflows (todo: `ai-agent-implementation`)

| ID | Title | Depends on | Acceptance criteria |
|---|---|---|---|
| `AI-001` | Foundry project + agent registration (Sweden Central, Data Zone EU model deployment) | `FAB-001`, `INFRA-005` | Model/tool/quota/Data-Zone availability verified in-tenant before use (open item in `deployment-topology.md` §15); Entra RBAC only, no API key in any config |
| `AI-002` | Energy agent: read/forecast/simulate OpenAPI tools only, separate propose endpoint | `AI-001`, `BE-004` | Agent cannot invent or commit a schedule; a commit-capable tool exists only behind the human-approval gate in `BE-007`-equivalent write path and is disabled outside approved phases |
| `AI-003` | Knowledge-capture orchestrator: consent workflow, Speech Fast Transcription call, restricted retrieval + draft-writing tool | `AI-001` | Draft never auto-publishes; only `Knowledge.Publisher` role can call the approve route; unapproved transcript is classified Highly Confidential end-to-end |
| `AI-004` | Prompt Shields + spotlighting on both agents; full tool-call audit logging | `AI-002`, `AI-003` | Untrusted content (spot-price payload, interview transcript) is never concatenated as instruction text; a fabricated prompt-injection test fixture is rejected |

### 6.5 Phase E — Frontend experience (todo: `frontend-implementation`)

| ID | Title | Depends on | Acceptance criteria |
|---|---|---|---|
| `FE-000` | Resolve and configure the approved npm protected feed (§2.3) | `FOUND-001` | `.npmrc` points only at the CFS-approved feed; `verify-protected-feeds` extended to assert this; **blocking** for all other `FE-*` items |
| `FE-001` | `portal-shell` Blazor host: MSAL sign-in, chrome, routing, typed interop bridge | `FOUND-001`, `FE-000` | Shell exposes exactly the typed context named in `solution-architecture.md` §5.1 (`themeMode`, `locale`, `activePersona`, `site`, navigation intent, toast, capacity request, telemetry); no workload credential crosses the bridge |
| `FE-002` | `analytics-mfe` scaffold + `TBL-STD` shared table component | `FE-000`, `FOUND-003` | Implements sorting, per-column search, global search, pagination/virtualization, export, and states exactly as defined in `api-contracts.md` §5; verified against the UX acceptance criteria `AC-G3` |
| `FE-003` | Command Center + canonical persona landing views | `FE-001`, `FE-002`, `BE-002` | Each of the 8 personas in `personas-and-journeys.md` receives the correct default section; Platform Ops remains a restricted supporting surface per `dashboard-specification.md` §3 |
| `FE-004` | Platform Ops capacity control panel (Demo Mode simulated / real gated) | `FE-003`, `BE-007` | Demo Mode always shows **Simulated**; real control only rendered/enabled for `Platform.Capacity.Manage` and only outside Demo Mode |
| `FE-005` | Accessibility and i18n pass (WCAG 2.2 AA) | `FE-003` | Automated axe-core scan clean on primary routes; keyboard-only navigation completes every persona's primary task |

### 6.6 Phase F — CI/CD and tests (todo: `cicd-testing`)

| ID | Title | Depends on | Acceptance criteria |
|---|---|---|---|
| `CI-001` | Per-service GitHub Actions build/test workflows, path-filtered | `FOUND-006` | Each service builds/tests independently; a change to `apps/analytics-mfe` does not trigger `services/bff-api` CI |
| `CI-002` | Contract tests wired to `contracts/openapi` and `contracts/events` | `FOUND-002`, `FOUND-003` | A breaking schema change fails CI before merge, not after deploy |
| `CI-003` | SBOM generation + dependency scanning (Dependabot) + secret scanning/push protection | `CI-001` | SBOM artifact retained 2 years (§14 security doc); Critical/High vulnerability SLA (7/30 days) enforced as a required check |
| `CI-004` | CodeQL/SAST on every PR; pinned action SHAs; minimal `GITHUB_TOKEN` permissions | `CI-001` | No workflow uses a floating action tag; `permissions:` block is least-privilege per job |
| `CI-005` | Integration test environment (`test`) wired to Fabric/Foundry test workspaces | `FAB-002`..`FAB-007`, `AI-001` | Full ingest→Fabric→BFF→frontend round trip passes in `test` before promotion to `demo`/`prod` gate |
| `CI-006` | E2E persona journey tests (Playwright or equivalent) against `demo` environment | `FE-003`, `CI-005` | Two consecutive successful 15-minute scripted demo runs recorded as CI evidence, matching `deployment-topology.md` §8 step 8 |

### 6.7 Phase G — Infrastructure and security hardening (todo: `azure-infrastructure`)

| ID | Title | Depends on | Acceptance criteria |
|---|---|---|---|
| `INFRA-001` | Hub-spoke networking, private endpoints, Azure Firewall egress allow-list (incl. protected feed domains) | `FOUND-005` | Deny-by-default NSGs; only explicitly required flows permitted; protected-feed domains explicitly allow-listed |
| `INFRA-002` | Key Vault per environment/bounded context, RBAC-only access, CMK for Confidential/Highly Confidential stores | `INFRA-001` | No legacy access policies; PIM-eligible admin roles only |
| `INFRA-003` | Event Hubs + `ingest-relay` deployment with per-plant managed identity | `INFRA-001` | No SAS key anywhere in config; identity scoped to one plant's Event Hub only |
| `INFRA-004` | Demo-capacity lifecycle Logic App (01:00 daily check) + GUI request wiring | `FAB-001`, `BE-007` | Matches `operations-and-cost.md` §5 exactly; production capacity is unreachable from this Logic App by allow-list |
| `INFRA-005` | Foundry + Speech resource provisioning, private endpoints where supported | `INFRA-001` | Sweden Central, Data Zone (EU) model deployment, Entra RBAC only |
| `SEC-010` | Conditional Access policies CA-01..CA-06, PIM configuration | `INFRA-002` | Matches security doc §2.2/§2.4 exactly; verified via a tenant policy export diff in the release evidence pack |
| `SEC-011` | Microsoft Sentinel onboarding + minimum detection set | `INFRA-001`..`INFRA-005` | All six minimum analytics rules from security doc §9 are enabled and firing against synthetic test events |

### 6.8 Dependency graph summary

```text
FOUND-001 → FOUND-002 → FOUND-003 → BE-001 → BE-002 → BE-003/BE-004/BE-005 → BE-006 → BE-007
FOUND-001 → FOUND-005 → INFRA-001 → INFRA-002/003/004/005 → FAB-001 → FAB-002 → FAB-003/004/005 → FAB-006 → FAB-007
FOUND-002 → SIM-001 → SIM-002 → SIM-003 → SIM-004/005 → SIM-006
FOUND-006 → CI-001 → CI-002/003/004 → CI-005 → CI-006
FE-000 → FE-001/FE-002 → FE-003 → FE-004/FE-005
FAB-001, INFRA-005 → AI-001 → AI-002/AI-003 → AI-004
```

This graph is the input to Section 16's prioritized execution sequence.

---

## 7. Fabric capacity lifecycle: request/status APIs (implementation contract)

This section is the build contract for `capacity-operator` (inside `bff-api`) and the 01:00 Logic App, both consuming the same underlying ARM operations. Full HTTP route shapes are in `api-contracts.md` §8; this section fixes the ARM call pattern and state machine that those routes wrap.

### 7.1 ARM operations used (verified against official REST reference)

| Operation | Method/path | Notes |
|---|---|---|
| Read capacity state | `GET https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Fabric/capacities/{capacityName}?api-version=2023-11-01` | Read-only; any authenticated app-role user may trigger this via `GET /v1/platform/capacity` |
| Resume | `POST .../capacities/{capacityName}/resume?api-version=2023-11-01` | Returns `202 Accepted`; poll `Location`/`Azure-AsyncOperation` per `Retry-After` |
| Suspend | `POST .../capacities/{capacityName}/suspend?api-version=2023-11-01` | Same async pattern |

`2023-11-01` is the one deliberately pinned API version in the whole platform (`solution-architecture.md` §1.2/§12.4); it must be rechecked against the official REST reference before each major release, not silently bumped by SDK auto-update.

### 7.2 Execution identity

Both the BFF-triggered request and the Logic App scheduled check use `mi-ns-capacity-demo`, scoped **only** to `Microsoft.Fabric/capacities/read`, `write`, `suspend/action`, `resume/action` on the allow-listed non-production capacity resource ID. This identity has zero Fabric workspace, OneLake, Key Vault-secret, or subscription-wide role (`deployment-topology.md` §5.2).

### 7.3 State machine (implementation target)

Implement exactly the state diagram in `deployment-topology.md` §5.1: `Paused → ResumeRequested → Resuming → ReadinessCheck → Running → DrainRequested → Draining → SuspendRequested → Paused`, with `Failed` states looping back to `Paused` after operator acknowledgement. `bff-api` persists this state (not just ARM's raw provisioning state) so the readiness checklist — Fabric workspace availability, Eventstream/Eventhouse query, Lakehouse/semantic-model reachability, application health, budget check, simulator-still-paused — gates the `Running` transition, matching `deployment-topology.md` §5.4 steps 4–6.

### 7.4 What is explicitly NOT built

- No route or Logic App action targets a production capacity resource ID; the allow-list is enforced both at the Logic App precondition check and independently at the `bff-api` policy layer (defense in depth, not a single check).
- No alert-triggered automatic pause/resume exists; only a human GUI request (with reason) or the 01:00 lifecycle check may initiate a transition (`operations-and-cost.md` §5 has the full runbook).

---

## 8. GitHub Copilot / agent workflow for this repository

This section defines how GitHub Copilot coding agent (and any other automation with repository write access) is used to build NovaSteel, consistent with the security document's agent-tooling controls (§19.4) and the "no guessed versions" ADR-009.

### 8.1 Task decomposition convention

- Each backlog ID in §6 is sized to be a single Copilot coding-agent task or a single human PR — not a multi-week epic. An agent assigned `BE-004` should be able to complete it without needing to also modify `FAB-005`'s schema (dependencies are already resolved by the graph in §6.8).
- Every agent task prompt must reference the specific architecture section(s) it implements (e.g., "implement `BE-005` per `solution-architecture.md` §4.2 and `api-contracts.md` §4") so the agent's output is traceable to an authoritative source rather than reinvented.
- Agent tasks that touch `contracts/` require a companion task (or the same task) to regenerate/verify generated clients in `services/*` and `apps/analytics-mfe` — never a manual hand-edit of a generated client.

### 8.2 Mandatory pre-flight for any agent with shell/package-manager access

Per security doc §19.4, any agent (including Copilot coding agent) with install/restore capability must have the protected-feed environment variables (§2.1/§2.2) pre-configured **before** it is granted that capability, and its tool definition must hardcode the protected feed and reject an override parameter. A Copilot coding agent working in this repository inherits `pip.conf`/`NuGet.Config` from the repository root automatically; it must not be instructed to add `--extra-index-url` or `--index-url` pointing anywhere else.

### 8.3 Required PR checklist for agent-authored changes

Every PR (agent- or human-authored) must state:

1. Which backlog ID(s) it completes.
2. Which STRIDE row(s) (`security-governance-and-threat-model.md` §17) it affects, if any new trust boundary is introduced.
3. Which security acceptance gate(s) (§21 of the same document) apply, with evidence (test output, `what-if` diff, SBOM link).
4. Confirmation that `verify-protected-feeds` passed.

### 8.4 Review model

- **Contract changes** (`contracts/`, `fabric/deployment-parameters`, `infra/bicep`) always require a human reviewer with the relevant domain ownership (data platform, security, or infra), regardless of who authored the change.
- **Service-internal changes** that do not alter a contract may be agent-authored and single-human-approved.
- **Agent tool-scope changes** (new Foundry tool, new OpenAPI operation exposed to an agent) always trigger the RAI-board sign-off gate (`security-governance-and-threat-model.md` §22 RACI) before merge — an agent cannot self-approve its own new capability.

---

## 9. Azure/Fabric setup sequence

This operationalizes `deployment-topology.md` §8 and §13 into an explicit run order with the exact tool used per step, and is intentionally conservative about what Bicep can and cannot provision.

### 9.1 Sequence

| Step | Action | Tool | Evidence gate |
|---|---|---|---|
| 1 | Create resource groups, tags, budgets, hub/spoke VNets, private DNS, Key Vault, Log Analytics/Sentinel connection, managed identities | Bicep (`infra/bicep`) via GitHub Actions OIDC | `what-if` reviewed in PR; Azure Policy assignment active; no unreviewed public-network exception |
| 2 | Create Fabric capacity (`Microsoft.Fabric/capacities`, ARM resource) | Bicep | Capacity resource visible in the target subscription/region; SKU = F2 for demo |
| 3 | Create Fabric workspaces and assign capacity, OneLake security roles, sensitivity labels | **Fabric REST API / Fabric portal / Git integration** — not Bicep (§9.2) | Workspace/role list matches `solution-architecture.md` §3.2 table exactly; verified by a scripted post-check, not manual memory |
| 4 | Deploy Event Hubs, DMZ gateway/relay, Eventstream Custom Endpoint, KQL/landing destinations | Bicep (Event Hubs, Container Apps) + Fabric REST API (Eventstream/KQL items) | Identity path proven end-to-end; no SAS key; duplicate/late/invalid messages visibly quarantined |
| 5 | Deploy Lakehouse tables, pipeline/notebook definitions, data-quality checks, Purview lineage | Fabric REST API / Git-integrated Fabric items + Purview scan configuration (Azure resource, Bicep-eligible for the Purview account itself) | Bronze/silver/gold reconciliation and schema tests pass |
| 6 | Deploy model workers, BFF, Foundry/Speech connections, tool allow-lists, content controls, tracing | Bicep (Container Apps/App Service, Foundry/Speech resource, Key Vault references) + application deployment (container image push) | Entra-only auth; no direct write/OT path; evaluation and tool audit pass |
| 7 | Deploy Direct Lake model/Power BI and Blazor/MFE client | Fabric REST API/portal (semantic model, reports) + static web app / container deployment (Bicep) | Persona/RLS checks, API contract/e2e, accessibility and stale/error behavior pass |
| 8 | Configure capacity lifecycle Logic App and GUI request flow | Bicep (Logic App resource + connections) | 01:00 skip/pause, resume LRO polling, denial, concurrency, and audit tests pass |
| 9 | Load demo seed/fallback pack and rehearse | Simulator + manual rehearsal | Two consecutive successful scripts; full offline path verified |
| 10 | Production onboarding approval | Manual governance gate | DPO/legal, OT, security/RAI, capacity/DR, source/market-license gates signed |

### 9.2 What Bicep can and cannot provision — stated explicitly

**Bicep-provisionable (ARM resource providers):** resource groups, virtual networks/subnets/NSGs/firewall, Key Vault, managed identities, Event Hubs namespaces/hubs, Container Apps/Container Apps Jobs, Log Analytics/Sentinel workspace connections, Microsoft Foundry/Speech resource accounts, Purview account, budgets/cost alerts, Azure Policy assignments, and the **`Microsoft.Fabric/capacities`** resource (the F-SKU capacity itself).

**Not Bicep-provisionable — Fabric SaaS-plane items** managed instead through the **Fabric REST API**, the **Fabric portal**, **Git integration**, or **deployment pipelines** (each with its own item-type support level, which must be reverified before automating it): Fabric **workspaces**, workspace role assignments, **OneLake security roles**, **Eventstream** definitions and Custom Endpoint sources, **Eventhouse/KQL databases** and tables, **Lakehouse** items and their Delta tables, **pipelines** and **notebooks**, the **Direct Lake semantic model**, and **Power BI reports**. This guide does not claim these are ARM/Bicep resources anywhere, and no `infra/bicep` template in this repository may declare a `Microsoft.Fabric` item type other than `capacities`. Automate their creation with idempotent scripts under `infra/scripts` calling the Fabric REST API (with a service-principal identity that has the documented Contributor-or-higher requirement isolated to `NS-<env>-RTI-Ingress` only, per `solution-architecture.md` §8.1), or accept a documented one-time manual portal step where an item type does not yet support programmatic creation — verify current API/Git-integration support for each item type immediately before automating it, because Fabric's supported-item list changes over time.

### 9.3 Environment promotion rule

`dev → test → demo`/`prod` promotion never copies a live connection string or production identifier into `demo`. Each environment's Fabric workspace IDs, capacity IDs, and connection references live in `fabric/deployment-parameters/<env>.json`, checked into source control (no secrets, only identifiers), consumed by both the Bicep parameter files and the Fabric REST API automation scripts.

---

## 10. IaC approach

- **Tool:** Bicep (not Terraform) for every ARM-manageable resource, matching the existing `infra/bicep` folder convention and the architecture's explicit IaC references (`solution-architecture.md` §12, `deployment-topology.md` §8/§13).
- **Structure:** one subscription-scoped or management-group-scoped root template per environment invoking modules per concern (`network.bicep`, `identity.bicep`, `keyvault.bicep`, `eventhubs.bicep`, `fabric-capacity.bicep`, `containerapps.bicep`, `foundry-speech.bicep`, `monitoring.bicep`, `logicapp-capacity-lifecycle.bicep`).
- **Parameters:** environment-specific `.bicepparam` files under `infra/bicep/parameters/<env>.bicepparam`; no secret values in parameter files — secret references use `existing` Key Vault lookups.
- **Validation:** every PR touching `infra/bicep` runs `az deployment ... what-if` and attaches the diff to the PR; a human with infra ownership approves before merge (§8.4).
- **State:** Bicep is stateless-by-design (idempotent ARM deployment); no separate state file to manage, which avoids a Terraform-state-locking concern in a fleet-parallel build.
- **Fabric items:** tracked separately as described in §9.2, under `fabric/items` and `infra/scripts`, versioned in Git but deployed through the Fabric REST API/Git integration, never claimed as Bicep resources.
- **Rollback:** roll back to a previously validated Bicep template version; never "roll back" by deleting source data, Eventstream history, audit facts, or a shared capacity (`deployment-topology.md` §4.2 rule 5).

---

## 11. GitHub Actions / OIDC pipeline design

### 11.1 Workflow inventory

| Workflow | Trigger | Purpose |
|---|---|---|
| `ci-bff-api.yml` | Push/PR touching `services/bff-api/**`, `contracts/**` | Lint, unit test, contract test, SBOM, dependency scan |
| `ci-optimizer-worker.yml`, `ci-scoring-worker.yml`, `ci-ingest-relay.yml`, `ci-knowledge-orchestrator.yml` | Path-filtered, same pattern as above | Per-service independence |
| `ci-simulator.yml` | Push/PR touching `simulator/**` | Determinism test, physics-assertion test, validator gate |
| `ci-portal-shell.yml` | Push/PR touching `apps/portal-shell/**` | `dotnet build`/`test` via protected NuGet feed only |
| `ci-analytics-mfe.yml` | Push/PR touching `apps/analytics-mfe/**` | Blocked pending `FE-000`; once unblocked, lint/build/test via protected npm feed only |
| `cd-infra.yml` | Push to `main` touching `infra/bicep/**`, environment approval | `what-if` then `deploy`, OIDC per environment |
| `cd-services.yml` | Tag/release | Build container images, push to an approved registry, deploy to Container Apps per environment with progressive promotion `dev→test→demo`/`prod` |
| `fabric-items-sync.yml` | Push touching `fabric/items/**` | Calls Fabric REST API / Git-integration sync per §9.2; environment-gated |
| `verify-protected-feeds.yml` | Every PR (required check) | §2.4 scan |
| `security-gates.yml` | Every PR (required check) | CodeQL, secret scanning status, `creds:` grep, SBOM presence |

### 11.2 OIDC federation pattern (from `security-governance-and-threat-model.md` §3.2, restated as a build contract)

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    environment: production   # exact GitHub Environment name; federated credential subject matches 1:1
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Azure login via OIDC (Workload Identity Federation)
        uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
          # No client secret. No AZURE_CREDENTIALS JSON. Ever.
```

One federated identity credential per environment (`novasteel-cicd-dev`, `-test`, `-demo`, `-prod`), each RBAC-scoped only to that environment's resource group(s), never subscription-level Owner. Production's federated credential subject never uses a wildcard branch ref.

### 11.3 Package restore step template (every workflow)

```yaml
    - name: Restore Python dependencies (protected feed only)
      run: |
        pip config set global.index-url https://packagefeedproxy.microsoft.io/pypi/simple
        pip install --disable-pip-version-check -r requirements.txt

    - name: Restore .NET dependencies (protected feed only)
      run: |
        dotnet restore --configfile NuGet.Config
```

### 11.4 `verify-protected-feeds` required check (exact behavior)

Fails the build if an endpoint in the CISO blocked-registry catalog appears in any executable configuration, workflow, Dockerfile, or developer setup script. The narrow policy-document allow-list exists only for explanatory prohibition text. Run it before every restore and as a standalone required PR check so a bypassed/forked workflow cannot skip it.

### 11.5 Branch/environment protection

- `main` requires the `verify-protected-feeds` and `security-gates` checks plus at least one human approval for any change touching `infra/`, `contracts/`, or `fabric/`.
- `prod` and `demo` GitHub Environments require a named human reviewer group for deployment approval; `dev`/`test` may auto-deploy on merge.

---

## 12. Test strategy

| Layer | What it verifies | Tooling convention | Gate |
|---|---|---|---|
| Contract tests | `contracts/openapi` and `contracts/events` are honored by every producer/consumer | Schema validators + generated-client round-trip tests | Required check on every PR touching `contracts/` or a service |
| Unit tests | Service-internal logic (solver constraints, scoring feature assembly, authz policy mapping) | Per-language native framework (`pytest`, `xunit`/`bunit`) | Required check per service CI |
| Simulator tests | Determinism, physics plausibility, scenario/contract assertions | `tests/simulator` (§6.2 `SIM-*`) | Required before any cloud publish is enabled |
| Integration tests | Cross-service round trip: ingest → Fabric → BFF → adapters | `tests/integration` against `test` environment | Required before promotion to `demo`/`prod` |
| E2E persona tests | Each of the 8 personas can complete its primary journey in `personas-and-journeys.md` | `tests/e2e` (Playwright-class tool) against `demo` | Required for demo-readiness sign-off (`deployment-topology.md` §8 step 8) |
| Accessibility tests | WCAG 2.2 AA on primary routes | Automated axe-core scan + manual keyboard-only pass | Required for `FE-005` |
| Security tests | STRIDE-row-specific abuse cases (`security-governance-and-threat-model.md` §18) | Fixture-driven negative tests (prompt-injection payloads, SAS-key regression, over-broad role token) | Required for any PR touching an agent tool or an authz boundary |
| Load/measurement tests | F2 vs. F4 Fabric capacity decision input | Scripted rehearsal load against demo capacity, Capacity Metrics app review | Required before any F4 upgrade decision (`deployment-topology.md` §6) |
| Chaos/fallback tests | Every fallback-ladder level actually works offline | Manual + scripted network-disabled rehearsal | Required before every live demo (`demo-runbook.md` §3.1) |

Every test class above must itself only restore packages from the protected feeds (§2); a test runner image built from a public base image still resolves its own dependencies through §2's configuration.

---

## 13. Observability hooks required at build time

Implementation must emit the exact signal set catalogued in `solution-architecture.md` §9.2 from day one, not retrofit it later. See `operations-and-cost.md` §6 for the operational SLOs and alerting thresholds built on top of these signals; this section only fixes what each component must emit:

- **`ingest-relay`**: `source_id`, partition/sequence, queue depth, oldest buffered event, connection state, event-time lag, duplicate count, publish retry count.
- **Eventstream/KQL**: input/output rate, failures, ingestion/query latency, materialized-view health, quarantine rate, freshness — surfaced via the RTI dashboard, not reinvented in the BFF.
- **Lakehouse/pipeline**: bronze→silver→gold row reconciliation, contract pass rate, late/invalid record count, pipeline duration, data freshness.
- **Capacity**: CU/utilization/throttling/cost from Capacity Metrics, pause/resume transition, active jobs, F SKU, budget alert.
- **Models**: input data version, model/config version, latency, confidence distribution, drift, prediction-vs-outcome, evaluation result.
- **Foundry/STT**: model deployment, response/tool-call outcome, safety filter result, quota/429 retry, evaluation, transcript status — with sensitive content redacted before logging.
- **Application (`bff-api`, workers)**: OpenTelemetry traces, request/error/latency, SSE reconnects, authorization denials, correlation ID on every log line.
- **Security**: Entra sign-in/audit, Key Vault access, Fabric/Power BI activity, Purview, Sentinel detections, capacity-lifecycle ARM activity.

Every flow propagates `correlation_id` end to end; `bff-api`'s audit table (§6.3 `BE-006`) is the append-only join point linking event IDs, source snapshots, model/agent configuration, prompt/template version, human action, and outcome.

---

## 14. Local demo mode ↔ offline fallback pack cross-reference

Section 5 defines local demo mode as a developer/runtime capability. It is also fallback-ladder level 2 for the live 15-minute defense (`demo-runbook.md` §6.1). Implementation must keep these identical, not build two divergent "offline modes":

1. **Level 1 — live cloud**: full Azure/Fabric path, described throughout this guide.
2. **Level 2 — local deterministic replay**: exactly §5 of this guide.
3. **Level 3 — cached interactive**: `bff-api` in `DEMO_MODE=local` serving
   the checksum-verified `services\bff-api\fixtures\demo-full` data, with no
   simulator process running.
4. **Level 4 — recorded flow**: static video assets, no application code involved; owned by the demo-runbook workstream, only referenced here.
5. **Level 5 — static proof pack**: screenshots/PDF/JSON, no application code involved.

`SIM-006` (§6.2) is the implementation task that produces and checksum-verifies the artifacts levels 3–5 depend on.

---

## 15. Production caveats (do not silently generalize the demo)

Restated from the architecture so implementers do not accidentally build production behavior into the demo path or vice versa:

1. Phase 0 is synthetic-only; no code path may read a non-`NS-DEMO-*` namespace while `DEMO_MODE` is set, and no production code path may read a `NS-DEMO-*` namespace either — enforce both directions with a startup assertion, not a comment.
2. No application, agent, Activator rule, pipeline, or demo control writes to a PLC, safety interlock, furnace, or production setpoint, in any environment, at any phase implemented so far. Any future work item proposing such a write requires the security/legal/OT/RAI review gate in `solution-architecture.md` ADR-007 before a single line of code is written.
3. Energy-recommendation "approve" and quality "what-if" routes return simulated/shadow state in Phase 0/1; a real write connector is a Phase 2+ item gated by the production onboarding checklist (§9.1 step 10), not an implementation detail to "just add later" inside `optimizer-worker`.
4. Capacity lifecycle automation (01:00 Logic App, GUI request) targets `dev`/`test`/`demo` only; the allow-list check is implemented independently in both the Logic App and `bff-api`, and a change that widens the allow-list to include a production capacity ID is a security-gate-blocking change requiring explicit sign-off.
5. Foundry Data Zone (EU) is not a single-region guarantee; if legal/DPO impose a Sweden-Central-only requirement, the model deployment type must change to regional Standard/Provisioned — this is a configuration change (`AI-001`), not an architecture change.
6. No exact runtime/package version is hard-coded in this guide beyond the one pinned Fabric capacity API version (§7.1); every other SDK/runtime version is resolved at bootstrap through the protected feed and recorded in lockfiles/SBOM per ADR-009.

---

## 16. Delivered implementation sequence and remaining cloud rollout

This records the sequence used to deliver the local baseline, derived from the
dependency graph in §6.8. It is retained as implementation provenance, not an
open local-development backlog. The tenant-dependent portions of later waves are
the cloud rollout gates summarized in the root handoff and `docs\README.md`.

| Wave | Backlog IDs | Rationale |
|---|---|---|
| **Wave 0 — Contracts and skeleton** | `FOUND-001`, `FOUND-002`, `FOUND-003`, `FOUND-004`, `FOUND-005`, `FOUND-006`, `FE-000` | Nothing else can start without the repository skeleton, event/API/data contracts, the protected-feed gate, and OIDC trust. `FE-000` is called out early because it blocks all frontend work and needs a manual CFS lookup that has non-trivial lead time. |
| **Wave 1 — Infra foundation + simulator core** | `INFRA-001`, `INFRA-002`, `INFRA-003`, `SIM-001`, `SIM-002`, `SIM-003` | Networking/Key Vault/Event Hubs and the deterministic simulator core can build in parallel; both are prerequisites for everything downstream and have no interdependency on each other. |
| **Wave 2 — Fabric capacity + workspaces, BFF skeleton** | `FAB-001`, `FAB-002`, `FAB-003`, `BE-001`, `SIM-004`, `SIM-005` | Capacity/workspace provisioning (via the Bicep-then-API sequence in §9) unblocks all Fabric item work; `bff-api`'s skeleton and the simulator's cloud/local publishers can proceed in parallel once `FAB-001`–`003` land. |
| **Wave 3 — Data core, read adapters, capacity lifecycle infra** | `FAB-004`, `FAB-005`, `FAB-006`, `FAB-007`, `BE-002`, `BE-003`, `INFRA-004`, `SIM-006` | The Lakehouse/KQL/semantic-model chain and the BFF's read/SSE adapters depend on the ingress items from Wave 2; the capacity-lifecycle Logic App can be built in parallel since it only needs `FAB-001`. |
| **Wave 4 — Domain services and AI** | `BE-004`, `BE-005`, `BE-006`, `BE-007`, `AI-001`, `AI-002`, `AI-003`, `AI-004`, `INFRA-005` | Optimizer/scoring workers, the audit ledger, capacity-operator routes, and both Foundry agents can proceed in parallel once the data core is queryable; Foundry provisioning (`INFRA-005`) should start at the beginning of this wave since regional/quota verification (§9.1 step 6 gate) can take longer than the code itself. |
| **Wave 5 — Frontend experience** | `FE-001`, `FE-002`, `FE-003`, `FE-004`, `FE-005` | Requires `BE-002`/`BE-003`/`BE-007` to be queryable; can otherwise proceed fully in parallel with Wave 4's backend-only items once those specific routes are stable (coordinate via contract tests, not calendar time). |
| **Wave 6 — CI/CD hardening and full-path testing** | `CI-001`–`CI-006`, `SEC-010`, `SEC-011` | Per-service CI should actually start in Wave 0 in skeletal form (lint/unit only); this wave is where the full contract/integration/E2E/security gate set is completed and made required, once there is a real cross-service path to test end to end. |
| **Wave 7 — Demo rehearsal and production-gate readiness** | Demo rehearsal (`deployment-topology.md` §8 step 8), production-gate checklist (§9.1 step 10) | Final integration: two consecutive successful 15-minute runs, every fallback level exercised offline, and the production-onboarding governance checklist reviewed — this is a go/no-go gate, not a coding task. |

**Explicit note for the fleet lead:** `FE-000` (npm protected feed resolution) and the Fabric/Foundry regional-availability and quota re-verification steps called out in `deployment-topology.md` §15 items 1–3 are the two most likely sources of calendar delay because they depend on an external approval or tenant check rather than engineering effort. Start both at the beginning of Wave 0/Wave 4 respectively, in parallel with coding work, rather than discovering the lead time mid-wave.
