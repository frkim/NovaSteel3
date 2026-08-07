# Business Value Assessment

> **Artifact:** Business Value Assessment · **Audience:** executive sponsors, finance, product owners, delivery leadership · **Status:** baseline · **Source of truth:** [use case](../usecase/usecase.md)

Purpose: summarize the business value case for NovaSteel while keeping pilot targets, illustrative financial assumptions, and measured synthetic-demo results separate. The assessment supports a decision on whether to proceed to a governed pilot; it is not a production financial forecast and does not claim realized benefits.

## Business problem

AxelorMetal is a fictitious Luxembourg-headquartered steel producer operating blast furnaces and rolling mills across Luxembourg, Germany, Belgium, and Spain. The documented situation is five-fold: energy is 35% of production cost with no real-time optimization, CO₂ exposure is rising under EU ETS pressure, furnace lining wear is unpredictable and a catastrophic event costs about €8M, high-grade automotive steel quality is inconsistent, and skilled operators are retiring faster than their tacit knowledge can be captured.

NovaSteel addresses those issues as a Microsoft-Fabric-centered decision-support platform: it senses synthetic operations data, predicts RUL and quality risk, recommends energy dispatch options, captures operator knowledge, and explains recommendations with humans retaining control. It is explicitly not an OT control system and all current proof uses synthetic/non-personal data.

> **Pilot targets vs measured demo evidence.** The 14% energy, 22% CO₂, 21-day warning, and 8% yield figures are **pilot targets** from the use case. The measured evidence below is from one deterministic 24-hour synthetic scenario at one site plus repository validation. Smaller measured percentages are expected because the scope is narrower than an annualized four-country pilot.

## Value hypotheses

| Hypothesis | Driver | Pilot target | Measured in demo | Evidence | Confidence |
|---|---|---|---|---|---|
| Energy dispatch can reduce cost by shifting schedulable load without breaking hard constraints | Energy is 35% of production cost; MILP schedules around spot-price scarcity and constraints | 14% energy reduction in an annual pilot | 7.25% whole-dispatch cost reduction; 7.89% peak reduction from 56.0 to 51.58 MW; 960 tonnes conserved; zero hard-constraint violations | Root README validated proof; operations value reconciliation | Medium for mechanism; target requires pilot validation |
| Carbon-aware dispatch contributes to ETS exposure reduction | CO₂ term in optimizer plus reporting links operational decisions to emissions | 22% CO₂ reduction in an annual pilot | 3.29% whole-dispatch CO₂ reduction in one 24-hour scenario | Root README; proof-of-execution caveat that load shifting alone is single-digit | Medium for direction; low for 22% until broader measures and real data are included |
| Furnace RUL warning gives maintenance time to avoid catastrophic lining failure | Physics-informed regression over thermal signatures; failures cost about €8M | 21-day advance warning across pilot fleet | P10/P50/P90 = 18.69/19.65/20.61 days; risk 0.8995 HIGH; confidence 0.7846; wear slope -3.21 mm/day at r² = 0.88 | Root README; implementation-process evidence table | Medium-high for order-of-magnitude warning; fleet average target requires pilot |
| Quality what-if can improve high-grade yield before batch completion | In-line quality risk, genealogy, bounded what-if, and human review | 8% high-grade yield uplift | Synthetic bounded what-if 88% to 95%; no operational write | Root README; proof-of-execution `OUT-04` caveat | Medium for demo mechanics; pilot needed for true yield uplift |
| Knowledge capture preserves retiring expertise safely | GenAI interview, transcription, structuring, reviewer approval, cited retrieval | Coverage of critical procedures and approved searchable knowledge base | Structured procedure workflow and decline-when-ungrounded behavior demonstrated; no production personal data used | Persona journeys; proof-of-execution knowledge evidence | Medium; depends on operator adoption and DPO-approved consent process |
| Unified audit and governance improve trust and regulatory readiness | Immutable recommendation log, RBAC, model cards, DPIA/AI Act posture, evidence export | 100% decision audit completeness for in-scope recommendations | Audit hash-chain and 66/66 live BFF checks validated; fallback/no-network 12/12 | Root README; solution requirements FR-GOV; operations monitoring | Medium-high for demo; production legal classification remains a gate |

