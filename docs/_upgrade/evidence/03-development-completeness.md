# NovaSteel Jury Review — Development Completeness (A vs B)

*Empirical comparison of two competing implementations of the NovaSteel use case.
Measurements taken 2026‑07‑25 against the on‑disk repositories.*

- **Project A**: `D:\work\20260507 - NovaSteel\NovaSteel`
- **Project B**: `D:\work\20260724 - Novasteel 3`

---

## Executive verdict

Both projects contain real, running code — neither is vapor. But they are optimized for
very different jury moments.

- **Project A** is a *scientifically stronger* Fabric‑centric ML library: physics‑informed
  linear RUL, a real PuLP/CBC MILP + greedy heuristic for energy dispatch, SPC drift
  detection, and a grounded RAG assistant with citation enforcement, PII redaction and
  Content Safety. It runs **81 pytest cases in 1.45 s** and its algorithms are of production
  shape. Its critical weakness for an executive audience is that **it has no runnable web UI
  or HTTP API in the repo**. The "demo" is an aspirational narrative script pointing at
  dashboards/Copilot/Teams that do not exist as code here — you cannot walk a jury through
  buttons and screens.

- **Project B** is a *product‑shaped, end‑to‑end demo platform*: Blazor WASM portal‑shell,
  React micro‑frontend with **20 dashboards**, a FastAPI BFF exposing **32 domain endpoints
  + `/health/live` + `/health/ready` + `/v1/meta`** with correlation‑IDs, idempotency,
  RBAC, error envelopes, and an in‑repo **15‑minute demo runbook + a scripted `drive_demo.py`
  that already recorded a full rehearsal (11 moments, 0.31 s total server time)**. It runs
  **206 pytest cases + 29 vitest cases** and its per‑capability domain logic (scoring‑worker,
  optimizer‑worker, knowledge‑orchestrator) is deterministic and testable. Its critical
  weakness is that some of the **quantitative claims come from calibration constants, not
  physics** — e.g. CO₂ savings are computed as `savings_pct × 0.84`, peak reduction is
  clamped to `[3 %, 7 %]`, RUL is `(thickness − 300) / rate`. Algorithmically shallower
  than A, but far more show‑ready.

For a **rubric that scores "Application Demo" and "Implementation completeness" against a
compelling executive walk‑through**, **B is materially ahead on demo, roughly tied on
completeness (more features, thinner algorithms), and stronger on reliability plumbing**
(retries, timeouts, health, idempotency, audit hash‑chain). A is the better science and
weaker showcase.

---

## Code inventory (files & LOC, excluding node_modules, .venv, v/, bin/obj, dist, build, __pycache__, package‑lock.json)

### Project A — `20260507 - NovaSteel\NovaSteel`

| Language / kind | Files | LOC     |
|-----------------|------:|--------:|
| Python (`.py`)  | 70    | 4 658   |
| C# (`.cs`)      | 38    | 1 814   |
| TypeScript / TSX / React | 0 | 0 |
| Blazor `.razor` | 0     | 0       |
| Bicep           | 21    | 1 734   |
| JSON            | 32    | 4 089   |
| KQL             | 3     | 152     |
| YAML (`.yml`)   | 9     | 422     |
| Markdown        | 142   | 12 408  |

Structure: `workloads/p1_predictive_maintenance`, `workloads/p2_energy_dispatch`,
`workloads/p3_quality`, `workloads/p4_knowledge_capture`, `platform/{medallion,kpi,governance,rti,bi,scripts}`,
`libs/{novasteel_core, NovaSteel.Contracts, NovaSteel.Contracts.Tests}`,
`apps/steel_factory_simulator` (ASP.NET Core simulator with 3 Razor Pages), `infrastructure/*.bicep`,
`website/` (only `README.md` — no site code).

### Project B — `20260724 - Novasteel 3`

