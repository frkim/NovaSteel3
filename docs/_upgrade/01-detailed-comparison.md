# NovaSteel — Detailed Dimension-by-Dimension Comparison

> Companion to `00-executive-summary-and-scoring.md`. Every finding below was verified against
> source files by a specialist agent; full evidence with line numbers is in `evidence\`.

**Legend:** 🟢 clear win · 🟡 partial/qualified · 🔴 failing · **A** = `20260507 - NovaSteel\NovaSteel` · **B** = `20260724 - Novasteel 3`

---

## 1. System architecture, modularity, scalability — A 3 · **B 5**

| Dimension | A | B |
|---|---|---|
| Resource groups | 🔴 1 flat RG | 🟢 6 (hub / integration / apps / ai / fabric / monitoring), per-context Key Vaults |
| Environments | 🟡 1 (dev) | 🟢 4, parameterised |
| Service layer | 🔴 None — `workloads\p1..p4` are importable Python modules only | 🟢 FastAPI BFF (42 KB of routes, 32 endpoints, SSE) + 4 workers + ingest relay + knowledge orchestrator |
| Front end | 🔴 3-page Razor simulator | 🟢 Blazor WASM shell + React/TS microfrontend (20 screens) |
| 4-country requirement | 🔴 Not expressed in IaC at all | 🟢 `plants[]` parameterised → per-plant Event Hub + per-plant managed identity |
| Decision records | 🔴 None | 🟢 10 formal ADRs |
| Architecture docs | 🟡 Good narrative, weaker as build spec | 🟢 56 KB `solution-architecture.md` + 28 KB `deployment-topology.md`, authoritative |
| Scalability | 🟡 Fabric medallion notebooks are real; nothing else scales | 🟢 Stateless BFF, async workers, capacity state machine, Event Hub partitioning |
| Integrity gap | 🔴 `platform\agents\` is an **empty folder** despite docs promising it | 🟡 `zoneRedundant: false` everywhere; audit/idempotency in-memory |

**Why the gap.** A designed an architecture and documented it beautifully; B *built* one. B's
Bicep is 3,050 lines against A's 1,734, and B's is doing structurally harder work
(hub-and-spoke, per-plant fan-out, policy). A's `main.bicep` opens with a comment admitting it
is a demo configuration.

---

## 2. Use of design patterns — A 3 · **B 5**

**Patterns verified in A's code:** Medallion architecture (Fabric notebooks) · Strategy
(heuristic ↔ MILP swap in energy dispatch) · Dependency Injection (.NET simulator) · shared
DTO/contract parity · quarantine pattern for bad data.

**Patterns verified in B's code:** all of A's, **plus** Ports & Adapters / hexagonal
(`services\knowledge-orchestrator\...\adapters\base.py` — local fixture and Azure adapters swap
cleanly) · Backend-for-Frontend · microfrontend composition · composition root · **9-state
capacity state machine** · idempotency keys · correlation envelope · policy-as-code ·
DRAFT→IN_REVIEW→APPROVED workflow state machine with optimistic concurrency · 10 ADRs
documenting the decisions.

> **Jury framing:** B can name a pattern, point at the file, and explain the trade-off. That is
> exactly what "appropriate and effective use of relevant design patterns" means in the grid.

---

## 3. Security — A 2 · **B 5** 🔴 *A's weakest and most dangerous area*

### The critical finding in A

```
apps\steel_factory_simulator\src\SteelFactorySimulator\Program.cs:83-94
  → POST /api/fabric/pause   (no auth middleware)
  → POST /api/fabric/resume  (no auth middleware)

infrastructure\...\container-app-simulator.bicep:62-67   → public ingress, external
infrastructure\...\container-app-simulator.bicep:153-161 → built-in **Contributor**
                                                            on the Fabric capacity
