# NovaSteel — Personas & User Journeys

> **Source of truth:** `docs\usecase\usecase.md`
> **Companion document:** `docs\specs\solution-requirements.md` (functional/non-functional requirements, KPI catalog, traceability matrix)
> **Status:** Aligned v1.1
> **Owner:** Business Specification workstream (`business-spec`)
> **Note:** Detailed dashboard visual design belongs to `ux-spec`; RBAC control implementation belongs to `security-spec`. This document defines role goals, pains, decisions, permissions (business-level), key screens (by name/purpose, not pixel design), and journeys — including the binding 10-minute demo storyboard used in the 1-hour defense.

---

## 1. How to Read This Document

Ten personas represent the full decision-making surface of the NovaSteel platform. For each persona:

- **Profile** — role, scope, a representative name/quote for the defense narrative.
- **Goals** — what "good" looks like for this role.
- **Pains** — current-state frustrations the platform must address.
- **Permissions** — business-level access (detailed RBAC matrix is owned by `security-spec`; this is the input to it).
- **Key decisions** — the decisions this persona makes using the platform.
- **Key screens** — the cockpit(s)/views this persona relies on.
- **Primary KPIs** — cross-referenced to `docs\specs\solution-requirements.md` §13.
- **User journey** — a realistic day/week-in-the-life narrative.
- **Demo moment** — which of the six demo moments (`DM-1`…`DM-6`, see §10) feature this persona.

A cross-persona RACI-style summary and the full 10-minute demo storyboard for the 1-hour defense appear in §9–§10.

---

## 1a. The AxelorMetal Cast

Every persona has a name. This is not decoration: an unnamed "Plant Manager" is
an abstraction a jury forgets, whereas *Marc Weber, who needs to know by 06:40
whether today is a good day*, is a person whose problem the platform either
solves or does not. Naming also makes the demo narration concrete — the
presenter says what Elena does next, not what "the operator persona" does next.

These names are **binding across the whole solution**. They appear in the
portal's section headers (`apps\analytics-mfe\src\personaRoutes.ts`), in the
Copilot Chat suggested questions, and in the defense deck. Changing a name here
means changing it in the code.

| Name | Role | Scope | Persona ID |
|---|---|---|---|
| **Marc Weber** | Plant Manager | Site | `plant-manager` |
| **Elena Duarte** | Furnace Operator | Shift / asset | `furnace-operator` |
| **Sofia Lindqvist** | Energy Manager | Site / portfolio | `energy-manager` |
| **Tomás Rossi** | Maintenance & Reliability Engineer | Asset / site | `maintenance-engineer` |
| **Jens Bakker** | Quality Engineer | Product / site | `quality-engineer` |
| **Amina Haddad** | Sustainability Officer | Portfolio | `sustainability-officer` |
| **Pieter Claes** | Knowledge Engineer / Admin | Platform-wide | `knowledge-engineer` |
| **Isabelle Moreau** | Executive (COO) | Enterprise | `executive` |
| **Rui Almeida** | OT Systems Engineer | Plant floor / edge | `ot-systems-engineer` |
| **Nils Andersen** | Platform Ops | Cloud platform | `platform-ops` |

The first eight are the decision-making personas documented in full in §2–§9.
**Rui Almeida** and **Nils Andersen** are supporting technical roles: they do not
make production trade-offs, but they own the two surfaces without which nothing
else works — the sensor fleet and the cloud platform. They are profiled briefly
in §9a.

Nationalities are spread across the sites AxelorMetal operates (Luxembourg,
Belgium, Germany, Sweden) to keep the fiction internally consistent with a
European multi-site group.

---

## 2. Persona: Marc Weber — Plant Manager

**Profile**: Site director accountable for safety, production output, cost, and quality at one integrated site (e.g., the Luxembourg home site). Represents operations leadership in the defense narrative. *"I need one screen that tells me if today is a good day — and why, if it isn't."*

**Goals**
- Hit production and cost targets without compromising safety.
- Minimize unplanned downtime, especially catastrophic furnace events.
- Maintain visibility across energy, quality, and asset-health simultaneously — not in silos.
- Build confidence in AI recommendations across the site's teams.

**Pains**
- Fragmented reporting: energy, quality, and maintenance data live in different systems and spreadsheets.
- Reactive management — finds out about problems (quality claims, near-miss lining issues) after the fact.
- Difficulty justifying capital/process changes without clear before/after evidence.
- Uncertainty about which AI recommendations are safe to trust.

