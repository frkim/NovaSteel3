# NovaSteel — Solution Requirements Specification

> **Source of truth:** `docs\usecase\usecase.md`
> **Companion document:** `docs\personas\personas-and-journeys.md`
> **Status:** Draft v1.0 — implementation-ready business specification
> **Owner:** Business Specification workstream (`business-spec`)
> **Out of bounds for this document:** detailed system architecture (`solution-architecture`), synthetic dataset design (`data-demo-spec`), UI/visual design system (`ux-spec`), security/governance control catalog (`security-spec`). This document defines *what* must be true and *why*; those workstreams define *how*.

---

## 0. Document Control

| Field | Value |
|---|---|
| Program | NovaSteel — AI-Powered Steel Production Optimization Platform |
| Industry | Heavy Industry & Metals (integrated steel: blast furnace + rolling mills) |
| Sites in scope | Luxembourg (HQ), Germany, Belgium, Spain |
| Regulatory context | GDPR, EU AI Act, sector-specific EU directives (EU ETS, Industrial Emissions Directive) |
| Presentation format constraint | 1-hour defense: 35-minute slides, 10-minute live demo, 15-minute FAQ (see §19) |
| Revision | v1.0 |

---

## 1. Purpose & Reading Guide

This specification translates the NovaSteel use case into an implementation-ready set of business and solution requirements. It is the contract that the architecture, data/demo, UX, and security workstreams must satisfy, and the basis on which the 1-hour defense and 10-minute demo are scripted and judged.

Requirement IDs use the pattern `FR-<AREA>-<NN>` (functional) and `NFR-<AREA>-<NN>` (non-functional). KPIs use `KPI-<AREA>-<NN>`. All IDs are stable identifiers — do not renumber; append new IDs at the end of a group if scope grows.

---

## 2. Problem Statement

AxelorMetal is a Luxembourg-headquartered integrated steel producer operating blast furnaces and rolling mills across four countries (Luxembourg, Germany, Belgium, Spain). The business is structurally exposed on five fronts:

1. **Energy cost exposure** — energy represents **35% of total production cost**, priced and consumed with no real-time optimization against volatile day-ahead/intraday electricity markets.
2. **Carbon cost exposure** — CO₂ emissions are under mounting financial pressure from EU Emissions Trading System (ETS) allowance costs and penalties, with no predictive linkage between operational decisions and emissions/allowance impact.
3. **Catastrophic, unpredictable asset failure** — blast furnace lining wear cannot currently be predicted; a lining failure event costs **€8M per occurrence** in repair, lost production, and safety risk.
4. **Quality inconsistency** — variability in high-grade steel (notably automotive-grade) causes downgrades, claims, and lost premium revenue with customers who apply strict specification and traceability requirements.
5. **Disappearing operational expertise** — experienced furnace and process operators are retiring faster than their tacit knowledge (heuristics, "how we really run this furnace") can be captured, documented, or transferred.

These are not independent problems: energy, quality, and asset‑health decisions are made by different roles, on different systems, with no shared real-time picture — and the people who best understand the trade-offs are leaving the workforce. AxelorMetal needs NovaSteel: a single AI-powered platform that senses, predicts, recommends, and explains across these four dimensions, with humans retaining control of safety- and cost-critical decisions.

---

## 3. Business Context

- **Industry**: Heavy Industry & Metals — integrated steelmaking (blast furnace / BOF route) plus downstream rolling.
- **Footprint**: 4 sites across Luxembourg (HQ + primary ironmaking/steelmaking), Germany, Belgium, Spain (rolling/finishing and/or additional melting capacity). *Site names used in personas/demo materials are illustrative, not real facilities.*
- **Regulatory context**: GDPR (personal data of employees/operators, especially voice/video interviews for knowledge capture), EU AI Act (risk classification of AI systems touching safety, employment, and critical infrastructure), EU ETS (carbon allowance trading), sector directives (Industrial Emissions Directive, machinery/functional-safety norms for furnace operation).
- **Customer context**: automotive OEMs and tier-1 suppliers demanding high-grade steel with tight specification tolerance, full genealogy/traceability, and low variability.

---

## 4. Transformation Objective & Target Outcomes

**Objective**: Implement an AI-driven production optimization platform that reduces energy consumption, predicts equipment failures, improves steel quality, and captures/structures operational expertise before it is lost.

### 4.1 Quantified Outcome Targets (from use case)

| # | Outcome | Target | KPI ID |
|---|---|---|---|
| 1 | Energy consumption per ton | **−14%** vs. baseline | KPI-ENE-01 |
| 2 | CO₂ emissions | **−22%** vs. baseline | KPI-CO2-01 |
| 3 | Furnace lining failure prediction | **21-day** advance warning | KPI-FUR-01 |
| 4 | High-grade steel yield | **+8%** vs. baseline | KPI-QUA-01 |

### 4.2 Illustrative Baseline Assumptions (for KPI modeling and synthetic demo data only)

> These figures are **not** disclosed in the use case and are not real AxelorMetal data. They are engineering-plausible baselines for an EU integrated BF-BOF route, provided so KPI formulas, dashboards, and synthetic datasets have concrete numbers to compute against. The `data-demo-spec` workstream owns final synthetic values; production values must be sourced from real historian/ERP data during discovery.

| Metric | Baseline (assumed) | Target (per use case %) |
|---|---|---|
| Specific energy consumption | 19.5 GJ / t crude steel | ≈16.8 GJ / t (−14%) |
| Specific CO₂ emissions | 2.10 t CO₂ / t crude steel | ≈1.64 t CO₂ / t (−22%) |
| Unplanned lining failure lead time | 0 days (failures are currently unpredicted) | ≥21 days advance warning |
| High-grade (automotive) first-pass yield | 90% of automotive-grade heats meeting spec first pass | ≈97% (+8% relative) |
| Cost of a lining failure event | €8,000,000 / event | Avoided via scheduled reline |
| Energy share of production cost | 35% | Reduced proportionally to KPI-ENE-01 |

