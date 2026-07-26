# NovaSteel — Modification Plan: taking Project B from 48.5 → 56+ / 60

> **Decision: submit Project B (`D:\work\20260724 - Novasteel 3`).**
> This is the prioritised backlog of changes. Every item states the rubric criterion it moves,
> the expected point gain, the effort, and the exact files to touch.
>
> **Golden rule of this plan:** *B has the body, A has the brains.* Nine of the twelve items
> below are a transplant from A, not new invention.

---

## Point-gain roadmap

| Wave | Items | Effort | Score after |
|---|---|---|:--:|
| **Baseline** | — | — | **48.5 / 60** (Grade B) |
| **Wave 1 — Credibility** (must do) | M1 · M2 · M3 | ~2–3 days | **54.5** (Grade A) |
| **Wave 2 — Rubric sweep** (high ROI) | M4 · M5 · M6 | ~2 days | **58.5** (Grade A) |
| **Wave 3 — Polish** (if time) | M7 · M8 · M9 · M10 · M11 · M12 | ~1–2 days | **59+** |

> Wave 1 alone crosses the A band (54–60). Do not start Wave 3 before Wave 1 is complete.

---

## 🔴 WAVE 1 — Credibility (non-negotiable)

These three fix the only defects that can *lose* the defense rather than merely cost points.
Each one is a defect where an inquisitive juror reading the source finds something that
contradicts what the slide said.

---

### M1 — Replace the deterministic energy optimizer with Project A's real MILP

