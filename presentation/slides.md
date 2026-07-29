---
marp: true
theme: novasteel
paginate: true
header: 'NovaSteel · AI-Powered Steel Production Optimization'
footer: 'Phase 0 · Synthetic demonstration · Not for operational control.'
---

<!-- _class: lead -->
<!-- _paginate: false -->

<div class="tag">Phase 0 · Oral Defense</div>

# NovaSteel — AI-Powered <span class="grad">Steel Production</span> Optimization

<div class="hero-line"></div>

Microsoft Fabric–centered architecture · AxelorMetal · 4 EU countries

<div class="herostats">
<div class="s"><b>−14%</b><span>energy per ton · target</span></div>
<div class="s"><b>−22%</b><span>CO₂ per ton · target</span></div>
<div class="s"><b>≥21 d</b><span>lining advance warning · target</span></div>
<div class="s"><b>+8%</b><span>high-grade yield · target</span></div>
</div>

<!-- ⏱ 0:45 · Good morning.
In the next hour I'll defend the NovaSteel platform: thirty minutes of architecture and value, a fifteen-minute live demonstration on fully synthetic data, and fifteen minutes for your hardest questions.
One ground rule I'll repeat throughout: I will always tell you whether a number is a target we're aiming for or evidence you're watching us reproduce.
Today's demo proves the mechanics on synthetic data — it does not claim realized savings. -->

---

# The Business Challenge

<div class="split">
<div>

- Luxembourg-based integrated producer
- Blast furnaces + rolling mills · **4 countries**
- Regulatory: GDPR · EU AI Act · EU ETS

</div>
<div>

<div class="cards">
<div class="card orange"><div class="card-num">35%</div><h3>Energy cost share</h3><p>No real-time optimization lever</p></div>
<div class="card teal"><div class="card-num">€8M</div><h3>Lining failure</h3><p>Per event, unpredictable today</p></div>
<div class="card purple"><div class="card-num">CO₂</div><h3>ETS penalty pressure</h3><p>Carbon as material as energy</p></div>
<div class="card green"><div class="card-num">Knowledge</div><h3>Operator attrition</h3><p>Retiring experts, irreversible loss</p></div>
</div>

</div>
</div>

<!-- ⏱ 1:30 · AxelorMetal runs blast furnaces and rolling mills across four EU countries.
Four structural problems: energy is thirty-five percent of production cost with no real-time lever; carbon is now a hard financial cost under the EU Emissions Trading System; a furnace-lining failure costs around eight million euros per event and today is effectively unpredictable; and the experts who know the furnace are retiring faster than we can capture what they know.
This is a heavy-industry, safety-sensitive, EU-regulated context — which shapes every architectural choice that follows. -->

---

# The Cost of Standing Still

<div class="split">
<div>

- Reactive management = paying the maximum on every axis
- One unpredicted reline ≈ **€8M** + unplanned outage
- Carbon cost "becoming as material as energy cost"
- Knowledge attrition is **irreversible**

</div>
<div>

<div class="stat"><div class="big">€8M</div><div class="label">single lining failure event</div></div>

> Doing nothing isn't neutral — it's the most expensive option.

</div>
</div>

<!-- ⏱ 1:15 · Doing nothing isn't neutral — it's the most expensive option.
Every axis compounds: energy bought at peak, carbon paid at penalty, failures paid at eight million a time, and knowledge lost permanently.
I'm deliberately not putting a single made-up total savings number here — you'll see me refuse round numbers all morning.
The point is direction and materiality, which the board already feels. -->

---

# Transformation Objectives

<div class="cards four">
<div class="card teal"><div class="card-num">KPI-ENE-01</div><h3>−14% energy/ton</h3><p>~19.5 → ~16.8 GJ/t</p></div>
<div class="card green"><div class="card-num">KPI-CO2-01</div><h3>−22% CO₂/ton</h3><p>~2.10 → ~1.64 t/t</p></div>
<div class="card orange"><div class="card-num">KPI-FUR-01</div><h3>≥21-day warning</h3><p>Furnace lining advance notice</p></div>
<div class="card purple"><div class="card-num">KPI-QUA-01</div><h3>+8% high-grade yield</h3><p>~90% → ~97%</p></div>
</div>

<span class="pill orange">🎯 TARGET</span> All four numbers are targets tied to stated baselines — not proven today