---

## 5. Scope

### 5.1 In Scope

- **S1** — Energy dispatch optimization agent: forecasting and scheduling recommendations for energy-intensive processes against day-ahead/intraday electricity spot prices.
- **S2** — Physics-informed furnace lining degradation model: predicts remaining useful life (RUL) of blast furnace refractory lining from thermal signatures, targeting ≥21-day advance warning.
- **S3** — Quality prediction and root-cause assistance for high-grade (automotive) steel, linking process parameters to predicted grade/defect outcomes.
- **S4** — GenAI knowledge-capture system: structured interview agent that converts operator tacit knowledge into a searchable, versioned procedure library (RAG-based retrieval).
- **S5** — Cross-site, role-based dashboards and copilots for the 8 personas defined in `docs\personas\personas-and-journeys.md`.
- **S6** — Auditable recommendation-and-decision trail for every AI-generated recommendation (energy dispatch, maintenance, quality, knowledge content) and the human decision taken on it.
- **S7** — KPI/ESG reporting surface for EU ETS exposure and CO₂ trajectory, at site and portfolio (4-country) level.
- **S8** — A 10-minute, reliably repeatable demo built on synthetic data illustrating all four outcome areas end-to-end (see §19).

### 5.2 Out of Scope (explicitly, for this engagement/phase)

- **O1** — Direct, closed-loop (fully autonomous, no-human-in-the-loop) control of furnace operations or safety-interlocked equipment. All AI outputs are decision-support or guarded-recommendation in this phase; see §18 phasing for when supervised automation may be introduced.
- **O2** — Physical instrumentation retrofit or procurement of new furnace sensors/hardware. The platform assumes sensor data feeds exist or are simulated; sensor installation is a separate capital project.
- **O3** — Direct participation in EU ETS allowance trading/transactions (the platform reports/forecasts exposure; it does not execute trades).
- **O4** — Replacement of existing MES/ERP/CMMS systems of record — the platform integrates with and augments them, it does not replace them.
- **O5** — HR/workforce reduction decisions. Knowledge capture supports continuity, not headcount decisions.
- **O6** — Non-EU sites, non-steel product lines, or business units not named in the use case.
- **O7** — Real production data ingestion for this defense/demo — the demo runs on synthetic/simulated data only (see `data-demo-spec`); production data onboarding is a Phase 1+ activity (§18).

---

## 6. Assumptions & Dependencies

| ID | Assumption | Impact if invalid |
|---|---|---|
| A1 | Historian/OT data (thermal sensors, energy meters) is technically retrievable (via OPC-UA, historian export, or equivalent) even if not yet integrated. | FR-FUR/FR-ENE ingestion design must change; may require an edge gateway workstream. |
| A2 | Electricity spot/intraday price feeds (e.g., EPEX SPOT, ENTSO-E Transparency Platform, or national equivalents for LU/DE/BE/ES) are available as a licensed data feed. | Energy dispatch optimization degrades to day-ahead-only or requires a market-data vendor contract. |
| A3 | Operator interviews for knowledge capture involve personal data (voice/video) and require explicit consent and GDPR-compliant handling. | Legal/HR sign-off required before any real (non-synthetic) interview is recorded. |
| A4 | Baseline metrics in §4.2 are illustrative; real baselines will be established during discovery via a data audit of the last 12–24 months of historian/ERP data. | KPI targets in production must be re-baselined; demo KPI targets remain as stated for illustration. |
| A5 | The four target outcomes (§4.1) are portfolio-wide (all 4 sites), not per-site; site-level targets will be apportioned during rollout planning. | Reporting cadence and attribution logic must support roll-up and drill-down. |
| A6 | A furnace lining reline can be rescheduled with ≥21 days' notice without breaching other maintenance/production constraints. | RUL model usefulness is bounded by planning lead-time flexibility, not just model accuracy. |
| A7 | The 1-hour defense audience includes both business and technical evaluators; the 10-minute demo must be self-contained and not depend on live external services (spot price API, live sensors) for reliability. | Demo must run against a deterministic synthetic dataset with recorded fallback (video) — see §19. |
| A8 | The EU AI Act risk classification of these AI systems (furnace lining prediction touching safety, energy dispatch touching critical infrastructure) requires legal confirmation; this document assumes a "high-risk-adjacent" posture (human oversight, logging, transparency) pending formal classification. | If confirmed high-risk, additional conformity assessment, technical documentation, and post-market monitoring obligations apply (owned by `security-spec`). |

---

## 7. Personas & Stakeholders (Summary)

Eight personas are defined in detail in `docs\personas\personas-and-journeys.md`: **Plant Manager, Furnace Operator, Energy Manager, Maintenance/Reliability Engineer, Quality Engineer, Sustainability Officer, Knowledge Engineer/Admin, Executive**. Each functional requirement below references the persona(s) it primarily serves (`Primary user`) for traceability. Full goals, pains, permissions, decisions, screens, and journeys live in the companion document; this document does not duplicate them.

---

## 8. Functional Requirements

Legend: **Primary user** = persona(s) most responsible for acting on the requirement (see §7 / personas doc). **Demo** = demo moment reference from §15/§19 (`DM-1` … `DM-6`).

### 8.1 Energy Dispatch Optimization (FR-ENE)

