# 13 · Platform Ops

**Audience:** complete newcomer to steel and cloud platform operations  
**Reading time:** 20 minutes  
**Persona:** Nils Andersen — Platform Ops  
**Routes covered:** `/{site}/platform-ops/capacity`, `/{site}/platform-ops/jobs`, `/{site}/platform-ops/cost-telemetry`, shell capacity dialog  
**Last updated:** 2026-07-27  
**Language:** 🇫🇷 [Version française](../fr/13-platform-ops.md)

---

## Fabric Capacity — `/{site}/platform-ops/capacity`
![Platform capacity](../screenshots/platform-ops-capacity.png)

**In one sentence.** A run-the-platform screen for Microsoft Fabric capacity state, safe non-production start/pause, and lifecycle audit (`apps\analytics-mfe\src\components\screens\PlatformCapacity.tsx`; `docs\personas\personas-and-journeys.md`).

**Background for newcomers.** Microsoft Fabric is Microsoft’s analytics platform for Lakehouse data, pipelines, real-time analytics, notebooks, semantic models and Power BI reports (`docs\README.md`; `docs\architecture\solution-architecture.md`). A **Fabric capacity** is the compute reservation that runs those workloads. An **F-SKU** is its size; NovaSteel allows only F2, F4 and F8 in the demo. Capacity units scale linearly, so F4 is about 2× F2 per hour and F8 about 4× (`apps\portal-shell\README.md`; `PlatformCapacity.tsx`). Pausing a non-production capacity overnight saves money; NovaSteel has a 01:00 Europe/Luxembourg pause check for dev/test/demo, never production (`docs\operations\operations-and-cost.md`; `infra\bicep\modules\logicapp-capacity-lifecycle.bicep`).

**What you see on screen.**
1. KPI cards show Capacity state, SKU, Environment and Lifecycle policy. In the screenshot the state is Paused/Simulated, SKU F2, environment demo and policy 01:00 Europe/Luxembourg (`PlatformCapacity.tsx`).
2. The blue Demo mode note says transitions are simulated and no Azure Resource Manager (ARM) operation fires (`PlatformCapacity.tsx`).
3. The **Fabric capacity (read-only mirror)** panel says the shell top-bar capacity panel is authoritative; the microfrontend never calls ARM directly (`PlatformCapacity.tsx`; `apps\portal-shell\README.md`).
4. Capacity ID, Sweden Central region, budget and reason are shown (`PlatformCapacity.tsx`).
5. **Request start** and **Request pause** are enabled only for `Platform.Capacity.Manage` and valid states; mid-transition states lock mutations (`PlatformCapacity.tsx`; `CapacityState.cs`).
6. The Recent transitions table lists Time, Actor, From, To, Reason and Correlation. The screenshot shows Paused → Resuming → ReadinessCheck → Running fixture transitions (`PlatformCapacity.tsx`; `apps\analytics-mfe\src\api\fixtures.ts`).

