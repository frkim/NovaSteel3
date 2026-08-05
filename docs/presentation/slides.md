---
marp: true
theme: novasteel
paginate: true
header: 'NovaSteel · AI-Powered Steel Production Optimization'
footer: 'AI advises, humans decide'
title: 'NovaSteel · AI-Powered Steel Production Optimization'
---

<!-- _class: lead -->
<!-- _paginate: false -->

<div class="corners">
<img class="bottom-right" src="images/microsoft-logo.png" alt="Microsoft" onerror="this.remove()">
</div>

<div class="tag">Oral Defense</div>

# <span style="color: #fff;">NovaSteel</span> — AI-Powered <span class="grad">Steel Production</span> Optimization

<div class="hero-line"></div>

<div class="brandbar">
<img src="images/novasteel-logo.png" alt="NovaSteel" onerror="this.remove()">
<img src="images/axelormetal-wordmark.png" alt="AxelorMetal" onerror="this.remove()">
</div>

4 EU countries

<div class="herostats">
<div class="s"><b>−14%</b><span>energy per ton · target</span></div>
<div class="s"><b>−22%</b><span>CO₂ per ton · target</span></div>
<div class="s"><b>≥21 d</b><span>lining advance warning · target</span></div>
<div class="s"><b>+8%</b><span>high-grade yield · target</span></div>
</div>

<!-- ⏱ 0:35 · Good morning.
In the next hour I'll defend the NovaSteel platform: thirty-five minutes of architecture and value, a ten-minute live demonstration on fully synthetic data, and fifteen minutes for your questions.
One ground rule I'll repeat throughout: I will always tell you whether a number is a target we're aiming for or evidence you're watching us reproduce.
Today's demo proves the mechanics on synthetic data — it does not claim realized savings. -->

---

<!-- _class: tight agenda -->

# Agenda

<p class="subtitle">From business pressure to governed decisions — then proof in the live experience</p>

<div class="agenda-grid">
<div class="agenda-item orange"><span>01</span><div><b>Business context</b><small>Challenge · objectives · personas</small></div></div>
<div class="agenda-item teal"><span>02</span><div><b>Platform & architecture</b><small>Scope · Fabric · AI flow</small></div></div>
<div class="agenda-item purple"><span>03</span><div><b>Decision intelligence</b><small>Energy · RUL · quality · knowledge</small></div></div>
<div class="agenda-item green"><span>04</span><div><b>Trust & governance</b><small>Security · Responsible AI · compliance</small></div></div>
<div class="agenda-item blue"><span>05</span><div><b>Live demonstration</b><small>Persona journeys · evidence reproduced</small></div></div>
<div class="agenda-item orange"><span>06</span><div><b>Value & next steps</b><small>Targets vs. evidence · roadmap · close</small></div></div>
</div>

<div class="agenda-path"><b>Business need</b><i>›</i><b>governed platform</b><i>›</i><b>human decision</b><i>›</i><b>measurable outcome</b></div>

<!-- ⏱ 0:40 · Here is the route through the defense.
I will start with the business pressure, objectives and the people making the decisions. Then I will show the governed platform and architecture that connect their fragmented information.
We will go deeper into the four decision-intelligence capabilities, the trust and compliance controls around them, and then reproduce the evidence in the live persona journeys.
I will close by separating demonstrated evidence from transformation targets and setting out the roadmap and next steps. -->

---

<!-- _class: lead chapter -->
<!-- _paginate: false -->

<img class="chapter-icon" src="images/icon_business_context.png" alt="" onerror="this.remove()">

<div class="chapter-num">01</div>

# Business context

<p class="chapter-sub">Challenge · objectives · personas</p>

<div class="chapter-path">
<span class="now">01 Business</span>
<span>02 Platform</span>
<span>03 Decision</span>
<span>04 Trust</span>
<span>05 Demo</span>
<span>06 Value</span>
<span>07 Appendix</span>
</div>

<!-- ⏱ 0:08 · Chapter one: the business pressure, the four targets, and the five people making the call. -->

---

<!-- _class: tight -->

# How a Steel Mill Works

![w:760](images/steel-process-routes.webp)

<div class="legend">
<span class="pill orange">Blast furnace route</span> ore, coke and limestone → pig iron → basic oxygen furnace. <span class="pill blue">Electric arc furnace route</span> scrap and DRI melted with electricity. Both converge on ladle refining, casting, rolling and coating.
</div>

<!-- ⏱ 0:55 · Before the architecture, thirty seconds on the process itself, because every design choice hangs off this picture.
AxelorMetal runs both primary routes. The integrated route reduces iron ore, coking coal and limestone in the blast furnace into molten pig iron, which the basic oxygen furnace then decarburises into steel. The electric arc furnace route melts scrap and direct-reduced iron with electricity instead — far less embedded carbon, far more exposure to the hourly power price, which is exactly why energy dispatch matters more on that route.
From ladle refining onward the two routes share one line: continuous casting into slabs, blooms and billets, then hot and cold rolling, galvanizing and coating.
Everything NovaSteel does hangs off four points on this picture — the electricity the furnace pulls, refractory wear inside the furnace, the defect risk introduced at the caster and the mill, and the tacit knowledge that walks out of the gate at shift handover. -->

---

# The Business Challenge

<div class="subtitle">A steel estate under pressure on five fronts</div>


<div class="cards five">
<div class="card orange"><div class="card-num">35%</div><h3>Energy cost share</h3><p>No real-time optimization lever</p></div>
<div class="card teal"><div class="card-num">€8M</div><h3>Lining failure</h3><p>Per event, unpredictable today</p></div>
<div class="card purple"><div class="card-num">CO₂</div><h3>ETS penalty pressure</h3><p>Carbon as material as energy</p></div>
<div class="card green"><div class="card-num">Knowledge</div><h3>Operator attrition</h3><p>Retiring experts, irreversible loss</p></div>
<div class="card blue"><div class="card-num">Yield</div><h3>Grade yield variability</h3><p>Genealogy must be heat-by-heat</p></div>
</div>

</BR>

Regulatory frame: GDPR · EU AI Act · EU ETS

<!-- ⏱ 1:15 · AxelorMetal runs blast furnaces and rolling mills across four EU countries.
Five structural problems: energy is thirty-five percent of production cost with no real-time lever; carbon is now a hard financial cost under the EU Emissions Trading System; a furnace-lining failure costs around eight million euros per event and today is effectively unpredictable; automotive-grade yield swings heat to heat, and the customers who buy that steel expect genealogy traced heat by heat rather than shift by shift; and the experts who know the furnace are retiring faster than we can capture what they know.
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

<div class="stat"><div class="big">€8M (~15 days)</div><div class="label">single lining failure event</div></div>

> Doing nothing isn't neutral — it's the most expensive option.

</div>
</div>

<!-- ⏱ 0:55 · Doing nothing isn't neutral — it's the most expensive option.
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

<!-- ⏱ 1:10 · These four numbers are our contract with the business — and they are targets, each tied to a stated baseline so they're falsifiable, not marketing.
Fourteen percent less energy per ton, twenty-two percent less CO₂ per ton, at least twenty-one days of warning before a lining failure, and eight percent more high-grade yield.
Notice I'm showing the baseline under each; a percentage without a baseline is a slogan.
Today's demo will show the platform producing these kinds of outputs on synthetic data — not that we've banked them. -->

---

# Personas & Journey

<p class="subtitle">Expert people are slowed by fragmented tools, software and data</p>

| Persona | Role | Dashboard | Key job-to-be-done |
|---|---|---|---|
| **Elena Duarte** | Furnace Operator | Health Monitor + Knowledge | Daily decision context at the furnace |
| **Sofia Lindqvist** | Energy Manager | Dispatch Optimization | Move flexible load off price peaks |
| **Jens Bakker** | Quality Engineer | In-line Quality | Catch drift before it ships |
| **Amina Haddad** | Sustainability Officer | ETS Cockpit | Own the −22% carbon target |
| **Pieter Claes** | Knowledge Engineer | GenAI Capture Studio | Preserve retiring expertise |

<div class="persona-friction"><b>Today:</b> each employee brings distinct knowledge and skills, but must reconcile historians, spreadsheets, MES exports and specialist software before acting.</div>