| ID | Requirement | Primary user | Demo |
|---|---|---|---|
| FR-ENE-01 | The platform shall ingest day-ahead and intraday electricity spot price signals (and, where available, grid carbon-intensity signals) per site/country. | Energy Manager | DM-2 |
| FR-ENE-02 | The platform shall forecast energy demand of schedulable, energy-intensive processes (e.g., EAF melting, rolling campaigns) over a rolling 24–48h horizon. | Energy Manager | DM-2 |
| FR-ENE-03 | The platform shall generate a recommended process schedule that minimizes energy cost and/or emissions subject to production, safety, and contractual constraints (min/max run windows, maintenance blackout periods). | Energy Manager | DM-2 |
| FR-ENE-04 | Every schedule recommendation shall be presented with a plain-language rationale (expected € saved, expected CO₂ avoided, constraints considered) before any action is taken. | Energy Manager, Plant Manager | DM-2 |
| FR-ENE-05 | The Energy Manager shall be able to accept, modify, or reject a recommendation; rejections shall require a reason code. In the demonstration and pilot phases this is a simulated/shadow decision record, not an operational schedule write. | Energy Manager | DM-2 |
| FR-ENE-06 | The platform shall track realized savings (recommended vs. as-run) and reconcile against forecast, producing an auditable "savings ledger." | Energy Manager, Executive | DM-6 |
| FR-ENE-07 | The platform shall support configurable approval guardrails for future, separately approved write-back connectors. Through Phase 1, recommendations remain simulated or shadow-only; autonomous execution is out of scope (see O1, §18). | Energy Manager | — |

### 8.2 Furnace Lining Degradation Prediction (FR-FUR)

| ID | Requirement | Primary user | Demo |
|---|---|---|---|
| FR-FUR-01 | The platform shall ingest furnace thermal signature data (shell/refractory temperature profiles, thermocouple time series) at a frequency sufficient to detect trend changes relevant to lining wear. | Furnace Operator, Maintenance Engineer | DM-3 |
| FR-FUR-02 | The platform shall run a physics-informed ML model that estimates remaining useful life (RUL) of the furnace lining from thermal signatures. | Maintenance Engineer | DM-3 |
| FR-FUR-03 | The platform shall issue an advance-warning alert when predicted RUL falls below a configurable threshold, targeting ≥21 days of lead time before predicted failure. | Maintenance Engineer, Plant Manager | DM-3 |
| FR-FUR-04 | Each RUL prediction shall include a confidence/uncertainty band and the top contributing thermal features (explainability). | Maintenance Engineer | DM-3 |
| FR-FUR-05 | The platform shall allow the Maintenance/Reliability Engineer to create or link a synthetic work-order record from a lining-wear alert. A production CMMS connector is a separately approved Phase 2+ integration, never a direct OT/control action. | Maintenance Engineer | DM-3 |
| FR-FUR-06 | The platform shall track prediction-vs-actual outcomes (predicted RUL vs. observed reline/failure date) to support model monitoring and drift detection. | Maintenance Engineer, Knowledge Engineer/Admin | — |
| FR-FUR-07 | The platform shall escalate to the Plant Manager any alert indicating lead time below a safety-critical minimum threshold. | Plant Manager | — |

### 8.3 Quality Prediction & Root-Cause Assistance (FR-QUA)

| ID | Requirement | Primary user | Demo |
|---|---|---|---|
| FR-QUA-01 | The platform shall predict, in-line, the likelihood that an active heat/coil will meet high-grade (automotive) specification, using process and chemistry parameters. | Quality Engineer | DM-4 |
| FR-QUA-02 | When predicted quality risk exceeds a threshold, the platform shall recommend corrective process parameter adjustments before the batch completes. | Quality Engineer | DM-4 |
| FR-QUA-03 | The platform shall provide a root-cause analysis assistant that links a quality deviation to likely upstream process/asset contributors, using historical genealogy data. | Quality Engineer | DM-4 |
| FR-QUA-04 | The platform shall maintain batch/heat genealogy (inputs, process parameters, quality outcomes) sufficient for customer traceability requests (automotive OEM audits). | Quality Engineer | — |
| FR-QUA-05 | The platform shall track non-conformances and customer claims against predicted-risk flags to measure prediction precision/recall over time. | Quality Engineer, Knowledge Engineer/Admin | — |

### 8.4 GenAI Knowledge Capture (FR-KNW)

| ID | Requirement | Primary user | Demo |
|---|---|---|---|
| FR-KNW-01 | The platform shall provide a conversational GenAI agent that interviews operators (voice or text) to elicit tacit operational knowledge (heuristics, edge cases, "tribal knowledge"). | Knowledge Engineer/Admin, Furnace Operator | DM-5 |
| FR-KNW-02 | The platform shall transcribe and structure interview content into a standard procedure format (trigger condition → recommended action → rationale → risk notes). | Knowledge Engineer/Admin | DM-5 |
| FR-KNW-03 | Structured procedures shall be searchable via natural-language query (retrieval-augmented generation) by any authorized persona, with citation back to the source interview/expert. | All personas (read), Furnace Operator (primary) | DM-5 |
| FR-KNW-04 | A human expert/reviewer shall approve or reject each structured procedure before it is published to the searchable library (human-in-the-loop content governance). | Knowledge Engineer/Admin | DM-5 |
| FR-KNW-05 | The platform shall version procedures and retain a full edit/approval history. | Knowledge Engineer/Admin | — |
| FR-KNW-06 | The platform shall produce a coverage/gap report identifying operational topics/equipment not yet documented, to prioritize future interviews. | Knowledge Engineer/Admin | — |
| FR-KNW-07 | Operators providing interview content shall be informed of and able to exercise data-subject rights (consent, access, deletion) over their recorded contributions per GDPR. | Knowledge Engineer/Admin | — |
| FR-KNW-08 | The platform shall provide a grounded natural-language query endpoint over approved procedures only, declining to answer when no approved source is found, a content-policy violation is detected, or citation enforcement fails. | All (reader access) | DM-5 |

### 8.5 Cross-Cutting Platform & Reporting (FR-PLT)

