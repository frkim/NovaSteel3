# NovaSteel — Project Comparison, Scoring & Final Recommendation

> **Deliverable:** deep comparative analysis of two competing implementations of the NovaSteel
> use case, scored against the official jury rating grid, with a final "which one do I keep and
> what do I change" verdict ahead of the **1-hour oral defense**.

| | |
|---|---|
| **Use case** | `D:\work\20260724 - Novasteel 3\docs\usecase\usecase.md` |
| **Rating grid** | `D:\work\20260507 - NovaSteel\NovaSteel\docs\usecase\10_oral_defense\rating_grid.md` |
| **Project A** | `D:\work\20260507 - NovaSteel\NovaSteel` — *"Project Ignition"* |
| **Project B** | `D:\work\20260724 - Novasteel 3` — *"final local demonstration handoff"* |
| **Method** | 6 parallel specialist agents (architecture, security, delivery, observability, AI/agentic, presentation) + independent code metrics; every claim verified against source, not READMEs |
| **Analysis date** | 2026-07-25 |

---

## 🏁 Verdict in one line

> **Keep Project B (`Novasteel 3`) as the submission, and transplant Project A's three
> genuine algorithmic assets — the PuLP MILP energy optimizer, the physics-informed RUL
> regression, and the live GPT-5 RAG call — into it.**
>
> B scores **48.5 / 60 (Grade B)** today versus A's **34.5 / 60 (Grade D/F)**.
> The transplant plus observability wiring takes B to a realistic **56–58 / 60 (Grade A)**.

---

## 📊 Official scoring table (jury rating grid, 60 points)

Scores are 1–5 per the grid: **5 = Excellent · 4 = Good · 3 = Satisfactory · 1–2 = Needs Improvement**.