<!-- ⏱ 1:00 · The platform serves people, not job titles — so every persona has a name, and those names are binding across the deck, the portal and the demo.
Elena Duarte runs the furnace on shift and wants the decision context for the next four hours, not a monthly report. Sofia Lindqvist manages energy and wants to move flexible load off price peaks. Jens Bakker owns quality and wants to catch drift before it ships, with genealogy provable heat-by-heat.
Amina Haddad owns the twenty-two-percent carbon target and the ETS exposure. Pieter Claes wants a retiring expert's judgment captured before it walks out of the gate.
Each brings different expertise, but today they lose time moving between historians, spreadsheets, MES exports and specialist applications, manually rebuilding the same context before they can decide. -->

---

<!-- _class: tight employee-agents -->

# An Agent for Every Role — Human Judgment at the Center

<p class="subtitle">Role-specific agents bring governed context into each employee's flow of work — while people retain control</p>

<div class="employee-agent-visual">
<img src="images/employees-with-agents.png" alt="Employees working with role-specific agents">
</div>

<div class="employee-agent-outcomes">
<span><b>Find faster</b><small>Governed data and approved knowledge</small></span>
<span><b>Decide better</b><small>Role-specific risks and recommendations</small></span>
<span><b>Share expertise</b><small>Consistent handoffs across teams</small></span>
<span><b>Stay accountable</b><small>Accept · modify · reject</small></span>
</div>

<!-- ⏱ 0:50 · NovaSteel changes the relationship between employees and their tools.
Instead of asking every person to search across systems and manually assemble context, a role-specific agent brings governed data, approved knowledge, risks and recommendations into the employee's flow of work.
The agent does not replace expertise; it makes that expertise more productive — faster discovery, better-informed decisions and more consistent handoffs between shifts and functions.
The employee remains accountable: they accept, modify or reject. No agent crosses into operational control. -->

---

<!-- _class: lead chapter teal -->
<!-- _paginate: false -->

<img class="chapter-icon" src="images/icon_platform_architecture.png" alt="" onerror="this.remove()">

<div class="chapter-num">02</div>

# Platform & architecture

<p class="chapter-sub">Scope · Fabric · AI flow</p>

<div class="chapter-path">
<span>01 Business</span>
<span class="now">02 Platform</span>
<span>03 Decision</span>
<span>04 Trust</span>
<span>05 Demo</span>
<span>06 Value</span>
<span>07 Appendix</span>
</div>

<!-- ⏱ 0:08 · Chapter two: one governed platform, its scope boundary, and why Fabric is the core. -->

---

<!-- _class: tight -->

# One Governed Platform

<div class="split">
<div>

- One **unified platform** core unifies production, energy, emissions, quality, maintenance & knowledge
- Instead of scattered data and disconnected tools, **one governed place** where the data, the AI and the decision live together
- Four AI capabilities: energy dispatch · lining RUL · quality risk · knowledge capture
- Persona dashboards for **every key role**, EU-hosted, audited end to end
- **Decision support** — a human approves; the platform never actuates equipment

</div>
<div>

![w:430](images/executive-overview.png)

</div>
</div>

<div class="chain">
<div class="node blue"><b>Plant signals</b><span>OT / MES / market</span></div>
<div class="step">›</div>
<div class="node teal"><b>Unified platform</b><span>governed data spine</span></div>
<div class="step">›</div>
<div class="node purple"><b>Four AI capabilities</b><span>Python + constrained GenAI</span></div>
<div class="step">›</div>
<div class="node green"><b>Persona experiences</b><span>role-specific views</span></div>
<div class="step">›</div>
<div class="node orange"><b>Human decision</b><span>approval + audit</span></div>
</div>

<!-- ⏱ 1:15 · Here is the entire platform in one picture.
Live plant signals flow into a single, unified platform core. Today AxelorMetal's data and tooling are scattered across historians, spreadsheets, MES exports and separate BI stacks; the whole point of this slide is that they stop being scattered — one governed place where the data, the AI and the decision live together.
On top of that governed core sit four AI capabilities. Those feed persona-specific experiences. A human always makes the consequential decision, and every decision is audited.
The center of gravity is that unified core — I'll spend real time defending why Microsoft Fabric is the right implementation of it, because it's the question this room should press hardest on. -->

---

<!-- _class: tight scope-boundary -->

# What's In — and What's Out

<p class="subtitle">A governed decision-support solution with a deliberate OT safety boundary</p>

<div class="scope-grid">
<div class="scope-panel in">
<h2>✓ In the solution</h2>

- Microsoft Fabric data spine: plant, energy, emissions, quality, maintenance & knowledge
- Four advisory capabilities: **energy dispatch, lining RUL, quality risk, knowledge capture**
- Persona dashboards, bounded what-if simulations, confidence & explainability
- Human accept / modify / reject gates with model version, correlation ID & audit trail
- EU-hosted processing, consent, content safety, retrieval limited to approved knowledge

</div>
<div class="scope-panel out">
<h2>× What's out of scope</h2>

- **No PLC, interlock, furnace, recipe or production-setpoint control**
- No autonomous schedule, work-order or CMMS commit
- No LLM-only calculation or relaxation of deterministic hard constraints
- No production credentials or shared demo / production storage
- No unapproved transcript or draft procedure as operational instruction

</div>
</div>

<div class="scope-footer"><b>Hard boundary:</b> no recommendation becomes authorization; no application path crosses into OT control</div>

<!-- ⏱ 0:55 · Now that the unified platform is clear, let me make its boundary explicit.
In scope is a governed Fabric data spine, four advisory capabilities, role-specific experiences, bounded simulation, confidence, and a complete human decision trail.
Out of scope is equally important: no path writes to a PLC, interlock, furnace, recipe, production setpoint, schedule, work order, or CMMS. Language models cannot replace the Python calculation or relax a hard constraint, and an unapproved transcript never becomes an instruction.
That boundary is not a future intention; it is an architectural rule: AI advises, humans decide, and the operational systems remain authoritative. -->

---

# Guardrails we will not trade away

<div class="cards four">
<div class="card teal"><div class="card-num">01</div><h3>Decision support only</h3><p>No write to PLC, interlock, furnace, or setpoint (ADR-007)</p></div>
<div class="card purple"><div class="card-num">02</div><h3>EU-only processing</h3><p>Sweden Central; Foundry Data Zone (EU) — ADR-003</p></div>
<div class="card green"><div class="card-num">03</div><h3>Append-only audit</h3><p>Every consequential AI output is replayable</p></div>
<div class="card orange"><div class="card-num">04</div><h3>Secure by design</h3><p>Zero Trust, least privilege, no standing secrets</p></div>
</div>

> Existing OT safety-instrumented systems stay authoritative. The platform advises; a human decides.

<!-- ⏱ 1:30 · Four guardrails are non-negotiable and they constrain everything else.
First and most important: this is decision support. No application, agent, rule, pipeline, or demo control writes to a PLC, a safety interlock, a furnace, or a production setpoint — existing OT safety systems stay authoritative. That is ADR-007.
Second, EU-only processing: Sweden Central, with Foundry in the EU Data Zone.
Third, every consequential AI output is auditable end to end — inputs, model version, confidence, rationale, the human decision, and the outcome, append-only.
Fourth, secure by design: Zero Trust and least privilege throughout, with no standing secret anywhere to steal. Every identity is scoped to exactly one job, so a compromised identity has a contained blast radius.
If any of these is a problem for you, stop me now, because I won't trade them away. -->

---

<!-- _class: tight -->
<!-- _header: '' -->
<!-- _footer: '' -->

# High Level Architecture