| ID | Requirement | Primary user | Demo |
|---|---|---|---|
| FR-PLT-01 | The platform shall provide a unified data layer ingesting OT (sensor/historian) and IT (ERP/MES/CMMS/market) sources across all 4 sites/countries. | All (platform capability) | — |
| FR-PLT-02 | The platform shall provide role-based dashboards/cockpits tailored to each of the 8 personas, showing only KPIs and actions relevant to that role (least-privilege UX, aligned to RBAC). | All | DM-1 |
| FR-PLT-03 | The platform shall provide a natural-language copilot capable of answering cross-domain questions (e.g., "why did site X's energy cost spike yesterday?") by querying the unified data layer. | Plant Manager, Executive | DM-1 |
| FR-PLT-04 | The platform shall support "what-if" simulation (e.g., simulate energy schedule change, simulate reline timing) before a recommendation is committed. | Energy Manager, Maintenance Engineer | DM-2, DM-3 |
| FR-PLT-05 | The platform shall roll up site-level KPIs to a portfolio (4-country) view and allow drill-down from portfolio → site → line → asset. | Executive, Sustainability Officer | DM-6 |
| FR-PLT-06 | The platform shall generate notifications/alerts (email, Teams, or in-app) for threshold breaches, routed to the correct persona based on alert type. | All (as configured) | — |

### 8.6 Governance, Audit & Compliance (FR-GOV)

| ID | Requirement | Primary user | Demo |
|---|---|---|---|
| FR-GOV-01 | Every AI-generated recommendation shall be logged immutably with: inputs/features used, model identifier and version, output, confidence, timestamp, and the human decision (accept/modify/reject + reason). | Knowledge Engineer/Admin (platform admin), all decision-makers | DM-6 |
| FR-GOV-02 | Each production ML/GenAI model shall have a model card documenting purpose, training data lineage, performance metrics, known limitations, and intended use. | Knowledge Engineer/Admin | DM-6 |
| FR-GOV-03 | The platform shall support role-based access control (RBAC) aligned to the 8 personas, enforcing least-privilege read/write/approve permissions (detailed matrix owned by `security-spec`, referenced here for traceability). | Knowledge Engineer/Admin | — |
| FR-GOV-04 | The platform shall provide an auditor/regulator-ready export of decision logs and model documentation for a specified time range and site. | Sustainability Officer, Knowledge Engineer/Admin, Executive | DM-6 |
| FR-GOV-05 | The platform shall flag and route to a human reviewer any AI recommendation classified as high-risk (safety-adjacent or with financial impact above a configurable threshold) before execution. | Plant Manager, Maintenance Engineer | — |

### 8.7 Device Operations (FR-DEV)

| ID | Requirement | Primary user | Demo |
|---|---|---|---|
| FR-DEV-01 | The platform shall provide a real-time device fleet view showing health status, health score, and active incidents for all devices registered at a site. | Maintenance Engineer, Plant Manager, Furnace Operator | Optional device-ops beat |
| FR-DEV-02 | Device health status shall be derived from individual sensor alarm/warning states using an OT-standard approach-band rule that fires warnings before a value reaches its configured limit (not a naive outside-range check). | Maintenance Engineer | — |
| FR-DEV-03 | The platform shall provide a sensor explorer allowing filtering by device and status, with sortable/searchable table and per-sensor time-series chart. | Maintenance Engineer, Furnace Operator | Optional device-ops beat |
| FR-DEV-04 | The sensor time-series chart shall support line, area, bar, and control-chart display types; statistical descriptors (min/max/mean/std dev/last) over the visible window; zoom; live polling; and a WCAG 2.2 AA "View as table" fallback. | Maintenance Engineer | — |
| FR-DEV-05 | The platform shall expose a deterministic device simulator with a controlled state machine (stopped/running/paused) allowing authorized operators to start, pause, resume, stop, reset, change speed, and change scenario. | Platform Ops (`Platform.Capacity.Manage`) | Optional device-ops beat |
| FR-DEV-06 | The simulator shall support injection and early clearance of parameterised fault incidents (hearth lining degradation, cooling-water loss, sensor drift, sensor dropout, energy-price spike, quality drift, edge-outage-recovery) for live demonstration and operator training. | Platform Ops | Optional device-ops beat |
| FR-DEV-07 | The simulator shall run in-process inside the BFF to avoid an additional Container App deployment; a standalone out-of-process option shall also be available for teams requiring independent scaling. | Platform Ops / Platform Admin | — |

### 8.8 Privacy / GDPR Art. 17 (FR-PRI)

| ID | Requirement | Primary user | Demo |
|---|---|---|---|
| FR-PRI-01 | The platform shall implement GDPR Article 17 right-to-erasure requests, covering interview transcripts (hard delete), knowledge procedures (attribution pseudonymization, body retained under Art. 17(3)), Copilot conversations (hard delete), and audit chain (tombstone). | Compliance Auditor (`Compliance.Auditor`) | Optional compliance beat |
| FR-PRI-02 | Erasure execution shall be idempotent: repeated requests with the same `Idempotency-Key` shall return the original receipt without re-executing the erasure. | Compliance Auditor | — |
| FR-PRI-03 | The hash-chained audit log shall not be mutated by erasure; an `erasure.executed` tombstone shall be appended; `verify()` shall return `true` both before and after. | Compliance Auditor, Security Engineer | — |
| FR-PRI-04 | The raw `subjectId` shall be write-only and never echoed in any API response; receipts shall carry a salted SHA-256 pseudonym (`subjectPseudonym`) only. | Compliance Auditor | — |
| FR-PRI-05 | The grounded RAG query pipeline shall apply PII redaction (email, phone, IBAN, role-contextual person name, employee ID, IPv4, date of birth) to generated answers before returning them to callers. | All (reader access) | — |

---

