# NovaSteel — Proof of execution

> **Purpose.** This document maps every requirement of the use-case brief
> (`docs/usecase/usecase.md`) to the part of the running NovaSteel solution that
> satisfies it, and states openly where the demo is a surrogate for the
> production claim.
>
> **Solution:** NovaSteel — the AI-powered steel production optimization platform.
> **Operator:** AxelorMetal — the fictitious Luxembourg integrated steel producer
> operating in Luxembourg, Germany, Belgium and Spain.

---

## Summary

Every requirement in the brief carries a stable **reference ID**. Those IDs are
not documentation-only: they are stamped on the screens that satisfy them, and
the in-app **Proof of Execution** page (`/{site}/proof-of-execution/requirements`)
renders the same register with a searchable, sortable evidence matrix and a
deep link into each proving screen.

| Category | IDs | Count | Fully met | Demo surrogate / partial |
|---|---|---:|---:|---:|
| Regulatory context | `REG-01` … `REG-03` | 3 | 2 | 1 |
| Business challenge | `CHL-01` … `CHL-05` | 5 | 5 | 0 |
| Transformation objective | `OBJ-01` … `OBJ-04` | 4 | 4 | 0 |
| Expected outcome | `OUT-01` … `OUT-04` | 4 | 1 | 3 |
| AI infusion point | `AI-01` … `AI-03` | 3 | 3 | 0 |
| **Total** | | **19** | **15** | **4** |

Status vocabulary used throughout:

| Status | Meaning |
|---|---|
| **Met** | The capability exists and runs in the demo. |
| **Partial** | The capability exists but is narrower than the brief implies. |
| **Demo surrogate** | The *mechanism* is real; the *headline number* is a target derived from the synthetic dataset, and is labelled as a target everywhere in the UI. |

The single machine-readable source of truth is
[`apps/analytics-mfe/src/proof/proofCatalog.ts`](../../apps/analytics-mfe/src/proof/proofCatalog.ts).

The same in-app page carries a second tab, **Use case**
(`/{site}/proof-of-execution/use-case`), which reproduces the original brief
[`docs/usecase/usecase.md`](../usecase/usecase.md) verbatim with every clause
badged by the reference IDs that prove it. Every source-code evidence entry on
these screens links straight to the file in the GitHub repository. The companion
rating-grid answer lives in
[`docs/tech/technical-analysis.md`](../tech/technical-analysis.md) and its own
in-app screen, **Technical Requirements**
(`/{site}/technical-requirements/criteria`).
This document and the in-app page are both projections of it — they cannot drift
apart without a failing build.

---

## How to read the evidence

Each block below follows the same shape:

1. **Requirement** — what the brief asks for, near-verbatim.
2. **How NovaSteel satisfies it** — the mechanism, in plain language.
3. **Evidence** — where a reviewer can see it: code, API route, screen, infrastructure.
4. **Caveat** — what is *not* fully real. Stated pre-emptively, because a jury
   that discovers a caveat by grepping loses more confidence than one that reads
   it here first.

---

## 1. Regulatory context

> *Regulatory Context: GDPR • EU AI Act • Sector-specific EU Directives*

### `REG-01` — GDPR

**Requirement.** Personal data captured from operators must be lawful, minimised
and erasable.

**How NovaSteel satisfies it.** Knowledge capture is the only place in the
platform where personal data exists, and it is fenced on three sides:

- **Lawfulness.** An interview cannot be created without a recorded consent grant
  whose `scope` is `knowledge-capture` and whose `retentionDays` is positive. The
  consent record is a state machine, and `is_capture_allowed()` re-checks scope
  and expiry on every use — consent is not a checkbox captured once.
- **Minimisation.** Transcripts pass a PII detector before any model sees them.
  It recognises e-mail, phone, IBAN (validated mod-97, so it does not fire on
  arbitrary digit strings), person names, `EMP-#####` employee IDs, IPv4 and
  dates of birth, and replaces each with `[REDACTED:{KIND}]`. Attribution that
  must survive is pseudonymised with a salted SHA-256 prefix rather than kept in
  clear.
- **Erasability.** A right-to-erasure request hard-deletes the source transcript,
  pseudonymises the derived procedure attribution, and **appends** a tombstone to
  the audit chain. The chain is verified before and after the operation, so
  erasure cannot be used as a cover for tampering — which is precisely the
  tension between Art. 17 and an append-only audit obligation.

**Evidence.**