```

**Anyone who discovers the FQDN can pause or resume the Fabric capacity.** That is a live
cost-DoS and an availability/integrity incident on the production analytics core. B's
equivalent is a **custom `Fabric Capacity Operator` role** limited to
`read/write/suspend/resume/action` (`infra\bicep\modules\roles.bicep:18-40`).

### Control-by-control

| Control | A | B |
|---|---|---|
| Private endpoints | 🔴 **Zero.** `main.bicep:3`: *"Demo configuration: public network access, no private endpoints"* | 🟢 On every stateful + AI service, with 6 private DNS zones |
| VNet / NSG | 🔴 No network module exists | 🟢 Hub-and-spoke + NSGs |
| `publicNetworkAccess` | 🔴 `'Enabled'` on Key Vault (`keyvault.bicep:31`), Foundry (`foundry.bicep:53`), Storage, Event Hubs | 🟢 `Disabled` on all of the above |
| Policy enforcement | 🔴 None | 🟢 Subscription-scope **deny-public-network-access** Azure Policy |
| Managed identities | 🔴 1 shared ("god identity") | 🟢 7 per-service + 1 per plant |
| Local auth / keys | 🔴 `disableLocalAuth: false` on the AI account holding **operator PII** | 🟢 `disableLocalAuth: true` on Event Hubs + Cognitive Services |
| CI identity | 🟡 — | 🟢 GitHub OIDC federated in Bicep, subject pinned `repo:*:environment:*`, `AZURE_CREDENTIALS` grep-blocked |
| Supply chain | 🔴 No CodeQL, no Dependabot, no SBOM; Python job installs from **public PyPI** despite the repo's own protected-feed policy | 🟢 CodeQL (Py/JS/TS/C#), Dependabot on `packagefeedproxy.microsoft.io`, CycloneDX SBOM, `npm audit`, `dotnet --vulnerable`, all actions pinned to 40-char SHAs, `@sha256:` digest enforcement |
| Audit integrity | 🟡 Immutable but **not hash-chained**, no redaction | 🟢 **SHA-256 hash-chained** append-only with `_redact()` + `verify()` |
| Threat model | 🔴 None | 🟢 STRIDE + abuse cases + 11 release-blocking gates (73 KB) |
| EU AI Act | 🔴 **All workloads "minimal-risk"** — indefensible for an €8M furnace | 🟢 "High-risk-adjacent pending Legal", Art. 9/10/12/14/15 designed in |
| GDPR erasure | 🟢 Implemented in code (`platform\governance\gdpr.py`) | 🟡 Documented, plus 72-h breach workflow |
| OT safety boundary | 🟡 Discussed | 🟢 Enforced and stated: never PLC / interlock / setpoint / schedule-commit / CMMS write |

**Score: 21 control wins for B, 5 ties, 0 wins for A.**

---

## 4. Application Demo — A 2 · **B 5**

| | A | B |
|---|---|---|
| Clickable product | 🔴 None | 🟢 `http://localhost:5266/lu/command-center` + 7 more persona routes |
| API | 🔴 None | 🟢 32 endpoints, `/health/ready` verified |
| Scripted demo | 🟡 Narrative markdown | 🟢 `drive_demo.py` — 6 demo moments + telemetry, authz, audit, capacity lifecycle |
| Rehearsal evidence | 🔴 None | 🟢 66/66 live BFF checks; 11 moments at 0.31 s server time; seed `240725`, bit-for-bit reproducible |
| Fallback plan | 🔴 None | 🟢 5-level ladder: live cloud → local replay → cached → recording → static pack; *"never diagnose > 10 s on-screen"* |
| Determinism | 🔴 — | 🟢 Committed `demo-full` fixture; no cloud account needed |
| Executive hook | 🟡 Strong story, nothing to see | 🟢 Persona-driven command center |

B can be demonstrated in three commands. A cannot be demonstrated at all beyond a slide deck
and a simulator that draws synthetic gauges. **On a rubric line that says "clean and clear
demonstration of the use case", this is the single most expensive gap in A.**

---

## 5. Implementation completeness — A 4 · **B 4** *(tie, for opposite reasons)*