<!-- ⏱ 1:30 · These four numbers are our contract with the business — and they are targets, each tied to a stated baseline so they're falsifiable, not marketing.
Fourteen percent less energy per ton, twenty-two percent less CO₂ per ton, at least twenty-one days of warning before a lining failure, and eight percent more high-grade yield.
Notice I'm showing the baseline under each; a percentage without a baseline is a slogan.
Today's demo will show the platform producing these kinds of outputs on synthetic data — not that we've banked them. -->

---

# One Governed Platform

<div class="split">
<div>

- One **Microsoft Fabric** core unifies production, energy, emissions, quality, maintenance & knowledge
- Four AI capabilities: lining RUL · energy dispatch · quality risk · knowledge capture
- Persona dashboards for **8 roles**, EU-hosted, audited end to end
- **Decision support** — a human approves; the platform never actuates equipment

</div>
<div>

![w:560](images/executive-overview.png)

</div>
</div>

<!-- ⏱ 1:30 · Here is the entire platform in one picture.
Live plant signals flow into a single Microsoft Fabric data core. On top of that governed core sit four AI capabilities. Those feed persona-specific experiences for eight roles. A human always makes the consequential decision, and every decision is audited.
The center of gravity is Fabric — I'll spend real time defending why that's the right center, because it's the question this room should press hardest on. -->

---

# Non-Negotiable Guardrails

<div class="cards">
<div class="card teal"><div class="card-num">01</div><h3>Decision support only</h3><p>No write to PLC, interlock, furnace, or setpoint</p></div>
<div class="card orange"><div class="card-num">02</div><h3>Synthetic-only Phase 0</h3><p>Isolated NS-DEMO-*; no production path</p></div>
<div class="card purple"><div class="card-num">03</div><h3>EU-only processing</h3><p>Sweden Central; Foundry Data Zone (EU)</p></div>
</div>

- **04** Every consequential AI output is append-only auditable
- **05** No standing secrets — Entra managed identities everywhere

<!-- ⏱ 1:30 · Five guardrails are non-negotiable and they constrain everything else.
First and most important: this is decision support. No application, agent, rule, pipeline, or demo control writes to a PLC, a safety interlock, a furnace, or a production setpoint — existing OT safety systems stay authoritative.
Second, Phase 0 is one-hundred-percent synthetic and physically isolated from production.
Third, EU-only processing. Fourth, every consequential AI output is auditable end to end.
Fifth, no standing secrets — Entra managed identities throughout.
If any of these is a problem for you, stop me now, because I won't trade them away. -->

---

# Who Benefits: Personas & Journeys

| Persona | Dashboard | Key job-to-be-done |
|---|---|---|
| Plant Manager | Site Command Center | Single-page operational truth |
| Reliability Engineer | Furnace Lining RUL | €8M failure → planned intervention |
| Energy Manager | Dispatch Optimization | Move flexible load off price peaks |
| Quality Engineer | In-line Quality | Catch drift before it ships |
| Sustainability Officer | ETS Cockpit | Own the −22% carbon target |
| Knowledge Engineer | GenAI Capture Studio | Preserve retiring expertise |
| Executive | Value & ROI Cockpit | Board-level KPI visibility |
| Furnace Operator | Health Monitor + Knowledge | Daily decision context |

<!-- ⏱ 1:30 · The platform serves eight roles, not one.
The Plant Manager wants everything on one page she can defend. The Reliability Engineer wants an eight-million-euro failure turned into a planned intervention. The Energy Manager wants to move flexible load off price peaks. The Quality Engineer wants to catch drift before it ships and prove genealogy heat-by-heat.
The Sustainability Officer owns the twenty-two-percent carbon target and ETS exposure. The Knowledge Engineer wants a retiring expert's judgment captured before it's gone.
In the demo I'll walk these as tabs, in the order a real operating day would touch them. -->

---

<!-- _class: tight -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Architecture at a Glance

![w:960](images/command-center-overview.png)

| Layer | Components |
|---|---|
| Sites (OT/DMZ) | Per-plant gateway, Purdue L3.5, outbound only |
| Azure ingress | Event Hubs buffer → managed-identity relay (no SAS) |
| Fabric core | Eventstream → Eventhouse/KQL + OneLake Lakehouse → Direct Lake → Power BI |
| AI & app services | Python FastAPI BFF + workers · Foundry (EU) + Speech |
| Experience | Blazor WASM C# shell + React/TS (MUI/D3) microfrontend |