| Language / kind | Files | LOC       |
|-----------------|------:|----------:|
| Python (`.py`)  | 123   | 14 233    |
| C# (`.cs`)      | 7     | 508       |
| TypeScript (`.ts`) | 27 | 2 679     |
| TSX (React)     | 50    | 4 986     |
| Blazor `.razor` | 7     | 438       |
| Bicep           | 18    | 3 050     |
| JSON            | 180   | 25 203    |
| SQL             | 3     | 507       |
| KQL             | 2     | 296       |
| YAML (`.yml/.yaml`) | 8 | 2 131     |
| Markdown        | 59    | 7 570     |
| JS (repo, excluding bundle) | 2 hand‑written; 1 built `analytics-mfe.js` bundle (1.68 MB) | — |

Structure: `apps/portal-shell` (Blazor WASM, `.csproj`, `Program.cs`, `App.razor`,
`Pages/AnalyticsHost.razor`, `Components/{AnalyticsBridge, CapacityPanel}.razor`,
`Services/{ShellState, CapacityService, AuthDemoContext}.cs`),
`apps/analytics-mfe` (Vite/React, 20 screen components under
`src/components/screens/*.tsx`, 13 chart primitives, tests with Vitest),
`services/{bff-api,scoring-worker,optimizer-worker,knowledge-orchestrator,ingest-relay}`,
`simulator/` (deterministic event generator, 18 modules),
`contracts/{data,events,openapi,ui}`, `fabric/{items,lakehouse,notebooks,semantic-model,rti,pipelines,kql,powerbi}`,
`infra/{bicep,policy,scripts}`, `tests/{backend,contract,e2e,infra,integration,knowledge,simulator}`,
`docs/demo/demo-runbook.md`, `artifacts/{validation,demo-validation}` with real rehearsal evidence.

---

## Capability coverage matrix

Legend: **Real** = production‑shape algorithm with tests; **Product** = shipping‑shape
end‑to‑end (UI + API + tests) even if algorithm is calibrated‑simple; **Stub/Doc** = only
docs or placeholder logic.