## 9. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-PERF-01 | Performance | Furnace lining RUL inference shall complete within a time budget that supports at least daily re-scoring per furnace (near-real-time is a stretch goal, not an MVP requirement). |
| NFR-PERF-02 | Performance | Energy dispatch recommendations shall be available with enough lead time to act before day-ahead market gate-closure (site/country-specific). |
| NFR-PERF-03 | Performance | Dashboards shall load primary KPI views within industry-acceptable interactive latency for a live demo audience (target: perceptibly instant during the 10-minute demo). |
| NFR-AVAIL-01 | Availability | The platform's core dashboards and alerting shall target high availability commensurate with a production-monitoring tool (final SLO owned by `solution-architecture`). |
| NFR-AVAIL-02 | Resilience | The 10-minute demo shall not depend on live external services (spot-price API, live OT feed); it must run fully against synthetic/cached data with a recorded-video fallback. |
| NFR-SCALE-01 | Scalability | The data layer shall support 4 sites/countries today with a clear path to additional sites/lines without architectural rework. |
| NFR-SEC-01 | Security | All data in transit and at rest shall be encrypted; access shall be governed by RBAC and, for sensitive actions (e.g., accepting an energy dispatch recommendation with real financial impact), by an auditable approval step. |
| NFR-SEC-02 | Security | Personal data collected for knowledge capture (operator voice/video/text) shall be processed under documented GDPR lawful basis, with data minimization, retention limits, and data-subject rights support. |
| NFR-SEC-03 | Data residency | Data shall be stored and processed within the EU, consistent with GDPR and AxelorMetal's EU-only footprint. |
| NFR-COMP-01 | Compliance | AI systems in scope shall maintain the documentation and human-oversight controls needed to support an EU AI Act conformity determination (final control catalog owned by `security-spec`). |
| NFR-USAB-01 | Usability | Each persona's primary cockpit shall be usable by a non-technical operator/manager without training beyond a short onboarding session (aligned to `ux-spec`). |
| NFR-OBS-01 | Observability | All models shall emit monitoring telemetry (prediction volume, confidence distribution, drift indicators) reviewable by the Knowledge Engineer/Admin. |
| NFR-INTEROP-01 | Interoperability | OT integration shall support common industrial protocols/standards (e.g., OPC-UA) and IT integration shall support standard APIs/exports from ERP/MES/CMMS (final integration spec owned by `solution-architecture`). |
| NFR-MAINT-01 | Maintainability | Procedure library content and model configurations shall be version-controlled with rollback capability. |
| NFR-I18N-01 | Localization | The platform shall support the languages of the 4 operating countries (at minimum English as the working/demo language, with content structures that do not preclude French/German/Spanish/Luxembourgish localization). |

---

## 10. Data Requirements

### 10.1 Data Domains & Illustrative Sources

| Domain | Illustrative source | Used by |
|---|---|---|
| Furnace thermal/process sensors | Historian / OPC-UA / simulated time series | FR-FUR-* |
| Energy meters & consumption | Site energy management system / simulated | FR-ENE-* |
| Electricity market prices | Day-ahead/intraday market feed (e.g., EPEX SPOT / ENTSO-E) or simulated equivalent | FR-ENE-* |
| Grid carbon intensity (optional) | National grid operator feed or simulated | FR-ENE-*, FR-PLT-05 |
| Process & quality lab data | MES / LIMS or simulated | FR-QUA-* |
| Maintenance/asset data | CMMS work orders, inspection records or simulated | FR-FUR-*, FR-QUA-* |
| Cost/production data | ERP (cost per ton, production volumes) or simulated | FR-ENE-06, FR-PLT-05 |
| Operator interview content | GenAI knowledge-capture sessions (voice/video/text) — synthetic personas for demo | FR-KNW-* |
| EU ETS allowance data | Regulatory/finance reference data or simulated | FR-PLT-05, Sustainability Officer reporting |

### 10.2 Data Quality & Governance Requirements

- **DQ-01**: All ingested time-series data shall carry a source system identifier, timestamp with timezone, and units of measure.
- **DQ-02**: Missing/late data shall be flagged (not silently interpolated without labeling) so predictions can indicate reduced confidence.
- **DQ-03**: Synthetic demo data shall be structurally representative of the real data domains in §10.1 and internally consistent with the KPI targets in §4 (owned by `data-demo-spec`, validated against this spec).
- **DQ-04**: Personal data (interview content) shall be minimized, pseudonymized where feasible for demo purposes, and clearly separated from operational/process data stores.
- **DQ-05**: Data lineage from source → feature → model → recommendation shall be traceable for audit purposes (feeds FR-GOV-01/02).
- **DQ-06**: Retention periods shall be defined per data domain (operational telemetry, decision logs, personal interview data) and shall satisfy the longer of business need, safety record-keeping norms, and GDPR minimization (detailed retention schedule owned by `security-spec`; decision-log retention of **≥7 years** is assumed here for safety-relevant furnace decisions, consistent with heavy-industry record-keeping norms, pending confirmation).

---

## 11. AI/ML Requirements

| ID | Requirement |
|---|---|
| AI-01 | The furnace lining model shall be **physics-informed** (i.e., combine domain heat-transfer/wear physics with learned components), not a pure black-box model, to improve extrapolation safety and explainability for a safety-adjacent use case. |
| AI-02 | The energy dispatch capability shall be framed as an **optimization/agentic scheduling** problem (constraint-aware schedule search), not a simple forecast — it must produce an actionable schedule, not just a price prediction. |
| AI-03 | The knowledge-capture capability shall use **GenAI (LLM-based) conversational interviewing** plus a **retrieval-augmented generation (RAG)** pattern for search, so answers are grounded in approved, versioned procedure content rather than open generation alone. |
| AI-04 | All predictive/generative outputs presented to a human decision-maker shall include an explanation artifact appropriate to the model type (feature attribution for FUR/QUA models; source citation for KNW/RAG answers; constraint/rationale summary for ENE optimization). |
| AI-05 | Every model shall have a defined human-in-the-loop checkpoint before any action with safety, financial (above threshold), or customer-facing consequence is executed (ties to FR-GOV-05, O1). |
| AI-06 | Models shall be monitored in production for performance degradation/drift, with a documented retraining or recalibration trigger. |
| AI-07 | GenAI knowledge-capture outputs shall be reviewed/approved by a qualified human expert before publication (ties to FR-KNW-04) to control hallucination risk in safety-relevant procedures. |
| AI-08 | Where feasible, models shall report a calibrated confidence/uncertainty measure (not just a point prediction), particularly for FR-FUR-02/03 given the high cost of both false negatives (missed failure) and false positives (unnecessary reline). |