**Permissions**
- Full read access to all site-level KPIs and cockpits (energy, furnace, quality, knowledge library, audit trail summaries).
- Approval authority for documented cross-domain trade-offs escalated by other roles (for example, “delay reline versus accept risk”); any production schedule connector remains outside the demonstration and pilot platform.
- Cannot directly override safety interlocks or bypass required human-approval gates (FR-GOV-05).
- Can escalate to Executive for cross-site or capital decisions.

**Key decisions**
- Approve or defer a furnace lining reline based on RUL alert and production calendar.
- Approve the documented business decision for an energy recommendation; the demonstration and pilot phases record that decision without writing a schedule.
- Approve corrective action plans for recurring quality deviations.
- Decide when to escalate an AI Act / governance concern (FR-GOV-05 flag) upward.

**Key screens**
- **Site Command Center Cockpit** — single-pane rollup of energy, CO₂, furnace health, quality, and open alerts for the site (FR-PLT-02, FR-PLT-03).
- **Cross-Domain Alert Queue** — all open, unresolved AI-generated alerts across domains needing management attention.

**Primary KPIs**: KPI-ADO-01, KPI-TRUST-01, plus rollups of KPI-ENE-01, KPI-CO2-01, KPI-FUR-01, KPI-QUA-01 at site level.

**User journey — "Monday morning site review"**
1. Opens the Site Command Center Cockpit before the daily production meeting; sees overnight AI alerts (one furnace RUL amber warning, one recorded energy decision, zero open quality flags).
2. Uses the natural-language copilot to ask "why did energy cost spike on the night shift?" and gets a rationale referencing a recorded-but-underperforming schedule recommendation.
3. Reviews the furnace RUL amber alert with the Maintenance/Reliability Engineer; approves a reline scheduling discussion given 24 days of lead time remaining.
4. In the weekly leadership sync, presents the site's energy/CO₂/yield trend against the four target outcomes, using AI-generated narrative summaries rather than manually built slides.
5. At month-end, reviews the audit trail summary to confirm all high-impact recommendations were properly reviewed and logged (FR-GOV-04) ahead of an internal compliance check.

**Demo moment**: DM-1 (portfolio/site command center), supporting role in DM-3 and DM-6.

---

## 3. Persona: Elena Duarte — Furnace Operator

**Profile**: Frontline/shift operator responsible for real-time, safe operation of the blast furnace. Represents the "veteran expertise at risk" narrative from the use case. *"I've run this furnace for 22 years — I know when something feels wrong before any sensor tells me."*

**Goals**
- Keep the furnace running safely and stably through the shift.
- Respond quickly and correctly to abnormal conditions.
- Meet shift production targets without cutting corners on safety.
- Pass on hard-won knowledge before retiring, in a way that's actually useful to less experienced colleagues.

**Pains**
- Alarm fatigue from raw sensor thresholds with no prioritization or context.
- Tacit knowledge ("what this particular furnace does when X happens") lives only in senior operators' heads.
- Limited advance warning of lining wear — historically only found out when it's urgent or too late.
- New operators have no fast way to find "how do I handle this specific situation" beyond asking someone who might not be on shift.

**Permissions**
- Read access to furnace health/thermal dashboards and the procedure library (search + read).
- Can acknowledge alerts, log shift observations, and contribute knowledge-capture interview sessions.
- Cannot modify model thresholds, approve energy schedule changes, or publish procedures unreviewed (publication requires Knowledge Engineer/Admin approval, FR-KNW-04).
- No override of safety-interlocked automated trips (O1 — outside platform scope; existing safety systems remain authoritative).

**Key decisions**
- Recommend or record an adjustment through the site's existing approved operating procedure; this platform never writes a burden, blast, furnace, or setpoint command.
- Decide when to escalate an abnormal thermal reading to the Maintenance/Reliability Engineer or Plant Manager.
- Decide what to log at shift handover for the next crew.

**Key screens**
- **Furnace Health & Thermal Signature Monitor** — live/near-live thermal trend view with plain-language alert context (not raw-only sensor values).
- **Shift Handover Log** — structured log of observations, actions taken, and open items.
- **Procedure Library Search** (mobile/tablet-friendly) — natural-language search over approved knowledge-capture content (FR-KNW-03).

**Primary KPIs**: KPI-FUR-01 (as the human recipient of lead-time alerts), KPI-KNW-02 (as a search user).