| Capability | Project A — evidence | Project B — evidence | Verdict A | Verdict B |
|---|---|---|---|---|
| **1. Predictive maintenance — furnace lining RUL 21d** | `workloads/p1_predictive_maintenance/physics_features.py` (139 LOC): least‑squares linear fit on HeatFlux/ThermocoupleTemp/Vibration windows, wear‑rate slope, acceleration, normalized health index. `rul_model.py` (155 LOC): extrapolates time‑to‑threshold `(threshold − heat_flux)/slope`, escalates when TTF<21d, produces `Prediction` contract with weighted `EvidenceItem`s and derived `confidence`. `decision_service.py` orchestrates. 4 golden/independent pytest cases. | `services/scoring-worker/src/scoring_worker/service.py` (172 LOC): RUL = `(hearth_refractory_estimate − 300) / degradation_rate` (rate hard‑coded 3.0 for sector 07, 0.02 otherwise). p10/p90 computed as fixed multipliers of p50 (×0.8, ×1.3095). Driver contributions are literal constants `[0.29, 0.24, 0.18]`. Water‑heat proxy and apparent thermal resistance are computed but not fed into the RUL. Consumed by BFF `/v1/furnaces/{id}/lining-forecast`, wired into `FurnaceLiningForecast.tsx` screen and `WO-DEMO-LUX-1042` work‑order flow. | **Real (physics‑informed)** | **Product (over‑simplified physics)** |
| **2. Energy dispatch — −14 % energy / −22 % CO₂** | `workloads/p2_energy_dispatch/dispatch_model.py` (196 LOC): baseline "each heat is a campaign" vs. optimized "batch each furnace's campaign into greenest contiguous window", including warm‑up energy modelling; per‑slot cost/CO₂ evaluator; `energy_savings_pct/co2_savings_pct/cost_savings_pct` derived from real deltas. `milp.py` (136 LOC): real PuLP + CBC MILP with binary start‑slot variables, single‑heat‑per‑furnace overlap constraint, weighted cost+CO₂ objective, lazy import so heuristic path never needs a solver. Golden fixture + MILP‑equivalence test. | `services/optimizer-worker/src/optimizer_worker/service.py` (318 LOC): bounded‑enumeration greedy — for each batch, pick the cheapest slot within `maxShiftMinutes` and per‑slot `maxConcurrent` capacity. Constraint report enforced (`equal_planned_tonnage`, `urgent_batch_fixed`, `minimum_soak_time`, `maximum_hold_time`, `equipment_capacity`). **However** `co2Pct = clamp(savings_pct × 0.84, 0, 15)` and `modeled_peak_reduction = clamp(raw_peak × 0.23, 0.03, 0.07)` — the "22 % / peak" story is a *calibrated projection from the cost saving*, not an independent physical model. Raw carbon arbitrage is also exposed for honesty. Consumed by BFF `/v1/energy/schedules:simulate`, `EnergySimulator.tsx`, `EnergySpotSchedule.tsx`. | **Real (MILP + heuristic)** | **Product (deterministic greedy + calibrated CO₂/peak)** |
| **3. Quality — +8 % high‑grade yield** | `workloads/p3_quality/quality_model.py` (181 LOC): rule‑based per‑heat predictor over sulfur/inclusion/tapping‑temp with recoverability logic and human‑review `Recommendation`; explicit yield calculation `recommended_yield − baseline_yield`. `spc.py` implements control limits + Western Electric drift rule; `spc_drift_prediction` raises typed `Prediction`. Golden fixture, from‑gold, and independent tests. | `scoring-worker.score_quality` + `quality_what_if`: `base_yield = 0.95` reduced by |bias|, `proposed_yield = current + |dTemp|×0.00875 + |dForce|×0.002`, capped at 0.95. Server‑side clamps at ±20 °C/±10 %. Consumed by `/v1/quality/batches`, `/v1/quality/what-if`, `QualityBatches.tsx`, `QualitySpc.tsx`, `QualityBatchDrawer.tsx` — three dashboards, genealogy JSON fixture, "predicted vs measured" labels. | **Real (rules + SPC)** | **Product (linear what‑if + full UI)** |
| **4. Knowledge capture — operator interviews + searchable procedure library** | `workloads/p4_knowledge_capture/assistant.py` (91 LOC): retrieve → ground → cite → decline‑on‑insufficient → Content Safety gate → `Recommendation` (`Proposed`, human‑in‑the‑loop). `retrieval.py` (47 LOC): lexical token‑overlap default + optional cosine over embeddings. `capture.py` (49 LOC): PII redaction (email/phone/name) + erasable `RawCapture` linked to GDPR pipeline (`platform/governance/gdpr.py`). Seeded library with 3 SOPs. 7 pytest cases + 4 Content Safety cases. | `services/knowledge-orchestrator` (~1200 LOC): consent lifecycle (grant/deny/withdraw with deletion directive), audio validation, Speech Fast Transcription adapter (local + Azure), Foundry knowledge agent adapter (local + Azure), grounding enforcement against transcript segment IDs, prompt‑injection defenses, `draft → in_review → approved/rejected` procedure workflow with expected‑version optimistic locking, RBAC (`Knowledge.Publisher`), idempotency, append‑only audit log with per‑record hash. BFF `/v1/knowledge/*` (5 routes) + `KnowledgeHub.tsx` UI. 10 dedicated pytest files. Fixtures for injection attacks, safe prompts, interview transcripts. | **Real (grounded RAG + PII)** | **Real (full workflow + prompt‑defense + consent)** |

Neither project *actuates* equipment; both are decision‑support with human‑in‑the‑loop
gates. Neither depends on real plant data — both use synthetic, labelled data.

---

## Demo readiness (what can be shown live in 15 min)

### Project A

- **No runnable web UI or HTTP API** in the repo. Grep for `FastAPI|Flask|@app.route|uvicorn|Blueprint` across `workloads/`, `platform/`, `libs/` returned **zero** hits.
- Only browser‑visible surface is `apps/steel_factory_simulator` — an ASP.NET Core Razor
  Pages app with 3 pages (`Index`, `Personas`, `Settings`) for the *synthetic device
  simulator*. It is not a customer/executive dashboard.
- `docs/usecase/First_Proposal/08-demo-script.md` (86 lines) narrates a *hypothetical*
  jury walk‑through of a "furnace health dashboard", "energy‑dispatch view", "knowledge
  assistant in Teams/Copilot", "Purview audit view" — **none of these dashboards exist as
  code in the repo**. The referenced setup checklist item is "dashboards loaded", not
  "run this command to start the demo".