| Kind | Where |
|---|---|
| Code | `services/knowledge-orchestrator/src/knowledge_orchestrator/erasure.py` — `ErasureService` |
| Code | `services/knowledge-orchestrator/src/knowledge_orchestrator/pii.py` — `detect()`, `redact()`, `pseudonymize()` |
| Code | `services/knowledge-orchestrator/src/knowledge_orchestrator/consent.py` — `ConsentRecord`, `is_capture_allowed()` |
| Code | `services/knowledge-orchestrator/src/knowledge_orchestrator/audio.py` — blocks audio whose consent is not `GRANTED` |
| API | `POST /v1/privacy/erasure-requests`, `POST /v1/privacy/erasure-requests/{id}:execute` (role `Compliance.Auditor`) |
| API | `POST /v1/knowledge/interviews` — rejects a missing or out-of-scope consent grant |
| Screen | Sustainability & Compliance › **Audit & Reports** |
| Tests | `tests/knowledge/` — erasure, consent and PII suites |

**Caveat.** Automatic deletion once `retentionDays` elapses is documented as an
operations runbook; there is no scheduled job in this repository that enforces it.

---

### `REG-02` — EU AI Act

**Requirement.** AI that influences industrial operations needs human oversight,
transparency and traceability.

**How NovaSteel satisfies it.** The design principle is *no agent acts on the
plant*. That is enforced structurally, not by prompt instruction:

- **Human-in-the-loop as a graph node, not a convention.** The knowledge workflow
  is an explicit, introspectable `StateGraph`. `IN_REVIEW` is a `gated` node with
  `actor="human"`; `APPROVED` and `REJECTED` are terminal. `to_mermaid()`
  generates the state diagram directly from the graph definition, so the diagram
  in the deck is generated from the code that runs, not drawn by hand.
- **Agents cannot approve their own work.** Each agent identity has an explicit
  tool allow-list, and `FORBIDDEN_TOOL_NAMES` reserves approve, publish, commit,
  schedule and delete for humans. `ToolRegistry.call()` raises `ToolNotAllowed`
  rather than silently ignoring a forbidden call.
- **Untrusted input is spotlighted.** Retrieved documents, tool results and
  transcripts are wrapped in `<<UNTRUSTED_DATA>>` markers and the safety
  meta-prompt instructs the model never to follow instructions found there.
- **Content safety on both directions.** Six categories (hate, self-harm, sexual,
  violence, jailbreak, prompt injection) are scored 0–7 and blocked at severity ≥ 4
  on input *and* output.
- **Oversight is monitored, not assumed.** A Sev-1 alert fires if an
  `energy_dispatch_executed` event ever appears without a matching
  `energy_dispatch_approved` audit event — the control is instrumented.

**Evidence.**

| Kind | Where |
|---|---|
| Code | `.../state_graph.py` — `StateGraph`, `build_knowledge_capture_graph()`, `to_mermaid()` |
| Code | `.../tools.py` — `AGENT_TOOL_ALLOWLIST`, `FORBIDDEN_TOOL_NAMES`, `ToolRegistry.call()` |
| Code | `.../prompt_defense.py` — `SAFETY_META_PROMPT`, `scan_for_injection()`, `spotlight()` |
| Code | `.../content_safety.py` — `screen_input()`, `screen_output()` |
| Code | `.../procedure_workflow.py` — approval requires the `Knowledge.Publisher` role and a matching `expectedVersion` |
| API | `POST /v1/energy/recommendations/{id}:approve` — role `EnergyPlanner.Approve` |
| Infra | `infra/bicep/modules/alerts.bicep` — Sev-1 "dispatch without approval" rule |
| Code | `services/bff-api/src/bff_api/audit.py` — SHA-256 hash-chained, redacting, verifiable audit log |
| Screen | Sustainability & Compliance › **Audit & Reports** |

**Caveat.** The Annex III risk classification and the model card exist as
documentation. There is no structured `RiskClassification` object in code, and
`MODEL_VERSION` is the only model-identity marker emitted at runtime.

---

### `REG-03` — Sector-specific EU directives

**Requirement.** Comply with sector-specific EU directives, principally the
EU Emissions Trading System.

**How NovaSteel satisfies it.** The Fabric gold layer computes Scope 1 and
Scope 2 emissions in tonnes CO₂e, subtracts the free-allocation benchmark, and
prices the residual as euro exposure. The **ETS Exposure** screen shows allowance
consumption against the period cap with a projection to period end, and the
emissions ledger behind it is append-only.

**Evidence.**

