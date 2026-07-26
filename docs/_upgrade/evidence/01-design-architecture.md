# NovaSteel — Design & Architecture Comparison (Criteria: System Architecture / Design Patterns / Architectural Security)

**Reviewer scope:** system architecture, modularity, scalability; use of design patterns; and *architectural* security (network topology, identity model, trust boundaries — not code-level security, which another reviewer covers).

---

## Executive verdict

Project B ("Novasteel 3") delivers a **substantially more mature, better-modularised and better-scaling architecture** than Project A. Where Project A is essentially a single-resource-group monolith with a decorative Fabric layer (public network access, one shared managed identity, empty `agents/` folder, no BFF, no service segmentation), Project B implements a real 6-resource-group hub-and-spoke, 7+ per-service managed identities, private endpoints on every stateful/AI service, deny-public-network Azure Policy guardrails, a Ports-and-Adapters BFF/worker split matched to a full v1 OpenAPI contract, and an explicit Fabric workspace-per-role model. Project A demonstrates domain depth (a real MILP dispatch solver, physics-informed RUL model, medallion Spark notebooks) that Project B lacks in production form (workers are ~14 KB each, Container Apps ship a quickstart placeholder image). Net: **B > A on architecture, patterns, and architectural security**, but A retains a meaningful edge on **domain algorithmic depth** which the jury may partly credit under criterion 1.

---

## Project A ("P1", `D:\work\20260507 - NovaSteel\NovaSteel`)

### Architecture summary