<!-- ⏱ 2:00 · This is the whole system on one slide; I'll return to it three times.
Read it left to right. At each site, a gateway in an industrial DMZ terminates OT protocols and only ever emits outbound, schema-validated telemetry — no cloud system ever reaches down into the plant.
Azure Event Hubs buffers, a managed-identity relay publishes to Fabric's Eventstream over Entra ID with no shared key. From there Fabric is the core: hot data in KQL, governed history in OneLake, one Direct Lake semantic model, Power BI, and Activator strictly for notifications.
Around it: Python services do the math, Foundry and Speech handle language, and the browser is a Blazor shell hosting a React analytics microfrontend. -->

---

# Why Microsoft Fabric Is the Center of Gravity

<div class="split">
<div>

- **Real-Time Intelligence** — Eventstream + Eventhouse/KQL for hot telemetry
- **OneLake / Lakehouse** — bronze→silver→gold governed history & ML
- **Direct Lake** — one semantic model, no data copy
- **Power BI + Activator** — reporting & notification (not control)

</div>
<div>

- ADR-001: Fabric is the analytics core; **no parallel data lake**
- ADR-002: hot KQL separated from governed Delta

> One governed estate, two clocks: operational and historical.

</div>
</div>

<!-- ⏱ 2:00 · Why bet the platform on Fabric? Because heavy-industry analytics has two clocks: a one-second operational clock and a governed-history clock. Fabric handles both in one governed estate.
Real-Time Intelligence — Eventstream into an Eventhouse KQL database — gives us hot telemetry, alarms, and freshness. OneLake with bronze-silver-gold Delta gives us immutable lineage, the training substrate, and stable KPI definitions.
Direct Lake means one semantic model reads gold data with no extra copy — so high-grade yield means exactly one thing everywhere.
We consciously chose not to build a parallel lake or a second BI stack — that's ADR-001 — and we keep hot KQL separate from governed Delta, ADR-002, so we always answer from the right store.
Azure services exist only for integration, APIs, and domain compute Fabric doesn't provide. -->

---

# From OT Signal to Trustworthy Data

<div class="split">
<div>

- Immutable **bronze envelope**: UUIDv7, event-time, sequence, schema version
- **Silver** = single dedup/normalize contract
- Late, duplicate, invalid events are **quarantined, never silently repaired**
- Ingress isolated in `NS-<env>-RTI-Ingress` workspace

</div>
<div>

- **No SAS key** — managed-identity relay to Custom Endpoint (ADR-005)
- Contributor scope isolated to ingress-only workspace
- Streaming & batch converge on the same silver contract

<span class="pill blue">🔬 EVIDENCE</span> Quarantine visible in demo

</div>
</div>

<!-- ⏱ 1:45 · Trust starts at ingestion. Every event arrives in an immutable bronze envelope with a UUIDv7 id, its original event time, a per-source sequence, and a schema version.
Silver is the single place we deduplicate and normalize units, so streaming and batch land on the same contract. Crucially, bad data is visible: late, duplicate, wrong-unit, or unknown-asset records are quarantined with a reason, never quietly fixed.
On identity: Fabric's Event Hubs connector uses a shared key, which our security policy forbids — so we buffer in Event Hubs and use a managed-identity relay to a Custom Endpoint over Entra ID. The wider permission — workspace Contributor — is isolated in an ingress-only workspace with no access to curated, ML, or reporting data. That's ADR-005. -->

---

# The Four AI Capabilities

<div class="cards four">
<div class="card teal"><div class="card-num">RUL</div><h3>Lining RUL</h3><p>Physics-informed Python model, daily scoring</p></div>
<div class="card orange"><div class="card-num">ENERGY</div><h3>Energy Dispatch</h3><p>Deterministic Python optimizer, constraint-aware</p></div>
<div class="card purple"><div class="card-num">QUALITY</div><h3>Quality Risk</h3><p>Python model over genealogy features</p></div>
<div class="card green"><div class="card-num">KNOWLEDGE</div><h3>Knowledge Capture</h3><p>Azure Speech + Foundry Agent Service</p></div>
</div>

**ADR-006:** Python is authoritative for math · Foundry explains/retrieves, never decides or commits