**User journey — "Mid-shift thermal anomaly"**
1. Shift start: reviews handover log and Furnace Health Monitor for any open items from the previous crew.
2. Mid-shift: a thermal sensor trend shifts subtly; the platform highlights it as a low-confidence early signal rather than a raw threshold breach.
3. Operator searches the procedure library ("unusual shell temperature rise, zone 3") and finds a structured procedure captured from a retired senior operator's interview, including the recommended check sequence and risk notes.
4. Follows the recommended check, resolves the anomaly as a sensor drift, not a real wear event, and logs the outcome.
5. At shift end, logs the event in the handover log; the event is fed back into the platform to potentially refine the RUL model's feature set (FR-FUR-06).
6. Separately, participates in a scheduled 30-minute GenAI knowledge-capture interview about a past near-miss they handled years ago, which the Knowledge Engineer/Admin later reviews and publishes as a new structured procedure.

**Demo moment**: DM-3 (furnace RUL, as the alert recipient), DM-5 (knowledge capture, as both interviewee and library searcher).

---

## 4. Persona: Sofia Lindqvist — Energy Manager

**Profile**: Site or portfolio-level manager accountable for energy cost, consumption, and procurement strategy across the 4-country footprint. *"Energy is 35% of our cost base — I need to act on price signals in hours, not renegotiate contracts once a year."*

**Goals**
- Minimize specific energy consumption and energy cost per ton (KPI-ENE-01).
- Exploit day-ahead/intraday price volatility without disrupting production.
- Support the portfolio's CO₂ reduction target through smarter scheduling.
- Build a defensible, auditable savings track record for finance.

**Pains**
- Scheduling energy-intensive processes is manual, spreadsheet-based, and disconnected from live market prices.
- No real-time link between production planning and energy markets across 4 countries with different price/grid dynamics.
- Difficult to prove savings attribution ("was that lower cost because of our schedule change, or just a low-price day?").

**Permissions**
- Read access to energy consumption, cost, and market-price data across all sites.
- Configure optimization guardrails/thresholds (FR-ENE-07) — subject to Plant Manager/Executive sign-off for major threshold changes.
- In the demonstration and pilot phases, review, simulate, or record approval/rejection of schedule recommendations (FR-ENE-05); rejections require a reason code and no platform action writes an operational schedule.
- Cannot unilaterally enable full autonomous execution without governance sign-off (C-04, AI-05).

**Key decisions**
- Approve, modify, or reject the documented recommendation; a real schedule write is a separately approved Phase 2+ connector, not a persona-tab action.
- Set risk/savings thresholds for human review and for a separately governed future connector; autonomous auto-apply is not a current platform capability.
- Decide when to escalate a schedule conflict (energy optimum vs. production plan) to the Plant Manager.

**Key screens**
- **Energy Dispatch Optimization Cockpit** — forecast demand, spot price curve, recommended schedule, expected €/CO₂ impact, accept/modify/reject controls (FR-ENE-01…05).
- **Spot Price & Load Forecast View** — 24–48h horizon chart across sites/countries.
- **Savings Ledger** — realized vs. forecast savings, audit-linked (FR-ENE-06, KPI-ENE-02).

**Primary KPIs**: KPI-ENE-01, KPI-ENE-02, KPI-ENE-03.

**User journey — "Day-ahead scheduling cycle"**
1. Early morning: reviews the Spot Price & Load Forecast View for the next 24–48h across all 4 sites.
2. Opens the Energy Dispatch Optimization Cockpit; the agent has already generated a recommended schedule shifting a rolling campaign to a lower-price overnight window, with expected savings of €X and CO₂ avoided of Y tons, and a plain-language rationale.
3. Runs a quick "what-if" simulation (FR-PLT-04) to check the impact of also shifting a second process, decides against it due to a production constraint flagged by the system.
4. Records a simulated/shadow approval of the primary recommendation; the decision and rationale are logged automatically (FR-GOV-01) without writing a scheduling system.
5. Midday: monitors intraday price deviation; no action needed as the schedule is holding.
6. Month-end: reviews the Savings Ledger with the CFO/Executive, using the auditable reconciliation between forecast and realized savings as the basis for the energy line of the ROI report.

**Demo moment**: DM-2 (primary), supporting role in DM-6 (ROI rollup).

---

## 5. Persona: Tomás Rossi — Maintenance & Reliability Engineer

**Profile**: Engineer accountable for asset health, reliability strategy, and maintenance planning for furnaces and critical rotating/refractory equipment. *"An €8M failure isn't a maintenance problem, it's a business continuity problem — I need weeks of warning, not hours."*

**Goals**
- Prevent catastrophic, unplanned furnace lining failures.
- Shift from reactive/calendar-based maintenance to predictive, condition-based maintenance.
- Optimize maintenance CAPEX/OPEX — reline exactly when needed, not too early or too late.
- Extend asset life through better understanding of wear drivers.