<div class="flow">
<div class="lane purple"><div class="lane-tag">AI &amp; app<br>services</div><div class="nodes">
<div class="node purple"><b>Decision Center App</b><span>domain APIs · read-only adapters to KQL + gold</span></div>
<div class="node purple"><b>Scoring / optimizer workers</b><span>MILP dispatch · RUL · quality risk</span></div>
<div class="node purple"><b>Foundry (EU) + Speech</b><span>explain &amp; transcribe · restricted OpenAPI tools</span></div>
</div></div>
<div class="arrow">▲ predictions, recommendations, audit facts ▼ features &amp; labels — never raw OT credentials</div>
<div class="lane teal"><div class="lane-tag">Microsoft Fabric<br>data core</div><div class="nodes">
<div class="node teal"><b>Eventstream</b><span>es-ns-telemetry-v1</span></div>
<div class="node teal"><b>Eventhouse / KQL</b><span>hot telemetry · alarms · Activator notify</span></div>
<div class="node teal"><b>OneLake Lakehouse</b><span>bronze → silver → gold · quarantine</span></div>
<div class="node teal"><b>Direct Lake model</b><span>one semantic layer → Power BI</span></div>
</div></div>
<div class="arrow">▲ Eventstream Custom Endpoint · Entra ID, no shared key</div>
<div class="lane blue"><div class="lane-tag">Azure ingress<br>Sweden Central</div><div class="nodes">
<div class="node blue"><b>Event Hubs</b><span>raw replay buffer</span></div>
<div class="node blue"><b>Identity-based relay</b><span>Container App · Entra workload identity, no SAS (ADR-005)</span></div>
<div class="node blue"><b>MES · ERP · LIMS · CMMS</b><span>Fabric pipelines / copy jobs</span></div>
</div></div>
<div class="arrow">▲ OPC UA · MQTT · historian export → AMQP/TLS, allow-listed outbound egress</div>
<div class="lane"><div class="lane-tag">Sites<br>LU · DE · BE · ES</div><div class="nodes">
<div class="node"><b>Industrial DMZ gateway</b><span>Purdue L3.5 · schema-validating · outbound only</span></div>
<div class="node"><b>PLC · SCADA · historian</b><span>Purdue L0–L2 · no cloud inbound path</span></div>
</div></div>
</div>

<!-- ⏱ 1:50 · This is the whole system on one slide; I'll return to it three times.
Read it bottom to top, the way the data actually travels. At each site, controllers and historians sit at Purdue levels zero to two with no inbound path from the cloud, and a gateway in an industrial DMZ terminates OT protocols and only ever emits outbound, schema-validated telemetry — no cloud system ever reaches down into the plant.
One level up, Azure Event Hubs buffers, and a managed-identity relay publishes to Fabric's Eventstream over Entra ID with no shared key; batch systems — MES, ERP, LIMS, CMMS — land on the same contract through Fabric pipelines.
Above that Fabric is the core: hot data in KQL, governed bronze-silver-gold history in OneLake, one Direct Lake semantic model, Power BI, and Activator strictly for notifications.
At the top, Python services do the math and read Fabric read-only, and Foundry and Speech handle language. Features and labels flow down into them; predictions, recommendations and audit facts flow back up. -->

---

<!-- _class: diagram diagram-title-in-image -->

# Fabric Architecture

![Fabric architecture](images/fabric-architecture-diagram.webp)

<!-- ⏱ 0:25 · This diagram expands the Fabric core: Real-Time Intelligence handles the operational clock, OneLake and the Lakehouse preserve governed history, and a shared semantic layer serves analytics and decision experiences without creating a parallel data estate. -->

---

<!-- _class: fabric-gravity -->

# Why Microsoft Fabric Is the Center of Gravity

<p class="subtitle">Fabric items span every workload — representative workspace item types, grouped by what they do.</p>

<div class="chain fabric-chain">
<div class="node orange"><b>01 · Move &amp; orchestrate</b><span class="wl">Data Factory</span><span>data pipeline · copy job · Dataflow Gen2 · Apache Airflow job</span></div>
<div class="step">›</div>
<div class="node teal"><b>02 · Store &amp; serve</b><span class="wl">Eng. / DW / DB</span><span>lakehouse · warehouse · mirrored database · SQL / Cosmos DB</span></div>
<div class="step">›</div>
<div class="node purple"><b>03 · Transform &amp; build</b><span class="wl">Data Engineering</span><span>notebook · Spark job definition · environment · API for GraphQL</span></div>
<div class="step">›</div>
<div class="node green"><b>04 · Analyze &amp; learn</b><span class="wl">Data Science / BI</span><span>ML experiment · ML model · semantic model · data agent</span></div>
<div class="step">›</div>
<div class="node blue"><b>05 · Stream &amp; respond</b><span class="wl">Real-Time Intelligence</span><span>Eventstream · Eventhouse · KQL queryset · RT dashboard / Activator · digital twin builder*</span></div>
<div class="step">›</div>
<div class="node pink"><b>06 · Share &amp; context</b><span class="wl">Power BI / Fabric IQ</span><span>report / dashboard · paginated report · ontology* · graph</span></div>
</div>

<div class="split">
<div>

- **Real-Time Intelligence** — Eventstream + Eventhouse/KQL for hot telemetry
- **OneLake / Lakehouse** — bronze→silver→gold governed history & ML

</div>
<div>

- **Direct Lake** — one semantic model, no data copy
- **Power BI + Activator** — reporting & notification (not control)

</div>
</div>

<div class="foundation-bar"><b>One shared foundation</b><span>OneLake · workspace governance · unified security</span></div>

<!-- ⏱ 1:45 · Why bet the platform on Fabric? Because heavy-industry analytics has two clocks: a one-second operational clock and a governed-history clock. Fabric handles both in one governed estate.
Real-Time Intelligence — Eventstream into an Eventhouse KQL database — gives us hot telemetry, alarms, and freshness. OneLake with bronze-silver-gold Delta gives us immutable lineage, the training substrate, and stable KPI definitions.
Direct Lake means one semantic model reads gold data with no extra copy — so high-grade yield means exactly one thing everywhere.
We consciously chose not to build a parallel lake or a second BI stack, and we keep hot KQL separate from governed Delta, so we always answer from the right store.
The chain across the top walks that estate end to end: move and orchestrate with Data Factory, store and serve in the lakehouse and warehouse, transform and build in notebooks and Spark, analyze and learn with ML and semantic models, stream and respond through Real-Time Intelligence, then share and context in Power BI and Fabric IQ. Six stages, one shared foundation — OneLake, workspace governance, unified security.
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

<!-- _class: lead chapter purple -->
<!-- _paginate: false -->

<img class="chapter-icon" src="images/icon_decision_intelligence.png" alt="" onerror="this.remove()">

<div class="chapter-num">03</div>

# Decision intelligence

<p class="chapter-sub">Energy · RUL · quality · knowledge</p>

<div class="chapter-path">
<span>01 Business</span>
<span>02 Platform</span>
<span class="now">03 Decision</span>
<span>04 Trust</span>
<span>05 Demo</span>
<span>06 Value</span>
<span>07 Appendix</span>
</div>

<!-- ⏱ 0:08 · Chapter three: the four AI capabilities that turn governed data into decisions. -->

---

# The Four AI Capabilities

<div class="cards four">
<div class="card orange"><div class="card-num">ENERGY</div><h3>Energy Dispatch</h3><p>Deterministic Python optimizer, constraint-aware</p></div>
<div class="card teal"><div class="card-num">RUL</div><h3>Lining RUL</h3><p>Physics-informed Python model, daily scoring</p></div>
<div class="card purple"><div class="card-num">QUALITY</div><h3>Quality Risk</h3><p>Python model over genealogy features</p></div>
<div class="card green"><div class="card-num">KNOWLEDGE</div><h3>Knowledge Capture</h3><p>Azure Speech + Foundry Agent Service</p></div>
</div>

**ADR-006:** Python is authoritative for math · Foundry explains/retrieves, never decides or commits

<!-- ⏱ 1:10 · Four capabilities, one principle that I'll defend hard: the deterministic, testable Python services compute the answer — feasible dispatch, remaining useful life, quality risk.
The generative agent explains, retrieves, and orchestrates approved tool calls; it never invents a schedule, relaxes a constraint, or makes a commitment.
That's ADR-006, and it's why a language model being confidently wrong can't hurt a furnace here. -->

---

<!-- _class: tight vnext -->
<!-- _header: '' -->
<!-- _footer: '' -->

# AI Architecture in Detail