- **IaC**: 21 Bicep files (~64 KB). One resource group (`rg-<prefix>-<env>`) containing every Azure resource (`infrastructure\main.bicep:23-97`, `infrastructure\resources.bicep:1-306`).
- **Compute topology**: one Azure Functions plan (`modules\functions.bicep`), one Container Apps environment hosting a **single** simulator app (`modules\container-app-simulator.bicep`), one Fabric F-SKU capacity (`modules\fabric.bicep`), one Foundry AIServices account, one Event Hubs namespace, one IoT Hub, one ADLS Gen2 data lake, optional Azure SQL app-state store, Purview, ACR, Key Vault (`modules\keyvault.bicep`), Log Analytics + App Insights, and a nightly Fabric pause Logic App (`modules\fabric-pause-schedule.bicep`).
- **Fabric artefacts (`platform/`)**: real Spark notebooks and KQL for the medallion pipeline (`platform\medallion\bronze_telemetry.py`, `silver_telemetry.py`, `gold_marts.py`, `platform\rti\eventhouse.kql`, `eventstream-telemetry.json`) plus governance/KPI/BI modules. The `platform\agents\` directory exists **but is empty** despite `docs/usecase/First_Proposal/02-solution-architecture.md:37-45` promising a dispatch agent.
- **Application code (`workloads/`)**: Python modules per pillar — `p1_predictive_maintenance` (physics-informed RUL, PuLP-free), `p2_energy_dispatch` (heuristic + real **PuLP/CBC MILP** in `workloads\p2_energy_dispatch\milp.py:41-100`), `p3_quality`, `p4_knowledge_capture` (Foundry client, RAG library, capture flow). Runtime shape: these are libraries/CLI scripts and Fabric notebooks — **there is no BFF or API surface** exposing them to a UI.
- **Contracts (`libs/`)**: A **shared C# contract library** `NovaSteel.Contracts` (10 record types + tests) mirrored by a Python `novasteel_core` Pydantic library using `alias_generator=to_camel` (`libs\novasteel_core\novasteel_core\models.py:1-40`). This is a genuine cross-language DTO alignment story.
- **UI**: the "front-end" is a Razor Pages+SignalR simulator dashboard (`apps\steel_factory_simulator\src\SteelFactorySimulator\Program.cs`) whose primary purpose is to drive the simulator, not to be the operator portal. `website/` contains only a README.
- **Diagrams**: `docs/usecase/First_Proposal/02-solution-architecture.md` (11 KB) and `02a-fabric-iot-architecture.md` (22 KB) with a clear Mermaid diagram and pattern table.

### Evidence table (claim → file → verified?)

| Claim (from README/docs) | Cited implementation | Verified? |
|---|---|---|
| "Medallion (Bronze/Silver/Gold)" | `platform\medallion\bronze_telemetry.py`, `silver_telemetry.py`, `gold_marts.py`, `transforms.py` | ✅ Yes — real PySpark notebooks |
| "Energy-dispatch agent" | `platform\agents\` | ❌ **Empty folder** |
| "MILP optimizer (Solver.Milp)" | `workloads\p2_energy_dispatch\milp.py:41-100` (`import pulp`, `LpProblem`) | ✅ Yes — real MILP |
| "Physics-informed RUL model" | `workloads\p1_predictive_maintenance\rul_model.py:1-50, physics_features.py` | ✅ Yes — dataclass-based estimator |
| "RAG knowledge-capture" | `workloads\p4_knowledge_capture\{assistant,retrieval,foundry_client}.py` | ✅ Yes — library-level |
| "Cloud-direct IoT Hub" | `infrastructure\modules\iot-hub.bicep` | ✅ Yes |
| "Private networking via VNet + Private Endpoints" (`02-solution-architecture.md:119`) | `infrastructure\modules\*.bicep` | ❌ **No private endpoints anywhere**; every module explicitly sets `publicNetworkAccess: 'Enabled'` (`keyvault.bicep:31`, `event-hubs.bicep:54`, `foundry.bicep:53`) |
| "Least privilege" | `infrastructure\modules\rbac.bicep`, `identity.bicep` | ⚠ Partially — a **single** shared user-assigned identity (`identity.bicep`), plus function/container app **system-assigned** principals; roles wired centrally but no per-service split |
| "MLOps (registry + CI/CD)" | `.github\workflows\ci.yml` (1.5 KB), `simulator.yml`, `scheduled-batch.yml` | ⚠ Minimal — no image build/publish pipeline for pillars |
| "Full Fabric estate: OneLake, Eventhouse, Direct Lake, Purview" | `platform\rti\`, `platform\medallion\`, `platform\bi\semantic_model\`, `modules\purview.bicep` | ✅ Yes |

### Design patterns actually found

1. **Medallion (Bronze/Silver/Gold)** — `platform\medallion\bronze_telemetry.py:13-38`, `silver_telemetry.py`, `gold_marts.py`. Real, not just diagrammatic.
2. **Cross-language DTO / contract sharing** — `libs\NovaSteel.Contracts\*.cs` + `libs\novasteel_core\novasteel_core\models.py` with camelCase alignment (`_CamelModel`, `models.py:11-17`).
3. **Strategy / pluggable solver** — `workloads\p2_energy_dispatch\{dispatch_model.py, milp.py}`: heuristic vs. MILP behind the same `DispatchResult`/`EnergyPlan` contract (`milp.py:11-46`).
4. **Repository / append-only audit** — `libs\novasteel_core\novasteel_core\audit.py` and Bicep `modules\app-state.bicep` (optional Azure SQL audit store).
5. **Data-quality gate / quarantine** — `platform\medallion\bronze_telemetry.py:21-34` splits `clean` vs `quarantine` on provenance.
6. **Scheduled cost lever (Logic App)** — `modules\fabric-pause-schedule.bicep` uses `Microsoft.Fabric/capacities/suspend/action` at 02:00.
7. **Hosted service / dependency-injection** — `apps\steel_factory_simulator\src\.\Program.cs:12-30` (simulator).

**Missing / claimed-but-absent**: BFF, ports/adapters, per-service DI, circuit-breaker, retry, microfrontend, CQRS, hexagonal, event-driven pub/sub between services (there are no "services" in the microservice sense — it's a library monolith plus notebooks plus a simulator).

### Scalability assessment

- **Positive**: Fabric F-SKU is the scaling unit for analytics; medallion notebook shape is Spark-native and horizontally scalable inside Fabric; Event Hubs partition count parametrised.
- **Negative**: single resource group and single region deployment (`infrastructure\main.bicep:9-14` restricts to 3 EU regions but topology is single-site). No hub/spoke, no per-plant Event Hub, no per-plant identity, so the four-country requirement isn't reflected in the IaC. Container Apps environment holds only the simulator; no worker autoscale. No application-tier statelessness/DI/queue-worker split. `residency-exceptions.md` and `MANUAL_STEPS.md` acknowledge manual out-of-band work. Alerting via `monitoring-alerts.bicep` is scheduled queries only; no per-plant SLO fan-out.

### Architectural security assessment

- **Weak**: every stateful/AI service is **public**. `keyvault.bicep:31` — `publicNetworkAccess: 'Enabled'`, `networkAcls.defaultAction: 'Allow'`; `event-hubs.bicep:54` — public; `foundry.bicep:53` — `publicNetworkAccess: 'Enabled', disableLocalAuth: false`; `storage.bicep`, `iot-hub.bicep` similarly open. The module header comments even state "Demo configuration: public network access, no private endpoints" (`main.bicep:3`, `resources.bicep:2`).
- **Identity**: one user-assigned managed identity for "platform workloads" (`identity.bicep:13-17`) plus system-assigned identities on Functions/Container Apps; RBAC roles centralised in `rbac.bicep` (`Storage Blob Data Contributor`, `Key Vault Secrets User`, `Cognitive Services OpenAI User`, `AcrPull`) — reasonable role choices but a single "god identity" pattern.
- **Zero-trust**: not present. No VNet, no subnets, no NSGs, no private DNS zones, no Firewall, no Defender for IoT, no per-plant OT identity.
- **Governance**: Defender-for-Cloud plan (`modules\defender.bicep`), an EU-residency Azure Policy (`modules\policy.bicep`), Purview lineage (`modules\purview.bicep`). Good high-level intent, but not enforced by a `deny-public-network` policy.

---

## Project B ("P2", `D:\work\20260724 - Novasteel 3`)

### Architecture summary

- **IaC**: 18 Bicep files (~117 KB, ≈1.8× P1). One subscription-scoped orchestrator (`infra\bicep\main.bicep:1-500`) creates **6 purpose-scoped resource groups**: `rg-ns-<env>-{hub,integration,apps,ai,fabric,monitoring}` (`main.bicep:120-154`). Environments: `dev|test|demo|prod` (`main.bicep:19-25`). Regions locked to `swedencentral|westeurope`.
- **Networking**: `modules\network.bicep` — hub-and-spoke VNet with dedicated subnets (`hubServices`, `integration`, `apps`, `aiPrivateEndpoints`, `containerAppsInfra`), NSGs with explicit `Deny-Internet-Inbound`, private DNS zones for KeyVault/Blob/ServiceBus/CognitiveServices/OpenAI, optional Azure Firewall (`deployFirewall` param). Container Apps environment is VNet-integrated with `internal: true` ingress (`modules\containerapps.bicep:52-58, 106-110`).
- **Compute topology**: 5 real Container Apps (bff-api, optimizer-worker, scoring-worker, ingest-relay, knowledge-orchestrator) plus a Container Apps Job for the simulator, each with its own user-assigned managed identity (`modules\containerapps.bicep:91-145`). BUT: the images are `mcr.microsoft.com/k8se/quickstart:latest` **placeholder** (`containerapps.bicep:27`); real images arrive via `.github\workflows\cd-services.yml` which requires an immutable `@sha256:` digest.
- **Identity**: 7 permanent user-assigned managed identities — bff, worker, ingest-relay, knowledge, capacity, plus one `mi-ns-otgw-<plant>-<env>` **per plant** and an optional demo simulator identity (`modules\identity.bicep:37-80`). GitHub OIDC federated credential (`identity.bicep:23-35`), no client secrets.
- **Data plane security**: `keyvault.bicep:46` — `publicNetworkAccess: 'Disabled'`, `defaultAction: 'Deny'`, RBAC-only, purge protection on, private endpoint mandatory. `eventhubs.bicep:56-58` — `disableLocalAuth: true`, `publicNetworkAccess: 'Disabled'`, per-plant hub, per-plant Data Sender role scoped to that hub only, namespace-scope Data Receiver for the relay. `foundry-speech.bicep:55-60` — `publicNetworkAccess: 'Disabled', disableLocalAuth: true, defaultAction: 'Deny'` on both Foundry and Speech. `storage.bicep` — private endpoint. `foundry-speech.bicep` **provisions the account only** — no model deployment, no Agent Service project (gated behind `foundryAgentServiceManuallyValidated`).
- **Governance**: subscription-wide Azure Policy assignments (`modules\policy-assignments.bicep:12-56`) — `allowed locations`, mandatory tags (environment/dataClassification/owner/costCenter), Fabric SaaS-item deny guardrail, **`publicNetworkGuardrailEffect: 'Deny'`** by default, Fabric-SKU allow-list. Custom RBAC role `roles.bicep` for capacity-scoped operator. Budget alerts across all 6 RGs (`modules\budget.bicep`).
- **Fabric artefacts (`fabric/`)**: 5 Fabric notebooks, 2 data pipelines, KQL dashboard queries, semantic model exports (22 files), lakehouse definitions, deployment parameters per env, capacity/scripts. Explicit Git-integration/deployment-item shape.
- **Application code (`services/`)**:
  - `bff-api` (~130 KB Python): FastAPI factory (`main.py:57-80`), routes.py (42 KB, 15+ v1 endpoints), auth boundary with 8 role → action map (`auth.py:17-60`), append-only audit, idempotency store, SSE alert buffer, capacity **state machine** with 9 states (`capacity.py:11-23`), Ports & Adapters for capacity (`CapacityAdapter`, `ArmCapacityClient` Protocols — `capacity.py:34-60`), demo repository loader with checksum validation (`repository.py:29-60`).
  - `knowledge-orchestrator` (~82 KB Python): fully hexagonal — `adapters/base.py:1-46` defines `SpeechTranscriptionAdapter` and `FoundryAgentAdapter` ABCs, with `azure_*` and `local_*` implementations (`azure_foundry.py`, `local_foundry.py`, `azure_speech.py`, `local_speech.py`); domain modules for consent, procedure workflow, prompt defense, grounding, evaluation, tools.
  - `optimizer-worker` (14 KB): deterministic bounded-enumeration dispatch (`service.py:1-80`) with hard-constraint validation, versioned `model_version`, no commit path.
  - `scoring-worker` (8 KB): thin RUL/quality scorer.
  - `ingest-relay` (6 KB): Event Hubs consumer → Fabric Custom Endpoint stub.
- **Contracts (`contracts/`)**: JSON Schema event envelopes (`contracts\events\event-envelope.v1.schema.json`, telemetry, alarm, quality, inference, quarantine) + a single OpenAPI file `bff-api-v1.yaml` describing the full BFF surface + Delta schema definitions.
- **UI (`apps/`)**: **Blazor WASM shell** (`portal-shell/Program.cs:1-35`, MSAL, token-reference broker, capacity/shell state services) + **React/TypeScript microfrontend** (`analytics-mfe/src` — MUI, D3, api client with envelope/fixtures/httpClient split). Genuine microfrontend/BFF architecture per ADR-004.
- **Docs**: `docs\architecture\solution-architecture.md` (56 KB, 15 numbered sections + 10 ADRs) and `deployment-topology.md` (28 KB) with reconciliation table for conflicting research inputs — an unusually rigorous "authoritative architecture" document.

### Evidence table

| Claim | Cited implementation | Verified? |
|---|---|---|
| "Hub-and-spoke topology with private endpoints" | `modules\network.bicep`, `keyvault.bicep:66-90`, `eventhubs.bicep`, `foundry-speech.bicep`, `storage.bicep` (67 private-endpoint refs total) | ✅ Yes |
| "Public network access disabled" | `keyvault.bicep:46`, `foundry-speech.bicep:55-60`, `eventhubs.bicep:56-58` + `publicNetworkGuardrailEffect='Deny'` policy | ✅ Yes |
| "Per-service managed identities, no god identity" | `identity.bicep:37-80` — 7 base MIs + per-plant OT gateway MI | ✅ Yes |
| "GitHub OIDC, no client secret" | `identity.bicep:23-35` federated credential | ✅ Yes |
| "Custom capacity-only operator role" | `modules\roles.bicep` + `fabric-capacity.bicep` role assignment | ✅ Yes |
| "Ports & Adapters (hexagonal)" | `services\knowledge-orchestrator\src\knowledge_orchestrator\adapters\base.py:1-46`; `services\bff-api\src\bff_api\capacity.py:34-60` `Protocol` | ✅ Yes |
| "BFF + React MFE + Blazor shell (ADR-004)" | `apps\portal-shell\Program.cs`, `apps\analytics-mfe\src\api\{httpClient,envelope}.ts`, `services\bff-api` | ✅ Yes |
| "Deterministic optimizer, human-approval required, no commit" | `services\optimizer-worker\src\optimizer_worker\service.py:1-80` | ✅ Yes (but very small; not MILP) |
| "Physics-informed RUL model" | `services\scoring-worker\src\scoring_worker\service.py` (8 KB stub) | ⚠ Placeholder-level implementation |
| "Container Apps host the 5 services in production shape" | `modules\containerapps.bicep:91-145` | ⚠ **Placeholder image only** (`mcr.microsoft.com/k8se/quickstart:latest`); real image via `cd-services.yml` at deploy time |
| "Dockerfiles for every service" | only `services\bff-api\Dockerfile` exists | ❌ Other 4 services lack a Dockerfile |
| "Fabric provisioning is out of scope for Bicep; only capacity" | `main.bicep:1-16` explicit scope discipline; only `Microsoft.Fabric/capacities` present | ✅ Yes |
| "Sentinel + Log Analytics + budget alerts" | `modules\monitoring.bicep`, `budget.bicep`, `main.bicep:186-189` | ✅ Yes |
| "MLOps / actual physics-informed RUL / real MILP" | `services\scoring-worker` (small), `services\optimizer-worker` (bounded enumeration) | ❌ Domain depth lower than P1 |

### Design patterns actually found

1. **Ports & Adapters (Hexagonal)** — `services\knowledge-orchestrator\src\knowledge_orchestrator\adapters\base.py:18-46` (`SpeechTranscriptionAdapter`, `FoundryAgentAdapter` ABCs with 2 implementations each). Also `bff-api\src\bff_api\capacity.py:34-60` (`CapacityAdapter`, `ArmCapacityClient` `Protocol`s with `LocalCapacityAdapter`/`UnconfiguredArmCapacityAdapter`).
2. **Backend-for-Frontend** — the entire `services\bff-api` (`main.py:57-80`; `routes.py` 42 KB) is a canonical BFF: authorization, response shaping, SSE, audit-initiation, mediation — never returning workload credentials to the browser (§8.1 of solution-architecture.md).
3. **Microfrontend + host shell** — `apps\portal-shell` (Blazor WASM) hosts `apps\analytics-mfe` (React) via typed same-page interop (§5.1 of solution-architecture.md, `bridge.tsx`).
4. **Composition Root / Dependency Injection** — `services\bff-api\src\bff_api\services.py:32-76` (`BffServices.create` wires repository/auth/audit/idempotency/events/capacity/knowledge/optimizer/scorer).
5. **State machine** — Capacity lifecycle 9-state machine (`bff-api\src\bff_api\capacity.py:11-23`) mirrored by the deployment-topology.md §5.1 Mermaid diagram.
6. **Append-only audit + idempotency-key** — `bff-api\src\bff_api\{audit,idempotency}.py`, propagated as `Idempotency-Key` per API contract (§5.3).
7. **Medallion + Quarantine** — `contracts\data\`, `fabric\notebooks\ns-bronze-to-silver.Notebook`, silver→gold, `ns-validate-data-quality.Notebook`; deliberate silver-as-single-dedup contract.
8. **Event-driven ingestion with buffered relay** — Event Hubs → identity-based relay → Fabric Custom Endpoint (§4.1 sequence diagram; `services\ingest-relay`).
9. **Correlation ID + envelope contract** — every API response wraps `{items,total,page,size,asOf,correlationId}` (§5.3; `bff-api\src\bff_api\contracts.py`).
10. **Custom RBAC role + policy-as-code** — `infra\bicep\modules\roles.bicep` (custom Fabric-capacity operator role), `policy-assignments.bicep` (deny-public-network, allowed-locations, mandatory tags, Fabric SKU allow-list).
11. **Strategy on demo vs cloud adapters** — `LocalCapacityAdapter` vs `UnconfiguredArmCapacityAdapter`; `local_foundry`/`azure_foundry`.
12. **Cost-lever scheduled action** — Logic App capacity lifecycle at 01:00 Europe/Luxembourg (`modules\logicapp-capacity-lifecycle.bicep`, deployment-topology.md §5.3), non-prod only.
13. **Explicit ADRs (10)** — `solution-architecture.md` §10 (ADR-001..010) codifies decisions.

### Scalability assessment

- **Positive**: per-plant Event Hub + per-plant OT identity (`eventhubs.bicep:63-72`, `identity.bicep:68-74`) natively supports the four-country requirement. 6 resource groups with per-context Key Vaults (platform vs OT gateway) contain blast radius. Container Apps autoscale `minReplicas: 0, maxReplicas: 3` (`containerapps.bicep:138-141`) — small but real. Stateless BFF (in-memory audit/idempotency in demo mode is explicit and swap-in point exists via services composition root). Explicit F2→F4 sizing policy with measurement gate. West Europe named as contingency, not silent replica.
- **Negative**: only one Container Apps environment per env (no multi-region), `zoneRedundant: false` on Container Apps env and Event Hubs (`containerapps.bicep:56`, `eventhubs.bicep:59`) — acceptable for demo but not for the "production" narrative. Workers are single-instance placeholders; there is no queue/broker splitting jobs across workers. Idempotency store is in-memory. Fabric semantic-model side is sized at F2 and needs measurement uplift.

### Architectural security assessment

- **Strong network posture**: private endpoints on every stateful service (Key Vault ×2, Storage ×2, Event Hubs, Foundry, Speech), private DNS zones (`network.bicep`), NSG deny-Internet-inbound + explicit outbound allow-lists (integration subnet allows outbound 443 to Event Hubs only), internal-only Container Apps ingress, optional Azure Firewall for prod.
- **Strong identity model**: 7 permanent per-service user-assigned MIs + one per plant, `disableLocalAuth: true` on Event Hubs and Cognitive Services, RBAC-only Key Vaults, GitHub OIDC federated identity for CI (no PAT/client-secret in workflow). BFF is the single enforcement point (`bff-api\src\bff_api\auth.py`, ADR-006/007); browser never sees a workload credential (ADR-004 §8.1 identity boundaries).
- **Governance guardrails**: subscription-wide **`Deny` public-network-access** policy, allowed-locations, mandatory tags, Fabric-SaaS-item Deny, budget alerts across all 6 RGs, Sentinel default on. Soft-delete + purge-protection mandatory on Key Vault.
- **OT boundary**: Purdue-style DMZ, one-way OT→IT, per-plant identity, Event Hubs Data Sender scoped to *this plant's* hub only; relay is namespace-scope Data Receiver in the isolated ingress workspace.
- **Weaknesses**: OT DMZ gateway is documented but not provisioned (deliberately — it lives on-prem); Container Apps environment `zoneRedundant: false`; capacity Contributor for the demo Logic App is a wider role than desired (acknowledged in ADR-005).

---

## Head-to-head comparison

| Dimension | Project A | Project B |
|---|---|---|
| Resource groups | 1 | 6 (hub/integration/apps/ai/fabric/monitoring) |
| Bicep modules (files/bytes) | 21 / ~64 KB | 18 / ~117 KB |
| Private endpoints in IaC | 0 (public everywhere by design) | ≥6 services + DNS zones |
| Managed identities | 1 shared user-assigned + system-assigned | 7 per-service + per-plant OT gateway |
| Per-plant identity/hub | ❌ | ✅ (`identity.bicep`, `eventhubs.bicep`) |
| Subscription Azure Policy | EU residency only | Allowed-locations + tags + **deny-public-network** + Fabric guardrails |
| GitHub OIDC | ❌ | ✅ federated credential |
| BFF / API layer | ❌ (no HTTP API to workloads) | ✅ FastAPI with 15+ v1 routes, SSE, audit, idempotency |
| Frontend | Razor Pages simulator | Blazor WASM shell + React/TS MFE |
| Contract-first | C# + Python DTO parity | JSON Schema events + OpenAPI + Delta contracts |
| Design patterns visibly implemented | Medallion, Strategy (MILP), DI (simulator) | Ports & Adapters, BFF, Microfrontend, State machine, Composition Root, DI, Medallion, ADRs, Policy-as-code |
| ADRs | Constitution + principles doc | 10 numbered ADRs + reconciliation table |
| Domain algorithm depth (RUL / MILP / RAG) | **Higher** (real PuLP MILP; physics features; RAG library) | Lower (bounded-enumeration optimizer; small scorer) |
| Fabric artefacts (notebooks/pipelines/semantic model) | 8 medallion + 4 RTI + BI semantic model | 5 notebooks + 2 pipelines + KQL + 22-file semantic model + deployment params |
| Multi-country / 4-site reflected in IaC | ❌ | ✅ (`plants` array parameter, per-plant hub/identity) |
| Scheduled capacity cost lever | Logic App 02:00 UTC (2-4 KB) | Logic App 01:00 Europe/Luxembourg with drain checks + custom role (6 KB) |
| Test topology | 15 test dirs scattered under workloads/platform | Central `tests/{contract,integration,e2e,knowledge,simulator,infra,backend}` (89 files) |
| Container image production shape | 1 real simulator app image | 5 placeholder + `cd-services.yml` immutable-digest gated |

---

## Proposed scores

Scale: 5 Excellent · 4 Good · 3 Satisfactory · 1-2 Needs Improvement.

### Criterion 1 — System architecture, modularity, scalability

- **Project A: 3 (Satisfactory)** — a coherent single-region demo architecture with real medallion notebooks and cross-language contracts, but flat single-RG topology, no per-plant modelling for the 4-country requirement, missing BFF/service layer, and one empty `agents/` folder betray a plan-vs-code gap.
- **Project B: 5 (Excellent)** — clear layered 6-RG hub-and-spoke, four-country requirement expressed in IaC via per-plant hub + per-plant identity, real service boundaries (bff/workers/relay/orchestrator) with a stateless BFF and typed contract, explicit environments (dev/test/demo/prod), authoritative 56 KB architecture doc + 28 KB topology doc, 10 ADRs. Docked half-notionally for placeholder Container Apps images.

### Criterion 2 — Use of design patterns

- **Project A: 3 (Satisfactory)** — Medallion, Strategy (heuristic/MILP), DI in the simulator, quarantine gate, contract sharing. Patterns are real but confined; no BFF, no ports-and-adapters, no state machine, no ADRs formalising decisions.
- **Project B: 5 (Excellent)** — Ports & Adapters, BFF, microfrontend, composition root, state machine, idempotency, correlation-envelope, policy-as-code, 10 ADRs, medallion+quarantine, adapter Strategy for demo/cloud. Broad, well-cited, and code-backed.

### Criterion 3 — Security (architectural)

- **Project A: 2 (Needs Improvement)** — every module explicitly enables public network access; a single shared managed identity; no VNet/private endpoints/private DNS; no OT identity segmentation; policy limited to EU residency. Docs promise private networking but IaC does the opposite.
- **Project B: 5 (Excellent)** — private endpoints everywhere; RBAC-only Key Vaults with public access disabled; disableLocalAuth on Event Hubs/Cognitive Services; 7+ per-service MIs plus per-plant OT identity; GitHub OIDC (no secrets); subscription-wide deny-public-network policy; explicit identity boundaries in §8.1; capacity-scoped custom role; Sentinel on by default.

---

## Top 5 concrete fixes — Project A

1. **Add a BFF/API layer between UI/notebooks and the pillar libraries.** Right now `workloads\p1..p4` are only importable Python modules; expose them via an authenticated FastAPI or ASP.NET Core service so operators (and the simulator's Razor UI) don't call them via direct in-process imports. Wire it into `apps\` and put it in a new `apps\bff\` project referenced by `NovaSteel.slnx`.
2. **Split the single managed identity and enable private endpoints.** Add per-workload user-assigned MIs (function, container-app-simulator, future BFF, per-plant OT identity) in `infrastructure\modules\identity.bicep`, and flip `publicNetworkAccess` to `Disabled` on `modules\{keyvault,storage,event-hubs,iot-hub,foundry}.bicep`. Introduce a new `modules\network.bicep` (VNet + subnets + private DNS zones) and re-wire each stateful module to accept a `privateEndpointSubnetId`.
3. **Model the four countries in IaC.** Parameterise `plants: array` (as P2 does) in `infrastructure\main.bicep`, and create one Event Hub + one OT-gateway identity per plant in `modules\event-hubs.bicep` and `modules\identity.bicep`. Today the four-country business requirement is invisible to the deployment.
4. **Implement the missing `platform\agents\` code.** The directory exists but is empty while `docs/usecase/First_Proposal/02-solution-architecture.md:42-45` describes an energy-dispatch agent. Either move `workloads\p2_energy_dispatch\decision_service.py` behind a Foundry Agent Service adapter here, or delete the folder and correct the doc.
5. **Add an Azure Policy assignment to deny public-network-access and enforce mandatory tags.** Extend `infrastructure\modules\policy.bicep` beyond EU-residency with `Deny publicNetworkAccess=Enabled` and mandatory `owner/costCenter/dataClassification/environment` tags; add a subscription-scope budget alert (P1 has none, so cost governance rests only on the nightly pause).

## Top 5 concrete fixes — Project B

1. **Ship real Dockerfiles and images for the 4 non-BFF services.** `services\{optimizer-worker,scoring-worker,ingest-relay,knowledge-orchestrator}\` have no `Dockerfile` yet `.github\workflows\cd-services.yml` promotes them by immutable digest. Add Dockerfiles + a `ci-build-services.yml` that publishes signed images to an approved registry so `cd-services.yml` has something to promote — otherwise `infra\bicep\modules\containerapps.bicep:27`'s `mcr.microsoft.com/k8se/quickstart:latest` remains the deployed reality.
2. **Deepen the domain algorithms.** `services\optimizer-worker\src\optimizer_worker\service.py` is a 14 KB bounded-enumeration heuristic; `services\scoring-worker\src\scoring_worker\service.py` is 8 KB. Import (or port) Project A's PuLP MILP (`workloads\p2_energy_dispatch\milp.py`) and physics-informed RUL (`workloads\p1_predictive_maintenance\rul_model.py`) so the "physics-informed" and "constraint-aware optimization" claims in `docs\architecture\solution-architecture.md:14-19` are backed by code, not by a deterministic proposal shape.
3. **Add zone-redundancy and second-region parameters where prod is claimed.** `infra\bicep\modules\containerapps.bicep:56` and `eventhubs.bicep:59` set `zoneRedundant: false`; make it `zoneRedundant: isProd` and add a `secondaryLocation` parameter that provisions a passive West-Europe replica shell for BFF/Event Hubs, so ADR-003's "West Europe is a tested EU contingency" is exercised.
4. **Persist audit + idempotency out of process.** `services\bff-api\src\bff_api\{audit.py,idempotency.py}` are in-memory. Introduce a `services\bff-api\src\bff_api\adapters\` folder (mirroring the knowledge-orchestrator hexagonal pattern) with an Azure Table/Cosmos/Storage adapter for both, so BFF can scale horizontally beyond one replica and the "append-only auditable" guarantee survives a restart.
5. **Fabric-item CI and workspace bootstrap.** `fabric\` holds notebooks/pipelines/semantic-model definitions and `.github\workflows\cd-fabric-items.yml` exists, but there is no evidence that the `NS-<env>-{RTI-Ingress,DataCore,ML,Analytics}` workspaces themselves get created (Fabric REST/CLI). Add `infra\scripts\` or a `fabric\scripts\bootstrap-workspaces.ps1` that creates the four workspaces from `fabric\deployment-parameters\<env>.json`, assigns them to the capacity, and applies OneLake roles — otherwise `solution-architecture.md:138-146`'s workspace isolation is a doc-only claim.