| Capability | A | B |
|---|---|---|
| **P1 Furnace lining RUL** | 🟢 **Real**: heat-flux slope least-squares → TTF extrapolation + MLflow GradientBoosting uplift | 🔴 **Shallow**: `p50 = (thickness − 300) / sectorRate`, hard-coded rates; Fabric notebook hard-codes `demo_warning` = 0.87 / 21 d for `LUX-BF-01` |
| **P2 Energy dispatch** | 🟢 **Real**: PuLP/CBC **MILP** — binary start-slot vars, per-furnace no-overlap constraints, weighted CO₂+cost objective; plus a greedy "greenest window" fallback | 🔴 **Deterministic rules**: bounded enumeration ±`maxShift`, CO₂ capped at `min(15, savings × 0.84)`, peak clamped `[0.03, 0.07]` |
| **P3 Quality / yield** | 🟢 Rules + SPC + yield-uplift model | 🟡 Linear what-if (88 % → 95 %), but **3 dashboards + genealogy UI** |
| **P4 Knowledge capture** | 🟢 **Real**: grounded RAG (lexical + cosine), citation-enforcement regex + decline path, PII handling, live Content Safety | 🟡 **Full workflow, no AI**: consent, STT/Foundry adapters *scaffolded*, prompt-injection defence, DRAFT→REVIEW→APPROVED, hash-chained audit — but `extract_draft` raises `NotImplementedError` and a keyword classifier runs instead |
| Tests | 104 (81 pytest + 23 xUnit) | **235** (206 pytest + 29 vitest) |
| CI | 1 workflow / 3 jobs | **9 workflows**, path-filtered, SBOM, CodeQL, evidence upload |
| Placeholders | 🟢 0 TODOs in code (all in `.github\agents\*.md`) | 🟡 ~4, all in abstract adapter stubs; **plus the `k8se/quickstart` placeholder container image actually deployed** |

> **This is the crux of the whole analysis.** A built the *brains* without a body.
> B built the *body* without brains. B's body is far harder to build; A's brains are
> a few hundred lines that can be lifted wholesale.

---

## 6. Logging and metrics — A 2 · **B 3** 🟠 *Both weak — the cheapest points on the board*