<div class="flow">
<div class="lane teal"><div class="lane-tag">Features<br>governed gold</div><div class="nodes">
<div class="node teal"><b>Dispatch inputs</b><span>day-ahead price, grid carbon, production & maintenance constraints</span></div>
<div class="node teal"><b>Thermal & cooling</b><span>heat-flux slope, spatial contrast, cooling residual</span></div>
<div class="node teal"><b>Genealogy</b><span>heat → slab → coil → sample → shipment</span></div>
<div class="node teal"><b>Consented transcripts</b><span>personal details stripped before use — names, IDs and contacts replaced by neutral placeholders</span></div>
</div></div>
<div class="arrow">▼ Direct Lake / read-only adapters — features and labels, never raw OT credentials</div>
<div class="lane purple"><div class="lane-tag">Deterministic core<br>Python decides</div><div class="nodes">
<div class="node purple"><b>Energy dispatch</b><span>MILP (PuLP + CBC) → feasible schedule · greedy fallback, labelled in UI</span></div>
<div class="node purple"><b>Lining RUL</b><span>physics-informed regression → P10/P50/P90 + confidence · daily scoring</span></div>
<div class="node purple"><b>Quality risk</b><span>genealogy model → spec probability + bounded what-if</span></div>
</div></div>
<div class="arrow">▼ recommendation object: value, drivers, confidence, model version, constraints honoured</div>
<div class="lane orange"><div class="lane-tag">Language layer<br>Foundry explains</div><div class="nodes">
<div class="node orange"><b>Speech Fast Transcription</b><span>consent state machine · speaker separation</span></div>
<div class="node orange"><b>Foundry Agent Service (EU)</b><span>drafts procedure trigger → action → rationale → risk, cited to transcript segments</span></div>
<div class="node orange"><b>Grounding & guardrails</b><span>Prompt Shields (direct + indirect) · read/simulate tool allow-list · Copilot chat has no tools (ADR-011)</span></div>
</div></div>
<div class="arrow">▼ a model response is never authorization</div>
<div class="lane green"><div class="lane-tag">Human gate<br>& audit</div><div class="nodes">
<div class="node green"><b>Accept · modify · reject</b><span>with a reason code, per recommendation</span></div>
<div class="node green"><b>Commit endpoint</b><span>separately policy-gated · work order, approved dispatch, published procedure</span></div>
<div class="node green"><b>Append-only trail</b><span>inputs, model version, confidence, rationale, decision, outcome</span></div>
</div></div>
</div>

<!-- ⏱ 2:05 · Now the same picture for the AI, because "we use AI" is not an architecture.
Bottom layer up: every model reads governed gold features — dispatch inputs, thermal and cooling signals, the full heat-slab-coil genealogy, and consented transcripts whose personal details have been stripped out before anything reaches a model — names, badge numbers and contact details are replaced by neutral placeholders, so the procedure survives and the person is not identifiable. No model gets a raw OT credential.
The deterministic core is Python and it is the only thing that decides. Dispatch is a mixed-integer linear program solved with PuLP and CBC, with a deterministic greedy heuristic as a labelled fallback — never a silent one. Lining life is a physics-informed regression that emits P10, P50 and P90 with a confidence. Quality risk is a model over genealogy features.
Only then does language enter: Speech transcribes under an explicit consent state machine, and the Foundry agent in the EU Data Zone drafts and explains, with every claim cited to a transcript segment, behind Prompt Shields and a read-or-simulate tool allow-list.
And nothing leaves that stack without a human accepting, modifying, or rejecting it with a reason code, written to an append-only trail. That is the whole trust argument in one diagram. -->

---

<!-- _class: tight deep-dive -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Deep Dive: Energy Dispatch Optimization

<div class="split right-wide">
<div>

### Shift production — do not reduce it

A deterministic **MILP** (PuLP/CBC) assigns every flexible batch to one
15-minute slot, minimizing weighted energy cost + CO₂. Required tonnage is
identical; urgent heats stay pinned.

**Hard constraints:** maximum shift / hold window, minimum soak time,
furnace concurrency and equipment eligibility. Invalid inputs or an infeasible
plan are surfaced — constraints are never silently relaxed.

The single-threaded solve returns baseline vs. optimized schedules, constraint
evidence and whole-dispatch savings. A human reviews the proposal and records
accept / modify / reject; the Foundry agent may explain it, **never compute it**.

</div>
<div>

<div class="deep-dive-shot"><img src="images/energy-optimization-spot-price-schedule.png" alt="Energy dispatch portal showing spot price and scheduled load"></div>

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

<!-- ⏱ 1:45 · Energy is the fastest payback. Tomorrow evening has a scarcity peak at two-hundred-eighty euros per megawatt-hour.
The optimizer shifts one eligible reheat batch — the urgent automotive coil stays fixed — and never silently relaxes a hard production constraint.
On this synthetic horizon that's a seven-point-two-five-percent modeled energy-cost reduction, peak down from fifty-six to fifty-one-point-six megawatts, three-point-three-percent CO₂ reduction — all on the whole-dispatch basis with identical planned tonnage at nine-sixty tonnes and zero hard-constraint violations.
Those are single-scenario evidence, not banked savings — realized savings are tracked separately in an auditable ledger, which is how the fourteen-percent annual target eventually gets proven rather than asserted. -->

---

<!-- _class: tight deep-dive -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Deep Dive: Furnace Lining Remaining Useful Life

<div class="split right-wide">
<div>

### Physics-based RUL — not a black box

Daily scoring fits an explainable linear wear trend to **hearth refractory
thickness**, corroborated by heat-flux and cooling-water behavior. The core
estimate is `TTF = (thickness − 300 mm safe threshold) / |wear slope|`.

Slope standard error is propagated with the **delta method** to produce
P10 / P50 / P90, while fit quality, observation window and thermal agreement
contribute to confidence. Fewer than three valid thickness observations yields
no forecast — not false precision.

A `HIGH` risk gate is raised at score ≥ 0.80. Engineers see named drivers,
acknowledge the advisory alert and may open a CMMS work order; the platform
never controls the furnace or creates maintenance action autonomously.

</div>
<div>

<div class="deep-dive-shot"><img src="images/furnace-health-lining-forecast.png" alt="Furnace health portal showing the lining forecast"></div>

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

<!-- ⏱ 1:45 · This is the capability that turns an eight-million-euro surprise into a planned intervention.
The model is physics-informed — constrained by heat-flux and cooling physics, not a black box fitting noise. On our warning scenario it estimates a P50 remaining life of about twenty days with a tight band — P10 nineteen, P90 twenty-one — a confidence of zero-point-seven-eight from an r-squared of zero-point-eight-eight, and three named drivers.
The engineer stays accountable: they acknowledge the alert and it links to a CMMS work order. The platform does not touch the furnace, and pilot scoring is daily — I'm not promising real-time inference as an MVP feature. -->

---

<!-- _class: tight deep-dive -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Deep Dive: In-line Quality Prediction

<div class="split">
<div>

### Detect drift before scrap occurs

The governed feature path joins full **heat → slab → coil genealogy** with
coiling-temperature bias, carbon-equivalent context and quality status. The
synthetic scenario activates the warning before the first off-spec laboratory
result, creating an intervention window rather than a scrap report.

The score returns calibrated spec risk, predicted first-pass yield and named
drivers. A bounded what-if tests only approved ranges for coiling temperature,
force balance and carbon-equivalent adjustment, with P10 / P50 / P90 impact.

Every proposal carries `operationalWrite: false`: it can guide a process
engineer, but cannot change a grade recipe or production setpoint.

</div>
<div>

<div class="deep-dive-shot"><img src="images/quality-spc.png" alt="Quality portal showing SPC drift and defect Pareto"></div>

<div class="stat"><div class="big">~88% → ~95%</div><div class="label">predicted first-pass yield after bounded correction</div></div>

<span class="pill blue">🔬 EVIDENCE</span> Synthetic what-if scenario
<span class="pill orange">🎯 TARGET</span> +8% yield fleet-wide

</div>
</div>

<!-- ⏱ 1:25 · Quality value is twofold: catch drift early, and prove traceability.
Here coiling temperature and force balance drift together before any off-spec lab result, and the model traces the affected heat, slab, and coil. A bounded what-if correction lifts predicted first-pass yield from about eighty-eight to ninety-five percent on this synthetic coil — roughly the eight-percent relative target — without changing the grade recipe.
That distinction matters: this is a what-if recommendation, not an automatic write-back to process control. -->

---

<!-- _class: tight deep-dive -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Deep Dive: GenAI Knowledge Capture

<div class="split">
<div>

