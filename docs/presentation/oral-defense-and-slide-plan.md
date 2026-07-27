# NovaSteel — Oral Defense and Slide Plan

> **Status:** Authoritative presentation plan v1.0
> **Date:** 2026-07-25
> **Owning workstream:** `delivery-pack`
> **Companion artifacts:** [solution-architecture.md](../architecture/solution-architecture.md) · [deployment-topology.md](../architecture/deployment-topology.md) · [demo-runbook.md](../demo/demo-runbook.md) · [faq.md](faq.md)
> **Delivered deck:** [`NovaSteel-Oral-Defense.pptx`](NovaSteel-Oral-Defense.pptx)
> is the validated 26-slide defense deck (20 primary slides plus six FAQ
> backups). This document remains the authoritative script, storyboard, and
> speaker-note companion.

## 0. How to use this document

This is the presenter's authoritative script for a **60-minute oral defense**:

| Segment | Duration | Running clock | Artifact |
|---|---|---|---|
| **Slides** | 30 min | 00:00 → 30:00 | §2 slide-by-slide plan (20 slides) |
| **Live demo** | 15 min | 30:00 → 45:00 | [demo-runbook.md](../demo/demo-runbook.md), handoff in §3 |
| **FAQ** | 15 min | 45:00 → 60:00 | [faq.md](faq.md), moderation in §5 |

**The single most important discipline in this defense:** every number is labeled as either **DEMONSTRATION EVIDENCE** (a deterministic synthetic-scenario result you can reproduce on screen) or a **PROJECTED BUSINESS OUTCOME / TARGET** (a transformation goal that is *not* proven by the demo). The four headline targets — **14% energy reduction, 22% CO₂ reduction, 21-day lining warning, 8% high-grade-yield improvement** — are **targets**. What the audience sees live is **synthetic scenario evidence** that the platform mechanics work end to end. Never let those two categories blur. A single overclaim will cost more credibility than any missing feature.

Legend used throughout:

- 🎯 **TARGET** = projected business outcome (from the use case / requirements), not demonstrated today.
- 🔬 **EVIDENCE** = reproducible synthetic-scenario result shown in the demo.
- 🛈 **SOURCE CUE** = where the claim is grounded (document/ADR) if challenged.
- ⛑ **FALLBACK** = what to do if a live element fails on this slide.

---

## 1. Narrative arc and design principles

**Arc (executive → technical → proof):** Business pain → measurable ambition → one governed platform → *why Microsoft Fabric is the center of gravity* → how data becomes trustworthy → what the AI actually does → how we keep it safe, legal, and honest → see it live → defend it.

**Design principles for the deck:**

1. **One idea per slide.** Executives read the title and the single hero visual; technical reviewers read the notes.
2. **Fabric is the spine, not a logo.** Return to the same architecture diagram (progressive reveal) so the audience never loses the map.
3. **Targets vs. evidence are color-coded on every slide** that carries a number (e.g., amber chip for 🎯 TARGET, blue chip for 🔬 EVIDENCE).
4. **Every AI output on a slide shows its uncertainty and its human approver.** No lonely point estimates.
5. **The demo is the payoff, not a tangent.** Slides 12–15 pre-load exactly what the demo will show, so the demo confirms rather than introduces.

**Timing envelope:** 20 content slides total **29:45** of speech with **~15 s** of built-in buffer to land the demo handoff exactly at **30:00**. Rehearsal checkpoints (§4) are at **10:00, 18:00, 26:00, 30:00**.

---

## 2. Slide-by-slide plan (30 minutes, 20 slides)

### Slide 1 — Title & framing
- **Duration:** 0:45 · **Running clock:** 00:00 → 00:45
- **Purpose:** Set identity, scope, and the honesty contract before any claim is made.
- **Visual:** NovaSteel wordmark over a muted blast-furnace image; a persistent footer chip that will appear on *every* slide: **"Phase 0 · Synthetic demonstration · Not for operational control."**
- **On-slide content:**
  - NovaSteel — AI-Powered Steel Production Optimization Platform
  - Phase 0 oral defense · Microsoft Fabric–centered architecture
  - Presenter name/role · date
- **Speaker notes:** "Good morning. In the next hour I'll defend the NovaSteel platform: 30 minutes of architecture and value, a 15-minute live demonstration on fully synthetic data, and 15 minutes for your hardest questions. One ground rule I'll repeat: I will always tell you whether a number is a **target** we're aiming for or **evidence** you're watching us reproduce. Today's demo proves the mechanics on synthetic data — it does not claim realized savings."
- 🛈 **SOURCE CUE:** solution-architecture.md §1.1 (non-negotiable boundaries); demo-runbook.md §1.
- ⛑ **FALLBACK:** none needed; static slide.

### Slide 2 — The business challenge
- **Duration:** 1:30 · **Running clock:** 00:45 → 02:15
- **Purpose:** Ground the room in a real, painful, quantified problem so the rest is obviously worth solving.
- **Visual:** Map of four countries (Luxembourg HQ, Germany, Belgium, Spain) with a "single integrated steel producer" caption; four pain icons.
- **On-slide content:**
  - Luxembourg-based integrated producer · blast furnaces + rolling mills · 4 countries
  - Energy = **35% of production cost**, no real-time optimization
  - CO₂ under EU ETS penalty pressure
  - Furnace lining failures ≈ **€8M per event**, unpredictable
  - Automotive-grade quality inconsistency
  - Skilled operators retiring → tacit knowledge lost
  - Regulatory context: GDPR · EU AI Act · sector EU directives