---

## 12. Auditability & Traceability Requirements

- **AUD-01**: Every AI recommendation across all four capability areas (energy, furnace, quality, knowledge) shall produce a single, queryable audit record per FR-GOV-01.
- **AUD-02**: Audit records shall be immutable (append-only or equivalent) and tamper-evident.
- **AUD-03**: The platform shall support reconstructing, for any historical date, "what did the AI recommend, what did the human decide, and what was the outcome" for each of the four capability areas — this is both a governance requirement and the mechanism for computing KPI-TRUST-01 and KPI-ENE-02 (§13).
- **AUD-04**: Model version and configuration used for each recommendation shall be captured, enabling like-for-like comparison across model versions over time.
- **AUD-05**: Access to audit records shall itself be logged (who viewed/exported an audit trail and when), supporting regulator/auditor requests (FR-GOV-04).
- **AUD-06**: The traceability matrix in §15 shall be kept current as the authoritative link between requirement → KPI → persona → demo moment, for use by all downstream workstreams and by defense reviewers.

---

## 13. KPI Catalog (Definitions & Formulas)

| KPI ID | Name | Formula | Target | Frequency | Primary owner |
|---|---|---|---|---|---|
| KPI-ENE-01 | Specific Energy Consumption (SEC) | `Total energy consumed (GJ) ÷ Total crude steel produced (t)` | −14% vs. baseline (≈16.8 GJ/t) | Daily / rolling 30-day | Energy Manager |
| KPI-ENE-02 | Energy Cost Avoidance | `Σ (Baseline-schedule cost − As-run cost)` over accepted recommendations, €, per period | Track & report; contributes to KPI-ENE-01 economics | Daily (ledger), Monthly (report) | Energy Manager |
| KPI-ENE-03 | Dispatch Recommendation Acceptance Rate | `Accepted recommendations ÷ Total recommendations issued` | ≥70% (illustrative adoption target) | Weekly | Energy Manager |
| KPI-CO2-01 | Specific CO₂ Emissions | `Total CO₂e emitted (t) ÷ Total crude steel produced (t)` | −22% vs. baseline (≈1.64 t/t) | Daily / rolling 30-day | Sustainability Officer |
| KPI-CO2-02 | ETS Allowance Cost Exposure | `Forecast emissions above free-allocation threshold (t) × EU ETS allowance price (€/t)` | Minimize; report trend | Monthly | Sustainability Officer |
| KPI-FUR-01 | Lining Failure Lead Time | `Date of predicted failure alert − Date of actual reline/failure event`, in days | ≥21 days | Per event | Maintenance Engineer |
| KPI-FUR-02 | Unplanned Outage Avoidance | `Count of furnace outages classified "unplanned" per rolling 12 months` (trend vs. pre-platform baseline) | Downward trend; 0 catastrophic (€8M-class) unplanned events | Monthly | Maintenance Engineer |
| KPI-FUR-03 | RUL Prediction Precision/Recall | Standard precision/recall of "alert issued" vs. "failure would have occurred within window" | Precision ≥ 0.8, Recall ≥ 0.9 (illustrative; refine with real data) | Quarterly (model review) | Maintenance Engineer / Knowledge Engineer-Admin |
| KPI-QUA-01 | High-Grade Yield Rate | `Tons meeting automotive-grade spec first-pass ÷ Total tons attempted at automotive-grade` | +8% relative vs. baseline (≈90%→97%) | Daily / rolling 30-day | Quality Engineer |
| KPI-QUA-02 | Customer Claims/Reject Rate | `Customer-reported non-conformances ÷ Tons shipped` | Downward trend | Monthly | Quality Engineer |
| KPI-KNW-01 | Procedure Library Coverage | `Documented/approved procedure topics ÷ Identified critical-knowledge topics (from gap analysis)` | Upward trend toward 100% of critical topics | Monthly | Knowledge Engineer/Admin |
| KPI-KNW-02 | Knowledge Retrieval Time | Median time from operator query to a cited, relevant answer via RAG search | Seconds, not minutes (target: <10s in demo) | Continuous (telemetry) | Knowledge Engineer/Admin |
| KPI-TRUST-01 | AI Recommendation Acceptance Rate (portfolio) | `Σ accepted recommendations (all domains) ÷ Σ recommendations issued (all domains)` | Upward trend as trust builds | Monthly | Plant Manager / Executive |
| KPI-ADO-01 | Platform Adoption | `Weekly active users ÷ Total licensed/target users` per persona group | ≥80% of target roles active weekly by end of pilot | Weekly | Plant Manager |
| KPI-GOV-01 | Audit Completeness | `Recommendations with complete audit record ÷ Total recommendations issued` | 100% | Continuous | Knowledge Engineer/Admin |

---

## 14. Constraints

| ID | Constraint | Type |
|---|---|---|
| C-01 | Solution must fit a **1-hour defense: 35-minute slides, 10-minute live demo, 15-minute FAQ** (see §19). Architecture and demo scripting must respect this timebox. | Program/process |
| C-02 | Demo must run on **synthetic/simulated data only**; no production OT/IT connectivity is assumed or required for the defense (O7). | Technical |
| C-03 | All data processing must remain within the EU (data residency) given the LU/DE/BE/ES footprint and GDPR. | Regulatory |
| C-04 | No AI system may autonomously execute a safety-relevant or high-financial-impact action without human approval in this phase (O1, AI-05). | Regulatory/Safety |
| C-05 | Operator interview content is personal data; any real (non-synthetic) capture requires prior legal/HR consent workflow (A3). | Regulatory |
| C-06 | Platform must interoperate with, not replace, existing ERP/MES/CMMS systems of record (O4). | Technical/Organizational |
| C-07 | KPI targets (§4.1) are fixed by the use case and must be preserved end-to-end through architecture, data, and demo design — no downstream workstream may silently alter them. | Program |
| C-08 | EU AI Act classification of in-scope AI systems is pending formal legal review; solution must be designed to satisfy the more conservative ("high-risk-adjacent") posture until confirmed otherwise (A8). | Regulatory |