- Live scripts that do exist: `workloads/p1_predictive_maintenance/run_p1_live.py`,
  `workloads/p4_knowledge_capture/live_smoke.py`, and `platform/scripts/*_live.py` —
  these are Fabric/Azure smoke scripts, not local demos. There is no local URL to click.
- Demo path an executive can see today: read the markdown script, look at unit‑test
  output, and open the physics‑lite plots you'd have to generate yourself.

### Project B

- **Runnable local stack** documented at `docs/demo/demo-runbook.md` (17.7 KB, 15‑minute
  minute‑by‑minute script tied to six DM moments) and driven by `package.json` scripts:
  - `npm run build` → builds React MFE + Blazor.
  - `npm run run:bff` → starts FastAPI BFF on `http://127.0.0.1:8080` (with
    `DEMO_MODE=local`, deterministic fixtures under `services/bff-api/fixtures/demo-full/`).
  - Blazor WASM `apps/portal-shell` hosts the React MFE via `AnalyticsBridge.razor`;
    `Program.cs` supports MSAL if `AzureAd:ClientId` is set, otherwise anonymous.
- **20 dashboards** already implemented as React screens:
  `CommandCenter`, `EnergySimulator`, `EnergySpotSchedule`, `ExecutiveOverview`,
  `ExecutivePowerBi`, `FurnaceLiningForecast`, `FurnaceMaintenance`, `FurnaceThermal`,
  `KnowledgeHub`, `Operations`, `PlatformCapacity`, `PlatformCost`, `PlatformJobs`,
  `QualityBatchDrawer`, `QualityBatches`, `QualitySpc`, `SustainabilityAudit`,
  `SustainabilityEmissions`, `SustainabilityEts`.
- **`artifacts/demo-validation/drive_demo.py` (23 KB)** — a scripted walk‑through that
  hits the running BFF over real HTTP with per‑persona demo headers, saves the JSON
  response of every moment, and cross‑checks the run‑book cue sheet (P50 21d,
  8‑13 % cost reduction, batch `COIL-LUX-260725-017`, etc.).
- **Recorded rehearsal already in‑repo**: `artifacts/demo-validation/http/_summary.json`
  shows a full pass across 11 moments in **0.309 s** of BFF server time, and
  `rehearsal-report.md` (15.8 KB) records the observed vs. expected values. Screenshots
  markdown, portal build log, and BFF logs are all committed.
- **Deterministic offline fixtures** under `services/bff-api/fixtures/demo-full/`
  (10 NDJSON streams + `manifest.json` + `checksums.json`) — the demo works with
  network disabled.
- 15‑minute executive walk‑through is *literally the intended flow* — the runbook
  script is aligned to the six DM moments (§5.2) and there is a fallback ladder.

**Verdict**: A cannot be shown live to an executive in 15 minutes without building
something new; B can (and its rehearsal artifacts prove it already has been).

---

## Test & CI evidence

### Test counts (files / cases, excluding third‑party venvs)

| | Project A | Project B |
|---|---|---|
| pytest files | 20 | 34 |
| `def test_*` functions | **79** | **187** (206 collected including class methods) |
| xUnit .cs test files | 8 | 0 |
| `[Fact]/[Theory]` methods | **23** | 0 |
| Vitest `.test.ts(x)` files | 0 | 6 |
| `it(...)/test(...)` cases | 0 | **29** |
| **Total** | **~102** | **~235** |

### What I actually ran

- **Project A** — `.\.venv\Scripts\python.exe -m pytest -q` executed from repo root.
  Result: **81 passed, 1 skipped in 1.45 s** (collect count 82). Suites covered:
  novasteel_core (audit/parity), platform/{medallion,kpi,governance}, workloads/{p1..p4},
  content_safety.
- **Project B** — `.\services\bff-api\.venv\Scripts\python.exe -m pytest tests -q`.
  Result: **206 passed, 1 warning in 284.44 s (4:44)** (one Starlette deprecation
  warning about httpx). Suites covered: `backend`, `contract`, `e2e`, `infra`
  (Bicep build/params/naming/policy), `integration`, `knowledge` (10 files),
  `simulator` (9 files, includes physics validators and determinism).