- **Speaker notes:** "AxelorMetal runs blast furnaces and rolling mills across four EU countries. Four structural problems: energy is thirty-five percent of cost with no real-time lever; carbon is now a hard financial cost under the EU Emissions Trading System; a furnace-lining failure costs around eight million euros per event and today is effectively unpredictable; and the experts who *know* the furnace are retiring faster than we can capture what they know. This is a heavy-industry, safety-sensitive, EU-regulated context — which shapes every architectural choice that follows."
- 🛈 **SOURCE CUE:** usecase.md (Business Challenge); personas-and-journeys.md (Energy Manager: "Energy is 35% of our cost base"; Reliability: "An €8M failure…").
- ⛑ **FALLBACK:** none; static.

### Slide 3 — The cost of standing still
- **Duration:** 1:15 · **Running clock:** 02:15 → 03:30
- **Purpose:** Convert pain into urgency for the executive sponsors and the CFO.
- **Visual:** A simple "exposure" bar: energy spend, ETS allowance exposure, one €8M failure, quality claims/downgrades, knowledge-attrition risk. No fake totals — labeled as illustrative exposure categories.
- **On-slide content:**
  - Reactive management = paying the maximum on every axis
  - One unpredicted reline ≈ €8M + unplanned outage
  - Carbon cost "becoming as material as energy cost" (Sustainability Officer)
  - Knowledge attrition is irreversible — retiring experts don't come back
- **Speaker notes:** "Doing nothing isn't neutral — it's the most expensive option. Every axis compounds: energy bought at peak, carbon paid at penalty, failures paid at eight million a time, and knowledge lost permanently. I'm deliberately *not* putting a single made-up 'total savings' number here — you'll see me refuse round numbers all morning. The point is direction and materiality, which the board already feels."
- 🛈 **SOURCE CUE:** personas-and-journeys.md (Sustainability Officer, Executive journeys); usecase.md.
- ⛑ **FALLBACK:** none; static.

### Slide 4 — Transformation objective & the four targets
- **Duration:** 1:30 · **Running clock:** 03:30 → 05:00
- **Purpose:** State the ambition precisely and label it honestly as target, not proof.
- **Visual:** Four target cards, each stamped 🎯 **TARGET**, with the baseline assumption shown beneath.
- **On-slide content:**
  - 🎯 **−14%** energy per ton (baseline ~19.5 GJ/t → ~16.8 GJ/t) · `KPI-ENE-01`
  - 🎯 **−22%** CO₂ per ton (baseline ~2.10 t/t → ~1.64 t/t) · `KPI-CO2-01`
  - 🎯 **≥21-day** furnace-lining advance warning · `KPI-FUR-01`
  - 🎯 **+8%** high-grade yield (baseline ~90% → ~97%) · `KPI-QUA-01`
  - Acceptance for energy recommendations targeted **≥70%**
- **Speaker notes:** "These four numbers are our contract with the business — and they are **targets**, each tied to a stated baseline so they're falsifiable, not marketing. Fourteen percent less energy per ton, twenty-two percent less CO₂ per ton, at least twenty-one days of warning before a lining failure, and eight percent more high-grade yield. Notice I'm showing the *baseline* under each; a percentage without a baseline is a slogan. Today's demo will show the platform *producing* these kinds of outputs on synthetic data — not that we've banked them."
- 🛈 **SOURCE CUE:** solution-requirements.md §4.1–4.2, §13 (KPI baselines); usecase.md (Expected Outcomes).
- ⛑ **FALLBACK:** none; static.

### Slide 5 — Solution overview: one governed platform
- **Duration:** 1:30 · **Running clock:** 05:00 → 06:30
- **Purpose:** Give the whole answer in one breath before decomposing it.
- **Visual:** A single ring diagram: live plant signals → Fabric data core → four AI capabilities → persona experiences → human decisions → audited outcomes. Fabric at the center.
- **On-slide content:**
  - One Microsoft Fabric core unifies production, energy, emissions, quality, maintenance & operator knowledge
  - Four AI capabilities: lining RUL · energy dispatch · quality risk · knowledge capture
  - Persona dashboards for 8 roles, EU-hosted, audited end to end
  - **Decision support** — a human approves; the platform never actuates equipment
- **Speaker notes:** "Here is the entire platform in one picture. Live plant signals flow into a single Microsoft Fabric data core. On top of that governed core sit four AI capabilities. Those feed persona-specific experiences for eight roles. A human always makes the consequential decision, and every decision is audited. The center of gravity is Fabric — I'll spend real time defending *why* that's the right center, because it's the question this room should press hardest on."
- 🛈 **SOURCE CUE:** solution-architecture.md §3 (target architecture), §1.
- ⛑ **FALLBACK:** none; static.

### Slide 6 — Non-negotiable guardrails
- **Duration:** 1:30 · **Running clock:** 06:30 → 08:00
- **Purpose:** Pre-empt the safety, control, and residency objections early, in the executive frame, so the rest of the talk inherits that trust.
- **Visual:** Five "lock" chips.
- **On-slide content:**
  - 1. **Decision support, not a control system** — no write to PLC, interlock, furnace, or setpoint
  - 2. **Phase 0 is synthetic-only** — isolated `NS-DEMO-*`; never shares a table, path, or credential with production
  - 3. **EU-only processing** — Sweden Central primary; Foundry Data Zone (EU)
  - 4. **Every consequential AI output is append-only auditable** — inputs, version, confidence, rationale, human decision, outcome
  - 5. **No standing secrets** — Entra managed identities everywhere
- **Speaker notes:** "Five guardrails are non-negotiable and they constrain everything else. First and most important: this is decision *support*. No application, agent, rule, pipeline, or demo control writes to a PLC, a safety interlock, a furnace, or a production setpoint — existing OT safety systems stay authoritative. Second, Phase 0 is one-hundred-percent synthetic and physically isolated from production. Third, EU-only processing. Fourth, every consequential AI output is auditable end to end. Fifth, no standing secrets — Entra managed identities throughout. If any of these is a problem for you, stop me now, because I won't trade them away."
- 🛈 **SOURCE CUE:** solution-architecture.md §1.1, ADR-007, ADR-008; security-governance-and-threat-model.md (OT boundary, no standing secrets).
- ⛑ **FALLBACK:** none; static.