## Benefit drivers by persona

| Persona | Decision improved | Benefit mechanism | Leading KPI |
|---|---|---|---|
| Plant Manager | Cross-domain trade-off between energy, asset health, quality, and production plan | One command-center view with escalation, RUL alerts, recommendation rationale, and audit trail | Portfolio/site KPI variance; decision lead time |
| Furnace Operator | Whether an abnormal thermal pattern needs escalation | Procedure search, device health, synthetic incident context, and clear safety boundary | Alert acknowledgment time; procedure hit rate |
| Energy Manager | Accept, modify, or reject dispatch recommendations | MILP schedule with cost/CO₂ impact, constraints, and rejection reason codes | Energy cost per tonne; recommendation acceptance/rejection reasons |
| Maintenance and Reliability Engineer | When to schedule a reline or synthetic work order | RUL band, feature drivers, risk score, and prediction-vs-actual monitoring | Days of advance warning; false-negative/false-positive rate |
| Quality Engineer | Whether to intervene before an active heat misses automotive spec | In-line risk scoring, bounded what-if, and genealogy/root-cause view | First-pass high-grade yield; predicted-risk precision/recall |
| Sustainability Officer | Where emissions trajectory needs escalation | ETS cockpit, CO₂ trend, allowance exposure, and decision lineage | CO₂ per tonne; allowance exposure variance |
| Knowledge Engineer/Admin | Which procedures to publish and where knowledge gaps remain | Human-reviewed GenAI structuring, versioning, and cited retrieval | Approved procedure coverage; review cycle time |
| Executive (COO) | Whether to fund pilot and scale-up | Portfolio KPI trend, ROI cockpit, savings ledger, and governance completeness | Pilot gate closure; benefits-realisation trend |
| Platform Ops | Whether capacity, health, and cost posture support a demo or pilot | Capacity controls, SLO dashboards, budget alerts, fallback readiness | SLO burn; F2/F4 decision evidence; budget threshold status |

## Quantified demo results

| Area | Exact measured result | Scope and interpretation |
|---|---|---|
| Live BFF checks | 66/66 passed | Deterministic scenario API proof, not production uptime |
| Automated tests | 1,139 tests: 874 Python and 265 frontend | Repository validation baseline |
| Furnace RUL | P10/P50/P90 = 18.69/19.65/20.61 days | One furnace scenario; target is fleet/pilot 21-day warning |
| Furnace risk | Risk 0.8995 HIGH; confidence 0.7846 | Confidence derives from r² = 0.88 |
| Furnace wear slope | -3.21 mm/day at r² = 0.88 | Regression responds to thermal input |
| Energy tonnage | 960 = 960 tonnes conserved | Optimized schedule preserves planned tonnage |
| Energy constraints | Zero hard-constraint violations | MILP respects delivery, soak, capacity, and other constraints |
| Energy cost | 7.25% whole-dispatch cost reduction | One 24-hour scenario at one site |
| Energy CO₂ | 3.29% whole-dispatch CO₂ reduction | Smaller than 22% pilot target by design and scope |
| Energy peak | 7.89% peak reduction, 56.0 to 51.58 MW | At a 280 EUR/MWh scarcity peak |
| Flexible-load transparency | 21.74% cost and 31.71% CO₂ on movable-reheat-load-only basis | Exposed as `rawFlexibleCostPct` and `rawFlexibleCo2Pct`; deliberately not a headline |
| Quality | Bounded synthetic what-if 88% to 95% | No operational write and not a production yield claim |
| Fallback/no-network | 12/12 checks passed | Local BFF uses loopback only; supports demo resilience |

## Evidence boundaries and interpretation

The value case uses three evidence classes:

| Evidence class | What it proves | What it does not prove |
|---|---|---|
| Live BFF and automated tests | The deterministic scenario, APIs, contracts, fallback behavior, and front-end behaviors are reproducible | Production availability or plant-floor integration |
| Synthetic model outputs | The optimizer, RUL regressor, quality scorer, and knowledge workflows execute with transparent inputs and caveats | Annualized savings, fleet reliability, or real yield uplift |
| Operations and cost controls | The repository has IaC, OIDC, budgets, monitoring, runbooks, and F2 demo cost discipline | A final production quote or target-tenant readiness |