| # | Category | Criterion | **A** | **B** | Δ | Deciding evidence |
|---|----------|-----------|:-----:|:-----:|:--:|-------------------|
| 1 | Design | System architecture, modularity, scalability | **3** | **5** | **+2 B** | A = 1 flat resource group, no service/API layer, `platform\agents\` empty. B = 6-RG hub-and-spoke, per-plant Event Hub + identity for all 4 countries, real BFF + 4 workers, 4 environments, 10 ADRs |
| 2 | Design | Use of design patterns | **3** | **5** | **+2 B** | A = Medallion, Strategy, DI. B = Ports & Adapters, BFF, microfrontend, composition root, 9-state capacity state machine, idempotency, correlation envelope, policy-as-code |
| 3 | Design | Security | **2** | **5** | **+3 B** | A = every PaaS `publicNetworkAccess: 'Enabled'`, 1 shared "god" MI, **unauthenticated public `/api/fabric/pause` with `Contributor` on capacity**. B = private endpoints + private DNS everywhere, `disableLocalAuth: true`, 7 per-service MIs, deny-public Azure Policy, custom least-privilege role |
| 4 | Development | Application Demo | **2** | **5** | **+3 B** | A = no clickable product UI, no API, narrative demo script only. B = Blazor WASM portal + 20 React screens + 32-endpoint FastAPI BFF, `drive_demo.py`, 66/66 rehearsed checks, minute-by-minute runbook |
| 5 | Development | Implementation completeness | **4** | **4** | tie | A = deeper science, no product. B = full stack, thinner algorithms. Genuine tie for different reasons |
| 6 | Monitoring | Logging and metrics | **2** | **3** | **+1 B** | A = `print()` in 15 Python files, zero correlation IDs (but *does* provision alert rules). B = `X-Correlation-ID` middleware end-to-end + SHA-256 hash-chained audit + Sentinel, **but App Insights provisioned and never consumed, zero alert rules in IaC** |
| 7 | AI Integration | Use of AI technologies | **4** | **3** | **+1 A** | **A is the only project that calls a live LLM** (GPT-5 + `text-embedding-3-large`, grounded RAG, citation enforcement, live Content Safety). B's knowledge extractor is `NotImplementedError` behind a keyword classifier |
| 8 | AI Integration | AI model selection and deployment | **3** | **4** | **+1 B** | A deploys models but with `publicNetworkAccess: Enabled` + `disableLocalAuth: false` on the account processing **operator PII**. B deploys no model but the Foundry/Speech landing zone is fully hardened |
| 9 | Agentic | Autonomy and orchestration | **3** | **3** | tie | Neither ships a true runtime planner/executor. A = single-turn RAG. B = agent identities + tool allow-list + HITL gates + `azure-ai-projects` scaffold |
| 10 | Agentic | Multi-agent coordination | **2** | **3** | **+1 B** | Neither has handoffs, reflection or state graphs at runtime. B has 2 declared agent identities with `FORBIDDEN_TOOL_NAMES` and a DRAFT→IN_REVIEW→APPROVED state machine; A's 10-agent pattern is **dev-time Copilot only** |
| 11 | Additional | Performance and reliability | **3** | **4** | **+1 B** | B = health/live + health/ready, retry + backoff, idempotency, caching, SBOM, CodeQL, 9 CI workflows. A = 1 workflow, 3 jobs, no health endpoints |
| 12 | Presentation | Clarity of explanation and presentation | **3.5** | **4.5** | **+1 B** | A = richer business case (real €), 16-chapter McKinsey analysis, MkDocs site — but **no .pptx** and its outline self-labels "30–40 min" (wrong length). B = validated 26-slide `.pptx`, explicit 30+15+15 plan, 50+ FAQ, TARGET🎯/EVIDENCE🔬 honesty discipline |
| | | **TOTAL / 60** | **34.5** | **48.5** | **+14 B** | |
| | | **Grade band** | **D/F** | **B** | | A(54–60) · B(48–53) · C(40–47) · D/F(<40) |

### Category subtotals

| Category | Max | A | B |
|---|:--:|:--:|:--:|
| Design | 15 | 8 | **15** |
| Development | 10 | 6 | **9** |
| Monitoring | 5 | 2 | **3** |
| AI Integration | 10 | **7** | **7** |
| Agentic Behavior | 10 | 5 | **6** |
| Additional Architecture Features | 5 | 3 | **4** |
| Presentation & Documentation | 5 | 3.5 | **4.5** |
| **Total** | **60** | **34.5** | **48.5** |

**Reading the table:** B wins or ties **11 of 12** criteria. A wins exactly one — *Use of AI technologies* —
and that single win is the most important thing to salvage.

---

## 📐 Independent code metrics (measured, not claimed)

Excludes `node_modules`, `.venv`, `bin`, `obj`, `dist`, `__pycache__`, `package-lock.json` and build bundles.

| Metric | Project A | Project B |
|---|---:|---:|
| Python files / LOC | 70 / 4,658 | **123 / 14,233** |
| C# files / LOC | **38 / 1,814** | 7 / 508 |
| TypeScript + TSX files / LOC | 0 / 0 | **77 / 7,665** |
| Blazor `.razor` files | 0 | **7** |
| Bicep files / LOC | 21 / 1,734 | **18 / 3,050** |
| PowerShell LOC | 1,279 | **3,873** |
| Markdown files / lines | **142 / 12,408** | 56 / 7,259 |
| pytest cases (actually executed) | 81 pass / 1 skip (1.45 s) | **206 pass (4 m 44 s)** |
| xUnit cases | **23** | 0 |
| Vitest cases | 0 | **29** |
| **Total automated tests** | 104 | **235** |
| CI workflows | 1 (3 jobs) | **9 (SBOM, CodeQL, path-filtered, evidence upload)** |
| Runnable product UI | ✗ (3-page simulator only) | ✓ **Portal + 20 screens + 32-endpoint API** |
| Git history | 80 commits | *(no repo — see risk)* |

**Interpretation:** A is a **documentation-led proposal with deep algorithmic spikes**
(1.7× the markdown, real MILP, real LLM). B is an **engineering-led product**
(≈3× the application code, 2.3× the tests, 1.8× the IaC, a real UI).
The jury grid rewards the second profile far more heavily.

---

## ✅ ❌ Pros and cons

### Project A — `20260507 - NovaSteel` ("Project Ignition")

**Pros**

| # | Strength | Evidence |
|---|---|---|
| A1 | **Only project with a live LLM call** — GPT-5 + `text-embedding-3-large` on `aif-novastee-dev-*`, Entra auth, live smoke test | `workloads\p4_knowledge_capture\` |
| A2 | **Real mathematical optimizer** — PuLP/CBC MILP, binary start-slot variables, per-furnace no-overlap constraints, weighted CO₂ + cost objective | `workloads\p2_energy_dispatch\milp.py` |
| A3 | **Genuinely physics-informed RUL** — heat-flux slope least-squares → time-to-failure extrapolation, MLflow GradientBoosting uplift path | `workloads\p1_predictive_maintenance\rul_model.py` |
| A4 | **Grounded RAG with enforced citations** and a decline path, plus live Azure Content Safety | `workloads\p4_knowledge_capture\` |
| A5 | **Strongest business case** — €0.6–1.1M build, €0.3–0.7M/yr run, ~€24.5M/yr energy benefit, sub-12-month payback, with assumptions **and sensitivity tables** | `docs\usecase\First_Proposal\05-cost-estimate.md` |
| A6 | **Exceptional strategic breadth** — 16-chapter McKinsey-style analysis, 10-chapter bilingual FR/EN explanation series, MkDocs product website, 11 hero images | `docs\usecase\0_preliminary analysis\2_mckensey_analysis\`, `docs\usecase\09_explaination\` |
| A7 | **Actually provisioned alert rules** — `Microsoft.Insights/scheduledQueryRules` for data freshness and P1 model drift, wired to an action group (B has none) | `infrastructure\modules\` |
| A8 | **A live Azure/Fabric environment exists** with working URLs | `MANUAL_STEPS.md` |
| A9 | **Exemplary dev-time agentic engineering** — a 10-agent Copilot orchestrator + specialists pattern used to build the repo | `.github\agents\`, `docs\usecase\1_agentic_work\` |
| A10 | GDPR erasure runbook implemented in code | `platform\governance\gdpr.py` |

**Cons**

| # | Weakness | Impact |
|---|---|---|
| A1 | **CRITICAL: unauthenticated public `/api/fabric/pause` and `/resume`** on the simulator Container App, holding built-in **`Contributor`** on the Fabric capacity — anyone with the FQDN can cost-DoS the capacity | 🔴 Security kill-shot if a juror finds it |
| A2 | **Everything is public by design** — `main.bicep:3` literally says *"Demo configuration: public network access, no private endpoints"*; zero private endpoints, no VNet module | 🔴 Fails "thoughtful security" |
| A3 | **One shared managed identity** for all workloads | 🔴 Violates least privilege |
| A4 | **Foundry account holding operator PII** has `publicNetworkAccess: Enabled` + `disableLocalAuth: false` (API keys accepted) | 🔴 GDPR exposure |
| A5 | **No product UI and no API** — the pillars are importable Python modules; the only UI is a 3-page ASP.NET simulator | 🔴 Kills the "Application Demo" criterion |
| A6 | **No `.pptx` and no 60-minute plan** — only a 949-word, 16-slide outline that self-labels *"30–40 minutes"* | 🔴 Wrong format for the defense |
| A7 | `docs\usecase\10_oral_defense\` contains **only the rating grid** — no speaker notes, no timing, no fallback assets | 🔴 |
| A8 | **`print()`-based logging** in 15 Python files, zero correlation IDs, no App Insights/OTel packages | 🟠 |
| A9 | **`platform\agents\` is an empty folder** despite being promised in the docs | 🟠 Credibility risk |
| A10 | **Four-country requirement is not expressed in IaC at all** | 🟠 |
| A11 | **All AI workloads classified "minimal-risk" under the EU AI Act** — indefensible for an €8M-per-failure furnace | 🟠 Jury will attack this |
| A12 | Thin CI (no CodeQL, no Dependabot, no SBOM) and its Python job installs from **public PyPI**, contradicting its own protected-feed policy | 🟠 |
| A13 | **Real tenant/subscription GUIDs committed** in a doc | 🟠 |
| A14 | ~55k words spread over **four overlapping narrative folders** telling the same story in different registers | 🟡 Presenter must choose one live |

---

### Project B — `20260724 - Novasteel 3`

**Pros**

| # | Strength | Evidence |
|---|---|---|
| B1 | **The only runnable product** — Blazor WASM shell + React/MUI/D3 microfrontend (20 screens) + 32-endpoint FastAPI BFF, all startable with 3 commands | `apps\`, `services\bff-api\` |
| B2 | **Rehearsed, deterministic demo** — `drive_demo.py`, 66/66 live BFF checks, seed `240725`, bit-for-bit reproducible, 11 captured moments at 0.31 s server time | `artifacts\demo-validation\` |
| B3 | **Best-in-class security architecture** — private endpoints + 6 private DNS zones, `publicNetworkAccess: Disabled`, `disableLocalAuth: true`, hub-and-spoke VNet + NSGs | `infra\bicep\modules\` |
| B4 | **Deny-public-network Azure Policy at subscription scope** — security is enforced, not just configured | `infra\policy\definitions\deny-public-network-access.json` |
| B5 | **7 per-service managed identities + per-plant OT identity + GitHub OIDC federation** defined in Bicep with the subject pinned to `repo:*:environment:*` | `infra\bicep\modules\identity.bicep` |
| B6 | **Custom least-privilege `Fabric Capacity Operator` role** instead of built-in Contributor | `infra\bicep\modules\roles.bicep:18-40` |
| B7 | **Four-country requirement is real in IaC** — `plants[]` parameterised with a per-plant Event Hub and per-plant identity | `infra\bicep\` |
| B8 | **6 resource groups** (hub / integration / apps / ai / fabric / monitoring) with per-context Key Vaults, across 4 environments | `infra\bicep\` |
| B9 | **Genuine hexagonal architecture** — Ports & Adapters in the knowledge orchestrator lets local fixtures and Azure adapters swap cleanly | `services\knowledge-orchestrator\...\adapters\base.py` |
| B10 | **SHA-256 hash-chained, append-only audit log** with redaction and `verify()` — the single best compliance artefact in either repo | `services\bff-api\src\bff_api\audit.py` |
| B11 | **End-to-end correlation IDs** — `X-Correlation-ID` middleware propagated into responses, audit records, SSE streams and adapters (60+ sites) | `services\bff-api\` |
| B12 | **9 CI workflows** with CodeQL (Py/JS/TS/C#), Dependabot on the protected feed, CycloneDX SBOM, `npm audit`, `dotnet --vulnerable`, every action pinned to a 40-char SHA, `AZURE_CREDENTIALS` grep-blocked, per-environment approvals | `.github\workflows\` |
| B13 | **One-command local validation** producing filed evidence | `tools\validation\Validate-Repository.ps1` → `artifacts\validation\` |
| B14 | **235 automated tests** across contract, simulator, backend, integration, E2E, infra and knowledge suites | `tests\` |
| B15 | **A real, validated 26-slide `.pptx`** (20 primary + 6 FAQ backups, 714 text runs, zero placeholders) with an explicit **30 + 15 + 15 = 60-minute** plan and 7 rehearsal checkpoints | `docs\presentation\` |
| B16 | **TARGET 🎯 vs EVIDENCE 🔬 discipline** applied to every quantitative claim — pre-empts the jury's hardest question | throughout `docs\` |
| B17 | **5-level demo fallback ladder** (live cloud → local replay → cached → recording → static pack; *"never diagnose > 10 s on-screen"*) | `docs\demo\demo-runbook.md` |
| B18 | **Explicit OT safety boundary** — decision-support only, never PLC / interlock / setpoint / schedule-commit / CMMS write | `README.md`, `docs\security\` |
| B19 | **Honest EU AI Act posture** — "high-risk-adjacent pending Legal", with Art. 9/10/12/14/15 obligations designed in, STRIDE threat model, 11 release-blocking gates | `docs\security\security-governance-and-threat-model.md` (73 KB) |
| B20 | **10 formal ADRs** | `docs\architecture\` |
| B21 | Sentinel onboarding, `dailyQuotaGb` capping, env-tiered retention (prod = 365 d), diagnostic settings on 7 modules | `infra\bicep\modules\` |
| B22 | Agent identities with a codified tool allow-list + `FORBIDDEN_TOOL_NAMES`, and a DRAFT→IN_REVIEW→APPROVED state machine with RBAC, optimistic concurrency and an eval harness | `services\knowledge-orchestrator\` |

**Cons**

| # | Weakness | Impact |
|---|---|---|
| B1 | **No AI model is actually deployed and no live LLM is ever called.** `AzureFoundryKnowledgeAgent.extract_draft` raises `NotImplementedError`; the runtime uses a keyword-bucket classifier | 🔴 Undercuts the whole "AI Integration" category |
| B2 | **The RUL "model" is `p50 = (thickness − 300) / sectorRate`** with hard-coded rates per sector — nothing physics-informed about it | 🔴 Biggest jury risk in the codebase |
| B3 | **Headline numbers are manufactured by calibration constants** — CO₂ savings capped at `min(15, savings × 0.84)` and peak reduction clamped to `[0.03, 0.07]` | 🔴 If a juror reads `service.py`, credibility collapses |
| B4 | **A Fabric notebook hard-codes the demo answer** — `demo_warning` = 0.87 risk / 21 days for `LUX-BF-01` + seed 240726 | 🔴 Looks like a rigged demo |
| B5 | **Application Insights is provisioned but never consumed** — `containerapps.bicep` never sets `APPLICATIONINSIGHTS_CONNECTION_STRING`; no service depends on `azure-monitor-opentelemetry`, `applicationinsights`, `Serilog` or `OpenTelemetry` | 🟠 |
| B6 | **Zero alert rules in IaC** — 10 alerts exist as prose in `docs\operations\operations-and-cost.md §4` with no `actionGroups` or `scheduledQueryRules` behind them | 🟠 |
| B7 | **Only 1 of 5 services uses a Python logger**, and `bff-api` relies on default `basicConfig`, so `extra={"correlation_id": …}` is silently dropped from stdout | 🟠 |
| B8 | **Container Apps deploy the `mcr.microsoft.com/k8se/quickstart:latest` placeholder image** — only `bff-api` has a Dockerfile, so `cd-services.yml` has nothing real to promote | 🟠 |
| B9 | **No git repository** — no history, no traceability, no ability to show engineering process | 🟠 Easy fix, real credibility cost |
| B10 | Audit and idempotency stores are **in-memory** — the "append-only auditable" guarantee does not survive a restart and blocks horizontal scale | 🟠 |
| B11 | **Fabric workspaces are never created** by any script — `solution-architecture.md:138-146`'s workspace isolation is doc-only | 🟠 |
| B12 | `zoneRedundant: false` everywhere; ADR-003's "West Europe is a tested EU contingency" is not exercised in IaC | 🟡 |
| B13 | **No cost/ROI figures at all** — the docs deliberately refuse to quote €/hr. A CFO on the jury gets nothing | 🟡 Costs points on business framing |
| B14 | No agent-to-agent handoffs, no reflection/critique loop, no state-graph orchestration at runtime | 🟡 Caps the Agentic category at 3 |
| B15 | Vendored `node_modules` and a committed 1.68 MB `analytics-mfe.js` bundle bloat the repo | 🟡 |
| B16 | pytest wall-time 4 m 44 s, dominated by `az bicep install` in the infra suite | 🟡 |
| B17 | Weaker visual assets (11 Mermaid + 3 images vs A's 29 Mermaid + 11 hero photos) and no French material for a Luxembourg jury | 🟡 |

---

## 🧭 Why B wins — the structural argument

The rating grid allocates **35 of 60 points (58%)** to *Design, Development, Monitoring and
Additional Architecture Features* — categories that reward **a built, secured, observable,
demonstrable system**. Only **10 points (17%)** go to *Use of AI technologies + model
deployment*, where A leads.

- A optimised for the **proposal**: it would win a consulting bid. It has the euros, the
  strategy chapters, the McKinsey framing, and three genuinely clever algorithms.
- B optimised for the **defense**: it has a system a juror can click, an IaC estate a juror
  can audit, a security posture that survives scrutiny, and a rehearsed 60-minute performance.

A's fatal problem is not depth — it is that **the jury cannot see anything run**, and that a
single `curl` against a public FQDN can pause the Fabric capacity. B's fatal problem is
narrower and entirely fixable: **its intelligence is simulated**, and the fix is a
*copy-paste from A*.

**Therefore: keep B, and harvest A.**

---

## 📁 Report index

| File | Contents |
|---|---|
| `00-executive-summary-and-scoring.md` | *(this file)* verdict, scoring table, metrics, pros/cons |
| `01-detailed-comparison.md` | Dimension-by-dimension deep dive with file-level evidence |
| `02-modification-plan.md` | Prioritised backlog to take B from 48.5 → 56+ |
| `03-oral-defense-plan.md` | 60-minute agenda, demo choreography, killer-question prep |
| `evidence\01-design-architecture.md` | Architecture & design-patterns agent report |
| `evidence\02-security-compliance.md` | Security & compliance agent report |
| `evidence\03-development-completeness.md` | Delivery & completeness agent report |
| `evidence\04-monitoring-observability.md` | Observability & SRE agent report |
| `evidence\05-ai-agentic.md` | AI & agentic-behaviour agent report |
| `evidence\06-presentation-documentation.md` | Presentation & documentation agent report |