### Slide 7 — Who benefits: personas & journeys
- **Duration:** 1:30 · **Running clock:** 08:00 → 09:30
- **Purpose:** Make the value human and multi-stakeholder; set up the demo's tab-by-tab structure.
- **Visual:** Eight persona tiles, each with one job-to-be-done and the demo cockpit they map to.
- **On-slide content:**
  - Plant Manager → Site Command Center · Executive → Value & ROI Cockpit
  - Reliability Engineer → Furnace Lining RUL · Furnace Operator → Health Monitor + Knowledge
  - Energy Manager → Dispatch Optimization · Sustainability Officer → ETS Cockpit
  - Quality Engineer → In-line Quality · Knowledge Engineer/Admin → GenAI Capture Studio
- **Speaker notes:** "The platform serves eight roles, not one. The Plant Manager wants everything on one page she can defend. The Reliability Engineer wants an €8M failure turned into a planned intervention. The Energy Manager wants to move flexible load off price peaks. The Quality Engineer wants to catch drift before it ships and prove genealogy heat-by-heat. The Sustainability Officer owns the twenty-two-percent carbon target and ETS exposure. The Knowledge Engineer wants a retiring expert's judgment captured before it's gone. In the demo I'll walk these as tabs, in the order a real operating day would touch them."
- 🛈 **SOURCE CUE:** personas-and-journeys.md §2–11 (persona→dashboard map); demo-runbook.md §2 (tabs).
- ⛑ **FALLBACK:** none; static.

### Slide 8 — Architecture at a glance
- **Duration:** 2:00 · **Running clock:** 09:30 → 11:30
- **Purpose:** Present the reference architecture as the map the rest of the deck annotates.
- **Visual:** The solution-architecture §3 flowchart, simplified into four bands: **Sites (OT/DMZ) → Azure ingress (Event Hubs + relay) → Microsoft Fabric core → AI & application services → Browser experience**. Everything EU/Sweden Central.
- **On-slide content:**
  - Per-plant OT gateway in an industrial DMZ (Purdue L3.5) — outbound only
  - Azure Event Hubs buffer → managed-identity relay → Fabric Eventstream (Entra ID, **no SAS**)
  - Fabric: Eventstream → Eventhouse/KQL + OneLake Lakehouses → Direct Lake → Power BI · Activator (notify only)
  - Python FastAPI BFF + workers · Microsoft Foundry (EU Data Zone) + Azure Speech
  - Blazor WASM C# shell + React/TS (MUI/D3) microfrontend