Interpretation rules for executives and finance:

- Treat measured demo values as proof of mechanism and integration quality.
- Treat the pilot targets as hypotheses to validate against real read-only data.
- Treat illustrative ROI ranges as a workshop model until AxelorMetal actuals replace assumptions.
- Keep avoided-failure value as upside until real maintenance history confirms frequency.
- Do not headline flexible-load-only energy percentages; the whole-dispatch basis is the honest view.
- Do not treat the synthetic 88% to 95% quality what-if as realized customer yield.
- Do not count any benefit that requires an operational write before the relevant governance gate closes.

## Cost model

The documented cost model separates the low-cost synthetic demo from any production business case.

| Cost driver | Demo control | Pilot/production implication |
|---|---|---|
| Fabric capacity | F2 in Sweden Central; paused outside demo windows; F4 only after measured contention | Production SKU chosen after pilot load test; production capacity never auto-paused |
| Container Apps | Deployed slice runs portal/BFF services on consumption-style app hosting | Service scaling and image promotion must be measured under pilot load |
| Event Hubs and relay | Partitioning/retention sized from observed synthetic throughput | Test peak and replay recovery before reserving or scaling |
| Storage, OneLake, KQL, and audit | Explicit retention/cache settings; paused capacity does not erase storage cost | Lifecycle policies and retention must match security and audit needs |
| Foundry, Speech, AI Search, Cosmos, and knowledge storage | Gated or offline-safe in current deployment; cached demo responses available | Token quotas, private-network support, regional availability, and DPO gates must clear |
| Logs, Sentinel, App Insights | Classification-aware logging; no raw audio/prompt payload logging | Retention, alert volume, and Sentinel cost reviewed with security |
| Implementation effort | Repository embodies foundation, services, apps, contracts, tests, docs, Bicep, Fabric definitions | Operations-and-cost frames build as illustrative one-off foundation, AI workloads, experience, compliance, and change effort |

Operations-and-cost lists illustrative annual pilot run cost of about €187k-€408k and illustrative one-off implementation cost of about €560k-€1.12M. Those figures are target/illustrative, date- and offer-sensitive, and must be replaced by live Azure/Fabric pricing and AxelorMetal actuals before any funding decision.

## ROI framing

This is an illustrative model, not a validated financial forecast:

| Element | Assumption from repository | How to use it |
|---|---|---|
| Production volume | About 1.0 Mt/year in-scope site; about 0.3 Mt/year pilot line | Replace with AxelorMetal actual tonnage |
| Production cost | About €500/t with energy about 35%, or about €175/t | Replace with finance-approved cost model |
| Energy benefit formula | `tonnes x €175/t x validated energy-saving %` | Do not substitute the 7.25% single-scenario result as an annual forecast without pilot evidence |
| At-scale target energy benefit | About €24.5M/year at 1.0 Mt and 14% | Target/illustrative only; recalculates if pilot validates a different percentage |
| Avoided failure | About €8M per event; illustrative expected value based on frequency assumption | Treat as upside until real failure frequency and maintenance data are agreed |
| Run and build cost | Run about €187k-€408k/year; build about €560k-€1.12M | Refresh from pricing calculator, procurement, and delivery plan |
| Payback | Operations document frames payback as under 12 months in conservative illustrative case | Use only after replacing all assumptions and validating pilot percentages |

The finance conversation should be sensitivity-led: if the validated annual energy saving, CO₂ contribution, failure frequency, yield uplift, or cloud cost differs from the target assumptions, the ROI changes transparently through the formulas rather than through a fixed claim.

## KPI and benefits-realisation plan