- The .NET test projects (A only) and the Vitest suite (B only) were not executed —
  no `dotnet` build cache present and the Vitest run wasn't necessary once the Python
  suite passed and file counts were confirmed.

### Test‑type mix

- A: unit (rul, dispatch, milp, quality, spc, assistant, capture, medallion,
  governance, kpi) + golden fixture (p2/p3) + contract/serialization tests in
  `NovaSteel.Contracts.Tests`. No end‑to‑end HTTP/UI tests because there is no
  HTTP surface to hit.
- B: unit (workers, orchestrator internals, format/tableProcessing, primitives),
  **contract** (`tests/contract/test_bff_contract.py` – validates BFF vs.
  `contracts/openapi/bff-api-v1.yaml`), **integration** (simulator→services,
  local demo API stack), **e2e** persona journeys (`test_local_demo_persona_journeys.py`
  drives the FastAPI TestClient across `/v1/me → /v1/furnaces/.../lining-forecast →
  POST /v1/workorders` with idempotency), **infra** (Bicep build/params/policy),
  **knowledge** (adapters, audio, audit, consent, evaluation, grounding, orchestrator,
  procedure_workflow, prompt_defense, tools).

### CI / CD gates

**Project A** — `.github/workflows/ci.yml` (54 lines). Three jobs:
1. `python-tests`: `pip install -e libs/novasteel_core pytest` + `python3 -m pytest -q`.
2. `dotnet-tests`: `dotnet test NovaSteel.slnx --configuration Release`.
3. `bicep-validate`: `az bicep build` for main + monitoring‑alerts modules.
No caching, no coverage, no path filters, no linting, no CodeQL.

**Project B** — 9 workflow files, `ci.yml` alone is 18 KB. Structure:
1. `changes` — path‑filter detection (contracts/simulator/backend/knowledge/frontend/portal/infra/fabric/presentation).
2. `verify-protected-feeds` — `tools/validation/verify_protected_feeds.py` uploads evidence.
3. `security-gates` — `security_scan.py` + `generate_sbom.py` (CycloneDX).
4. `contract-schema` — venv restore from protected pip feed + `Validate-Repository.ps1 -Suite contract`.
5. `simulator` — determinism & physics validators via same runner.
6. `backend-contract-integration` — unit/contract/integration/local‑e2e journeys.
7. `knowledge-workflow` — consent, prompt‑defense, publication workflow.
8. `frontend` — Node 22, `npm ci --ignore-scripts`, lint/test/build, `npm audit --omit=dev --audit-level=high`, evidence uploaded.
9. `portal` — Blazor restore/build + `dotnet package list --vulnerable`.
10. `infrastructure` — `az bicep install`, `Validate-Repository.ps1 -Suite infra`.
11. `fabric` — local Fabric item validator.
12. `presentation` — PPTX package validator.
Plus separate `cd-infra.yml`, `cd-services.yml`, `cd-fabric-items.yml`, `codeql.yml`,
`scheduled-batch.yml`, `simulator.yml`, `deploy-website.yml`, and Dependabot config.
Every job pins actions by SHA, disables persist‑credentials, and uploads evidence
artifacts with 90‑day retention.

---

## Reliability & performance evidence

### Project A

- No HTTP service ⇒ no retries / timeouts / circuit breakers / health probes in code.
- Reliability posture is *scientific*: deterministic fixtures, contract‑shape parity
  between Python and C# (`novasteel_core/tests/test_parity.py`, `libs/NovaSteel.Contracts.Tests/GoldenFixtureTests.cs`), and content‑safety gates in every explainer path (P2/P3/P4).
- KPI baseline is frozen and per‑site isolated (`platform/kpi/tests/test_kpi_baseline.py`).
- Steel‑factory simulator is an ASP.NET Core Worker/host with an IoT Hub transport but
  no explicit retry/backoff in code — grep on the repo returns zero hits for
  `retry|circuit|backoff|breaker|throttle` in code files.
- Perf: pytest suite runs in **1.45 s**, giving a very fast inner dev loop.

### Project B