---

## 15. Traceability Matrix (Requirements ↔ Demo Moments ↔ Personas ↔ KPIs)

The 10-minute demo (detailed script in §19 and in the personas document) is organized into six demo moments (`DM-1` … `DM-6`). This matrix is the authoritative cross-reference for defense reviewers and downstream workstreams.

| Demo Moment | Duration | Persona(s) | Requirements demonstrated | KPI(s) evidenced |
|---|---|---|---|---|
| **DM-1** — Portfolio command center | ~2 min | Plant Manager, Executive | FR-PLT-02, FR-PLT-03, FR-PLT-05 | KPI-ADO-01, KPI-TRUST-01 (context-setting) |
| **DM-2** — Energy dispatch optimization | ~2.5 min | Energy Manager | FR-ENE-01…06, FR-PLT-04 | KPI-ENE-01, KPI-ENE-02, KPI-ENE-03 |
| **DM-3** — Furnace lining RUL & maintenance | ~2.5 min | Maintenance/Reliability Engineer, Furnace Operator | FR-FUR-01…05, FR-PLT-04 | KPI-FUR-01, KPI-FUR-02, KPI-FUR-03 |
| **DM-4** — In-line quality prediction & root cause | ~2.5 min | Quality Engineer | FR-QUA-01…04 | KPI-QUA-01, KPI-QUA-02 |
| **DM-5** — GenAI knowledge capture & search | ~2.5 min | Knowledge Engineer/Admin, Furnace Operator | FR-KNW-01…04 | KPI-KNW-01, KPI-KNW-02 |
| **DM-6** — Sustainability, ROI & audit trail | ~2 min | Sustainability Officer, Executive | FR-PLT-05, FR-GOV-01…04 | KPI-CO2-01, KPI-CO2-02, KPI-GOV-01, KPI-ENE-02 (ROI roll-up) |

Total scripted time: ~14 minutes + 1 minute transitions/buffer = **15 minutes**.

---

## 16. Acceptance Criteria

### 16.1 Capability-Level Acceptance Criteria (Given/When/Then)

**Energy Dispatch (FR-ENE)**
- *Given* a 24h horizon of forecast energy demand and spot prices, *when* the optimization agent runs, *then* it shall produce a schedule recommendation with an explicit expected € and CO₂ delta versus the baseline (as-planned) schedule.
- *Given* an Energy Manager rejects a recommendation, *when* they submit the rejection, *then* a reason code shall be mandatory and logged (FR-ENE-05, FR-GOV-01).

**Furnace Lining (FR-FUR)**
- *Given* simulated thermal signature data trending toward failure, *when* predicted RUL crosses the alert threshold, *then* an alert shall be raised at least 21 simulated days before the simulated failure date, with confidence band and top contributing features displayed.
- *Given* an active alert, *when* the Maintenance Engineer selects "create work order," *then* a CMMS-linked work order record shall be created/simulated with alert context attached.

**Quality (FR-QUA)**
- *Given* an in-progress heat with process parameters trending out of automotive-grade spec, *when* predicted risk exceeds threshold, *then* the platform shall display a corrective-action recommendation and a root-cause hypothesis referencing upstream genealogy.

**Knowledge Capture (FR-KNW)**
- *Given* a synthetic operator interview transcript, *when* the GenAI agent structures it, *then* the output shall conform to the trigger→action→rationale→risk template and be routed to a reviewer queue before publication.
- *Given* a published, approved procedure, *when* any authorized user searches in natural language, *then* the top result shall cite the source procedure and return within the target latency (KPI-KNW-02).

**Governance (FR-GOV)**
- *Given* any AI recommendation issued in the demo, *when* a reviewer opens the audit trail, *then* they shall see input features, model version, output, confidence, and the resulting human decision for that recommendation (KPI-GOV-01 = 100% in demo).

### 16.2 MVP/Demo-Level Acceptance Criteria

- **AC-01**: The full 10-minute demo (DM-1…DM-6) runs end-to-end on synthetic data without manual data patching, in ≤10 minutes, at least twice consecutively without failure (dress-rehearsal standard).
- **AC-02**: All 8 personas defined in the companion document are represented on-screen at least once during the demo or explicitly referenced in the narration with their cockpit shown.
- **AC-03**: All four use-case outcome metrics (§4.1) are visibly displayed with baseline vs. target vs. "as achieved in simulation" values during DM-1 and/or DM-6.
- **AC-04**: A recorded video fallback of the full demo exists and is verified to play, satisfying NFR-AVAIL-02/A7 in case of live environment failure during the defense.
- **AC-05**: Every functional requirement tagged with a `Demo` reference in §8 is observably exercised in the demo moment listed in §15.
- **AC-06**: The defense deck and demo together fit the 1-hour session structure in §19 with time remaining for Q&A.

---