**Pains**
- No predictive signal for lining wear today — failures are effectively unpredicted (§2).
- Disconnected historian and CMMS data makes root-cause and RUL analysis slow and manual.
- Difficulty justifying a scheduled shutdown to production/plant leadership without strong predictive evidence.

**Permissions**
- Read access to furnace thermal data, RUL model outputs, confidence bands, and feature explainability (FR-FUR-01…04).
- Create or link a synthetic work-order record from an alert in the demonstration; any production CMMS connector is a separately approved Phase 2+ integration (FR-FUR-05).
- Configure sensor/alert thresholds within approved engineering limits.
- Provide model feedback (predicted vs. actual outcomes, FR-FUR-06) but does not directly retrain models (a Knowledge Engineer/Admin or MLOps function owns retraining pipelines).

**Key decisions**
- Recommend whether and when to schedule a lining reline based on RUL prediction and production-calendar constraints; the platform records the decision but does not control plant equipment.
- Decide whether an anomalous reading warrants immediate escalation (safety-critical) vs. routine monitoring.
- Approve or reject the AI's suggested maintenance window.

**Key screens**
- **Furnace Lining RUL Dashboard** — current RUL estimate, trend, confidence band, top contributing thermal features (FR-FUR-02…04).
- **Work Order Integration Panel** — create/link the synthetic work-order record from an alert; production CMMS integration remains gated (FR-FUR-05).
- **Model Confidence & Explainability View** — feature attribution and historical prediction-vs-actual accuracy (KPI-FUR-03).

**Primary KPIs**: KPI-FUR-01, KPI-FUR-02, KPI-FUR-03.

**User journey — "21-day advance warning"**
1. Receives an automated alert: predicted RUL for Furnace 2 lining has dropped below the warning threshold, with an estimated 24 days of remaining life and a 90% confidence band of ±4 days.
2. Opens the RUL Dashboard, reviews the top contributing thermal features (localized hot-spot trend in one shell zone) and compares against the explainability view.
3. Cross-checks against the last physical inspection report and confirms the trend is consistent with known wear patterns.
4. Uses "what-if" simulation to compare reline timing options against the production calendar (FR-PLT-04).
5. Creates a synthetic CMMS-linked work-order record from the alert, proposing a day-18 reline window (buffer before the predicted day-24 threshold), and notifies the Plant Manager for approval. No plant-control or production-connector write occurs in the platform.
6. After the reline, logs the actual outcome; the platform compares predicted vs. actual RUL to refine future model confidence reporting (FR-FUR-06, KPI-FUR-03).

**Demo moment**: DM-3 (primary).

---

## 6. Persona: Jens Bakker — Quality Engineer

**Profile**: Metallurgist/quality engineer responsible for ensuring steel grades — especially automotive-grade — meet specification, with full traceability for OEM customers. *"Our automotive customers don't just want good steel, they want proof it was good, heat by heat."*

**Goals**
- Reduce downgrades and customer claims for high-grade steel.
- Catch quality risk in-line, before a heat/coil completes, rather than after lab results return.
- Speed up root-cause analysis when a deviation occurs.
- Maintain complete genealogy/traceability for customer audits.

**Pains**
- Lab results lag production, so corrective action often comes too late for the current batch.
- Root-cause investigation today is manual, spanning multiple systems and tribal knowledge of "what usually causes this."
- Customer claims and audits require assembling traceability data manually from disparate sources.

**Permissions**
- Read access to in-line quality predictions, genealogy data, and the root-cause copilot (FR-QUA-01…04).
- Authority to quarantine a suspect batch or flag a heat for hold pending review.
- Approve/reject corrective action plans for a given deviation.
- Cannot alter genealogy/traceability records (audit-protected, FR-QUA-04) — can only append investigation notes.

**Key decisions**
- Recommend a bounded process adjustment and escalate it through the existing approved plant procedure; the platform does not write a recipe or setpoint.
- Decide whether to quarantine, downgrade, or release a batch flagged as at-risk.
- Approve corrective action documentation for a customer-facing non-conformance.

**Key screens**
- **In-line Quality Prediction Dashboard** — live risk score per active heat/coil against automotive-grade spec (FR-QUA-01).
- **Batch Genealogy & Root-Cause Copilot** — traces a deviation back through upstream process/asset history with AI-suggested likely contributors (FR-QUA-03).
- **Customer Claims Tracker** — non-conformances and claims linked to predicted-risk flags (FR-QUA-05).

**Primary KPIs**: KPI-QUA-01, KPI-QUA-02.