<!-- ⏱ 1:00 · Four capabilities, one principle that I'll defend hard: the deterministic, testable Python services compute the answer — remaining useful life, feasible dispatch, quality risk.
The generative agent explains, retrieves, and orchestrates approved tool calls; it never invents a schedule, relaxes a constraint, or makes a commitment.
That's ADR-006, and it's why a language model being confidently wrong can't hurt a furnace here. -->

---

<!-- _class: tight -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Deep Dive: Furnace Lining Remaining Useful Life

![w:960](images/furnace-health-lining-forecast.png)

<div class="split right-wide">
<div>

- Physics-informed model on silver thermal/cooling features
- Drivers: heat-flux slope, spatial contrast, cooling residual
- Advisory only → acknowledge → CMMS work order

</div>
<div>

| Metric | Value |
|---|---|
| P50 RUL | ~20 d (19.65) |
| P10 / P90 | 18.69 / 20.61 |
| Risk score | 0.90 |
| Confidence | 0.78 |
| Rating | `HIGH` |

<span class="pill blue">🔬 EVIDENCE</span> Synthetic scenario result

</div>
</div>

<!-- ⏱ 2:00 · This is the capability that turns an eight-million-euro surprise into a planned intervention.
The model is physics-informed — constrained by heat-flux and cooling physics, not a black box fitting noise. On our synthetic warning scenario it estimates a P50 remaining life of about twenty days with a tight band — P10 about nineteen, P90 about twenty-one — and it explains itself with three drivers.
The model confidence is zero-point-seven-eight from an r-squared of zero-point-eight-eight. The engineer stays accountable: they acknowledge the alert and it links to a CMMS work order recommending inspection.
The platform does not touch the furnace. And note the honesty: pilot scoring is daily; I'm not promising real-time inference as an MVP feature. -->

---

<!-- _class: tight -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Deep Dive: Energy Dispatch Optimization

![w:960](images/energy-optimization-spot-price-schedule.png)

<div class="split right-wide">
<div>

- Day-ahead price + grid carbon + production constraints
- Moves **only eligible flexible loads**
- Human accepts / modifies / rejects with reason code

</div>
<div>

| Metric | Value |
|---|---|
| Energy-cost cut | **7.25%** |
| Peak reduction | 56.0 → 51.58 MW (−7.89%) |
| CO₂ reduction | **3.29%** |
| Planned tonnage | 960 t (unchanged) |
| Constraint violations | **Zero** |

<span class="pill blue">🔬 EVIDENCE</span> Single synthetic scenario

</div>
</div>

<!-- ⏱ 1:30 · Energy is the fastest payback. Tomorrow evening has a scarcity peak at two-hundred-eighty euros per megawatt-hour.
The optimizer shifts one eligible reheat batch — the urgent automotive coil stays fixed — and never silently relaxes a hard production constraint.
On this synthetic horizon that's a seven-point-two-five-percent modeled energy-cost reduction, peak down from fifty-six to fifty-one-point-six megawatts, three-point-three-percent CO₂ reduction — all on the whole-dispatch basis with identical planned tonnage at nine-sixty tonnes and zero hard-constraint violations.
Those are single-scenario evidence, not banked savings — realized savings are tracked separately in an auditable ledger, which is how the fourteen-percent annual target eventually gets proven rather than asserted. -->

---

<!-- _class: tight -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Deep Dive: In-line Quality Prediction

![w:960](images/quality-spc.png)

<div class="split">
<div>

- Predicts meeting automotive-grade spec **before first lab result**
- Full genealogy: heat → slab → coil → sample → shipment
- **No automatic recipe/setpoint write** — what-if only

</div>
<div>

<div class="stat"><div class="big">~88% → ~95%</div><div class="label">predicted first-pass yield after bounded correction</div></div>

<span class="pill blue">🔬 EVIDENCE</span> Synthetic what-if scenario
<span class="pill orange">🎯 TARGET</span> +8% yield fleet-wide

</div>
</div>

<!-- ⏱ 1:15 · Quality value is twofold: catch drift early, and prove traceability.
Here coiling temperature and force balance drift together before any off-spec lab result, and the model traces the affected heat, slab, and coil. A bounded what-if correction lifts predicted first-pass yield from about eighty-eight to ninety-five percent on this synthetic coil — roughly the eight-percent relative target — without changing the grade recipe.
That distinction matters: this is a what-if recommendation, not an automatic write-back to process control. -->