## 17. Risks & Mitigations

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | Live demo environment fails during the 1-hour defense (network, cloud service outage). | Medium | High | Fully synthetic/offline-capable demo; recorded video fallback (AC-04); rehearse twice before defense. |
| R-02 | Illustrative baseline numbers (§4.2) are challenged as unrealistic by domain-expert reviewers. | Medium | Medium | Clearly label all baselines as illustrative assumptions pending real data audit; cite plausible industry ranges; do not present as measured fact. |
| R-03 | Operators/experts distrust or resist AI recommendations (adoption risk), undermining KPI-TRUST-01/KPI-ADO-01. | Medium | High | Human-in-the-loop design (AI-05), transparent rationale (AI-04), knowledge-capture program explicitly frames AI as augmenting not replacing experts. |
| R-04 | EU AI Act classification is stricter than assumed (A8), requiring conformity assessment not scoped here. | Low-Medium | High | Conservative "high-risk-adjacent" design posture now (logging, human oversight, documentation); formal legal classification tracked as a dependency for `security-spec`. |
| R-05 | GenAI knowledge capture hallucinates or misattributes expert statements, creating unsafe or incorrect procedures. | Medium | High | Mandatory human expert review/approval before publication (FR-KNW-04, AI-07); RAG grounding with citations (AI-03). |
| R-06 | Physics-informed furnace model produces false negatives (missed failure) given synthetic/limited training data. | Medium | High (safety) | Conservative alert thresholds, explicit confidence bands (AI-08), human escalation path (FR-FUR-07), clearly scope MVP as decision-support only. |
| R-07 | Energy market data licensing/access is not finalized in time for production rollout. | Medium | Medium | Demo uses simulated price series (C-02); production dependency flagged (A2) for early procurement engagement. |
| R-08 | Cross-country data residency/localization adds integration complexity across LU/DE/BE/ES. | Medium | Medium | EU-only hosting assumed from the outset (NFR-SEC-03); architecture workstream to confirm regional data handling. |
| R-09 | Scope creep during architecture/UX design threatens the 10-minute demo timebox. | Medium | Medium | §15 traceability matrix and §19 agenda are binding; any new capability must map to an existing DM slot or be deferred to §18 roadmap. |
| R-10 | Quality/root-cause model requires deeper genealogy data than available in synthetic dataset, weakening DM-4. | Low-Medium | Medium | Coordinate early with `data-demo-spec` to ensure genealogy fields are modeled in synthetic data generation. |

---

## 18. Staged Delivery Scope (MVP → Production)

| Phase | Scope | Data | Automation posture |
|---|---|---|---|
| **Demonstration — Defense/Demo (this engagement)** | All four capability areas demonstrated end-to-end (S1–S8); single simulated "portfolio" spanning 4 illustrative sites. | 100% synthetic/simulated (C-02, O7). | Decision-support only; no live execution. |
| **Phase 1 — Pilot (0–6 months post-approval)** | One real site, read-only integration to historian/energy/quality/CMMS data; AI runs in **shadow mode** (recommendations logged, not required to be acted on) to validate accuracy against real outcomes. | Real data (read-only), GDPR consent process live for any real interviews (C-05). | Shadow mode; human fully in control; audit trail live (FR-GOV-01). |
| **Phase 2 — Scale (6–18 months)** | Roll out to remaining 3 sites; enable guarded, human-approved execution of energy dispatch recommendations and maintenance work-order creation; knowledge library reaches critical-topic coverage target. | Real data, bi-directional integration (write-back to CMMS/MES where approved). | Human-approved execution (guardrails per FR-ENE-07); AI Act conformity documentation finalized (C-08). |
| **Phase 3 — Steady State (18+ months)** | Cross-plant benchmarking, continuous model retraining pipeline, optional supervised automation for lower-risk, high-confidence recommendation classes only (re-evaluated per risk framework); ETS exposure forecasting feeding finance/trading workflows (still O3-compliant: report, not trade). | Full production data lineage, long-term audit retention (§10.2 DQ-06). | Selective, governed automation with continuous human oversight audit (FR-GOV-05). |

This phasing directly supports the "in scope / out of scope" boundaries in §5: everything in §5.1 is demonstrated in the defense demonstration; everything in §5.2 (O1–O7) is either explicitly deferred to a later phase (O1, O3, O7) or remains permanently out of scope for this platform (O2, O4, O5, O6).

---

## 19. Defense & Demo Format

### 19.1 Constraint

Per the assignment format, the solution is presented in a **1-hour defense**: **35 minutes of slides**, a **10-minute live demo**, and **15 minutes of FAQ**. All content in this specification (and the architecture/UX/data workstreams built on it) must fit this constraint without truncating the four core outcome areas.

### 19.2 Suggested 60-Minute Defense Agenda

| Segment | Duration | Content |
|---|---|---|
| Slides: problem, personas, architecture, Fabric, AI, governance, data, deployment | 35 min | [Oral-defense plan](../presentation/oral-defense-and-slide-plan.md), slides 1–20 |
| **Live demo** | **10 min** | DM-1 → DM-6 per §15/§19.3 |
| FAQ / defense | 15 min | [Oral-defense FAQ](../presentation/faq.md); validation gates and follow-ups |

### 19.3 10-Minute Demo Script (binding reference)

Follows §15 exactly: DM-1 (1.5 min) → DM-2 (1.5 min) → DM-3 (2 min) → DM-4 (1.5 min) → DM-5 (1.5 min) → DM-6 (1.5 min) = 9.5 min + 0.5 min recap/buffer = 10 min. Full narrative script, screen-by-screen walkthrough, and persona framing for each moment are provided in [personas and journeys](../personas/personas-and-journeys.md).

### 19.4 Reliability Requirements for the Demo

- Must satisfy NFR-AVAIL-02 (no live external dependency) and AC-04 (recorded fallback).
- Must be rehearsed at least twice end-to-end before the defense (AC-01).
- Presenter(s) mapped to personas should be identified in advance so narration matches the persona voice in the companion document.

---

## 20. Glossary

| Term | Definition |
|---|---|
| BF-BOF | Blast Furnace – Basic Oxygen Furnace, the integrated primary steelmaking route |
| EAF | Electric Arc Furnace, an alternative/complementary steelmaking route |
| RUL | Remaining Useful Life (of an asset, here: furnace refractory lining) |
| ETS | EU Emissions Trading System — carbon allowance market |
| RAG | Retrieval-Augmented Generation — LLM pattern grounding answers in retrieved, approved content |
| OT / IT | Operational Technology (sensors, control systems) / Information Technology (ERP, MES, business systems) |
| CMMS | Computerized Maintenance Management System |
| LIMS | Laboratory Information Management System |
| SEC | Specific Energy Consumption (energy per ton produced) |
| Shadow mode | AI operates and logs recommendations without being required to drive real action, used to validate accuracy before enabling human-approved execution |

---

## 21. Change Log

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-07-25 | Initial implementation-ready specification derived from `docs\usecase\usecase.md`. |