**User journey — "Catching a deviation before it ships"**
1. Mid-production: the In-line Quality Prediction Dashboard flags an active heat as trending toward a 15% risk of missing automotive-grade spec, driven by a chemistry parameter drift.
2. Opens the recommended corrective action, records the bounded what-if, and escalates it through the existing approved plant procedure before the heat completes (FR-QUA-02).
3. The heat completes within spec; the independently executed plant intervention and outcome are logged for future model calibration.
4. Separately, a customer claim arrives for an earlier shipment; uses the Batch Genealogy & Root-Cause Copilot to trace the deviation to a specific upstream process window, identifying a likely contributing furnace condition.
5. Documents the corrective action and root cause for the customer's quality audit, using the platform's genealogy export as supporting evidence (FR-QUA-04).
6. Reviews monthly claims trend against predicted-risk flags to assess model precision/recall and refine thresholds with the Knowledge Engineer/Admin.

**Demo moment**: DM-4 (primary).

---

## 7. Persona: Amina Haddad — Sustainability Officer

**Profile**: ESG/environmental manager accountable for CO₂ performance, EU ETS exposure management, and regulatory/ESG reporting across the 4-country portfolio. *"Our carbon cost is becoming as material as our energy cost — and right now I find out about it a month late."*

**Goals**
- Meet the portfolio's 22% CO₂ reduction target (KPI-CO2-01).
- Manage and forecast EU ETS allowance cost exposure (KPI-CO2-02).
- Produce timely, accurate ESG/regulatory reports.
- Connect emissions performance back to specific operational decisions (e.g., energy dispatch choices).

**Pains**
- Emissions calculation today is manual, delayed, and disconnected from day-to-day operational decisions.
- No early warning of trajectory risk toward exceeding free allowance allocations.
- Board/regulator reporting requires manually assembling data from multiple sites and systems.

**Permissions**
- Read access to CO₂ and energy KPIs across all sites (roll-up and drill-down, FR-PLT-05).
- Generate regulator/board-ready reports (FR-GOV-04).
- No direct operational control (cannot change schedules or process parameters) — influences via reporting and escalation to Plant Manager/Executive.

**Key decisions**
- Decide when to escalate a site's emissions trajectory risk to the Plant Manager or Executive.
- Decide what goes into quarterly/annual regulatory and ESG disclosures.

**Key screens**
- **Sustainability & ETS Cockpit** — CO₂ trend vs. target, allowance exposure forecast, portfolio drill-down (FR-PLT-05, KPI-CO2-01/02).
- **Emissions Driver View** — links emissions trend to operational drivers (e.g., energy schedule decisions, process mix).
- **Regulatory Report Generator** — exports audit-ready ESG/compliance reports (FR-GOV-04).

**Primary KPIs**: KPI-CO2-01, KPI-CO2-02.

**User journey — "Monthly ETS exposure review"**
1. Opens the Sustainability & ETS Cockpit; portfolio CO₂/ton is tracking at −18% vs. baseline, short of the −22% target, with one site lagging.
2. Drills down to the lagging site and uses the Emissions Driver View to see that a lower-than-usual acceptance rate of energy dispatch recommendations at that site is a contributing factor.
3. Flags the finding to that site's Plant Manager and Energy Manager, recommending a review of rejected recommendations' reason codes.
4. Forecasts ETS allowance exposure for the quarter using KPI-CO2-02 and prepares a board-ready summary via the Regulatory Report Generator.
5. Presents the trajectory and mitigation plan at the quarterly leadership review, alongside the Executive.

**Demo moment**: DM-6 (primary).

---

## 8. Persona: Pieter Claes — Knowledge Engineer / Admin

**Profile**: Knowledge-management owner responsible for the GenAI knowledge-capture program, procedure-library governance, scoped role-assignment requests, and model/audit oversight. *"If we don't capture what our retiring experts know in a structured way, we lose it forever — and if we capture it carelessly, we risk publishing something unsafe."*

**Goals**
- Capture critical tacit knowledge from experienced operators before they retire.
- Maintain an accurate, trustworthy, well-governed procedure library.
- Steward application-role requests and model-governance evidence while the Platform Admin retains infrastructure administration.
- Ensure GenAI outputs are reviewed and safe before publication.

**Pains**
- Valuable knowledge is scattered, undocumented, or trapped in individuals' heads.
- Risk of publishing incorrect or unsafe "knowledge" if GenAI output isn't properly reviewed.
- Platform administration (users, permissions, model governance) is a full-time governance burden without the right tooling.