### Capture expertise before it retires

Explicit consent gates recording; **Azure Speech Fast Transcription** creates
speaker-separated segments. A Foundry 5-series deployment drafts grounded
observation, recommended check, rationale and safety-boundary fields.

Every claim must cite a real `[S<n>]` transcript segment. A second critic pass
checks citations, completeness and unsafe steps, with at most two revision
iterations. Missing evidence triggers revision or refusal — never invention.

Only a `Knowledge.Publisher` can approve the versioned draft. Prompt-injection
screening, content safety, PII redaction and a hash-chained audit trail protect
the flow; only **APPROVED** procedures become retrievable.

</div>
<div>

<div class="deep-dive-shot"><img src="images/knowledge-hub-capture-status.png" alt="Knowledge capture portal showing grounded procedure status"></div>

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

<!-- _class: lead chapter green -->
<!-- _paginate: false -->

<img class="chapter-icon" src="images/icon_trust_governance.png" alt="" onerror="this.remove()">

<div class="chapter-num">04</div>

# Trust & governance

<p class="chapter-sub">Security · Responsible AI · compliance</p>

<div class="chapter-path">
<span>01 Business</span>
<span>02 Platform</span>
<span>03 Decision</span>
<span class="now">04 Trust</span>
<span>05 Demo</span>
<span>06 Value</span>
<span>07 Appendix</span>
</div>

<!-- ⏱ 0:08 · Chapter four: the guardrails, security posture and compliance obligations behind every recommendation. -->

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
If a capability is classified high-risk, we apply the full control set — risk management, documentation, human oversight, robustness, and conformity assessment. Nothing reaches production without the cross-functional board's sign-off.
On the generative side we treat every retrieved document and market payload as untrusted: Prompt Shields for direct and indirect injection, instructions separated from data, narrow tool allow-lists, full tool-call logging, and human approval on any write.
A model response is never authorization. -->

---

<!-- _class: tight security-slide -->

# Security, Identity & EU Data Residency

<div class="split">
<div>

<div class="security-principles">
<div><b>Zero Trust</b><span>Never trust, always verify — every agent request is authenticated and authorized</span></div>
<div><b>Least Privilege</b><span>Each agent has minimal permissions for its specific function</span></div>
<div><b>Defense in Depth</b><span>Multiple security layers: network, identity, data and application</span></div>
<div><b>Security Left Shift</b><span>Security checks run in the CI/CD pipeline, not just production</span></div>
<div><b>Data Minimization</b><span>Agents access only the data required for their specific task</span></div>
</div>

</div>
<div>

| Aspect | Posture |
|---|---|
| Identity | Entra managed identities; no standing secrets |
| Authorization | Azure RBAC ≠ Fabric ≠ Foundry ≠ app roles |
| Residency | Sweden Central + Data Zone (EU) |
| Audit retention | 1 yr hot + 6 yr archive |
| Interview audio | Highly Confidential, 30 d |
| Deploy secrets | None — GitHub OIDC |

</div>
</div>

<!-- ⏱ 1:50 · Security here is Zero Trust and least privilege by construction, not by policy document.
Zero Trust means three things concretely: every call is authenticated and authorized on its own merits, nothing is trusted just because it is inside the network, and we design assuming a breach has already happened — so we optimise for containment rather than for a perfect perimeter.
Least privilege means every identity is scoped to exactly one job and nothing more. There are no standing secrets — every workload uses its own Entra managed identity — and Azure RBAC, Fabric roles, Foundry RBAC and application roles are four separate planes: holding one grants nothing in another. That is what keeps the blast radius of any single compromise small.
Data is classified, and operator audio is Highly Confidential with DLP and deletion workflows.
Everything processes in the EU — Sweden Central primary, Foundry in the EU Data Zone — and deployments federate through GitHub OIDC, so even the pipeline holds no secret. -->

---

<!-- _class: cost-slide -->

# What It Costs to Run One Site

<span class="pill orange">🎯 TARGET</span> Sweden Central list-price check · EUR · 04 Aug 2026 — not a quote

<div class="split">
<div>

| Tier · one site | Shape | Fabric | Fabric + OneLake €/yr |
|---|---|:-:|--:|
| **Mini** — demo / shadow | 1 line, replay + shadow scoring | F8 · PAYG 6 h/day | **≈ €3k–€4k** |
| **Medium** — pilot ~0.3 Mt | 1 site read-only, live ingest | F64 · 24×7 | **≈ €57k–€98k** |
| **Large** — full site ~1.0 Mt | full plant, 4 AI capabilities | F128 · 24×7 | **≈ €116k–€205k** |

<p class="legend">Baseline = Fabric compute + assumed hot OneLake: 0.5–5 TB / 5–20 TB / 20–75 TB. Medium and large span 1-year reservation to PAYG; mini uses PAYG because it is paused.</p>

</div>
<div>

| Medium full-stack planning envelope | Indicative €/yr |
|---|--:|
| Fabric F64 + OneLake | €57k–€98k |
| Event Hubs buffer | €40k–€80k |
| Foundry + Speech · usage based | €30k–€90k |
| Apps + Power BI creator seats | €20k–€50k |
| Security & governance | €30k–€60k |
| Platform networking | €10k–€30k |
| **Total planning envelope** | **≈ €187k–€408k** |

</div>
</div>

<!-- ⏱ 1:50 · Now the question every CFO asks: what does one site cost to run?
We use three explicit deployment profiles: F8 for a mini demo or shadow footprint, F64 for a medium one-site pilot, and F128 for a large full-site deployment. At the official Sweden Central list rate of 0.1667 euros per capacity unit-hour, F8 running six hours a day is about 2.9 thousand euros a year in Fabric compute. F64 running continuously is 93.5 thousand PAYG or 55.6 thousand with a one-year reservation. F128 is 186.9 thousand PAYG or 111.2 thousand reserved. The displayed baseline adds explicit hot-OneLake volume assumptions.
The corrected medium full-stack envelope is roughly 187 to 408 thousand euros a year. The earlier model double-counted AI and machine-learning compute as a separate line: Fabric Data Science, notebooks, real-time intelligence, and Power BI draw from the same shared F-capacity pool. Separate Spark autoscale would be added only if we deliberately enable it and measure its job hours.
Event Hubs, Foundry, Speech, creator licenses, security, and broader platform networking remain usage-sensitive planning allowances. At F64 and above, viewer-role users can view Power BI with a free Fabric license, while creators still need Pro or PPU. These are retail planning figures before negotiated discounts, taxes, and measured workload tuning — not a quote. -->

---

# The Business Case for One Site

<div class="split">
<div>

<div class="stat"><div class="big">&lt; 12 mo</div><div class="label">payback, conservative case · &lt; 9 base · &lt; 6 optimistic</div></div>

- Build (one-off): **€0.6M–€1.1M** — foundation, three AI workloads, experience, DPIA & AI Act file
- Run: **€0.19M–€0.41M/yr** at pilot scale

</div>
<div>

| Value lever | Basis | €/yr at ~1.0 Mt |
|---|---|--:|
| Energy (O1) | 1.0 Mt × €175/t × 14% | **~€24.5M** |
| Avoided reline (O3) | €8M × 1 / 2.5 yr | **~€3.2M** |
| ETS avoidance (O2) | tonnage × tCO₂/t × €70 × 22% | several M |
| High-grade yield (O4) | premium tonnage × margin × 8% | several M |

<span class="pill orange">🎯 TARGET</span> Every figure above is modelled, not banked

</div>
</div>

<!-- ⏱ 1:25 · Put the run cost next to the value and the case is not close.
Build is between six hundred thousand and one-point-one million one-off. The corrected run-cost planning envelope is under four hundred and ten thousand a year at pilot scale.
Against that, the energy lever alone is roughly twenty-four and a half million a year at a one-million-tonne site — because fourteen percent of thirty-five percent of a five-hundred-euro-per-tonne cost base is a structural number, not a rounding error. Avoided relines add about three point two million expected. Carbon and yield add several million more.
So payback is well under a year even after large conservative haircuts. But I will not leave you with one number: the sensitivity table in the appendix shows what happens if the percentages come in lower, and the answer is that the case shrinks and stays comfortably positive. The pilot proves the real percentage before anyone commits at scale. -->