- **Speaker notes:** "This is the whole system on one slide; I'll return to it three times. Read it left to right. At each site, a gateway in an industrial DMZ terminates OT protocols and only ever emits outbound, schema-validated telemetry — no cloud system ever reaches down into the plant. Azure Event Hubs buffers, a managed-identity relay publishes to Fabric's Eventstream over Entra ID with no shared key, and from there Fabric is the core: hot data in KQL, governed history in OneLake, one Direct Lake semantic model, Power BI, and Activator strictly for notifications. Around it: Python services do the math, Foundry and Speech handle language, and the browser is a Blazor shell hosting a React analytics microfrontend. Hold this map; the next slide explains why Fabric is deliberately at the center."
- 🛈 **SOURCE CUE:** solution-architecture.md §3, §3.1; deployment-topology.md §3.
- ⛑ **FALLBACK:** none; static (this diagram also serves as the demo's Fabric-Core backup image).

### Slide 9 — Why Microsoft Fabric is the center of gravity
- **Duration:** 2:00 · **Running clock:** 11:30 → 13:30
- **Purpose:** Defend the central architectural bet — this is the slide the panel will probe.
- **Visual:** Fabric "one core, many workloads" diagram: RTI (Eventstream/Eventhouse) for hot, OneLake/Lakehouse for governed history, Direct Lake for one semantic truth, Power BI for reporting — with a callout "one governed copy, one lineage."
- **On-slide content:**
  - **Real-Time Intelligence** (Eventstream + Eventhouse/KQL) for hot telemetry, alarms, freshness
  - **OneLake / Lakehouse** bronze→silver→gold as the governed historical, ML & KPI substrate
  - **Direct Lake** semantic model = one KPI definition, no data copy
  - **Power BI + Activator** for reporting and notification (not control)
  - ADR-001: Fabric is the analytics core; **no parallel data lake or BI store**
  - ADR-002: hot KQL is separated from governed Delta — right store for the right question
- **Speaker notes:** "Why bet the platform on Fabric? Because heavy-industry analytics has two clocks: a one-second operational clock and a governed-history clock. Fabric handles both in one governed estate. Real-Time Intelligence — Eventstream into an Eventhouse KQL database — gives us hot telemetry, alarms, and freshness for operational awareness. OneLake with bronze-silver-gold Delta gives us immutable lineage, the training substrate, and stable KPI definitions. Direct Lake means one semantic model reads that gold data with no extra copy — so 'high-grade yield' means exactly one thing everywhere. We consciously chose *not* to build a parallel lake or a second BI stack — that's ADR-001 — and we deliberately keep hot KQL separate from governed Delta, ADR-002, so we always answer a question from the right store. Azure services exist only for the integration, APIs, and domain compute Fabric doesn't provide."
- 🛈 **SOURCE CUE:** solution-architecture.md §3.1, ADR-001, ADR-002; fabric-platform.md; deployment-topology.md §4.
- **Anticipated objection (rehearse aloud):** *"Why not Databricks / Snowflake / a custom lake?"* → "Those can store data; none give us this single governed estate spanning sub-second RTI, OneLake lineage, one Direct Lake semantic layer, and native Power BI without stitching and copying. Fewer copies, fewer trust boundaries, one lineage graph for audit."
- ⛑ **FALLBACK:** none; static.

### Slide 10 — From OT signal to trustworthy data
- **Duration:** 1:45 · **Running clock:** 13:30 → 15:15
- **Purpose:** Prove the data is honest — ingestion, identity, and quarantine — because the whole credibility rests here.
- **Visual:** The §4.1 sequence: gateway → Event Hubs → relay → Eventstream → KQL + bronze → silver (dedup/normalize) → gold. Highlight the quarantine branch.
- **On-slide content:**
  - Immutable bronze envelope: UUIDv7 `event_id`, event-time, sequence, source, schema version, classification
  - **Silver is the single dedup/normalize contract** — streaming & batch converge
  - Late, duplicate, invalid-unit, unknown-asset events are **quarantined, never silently repaired**
  - Ingress isolated in `NS-<env>-RTI-Ingress` workspace (narrow blast radius)
  - **No SAS key** — managed-identity relay to a Custom Endpoint (ADR-005)
- **Speaker notes:** "Trust starts at ingestion. Every event arrives in an immutable bronze envelope with a UUIDv7 id, its original event time, a per-source sequence, and a schema version. Silver is the *single* place we deduplicate and normalize units, so streaming and batch land on the same contract. Crucially, bad data is *visible*: late, duplicate, wrong-unit, or unknown-asset records are quarantined with a reason, never quietly fixed. On identity: Fabric's Event Hubs connector historically uses a shared key, which our security policy forbids — so we buffer in Event Hubs and use a managed-identity relay to a Custom Endpoint over Entra ID. The one wider permission that requires — workspace Contributor for the publisher — is isolated in an ingress-only workspace with no access to curated, ML, or reporting data. That's ADR-005."
- 🛈 **SOURCE CUE:** solution-architecture.md §4.1, §3.2–3.3, ADR-005; deployment-topology.md §3.1; synthetic-data-and-simulators.md §4.1 (envelope).
- **Anticipated objection:** *"Contributor is too broad."* → "Agreed it's wider than ideal; it's the documented Custom-Endpoint requirement, fully isolated in an ingress-only workspace, and flagged to re-evaluate when Fabric ships a narrower publisher role."
- ⛑ **FALLBACK:** none; static (doubles as demo Fabric-Core lineage backup).

### Slide 11 — The four AI capabilities
- **Duration:** 1:00 · **Running clock:** 15:15 → 16:15
- **Purpose:** Transition from platform to intelligence; set the frame that Python computes and Foundry explains.
- **Visual:** Four columns (Lining RUL · Energy Dispatch · Quality Risk · Knowledge Capture), each with input → model → human-approved output.
- **On-slide content:**
  - Lining RUL — physics-informed Python model, daily scoring
  - Energy dispatch — deterministic Python optimizer (constraint-aware)
  - Quality risk — Python model over genealogy features
  - Knowledge capture — Azure Speech + Foundry Agent Service
  - **ADR-006:** Python is authoritative for math; **Foundry explains/retrieves, it does not decide or commit**
- **Speaker notes:** "Four capabilities, one principle that I'll defend hard: the deterministic, testable Python services compute the answer — remaining useful life, feasible dispatch, quality risk. The generative agent explains, retrieves, and orchestrates approved tool calls; it never invents a schedule, relaxes a constraint, or makes a commitment. That's ADR-006, and it's why a language model being confidently wrong can't hurt a furnace here."
- 🛈 **SOURCE CUE:** solution-architecture.md §4.2, ADR-006.
- ⛑ **FALLBACK:** none; static.

### Slide 12 — Deep dive: furnace lining remaining-useful-life
- **Duration:** 2:00 · **Running clock:** 16:15 → 18:15
- **Purpose:** Show the flagship safety-adjacent capability and pre-load the demo's centerpiece.
- **Visual:** Hearth thermal map with sector 07 warming; a P10/P50/P90 RUL fan chart; a driver bar (heat-flux slope, spatial contrast, cooling residual).
- **On-slide content:**
  - Physics-informed model on silver thermal/cooling features → feature snapshot → RUL
  - 🔬 **EVIDENCE (synthetic scenario):** P50 **~20 d** (19.65), P10 **18.69**, P90 **20.61**, risk **0.90**, confidence **0.78**, `HIGH`
  - Explains itself: heat-flux 6h slope, spatial temperature contrast, cooling-efficiency residual
  - Advisory only → acknowledge → **linked CMMS work order** → no furnace actuation
  - Pilot scoring is **daily**; near-real-time is a measured later enhancement, not an MVP claim
- **Speaker notes:** "This is the capability that turns an eight-million-euro surprise into a planned intervention. The model is physics-informed — it isn't a black box fitting noise; it's constrained by heat-flux and cooling physics. On our synthetic warning scenario it estimates a P50 remaining life of about twenty days with a tight band — P10 about nineteen, P90 about twenty-one — and it explains itself with three drivers. The model confidence is zero-point-seven-eight from an r-squared of zero-point-eight-eight. The engineer stays accountable: they acknowledge the alert and it links to a CMMS work order recommending inspection and ultrasound. The platform does not touch the furnace. And note the honesty: pilot scoring is daily; I'm not promising real-time inference as an MVP feature."
- 🛈 **SOURCE CUE:** solution-architecture.md §4.2; demo-runbook.md §5 (cue: P50 19.65/P10 18.69/P90 20.61/risk 0.8995); solution-requirements.md FR-FUR; synthetic-data-and-simulators.md §8.1.
- **Anticipated objection:** *"Is 21 days validated?"* → "The measured P50 on this scenario is about twenty days — close to the target, not exactly it. Twenty-one days as a fleet-wide guarantee is the target requiring pilot validation across many relines. The model gives an actionable advance warning in the right order of magnitude and, critically, with a confidence estimate."
- ⛑ **FALLBACK:** none on slide; the *demo* equivalent falls back to saved alert JSON (ensure risk ≥ 0.80, confidence ≥ 0.70, P50 ≈ 19.65).

### Slide 13 — Deep dive: energy dispatch optimization
- **Duration:** 1:30 · **Running clock:** 18:15 → 19:45
- **Purpose:** Show the clearest ROI story and the constraint-safety discipline.
- **Visual:** Day-ahead price curve with an evening scarcity peak; baseline vs optimized Gantt; a savings/constraint panel.
- **On-slide content:**
  - Inputs: day-ahead price + grid carbon intensity + production/maintenance constraints
  - Deterministic optimizer moves **only eligible flexible loads**; preserves soak times, delivery, capacity, planned tonnage
  - 🔬 **EVIDENCE (synthetic):** 280 EUR/MWh peak → **7.25%** modeled energy-cost cut, **7.89%** lower peak (56.0→51.58 MW), **3.29%** CO₂ reduction, **equal tonnage (960 t)**, zero hard-constraint violations
  - Human accepts / modifies / **rejects with reason code**; realized savings tracked in an auditable ledger
- **Speaker notes:** "Energy is the fastest payback. Tomorrow evening has a scarcity peak at two-hundred-eighty euros a megawatt-hour. The optimizer shifts one eligible reheat batch by a hundred-and-twenty minutes — the urgent automotive coil stays fixed — and it never silently relaxes a hard production constraint. On this synthetic horizon that's a seven-point-two-five-percent modeled energy-cost reduction, a seven-point-nine-percent peak reduction from fifty-six to fifty-one-point-six megawatts, and three-point-three-percent CO₂ reduction — all on the whole-dispatch basis with identical planned tonnage at nine-sixty tonnes and zero hard-constraint violations. Those are single-scenario evidence, not banked savings — realized savings are tracked separately in an auditable ledger, which is how the fourteen-percent annual target eventually gets *proven* rather than asserted."
- 🛈 **SOURCE CUE:** solution-architecture.md §4.2; demo-runbook.md §5; solution-requirements.md FR-ENE; synthetic-data-and-simulators.md §8.2.
- ⛑ **FALLBACK:** demo reveals cached feasible result after ≤5 s; never leave a solver spinner visible.

### Slide 14 — Deep dive: in-line quality prediction
- **Duration:** 1:15 · **Running clock:** 19:45 → 21:00
- **Purpose:** Show yield/traceability value and the "no automatic recipe write" boundary.
- **Visual:** Coil genealogy tree (heat→slab→coil) + a drift panel (coiling temperature & force balance drifting together) + predicted-vs-measured toggle.
- **On-slide content:**
  - Predicts likelihood of meeting automotive-grade spec **before the first lab result**
  - Full genealogy: heat → slab → coil → sample → shipment (OEM traceability, "heat by heat")
  - 🔬 **EVIDENCE (synthetic what-if):** bounded setpoint correction → predicted first-pass yield **~88% → ~95%**
  - **No automatic recipe/setpoint write** — what-if recommendation only
- **Speaker notes:** "Quality value is twofold: catch drift early, and prove traceability. Here coiling temperature and force balance drift together before any off-spec lab result, and the model traces the affected heat, slab, and coil. A bounded what-if correction lifts predicted first-pass yield from about eighty-eight to ninety-five percent on this synthetic coil — roughly the eight-percent relative target — *without* changing the grade recipe. That distinction matters: this is a what-if recommendation, not an automatic write-back to process control."
- 🛈 **SOURCE CUE:** solution-architecture.md §4.2; demo-runbook.md §5; solution-requirements.md FR-QUA; synthetic-data-and-simulators.md §8.3.
- ⛑ **FALLBACK:** demo uses cached what-if result; never imply automatic control write-back.

### Slide 15 — Deep dive: GenAI knowledge capture
- **Duration:** 1:30 · **Running clock:** 21:00 → 22:30
- **Purpose:** Show the "capture retiring expertise" capability and its privacy/consent discipline.
- **Visual:** Interview → Azure Speech transcript (speaker + confidence) → extracted fact card (trigger / observation / recommended check / rationale / safety boundary / citations) → DRAFT status.
- **On-slide content:**
  - Consent-aware Speech **Fast Transcription** → transcript → Foundry draft procedure
  - Structured as **trigger → action → rationale → risk**, with **source citations**
  - **Human expert approval required before publication** — draft never becomes an operational instruction
  - Fictional synthetic persona (e.g., `OP-DEMO-014`); consent, retention & deletion enforced
- **Speaker notes:** "The final capability preserves judgment before it retires. A consented interview is transcribed with speaker separation, and the Foundry agent drafts a structured procedure — trigger, observation, recommended check, rationale, safety boundary — every claim cited to a transcript segment. Then the guardrail: it stays a DRAFT until a human expert approves it. An unreviewed draft is never an operational instruction. In the demo the operator is a fictional synthetic persona, consent is explicit, and raw audio is Highly Confidential with a retention and deletion workflow. This is where generative AI adds real value *and* where it's most tightly governed."
- 🛈 **SOURCE CUE:** solution-architecture.md §4.2–4.3; demo-runbook.md §7; azure-ai-regions.md (Fast Transcription); security doc (consent, 30-day audio retention).
- ⛑ **FALLBACK:** demo plays approved WAV; if audio fails, paste approved transcript ("replay mode").

### Slide 16 — Responsible AI & EU AI Act governance
- **Duration:** 2:00 · **Running clock:** 22:30 → 24:30
- **Purpose:** Defend AI governance head-on — the compliance and risk reviewers live here.
- **Visual:** Governance stack: EU AI Act classification → RAI review board → human-in-the-loop → auditable evidence; plus a prompt-injection defense mini-stack.
- **On-slide content:**
  - Conservative **high-risk-adjacent** posture pending legal EU AI Act classification; knowledge system has transparency obligations
  - If classified high-risk: risk management, technical documentation & logging, **human oversight**, accuracy/robustness/cybersecurity, conformity assessment
  - **Responsible AI review board** (Data Scientist, Compliance/DPO, OT/ICS, Maintenance) sign-off gate before production
  - Prompt-injection defense: **Prompt Shields** (direct + indirect), untrusted-content separation, **tool allow-lists**, full tool-call audit, human approval
  - Every consequential output: inputs, model version, confidence, rationale, human decision, outcome — append-only
- **Speaker notes:** "We adopt a conservative high-risk-adjacent posture while Legal and Compliance determine the formal EU AI Act classification. The knowledge system is at minimum under transparency obligations. If a capability is classified high-risk, we apply the full control set — risk management, technical documentation and logging, human oversight, robustness and cybersecurity, and conformity assessment. Nothing reaches production without a cross-functional Responsible AI board sign-off that includes the DPO and an OT engineer. On the generative side specifically: we treat every retrieved document and market payload as *untrusted* — Prompt Shields for direct and indirect injection, instructions separated from data, narrow tool allow-lists, full tool-call logging, and human approval on any write. A model response is never authorization."
- 🛈 **SOURCE CUE:** security-governance-and-threat-model.md §12 (Prompt Shields), §15 (RAI board), §16.2 (AI Act classification gate); solution-architecture.md §8.2, ADR-006/007.
- **Anticipated objection:** *"Isn't an LLM in the loop inherently risky?"* → "It would be if it decided. It doesn't. Python decides; the LLM explains within an allow-listed, audited, human-approved envelope."
- ⛑ **FALLBACK:** none; static.

### Slide 17 — Security, identity & EU data residency
- **Duration:** 1:45 · **Running clock:** 24:30 → 26:15
- **Purpose:** Defend the security posture and residency, closing the CISO/DPO objections.
- **Visual:** Zero-Trust identity matrix (human, per-plant gateway MI, relay MI, BFF MI, worker MI, Foundry agent identity, capacity MI, GitHub OIDC) + a "no standing secrets" and "EU-only" banner.
- **On-slide content:**
  - **No standing secrets** — Entra managed identities; four separate authorization planes (Azure RBAC ≠ Fabric roles ≠ Foundry RBAC ≠ app roles)
  - Least privilege: per-plant gateway identity, ingress relay scoped, browser never gets a workload token
  - Data classes: Synthetic-nonpersonal · Confidential operational · **Highly Confidential** interview audio/transcript · Audit evidence
  - Residency: Fabric, Event Hubs, apps, Foundry, Speech in **Sweden Central**; Foundry **Data Zone (EU)**
  - Supply chain: **protected feeds only** (no public PyPI/NuGet), **SBOM**, **GitHub OIDC** deploy; breach notification **72 h**; audit **1 yr hot + 6 yr archive**
- **Speaker notes:** "Security is Zero-Trust and least-privilege by construction. There are no standing secrets — every workload uses its own Entra managed identity, and I want to stress that Azure RBAC, Fabric workspace roles, Foundry RBAC, and application roles are four *separate* planes: holding one grants nothing in another. The per-plant gateway can produce to its own Event Hub and nothing else. The browser never receives a workload credential. Data is classified, and operator audio is Highly Confidential with DLP and deletion workflows. Everything processes in the EU — Sweden Central primary, Foundry in the EU Data Zone. The software supply chain is locked to Microsoft-protected feeds — public PyPI and NuGet are unreachable — every build emits an SBOM, and deployment uses GitHub OIDC, not secrets."
- 🛈 **SOURCE CUE:** solution-architecture.md §8.1–8.2, ADR-003; deployment-topology.md §2.3; security doc §1/§3/§6/§16/§19/§20.
- ⛑ **FALLBACK:** none; static.

### Slide 18 — Synthetic data & OT realism
- **Duration:** 1:30 · **Running clock:** 26:15 → 27:45
- **Purpose:** Pre-empt "it's just fake data" — show determinism, physics, and honest boundaries.
- **Visual:** Simulator pipeline: signed manifest (root seed) → process/truth-ledger simulation → contract+physics+scenario validator → publish/replay; named-scenario chips.
- **On-slide content:**
  - Deterministic: root seed **240725**; child seeds via `SHA-256(root|scenario|plant|asset|signal)`; generator `novasteel-sim/1.0.0`
  - **Physics-first:** process state simulated, then sensors observe it; mass/energy balance, lining thickness monotonic (except reline), RUL ≥ 0
  - **Truth ledger** holds hidden state, injected anomalies, expected KPI outcomes
  - Named scenarios: 21-day warning (`240726`), evening spike (`240727`), quality drift (`240728`), outage/recovery (`240729`)
  - 4 synthetic plants (LUX/DE/BE/ES); every record `SYNTHETIC` / `DEMO-NONPERSONAL`
- **Speaker notes:** "You should push on 'it's synthetic.' Here's why it's credible synthetic. It's deterministic — one root seed, child seeds hashed per signal — so any result I show you regenerates bit-for-bit. It's physics-*first*: we simulate the true process state and then let modeled sensors observe it, so signals can't contradict each other, and physical invariants are enforced — lining thickness can't spontaneously increase, remaining life can't go negative, energy and mass must balance. A truth ledger records the hidden state and the anomalies we inject, so we can score predictions against ground truth. These are exactly the properties real OT data lacks and that let us defend the *mechanics* honestly without touching a real furnace."
- 🛈 **SOURCE CUE:** synthetic-data-and-simulators.md §1, §4.1, §6.1–6.2, §8, §9.2; solution-architecture.md §4.1.1.
- ⛑ **FALLBACK:** none; static.

### Slide 19 — Deployment, capacity, cost & scale
- **Duration:** 1:30 · **Running clock:** 27:45 → 29:15
- **Purpose:** Close the CFO/operations loop: how it runs, what it costs, how it grows.
- **Visual:** Phase ladder (Phase 0 defense → Phase 1 one-site pilot → Phase 2+ four-site production) + capacity lifecycle chip (F2→F4, pause/resume).
- **On-slide content:**
  - Capacity: **F2** demo baseline; **F4** only on measured contention; **not F64** merely for viewer licensing (consumers on Pro/PPU/trial)
  - Cost control: 01:00 Europe/Luxembourg Logic App **pause** check (non-prod only); ARM `2023-11-01` suspend/resume (202 async); production **never auto-paused**
  - Scale: same event/API contract for **4 countries**; per-plant relay & measured capacity
  - Phases: Phase 0 synthetic → Phase 1 shadow-scoring pilot (read-only) → Phase 2+ human-approved write-back after gates
  - Region posture: Sweden Central primary; West Europe = **tested** EU contingency, not automatic failover
- **Speaker notes:** "How does it run and what does it cost? We start on the smallest Fabric SKU, F2, and only move to F4 if measured contention demands it — we do *not* buy the big F64 tier just to give viewers free licenses; consumers sit on Pro or PPU. Cost is actively controlled: a nightly one-a.m. Logic App safely pauses non-production capacity using the official ARM suspend operation, and production is *never* auto-paused. Scaling to four countries is a capacity and per-plant-relay decision, not a redesign — the event and API contracts are stable. And we phase it honestly: today synthetic; then a one-site shadow pilot that only *reads*; then, only after DPO, OT, security, and RAI gates, human-approved write-back. I'm deliberately not quoting a euro-per-hour price — it's region-, currency-, and offer-specific, and I won't invent it."
- 🛈 **SOURCE CUE:** deployment-topology.md §2.1, §4.1, §5, §6; solution-architecture.md §1.2, ADR-003; fabric-platform.md (F SKUs, pause/resume).
- **Anticipated objection:** *"What will production cost?"* → "A sizing decision after pilot load measurement, not an assumed architecture fact. I can give the cost *drivers* and controls today; a credible euro figure needs measured CU consumption."
- ⛑ **FALLBACK:** none; static.

### Slide 20 — What you'll see next (demo handoff)
- **Duration:** 0:30 · **Running clock:** 29:15 → 29:45 *(→ 30:00 buffer)*
- **Purpose:** Transition cleanly into the 15-minute live demo with expectations set.
- **Visual:** The seven demo tabs in order + a big "Synthetic demo data — not for operational control" banner + a 15:00 timer icon.
- **On-slide content:**
  - Live, deterministic, synthetic — seed `240725`, accelerated 60× clock
  - You'll watch: fleet → Fabric core → energy dispatch → lining alert → quality → knowledge → sustainability/audit → recap
  - Everything reproducible; every screen labeled synthetic
- **Speaker notes:** "Now I'll show it live. Everything is synthetic and deterministic — seed two-four-oh-seven-two-five, an accelerated clock so forty-five days compress into seconds. I'll move through seven tabs in the order an operating day touches them, and I'll call out target versus evidence as we go. If anything hesitates, I'll switch to a cached deterministic result rather than debug in front of you — that's a rehearsed choice, not a failure. Fifteen minutes, starting now." *(Start the 15:00 timer; switch to Plant Manager tab.)*
- 🛈 **SOURCE CUE:** demo-runbook.md §3.3, §4.
- ⛑ **FALLBACK:** if the live environment is already known-degraded, open on the cached fleet-overview screenshot and narrate from the fallback pack (§3 below).

---

## 3. Demo handoff script (30:00 → 45:00)

The demo is executed strictly per [demo-runbook.md](../demo/demo-runbook.md) §4 (minute-by-minute). This section is the **presenter's bridge language and the slide↔demo contract** — what each slide promised and where the demo confirms it.

### 3.1 Entry checklist (say nothing until all true)
- Control status reads `history=loaded`, `stream=paused`, `alert=armed`, `fallbacks=ready` (runbook §3.3).
- Every tab shows the synthetic banner; freshness is green.
- The visible 15:00 presenter timer is started.
- Presenter and reset operator have agreed the hand signal for switching to fallback.

### 3.2 Bridge lines (slide promise → demo proof)
| Demo minute (runbook §4) | Tab / action | Bridge line connecting to the slides |
|---|---|---|
| 00:00–02:00 | Plant Manager → Fabric Core | "Slide 8's map, now live: one fleet view, and behind it the Fabric core with bronze-silver-gold lineage from Slide 10." |
| 02:00–04:30 | Demo Control → Energy Manager | "We're accelerating *time*, not fabricating UI. Slide 13: only eligible loads move; seven-point-two-five-percent modeled cost cut; peak down from fifty-six to fifty-one-point-six megawatts; tonnage conserved; zero hard-constraint violations; no production schedule write." |
| 04:30–07:00 | Reliability Engineer → RUL alert and synthetic work order | "This is Slide 12 live. Watch the band: P50 about twenty days, P10 nineteen, P90 twenty-one — a tight, confident prediction. Advisory only; no furnace actuation." |
| 07:00–09:30 | Quality Engineer → what-if | "Slide 14: genealogy heat-by-heat, predicted yield eighty-eight to ninety-five percent, no recipe write-back." |
| 09:30–12:00 | Operator Knowledge | "Slide 15: consented synthetic interview, cited draft, stays DRAFT until a human approves." |
| 12:00–14:00 | Plant Manager / Sustainability / Executive → ETS, ROI, audit | "The targets are not banked savings; this is the semantic-model and audit evidence that makes them measurable." |
| 14:00–15:00 | Plant Manager → Fabric Core recap | "Back to one core: targets are 14/22/21/8; what you just saw is synthetic scenario *evidence* the mechanics work." |

### 3.3 Backup / fallback transitions during the demo
Use the runbook's binding fallback ladder — **live cloud → local deterministic replay → cached interactive → recorded flow → static proof pack** — and **never diagnose for more than 10 seconds** on screen (runbook §6, §8). Spoken bridges (memorize):
- No live events → "I'll switch to our deterministic replay so we keep the same event sequence."
- Model endpoint slow → "For a predictable demo we cache the signed result from this exact seed." (Ensure risk ≥ 0.80 and confidence ≥ 0.70.)
- Optimizer infeasible → "The platform never relaxes hard production constraints silently — here's the known feasible result and its constraint table."
- STT fails → "We support offline replay; the review workflow is unchanged." (Play WAV, else paste approved transcript.)
- Value out of expected band → stop the stream, load the manifest result: "The live run differs from the rehearsed seed, so I'm switching to the validated scenario."
- Network fully lost → fallback levels 2–5; "The edge buffers data and preserves event time; here's the offline path."
- **Never** expose stack traces, tokens, tenant details, or production-like settings on the projector.

### 3.4 Return from demo (45:00)
One sentence to close and pivot to FAQ: *"That's the platform end to end on synthetic data. The four headline numbers remain targets we intend to prove in a one-site pilot; what you just saw is reproducible evidence that the data core, the models, the governance, and the human-approval flow all work together. Now — your hardest questions."*

---

## 4. Rehearsal checkpoints

Rehearse against these hard gates; if a checkpoint slips by more than ~30 s, cut depth (not honesty) from the next section.

| Checkpoint | Target clock | Must be true | Recovery if behind |
|---|---|---|---|
| **CP-1** end of Slide 7 | **09:30** | Business case, targets, guardrails, personas all landed | Compress Slide 3 and Slide 7 to titles + one line each |
| **CP-2** end of Slide 11 | **16:15** | Architecture, Fabric-centrality, ingestion, "Python decides/Foundry explains" landed | Merge Slides 10 narration into Slide 9; keep the quarantine point |
| **CP-3** end of Slide 15 | **22:30** | All four AI deep-dives done with target-vs-evidence labels intact | Shorten Quality (14) and Knowledge (15) to the guardrail line each |
| **CP-4** end of Slide 19 | **29:15** | RAI, security/residency, synthetic realism, cost/scale defended | Collapse Slide 18 to the determinism + physics bullet only |
| **CP-5** demo handoff | **30:00** | Timer started, Plant Manager tab up, entry checklist green | If env degraded, open on cached fleet screenshot and narrate fallback |
| **CP-6** demo end | **45:00** | Recap sentence delivered; target-vs-evidence restated | Stop at 45:00 regardless; do not debug live |
| **CP-7** FAQ close | **60:00** | ≥ 8–10 questions answered; unknowns logged as follow-ups | Offer written follow-up for anything requiring measurement |

**Full-run rehearsal requirements (from runbook §3.1):** rehearse once online and once with the network disabled; verify two consecutive clean 15-minute demo runs; confirm the presenter can finish the entire story offline.

---

## 5. FAQ segment moderation (45:00 → 60:00)

- Work from [faq.md](faq.md); it is organized by theme (business value, Fabric centrality, architecture alternatives, capacity/cost, regions/residency, AI governance, security, OT realism, synthetic data, models, deployment, scalability, limitations).
- **Answer discipline (same contract as the slides):** name whether the answer is EVIDENCE or TARGET; cite the owning document/ADR; if you don't know, say "that's a validation gate, not a claim" and log it as a written follow-up rather than inventing a number.
- Reserve the **Limitations** answers for skeptics — leading with candor (daily-not-real-time scoring, Custom-Endpoint Contributor scope, no automatic BCDR, no production cost figure yet) buys credibility for the confident answers.
- Time-box each answer to ~60–90 s; park deep dives for after.

---

## 6. Evidence & source ledger (for the whole defense)

| Claim family | Grounding document | Notes on target vs evidence |
|---|---|---|
| Four headline outcomes (14/22/21/8) | usecase.md; solution-requirements.md §4, §13 | Always **TARGET**; baselines quoted make them falsifiable |
| Fabric-centered architecture, ADRs | solution-architecture.md §3, §10 | Architecture facts |
| Ingestion, identity, quarantine | solution-architecture.md §4.1, ADR-005; deployment-topology.md §3 | Architecture facts |
| Live scenario numbers (RUL ~20/18.7/20.6, energy 7.25%, CO₂ 3.29%, peak 7.89%, quality 88→95%) | demo-runbook.md §5; synthetic-data-and-simulators.md §8 | Always **EVIDENCE** (synthetic, reproducible) |
| RAI / EU AI Act / Prompt Shields | security-governance-and-threat-model.md §12, §15, §16 | Governance posture |
| Security / identity / residency | solution-architecture.md §8; deployment-topology.md §2; security doc §1/§3/§6/§16/§19/§20 | Architecture + policy |
| Synthetic determinism & physics | synthetic-data-and-simulators.md §1/§4/§6/§9 | Method credibility |
| Capacity / cost / pause-resume / scale | deployment-topology.md §4/§5/§6; fabric-platform.md | No euro price is asserted |
| Regions / Foundry Data Zone / Speech | azure-ai-regions.md; solution-architecture.md ADR-003 | Validation gates flagged |

**Golden rule, repeated because it is the whole game:** the demo proves the *mechanics* on synthetic data; the four headline numbers are *targets* a one-site pilot must prove. Never merge the two.
