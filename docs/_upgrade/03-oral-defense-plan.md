# NovaSteel — 60-Minute Oral Defense Plan

> Built on **Project B (`Novasteel 3`)** after the Wave 1 + Wave 2 modifications in
> `02-modification-plan.md`. Structure follows B's existing **35 + 10 + 15** plan in
> `docs\presentation\oral-defense-and-slide-plan.md`, reinforced with Project A's
> business-case material.

---

## Governing principles

1. **Never claim what you cannot show.** Keep B's 🎯 TARGET / 🔬 EVIDENCE labelling on every
   number. It disarms the single hardest question — *"is that real or aspirational?"* — before
   it is asked. Volunteer the distinction; do not wait to be caught.
2. **Show, then explain.** Every architectural claim should be one click from a file, a
   running endpoint, or a resource in the portal.
3. **Own the gaps first.** Name your two weakest points yourself, in your own framing, before
   the Q&A. A gap you disclose is engineering maturity; a gap the jury finds is a defect.
4. **Never diagnose on screen for more than 10 seconds.** Drop down B's 5-level fallback
   ladder (live cloud → local replay → cached → recording → static pack) and keep talking.

---

## Part 1 — Architecture & value story (00:00 – 35:00)

| Clock | Slide(s) | Content | Notes |
|---|---|---|---|
| 00:00–03:00 | 1–2 | **The hook.** Four numbers: energy = 35 % of cost · €8 M per lining failure · EU ETS penalties rising · operators retiring. Then: *"Four countries, one platform, three decisions."* | Do **not** open with architecture. Open with money and risk. |
| 03:00–06:00 | 3–4 | **Business case.** €0.6–1.1 M build, €0.3–0.7 M/yr run, ~€24.5 M/yr energy benefit, sub-12-month payback, with sensitivity band. | 🎯 TARGET-labelled. From M7 (imported from Project A). |
| 06:00–12:00 | 5–7 | **Target architecture.** OT gateway (outbound only) → Event Hubs → managed-identity relay → Fabric Eventstream → Eventhouse/KQL + OneLake medallion → Python advisory services → FastAPI BFF → Blazor shell + React dashboard. | Land the **safety boundary** here: decision support only — never PLC, interlock, setpoint, schedule-commit or CMMS write. Jurors remember this. |
| 12:00–16:30 | 8–10 | **Design & scalability.** 6 resource groups, hub-and-spoke, **per-plant Event Hub + per-plant identity for all four countries**, 4 environments, 10 ADRs. Named patterns: Ports & Adapters, BFF, microfrontend, capacity state machine, idempotency, policy-as-code. | Compress these slides (they are B's densest). One pattern → one file → one trade-off, then move. |
| 16:30–23:00 | 11–13 | **Security & compliance.** Private endpoints + private DNS everywhere · `disableLocalAuth: true` · **7 per-service managed identities + per-plant OT identity** · GitHub OIDC (no secrets) · **subscription-scope deny-public-network Azure Policy** · custom least-privilege `Fabric Capacity Operator` role · SHA-256 hash-chained audit · STRIDE threat model · **EU AI Act: high-risk-adjacent pending Legal**. | 🥇 **Your strongest 6+ minutes.** Slow down. This is where B scores 5/5; give the added time to the compliance and EU AI Act story. Show the policy JSON on screen. |
| 23:00–30:30 | 14–17 | **AI & agentic.** (a) Physics-informed RUL — heat-flux slope regression, P10/P50/P90 from fit residuals. (b) Energy dispatch — **PuLP/CBC MILP**, binary start-slot variables, no-overlap constraints, weighted CO₂+cost objective. (c) GenAI knowledge capture — grounded RAG on GPT-5, enforced citations, decline path, Content Safety. Then the **state graph**: DRAFT→IN_REVIEW→APPROVED with HITL gates, a **critic/reflection loop**, and the **RUL↔dispatch handoff**. | Post-M1/M2/M3/M6 this is real. Show the Mermaid state graph **generated from the code**. |
| 30:30–34:00 | 18–19 | **Operations.** Correlation IDs end-to-end → W3C traceparent · the four business KPIs as Application Insights **custom metrics** · alert rules as Bicep resources · Sentinel · tiered retention (prod 365 d) · 9 CI workflows with CodeQL, SBOM, SHA-pinned actions. | From M4/M5. *"Every number on the executive dashboard is also a metric with an alert on it."* |
| 34:00–35:00 | 20 | **Handoff to demo.** Restate the three decisions and name the personas about to be shown. | |

---

## Part 2 — Live demonstration (35:00 – 45:00)

Use `docs\demo\demo-runbook.md` and `drive_demo.py`. Deterministic seed, committed
`demo-full` fixture, no cloud dependency for the core path.

| Clock | Moment | Persona | Proof point | Route |
|---|---|---|---|---|
| 35:00–36:30 | 1 | **Plant Manager** | Command center: live estate across 4 countries, one screen | `/lu/command-center` |
| 36:30–38:30 | 2 | **Reliability Engineer** | RUL forecast — **P10/P50/P90 = 18.69 / 19.65 / 20.61 days, risk 0.90 HIGH**, confidence 0.78 from a fitted wear slope of −3.21 mm/day (r² = 0.88). Change the thermal input, watch the forecast move (this is the M2 payoff) | `/lu/furnace-health/lining-forecast` |
| 38:30–40:30 | 3 | **Energy Manager** | MILP dispatch — 960 = 960 tonnes conserved, **zero hard-constraint violations**, **7.25 % cost / 3.29 % CO₂ / 7.89 % peak reduction** (all whole-dispatch basis), peak 56.0 → 51.58 MW, CO₂ computed from per-slot carbon intensity | `/lu/energy-optimization/spot-price-schedule` |
| 40:30–41:30 | 4 | **Quality Engineer** | Batch genealogy + bounded what-if 88 % → 95 %, **with no operational write** | `/lu/quality/batches` |
| 41:30–43:30 | 5 | **Knowledge Engineer** | 🎬 **The set-piece.** A live GPT-5 extraction from an operator interview → **critic loop rejects an uncited claim** → revision → human approval gate → entry appended to the hash-chained audit | `/lu/knowledge-hub/procedures` |
| 43:30–44:30 | 6 | **Sustainability / Audit** | Emissions ledger + `verify()` on the SHA-256 audit chain, live | `/lu/sustainability-compliance/emissions-ledger` |
| 44:30–45:00 | — | **Close** | Executive overview; hand back to the panel | `/lu/executive-overview` |

**Demo discipline**
- Pre-warm everything: BFF running, `/health/ready` green, portal built, browser tabs open in order, zoom set for the room.
- Terminal font large enough to read from the back.
- If anything stalls > 10 s, drop a rung on the fallback ladder and keep narrating.
- Moment 5 is the one they will remember. Rehearse it until it is muscle memory.

---

## Part 3 — Q&A and production gates (45:00 – 60:00)

Draw on `docs\presentation\faq.md` (50+ Q&A) and the 6 FAQ backup slides.

### Open with a 90-second self-critique (45:00 – 46:30)

Take the initiative. Something close to:

> *"Before your questions — two things I want to put on the table myself. First: what you
> just saw runs against a live Azure deployment in Sweden Central, and it also runs fully
> offline as a deterministic fallback — the IaC is written, validated and what-if'd, and the
> live environment passes 66/66 automated API checks. What is **not** yet in place is
> production tenant hardening: real plant data, DPO sign-off and the security review are
> gated. Second: the −14 % energy, −22 % CO₂, 21-day warning and +8 % yield figures are
> **pilot targets**, not realised outcomes. What I have measured on a fixed-seed synthetic
> scenario is 7.25 % cost, 3.29 % CO₂, 7.89 % peak reduction and a 19.65-day lining warning.
> Those are smaller numbers, and they are real ones — one 24-hour scenario at one site is not
> an annualised four-country pilot. Every slide labels which of the two it is."*

This converts your biggest vulnerability into your strongest credibility signal.

### Anticipated questions

| # | Question | Answer |
|---|---|---|
| Q1 | *"Is any of this actually deployed?"* | No — and deliberately. IaC is written, validated, what-if'd, with per-environment approval gates. Production is gated on Fabric capacity/SKU sizing, Eventstream managed-identity proof, DPO/DPIA and EU AI Act decisions, OT vendor/DMZ approval and market-data licensing. Deploying an unapproved OT-adjacent platform would be the wrong engineering answer. |
| Q2 | *"How is the RUL model physics-informed?"* | Least-squares regression on the **heat-flux slope** over a rolling window, extrapolated to the lining thickness threshold; P10/P50/P90 come from the fit residuals, so the uncertainty band is derived, not assumed. Show `rul_model.py`. *(Requires M2 — without it, do not use the phrase "physics-informed".)* |
| Q3 | *"Where does −22 % CO₂ come from?"* | Post-M1: `Σ (shifted MWh × per-slot carbon intensity)` from the MILP schedule, on a synthetic price/carbon curve. −22 % is the pilot 🎯 TARGET; the 🔬 EVIDENCE figure from the seeded scenario is **3.29 % on a whole-dispatch basis** (31.71 % if you look only at the movable reheat load, exposed as `rawFlexibleCo2Pct`). We headline the whole-dispatch number because it includes the non-flexible base load the optimizer cannot move — quoting the flexible-only figure would overstate the result roughly sixfold. The gap to 22 % is scope: one 24-hour scenario at one site versus an annualised four-country pilot. **Never** defend a calibration constant. |
| Q4 | *"That's an optimizer, not AI."* | Correct, and deliberate — a MILP is the right tool for constrained scheduling; ML is the wrong one. The AI is in the three places it belongs: the degradation model, the LLM knowledge extraction, and the agentic orchestration between them. Knowing *when not to use a model* is an architecture decision. |
| Q5 | *"Show me the multi-agent coordination."* | The state graph. Dispatch proposes a schedule → hands off to the RUL agent → RUL returns a thermal constraint → dispatch re-plans. Separately, the knowledge extractor is critiqued by a second LLM pass that can force a revision. Both logged to the hash-chained audit. *(Requires M6.)* |
| Q6 | *"What if the LLM hallucinates a procedure?"* | Four layers: retrieval grounding, an enforced citation regex with a decline path, a critic pass, and a mandatory human approval gate before DRAFT→APPROVED. Nothing reaches an operator unreviewed. Plus Content Safety and a prompt-injection scanner with a tool allow-list. |
| Q7 | *"Can this touch the furnace?"* | Architecturally no. The OT gateway is **outbound-only**; there is no control path back. No PLC, interlock, setpoint, schedule-commit or CMMS write exists anywhere in the codebase. It is decision support. |
| Q8 | *"EU AI Act classification?"* | High-risk-adjacent, pending Legal. Articles 9, 10, 12, 14 and 15 obligations are designed in — risk management, data governance, logging/traceability, human oversight, accuracy/robustness — with 11 release-blocking acceptance gates. I have not self-certified minimal-risk, because a system advising on an €8 M asset does not deserve that label. |
| Q9 | *"GDPR — you're recording operators."* | Explicit consent capture in the interview workflow, EU-only residency (Sweden Central primary, West Europe contingency), PII redaction in the audit chain, erasure runbook, 72-hour breach workflow, and works-council consultation as a named production gate. |
| Q10 | *"Why Fabric rather than Databricks/Synapse?"* | ADR-001. Fabric gives one governed OneLake surface plus Real-Time Intelligence for the streaming path and Power BI for the executive layer, under a single capacity and a single Entra/Purview governance model — decisive for a 4-country estate with one small platform team. |
| Q11 | *"How does this scale to 4 countries?"* | It already does in IaC: `plants[]` is parameterised into a per-plant Event Hub and a per-plant managed identity. Adding a plant is a parameter change, not a code change. Show the Bicep. |
| Q12 | *"What's your cost at scale?"* | From M7: €0.6–1.1 M build, €0.3–0.7 M/yr run, dominated by Fabric capacity; auto-pause in non-prod, never in prod. Payback under 12 months on the energy line alone. 🎯 illustrative, requires a detailed Azure assessment. |
| Q13 | *"How do you know it works?"* | 235 automated tests across contract, simulator, backend, integration, E2E, infra and knowledge suites; 66/66 live BFF checks; 9 CI workflows with CodeQL, CycloneDX SBOM and SHA-pinned actions; one-command repository validation writing filed evidence to `artifacts\validation\`. |
| Q14 | *"What would you do next with 3 more months?"* | Deploy to a gated demo tenant behind the approval gates; replace deterministic adapters with live Foundry across all three workloads; add drift detection and an automated retraining loop; run a shadow-mode pilot on one furnace at one plant, measuring against a control furnace before any operator-facing rollout. |
| Q15 | *"What's the weakest part of your solution?"* | Observability was provisioned before it was consumed — App Insights existed with nothing emitting to it. I fixed it by instrumenting the four business KPIs as custom metrics with alerts. It is a good example of the gap between IaC and a working system, which is exactly why I validate both. |

---

## Materials checklist

- [ ] `docs\presentation\NovaSteel-Oral-Defense.pptx` regenerated after M1–M6 (26 slides, zero placeholders)
- [ ] Slides 8–10 compressed; 2–3 hero visuals added (M11)
- [ ] CFO cost/ROI bridge slide inserted (M7)
- [ ] French 1-page executive summary printed for the panel (M11)
- [ ] 1-page presenter rehearsal card with clock checkpoints
- [ ] State-graph Mermaid diagram, generated from code (M6)
- [ ] Backup: full demo screen recording, on local disk, not the network
- [ ] Static PDF pack as the last fallback rung
- [ ] BFF pre-warmed, `/health/ready` green, portal built, tabs pre-opened
- [ ] Two full timed dry runs completed
- [ ] Network-cable-pull recovery rehearsed

---

## Expected outcome

| Scenario | Score | Grade |
|---|:--:|:--:|
| Project B as-is today | 48.5 / 60 | B |
| B + Wave 1 (M1–M3) | ~54.5 / 60 | **A** |
| B + Waves 1–2 (M1–M6) | ~58.5 / 60 | **A** |
| Project A as-is today | 34.5 / 60 | D/F |