- `services/bff-api/src/bff_api/main.py`: correlation‑ID middleware
  (X‑Correlation‑ID both directions, generates UUID if missing), global exception
  handlers mapping to `ErrorEnvelope { code, message, correlationId, retryable }`,
  `retryable=True` set on unexpected 500s and upstream failures, dedicated
  `/health/live`, `/health/ready`, `/v1/meta` endpoints, CORS locked to
  configured origins with limited methods/headers.
- `services/bff-api/src/bff_api/services.py`: in‑process forecast cache keyed by
  asset (`cached = self.forecasts.get(asset_id)`), rehydrating persisted audit refs.
- `services/bff-api/src/bff_api/capacity.py`: models ARM long‑running operations,
  respects `Retry-After` (line 63), safely returns cached capacity state during
  transient outages, and models a `ReadinessCheck` phase; `CapacityUpstreamError`
  is surfaced as HTTP 503 with `retryable=True` (routes.py:898).
- `services/bff-api/src/bff_api/idempotency.py`: idempotency store used by
  `POST /v1/workorders`, `POST /v1/knowledge/procedures/{id}:approve`,
  `POST /v1/energy/recommendations/{id}:{approve|reject}`, and
  capacity start/pause requests — verified by e2e test `test_maintenance_persona_can_turn_a_lining_warning_into_synthetic_work`.
- `services/bff-api/src/bff_api/audit.py`: append‑only decision log with hash chain
  reachable via `GET /v1/audit/decisions`.
- `services/bff-api/src/bff_api/auth.py` (9.4 KB): role hierarchy (`READER_ROLES`,
  `require_any_role`, `require_reader`, `require_site`) enforced server‑side.
- `simulator/sink_http.py` has explicit **retry on transient failures** and
  **idempotent replay** (tests: `test_publish_retries_transient_failures`,
  `test_publish_can_replay_duplicates_for_idempotency_testing`).
- Perf: measured demo rehearsal shows **0.309 s total server time across 11
  moments** — the whole 15‑minute walk‑through spends its budget on narrative
  and screen changes, not on waiting for the BFF. Full pytest 4:44 (dominated by
  Bicep build + integration harness).
- Observability: correlation IDs echoed in every response, CI publishes
  evidence artifacts (`artifacts/validation/*/manifest.json`).

---

## Placeholder / TODO / stub findings

| Signal | Project A | Project B |
|---|---:|---:|
| `TODO` occurrences (all extensions) | 8 | 17 |
| `FIXME` | 0 | 0 |
| `NotImplemented` | 0 | 3 |
| `placeholder` | 18 | 33 |
| `XXX` | 6 | 0 |
| `HACK` | 0 | 1 |

Qualitative check on `.py/.cs/.ts/.tsx/.razor` (excluding docs and .venv):

- **Project A** — no `TODO/FIXME/NotImplemented` in production code. The word
  "TODO" only appears inside `.github/agents/*.md` (SpecKit agent prompts describing
  how to *scan* for TODOs) and inside `docs/usecase/1_agentic_work/plans/00-foundation-plan.md`
  which literally certifies "Placeholder scan: no TBD/TODO; every code step has real code."
- **Project B** — `TODO/NotImplemented` are constrained to interface stubs
  (`services/knowledge-orchestrator/src/knowledge_orchestrator/adapters/base.py:24,45`,
  `adapters/azure_foundry.py:66`) and to `tools/validation/validate_pptx.py:19`.
  Production business logic (workers, orchestrator, BFF routes) is free of TODOs. The
  `NotImplemented` markers are `raise NotImplementedError` in `abstract` adapter
  base classes, which is idiomatic.

### Honest calls on "real vs. calibrated"

- **B: energy CO₂ and peak reduction** — `optimizer-worker/service.py` computes
  `co2_pct = clamp(savings_pct × 0.84, 0, 15)` (line 143) and
  `modeled_peak_reduction = clamp(raw × 0.23, 0.03, 0.07)` (lines 131–137). The
  code even comments the honesty: *"The constrained model exposes the
  dispatch‑attributable part of the observed peak change. It is capped to the
  validated demo band."* Jury‑safe if disclosed; misleading if presented as raw
  physics. The 22 % CO₂ headline is **not** a MILP result on grid‑carbon curves.