---

<!-- _class: tight compliance-slide -->

# Compliance

<div class="split">
<div>

| Regulation | Duty that binds us | Where it lands |
|---|---|---|
| **EU AI Act** (EU) 2024/1689 | Art. 12–15 · logging, oversight, robustness | Append-only audit chain · RAI board gate |
| **EU ETS** 2003/87/EC · MRV 2018/2066 | Monitored, verifiable CO₂ lineage | Emission-factor lineage · allowance cost in dispatch |
| **IEC 62443** ‑3‑2 / ‑3‑3 | Zones, conduits, target SL | Outbound-only DMZ · no write-back |
| **NIS2** (EU) 2022/2555 | Art. 21 measures · Art. 23 24 h / 72 h | Sev-1 path · runbooks · registration |
| **GDPR** (EU) 2016/679 | Art. 17 · 22 · 32 · 35 | Erasure · human decision · DPIA |

</div>
<div>

- **CBAM** definitive period from 2026 — fed by the same emission lineage
- **Machinery Reg. (EU) 2023/1230** out of scope while advisory-only
- **IEC 61511** safety instrumented system stays fully independent
- **CSRD / ESRS E1** still moving — we produce the data, not the assurance
- **ISO/IEC 27001 · 42001** as the management-system frame

</div>
</div>

<p class="compliance-gates"><span class="pill orange">🎯 OPEN GATES</span> Accredited ETS verifier · DPIA · Legal's AI Act classification</p>

> We produce audit-grade **management information**, not a regulated filing. Full analysis: `docs/business/compliance/`

<!-- ⏱ 2:00 · Compliance is not a slide we bolt on at the end; five regulatory regimes shaped the architecture itself.
The EU AI Act drove the append-only audit chain — inputs, model version, confidence, rationale, the human decision and the outcome — and the Responsible AI board as a hard promotion gate.
The Emissions Trading System drove emission-factor lineage: every tonne of CO₂ we report can be traced back to the meter reading and the factor version that produced it, and the allowance price sits inside the dispatch objective rather than in a spreadsheet next to it.
IEC 62443 drove the zone-and-conduit design: the plant is a zone, the conduit is outbound-only, and there is no return path to a controller. That single decision is what keeps the Machinery Regulation and IEC 61511 out of scope — we are not a safety component, and the safety instrumented system remains completely independent of us.
NIS2 applies because manufacture of basic metals is an important entity: twenty-four-hour early warning, seventy-two-hour notification, and management liability. GDPR applies to the operator data in the knowledge capture, so erasure, the Article 22 human-decision guarantee, and a DPIA are all in scope.
Be clear about what we are not claiming. We produce audit-grade management information. An accredited verifier, a completed DPIA, and Legal's formal AI Act classification are open gates, and I will not pretend otherwise. -->

---

<!-- _class: lead chapter blue -->
<!-- _paginate: false -->

<img class="chapter-icon" src="images/icon_demo.png" alt="" onerror="this.remove()">

<div class="chapter-num">05</div>

# Live demonstration

<p class="chapter-sub">Persona journeys · evidence reproduced</p>

<div class="chapter-path">
<span>01 Business</span>
<span>02 Platform</span>
<span>03 Decision</span>
<span>04 Trust</span>
<span class="now">05 Demo</span>
<span>06 Value</span>
<span>07 Appendix</span>
</div>

<!-- ⏱ 0:08 · Chapter five: seven persona journeys, reproducing the evidence live. -->

---

# What You'll See Next

<div class="split">
<div>

**From operations to optimization**

1. Fleet overview — Marc Weber, Plant Manager
2. Energy dispatch optimization
3. Furnace lining RUL alert
4. Quality prediction & genealogy

</div>
<div>

**From prediction to proof**

5. Operator knowledge capture
6. Sustainability / ETS / audit
7. Recap — targets vs. evidence

</div>
</div>

> Targets are 14 / 22 / 21 / 8 — the demo proves the mechanics, not the savings.

<!-- ⏱ 0:20 · I'll move through seven experiences in the order an operating day touches them, starting with Marc Weber's site command centre, and I'll call out target versus evidence as we go. -->

---

<!-- _class: tight agent-swarm -->

# How We Built the Demo with an Agent Swarm

<p class="subtitle">Agentic development = organized specifications + reusable skills + Copilot execution + bounded GitHub specialists</p>

<div class="cards four">
<div class="card purple"><div class="card-num">01 · Organize</div><h3>GitHub Spec Kit</h3><p>Constitution → spec → plan → tasks; acceptance criteria exist before code</p></div>
<div class="card blue"><div class="card-num">02 · Equip</div><h3>Superpowers</h3><p>Reusable skills enforce brainstorming, TDD, debugging and review discipline</p></div>
<div class="card teal"><div class="card-num">03 · Execute</div><h3>GitHub Copilot</h3><p>VS Code + Copilot CLI + GitHub Copilot app carry one governed workflow</p></div>
<div class="card green"><div class="card-num">04 · Delegate</div><h3>Specialized GitHub agents</h3><p>Coding, QA, security, research and docs agents own bounded branches and PRs</p></div>
</div>

<div class="chain">
<div class="node purple"><b>Specify</b><span>intent + constraints</span></div>
<div class="step">›</div>
<div class="node blue"><b>Approve plan</b><span>human gate</span></div>
<div class="step">›</div>
<div class="node teal"><b>Build in parallel</b><span>bounded ownership</span></div>
<div class="step">›</div>
<div class="node green"><b>Prove in GitHub</b><span>CI + reviews + PR</span></div>
</div>

<!-- ⏱ 0:35 · We treated agentic development as an organized engineering system, not ad-hoc prompting. GitHub Spec Kit turns intent into a constitution, specification, plan, tasks, and acceptance criteria. Superpowers adds reusable skills for brainstorming, test-driven development, debugging, and review. GitHub Copilot then executes the same governed workflow across VS Code, Copilot CLI, and the GitHub Copilot app. Specialized coding, QA, security, research, and documentation agents own bounded branches and pull requests; automated gates prove the work, and a human approves the plan and the merge. -->

---

<!-- _class: lead chapter -->
<!-- _paginate: false -->

<img class="chapter-icon" src="images/icon_value_next_steps.png" alt="" onerror="this.remove()">

<div class="chapter-num">06</div>

# Value & next steps

<p class="chapter-sub">Targets vs. evidence · roadmap · close</p>

<div class="chapter-path">
<span>01 Business</span>
<span>02 Platform</span>
<span>03 Decision</span>
<span>04 Trust</span>
<span>05 Demo</span>
<span class="now">06 Value</span>
<span>07 Appendix</span>
</div>

<!-- ⏱ 0:08 · Chapter six: separating target from evidence, the roadmap, and the decision asked today. -->

---

<!-- _class: tight -->

# NovaSteel vNext: Two-way Control with Microsoft Adaptive Cloud

<div class="split right-wide">
<div class="small-body">

**Goal**

- Enable selected closed-loop actions for low-risk workloads

**Adaptive Cloud implementation**

- **Azure Arc** manages edge Kubernetes lifecycle and policy
- **Azure IoT Operations** provides MQTT, OPC UA, and local dataflows
- **Azure IoT Hub** provides command, device identity, twins, and jobs
- **Fabric + AI services** provide prediction and policy context

**Safe control loop**

1. AI marks a low-risk workload as control-eligible
2. Policy checks the safety envelope, interlocks, and approval
3. IoT executes the bounded command; acknowledgement and telemetry close the audit loop

</div>
<div>

![w:610](images/adaptive-cloud-iot-operations.png)

<span class="pill orange">vNext</span> OT safety systems remain authoritative; AI can act only inside predefined control envelopes.

</div>
</div>

<!-- ⏱ 0:30 · This is the forward-looking control architecture: Arc-managed edge, IoT Operations for local protocol and runtime, IoT Hub for identity and cloud command, and policy-gated AI decisions. We start with human-confirmed actions and expand only to bounded autonomous loops where safety and governance approvals are explicit. -->

---

# Conclusion