**Permissions**
- Application-level knowledge-governance access: review queues, publication approval, and scoped role-assignment requests. Azure/Fabric/Key Vault administration remains a separate PIM-controlled Platform Admin responsibility.
- Approve or reject structured procedures before publication (FR-KNW-04) — the only role with publish authority.
- Access to the audit log, model registry, and drift-monitoring telemetry (FR-GOV-01…04, NFR-OBS-01).
- Request and review application-role assignments for other personas; the Platform Admin enforces underlying platform controls.

**Key decisions**
- Approve, edit, or reject each GenAI-structured procedure before it goes live.
- Prioritize which experts/topics to interview next based on the coverage/gap report (FR-KNW-06).
- Decide when a model shows enough drift to require retraining/recalibration review (AI-06).
- Provide retention/redaction requirements for interview content; DPO/Legal approves the governing GDPR decision (FR-KNW-07).

**Key screens**
- **GenAI Knowledge Capture Studio** — conducts/manages interview sessions with operators (FR-KNW-01).
- **Procedure Library CMS & Approval Queue** — review, edit, version, publish structured procedures (FR-KNW-02, 04, 05).
- **Admin/Governance Console** — audit logs, model registry/model cards, RBAC configuration, drift telemetry (FR-GOV-01…03, NFR-OBS-01).
- **Coverage/Gap Report** — critical topics not yet documented (FR-KNW-06).

**Primary KPIs**: KPI-KNW-01, KPI-KNW-02, KPI-GOV-01.

**User journey — "From retiring expert to searchable procedure"**
1. Reviews the Coverage/Gap Report; identifies that "blast furnace tuyere-level abnormal condition response" is a critical topic with no documented procedure, held only by a furnace operator retiring in 3 months.
2. Schedules a GenAI-facilitated interview session via the Knowledge Capture Studio; the agent conducts a structured conversational interview, eliciting the trigger conditions, recommended actions, and risk notes.
3. Reviews the GenAI-structured output in the Approval Queue, edits a phrase for precision, and confirms it matches the operator's intent (validated with the operator).
4. Approves and publishes the procedure to the library, versioned and citation-linked to the source interview (FR-KNW-04, 05).
5. Monitors the Admin/Governance Console for the week; confirms 100% audit completeness (KPI-GOV-01) across all AI recommendations issued platform-wide, and reviews model drift telemetry for the furnace RUL model, finding it within normal bounds.
6. Requests and reviews a routine application-role assignment for a new Quality Engineer; the PIM-controlled Platform Admin implements any underlying platform-role change.

**Demo moment**: DM-5 (primary), supporting role in DM-6 (audit trail).

---

## 9. Persona: Isabelle Moreau — Executive (COO)

**Profile**: Senior leadership accountable for enterprise strategy, capital allocation, and board/investor reporting across the full 4-country portfolio. *"I need to know this platform is making us money and reducing our risk — in one page, with numbers I can defend to the board."*

**Goals**
- Demonstrate measurable ROI on the AI platform investment.
- Reduce financial exposure to energy cost, carbon cost, and catastrophic failure risk.
- Maintain competitiveness with automotive customers on quality and traceability.
- Make informed go/no-go decisions on scaling the platform (Phase 1 → 2 → 3, see solution-requirements §18).

**Pains**
- No unified, trustworthy, cross-site view of AI-driven value today.
- Difficulty quantifying "what would have happened without this" for ROI justification.
- Board and investor reporting is time-consuming to assemble from fragmented sources.

**Permissions**
- Read-only access to executive/portfolio dashboards across all sites and countries.
- No direct operational access (does not accept/reject recommendations, does not configure models).
- Approves capital/scope decisions for phase progression (Phase 1 → 2 → 3) based on presented evidence.

**Key decisions**
- Approve continued investment/scale-up of the platform beyond the pilot (Phase 1 → Phase 2 → Phase 3).
- Represent platform outcomes to the board/investors and regulators as needed.
- Set enterprise risk appetite for AI autonomy levels (in coordination with governance/security).

**Key screens**
- **Executive Value & ROI Cockpit** — portfolio-wide KPI trend vs. the four target outcomes, savings ledger rollup, ROI summary (FR-PLT-05).
- **Multi-Country Benchmark View** — compares performance across Luxembourg, Germany, Belgium, and Spain sites.

**Primary KPIs**: All portfolio-level rollups — KPI-ENE-01/02, KPI-CO2-01/02, KPI-FUR-01/02, KPI-QUA-01/02, KPI-TRUST-01.