| Kind | Where |
|---|---|
| Code | `fabric/notebooks/ns-silver-to-gold.Notebook` — `scope1_co2e_t`, `scope2_co2e_t`, `free_allocation_t`, `ets_exposure_eur` |
| API | `GET /v1/sustainability/summary`, `GET /v1/sustainability/emissions` |
| Screen | Sustainability & Compliance › **ETS Exposure**, **Emissions Ledger** |

**Caveat — this one is genuinely partial.** The free-allocation benchmark
(1.50 t CO₂e per tonne of crude steel) and the allowance price are demo
constants, not a live registry feed. **CBAM and the Industrial Emissions
Directive are described in the architecture documentation but have no code
implementation** — no permit limits, no stack-emission monitoring, no CBAM
certificate logic. We claim ETS, and only ETS.

---

## 2. Business challenge

### `CHL-01` — Energy is 35% of production cost with no real-time optimization

**How NovaSteel satisfies it.** Energy-intensive batches are re-placed against the
half-hourly spot-price and carbon-intensity curve by a **mixed-integer linear
program** (PuLP with the CBC solver): binary placement variables `x[b,s]`, one
assignment constraint per batch, per-slot capacity constraints, and an objective
that trades euro against kilograms of CO₂ with explicit weights. A tie-break term
biases the solver toward the originally planned slot, so the schedule the operator
sees is the *minimum* disturbance that achieves the saving.

The output is a *proposal*. It becomes a plan only when a human with the
`EnergyPlanner.Approve` role approves it, and that approval is written to the
hash-chained audit log with the actor recorded.

**Evidence.** `services/optimizer-worker/src/optimizer_worker/milp.py` ·
`.../service.py` (`EnergyDispatchOptimizer.simulate()`) ·
`POST /v1/energy/schedules:simulate` · Energy Optimization › **Spot & Schedule**,
**Load-Shift Simulator**.

**Caveat.** The demo runs on fixture spot prices, not a live ENTSO-E feed. If
PuLP/CBC is unavailable the service falls back to a deterministic greedy
heuristic, and the response says which strategy produced the result — the UI
never hides the difference.

---

### `CHL-02` — CO₂ under EU ETS penalty pressure

**How NovaSteel satisfies it.** Carbon intensity is a first-class term in the
dispatch objective, not a post-hoc report: the solver minimises
`co2_weight × MWh × carbon + cost_weight × MWh × price`. The resulting emissions
land in an immutable ledger, feed the ETS exposure figure, and are emitted as the
custom metric `novasteel.emissions.co2_kg` so they can be alerted on.

**Evidence.** `.../milp.py` (objective) · `services/optimizer-worker/.../metrics.py` ·
Sustainability & Compliance › **Emissions Ledger** · `infra/bicep/modules/alerts.bicep`.

---

### `CHL-03` — Furnace lining wear is unpredictable; failures cost €8M

**How NovaSteel satisfies it.** Refractory thickness and local heat flux are
regressed by ordinary least squares over a rolling observation window. The fit is
extrapolated to the minimum-safe thickness to give time-to-failure, and the
standard error of the slope is propagated through that extrapolation to produce
P10/P50/P90 bands. Confidence is not a decoration — it is computed from fit
quality (r²), window length, slope magnitude and heat-flux corroboration, and it
drives a model-drift alert when it degrades.

Crucially, the **P10 bound is the actionable number**. Planning against P50 on a
€8M failure mode would be indefensible; the screen leads with the lower bound.

**Evidence.** `services/scoring-worker/.../physics_features.py`
(`extract_thermal_features()`, `linear_fit()`) · `.../rul_model.py`
(`estimate_rul()`, `confidence_score()`, `compute_drivers()`) ·
`GET /v1/furnaces/{assetId}/lining-forecast` · Furnace Health › **Lining Forecast**.

---

### `CHL-04` — Quality consistency in high-grade automotive steel

**How NovaSteel satisfies it.** Every batch is scored for first-pass yield risk
from its process bias, plotted on SPC charts with control limits, and exposed to a
**bounded** what-if so a quality engineer can test a corrective set-point before
committing it. "Bounded" is deliberate: the what-if refuses inputs outside the
range the surrogate was calibrated over, rather than extrapolating confidently
into nonsense.

**Evidence.** `services/scoring-worker/.../service.py` (`score_quality()`,
`quality_what_if()`) · `GET /v1/quality/batches`, `POST /v1/quality/what-if` ·
Quality › **Batch Quality**, **Defect Analytics (SPC)**.