| | |
|---|---|
| **Criterion** | Use of AI technologies (7) · Implementation completeness (5) |
| **Gain** | +2 (3→5 on #7), reinforces #5 |
| **Effort** | ~1 day |
| **Risk if skipped** | 🔴 **Highest single risk in the submission** |

**The problem.** `services\optimizer-worker\src\optimizer_worker\service.py` is a bounded-enumeration
heuristic whose headline outputs are manufactured by calibration constants:

```python
co2_pct = min(15, savings_pct * 0.84)          # ← CO₂ result is a multiplier
peak_reduction = clamp(raw, 0.03, 0.07)        # ← peak result is a clamp
```

The slide claims *"−22 % CO₂"* and *"constraint-aware optimization"*. A juror who opens this
file sees that the CO₂ number is arithmetic on another number, and the peak number cannot
leave `[3 %, 7 %]` regardless of input. That is a credibility collapse mid-defense.

**The fix.**

1. Port `D:\work\20260507 - NovaSteel\NovaSteel\workloads\p2_energy_dispatch\milp.py` into
   `services\optimizer-worker\src\optimizer_worker\milp.py`.
   It is a genuine PuLP/CBC model: binary start-slot decision variables, per-furnace
   no-overlap constraints, weighted CO₂ + cost objective.
2. Add `pulp` to `services\optimizer-worker\requirements.txt`
   (via the protected feed — `https://packagefeedproxy.microsoft.io/pypi/simple`).
3. Compute CO₂ **from physics**: `Σ (shifted_MWh × carbon_intensity_kgco2e_per_mwh)`.
   The `rawCarbonArbitragePct` field already in the payload shows this was the intent.
4. Keep the existing heuristic behind a **Strategy** switch as the CBC-unavailable fallback —
   this is itself a design-patterns point (criterion 2) and a reliability point (criterion 11).
5. Delete both calibration constants. Let the real number be whatever it is, and put the real
   number on the slide with the 🔬 EVIDENCE marker.

**Acceptance:** with `pulp` installed, the optimizer returns a schedule with zero
hard-constraint violations and a CO₂ figure traceable to per-slot carbon intensity; with
`pulp` absent, it falls back and logs a warning.

---

### M2 — Make the RUL model genuinely physics-informed, and delete the hard-coded demo answer

| | |
|---|---|
| **Criterion** | Use of AI technologies (7) · Implementation completeness (5) |
| **Gain** | reinforces the +2 above; removes a 🔴 risk |
| **Effort** | ~0.5 day |
| **Risk if skipped** | 🔴 The use case *literally specifies* "physics-informed ML model" |

**The problem — two defects.**

1. `services\scoring-worker\src\scoring_worker\service.py`:
   `p50 = (thickness - 300) / sector_rate` with hard-coded per-sector rates. There is no
   physics, no ML, and no uncertainty model — yet the deck says *"physics-informed"*.
2. `fabric\notebooks\ns-deterministic-demo-scoring.Notebook` **hard-codes the demo result**:
   `demo_warning` = 0.87 risk / 21 days for `LUX-BF-01` at seed 240726. If a juror opens
   this, the entire demo reads as rigged.

**The fix.**

1. Port `D:\work\20260507 - NovaSteel\NovaSteel\workloads\p1_predictive_maintenance\rul_model.py`.
   It performs a least-squares regression on the **heat-flux slope** over the last N days and
   extrapolates to the failure threshold — thermal-degradation physics, exactly what the use
   case asks for.
2. Derive **P10 / P50 / P90 from the fit residuals** instead of returning fixed spreads. The
   uncertainty band then means something, and you can defend it.
3. **Delete the `demo_warning` hard-code.** Feed the deterministic simulator trace through the
   real model. If the seeded scenario is calibrated correctly it will still land near
   21 days — but now because the model computed it.
4. Optional, high-value: bring A's MLflow GradientBoosting uplift path across as the
   "learned residual on top of the physics prior" — that phrase alone is worth a point on #7.

**Acceptance:** changing the input thermal trace changes the RUL output; the notebook contains
no literal `0.87` or `21`; P10/P50/P90 derive from residuals.

---

### M3 — Actually call a model: wire the live Foundry/GPT-5 knowledge extraction

| | |
|---|---|
| **Criterion** | Use of AI technologies (7) · AI model selection and deployment (8) |
| **Gain** | +2 (3→5 on #7), +1 (4→5 on #8) |
| **Effort** | ~1 day |
| **Risk if skipped** | 🔴 *"Which model are you calling?"* — currently the honest answer is "none" |

**The problem.** `AzureFoundryKnowledgeAgent.extract_draft` raises `NotImplementedError`; the
runtime falls back to a keyword-bucket classifier. B's Ports & Adapters design makes this a
*clean* gap rather than a hack — but the AI Integration category is 10 points and B currently
earns them on landing-zone hardening alone.

**The fix.**

1. Implement `extract_draft` in
   `services\knowledge-orchestrator\src\knowledge_orchestrator\adapters\azure_foundry.py`,
   reusing A's prompt and citation-enforcement logic from `workloads\p4_knowledge_capture\`.
2. Add the model deployments to `infra\bicep\modules\foundry.bicep` — GPT-5 (or GPT-4o) +
   `text-embedding-3-large`. **Keep B's hardening**: `disableLocalAuth: true`,
   `publicNetworkAccess: 'Disabled'`, private endpoint, Sweden Central.
   *This combination — A's model deployment inside B's landing zone — is the 5/5 answer on
   criterion 8.*
3. Port A's **citation-enforcement regex + decline path**. Grounding you can demonstrate live
   is worth more than any slide about hallucination.
4. Enable **Azure AI Content Safety** on the deployment (A already proved this works).
5. Keep the local fixture adapter as the demo-mode default and the offline fallback. The port
   already exists — this is why B's hexagonal design was the right call.

**Acceptance:** with cloud credentials the orchestrator produces a real LLM-extracted draft
with citations; without them it falls back to fixtures and the demo still runs.

---

## 🟠 WAVE 2 — Rubric sweep (highest points per hour)

---

### M4 — Emit telemetry: OpenTelemetry + the four business KPIs as custom metrics

| | |
|---|---|
| **Criterion** | Logging and metrics (6) · Performance and reliability (11) |
| **Gain** | +2 (3→5 on #6), reinforces #11 |
| **Effort** | ~0.5 day |

**The problem.** Application Insights is **provisioned and never consumed**.
`infra\bicep\modules\containerapps.bicep` never sets `APPLICATIONINSIGHTS_CONNECTION_STRING`,
and no service depends on `azure-monitor-opentelemetry`, `applicationinsights`, `Serilog` or
`OpenTelemetry`. Only 1 of 5 services uses a Python logger, and `bff-api` uses the default
`basicConfig`, so `extra={"correlation_id": …}` is **silently dropped from stdout**.

**The fix.**

1. Add `APPLICATIONINSIGHTS_CONNECTION_STRING` to the Container Apps env block in
   `containerapps.bicep`.
2. Add `azure-monitor-opentelemetry` to each service's `requirements.txt` and call
   `configure_azure_monitor()` at startup. B's `X-Correlation-ID` middleware already exists —
   map it onto the W3C `traceparent` and distributed tracing works end-to-end **for free**.
3. Replace the default `basicConfig` with a **JSON formatter** so `correlation_id` actually
   reaches stdout. Roll `logging.getLogger(__name__)` out to the other 4 services (they
   currently have none).
4. **Emit the four business KPIs as custom metrics** — this is the highest-impact item on the
   whole page:
   - `novasteel.energy.kwh_per_tonne`
   - `novasteel.emissions.co2_kg`
   - `novasteel.rul.days_p50` + `novasteel.rul.confidence`
   - `novasteel.quality.high_grade_yield_pct`

> 💡 **Defense gold.** Being able to say *"every number on this executive dashboard is also an
> Application Insights custom metric with an alert on it"* converts a Satisfactory into an
> Excellent on criterion 6 **and** gives you a genuinely impressive live demo moment.

---

### M5 — Move the 10 documented alerts from prose into Bicep

| | |
|---|---|
| **Criterion** | Logging and metrics (6) · Performance and reliability (11) |
| **Gain** | completes #6 → 5; supports #11 → 5 |
| **Effort** | ~2 hours |

**The problem.** `docs\operations\operations-and-cost.md §4` lists 10 alerts. There is **not a
single `actionGroups` or `scheduledQueryRules` resource** anywhere in `infra\bicep\`. This is
the one place Project A is unambiguously better.

**The fix.** Copy the pattern from
`D:\work\20260507 - NovaSteel\NovaSteel\infrastructure\modules\` — A ships working
`Microsoft.Insights/scheduledQueryRules` for data freshness and model drift, wired to an action
group. Create `infra\bicep\modules\alerts.bicep` with all 10, referencing the M4 custom metrics
plus BFF availability, ingestion lag and capacity utilisation. Add an `actionGroups` resource
with an email/webhook receiver per environment.

---

### M6 — Add real multi-agent coordination: a critic loop and one handoff

| | |
|---|---|
| **Criterion** | Autonomy and orchestration (9) · Multi-agent coordination (10) |
| **Gain** | +2 (3→5 on #9), +2 (3→5 on #10) — **4 points, the largest single gain available** |
| **Effort** | ~1 day |

**The problem.** 10 points sit in the Agentic category and B currently scores 6. Neither
project has handoffs, reflection, or state-graph orchestration at runtime. The grid names these
patterns *explicitly*: *"coordination patterns such as handoffs, reflections, or state graphs"*.

**The fix — three additions, each directly quoting the rubric's own vocabulary.**

1. **Reflection / critic loop** (criterion 10). After M3's extractor produces a draft
   procedure, run a **second LLM pass as a critic**: does every claim carry a citation to
   retrieved source text? Is any step unsafe? The critic returns `APPROVE` or
   `REVISE + reasons`; on `REVISE` the extractor runs once more (cap at 2 iterations).
   Log every iteration to the hash-chained audit — you can then *show the reflection happening*
   on screen.
2. **Handoff** (criterion 10). Make the `energy-dispatch` agent hand off to the
   `scoring`/RUL agent when a proposed schedule would push a furnace past its RUL threshold.
   The RUL agent returns a constraint, the dispatch agent re-plans. **This is a genuinely
   compelling demo moment**: two agents negotiating a schedule that is both cheap and safe —
   and it maps perfectly onto the use case's real business tension.
3. **State graph** (criterion 9). Promote the existing DRAFT→IN_REVIEW→APPROVED workflow into
   an explicit, introspectable state graph (LangGraph, or Semantic Kernel process framework, or
   a hand-rolled `StateGraph` class — hand-rolled is fine and avoids a dependency). Render it
   as a Mermaid diagram **generated from the code** and put it on a slide. Keep the existing
   human-in-the-loop approval gates as terminal nodes — HITL *inside* a state graph is exactly
   the "autonomy with control" story the EU AI Act narrative needs.

> The agent identities, tool allow-list and `FORBIDDEN_TOOL_NAMES` already exist in
> `services\knowledge-orchestrator\`. This is wiring, not greenfield.

---

## 🟡 WAVE 3 — Polish

### M7 — Import Project A's cost model and ROI story
**Criterion:** Clarity of explanation (12) · **Gain:** +0.5 · **Effort:** 2 h

B deliberately refuses to quote any €/hr. If a CFO or a commercially-minded juror is on the
panel, that is an unanswered question. Port the model from
`D:\work\20260507 - NovaSteel\NovaSteel\docs\usecase\First_Proposal\05-cost-estimate.md`
(€0.6–1.1 M build, €0.3–0.7 M/yr run, ~€24.5 M/yr energy benefit, sub-12-month payback, with
assumptions **and sensitivity tables**) into `docs\operations\operations-and-cost.md`, and add
**one** CFO bridge slide. Label every figure 🎯 TARGET / illustrative — consistent with B's
existing honesty discipline, which is what makes this safe to add.

### M8 — `git init` and build a real history
**Criterion:** credibility across all criteria · **Gain:** intangible but real · **Effort:** 1 h

B has **no git repository**. A has 80 commits. "Show me your engineering process" currently has
no answer. Initialise, add a proper `.gitignore` (exclude `node_modules`, `bin`, `obj`,
`artifacts`, the committed `analytics-mfe.js` bundle), and commit in logical, well-messaged
slices — contracts → infra → services → apps → tests → docs. Enable branch protection if you
push it. Also removes the repo-bloat con (B15).

### M9 — Ship real Dockerfiles for the 4 non-BFF services
**Criterion:** Implementation completeness (5) · **Gain:** +1 (4→5) · **Effort:** 3 h

`infra\bicep\modules\containerapps.bicep:27` deploys `mcr.microsoft.com/k8se/quickstart:latest`.
Only `bff-api` has a Dockerfile, so `cd-services.yml` — which promotes by immutable
digest — has nothing to promote. Add Dockerfiles to `optimizer-worker`, `scoring-worker`,
`ingest-relay`, `knowledge-orchestrator` plus a `ci-build-services.yml` that publishes to an
approved registry. Removes the "what's actually deployed?" trap.

### M10 — Persist audit and idempotency out of process
**Criterion:** Design (1) · Performance and reliability (11) · **Gain:** +0.5 · **Effort:** 3 h

`services\bff-api\src\bff_api\{audit.py,idempotency.py}` are in-memory, so the "append-only
auditable" guarantee dies on restart and the BFF cannot scale past one replica. Add an
`adapters\` folder mirroring the knowledge-orchestrator's hexagonal pattern, with an Azure
Table/Cosmos adapter. **Keep the SHA-256 hash chain** — it becomes far more impressive once
it's durable.

### M11 — French executive summary + hero visuals
**Criterion:** Clarity of explanation (12) · **Gain:** +0.5 · **Effort:** 2 h

Luxembourg jury: add a 1-page FR executive summary (A already has a bilingual FR/EN series in
`docs\usecase\09_explaination\` to draw from). Add 2–3 hero visuals — A has 11 real
blast-furnace photos and 29 Mermaid diagrams against B's 11 + 3. Compress B's dense slides
8–10 and print a 1-page presenter rehearsal card.

### M12 — Fabric workspace bootstrap + prod zone redundancy
**Criterion:** Design (1) · Performance and reliability (11) · **Gain:** +0.5 · **Effort:** 3 h

Nothing in the repo actually **creates** the `NS-<env>-{RTI-Ingress,DataCore,ML,Analytics}`
workspaces, so `solution-architecture.md:138-146`'s workspace isolation is a doc-only claim.
Add `fabric\scripts\bootstrap-workspaces.ps1` (Fabric REST/CLI) driven from
`fabric\deployment-parameters\<env>.json`, assigning capacity and applying OneLake roles.
Separately, change `zoneRedundant: false` → `zoneRedundant: isProd` in `containerapps.bicep:56`
and `eventhubs.bicep:59`, and add a `secondaryLocation` parameter so ADR-003's West Europe
contingency is exercised rather than asserted.

---

## What to take from Project A — the harvest list

| From A | To B | Why |
|---|---|---|
| `workloads\p2_energy_dispatch\milp.py` | `services\optimizer-worker\` | Real PuLP/CBC MILP → M1 |
| `workloads\p1_predictive_maintenance\rul_model.py` | `services\scoring-worker\` | Physics-informed heat-flux regression → M2 |
| `workloads\p4_knowledge_capture\` prompts + citation regex + decline path | `services\knowledge-orchestrator\adapters\azure_foundry.py` | Live grounded RAG → M3 |
| Foundry model deployments in `infrastructure\modules\foundry.bicep` | `infra\bicep\modules\foundry.bicep` (**keep B's hardening**) | A's models + B's landing zone = 5/5 on #8 → M3 |
| `Microsoft.Insights/scheduledQueryRules` + action group | `infra\bicep\modules\alerts.bicep` | The one thing A does better on monitoring → M5 |
| `docs\usecase\First_Proposal\05-cost-estimate.md` | `docs\operations\operations-and-cost.md` | €/ROI/payback + sensitivity → M7 |
| Hero images from `docs\business\images\` | `docs\presentation\` | Visual warmth → M11 |
| FR content from `docs\usecase\09_explaination\` | New FR exec summary | Luxembourg jury → M11 |
| `.github\agents\` 10-agent pattern | Reference only | A 60-second "how I built this" slide — **never** as the answer to criterion 9 |

## What to explicitly NOT take from Project A

| ❌ Do not port | Reason |
|---|---|
| The simulator's `/api/fabric/pause` + `/resume` endpoints | Unauthenticated, public, `Contributor` on the capacity |
| `main.bicep`'s public-network posture | B's private-endpoint estate is worth 3 points; do not dilute it |
| The single shared managed identity | B's 7 per-service MIs are a differentiator |
| The "all workloads are minimal-risk" EU AI Act classification | Indefensible; B's "high-risk-adjacent pending Legal" is the correct posture |
| The four overlapping narrative folders (~55 k words) | Documentation bloat; B's focus is an asset |
| Committed tenant/subscription GUIDs | Rotate them in A regardless of which project ships |

---

## Pre-defense checklist

- [ ] **M1** MILP replaces the `× 0.84` / `[0.03, 0.07]` constants
- [ ] **M2** RUL derives from heat-flux physics; `demo_warning` hard-code deleted
- [ ] **M3** A live model call succeeds end-to-end; fixture fallback still works offline
- [ ] **M4** Custom KPI metrics visible in Application Insights
- [ ] **M5** Alerts exist as Bicep resources, not prose
- [ ] **M6** Critic loop + RUL↔dispatch handoff + state graph demonstrable on screen
- [ ] `pwsh .\tools\validation\Validate-Repository.ps1` passes clean
- [ ] `drive_demo.py` still returns 66/66 after all changes
- [ ] Every number on every slide carries 🎯 TARGET or 🔬 EVIDENCE
- [ ] Full 60-minute dry run completed against a clock, twice
- [ ] Fallback ladder tested — pull the network cable mid-demo and recover in < 10 s