| KPI | Baseline | Target | Measurement source | Cadence | Owner |
|---|---|---|---|---|---|
| Energy consumption or cost per tonne | Use-case baseline: energy is 35% of total production cost; illustrative 19.5 GJ/t in requirements | 14% reduction in pilot target | Fabric gold energy facts, optimizer ledger, as-run comparison | Weekly in pilot; monthly benefits review | Energy Manager |
| CO₂ emissions per tonne | Illustrative 2.10 tCO₂/t in requirements | 22% reduction in pilot target | Sustainability cockpit, ETS ledger, dispatch emissions terms | Monthly | Sustainability Officer |
| Furnace RUL advance warning | Current state: unpredicted failures, 0-day warning | 21-day warning | RUL fact table, alert log, maintenance outcome reconciliation | Daily scoring; monthly model review | Maintenance and Reliability Engineer |
| High-grade first-pass yield | Illustrative 90% automotive first-pass yield | 8% relative uplift | Quality yield facts, batch genealogy, claims/non-conformance data | Weekly production quality review | Quality Engineer |
| Recommendation audit completeness | No shared immutable AI decision lineage in starting problem | 100% in-scope recommendation logs | Hash-chained audit table and export | Per release and monthly audit | Knowledge Engineer/Admin |
| Model confidence and drift | Demo confidence and r² baseline only | Within pilot tolerance set by RAI board | MLflow/App Insights evaluation | Per model release and monthly | Data/AI team |
| Platform SLO health | No production baseline yet | Pilot SLOs met without budget breach | App Insights, Fabric monitoring, Capacity Metrics | Weekly | Platform team |
| Adoption and trust | Not established before pilot | Persona-specific use of dashboards and reason-code quality | Usage telemetry, rejection reasons, interview coverage | Monthly | Plant Manager / Executive sponsor |

## Risks and assumptions

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Pilot percentages are lower than target | Business case shrinks | Medium | Prove percentages on about 0.3 Mt pilot line before scale; recalculate ROI with validated values |
| Synthetic scenario overfits expectations | Demo looks stronger than real performance | Medium | Use shadow-mode real data, prediction-vs-outcome monitoring, and explicit target/evidence labels |
| Fabric capacity, Eventstream, Foundry Agent Service, Speech, or Power BI tenant gates remain unresolved | Blocks live-cloud pilot capabilities | Medium | Clear target-tenant quota, regional, private-network, and capability-host gates before pilot |
| Market-data licensing/freshness not finalized | Energy optimizer degrades | Medium | Procure licensed source early; degrade to approved day-ahead or cached snapshots with expiry |
| Model false negatives or poor confidence | Safety-adjacent maintenance decisions lose trust | Medium | Keep decision-support-only posture, conservative thresholds, human escalation, confidence bands, and RAI review |
| GenAI knowledge capture hallucinates or misattributes expertise | Unsafe procedure publication | Medium | Mandatory human review, citations, PII redaction, approval workflow, and decline when ungrounded |
| EU AI Act/DPIA classification stricter than assumed | Delays production | Low-medium | Treat as high-risk-adjacent, retain audit evidence, obtain legal/DPO sign-off before real data |
| Cross-country data residency and localization add integration effort | Rollout slows | Medium | EU-only hosting posture, per-site gateways, localization, and per-country market-data validation |
| Cost grows beyond illustrative run envelope | ROI and budget confidence weaken | Medium | Budgets, 50/80/100% alerts, Capacity Metrics, right-sizing, and no unmeasured SKU escalation |
| Users distrust recommendations or workflows | Adoption and benefits lag | High | Human-in-the-loop design, transparent rationale, reason codes, persona training, and benefits-realisation reviews |

## Decision recommendation

Proceed to a time-boxed Phase 1 pilot only if the open production gates close: target-tenant Fabric capacity/SKU and SaaS items, Eventstream Custom Endpoint identity/network proof, Entra/Fabric authorization and RLS, Foundry/Speech private-network validation, DPO/legal/DPIA and EU AI Act decisions, OT vendor/DMZ approval, market-data licensing, DR/performance/accessibility tests, live-cloud fallback rehearsal, and an agreed benefits measurement plan. The demo evidence is strong enough to justify pilot discovery and shadow-mode validation, but not enough to claim production savings.

## Related artifacts

- [Glossary](glossary.md)
- [Diagrams](diagrams/README.md)
- [Solution Architecture](solution-architecture.md)
- [Data Baseline](data-baseline.md)
- [AI Design](ai-design.md)
- [Security Baseline](security-baseline.md)
- [Compliance](compliance.md)
- [Operating Model](operating-model.md)
- [Test Strategy](test-strategy.md)