**Why this component was implemented.** NovaSteel’s business screens depend on analytics being available, but the local baseline is synthetic and cost-conscious (`docs\README.md`). Platform Ops makes capacity availability, cost control and audit explicit (`docs\operations\operations-and-cost.md`; `docs\ux\dashboard-specification.md`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Analytics platform availability | Platform support | Capacity state, SKU, lifecycle policy, transitions | `PlatformCapacity.tsx` → `DataClient.getCapacity()` → `GET /v1/platform/capacity` (`routes.py`) → local or ARM adapter (`capacity.py`). |
| Cost-aware lifecycle | Platform support | 01:00 Europe/Luxembourg policy | Runbook in `docs\operations\operations-and-cost.md`; trigger in `infra\bicep\modules\logicapp-capacity-lifecycle.bicep`. |
| Role-gated mutation | Platform support | Start/pause controls depend on role and state | `PlatformCapacity.tsx`; `CapacityState.cs`; `_capacity_mutation()` in `routes.py`. |
| No browser-to-ARM call | `REG-02` boundary | Read-only mirror text | `PlatformCapacity.tsx`; shell/BFF design in `apps\portal-shell\README.md` and `CapacityService.cs`. |

**How the data reaches this screen.** `PlatformCapacity.tsx` → `client.getCapacity()` → `GET /v1/platform/capacity` → BFF `services.capacity.status()` → `LocalCapacityAdapter` or ARM adapter (`apps\analytics-mfe\src\api\dataClient.ts`; `services\bff-api\src\bff_api\routes.py`; `services\bff-api\src\bff_api\capacity.py`). Start/pause emits `capacity.request` to the shell (`PlatformCapacity.tsx`; `apps\portal-shell\Services\CapacityService.cs`).

**Honesty & caveats.** Demo Mode is deterministic simulation. The local baseline has not proven a real Fabric tenant capacity or Power BI workspace (`docs\README.md`). Production is never automatically paused (`docs\operations\operations-and-cost.md`).

**Try it yourself.** Open `http://localhost:5266/{site}/platform-ops/capacity` and inspect transitions or open the top-bar Fabric panel.

---

## Jobs & Pipelines — `/{site}/platform-ops/jobs`
![Platform jobs](../screenshots/platform-ops-jobs.png)

**In one sentence.** A table showing whether data jobs and pipelines are running, succeeded or failed (`apps\analytics-mfe\src\components\screens\PlatformJobs.tsx`).

**Background for newcomers.** A **job** is one execution. A **pipeline** is a repeatable data process. NovaSteel uses a medallion pattern: bronze is raw-ish data, silver is cleaned data, and gold is business-ready data for dashboards (`docs\README.md`; `docs\operations\operations-and-cost.md`). If a pipeline is stale, the dashboard may be stale.

**What you see on screen.**
1. The Jobs & Pipelines tab is selected (`PlatformJobs.tsx`).
2. The table columns are Run id, Pipeline, Status, Started, Duration (s) and Actor, using the shared table standard (`PlatformJobs.tsx`; `docs\ux\dashboard-specification.md`).
3. The screenshot shows `semantic-refresh` RUNNING and `bronze-to-silver`, `silver-to-gold`, `contract-assertions`, `quarantine-negative-tests` SUCCEEDED (`apps\analytics-mfe\src\api\fixtures.ts`).
4. The component reloads the deterministic set every 12 seconds to mimic operational telemetry (`PlatformJobs.tsx`).

**Why this component was implemented.** Energy, CO₂, furnace, quality and knowledge decisions are only credible if their data pipelines are healthy. The operations document requires monitoring pipeline duration, freshness, reconciliation and quarantine (`docs\operations\operations-and-cost.md`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Data freshness for all screens | Cross-cutting evidence | Pipeline run table | No live BFF route; `PlatformJobs.tsx` loads `jobs()` from `apps\analytics-mfe\src\api\fixtures.ts`. |
| Bronze→silver→gold path | `OBJ-01`…`OBJ-04` support | Rows for bronze-to-silver and silver-to-gold | Fixture rows in `fixtures.ts`; medallion assets described in `docs\README.md`. |
| Contract/quarantine checks | Governance support | Rows for contract assertions and quarantine tests | `fixtures.ts`; operations expectations in `docs\operations\operations-and-cost.md`. |

**How the data reaches this screen.** `PlatformJobs.tsx` → `jobFixture()` → `apps\analytics-mfe\src\api\fixtures.ts` → no BFF route. Rows are wrapped as source `fixture` and polled (`PlatformJobs.tsx`).

**Honesty & caveats.** This is synthetic platform telemetry, not a live Fabric run-history API in the local baseline (`PlatformJobs.tsx`; `docs\README.md`).

**Try it yourself.** Open `http://localhost:5266/{site}/platform-ops/jobs`, then search for `gold` or sort by Started.

---

## Cost & Telemetry — `/{site}/platform-ops/cost-telemetry`
![Platform cost telemetry](../screenshots/platform-ops-cost-telemetry.png)

**In one sentence.** A FinOps view showing synthetic spend, hourly cost, utilization and telemetry freshness (`apps\analytics-mfe\src\components\screens\PlatformCost.tsx`).

**Background for newcomers.** **Telemetry** means measurements emitted by systems: cost, utilization, freshness, failures and latency. **FinOps** is the practice of managing cloud spending with engineering and finance discipline. For Fabric, both capacity size and run time matter (`docs\operations\operations-and-cost.md`; `apps\portal-shell\README.md`).

**What you see on screen.**
1. KPI cards show Spend to date €35, Cost/hour €3, Utilization 38% and Freshness 12 s; the component says these are synthetic, not an Azure invoice (`PlatformCost.tsx`).
2. **Cost trend** is a line chart over the demo window (`PlatformCost.tsx`; `fixtures.ts`).
3. **Capacity utilization** is a green area chart; very low overnight utilization supports pausing (`PlatformCost.tsx`; `docs\operations\operations-and-cost.md`).
4. Tooltips warn that a real €/hour value depends on region, currency and offer (`PlatformCost.tsx`; `docs\presentation\faq.md`).

**Why this component was implemented.** The platform must prove not only technical health but also cost discipline. The operations plan requires capacity cost, utilization, budget alerts and cost review (`docs\operations\operations-and-cost.md`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Cost-aware platform operation | Platform support | Spend, cost/hour, utilization, freshness cards | No live BFF route; `PlatformCost.tsx` computes from `costTrend()` in `apps\analytics-mfe\src\api\fixtures.ts`. |
| Pause justification | Platform support | Utilization chart and capacity policy | Fixture in `fixtures.ts`; pause runbook in `docs\operations\operations-and-cost.md`. |
| Honest price caveat | Governance support | Synthetic placeholder tooltip | `PlatformCost.tsx`; `docs\presentation\faq.md`. |

**How the data reaches this screen.** `PlatformCost.tsx` → `costTrend()` → `apps\analytics-mfe\src\api\fixtures.ts` → no BFF route. The visual layer uses shared D3 chart containers (`PlatformCost.tsx`; `docs\ux\dashboard-specification.md`).

**Honesty & caveats.** Do not quote €3/hour as a Microsoft Fabric price. It is illustrative; real pricing depends on region, currency, commercial offer, SKU and measured capacity-unit consumption (`PlatformCost.tsx`; `docs\presentation\faq.md`).

**Try it yourself.** Open `http://localhost:5266/{site}/platform-ops/cost-telemetry` and hover the KPI cards.

---

## Shell-owned Fabric capacity dialog — `/{site}/platform-ops/capacity` plus top-bar Fabric pill
![Fabric capacity panel](../screenshots/feature-capacity-panel.png)

**In one sentence.** The authoritative control surface for capacity start, pause and SKU change; it belongs to the Blazor shell, not the React microfrontend (`apps\portal-shell\Components\CapacityPanel.razor`; `apps\portal-shell\README.md`).

**Background for newcomers.** **ARM** means Azure Resource Manager, Azure’s control-plane API. Browsers should not call ARM directly because capacity changes require role checks, allow-lists, audit records, idempotency and managed identity. NovaSteel routes browser actions through the shell and FastAPI Backend-for-Frontend (BFF) (`apps\portal-shell\Services\CapacityService.cs`; `services\bff-api\src\bff_api\routes.py`).

**What you see on screen.**
1. The right-side dialog opens from the top-bar Fabric pill and dims the app (`CapacityPanel.razor`).
2. State is **Paused** and the Simulated note says no ARM operation fires (`CapacityPanel.razor`; `CapacityState.cs`).
3. Facts show capacity ID, SKU F2, environment demo, Sweden Central region and Live BFF/Simulated source (`CapacityPanel.razor`).
4. The policy line repeats 01:00 Europe/Luxembourg, non-production only (`CapacityPanel.razor`; `logicapp-capacity-lifecycle.bicep`).
5. The Reason field makes every request auditable (`CapacityPanel.razor`; `routes.py`).
6. The SKU selector offers only F2, F4 and F8; Apply SKU is disabled without `Platform.Capacity.Manage`, during transitions or when unchanged (`CapacityPanel.razor`; `CapacityState.cs`).
7. Start and pause buttons are state-aware and role-gated; transition history appears below (`CapacityPanel.razor`; `CapacityService.cs`).

**Four-place SKU allow-list enforcement.**

| Place | Enforcement | Source |
|---|---|---|
| Azure Policy | `restrict-fabric-capacity-sku` allows F2/F4/F8 | `infra\policy\definitions\restrict-fabric-capacity-sku.json` |
| Bicep | `fabricSkuName` has `@allowed(['F2','F4','F8'])` | `infra\bicep\main.bicep` |
| BFF | `SCALABLE_SKUS = ('F2','F4','F8')` and request validation | `services\bff-api\src\bff_api\capacity.py`; `routes.py` |
| Shell fallback | `DefaultSkuOptions = ['F2','F4','F8']` | `apps\portal-shell\Services\CapacityState.cs` |

`tests\infra\test_capacity_sku_allow_list.py` pins all four layers together, so the portal cannot silently offer a SKU that policy rejects.

**Idempotency key.** Every mutating request includes an `Idempotency-Key`; repeated same-key/same-body calls replay safely, while same-key/different-body calls conflict (`CapacityService.cs`; `services\bff-api\src\bff_api\idempotency.py`; `docs\implementation\api-contracts.md`).

**Why the microfrontend never owns the control surface.** The Blazor shell owns identity, top bar, routing and capacity panel. The React microfrontend may display status or request the panel, but it never owns workload credentials and never calls ARM (`apps\portal-shell\README.md`; `docs\ux\dashboard-specification.md`).

**Why this component was implemented.** The use case depends on a Fabric-centered platform, but the local baseline is synthetic and cost-aware. The dialog makes capacity spend visible, reversible and audited while protecting production (`docs\README.md`; `docs\operations\operations-and-cost.md`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Capacity lifecycle control | Platform support | State, SKU, policy, reason, start/pause | `CapacityPanel.razor` → `CapacityState` → `CapacityService` → `/v1/platform/capacity/*` (`routes.py`). |
| Role gate | Platform support | Read-only message without `Platform.Capacity.Manage` | `CapacityPanel.razor`; `CapacityState.cs`; `_capacity_mutation()` (`routes.py`). |
| SKU governance | Platform support | F2/F4/F8 dropdown only | Policy, Bicep, BFF and shell allow-lists pinned by `test_capacity_sku_allow_list.py`. |
| No ARM from browser | `REG-02` boundary | BFF-only service design | `CapacityService.cs` calls BFF; `capacity.py` contains ARM adapter boundary. |
| Deterministic fallback | Demo reliability | Local simulation if BFF is unavailable | `CapacityState.cs`; `LocalCapacityAdapter` in `capacity.py`. |

**How the data reaches this screen.** Fabric pill → `CapacityPanel.razor` → `CapacityState.RefreshAsync()` → `CapacityService.GetStatusAsync()` → `GET /v1/platform/capacity` → BFF capacity adapter. Start, pause and SKU change use `POST /v1/platform/capacity/start-requests`, `pause-requests`, and `sku-requests` with an idempotency key (`CapacityPanel.razor`; `CapacityState.cs`; `CapacityService.cs`; `routes.py`).

**Honesty & caveats.** In local/demo mode, no ARM call fires. Azure Policy alias support for Fabric capacity SKU is documented as needing target-tenant verification before switching the effect to Deny (`infra\bicep\modules\policy-assignments.bicep`). The local baseline has not proven real tenant capacity lifecycle behavior (`docs\README.md`).

**Try it yourself.** Open any page, click the top-bar **Fabric** pill, inspect the SKU dropdown, enter a reason and try a permitted action based on the simulated state.

---

[◀ Previous: 12 · Proof of Execution](12-proof-of-execution.md) · [▲ Index](README.md) · [Next ▶ 14 · Cross-cutting Features](14-cross-cutting-features.md)