<div class="cards four">
<div class="card teal"><div class="card-num">01</div><h3>One governed platform</h3><p>Scattered data and tools replaced by a single EU-hosted estate</p></div>
<div class="card purple"><div class="card-num">02</div><h3>AI that is accountable</h3><p>Python decides, GenAI explains, a human approves — every output replayable</p></div>
<div class="card green"><div class="card-num">03</div><h3>Safe by construction</h3><p>Advisory only · outbound-only OT boundary · Zero Trust, least privilege</p></div>
<div class="card orange"><div class="card-num">04</div><h3>A case that survives haircuts</h3><p>Payback under 12 months even on conservative assumptions</p></div>
</div>

<div class="split">
<div>

<span class="pill blue">🔬 EVIDENCE</span> The mechanics work end to end, reproducibly, on synthetic data

</div>
<div>

<span class="pill orange">🎯 TARGET</span> 14 / 22 / 21 / 8 remain targets until a pilot proves them

</div>
</div>

> The honesty discipline *is* the trustworthiness.

> **Turns Signal into business outcomes with Intelligence & Trust.**

<!-- ⏱ 1:05 · Let me close on four things, and one distinction.
First, one governed platform: the scattered historians, spreadsheets and disconnected tools become a single EU-hosted estate with one definition of every KPI.
Second, AI that is accountable: deterministic Python computes the answer, the language model only explains it, a human approves it, and every consequential output is replayable input by input.
Third, safe by construction: advisory only, an outbound-only boundary to the plant, Zero Trust and least privilege — safety systems stay authoritative and untouched.
Fourth, a business case that survives large haircuts: payback under twelve months even on the conservative assumptions in the appendix.
And the distinction I have kept all morning: what you just watched is evidence that the mechanics work, reproducibly, on synthetic data. Fourteen, twenty-two, twenty-one and eight remain targets until a pilot proves them. That discipline is the trustworthiness. In one line: NovaSteel turns signal into business outcomes with intelligence and trust. -->

---

<!-- _class: tight -->

# Next Steps

<div class="split">
<div>

**Immediate — next 30 days**

1. **Assumption workshop** — replace our seven cost assumptions with AxelorMetal actuals
2. **Site selection** for the Phase 1 pilot (~0.3 Mt line)
3. **Open the governance gates**: DPIA kick-off, Legal's EU AI Act classification, accredited ETS verifier engagement

**Phase 1 — one-site pilot**

- Read-only integration: historian, MES, CMMS, market feed
- Shadow scoring, fully logged, **zero operational effect**
- Auditable **savings ledger** — the mechanism that converts a target into a banked number

</div>
<div>

| Gate | Owner | Must be closed before |
|---|---|---|
| DPIA complete | DPO | Any operator recording |
| AI Act classification | Legal | Production promotion |
| OT/ICS sign-off | OT engineering | Any site connection |
| RAI board approval | RAI board | Any model promotion |
| Measured capacity | Platform ops | Production sizing |

<span class="pill orange">🎯 DECISION ASKED TODAY</span> Approve the pilot scope and open the gates — not the full rollout

</div>
</div>

<!-- ⏱ 0:55 · So what do I actually want from you?
Not a rollout decision. In the next thirty days: a workshop where we replace our seven assumptions with your real numbers, a choice of pilot site, and the opening of three governance gates — the DPIA, Legal's AI Act classification, and an accredited ETS verifier.
Then Phase 1 is a single site, read-only, with shadow scoring that changes nothing on the floor, and an auditable savings ledger — because that ledger is the only honest mechanism for turning a fourteen-percent target into a banked fourteen percent.
The right-hand table is the gate list, each with a named owner, and none of them is ours to waive.
The decision I'm asking for today is narrow: approve the pilot scope and open the gates. Thank you — I'll take your hardest questions now. -->

---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Thank You

## Questions & discussion

> AI advises, humans decide.

<!-- ⏱ 0:10 · Thank you. I welcome your questions. -->


---

<!-- _class: lead chapter gray backup -->
<!-- _paginate: false -->

<img class="chapter-icon" src="images/icon_appendix.png" alt="" onerror="this.remove()">

<div class="chapter-num">07</div>

# Appendix

<p class="chapter-sub">ADRs · cost model · roadmap · backup Q&A</p>

<div class="chapter-path">
<span>01 Business</span>
<span>02 Platform</span>
<span>03 Decision</span>
<span>04 Trust</span>
<span>05 Demo</span>
<span>06 Value</span>
<span class="now">07 Appendix</span>
</div>

<!-- ⏱ 0:00 · Appendix: architecture decision records, cost sensitivity, phased roadmap, and backup answers for the harder questions. -->

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
- EU AI Act high-risk duties cannot be evidenced on synthetic data

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

---

<!-- _class: tight backup -->

# Appendix — Architecture Decision Records

<div class="split">
<div>

| ADR | Decision |
|---|---|
| 001 | Fabric is the data and analytics core — **no parallel data lake** |
| 002 | Separate hot KQL from governed Delta |
| 003 | Sweden Central primary, EU-zone-aware AI |
| 004 | Blazor shell plus React/MUI/D3 microfrontend |
| 005 | Identity-based Custom Endpoint ingress — **no SAS key** |
| 006 | Python is authoritative for optimization/scoring; Foundry is not the controller |
| 007 | Human approval and **no direct OT action** |
| 008 | Demo is a separate deterministic product slice *(amended by 017)* |
| 009 | No guessed runtime versions |

</div>
<div>

| ADR | Decision |
|---|---|
| 010 | Internal Power BI embedding is user-owned data |
| 011 | The Copilot chat explains; it does not retrieve operational values |
| 012 | Conversations are in-process, never persisted to Fabric |
| 013 | Device simulator runs in-process inside the BFF |
| 014 | Two-level Dockview workspace with JSX-derived panels |
| 015 | The Help Assistant resolves topics from the DOM |
| 016 | Event Hubs, not IoT Hub, is the telemetry ingress buffer |
| 017 | One data path — no mode toggle; **honesty is unconditional** |
| 018 | Two streams into Fabric: governed analytical **and** real-time |

</div>
</div>

<!-- ⏱ 0:00 · Appendix slide. Eighteen recorded architecture decisions, each with a rationale and a rejected-alternatives section in docs/architecture/solution-architecture.md section 10. Anything I assert on stage traces back to one of these; ADR-001, 005, 006 and 007 are the four that carry the most weight, and 017 and 018 are the newest — they remove the demo/cloud toggle and define the two data streams landing in Fabric. -->

---

<!-- _class: tight backup -->

# Appendix — Cost Model & Sensitivity

<div class="split">
<div>

**Assumptions to challenge first**

| # | Assumption | Value |
|---|---|--:|
| A1 | Annual production, in-scope site | ~1.0 Mt/yr |
| A1b | Pilot line (Phase 1) | ~0.3 Mt/yr |
| A2 | Production cost | ~€500/t |
| A3 | Energy share | 35% → ~€175/t |
| A5 | EU ETS carbon price | ~€70/tCO₂ |
| A7 | Furnace failure cost | ~€8M/event |
| A8 | Failure frequency (pilot line) | 1 per 2–3 yr |

</div>
<div>

**What changes the answer**

| Driver | If lower than assumed | Mitigation |
|---|---|---|
| Energy saving < 14% | Benefit shrinks, stays large | Pilot proves the real % first |
| CO₂ reduction < 22% | Smaller ETS avoidance | Validate by shadow scoring |
| Failures less frequent | O3 benefit smaller | Treat O3 as upside, not base case |
| Yield uplift < 8% | O4 smaller | Prove via SPC before crediting |
| Azure cost higher | Run cost up | Reservations, right-sizing, FinOps cadence |

</div>
</div>

<!-- ⏱ 0:00 · Appendix slide. Every euro on the business-case slide derives from these seven assumptions, and each is meant to be replaced by AxelorMetal actuals in a design workshop. The right-hand table is the honest downside: if the percentages come in lower, the case shrinks and stays positive, and no lever is load-bearing on its own. -->

---

<!-- _class: tight backup -->

# Appendix — Phased Delivery Roadmap