---

<!-- _class: tight -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Deep Dive: GenAI Knowledge Capture

![w:960](images/knowledge-hub-capture-status.png)

<div class="split">
<div>

- Consent-aware Speech **Fast Transcription**
- Foundry drafts structured procedure:
  trigger → action → rationale → risk
- **Source citations** to transcript segments

</div>
<div>

- **Human expert approval** required before publication
- Draft never becomes operational instruction unsupervised
- Synthetic persona (`OP-DEMO-014`)
- Highly Confidential; retention & deletion enforced

<span class="pill green">GOVERNED</span> Consent · DLP · 30-day audio retention

</div>
</div>

<!-- ⏱ 1:30 · The final capability preserves judgment before it retires.
A consented interview is transcribed with speaker separation, and the Foundry agent drafts a structured procedure — trigger, observation, recommended check, rationale, safety boundary — every claim cited to a transcript segment.
Then the guardrail: it stays a DRAFT until a human expert approves it. An unreviewed draft is never an operational instruction.
In the demo the operator is a fictional synthetic persona, consent is explicit, and raw audio is Highly Confidential with a retention and deletion workflow.
This is where generative AI adds real value and where it's most tightly governed. -->

---

# Responsible AI & EU AI Act Governance

<div class="split">
<div>

- Conservative **high-risk-adjacent** posture pending legal classification
- Knowledge system: transparency obligations
- **RAI review board** (Data Scientist, DPO, OT/ICS, Maintenance) — mandatory sign-off gate

</div>
<div>

- Prompt-injection defense: **Prompt Shields** (direct + indirect), tool allow-lists, full audit
- Every output: inputs, model version, confidence, rationale, human decision, outcome — **append-only**
- ADR-006: LLM explains; **Python decides**

</div>
</div>

> A model response is never authorization.

<!-- ⏱ 2:00 · We adopt a conservative high-risk-adjacent posture while Legal determines the formal EU AI Act classification. The knowledge system is at minimum under transparency obligations.
If a capability is classified high-risk, we apply the full control set — risk management, documentation, human oversight, robustness, and conformity assessment. Nothing reaches production without a cross-functional Responsible AI board sign-off.
On the generative side: we treat every retrieved document and market payload as untrusted — Prompt Shields for direct and indirect injection, instructions separated from data, narrow tool allow-lists, full tool-call logging, and human approval on any write.
A model response is never authorization. -->

---

# Security, Identity & EU Data Residency

<div class="split">
<div>

- **No standing secrets** — Entra managed identities
- Four separate auth planes: Azure RBAC ≠ Fabric ≠ Foundry ≠ app roles
- Per-plant gateway scoped; browser never gets workload token
- Supply chain: protected feeds only, SBOM, GitHub OIDC

</div>
<div>

| Aspect | Posture |
|---|---|
| Residency | Sweden Central + Data Zone (EU) |
| Breach notification | 72 hours |
| Audit retention | 1 yr hot + 6 yr archive |
| Interview audio | Highly Confidential, 30 d |
| Deploy secrets | None — GitHub OIDC |

</div>
</div>

<!-- ⏱ 1:45 · Security is Zero-Trust and least-privilege by construction.
There are no standing secrets — every workload uses its own Entra managed identity, and Azure RBAC, Fabric roles, Foundry RBAC, and application roles are four separate planes: holding one grants nothing in another.
The per-plant gateway can produce to its own Event Hub and nothing else. The browser never receives a workload credential.
Data is classified, and operator audio is Highly Confidential with DLP and deletion workflows.
Everything processes in the EU — Sweden Central primary, Foundry in the EU Data Zone.
The software supply chain is locked to Microsoft-protected feeds — public PyPI and NuGet are unreachable — every build emits an SBOM, and deployment uses GitHub OIDC, not secrets. -->

---

# Synthetic Data & OT Realism

<div class="split">
<div>

- Deterministic: root seed **240725**
- Child seeds: `SHA-256(root|scenario|plant|asset|signal)`
- Generator: `novasteel-sim/1.0.0`
- **Physics-first:** process state simulated, then sensors observe it

</div>
<div>

- Mass/energy balance enforced; lining thickness monotonic
- **Truth ledger** holds hidden state & injected anomalies
- Named scenarios: warning (`240726`), spike (`240727`), drift (`240728`), outage (`240729`)
- 4 synthetic plants (LUX/DE/BE/ES) · all `SYNTHETIC`