**User journey — "Quarterly board preparation"**
1. Opens the Executive Value & ROI Cockpit ahead of the board meeting; reviews portfolio trend against the four target outcomes (energy −14%, CO₂ −22%, lining lead time ≥21 days, yield +8%).
2. Uses the Multi-Country Benchmark View to identify the Spain site outperforming on yield and the Belgium site lagging on energy — flags for the Plant Manager's follow-up.
3. Reviews the audit completeness KPI (KPI-GOV-01) with the Knowledge Engineer/Admin to confirm governance readiness ahead of a potential regulator inquiry.
4. Reviews the Phase 1 pilot results and the Phase 2 business case (from `solution-requirements.md` §18) and approves scale-up funding.
5. Presents a one-page summary to the board, citing specific, auditable savings and risk-avoidance figures rather than estimates.

**Demo moment**: DM-1 (context), DM-6 (primary — ROI/value summary).

---

## 9a. Supporting Technical Personas

These two roles make no production trade-offs, so they do not carry the full
profile structure of §2–§9. They are documented because they own the two
surfaces the decision-making personas silently depend on, and because each has a
dedicated screen in the portal.

### 9a.1 Rui Almeida — OT Systems Engineer

**Profile**: Operational-technology engineer responsible for the sensor fleet on the plant floor — thermocouples, flow meters, vibration probes, gas analysers — and for the edge gateways that carry their readings into the platform. Based at the Luxembourg site, supports all four. *"Every number on your dashboard is a sensor I have to keep alive."*

**Goals**
- Keep every sensor reporting, calibrated and within its expected range.
- Detect a failing or drifting sensor before it corrupts a downstream decision.
- Onboard new tags without a change request cycle measured in weeks.

**Pains**
- A silently dead sensor looks exactly like a stable process until someone acts on the stale value.
- No single view of fleet health across sites; each plant has its own historian.
- Simulating a fault to test a response plan means waiting for a real one.

**Permissions**: Read across all telemetry; operate the device simulator; acknowledge and annotate device faults. **No** authority to approve production, energy or maintenance recommendations.

**Key decisions**
- Whether a suspect reading is a process excursion or an instrument fault — an important distinction, because the two demand opposite responses.
- When to take a sensor out of service and how to flag the resulting gap so downstream models do not treat it as signal.

**Key screens**: Device Operations (fleet table, per-sensor charts, simulator and incident controls).

**Why the platform matters to him**: the fleet view makes data quality a first-class, visible property rather than an assumption, and the incident simulator lets a response be rehearsed rather than improvised.

### 9a.2 Nils Andersen — Platform Ops

**Profile**: Cloud platform engineer accountable for the NovaSteel platform itself — the Container Apps, the Fabric capacity, cost, availability and the audit trail. Based in Sweden, near the Sweden Central region the platform runs in. *"The platform has to be cheap when nobody is looking and instant when somebody is."*

**Goals**
- Keep the platform inside its cost envelope, notably by keeping Fabric capacity paused outside demonstration and working hours.
- Keep data freshness, ingestion lag and service availability inside their thresholds, and be told by an alert rather than by a user.
- Be able to prove, after the fact, who approved what and on what evidence.

**Pains**
- Idle cloud capacity is pure cost, but a paused capacity that nobody can resume blocks the people who need it.
- Alerts that exist only as prose in a runbook are not alerts.
- Reconstructing an incident from unstructured logs.

**Permissions**: Operate platform infrastructure, including Fabric capacity pause/resume and SKU changes; read the audit log; **no** access to approve domain recommendations.

**Key decisions**
- When to resume or pause Fabric capacity, and at which SKU (F2/F4/F8) a given workload should run.
- Whether a degraded signal is a platform problem or a plant problem — the first question to answer in any incident.

**Key screens**: Platform Ops (capacity control, service health, cost posture, audit log).

**Why the platform matters to him**: capacity control is exposed in the product rather than requiring portal access, and the hash-chained audit log makes "who approved this" answerable rather than reconstructable.

---

## 10. The 15-Minute Demo Storyboard (1-Hour Defense)

This storyboard is the binding link between personas and the demo, matching `docs\specs\solution-requirements.md` §15/§19. It is designed to be reliably rehearsed, run on synthetic data only, and to fit the 1-hour defense allocation: 35-minute slides, 10-minute demo, and 15-minute FAQ.