**Caveat.** The yield model is a calibrated surrogate over the coiling-temperature
bias, not a trained metallurgical model.

---

### `CHL-05` — Retiring operators, knowledge disappearing

**How NovaSteel satisfies it.** A consent-bound interview is transcribed, mined
for procedure steps by an extraction agent, reviewed by a **critic agent**, and
only then offered to a human publisher. Approved procedures become the *only*
corpus the retrieval layer will cite — a draft can never be quoted as if it were
approved practice.

**Evidence.** `.../procedure_workflow.py` (`create_draft()`, `submit_for_review()`,
`approve()`, `reject()`) · `.../retrieval.py` (hybrid lexical + cosine over
approved procedures) · `POST /v1/knowledge/interviews`, `GET /v1/knowledge/search` ·
Knowledge Hub › **Procedures**, **Capture Status**.

---

## 3. Transformation objective

### `OBJ-01` — Reduce energy consumption

The dispatch optimiser produces a re-timed schedule; energy per tonne is computed
from the solved plan (`kwh_per_tonne = total_mwh × 1000 / total_tonnage`) and
emitted as `novasteel.energy.kwh_per_tonne`. The Command Center shows it against
target. → *see `CHL-01`, `OUT-01`.*

### `OBJ-02` — Predict equipment failures

Lining remaining-useful-life is scored continuously. A Fabric Real-Time
Intelligence activator rule (`ACT-FUR-001`) fires when `risk_score ≥ 0.80` **and**
`P50 ≤ 21 days` sustained for five minutes, and the Maintenance Planner turns that
signal into scheduled work with a slot and an owner. → *see `CHL-03`, `OUT-03`.*

### `OBJ-03` — Improve steel quality

Predicted first-pass yield, defect Pareto and SPC control limits are computed per
grade and per batch, aggregated into `fact_quality_yield` in the gold layer, and
fed back to caster set-points through the bounded what-if.
→ *see `CHL-04`, `OUT-04`.*

### `OBJ-04` — Capture and structure expertise before it is lost

The knowledge pipeline turns a spoken interview into a structured, cited, reviewed
and versioned procedure. Nothing reaches the library without a named human
publisher and a complete audit trail; `enforce_extraction_grounding()` rejects any
draft containing a claim that cannot be traced to a transcript segment.
→ *see `CHL-05`, `AI-03`.*

---

## 4. Expected outcomes

> **Read this section first if you are going to read only one.**
>
> The four headline numbers in the brief are **targets on a synthetic dataset**.
> The *mechanisms* that would produce them are real and running; the *magnitudes*
> are properties of the generated data. Every one of these figures is labelled
> "target" in the UI — never "measured". We would rather be asked about this than
> be caught by it.

### `OUT-01` — Energy per tonne reduced by 14% · **demo surrogate**

Energy per tonne is genuinely computed from the solved dispatch schedule. The
baseline it is compared against is generated: the demo branch of the gold-layer
notebook sets `baseline_energy_gj = energy_gj / 0.86`, which *is* the −14%.

**What is real:** the MILP, the metric, the plumbing to Application Insights.
**What is generated:** the 0.86 baseline ratio.
**What the UI says:** `target −14% energy/t` — with the live modelled saving shown
separately and smaller.

### `OUT-02` — CO₂ reduced by 22% · **demo surrogate**

Same shape: `baseline_co2e_t = total_co2e_t / 0.78` in the demo environment.

This one deserves the sharpest honesty, because it is the number a juror is most
likely to challenge. **Load-shifting alone produces a single-digit percentage CO₂
reduction on this dataset**, and the modelled dispatch reduction the BFF returns
reflects that. The −22 % ambition in the brief assumes the accompanying grid-mix
and scrap-ratio measures set out in the business case, which are outside the scope
of what this platform controls. NovaSteel's contribution is the carbon-aware
dispatch term; it is not the whole −22 %.

### `OUT-03` — Failure predicted 21 days in advance · **met**

This is the one headline outcome that is structurally, rather than statistically,
true. The RTI activator threshold *is* 21 days at risk ≥ 0.80, the alert path is
wired, and the demo scenario walks a furnace across it live.

**Caveat.** The estimator is a least-squares regression over physical signals with
propagated uncertainty. It is **not** a thermodynamic wear model — there is no
Arrhenius kinetics term in the code, and we do not claim one. The
gradient-boosted residual-learning hook (`MLUpliftHook`) is a declared interface
with no trained artefact behind it.

### `OUT-04` — High-grade yield improved by 8% · **demo surrogate**