</div>
</div>

<!-- ⏱ 1:30 · You should push on "it's synthetic." Here's why it's credible.
It's deterministic — one root seed, child seeds hashed per signal — so any result I show regenerates bit-for-bit.
It's physics-first: we simulate the true process state and then let modeled sensors observe it, so signals can't contradict each other and physical invariants are enforced — lining thickness can't spontaneously increase, remaining life can't go negative, energy and mass must balance.
A truth ledger records hidden state and the anomalies we inject, so we score predictions against ground truth.
These are exactly the properties real OT data lacks and that let us defend the mechanics honestly without touching a real furnace. -->

---

# Deployment, Capacity, Cost & Scale

<div class="split">
<div>

- Capacity: **F2** baseline; **F4** only on measured contention
- Cost control: 01:00 Logic App pause (non-prod); ARM suspend/resume
- Production **never** auto-paused
- No €/hour claim — needs measured pilot load

</div>
<div>

| Phase | Scope |
|---|---|
| **Phase 0** | Synthetic defense (today) |
| **Phase 1** | One-site shadow pilot (read-only) |
| **Phase 2+** | Human-approved write-back after gates |

- Scale: same event/API contract for **4 countries**
- Region: Sweden Central primary; West Europe = tested contingency

</div>
</div>

<!-- ⏱ 1:30 · How does it run and what does it cost?
We start on the smallest Fabric SKU, F2, and move to F4 only if measured contention demands it — we do not buy F64 just for viewer licensing; consumers sit on Pro or PPU.
Cost is actively controlled: a nightly one-a.m. Logic App safely pauses non-production capacity using the official ARM suspend operation, and production is never auto-paused.
Scaling to four countries is a capacity and per-plant-relay decision, not a redesign — event and API contracts are stable.
We phase it honestly: today synthetic, then a one-site shadow pilot that only reads, then — only after DPO, OT, security, and RAI gates — human-approved write-back.
I'm deliberately not quoting a euro-per-hour price — it's region-specific, and I won't invent it. -->

---

# What You'll See Next

<div class="split">
<div>

- Live, deterministic, synthetic — seed `240725`
- Accelerated 60× clock
- Every screen labeled synthetic
- 15-minute demonstration

</div>
<div>

**Demo sequence:**
1. Fleet overview → Fabric core
2. Energy dispatch optimization
3. Furnace lining RUL alert
4. Quality prediction & genealogy
5. Operator knowledge capture
6. Sustainability / ETS / audit
7. Recap — targets vs. evidence

</div>
</div>

> Targets are 14 / 22 / 21 / 8 — the demo proves the mechanics, not the savings.

<!-- ⏱ 0:30 · Now I'll show it live. Everything is synthetic and deterministic — seed two-four-oh-seven-two-five, an accelerated clock so forty-five days compress into seconds.
I'll move through seven tabs in the order an operating day touches them, and I'll call out target versus evidence as we go.
Fifteen minutes, starting now. -->

---

<!-- _class: tight backup -->

# Backup — Are the headline numbers proven?

<div class="split">
<div>

**Q: Are 14% energy, 22% CO₂, 21-day warning, 8% yield proven?**

No — they are <span class="pill orange">🎯 TARGETS</span>, each tied to a stated baseline so they're falsifiable:

- Energy ~19.5 → 16.8 GJ/t
- CO₂ ~2.10 → 1.64 t/t
- ≥21 days lead time
- High-grade yield ~90% → 97%

</div>
<div>

Today's demo shows the platform *producing* those outputs on synthetic data — <span class="pill blue">🔬 EVIDENCE</span> the mechanics work, not banked savings.

Realized savings get proven in a one-site pilot via an auditable savings ledger.

</div>
</div>

<!-- ⏱ 0:00 · Backup slide. The four headline numbers are targets tied to baselines. Today's demo is evidence the mechanics work on synthetic data; banked savings require a pilot with an auditable ledger. -->

---

<!-- _class: tight backup -->

# Backup — Why Microsoft Fabric, Not Databricks or Snowflake?

<div class="split">
<div>

**Q: Why not Databricks, Snowflake, or a custom data lake?**

Those can store and process data, but none give a *single governed estate* spanning:

- Sub-second RTI (Eventstream/Eventhouse)
- OneLake lineage
- One Direct Lake semantic layer
- Native Power BI

</div>
<div>

Without stitching multiple products or copying data across trust boundaries.

Fewer copies and one lineage graph directly serve audit and EU AI Act obligations.

A parallel lake is explicitly rejected in **ADR-001**.

</div>
</div>

<!-- ⏱ 0:00 · Backup slide. Databricks and Snowflake can store data but don't provide the single governed estate spanning real-time intelligence, OneLake lineage, Direct Lake, and native Power BI without copying across trust boundaries. ADR-001 explicitly rejects a parallel data lake. -->

---

<!-- _class: tight backup -->

# Backup — What Stops a Hallucinating LLM From Causing Harm?

<div class="split">
<div>

**Q: What stops a hallucinating LLM from causing harm?**

Architecture, not hope:

- Python computes every authoritative answer
- LLM only explains, retrieves, calls allow-listed tools (ADR-006)
- Cannot relax a constraint, make a commitment, or be sole calculation

</div>
<div>

- Tools are read/simulate by default
- "Commit" endpoint separately policy-gated
- A model response is **never** authorization
- Full tool-call input/output logging
- Human-in-the-loop for any write action

</div>
</div>

<!-- ⏱ 0:00 · Backup slide. The architecture separates computation from explanation. Python decides; the LLM explains within an allow-listed, audited, human-approved envelope. It cannot relax constraints or make commitments. A model response is never authorization. -->

---

<!-- _class: tight backup -->

# Backup — Where Are the Secrets?

<div class="split">
<div>

**Q: Where are the secrets / connection strings?**

There are **no standing application secrets**.

- Humans: Entra user tokens
- Workloads: separate managed identities
- GitHub: OIDC/workload-identity federation

</div>
<div>

- Public registries prohibited (protected feeds only)
- Every build emits an SBOM
- Breach notification: 72 hours
- Audit logs: 1 year hot + 6 years archive
- Blast radius contained: four separate auth planes

</div>
</div>

<!-- ⏱ 0:00 · Backup slide. No standing secrets exist. Humans use Entra tokens, workloads use managed identities, deployment uses GitHub OIDC federation. Public package registries are blocked; every build produces an SBOM. If one identity is compromised, blast radius is contained across four separate authorization planes. -->

---

<!-- _class: tight backup -->

# Backup — Why We Do Not Write to the Furnace

<div class="split">
<div>

**Q: Isn't advisory-only just a dashboard?**

Not writing is **designed, not missing**:

- Setpoints and interlocks at Purdue L0–L2 under IEC 61511
- Outbound-only IEC 62443 zone boundary
- EU AI Act high-risk duties cannot be evidenced in Phase 0

</div>
<div>

The platform **is not read-only** — it writes decisions:

- `POST /v1/energy/recommendations/{id}:approve`
- `POST /v1/workorders` from lining alert
- `POST /v1/knowledge/procedures/{id}:approve`
- Append-only hash-chained audit trail

Phase 2: guarded write-back to CMMS/MES — human-approved, bounded, reversible.

</div>
</div>

<!-- ⏱ 0:00 · Backup slide. Not writing to the furnace is a designed acceptance boundary, not a missing feature. Existing safety-instrumented functions stay authoritative. The platform does write decisions — approved dispatches, work orders, published procedures, and audit trails. Phase 2 adds guarded CMMS write-back, never direct control. -->

---

<!-- _class: tight backup -->

# Backup — Honest Limitations

<div class="split">
<div>

**Q: What are the honest limitations of today's demo?**

1. All data is **synthetic** — four targets are not realized results
2. Pilot RUL scoring is **daily**, not real-time
3. Custom Endpoint requires **Contributor** role — mitigated by isolation, not eliminated

</div>
<div>

4. **No automatic Fabric BCDR** in Sweden Central
5. **No production €/hour cost** — needs measured pilot load
6. Real-plant accuracy needs pilot validation against actual relines and lab results

> This discipline *is* the trustworthiness.

</div>
</div>

<!-- ⏱ 0:00 · Backup slide. We name limitations unprompted: synthetic-only data, daily not real-time scoring, Contributor role mitigated by isolation, no automatic BCDR, no cost figure, and real accuracy needs pilot validation. This honesty discipline is the trustworthiness — a vendor who converts every synthetic result into banked savings is the one to distrust. -->