| # | Moment | Time | Lead persona (voice) | Narrative beat | What's shown |
|---|---|---|---|---|---|
| **DM-1** | Portfolio Command Center | 0:00–2:00 | Plant Manager (Executive sets context) | "Here's AxelorMetal today — and here is how NovaSteel gives one view across energy, carbon, furnace health, and quality for all four sites." | Site/portfolio cockpit; natural-language copilot answers a live question; four target outcomes shown as baseline→target→current. |
| **DM-2** | Energy Dispatch Optimization | 2:00–4:30 | Energy Manager | "Electricity prices swing hourly — our agent turns that volatility into savings, safely." | Spot price/load forecast, AI-recommended schedule with € and CO₂ impact, simulated/shadow approval, savings-ledger update. |
| **DM-3** | Furnace Lining RUL & Maintenance | 4:30–7:00 | Maintenance/Reliability Engineer (Furnace Operator cameo) | "A €8M failure, 21 days before it happens, not after." | RUL dashboard with confidence band and contributing features, alert-to-synthetic-work-order flow. |
| **DM-4** | In-line Quality Prediction & Root Cause | 7:00–9:30 | Quality Engineer | "We catch the automotive-grade risk while the heat is still running, not after the customer complains." | Live risk score on an active heat, corrective-action recommendation, root-cause copilot tracing a past claim. |
| **DM-5** | GenAI Knowledge Capture & Search | 9:30–12:00 | Knowledge Engineer/Admin (Furnace Operator cameo) | "We capture 22 years of expertise before it walks out the door — and make it searchable in seconds." | Interview snippet → GenAI structuring → reviewer approval → natural-language search returning a cited procedure. |
| **DM-6** | Sustainability, ROI & Audit Trail | 12:00–14:00 | Sustainability Officer & Executive | "Every one of those recommendations is fully auditable — and here's what it's worth." | ETS/CO₂ cockpit, portfolio ROI rollup against the four target outcomes, one-click audit trail for a prior recommendation (KPI-GOV-01 = 100%). |
| — | Buffer/transition | 14:00–15:00 | — | Smooth handoffs between presenters/screens. | — |

**Reliability notes** (binding, see `solution-requirements.md` NFR-AVAIL-02, AC-01/AC-04): the demo must run entirely on synthetic/cached data with no live external dependency, must be rehearsed at least twice end-to-end, and must have a recorded-video fallback ready in case of live failure during the defense.

### 10.1 Fitting the 1-Hour Defense

The demo above is nested inside the 60-minute agenda defined in `solution-requirements.md` §19.2 (**35-minute slides → 10-minute demo → 15-minute FAQ**). Presenters should map to personas where possible (e.g., whoever narrates DM-2 should consistently "be" the Energy Manager voice) so the audience experiences a coherent role-based story rather than a feature tour.

---

## 11. Cross-Persona Summary Table

| Persona | Scope | Primary decision | Primary screen | Demo moment |
|---|---|---|---|---|
| **Marc Weber** — Plant Manager | Site | Approve cross-domain trade-offs | Site Command Center Cockpit | DM-1, DM-3, DM-6 |
| **Elena Duarte** — Furnace Operator | Shift/asset | React to furnace alerts within limits | Furnace Health Monitor / Procedure Library | DM-3, DM-5 |
| **Sofia Lindqvist** — Energy Manager | Site/portfolio | Accept/reject dispatch recommendations | Energy Dispatch Optimization Cockpit | DM-2 |
| **Tomás Rossi** — Maintenance & Reliability Engineer | Asset/site | Schedule reline based on RUL | Furnace Lining RUL Dashboard | DM-3 |
| **Jens Bakker** — Quality Engineer | Product/site | Adjust process on quality risk | In-line Quality Prediction Dashboard | DM-4 |
| **Amina Haddad** — Sustainability Officer | Portfolio | Escalate emissions trajectory risk | Sustainability & ETS Cockpit | DM-6 |
| **Pieter Claes** — Knowledge Engineer/Admin | Platform-wide | Approve/publish procedures; govern platform | GenAI Knowledge Capture Studio / Admin Console | DM-5, DM-6 |
| **Isabelle Moreau** — Executive | Enterprise | Approve phase scale-up investment | Executive Value & ROI Cockpit | DM-1, DM-6 |
| **Rui Almeida** — OT Systems Engineer | Plant floor/edge | Distinguish instrument fault from process excursion | Device Operations | — |
| **Nils Andersen** — Platform Ops | Cloud platform | Resume/pause Fabric capacity and set SKU | Platform Ops | — |

---

## 12. Change Log

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-07-25 | Initial persona and journey set derived from `docs\usecase\usecase.md`, aligned to `docs\specs\solution-requirements.md`. |
| v1.1 | 2026-07-26 | Named every persona (§1a, "The AxelorMetal Cast") and carried the names into the section headings and the cross-persona table. Added §9a for the two supporting technical personas, Rui Almeida (OT Systems Engineer) and Nils Andersen (Platform Ops), each of which now has a dedicated screen in the portal. Names are binding and mirrored in `apps\analytics-mfe\src\personaRoutes.ts`. |