- **B: RUL** — physics reduced to `(thickness − 300 mm) / rate` with `rate = 3.0`
  for sector 07 and `0.02` elsewhere. Uncertainty band is `p10 = p50×0.8`,
  `p90 = p50×1.31` — deterministic advisory, not a probabilistic model.
- **A: quality** — pure rule engine (thresholds), not a learned model.
  Documentation is honest about this (`quality-rules-v1`).
- **A: energy dispatch** — a *real* MILP is available (PuLP/CBC) alongside the
  heuristic; `test_p2_milp.py` proves feasibility and equivalence. The 14 % / 22 %
  headline numbers come from *computed* baseline‑vs‑optimized deltas on the
  synthetic scenario, not from calibration constants.

---

## Proposed scores (1‑5)

### 1. Application Demo

| | Score | Justification |
|---|:---:|---|
| **Project A** | **2** | No runnable web UI or HTTP API in the repo. Demo script is aspirational narrative for dashboards that don't exist as code (`docs/usecase/First_Proposal/08-demo-script.md` mentions "furnace health dashboard", "energy‑dispatch view", "knowledge assistant in Teams/Copilot" — none present). The only browsable UI is a 3‑page Razor Pages simulator whose purpose is to *generate synthetic device telemetry*, not to walk an executive through the four capabilities. Nothing to click for the jury without additional build work. |
| **Project B** | **5** | Executive‑ready: Blazor WASM shell + 20 React dashboard screens + FastAPI BFF with 32 domain endpoints, all runnable locally via `npm run run:bff` and `dotnet build apps/portal-shell/PortalShell.csproj`. In‑repo `docs/demo/demo-runbook.md` prescribes the 15‑minute walk‑through minute‑by‑minute with cue values and a fallback ladder. `artifacts/demo-validation/drive_demo.py` scripts the walk‑through against a real HTTP surface, and a **captured rehearsal (`_summary.json`, `rehearsal-report.md`) proves 11 demo moments completed in 0.309 s of server time**. Deterministic fixtures under `services/bff-api/fixtures/demo-full/` mean it works offline. |

### 2. Implementation completeness

| | Score | Justification |
|---|:---:|---|
| **Project A** | **4** | All four capabilities have real Python implementations wired to typed contracts (`novasteel_core.models`). Physics‑informed linear RUL with wear‑rate/health‑index; MILP + heuristic dispatch with baseline/optimized/savings; SPC + rule‑based quality with yield uplift; grounded RAG assistant with citation enforcement, decline‑on‑insufficient, PII redaction, Content Safety. Cross‑language contract parity (Python ↔ .NET). Governance modules (`eu_ets.py`, `gdpr.py`) with tests. Loses the fifth point because there is no runnable service/UI, no HTTP API, no end‑to‑end runnable pipeline outside pytest — the "product" is really a library. |
| **Project B** | **4** | All four capabilities implemented end‑to‑end (worker + BFF + UI). Full knowledge‑capture workflow (consent, STT adapter, Foundry adapter, grounding, prompt‑defense, draft→review→approve, audit hash chain). Contracts are formalized (`contracts/openapi/bff-api-v1.yaml`, event JSON schemas, UI design tokens). Fabric assets present (`fabric/{items,lakehouse,semantic-model,rti,notebooks}`). Infrastructure as Bicep with policy. Loses a point because the quantitative claims (14 %/22 %/21 d/8 %) depend on calibrated constants rather than physics — the algorithms are shallower than A's. If you asked the code to prove the 22 % CO₂ headline from first principles, B could not; A could. |

### Bonus — Performance & reliability

Both projects address reliability, differently:
- A: deterministic algorithms, golden fixtures, cross‑language parity, human‑in‑the‑loop
  gates on every recommendation; **no service** ⇒ no timeouts, retries, or health probes.
- B: correlation IDs, idempotency, retryable error envelopes, health/live + health/ready,
  ARM `Retry-After` handling, forecast cache, append‑only audit with hash chain,
  simulator sink with retries and idempotent replay, CodeQL, SBOM, `npm audit`,
  `dotnet package list --vulnerable`.