The improvement is the delta between the pre-platform baseline recorded in the
scenario manifest (88 %) and the scored prediction (≈ 94.8 %) on synthetic data.
The scoring is real; the baseline is a manifest constant.

---

## 5. AI infusion point

### `AI-01` — Physics-informed ML predicting lining degradation from thermal signatures

**Thermal signatures in, degradation out.** The raw signals are refractory
thickness (`hearth_refractory_estimate`), local heat flux (`local_heat_flux`) and
cooling-water delta. `extract_thermal_features()` converts them into physical
quantities — apparent thermal resistance (`R = ΔT / q`), a water-side heat proxy,
and a normalised health index — and the RUL model regresses on those. Every
driver that moved the prediction is returned with it and rendered in the *Why?*
panel, so the forecast is explainable at the point of use.

**Evidence.** `services/scoring-worker/.../physics_features.py` ·
`.../rul_model.py` · Furnace Health › **Thermal Explorer**, **Lining Forecast** ·
custom metrics `novasteel.rul.days_p50`, `novasteel.rul.confidence` ·
model-drift alert in `alerts.bicep`.

**Caveat — stated plainly.** "Physics-informed" here means *physics-derived
features in a regression with propagated uncertainty*. It does not mean a
first-principles thermodynamic model. We consider this the honest reading of what
is implementable and defensible on synthetic data in a demo; a production
deployment would fit the residual learner against real failure history.

### `AI-02` — Energy dispatch optimization agent scheduling around spot prices

A named agent identity (`energy-dispatch`) with its own tool allow-list
(`read_energy_context`, `forecast_demand`, `simulate_schedule`,
`propose_recommendation` — note the absence of anything that commits) solves the
MILP and *proposes* a schedule.

**The interesting part is what happens when the cheap schedule is unsafe.** If a
proposal would push a furnace past its remaining-useful-life limit, the dispatch
agent **hands off** to the scoring agent, which returns a `RULConstraint`; the
dispatch agent then re-plans under that constraint. Two agents negotiating a
schedule that is simultaneously cheap and safe is a genuine agent-to-agent
coordination pattern, and it maps exactly onto the business tension in the brief.
Every hop emits an OpenTelemetry span.

**Evidence.** `.../milp.py` · `services/knowledge-orchestrator/.../handoff.py`
(`execute_handoff()`, `HandoffOutcome`, `RULConstraint`) · `.../tools.py` ·
`POST /v1/energy/recommendations/{id}:approve` · Energy Optimization ›
**Load-Shift Simulator**.

**Caveat.** In the demo the handoff counterparties are in-process deterministic
scorers; the cross-service HTTP hop is not exercised.

### `AI-03` — GenAI knowledge-capture structuring expertise into a searchable library

The full chain: consent → speech-to-text → grounded extraction → **critic** →
human review → approved, searchable procedure.

- **Reflection.** `run_reflection_loop()` runs extract → critique → revise. The
  critic checks that every claim carries a citation to retrieved source text and
  that no step is unsafe, then returns `APPROVE` or `REVISE` with reasons.
  Revision is capped at two iterations and **every iteration is written to the
  hash-chained audit log**, so the reflection can be shown happening on screen
  rather than asserted.
- **Grounded retrieval.** Hybrid lexical + cosine retrieval over approved
  procedures only, with citation enforcement and an explicit decline path: if
  nothing grounds the answer, the system says so instead of improvising.
- **Evaluation.** An offline scorecard measures injection resistance, grounding,
  citation compliance and safe-prompt behaviour against fixtures.

**Evidence.** `.../critic.py` (`DeterministicCritic`, `LLMCritic`,
`run_reflection_loop()`, `MAX_CRITIC_ITERATIONS = 2`) · `.../retrieval.py` ·
`.../grounding.py` · `.../evaluation.py` · `.../orchestrator.py` ·
Knowledge Hub › **Procedures**, **Capture Status**.

**Caveat.** In offline demo mode the extraction and critic adapters are local
deterministic stand-ins. The Azure AI Foundry adapter is wired but requires a
deployed model and passage of the manual Agent Service validation gate
(`foundryAgentServiceManuallyValidated` in `main.bicep`).

---

## 6. Where the reference IDs appear in the application