| Dimension | Demonstration — defense | Phase 1 — one-site pilot | Phase 2+ — production |
|---|---|---|---|
| Sources | Simulator + approved replay | One site: historian, MES, CMMS, market feed — read-only | Four sites, approved integrations |
| Ingestion | Eventstream from simulator | OT gateway → Event Hubs → relay → Eventstream | Same contract, per-plant relay |
| AI | Cached / replayable scoring | Shadow scoring, fully logged, no operational effect | Human-approved write-back only |
| Capacity | F2 (F4 on measured need) | Measured from real workload | Sized per SLOs |
| Operational action | Simulated acknowledge, CMMS link | Read-only / shadow | Explicit human approval — never autonomous OT |
| Gate to exit | Defense passed | DPO, OT/ICS, security and RAI board sign-off | Conformity assessment on any high-risk capability |

<!-- ⏱ 0:00 · Appendix slide. Three phases, and each boundary is a gate rather than a date. Phase 1 reads a single site and changes nothing. Only after the Data Protection Officer, the OT engineers, security, and the Responsible AI board sign off does any human-approved write-back reach a CMMS or MES — and never a setpoint. -->

---

<!-- _class: tight backup -->

# Appendix — Who Is Accountable

| Activity | CISO org | Platform admin | Data scientist | OT/ICS engineer | DPO | RAI board |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Entra & Conditional Access policy | A | **R** | I | I | C | I |
| Key Vault / customer-managed keys | C | **R/A** | I | I | I | I |
| Fabric & OneLake role administration | C | **R/A** | C | I | C | I |
| Purview classification and lineage | C | C | **R** | I | **A** | I |
| OT network segmentation | A | C | I | **R** | I | I |
| Model promotion to production | I | I | **R** | C | C | **A** |
| Agent tool-scope changes | C | **R** | **R** | I | I | **A** |
| Incident response command | **A** | **R** | I | R (OT) | C | I |
| Package feed policy | A | **R** | I | I | I | I |

<span class="pill gray">R responsible · A accountable · C consulted · I informed</span>

<!-- ⏱ 0:00 · Appendix slide. Governance only works if a name sits behind each control. Two rows matter most: model promotion and agent tool-scope changes are both accountable to the Responsible AI board, not to the team that wants to ship. OT network segmentation stays with the OT engineers, who can veto. -->

---

<!-- _class: tight backup -->

# Appendix — Service Levels & Incident Response

<div class="split">
<div>

| SLO | Target | Window |
|---|---|---|
| BFF-API availability | 99.5% | 30-day rolling |
| BFF-API p95 read latency | < 800 ms | 7-day |
| Alert delivery (SSE) | < 5 s | per incident |
| Data freshness (hot KQL) | < 5 s | continuous |
| Bronze→silver→gold reconciliation | 100% or explicit quarantine | per run |
| Optimizer response (cached fallback) | ≤ 5 s | per request |

</div>
<div>

| Severity | Example | Triage |
|---|---|---|
| **Sev-1** | Confirmed Highly Confidential breach; OT compromise | 15 min |
| **Sev-2** | Compromised identity; freshness stale > 60 s | 1 hour |
| **Sev-3** | Repeated prompt-injection attempts; quarantine spike | 4 hours |
| **Sev-4** | Policy drift; expired certificate | Next business day |

Burned error budget triggers a change freeze until root cause is addressed.

</div>
</div>

<!-- ⏱ 0:00 · Appendix slide. Availability, latency, freshness, and reconciliation are all measured with an error budget, and a burned budget freezes change until the root cause is fixed. Note that a data-freshness breach is a Sev-2 alongside a compromised identity — stale data on an advisory screen is a safety concern, not a cosmetic one. -->

---

<!-- _class: tight backup -->

# Appendix — Reproducible Demonstration Evidence

<div class="split">
<div>

**Expected values — one 24 h scenario, seed `240725`**

| Output | Expected |
|---|---|
| Energy-cost cut | −7.25% |
| Peak | 56.0 → 51.58 MW (−7.89%) |
| CO₂ | −3.29% |
| Planned tonnage | 960 t · zero violations |
| RUL P50 / P10 / P90 | 19.65 / 18.69 / 20.61 d |
| Risk · confidence | 0.90 · 0.78 (r² 0.88) |
| Quality what-if | ~88% → ~95% first-pass |

</div>
<div>

**Named scenarios**

`240727` energy spike · `240726` lining warning · `240728` quality drift · `240729` outage & recovery

**Five-level fallback ladder**

1. Cloud live
2. Local deterministic replay
3. Cached interactive
4. Recorded 90-second flow
5. Static proof pack — screenshots, JSON, transcripts

</div>
</div>

<!-- ⏱ 0:00 · Appendix slide. Every number I quote on stage is pinned to a seed and reproducible bit-for-bit, so you can regenerate the run yourself. If the live environment misbehaves, there are five rehearsed fallback levels down to a static proof pack, and I will always tell you which level you are watching. -->

---

<!-- _class: tight backup -->

# Appendix — Reusing the NovaSteel Pattern for Glass Plants

<div class="split">
<div>

**What stays the same (high reuse)**

- Same two-stream data foundation: hot telemetry + governed history in Fabric
- Same portal pattern: Blazor shell + React MFE + Power BI personas
- Same compute pattern: Python scoring/optimizer workers + append-only audit
- Same governance baseline: EU residency, managed identity, RAI gates, human approval

**What changes for glass**

- Asset model: furnaces, forehearth, lehr, forming lines
- KPIs: kWh/ton glass, pull-rate stability, cullet ratio, defect ppm
- Feature set: melt profile, viscosity proxies, annealing curve, vision defects

</div>
<div>

| Steel capability | Glass equivalent |
|---|---|
| Lining RUL | Refractory campaign and forehearth wear forecasting |
| Energy dispatch | Electric boosting + batch timing optimization |
| In-line quality risk | Bubble/cord/thickness/optical defect risk |
| Knowledge capture | Shift handover + troubleshooting playbooks |

<span class="pill blue">REUSE</span> Platform and controls stay; process models and KPIs are swapped to glass physics.

</div>
</div>

<!-- ⏱ 0:00 · Appendix slide. The point is reuse by architecture pattern: keep the governed data core, deterministic compute, portal experience and control framework, then swap only industry semantics — assets, KPIs and physics features. For glass the same blueprint supports forehearth wear, pull-rate stability, energy dispatch, and defect prevention without redesigning the platform. -->

---

<!-- _class: tight backup -->

# Appendix — Why We Do Not Write to the Furnace

<div class="split">
<div>

**Design choice, not missing feature**

- Furnace setpoints and interlocks remain in OT safety layers (Purdue L0-L2)
- Cloud-to-OT direct actuation would cross the IEC 62443 boundary by design
- With synthetic data, we cannot evidence high-risk control duties to production standard

</div>
<div>

**What the platform writes today**

- Approved dispatch decisions
- CMMS work orders from lining alerts
- Approved knowledge procedures
- Append-only, hash-chained audit facts

<span class="pill green">SAFETY</span> The platform advises and records decisions; OT control systems stay authoritative.

</div>
</div>

<!-- ⏱ 0:00 · Appendix slide. This is an intentional safety boundary. We automate decision quality and traceability, but direct furnace actuation stays with existing OT control and safety systems. -->

---

<!-- _class: tight backup -->

# Appendix — Why Not Azure IoT Hub — or IoT Operations?

<div class="split">
<div>

**Current baseline (this solution)**

- Event Hubs + identity relay + Fabric Eventstream
- Optimized for analytics ingestion, governance, and deterministic replay
- Lowest integration overhead for the current advisory-only scope

</div>
<div>

**When IoT Hub / IoT Operations becomes the right choice**

- Need bidirectional device command and control loops
- Need edge-native protocol mediation and local autonomy
- Need fleet operations with device twins, jobs, and lifecycle orchestration

Today they are roadmap capabilities, not required for the validated MVP boundary.

</div>
</div>

<!-- ⏱ 0:00 · Appendix slide. We did not reject IoT Hub or IoT Operations as bad options; we deferred them because this release is advisory-first and analytics-centric. They become first-class in vNext closed-loop control. -->

---

<!-- _class: diagram rti-diagram backup -->

# Appendix — Fabric RTI

![Fabric Real-Time Intelligence architecture](images/fabric-rti-diagram.webp)

<!-- ⏱ 0:00 · Appendix slide. This diagram isolates the Fabric Real-Time Intelligence path from streaming ingestion through Eventstream and Eventhouse to operational analytics, alerting, and downstream governed storage. -->