For the *"Performance and reliability clearly addressed"* rubric bullet:
- **A ≈ 3** — algorithmic reliability and fast tests; missing runtime concerns.
- **B ≈ 4** — full service reliability toolbox in code; performance quantified in
  rehearsal artifacts.

---

## Top 5 fixes for Project A

1. **Ship a runnable demo UI.** Wrap the existing workloads in a tiny FastAPI + a
   minimal Streamlit or Blazor page that exposes: (a) fleet health, (b) a "raise 21‑day
   alert" button that runs `score_rul` on a fixture, (c) baseline‑vs‑optimized dispatch
   chart from `dispatch_model.build_energy_plan`, (d) an assistant chat box calling
   `KnowledgeAssistant.ask`. Without this, the jury cannot see the science.
2. **Publish an HTTP surface with contract tests.** Convert `Prediction`,
   `Recommendation`, `EnergyPlan` into an OpenAPI spec and add a service layer.
   The contract shapes already exist in `libs/NovaSteel.Contracts` — expose them.
3. **Add a 15‑minute demo runbook** that maps commands to jury moments (which
   `python -m` command, which fixture, which expected number). The current
   `08-demo-script.md` is a *narrative* — replace it with a runnable script that
   captures response evidence like B's `drive_demo.py`.
4. **Expand CI** to include coverage, ruff/mypy, and (if a service is added)
   contract tests. Current CI runs three basic jobs; add path filters and
   evidence artifacts.
5. **Consolidate the two orphan trees** (`website/` has only a README;
   `platform/scripts/*_live.py` require a live Fabric workspace). Either delete
   `website/` or populate it, and provide dry‑run flags for the live scripts so
   they can be exercised in CI.

## Top 5 fixes for Project B

1. **Ground the headline numbers in real physics.** Replace the
   `co2Pct = savings_pct × 0.84` and `peak_reduction ∈ [3 %, 7 %]` clamps with
   an actual CO₂ objective computed from `carbon_intensity_kgco2e_per_mwh` on
   shifted MWh; keep the current values as a fallback but expose the real
   number too (the `rawCarbonArbitragePct` field already hints at this).
2. **Upgrade the RUL model** to at least match A's physics‑informed linear
   regression on the last N days of heat‑flux slope with an uncertainty band
   derived from the fit residuals. The current
   `(thickness − 300) / degradation_rate` with hard‑coded rates by sector is
   the biggest jury‑risk in the codebase.
3. **Delete the vendored `node_modules`** from the repository (large & noisy).
   Rely on `npm ci` from `package-lock.json`. Same for the committed
   `apps/portal-shell/wwwroot/analytics-mfe/analytics-mfe.js` bundle (1.68 MB).
4. **Address the abstract‑adapter `NotImplementedError` stubs** in
   `services/knowledge-orchestrator/src/knowledge_orchestrator/adapters/base.py`
   and `adapters/azure_foundry.py` — either wire the Azure adapters end‑to‑end
   or clearly gate them behind capability flags with tests that assert the
   local adapter is used in demo mode.
5. **Trim pytest wall‑time** (4:44 dominated by `az bicep install` and
   integration harness). Split infra tests into a separate CI stage and mark
   them `slow` so the dev inner loop can run backend + knowledge + frontend
   in <60 s. This will also cut CI cost.

---

## Appendix — commands executed

```powershell
# Project A — collect + run
cd "D:\work\20260507 - NovaSteel\NovaSteel"
.\.venv\Scripts\python.exe -m pytest --collect-only -q   # 82 items
.\.venv\Scripts\python.exe -m pytest -q --tb=line        # 81 passed, 1 skipped, 1.45s

# Project B — collect + run
cd "D:\work\20260724 - Novasteel 3"
.\services\bff-api\.venv\Scripts\python.exe -m pytest tests --collect-only -q   # 206 items
.\services\bff-api\.venv\Scripts\python.exe -m pytest tests -q --tb=line        # 206 passed, 1 warning, 4:44

# Inventory
Get-ChildItem -Recurse -File -Filter '*.py' | Where-Object { $_.FullName -notmatch '\.venv|\\v\\|\\build\\|node_modules|__pycache__' }
# ...repeated per extension with LOC accumulation
```