| | A | B |
|---|---|---|
| Structured logging (Python) | 🔴 **Zero** `import logging` in `workloads\`, `libs\`, `platform\`; `print()` in 15 files | 🟡 Only **1 of 5 services** uses a logger; `bff-api` relies on default `basicConfig` so `extra={"correlation_id": …}` is **silently dropped** |
| Structured logging (.NET) | 🟡 Good `ILogger<T>` templates (14 sites) — but no sink, so parameters die at stdout | — |
| Correlation IDs | 🔴 **Zero** anywhere | 🟢 `X-Correlation-ID` middleware propagated into responses, audit, SSE, adapters (60+ sites) |
| Health endpoints | 🔴 None | 🟢 `/health/live` + `/health/ready` |
| App Insights | 🟡 Provisioned **and consumed** by Functions | 🔴 **Provisioned and never consumed** — `containerapps.bicep` never sets `APPLICATIONINSIGHTS_CONNECTION_STRING`; no OTel/AppInsights/Serilog package in any service |
| Alert rules | 🟢 **Real** `scheduledQueryRules` (data freshness, P1 model drift) + action group | 🔴 **Zero in IaC** — 10 alerts are prose in `docs\operations\operations-and-cost.md §4` |
| Audit chain | 🟡 Immutable, not hash-chained, no redaction | 🟢 SHA-256 hash-chained + redaction + `verify()` |
| Retention / SIEM | 🔴 — | 🟢 Sentinel onboarding, `dailyQuotaGb` cap, prod retention 365 d, diagnostics on 7 modules |
| Custom metrics / OpenTelemetry | 🔴 **None** | 🔴 **None** |

**Neither project emits a single custom application metric or uses OpenTelemetry.** For a
platform whose entire value proposition is *energy per ton, CO₂, RUL confidence and yield*,
not emitting those as metrics is the most glaring, and most cheaply fixed, omission in both.

---

## 7–8. AI Integration — A 7/10 · B 7/10

### Use of AI technologies — **A 4** · B 3

**A is the only project that calls a live LLM.** GPT-5 + `text-embedding-3-large` deployed on
`aif-novastee-dev-ox26fi`, authenticated via Entra, with a live smoke test; RAG combining
lexical and cosine retrieval; a citation-enforcement regex with a decline path; live Azure AI
Content Safety.

**B calls no model at all.** `AzureFoundryKnowledgeAgent.extract_draft` →
`NotImplementedError`. The runtime substitutes a keyword-bucket classifier. The Speech adapter
is scaffolded and unused. B compensates with genuinely strong *governance* around the
AI — spotlighting, a prompt-injection scanner, a tool allow-list, an evaluation harness — but
governance around an absent model cannot score above Satisfactory.

### AI model selection and deployment — A 3 · **B 4**

A deploys models but with a **development-grade posture on an account processing operator
PII**: `publicNetworkAccess: 'Enabled'`, `disableLocalAuth: false` (API keys accepted).
B deploys *no* model but the Foundry + Speech landing zone is production-grade:
`disableLocalAuth: true`, `publicNetworkAccess: 'Disabled'`, private endpoints, private DNS,
Log Analytics diagnostics, Sweden-Central-first residency policy.

> **The combined asset is obvious:** A's model deployments dropped into B's hardened landing
> zone scores 5 on both criteria.

---

## 9–10. Agentic Behavior — A 5/10 · B 6/10 🟠 *Weakest shared category*

**Neither project ships true multi-agent behaviour at runtime.** This is 10 of 60 points and
both are leaving roughly half of it on the table.

| | A | B |
|---|---|---|
| Runtime agent | 🔴 None — single-turn RAG chat | 🟡 2 declared agent identities (`knowledge-capture`, `energy-dispatch`) |
| Tool governance | 🔴 — | 🟢 Codified tool allow-list + `FORBIDDEN_TOOL_NAMES` |
| Agent SDK | 🔴 — | 🟡 `azure-ai-projects` scaffolded, not driving the runtime |
| State machine | 🔴 — | 🟢 DRAFT→IN_REVIEW→APPROVED with RBAC + optimistic concurrency |
| Human-in-the-loop | 🟡 Documented | 🟢 Implemented as approval gates |
| Handoffs | 🔴 None | 🔴 None |
| Reflection / critique loop | 🔴 None | 🔴 None |
| State-graph orchestration | 🔴 None | 🔴 None |
| **Dev-time agentic work** | 🟢 **Excellent** — a genuine 10-agent Copilot orchestrator + specialists pattern (`.github\agents\`, `docs\usecase\1_agentic_work\`) used to *build* the repo | 🟡 Present but lighter |

> ⚠️ **Do not conflate the two.** A's 10-agent Copilot pattern is impressive *engineering
> practice* and is worth 60 seconds of the defense — but the rubric line reads *"Agent
> demonstrates autonomous behavior and orchestrates tasks effectively"*, which the jury will
> read as the **delivered product**. Presenting dev-time agents as the answer to criterion 9
> is the fastest way to lose those points.

---

## 11. Performance and reliability — A 3 · **B 4**

| | A | B |
|---|---|---|
| Health / readiness probes | 🔴 None | 🟢 `/health/live`, `/health/ready` |
| Retry + backoff | 🔴 — | 🟢 Implemented |
| Idempotency | 🔴 — | 🟢 Idempotency keys (in-memory — see gap) |
| Caching | 🔴 — | 🟢 Present |
| Measured latency | 🔴 — | 🟢 11 demo moments at 0.31 s server time |
| Test wall-time | 🟢 1.45 s | 🟡 4 m 44 s (dominated by `az bicep install`) |
| Zone redundancy | 🔴 — | 🔴 `zoneRedundant: false` everywhere |
| DR / second region | 🔴 — | 🟡 ADR-003 claims West Europe contingency, not exercised in IaC |
| Load / perf testing | 🔴 None | 🔴 None |

---

## 12. Clarity of explanation and presentation — A 3.5 · **B 4.5**

| Asset | A | B |
|---|---|---|
| Slide deck | 🔴 **No `.pptx`** — a 949-word, 16-slide *outline* that self-labels **"30–40 minutes"** | 🟢 `NovaSteel-Oral-Defense.pptx`, 2.1 MB, **26 slides** (20 primary + 6 FAQ backups), 714 text runs, validated zero-placeholder |
| 60-minute plan | 🔴 None. `docs\usecase\10_oral_defense\` contains **only the rating grid** | 🟢 Explicit **30 + 15 + 15**, per-slide duration and running clock, 7 rehearsal checkpoints |
| Speaker notes | 🔴 — | 🟢 `oral-defense-and-slide-plan.md` |
| FAQ / objection handling | 🔴 — | 🟢 **50+ Q&A** in `docs\presentation\faq.md` |
| Demo script | 🟡 Narrative | 🟢 Minute-by-minute runbook + driver script |
| Fallback assets | 🔴 None committed | 🟢 5-level ladder |
| Business case (€) | 🟢 **€0.6–1.1 M build, €0.3–0.7 M/yr run, ~€24.5 M/yr benefit, sub-12-month payback**, with assumptions + sensitivity | 🔴 **Refuses to quote any €/hr** |
| Strategic depth | 🟢 16-chapter McKinsey analysis, 10-chapter bilingual FR/EN series, MkDocs website | 🟡 Focused, less breadth |
| Visual assets | 🟢 29 Mermaid + 11 hero images (real blast-furnace photos) + 1 Excalidraw | 🟡 11 Mermaid + 3 images + 3 Excalidraw |
| Honesty discipline | 🟡 — | 🟢 **TARGET 🎯 / EVIDENCE 🔬** on every quantitative claim |
| Hygiene issues | 🔴 Real tenant/subscription **GUIDs committed**; ~55 k words across 4 overlapping narrative folders | 🟡 Dense slides 8–10 |

---

## Consolidated risk register for the defense

| # | Risk | Where | Severity | Mitigation |
|---|---|---|:--:|---|
| R1 | Juror greps `optimizer_worker\service.py` and finds `savings × 0.84` and the `[0.03, 0.07]` clamp | B | 🔴 | **Replace with A's MILP** (M1) or pre-emptively label it a calibrated demo surrogate |
| R2 | Juror asks "show me the physics" and the RUL is `(thickness − 300) / rate` | B | 🔴 | **Port A's heat-flux regression** (M2) |
| R3 | Juror finds `demo_warning` hard-coded in the Fabric notebook | B | 🔴 | **Delete the hard-code** (M2) |
| R4 | "Which model are you calling?" → B calls none | B | 🔴 | **Wire the live Foundry call** (M3) |
| R5 | Juror finds A's unauthenticated public `/api/fabric/pause` with Contributor | A | 🔴 | Moot if B is submitted; **do not demo A's simulator** |
| R6 | "Show me your metrics" → App Insights provisioned, nothing emitting | B | 🟠 | **Wire OTel + custom KPI metrics** (M4) |
| R7 | "Show me your alerts" → prose only | B | 🟠 | **Add `scheduledQueryRules` to Bicep** (M5) |
| R8 | "Where's the multi-agent coordination?" → none at runtime | Both | 🟠 | **Add critic/reflection + handoff** (M6) |
| R9 | CFO on the panel asks for TCO/ROI → B has none | B | 🟠 | **Import A's cost model** (M7) |
| R10 | "What's actually deployed?" → placeholder `k8se/quickstart` image | B | 🟠 | **Ship real Dockerfiles** (M9) |
| R11 | "Show me your commit history" → B has no git repo | B | 🟠 | **`git init` + a structured history** (M8) |
| R12 | Luxembourg jury expects some French | B | 🟡 | **Add an FR executive summary** (M11) |