| Screen | Reference IDs stamped |
|---|---|
| Furnace Health › Lining Forecast | `CHL-03` `OBJ-02` `OUT-03` `AI-01` |
| Energy Optimization › Spot & Schedule | `CHL-01` `OBJ-01` `AI-02` |
| Quality › Batch Quality | `CHL-04` `OBJ-03` `OUT-04` |
| Sustainability › Emissions Ledger | `CHL-02` `OUT-02` |
| Sustainability › ETS Exposure | `REG-03` |
| Sustainability › Audit & Reports | `REG-01` `REG-02` |
| Knowledge Hub › Procedures | `CHL-05` `OBJ-04` `AI-03` |
| Executive Overview › Target vs actual | `OUT-01` `OUT-02` `OUT-03` `OUT-04` |
| **Proof of Execution › Requirement Register** | all 19 |

Each badge is a clickable chip: it navigates to the Proof of Execution register,
where the full evidence and caveat for that ID are shown, with a deep link back
to the proving screen. The loop closes in both directions.

---

## 7. Supporting platform evidence

These are not use-case requirements, but they are what makes the claims above
verifiable rather than asserted.

| Area | Evidence |
|---|---|
| **Fabric as the core** | Medallion lakehouse (`00_bronze.sql`, `10_silver.sql`, `20_gold.sql`), notebooks `ns-bronze-to-silver`, `ns-silver-to-gold`, `ns-validate-data-quality`; Eventstream + Eventhouse + KQL database; RTI activator rules; F2 capacity with a nightly 01:00 pause Logic App and GUI-initiated resume |
| **Observability** | `configure_azure_monitor()` in every service; W3C trace context carrying `novasteel.correlation_id`; five business custom metrics; JSON log formatter |
| **Alerting** | 10 `scheduledQueryRules` + an action group in `infra/bicep/modules/alerts.bicep` — including model drift on `novasteel.rul.confidence` and dispatch-without-approval |
| **Audit** | SHA-256 hash-chained, redacting, `verify()`-able append-only log in `services/bff-api/src/bff_api/audit.py` |
| **Residency** | `@allowed(['swedencentral', 'westeurope'])` in `main.bicep`; Sweden Central primary, West Europe the only approved EU contingency |
| **Supply chain** | `NuGet.Config` and pip configured to `packagefeedproxy.microsoft.io` only; `verify_protected_feeds.py` gate; SBOM generation |
| **Validation** | `tools/validation/Validate-Repository.ps1` — 20 gates covering contracts, backend, knowledge workflow, frontend lint/test/build, portal build, vulnerability gates, infra, Fabric assets and security scan |

---

## 8. Anticipated jury questions

| Question | Answer |
|---|---|
| *"Is the −22 % CO₂ measured?"* | No. It is a target derived from the synthetic baseline ratio. Load-shifting alone contributes single digits; the rest of the brief's ambition depends on grid-mix and scrap-ratio measures outside this platform. `OUT-02` says so. |
| *"Show me the physics."* | OLS regression on refractory thickness and heat flux with slope-standard-error propagated into P10/P50/P90, plus apparent thermal resistance as a feature. Not Arrhenius — and we do not claim it. `AI-01`. |
| *"Which model do you call?"* | The Foundry adapter is wired; the demo runs deterministic local adapters so the demonstration is reproducible offline. The gate is explicit in `main.bicep`. `AI-03`. |
| *"Where is the multi-agent coordination?"* | A critic/reflection loop capped at two iterations, and a dispatch → scoring handoff that returns a constraint and forces a re-plan. Both audited. `AI-02`, `AI-03`. |
| *"Can an agent change the plant?"* | No. `FORBIDDEN_TOOL_NAMES` makes approve/publish/commit/schedule/delete unreachable, and a Sev-1 alert fires if an execution ever lacks a matching approval. `REG-02`. |
| *"What about CBAM?"* | Not implemented. ETS is. `REG-03` states this. |
| *"Show me your alerts."* | Ten `scheduledQueryRules` in Bicep, including model drift on a custom metric this solution actually emits. |

---

## 9. Cross-references

- Use-case brief — [`docs/usecase/usecase.md`](../usecase/usecase.md)
- Machine-readable register — [`apps/analytics-mfe/src/proof/proofCatalog.ts`](../../apps/analytics-mfe/src/proof/proofCatalog.ts)
- In-app page — **Proof of Execution** (`/{site}/proof-of-execution/requirements`)
- Slide plan — [`docs/presentation/archives/oral-defense-and-slide-plan.md`](archives/oral-defense-and-slide-plan.md)
- FAQ — [`docs/presentation/faq.md`](faq.md)
- French executive summary — [`docs/presentation/resume-executif-fr.md`](resume-executif-fr.md)
