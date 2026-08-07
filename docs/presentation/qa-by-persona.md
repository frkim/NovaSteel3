# NovaSteel — Oral Defense Q&A by Persona

> **Status:** Defense preparation asset — companion to the presentation deck and the demo runbook.
> **Scope:** Anticipated questions grouped by *who is asking*, plus a dedicated section per rating-grid
> criterion, plus deployment, evolution and curveball questions.

---

## 0. How to use this document

### 0.1 Relationship to the existing FAQ

| Document | Organised by | Count | Use it for |
| --- | --- | --- | --- |
| [`faq.md`](faq.md) | **Topic** (A–T: business value, Fabric, architecture, cost, AI governance, security, …) | 90 questions | Deep-dive rebuttals on a specific subject |
| **This document** | **Persona** (who is in the room and what they care about) | ~180 questions | Fast retrieval *during* Q&A, and rehearsal by stakeholder viewpoint |

The two are deliberately complementary. Where a question here overlaps a topic already covered in depth,
this document gives the short persona-framed answer and points at the FAQ entry rather than repeating it.

### 0.2 Answer discipline (non-negotiable)

Every number spoken during the defense must be labelled:

- 🔬 **EVIDENCE** — a reproducible result produced by the running system on the synthetic scenario
  (seed `240725`) and visible in the demo or in a committed fixture.
- 🎯 **TARGET** — a projected business outcome derived from the use-case brief and industry benchmarks.
  It is an objective, **not** a proven result.
- 📐 **DESIGN** — an architectural or procedural property that is specified and reviewable, but not
  exercised at scale in the demonstration (multi-site rollout, DR failover, load behaviour).

Three rules:

1. **Never** blur 🎯 into 🔬. If a jury member restates a target as a result, correct it immediately.
2. Time-box answers to **60–90 seconds**. Answer, give the one supporting number, stop.
3. When you do not know, say so with the standard formula:
   > *"That is a validation gate, not a claim. It is listed in the compliance roadmap as gate G&lt;n&gt;
   > and it is explicitly out of scope for this demonstration."*

### 0.3 Question ID scheme

To avoid collision with the topic FAQ (`Q1`–`Q90`), this document uses prefixes:

| Prefix | Section |
| --- | --- |
| `PB-` | Part 1 — Business personas |
| `PT-` | Part 2 — Technical & governance personas |
| `RG-` | Part 3 — Rating-grid criteria |
| `DP-` | Part 4 — Deployment & operations |
| `EV-` | Part 5 — Evolution & roadmap |
| `CB-` | Part 6 — Curveballs, traps and meta questions |

---

## 0.4 The numbers you must never get wrong

Rehearse these until they are reflex. Getting one of these wrong is more damaging than not knowing an answer.

| Figure | Value | Label |
| --- | --- | --- |
| Energy intensity objective | 19.5 → 16.8 GJ/t (**−14%**) | 🎯 TARGET |
| CO₂ intensity objective | 2.10 → 1.64 t CO₂/t (**−22%**) | 🎯 TARGET |
| Lining failure warning objective | **≥ 21 days** | 🎯 TARGET |
| High-grade yield objective | 90% → 97% (**+8 pts** on first-pass) | 🎯 TARGET |
| Cost of one unplanned lining failure | **€8M** | Use-case brief |
| Optimiser cost reduction, 24 h scenario | **7.25%** (€2,688.70 avoided) | 🔬 EVIDENCE |
| Optimiser CO₂ reduction, 24 h scenario | **3.29%** (169,268.99 → 163,705.39 kg) | 🔬 EVIDENCE |
| Peak demand reduction | **7.89%** (56.0 → 51.58 MW) | 🔬 EVIDENCE |
| Tonnage conserved by the schedule | **960 t** (production is not sacrificed) | 🔬 EVIDENCE |
| Hard-constraint violations | **0** | 🔬 EVIDENCE |
| RUL P10 / P50 / P90 | **18.69 / 19.65 / 20.61 days** | 🔬 EVIDENCE |
| Wear slope / fit quality | **−3.21 mm/day**, r² = **0.88** | 🔬 EVIDENCE |
| Quality what-if | first-pass 88% → **95%** | 🔬 EVIDENCE |
| Automated tests | **1,139** (874 Python + 265 frontend) | 🔬 EVIDENCE |
| Validation gates / live BFF checks | **19 gates**, **66/66** live, **12/12** offline fallback | 🔬 EVIDENCE |
| Self-assessed rubric score | **56 / 60** | Self-assessment |
| Demo running cost | **< €100 / month** | 🔬 EVIDENCE (Sweden Central) |
| Production pilot run cost | **€187k – €408k / year** | 📐 estimate |
| Architecture decisions recorded | **20 ADRs** (ADR-001 … ADR-020) | 🔬 EVIDENCE |
| Agents in the Foundry project | **7** (2 knowledge, 4 specialist, 1 orchestrator) | 🔬 EVIDENCE |

**Two numbers you must never headline:** `rawFlexibleCostPct` = 21.74% and `rawFlexibleCo2Pct` = 31.71%.
They are transparency fields whose denominator counts only movable load; the CO₂ one overstates the
plant-wide effect by roughly 6×. If asked, explain them — never lead with them.

---

# Part 1 — Business personas

The eight primary personas below are the ones named in
[`../business/personas-and-journeys.md`](../business/personas-and-journeys.md) and wired into the
application router. A jury member will often *role-play* one of them: "Imagine I am the furnace
operator…". Answer in that persona's language, not in architecture language.

---

## 1.1 Marc Weber — Plant Manager (Luxembourg HQ) · `plant-manager` · Demo moment DM-1

> *Pain: fragmented reporting across four sites, reactive rather than anticipatory management.*

**PB-01. You already have five reporting tools. Why would you use a sixth?**
Because the other five answer "what happened"; none of them answer "what should I do in the next four
hours". The plant overview is a single decision surface where energy, carbon, furnace health and quality
share one time axis and one site filter. The measure of success is not a new dashboard — it is
KPI-ADO-01: the morning routine collapses from multi-tool triage to one screen.

**PB-02. How long before I trust the numbers on this screen?**
Trust is engineered, not asserted. Every KPI card carries its source, its freshness stamp and its model
version. The `GET /v1/meta` endpoint tells you whether you are reading the lakehouse, a committed
fixture, or a fallback — so a degraded state is visible, never silent. And KPI-QUA-01 is deliberately
displayed as **not met** (0.9494 against a 0.972 objective) because a platform that only ever shows green
is not a decision tool.

**PB-03. Four sites, four cultures, four maturity levels. Does one platform actually fit?**
The data contract is common; the thresholds are per site. Site scoping is a first-class dimension in the
semantic model, and every screen has a site selector rather than a hardcoded plant. 📐 That said, the
demonstration runs one site's synthetic scenario — multi-site is architecturally supported and *not*
proven at scale. Rollout is Phase 1 of the compliance roadmap: one site, read-only shadow mode.

**PB-04. If the platform is wrong and I follow it, who is accountable?**
You are — and the system is designed so that stays true. No recommendation reaches the plant floor
without a named human approval, recorded in the append-only audit chain with the approver identity,
timestamp, model version and the inputs the recommendation was built on. The platform never writes to OT.
That is ADR-007, and it is enforced by a `FORBIDDEN_TOOL_NAMES` list the agents cannot call.

**PB-05. What does my shift supervisor have to learn?**
The interaction vocabulary is intentionally small: select a site, read a card, open a detail panel, ask
the assistant in plain language, approve or reject. There is no query language and no modelling step.
KPI-TRUST-01 tracks whether a supervisor can explain *why* a recommendation was made — comprehension, not
click-through, is the adoption metric.

**PB-06. What happens on a day when the network to Azure is down?**
Nothing on the plant floor changes. The platform is an advisory layer outside the control path: an outage
degrades insight, never control. That is the IEC 62443 FR7 (Resource Availability) property and it is the
single most important design consequence of refusing an inbound control plane.

**PB-07. Give me one number that justifies the project to my board.**
🎯 A 14% cut in energy intensity on a cost base where energy is 35% of conversion cost, plus avoiding a
single €8M lining failure, pays back the build inside a year. 🔬 What is *proven* today is narrower and
honest: on one 24-hour synthetic scenario the optimiser removed 7.25% of energy cost and 7.89% of peak
demand with zero constraint violations and no tonnage lost.

---

## 1.2 Elena Duarte — Furnace Operator · `furnace-operator` · cameo in DM-3 / DM-5

> *"I've run this furnace for 22 years."* Pain: alarm fatigue, and 22 years of tacit knowledge that
> leaves with her.

**PB-08. I've run this furnace for 22 years. Why should I listen to a computer?**
You should not — you should *check* it. The screen is built to be argued with: every recommendation shows
the sensor evidence, the physical reasoning, the confidence, and the procedure it derives from. If your
experience disagrees with the model, the disagreement itself is the valuable signal, and rejecting a
recommendation is a first-class recorded action, not an error state.

**PB-09. Is this going to replace me?**
No — and structurally it cannot. The system has no actuation path. It cannot open a valve, change a
setpoint or start a heat. What it does is make your judgement reusable: the knowledge capture flow turns
your spoken explanation into a draft procedure that another operator can find at 3 a.m.

**PB-10. Another alarm system? I already ignore half of them.**
That is exactly the failure mode the design targets. Instead of threshold alarms, the furnace health view
gives a *trend with a horizon*: 19.65 days of remaining lining life with a P10 of 18.69, not a red light.
An alarm tells you something crossed a line; a horizon tells you how much time you have to act.

**PB-11. When I record my explanation, where does my voice go?**
Into a governed capture flow, not into a model's training set. The audio is transcribed, the transcript is
turned into a draft procedure, and a knowledge engineer reviews it before anything is published. Audio has
a defined retention and a deletion path, and the draft is never indexed for retrieval until it reaches
`APPROVED` status.

**PB-12. What if the assistant tells a new operator something dangerous?**
It is constrained to decline rather than improvise. Retrieval only indexes `APPROVED` procedures, and if
no grounded source clears the relevance guard the assistant returns an explicit refusal
(`no_grounded_source`) instead of a plausible-sounding answer. Declining is a demonstrated behaviour, not
a theoretical safeguard.

---

## 1.3 Sofia Lindqvist — Energy Manager · `energy-manager` · Demo moment DM-2

> *Energy is ~35% of the conversion cost base; day-ahead prices are volatile.*

**PB-13. Optimisers always look good in a slide. What did yours actually do?**
🔬 On the 24-hour scenario it produced a schedule that cut energy cost 7.25% (€2,688.70), cut CO₂ 3.29%,
flattened peak demand from 56.0 to 51.58 MW, and did it while conserving all 960 t of planned production
with zero hard-constraint violations. The comparison is against the same demand under the unoptimised
schedule, not against a strawman.

**PB-14. Why only 3.29% CO₂ when your objective is 22%?**
Because load-shifting alone *cannot* deliver 22%, and pretending otherwise would be the weakest claim in
this defense. Shifting flexible load against the grid carbon curve is worth single digits. The remainder
of the −22% objective depends on grid mix, scrap ratio and process changes that sit outside this
platform's control. The platform's honest contribution is the visible, attributable part.

**PB-15. What is the optimiser, technically? Is it AI?**
It is a mixed-integer linear program — PuLP with the CBC solver — over 96 fifteen-minute slots with binary
batch-to-slot assignment. The objective weights energy against a blended carbon-and-price signal with an
epsilon tie-break for determinism. It is deliberately *not* a neural network: for a schedule an operator
must approve, provable optimality and reproducibility beat model sophistication.

**PB-16. Is it reproducible? I need the same answer twice.**
Yes, and it is enforced. The solver runs single-threaded (`threads=1`) precisely so the branch-and-bound
path is deterministic, and the tie-break epsilon removes ambiguity between equal-cost schedules. Same
inputs, same seed, same schedule — that is a tested invariant, not a hope.

**PB-17. What happens if the solver does not converge?**
It falls back to a deterministic heuristic and *says so*: the response carries a `solver` field set to
`DETERMINISTIC_HEURISTIC`. A degraded answer that announces its own degradation is safe; a silent one is
not.

**PB-18. Where do day-ahead prices and grid carbon intensity come from?**
In the demonstration they are synthetic series shaped to realistic European volatility, at a reference
peak price of 280 EUR/MWh. 📐 In production these are external market and TSO feeds; the ingestion
contract exists, the live connection is a Phase 1 integration item. Nothing in the optimiser changes when
the series becomes real.

**PB-19. Why do I see 21.74% cost and 31.71% CO₂ in the payload but 7.25% and 3.29% on screen?**
Those raw fields express the improvement relative to the *movable* load only — the slice the optimiser can
actually touch. They are exposed for transparency and debugging. The headline figures are plant-wide,
which is the only honest denominator. The raw CO₂ figure overstates the plant-wide effect by roughly six
times, which is exactly why it is not the headline.

---

## 1.4 Tomás Rossi — Maintenance & Reliability Engineer · `maintenance-engineer` · Demo moment DM-3

> *An unplanned furnace lining failure costs €8M. He needs warning, not hindsight.*

**PB-20. 19.65 days of remaining life — how confident should I be?**
Confident enough to plan, not to bet the plant. The estimate comes with a P10 of 18.69 and a P90 of 20.61
days, a model confidence of 0.7846 and a risk score of 0.8995 classified HIGH. Plan against P10. The
interval is the deliverable; the point estimate alone would be misleading.

**PB-21. What model is behind it? Please do not say "deep learning".**
It is not. It is a physics-informed ordinary least-squares fit on refractory wear: the slope is −3.21
mm/day with r² = 0.88, and time-to-failure is `(current thickness − 300 mm minimum safe) / |slope|`, with
the prediction interval derived by the delta method at z = 1.2816. The physics — a monotonic wear process
with a hard safety floor — is what makes a simple estimator defensible.

**PB-22. That is just a straight line. Is that not embarrassingly simple?**
It is simple and it is honest about being simple, which is the correct trade-off at this data volume. A
deep model trained on synthetic data would produce sophistication without validity. The architecture has
an explicit `MLUpliftHook` seam so the estimator can be swapped for a learned model once real campaign
histories exist — the interface is stable, the implementation is intentionally conservative.

**PB-23. Twenty-one days' notice is your objective. Is 19.65 a failure?**
The scenario is deliberately set inside the warning window to show the alerting behaviour. The 🎯 21-day
objective is about *when the platform must first raise the flag*, which depends on the wear trajectory
being established early in the campaign, not on this single snapshot. And it rests on assumption A6: that
a reline can actually be rescheduled with 21 days' notice.

**PB-24. Can I change the reline date from the platform?**
No. The platform produces a recommendation and a justification; scheduling remains in your CMMS. The CMMS
interface is a defined contract, not a live integration in this demonstration — write-back is deliberately
deferred to Phase 2 and gated.

**PB-25. What sensor coverage does this assume?**
Thermocouple and thickness-proxy telemetry at campaign cadence, streamed through the industrial DMZ into
Event Hubs and landed in the lakehouse. 📐 The demonstration uses an in-process simulator (ADR-013)
producing that exact contract, so replacing the simulator with a historian tap is an ingestion change, not
an application change.

---

## 1.5 Jens Bakker — Quality Engineer · `quality-engineer` · Demo moment DM-4

**PB-26. Your what-if takes first-pass yield from 88% to 95%. Prove that is not a slider.**
🔬 It is a scored evaluation: the risk model re-evaluates the batch under the modified parameter set and
returns the new first-pass probability with the contributing factors ranked. What it is *not* is a
causal claim — it says "under this model, these parameters score better", and the model is a documented
bias heuristic (`quality-risk:1.0.0-demo`), not a validated metallurgical predictor.

**PB-27. So the quality model is a heuristic. Why should I take it seriously?**
Because its role is to *structure* the conversation, not to replace metallurgy. It makes the parameter
sensitivities explicit and reproducible so that a disagreement becomes testable. Its limitations are
stated in the technical analysis and it is a named Phase 1 validation item — it is a scaffold with a
declared upgrade path, not a black box being sold as science.

**PB-28. What about the LIMS? My results live there.**
LIMS is one of four enterprise interfaces (with MES, ERP and CMMS) defined as data contracts. 📐 In this
demonstration they are contracts and fixtures, not live integrations, and the technical analysis scores
that gap explicitly rather than hiding it.

**PB-29. Can I trace a decision back to the exact batch and parameters six months later?**
Yes. Every recommendation and approval is written to a SHA-256 hash-chained audit log with the model
version, the input snapshot reference and the approver. The chain verifies end-to-end, so tampering is
detectable rather than merely discouraged.

---

## 1.6 Amina Haddad — Sustainability Officer · `sustainability-officer` · Demo moment DM-6

**PB-30. Can I use these numbers for my EU ETS submission?**
No, and that boundary is deliberate. The platform produces **management information, not regulated MRV**.
Reported figures are not produced under an approved monitoring plan, the free-allocation factor (1.50 t
per t crude steel) and the EUA price (82.0 €) are demo constants, and ETS retention here is 6 years where
MRR Article 66 requires 10 — tracked as gate G2.4.

**PB-31. What about CBAM?**
CBAM is described in the compliance analysis and **not implemented**. Requirement REG-03 is marked partial
for exactly that reason. Claiming CBAM readiness would be the easiest and least defensible overclaim in
this project.

**PB-32. Where does the CO₂ number actually come from?**
From energy consumption multiplied by a time-varying grid carbon intensity, plus process emissions
factors, aggregated on the same time axis as the energy series. That is why the optimiser can report a CO₂
delta at all: shifting load against the carbon curve changes the integral even when total energy is
unchanged.

**PB-33. Your headline is −22% CO₂ but the demo shows 3.29%. Which is it?**
Both, and they answer different questions. −22% is the 🎯 corporate decarbonisation objective for the
plant, achieved mostly through grid mix, scrap ratio and process investment. 3.29% is 🔬 what
load-shifting alone contributed in one scenario. The platform's job is to make the attributable slice
visible and auditable, not to claim the whole reduction.

**PB-34. What would make this audit-grade?**
An approved monitoring plan, 10-year retention, verified emission factors, and the accredited verifier in
the loop — plus a DPIA and, if Legal reclassifies the system, a FRIA. Those are enumerated gates in the
compliance roadmap, not aspirations.

---

## 1.7 Pieter Claes — Knowledge Engineer / Admin · `knowledge-engineer` · Demo moment DM-5

**PB-35. Who decides what the assistant is allowed to say?**
You do, through the procedure lifecycle. Only documents in `APPROVED` status enter the retrieval index. A
draft — even a good one — is invisible to the assistant. Publication is a human transition recorded in the
audit chain, and the approve/publish/reject actions are on the agents' forbidden-tool list, so no model
can promote its own content.

**PB-36. How does retrieval work, and how do you stop it inventing citations?**
Hybrid retrieval: BM25 lexical scoring and vector cosine similarity fused with reciprocal rank fusion. RRF
always returns *something*, which is the classic failure mode, so a content-term guard requires a genuine
token overlap of at least four characters before a passage qualifies as grounding. If nothing qualifies,
the assistant declines with a typed reason rather than answering.

**PB-37. What are the decline reasons, exactly?**
`no_grounded_source`, `content_policy_violation`, and `citation_enforcement_failed`. Each is a distinct,
testable path — the third exists specifically to catch the case where an answer was generated but its
citations could not be verified against the retrieved set.

**PB-38. We operate in five languages. Does that hold up?**
Retrieval and response support EN, FR, DE, NL and ES, matching the four-site footprint. 📐 Cross-lingual
retrieval quality is uneven by construction and is a Phase 1 evaluation item — a Dutch operator asking
about a French-authored procedure is exactly the case that needs measurement before rollout.

**PB-39. Can I delete a procedure and have it truly gone?**
From the retrieval index, yes, immediately. From the audit chain, no — and that is intentional. Erasure
appends an `erasure.executed` tombstone with a salted pseudonym of the subject; it never mutates prior
blocks. The receipt records `chainVerifiedBefore` and `chainVerifiedAfter` so you can prove the chain
stayed intact across the erasure.

---

## 1.8 Isabelle Moreau — Executive / COO · `executive` · Demo moment DM-6

**PB-40. Thirty seconds. What is this?**
A decision-support layer over four steel plants that turns energy, carbon, furnace health and quality data
into ranked, explainable actions a human approves. It never touches the process. 🎯 The prize is 14% less
energy intensity and avoiding €8M furnace failures; 🔬 what is proven today is a working system that cut
7.25% of energy cost on a reproducible scenario with zero constraint violations.

**PB-41. What is the total cost of ownership?**
📐 Build is estimated at €560k–€1.12M; annual run for a production pilot at €187k–€408k. The demonstration
environment itself runs under €100 a month. Payback is estimated under 12 months conservatively and under
9 months in the base case — those are illustrative models, not quotations.

**PB-42. What is the single biggest risk to this programme?**
Adoption, not technology. The platform is advisory, so its value is realised only when operators act on
it. That is why the adoption KPIs measure comprehension rather than logins, and why Phase 1 is a
read-only shadow pilot on one site — proving the recommendations would have been right before anyone is
asked to follow them.

**PB-43. Why should we not just buy this from a vendor?**
For the analytics layer you probably should evaluate one. What is not buyable off the shelf is the
governance spine: the approval chain, the audit invariants, the OT boundary and the AI Act posture, all
tied to your own data estate. This architecture makes those the product and treats the models as
replaceable components.

**PB-44. When do we know it worked?**
At the Phase 1 exit gate: shadow-mode recommendations compared against what operators actually did, with
agreement rate, energy delta attributable to accepted recommendations, and false-alarm rate on lining
warnings. If those do not clear, Phase 2 does not start — the roadmap gates are stop conditions, not
milestones.

---

## 1.9 Rui Almeida — OT Systems Engineer (supporting persona)

**PB-45. What are you plugging into my control network?**
Nothing inbound. Telemetry leaves through the Level 3.5 industrial DMZ as an **outbound-only** flow with a
protocol break; the cloud side has no route back into the process network. That is the reason ADR-016
chose Event Hubs over IoT Hub: IoT Hub's device-management model would create exactly the inbound control
plane we refuse to acquire.

**PB-46. Purdue levels — where does each component sit?**
Zones are Z-CTRL (SL3), Z-SUP (SL2-3), Z-HIST (SL2), Z-DMZ (SL3) and Z-CLOUD (SL2). The DMZ is the only
IT↔OT crossing. Conformance is claimed as *design* conformance to IEC 62443 — **no certification is
claimed**, and pretending otherwise would be trivially disprovable.

**PB-47. If your cloud is compromised, what can the attacker do to my furnace?**
Nothing directly. There is no command path, no writable OT endpoint and no credential in the cloud that
authenticates to a controller. The worst case is corrupted advice, which is why every recommendation
requires a human approval and every approval is auditable. The threat model treats "attacker influences a
human decision" as the real attack, and mitigates it with provenance rather than with network controls
alone.

**PB-48. What is the sensor-to-screen latency?**
The SLO is under five seconds of data freshness with p95 API latency below 800 ms. 📐 Measured in the
demonstration topology on synthetic volumes — not validated against production tag counts or a real
historian, which is a Phase 1 measurement item.

---

## 1.10 Nils Andersen — Platform Ops (supporting persona)

**PB-49. Who gets paged, and for what?**
Alert rules cover availability, latency, ingestion freshness, capacity state and a Sev-1 security rule
that fires if a dispatch tool call ever appears without a matching human-approval audit event. 📐 The
Activator rules are templates in the repository rather than provisioned production monitors — that gap is
scored explicitly in the technical analysis.

**PB-50. You pause the Fabric capacity every night. What breaks?**
Everything that reads the lakehouse — visibly. `GET /v1/meta` reports `dataSource` as `fabric-fallback:*`
instead of `fabric-lakehouse:*`, and the UI surfaces the degraded state. Resume SLO is under 10 minutes.
The pause is **non-production only** and a production capacity is never auto-paused.

**PB-51. Show me the runbook for a bad deployment.**
Redeploy the previous tagged revision through the same pipeline; infrastructure is idempotent Bicep so
re-applying a known-good template converges. 📐 There is no blue-green swap or automated rollback gate
today — that is an honest maturity gap, listed under the reliability criterion.

---

# Part 2 — Technical & governance personas

These are the personas most likely to be *in the room* at the defense: they are not users of the plant,
they are gatekeepers of the architecture.

---

## 2.1 CISO / Head of Security

**PT-01. Walk me through your threat model in one minute.**
STRIDE applied per trust boundary, extended with eight abuse cases specific to an advisory AI system —
prompt injection through ingested procedures, recommendation poisoning, approval spoofing, audit
tampering, exfiltration through the assistant, model-endpoint abuse, over-privileged relay identity and
insider misuse of the knowledge pipeline. Each maps to one of eleven acceptance gates, G1 through G11.

**PT-02. What is your worst-case breach scenario?**
An attacker who compromises the BFF identity and forges plausible recommendations that a human then
approves. The mitigation is not perimeter — it is provenance: recommendations carry their model version
and input snapshot, approvals are hash-chained, and a Sev-1 Sentinel rule fires if a dispatch tool call
ever lacks a matching approval event. The blast radius is bounded because there is no actuation path.

**PT-03. How do you authenticate? Any secrets in the codebase?**
Microsoft Entra ID with managed identities for service-to-service, workload identity federation via OIDC
for CI/CD, and Key Vault for the residue. Notably, ADR-005 chose an **identity-based** Fabric Custom
Endpoint specifically to eliminate SAS tokens. There are no long-lived credentials in the repository.

**PT-04. Ten application roles is a lot. Justify it.**
Each maps to a distinct approval or publication authority — the roles exist because the audit trail has to
answer "who was allowed to approve this", and a coarse role model makes that unanswerable. Separation of
duties between the person who drafts a procedure and the person who publishes it is a role boundary, not
a convention.

**PT-05. Conditional Access — is it in the code or on a slide?**
Six policies, CA-01 through CA-06, plus PIM with a maximum 8-hour activation for privileged roles. 📐 They
are **documented, not deployed in the Bicep**. That is a real gap and it is scored as such in the security
criterion — tenant-level policy is deliberately outside this subscription's IaC scope, but that is an
explanation, not an excuse.

**PT-06. What stops an agent from doing something destructive?**
A `FORBIDDEN_TOOL_NAMES` deny-list covering eight actions: approve, publish and reject a procedure;
approve a recommendation; commit a schedule; delete audio; delete a procedure; and transition a status.
Beyond the runtime deny-list, the two knowledge agents are asserted to have **zero function tools at all**,
and that invariant is verified in CI — a pull request that gives the procedure agent a tool fails the
build.

**PT-07. Prompt injection through an ingested procedure — how do you survive it?**
Three layers. Only `APPROVED` documents are indexed, so injection requires passing human review.
Retrieved content is treated as data, not instruction, and citations are verified against the retrieved
set. And even a fully successful injection cannot reach a privileged action, because the tools that
matter are not on the agent's roster at all.

**PT-08. How would I detect tampering with your audit log?**
By verifying the chain. Each entry hashes the previous one, the genesis block is 64 zeros, and there is a
`verify()` invariant exercised by tests. Any mutation of a historical entry invalidates every subsequent
hash. Append-only is enforced structurally rather than by permission alone.

**PT-09. Did you run a real security scan?**
There is an automated security workflow in CI, and it is a **lightweight scanner** — dependency and secret
scanning, not DAST or a penetration test. Claiming a pen test would be false. External testing is a
Phase 1 gate.

**PT-10. Where is data stored, and does anything leave the EU?**
Sweden Central primary with West Europe as the recovery region — both EU. Model inference stays on
regional Azure AI Foundry deployments. There is no third-party API call outside the EU boundary in the
runtime path.

**PT-11. What is your most over-privileged component?**
The relay identity for the Fabric Custom Endpoint requires Workspace **Contributor**, which is wider than
the read-only grant we would prefer, because Fabric does not expose a finer-grained role for this pattern.
It is documented as an accepted risk with a compensating control — the identity is scoped to a single
workspace and its actions are audited.

---

## 2.2 Software / Solution Architect

**PT-12. Justify the polyglot front end. Blazor *and* React?**
The Blazor WebAssembly shell owns shell concerns — authentication, navigation, layout persistence — while
the analytics micro-frontend is React with MUI and D3 because the data-visualisation ecosystem there is
strictly better. ADR-014 defines a two-level Dockview composition so the boundary is explicit. The honest
counter-argument is that a single-framework SPA would be simpler; the trade was made for visualisation
capability and to demonstrate a real micro-frontend contract.

**PT-13. Why a Python BFF instead of calling Fabric and Foundry from the browser?**
Because the BFF is where authority lives. ADR-006 is explicit: the Python service is authoritative and
Azure AI Foundry is **not** the controller. Orchestration, tool policy, audit writes and the approval
gate all sit in code we own and test, not in a hosted agent's opaque loop. It also keeps tokens off the
client.

**PT-14. Twenty ADRs — which three would you defend hardest?**
ADR-006 (Python authoritative, Foundry not the controller) because it is what makes the system auditable.
ADR-007 (human approval, no direct OT action) because it defines the safety envelope. ADR-016 (Event Hubs
over IoT Hub) because refusing a capability is a harder and better decision than adding one.

**PT-15. ADR-020 collapsed two Foundry projects into one. Is that not a regression?**
On one axis, yes, and the ADR says so. Two projects gave a hard tenancy boundary between knowledge and
action agents. One project with a manifest-plus-CI-enforced read/call boundary gives lower operational
complexity and a boundary that is *tested* rather than merely configured. It is a net posture reduction on
isolation traded for verifiability and cost — recorded as such rather than presented as pure improvement.

**PT-16. You hand-rolled a StateGraph instead of using LangGraph. Why?**
To keep the orchestration surface small, dependency-light and fully testable, and to avoid a framework
upgrade cadence in a system whose selling point is determinism. The cost is that we reimplemented
machinery someone else maintains. It is a defensible trade for this scope and a poor one at ten times the
agent count.

**PT-17. How do agents get selected? Is there a supervisor LLM?**
No — routing is a **deterministic keyword scorer**. Seven agents: two knowledge agents with zero tools,
four domain specialists with one tool each, and one operations orchestrator holding all four. Deterministic
routing means the same question routes the same way every time, which matters far more than routing
elegance when you have to explain a decision six months later.

**PT-18. What are the seams you would extend first?**
The `MLUpliftHook` for swapping estimators, the solver abstraction behind the MILP (CBC to HiGHS or a
commercial solver), the enterprise interface contracts for MES/ERP/LIMS/CMMS, and the agent roster which
is currently static. Each is an interface with fixtures behind it, so extension does not touch the
orchestration core.

**PT-19. What would you do differently if you started again?**
Put the idempotency store in a durable backing service from day one rather than in memory, introduce a
real job queue instead of a single synchronous request path, and write the load test early — the three
gaps that cost points are all "we deferred the operational scaffolding".

**PT-20. Is this over-engineered for a demonstration?**
For a demonstration, parts of it are — the audit chain and the compliance mapping exceed what a demo
needs. That is deliberate: the brief is a production architecture evidenced by a working demo, and the
governance spine is the part that cannot be retrofitted later.

---

## 2.3 Data Architect / Data Engineer

**PT-21. Why Microsoft Fabric rather than assembling the components?**
ADR-001 makes Fabric the core because the alternative — Event Hubs plus Databricks plus Synapse plus a
separate semantic layer plus Purview — is five integration surfaces and five identity models to govern.
One capacity, one workspace security model, one lineage story. The cost is SKU coupling and less
per-component tuning freedom, which the ADR states.

**PT-22. Explain the hot path versus the governed path.**
ADR-002: streaming telemetry lands in an eventhouse KQL database for sub-second interactive querying,
while the curated, governed, versioned data lives in Delta tables in the lakehouse. Two paths because the
access patterns are genuinely different — an operator scrubbing a live trend and an auditor
reconstructing a decision have nothing in common.

**PT-23. Medallion architecture — is it real or a diagram?**
Bronze/silver/gold layering with contracts at each boundary, four workspaces per environment
(`RTI-Ingress`, `DataCore`, `ML`, `Analytics`). 📐 The Fabric pipeline items are **specified but not
deployed** in the demo environment — `cd-fabric-items.yml` is a placeholder workflow. That is the single
largest honesty point on the data side and it is scored in the implementation-completeness criterion.

**PT-24. Two streams into Fabric — why?**
ADR-018 separates the telemetry stream from the event/decision stream so that retention, schema evolution
and access control can differ. Sensor data is high-volume and short-retention; decision events are
low-volume and long-retention with audit obligations. One stream would force the strictest policy on the
largest volume.

**PT-25. How do you keep the demo reproducible if the data is generated?**
Seed `240725`, a committed fixture pack, and a five-rung fallback ladder: live services → committed
fixtures → local deterministic replay → cached interactive state → recorded proof pack. Any rung produces
the same numbers. ADR-017 mandates one data path with an unconditional synthetic-data banner, so nobody
can mistake the scenario for production data.

**PT-26. Schema evolution — what happens when a plant adds tags?**
Additive changes flow through the bronze contract without breaking downstream because the silver
projection is explicit rather than `select *`. Breaking changes require a contract version bump. 📐 That
is a designed process, not one exercised under change pressure in this demonstration.

**PT-27. What is your data quality strategy?**
Contract validation at ingestion, expectation checks between medallion layers, and freshness surfaced to
the user rather than hidden. The user-visible part matters most: a stale or fallback source is displayed,
so a data quality failure becomes a visible degradation instead of a confidently wrong number.

---

## 2.4 AI / ML Engineer

**PT-28. Which models, and why those?**
`gpt-5.4-mini` as the default chat deployment and `gpt-5.5` for reasoning, with an automatic tier
escalation: questions over 120 characters or containing comparison, causal or simulation markers
("why", "compare", "simulate") route to the high tier. Cheap model by default, expensive model when the
question actually needs it — measured by question shape, not by user choice.

**PT-29. How do you version and track models?**
Explicit semantic versions on every analytical artefact: `energy-dispatch-deterministic:2.1.0`,
`lining-rul-piml:1.3.0-demo`, `quality-risk:1.0.0-demo`, and the version travels into the audit record
with each recommendation. 📐 There is **no MLflow registry artefact** in the repository and no live model
evaluation metrics — that is why this criterion is self-scored 4 out of 5 rather than 5.

**PT-30. Do you evaluate the RAG pipeline?**
There are behavioural tests for the decline paths and the grounding guard, which is the safety-critical
half. 📐 There is **no golden-set retrieval benchmark** with precision/recall numbers. Building one over
approved procedures in five languages is a named Phase 1 activity, and I would rather say that than quote
an unmeasured accuracy figure.

**PT-31. Why is the RRF guard necessary?**
Because reciprocal rank fusion is a ranking function, not a relevance threshold — it will always return a
top result even when nothing is relevant. The `_shares_content_term` guard requires a real token overlap
of at least four characters before a passage counts as grounding. Without it, the assistant would answer
every question, which for an operator-facing system is worse than declining.

**PT-32. Prompt management — where do prompts live?**
In versioned source, reviewed like code, not in a portal. That is a direct consequence of ADR-006: if the
Python service is authoritative, its prompts have to be under the same review and rollback discipline as
its logic.

**PT-33. What is your hallucination rate?**
I do not have a measured rate and I will not invent one. What I can demonstrate is the *architecture* that
bounds the consequence: grounded-only answering, typed decline reasons, citation verification, and no
privileged tool on the knowledge agents. Measuring the residual rate is a Phase 1 gate, not a claim.

**PT-34. Is the "agentic" label earned, or is this a chatbot with steps?**
It is earned on orchestration and coordination — a stateful graph, specialist agents with bounded tools,
deterministic routing, and inter-agent handoff. It is *not* earned on autonomy: this is a single
synchronous request-response with no persistent job queue and no long-running goal pursuit. The technical
analysis states exactly that.

---

## 2.5 SRE / Platform Engineer

**PT-35. What are your SLOs and are they measured?**
99.5% availability, p95 API latency under 800 ms, SSE stream establishment under 5 s, data freshness under
5 s, capacity resume under 10 minutes. 📐 They are defined and instrumented; they are **not** validated
under load, and there is no formal SLA. Honest position: these are engineering targets with telemetry
behind them, not contractual commitments.

**PT-36. Have you load tested?**
No. There is no load test in the repository, and that is one of the specific reasons the
performance-and-reliability criterion is self-scored 4 out of 5. A k6 or Locust profile against the BFF is
the first thing I would add before a pilot.

**PT-37. Circuit breakers, retries, bulkheads?**
Not implemented. Timeouts and graceful degradation are, and the fallback ladder covers the dependency
failure case at the data layer. But there is no circuit breaker around the Foundry or Fabric calls, and
adding Polly-style resilience policies is a named gap rather than a hidden one.

**PT-38. What is your RTO and RPO?**
📐 The design targets a West Europe recovery region with infrastructure reproducible from Bicep, which
makes the RTO a function of redeploy time plus data replication. **DR has not been tested.** An untested
DR plan is a document, not a capability, and I will not quote an RTO I have not exercised.

**PT-39. How much of the platform is in infrastructure as code?**
Twenty Bicep modules across six resource groups, deployed by GitHub Actions with OIDC workload identity
federation — no stored cloud credentials. The exceptions are tenant-scope items: Conditional Access and
PIM, which are documented but applied outside this IaC.

**PT-40. How do you observe an agent run?**
Structured logging with correlation identifiers spanning the request from the UI through the BFF to the
model call, plus metrics on latency, token use and decline reasons. 📐 The Azure Monitor workbook is
described but there is **no workbook JSON committed**, and the Activator alert rules are templates.

**PT-41. What is your on-call story?**
There is not one, and there should not be a fictional one. This is a demonstration environment with alert
rules defined but no rota, no escalation policy and no incident history. Operational readiness is a Phase 1
exit gate.

---

## 2.6 Data Protection Officer / Legal Counsel

**PT-42. Is there personal data in this system at all?**
Yes, and it is deliberately minimised: identities of approvers and authors, and operator voice recordings
in the knowledge capture flow. There is no process data that identifies an individual. Voice is the
sensitive category and it has an explicit retention and deletion path.

**PT-43. Article 17 erasure against an immutable audit chain — how do you reconcile those?**
By separating the personal data from the integrity proof. Erasure removes the content and appends an
`erasure.executed` tombstone referencing a **salted SHA-256 pseudonym** of the subject; it never rewrites a
prior block. The receipt carries `chainVerifiedBefore` and `chainVerifiedAfter`, so the data subject gets
proof of erasure and the auditor keeps an intact chain.

**PT-44. Is that legally sufficient?**
It is a defensible design under the accepted reading that integrity records may be retained on legal-basis
grounds while the personal content is erased and pseudonymised. 🎯 Confirmation is a legal review item —
assumption A8 states that classification and this reconciliation both require counsel sign-off, and a DPIA
is a Phase 1 gate.

**PT-45. Under the EU AI Act, what is this system?**
The stated posture is "**high-risk-adjacent**". The argument: it is not in an Annex III category — there is
no entry for industrial process optimisation — and it is not an Article 6(1) safety component of a product
because there is no actuation path. But it is *built* to Chapter III obligations anyway.

**PT-46. Is that not just avoiding the classification?**
The opposite: it means a reclassification costs nothing architecturally. Article 12 logging is satisfied by
the hash chain, Article 13 transparency by the evidence-and-provenance UI, Article 14 human oversight by the
mandatory approval gate, and Article 50 disclosure by the unconditional AI and synthetic-data banners. If
Legal says high-risk tomorrow, we add documentation and a FRIA, not a redesign.

**PT-47. Who is the provider and who is the deployer?**
In a real deployment AxelorMetal would be the deployer, and the provider role depends on whether the system
is built in-house or procured. That distinction changes the obligation split materially and is exactly the
kind of question a FRIA scoping exercise resolves.

**PT-48. Data residency — can you prove nothing leaves the EU?**
Region pinning to Sweden Central and West Europe, EU-resident model deployments, and no third-party
egress in the runtime path. Proof at audit grade needs Azure Policy enforcement and a policy compliance
report, which is a hardening item rather than a demonstrated control.

---

## 2.7 Compliance Officer / Internal Auditor

**PT-49. Show me you can reconstruct a decision from twelve months ago.**
Every recommendation and approval writes an audit entry containing the model version, the input snapshot
reference, the recommendation payload, the approver identity and the timestamp, hash-chained to its
predecessor. Reconstruction is a chain walk plus a fixture fetch, and the chain verification proves the
record was not altered in between.

**PT-50. What are your retention periods and are they consistent?**
They vary by category, and one is knowingly short: ETS-related data is retained six years where MRR
Article 66 requires ten. That mismatch is documented as gate G2.4 rather than quietly rounded up.

**PT-51. Which regulatory requirements are only partially met?**
REG-03 for CBAM is partial — described, not implemented. DPIA and FRIA are unstarted pilot gates. IEC
62443 is design conformance with no certification. The compliance roadmap lists residual risks RR-1
through RR-7 explicitly, and out-of-scope items O1 through O7, of which O7 — no real production data —
frames everything else.

**PT-52. How do I know the controls work rather than merely exist?**
Eleven acceptance gates, G1 through G11, each with a test. The most interesting is the one that says a
dispatch tool call without a matching human approval must raise a Sev-1 — a control that produces an
alert when violated is auditable in a way that a policy statement is not.

---

## 2.8 CFO / FinOps

**PT-53. What does this actually cost to run today?**
Under €100 per month for the whole demonstration in Sweden Central, because the Fabric capacity is an F2
paused nightly. At full-time pay-as-you-go, F2 alone is roughly €263 per month.

**PT-54. And in production?**
📐 €187k to €408k per year for a pilot, driven mainly by a materially larger Fabric capacity — F64 is the
indicative production tier — plus model inference and observability. Build is estimated at €560k to
€1.12M. These are planning ranges from published list pricing, not quotes.

**PT-55. What stops the cost running away?**
Capacity is a fixed reservation rather than a per-query charge, which caps the largest line item by
construction. Model spend is bounded by the cheap-by-default tiering. 📐 Budget alerts and cost anomaly
detection are designed but not provisioned — a genuine gap for a production deployment.

**PT-56. How do you justify a nine-month payback on a 7.25% result?**
I do not justify it on 7.25%. The payback model rests on the 🎯 targets — 14% energy intensity on a 35%
cost base, plus avoided €8M failures — and it is explicitly illustrative. The 7.25% is 🔬 evidence that the
mechanism works on one scenario. Conflating the two would be the dishonest version of this answer.

**PT-57. What if we only ever get the 7.25%?**
Then the business case narrows to peak-demand savings and avoided failures, and the honest answer is that
it becomes a marginal call at €187k a year for one site — which is precisely why Phase 1 is a shadow
pilot that measures the real delta before anyone commits to a multi-site rollout.

---

## 2.9 Procurement / Vendor Management

**PT-58. How locked in are we to Microsoft?**
Deeply, and deliberately — ADR-001 chose Fabric as the core. The portable parts are the Python domain
logic, the MILP model, the RUL estimator and the React front end, all of which are framework-agnostic.
The non-portable parts are ingestion, the semantic layer and the agent hosting. The exit cost is real and
was accepted for integration and governance velocity.

**PT-59. What is the third-party dependency footprint?**
Minimal by design: PuLP with CBC for optimisation, standard scientific Python, FastAPI, MUI and D3. All
packages are restored through the organisation's protected feed proxy, not from public registries — that
is a supply-chain policy, not a preference.

**PT-60. Could we swap the LLM provider?**
The model interaction is behind the BFF, so swapping the deployment is a configuration and prompt-tuning
exercise. The agent hosting and tool-calling contract are Foundry-shaped, so a provider change would
require reimplementing the orchestration adapter — days, not weeks, but not free.

---

## 2.10 QA / Test Lead

**PT-61. What is actually tested?**
1,139 automated tests — 874 Python and 265 frontend — covering domain logic, the optimiser's determinism
and constraint satisfaction, the RUL estimator, the audit chain invariants, the retrieval guards and the
decline paths, plus the API contract. On top, 19 validation gates, 66 out of 66 live BFF checks and 12
out of 12 offline fallback checks.

**PT-62. Test count varies between documents. Which is right?**
The validation report says 1,139; an earlier development document says 1,168. The difference is a
measurement-date variance as tests were added, and I would rather point at it than have you find it. The
reproducible number is whatever `pytest` and the frontend runner report at the commit you are looking at.

**PT-63. What is *not* tested?**
Load and concurrency, disaster recovery, cross-lingual retrieval quality, real integration with MES, ERP,
LIMS or CMMS, and the Fabric pipeline items that are specified rather than deployed. Every one of those
appears in the technical analysis gap list.

**PT-64. Are these real tests or assertion theatre?**
The ones that matter assert behaviour, not shape. The optimiser tests check that zero hard constraints are
violated and that identical inputs yield identical schedules; the audit tests corrupt an entry and assert
the chain fails to verify; the retrieval tests assert a decline when grounding is absent. Those fail
loudly if the logic regresses.

---

## 2.11 UX / Frontend Lead

**PT-65. How many screens, and who decided the information hierarchy?**
The screen inventory follows the persona journeys: each of the eight primary personas has a home surface
plus the shared device-operations and platform-ops views. The hierarchy is derived from the demo moments
DM-1 to DM-6 — the screen exists to make one decision, and everything else on it supports that decision.

**PT-66. Accessibility?**
Colour is never the sole encoder of state, focus order follows the visual order and the component library
provides the ARIA baseline. 📐 There is no audited WCAG conformance statement, and an industrial
environment with gloves, glare and noise needs a field usability study that has not been done.

**PT-67. How do you visualise uncertainty without confusing people?**
By showing the interval as the primary object rather than the point estimate — the P10/P90 band is drawn,
not just tabulated, and the number people are told to plan against is P10. Uncertainty presented as a
range with an instruction is usable; uncertainty presented as a decimal is noise.

**PT-68. Why Dockview and a two-level layout?**
ADR-014: the shell owns the outer dock so the micro-frontend can compose its own panels without fighting
the host for layout state. It lets an operator arrange a workspace that persists across sessions, which
matters for a screen someone stares at for eight hours.

---

## 2.12 Change Manager / Training Lead

**PT-69. What is the training burden?**
Deliberately low: no query language, no model configuration, no report authoring. The learnable surface is
navigation plus the approve/reject decision plus asking a question in your own language. The trust KPI
measures whether a user can explain a recommendation, which is the only training outcome that matters.

**PT-70. How do you handle the operator who refuses to use it?**
By treating rejection as data. A rejected recommendation with a reason is a labelled disagreement between
model and expertise, and Phase 1 shadow mode is designed to accumulate exactly those. If the disagreement
rate stays high, the model is wrong and the gate does not pass.

**PT-71. Five languages, four countries, one works council. Any employee-relations exposure?**
Yes — voice capture in particular. The design keeps recordings scoped to a voluntary knowledge-capture
action rather than ambient monitoring, with retention limits and a deletion path. Works-council
consultation is a Phase 1 prerequisite, not an afterthought.

---

# Part 3 — Rating-grid questions (the examiner persona)

Source rubric: [`../usecase/rating_grid.md`](../usecase/rating_grid.md) — 7 categories, 12 criteria,
60 points. Bands: **A** 54–60, **B** 48–53, **C** 40–47, **D/F** below 40.
Self-assessment: [`../tech/technical-analysis.md`](../tech/technical-analysis.md) — claimed **56/60 (A)**.

> **How to answer a rubric question.** Three beats, always in this order:
> **(1)** the evidence that earns the score, **(2)** the artefact where the examiner can verify it,
> **(3)** the gap you are choosing to disclose. Volunteering the gap *before* it is found is worth more
> than the point it might cost.

| Criterion | Category | Self-score |
| --- | --- | --- |
| TR-DES-01 System architecture, modularity, scalability | Design | 5/5 |
| TR-DES-02 Use of design patterns | Design | 5/5 |
| TR-DES-03 Security | Design | 5/5 |
| TR-DEV-01 Application demo | Development | **4/5** |
| TR-DEV-02 Implementation completeness | Development | **4/5** |
| TR-MON-01 Logging and metrics | Monitoring | 5/5 |
| TR-AI-01 Use of AI technologies | AI Integration | 5/5 |
| TR-AI-02 AI model selection and deployment | AI Integration | **4/5** |
| TR-AGT-01 Autonomy and orchestration | Agentic | 5/5 |
| TR-AGT-02 Multi-agent coordination | Agentic | 5/5 |
| TR-ARC-01 Performance and reliability | Additional | **4/5** |
| TR-PRE-01 Clarity of explanation | Presentation | 5/5 |
| **Total** | | **56/60** |

---

## 3.1 TR-DES-01 — System architecture, modularity, scalability *(claimed 5/5)*

**RG-01. Summarise the architecture in ninety seconds.**
Four tiers. Ingestion: OT telemetry leaves through a Level 3.5 DMZ, outbound only, into Event Hubs.
Data: Microsoft Fabric with a hot KQL eventhouse for interactive querying and governed Delta tables for
curated history, across four workspaces per environment. Application: a Python FastAPI BFF that owns
orchestration, tool policy, audit and the approval gate, calling Azure AI Foundry. Presentation: a Blazor
WebAssembly shell hosting a React analytics micro-frontend. Twenty ADRs record why each boundary is where
it is.

**RG-02. What makes it modular rather than merely layered?**
Every cross-tier interaction is a contract with fixtures behind it — the enterprise interfaces, the
simulator, the model artefacts, the retrieval index. That is what makes the demonstration runnable
offline: swapping an implementation behind a contract does not touch the orchestration core. The
`MLUpliftHook` and the solver abstraction are the clearest examples.

**RG-03. Where does it scale, and where does it not?**
It scales horizontally on the stateless BFF and vertically on the Fabric capacity, which is the dominant
knob — F2 for the demo, F64 indicative for production. 📐 It does **not** scale today on the orchestration
path: a single synchronous request with an in-memory idempotency store, which is the honest ceiling. Both
statements are in the technical analysis.

**RG-04. Why should this be a 5 when multi-site is only architectural?**
Because site scoping is a first-class dimension throughout the model and the API rather than a retrofit,
and because the criterion asks for scalability *considerations*, documented. What I will not claim is
multi-site *proof* — there is no load test and the Fabric pipeline items are specified, not deployed. If
you weigh proof over design, mark it 4 and I will not argue.

---

## 3.2 TR-DES-02 — Use of design patterns *(claimed 5/5)*

**RG-05. Which patterns, and where?**
Backend-for-frontend for the API tier. Micro-frontend with a shell/remote split. Strategy behind the
solver and the ML uplift hook. A state graph for agent orchestration. Circuit-free graceful degradation
via the five-rung fallback ladder. Repository and contract patterns at the data boundaries. Append-only
event sourcing for the audit chain. Deny-list policy enforcement for tool governance.

**RG-06. Is a hand-rolled StateGraph a pattern or a reinvention?**
It is a deliberate implementation of a known pattern rather than adoption of a framework. The reasoning:
determinism and testability matter more here than feature breadth, and LangGraph would add an upgrade
cadence to the component whose behaviour must be most stable. The counter-argument is legitimate and is
recorded — at ten times the agent count I would take the framework.

**RG-07. Any anti-patterns you are aware of in your own code?**
Yes — the in-memory idempotency store is a singleton with process-scoped state, which is fine for one
replica and wrong for many. It is the first thing I would move to a durable store, and it is disclosed
rather than discovered.

---

## 3.3 TR-DES-03 — Security *(claimed 5/5)*

**RG-08. What earns a 5 here?**
A threat model that is specific to this system rather than generic: STRIDE per boundary plus eight
AI-specific abuse cases, eleven acceptance gates with tests, ten application roles built around approval
authority, managed identities and OIDC federation with no stored credentials, a tool deny-list, a
CI-enforced zero-tool invariant on the knowledge agents, a hash-chained audit log, and an OT boundary that
architecturally refuses inbound control.

**RG-09. And what would cost you the 5?**
Three things, all disclosed: Conditional Access and PIM are documented but not in the IaC because they are
tenant-scope; the CI security scan is lightweight dependency-and-secret scanning, not DAST or a
penetration test; and the Fabric relay identity needs Workspace Contributor, which is broader than we
would like.

**RG-10. Give me one security control that a typical project would not have.**
The Sev-1 rule that fires when a dispatch tool call appears without a matching human-approval audit event.
It is a detection control on the *governance* invariant rather than on the network — it catches the
scenario where the safety property has been bypassed regardless of how.

---

## 3.4 TR-DEV-01 — Application demo *(claimed 4/5)*

**RG-11. Why did you score yourself 4 instead of 5?**
Because the demonstration does not exercise two things it describes: the Fabric assets are not wired live
into the demo path, and the Power BI embed is not exercised. A demo that shows a screen backed by a
fixture while the narrative says "Fabric" would be a gap you would find, so I score it and state it.

**RG-12. What is the executive hook?**
One screen, six minutes, six moments: DM-1 the plant overview replacing multi-tool triage, DM-2 the
optimiser producing a scheduled saving with zero violations, DM-3 the lining warning with an uncertainty
band, DM-4 the quality what-if, DM-5 knowledge capture from an operator's voice, DM-6 the executive and
sustainability rollup. Each ends with a human approving or rejecting.

**RG-13. What happens if the live demo fails in front of us?**
I drop a rung on the fallback ladder and say so out loud. Live services, then committed fixture pack, then
local deterministic replay, then cached interactive state, then a recorded proof pack. Every rung produces
the same numbers because they come from the same seeded scenario, so the argument does not change — only
the fidelity does.

**RG-14. Is the demo data synthetic, and is that disclosed?**
Entirely synthetic, seed `240725`, and ADR-017 mandates an **unconditional** synthetic-data banner — it is
not dismissible and not conditional on environment. Out-of-scope item O7 states plainly that no real
production data is used.

---

## 3.5 TR-DEV-02 — Implementation completeness *(claimed 4/5)*

**RG-15. What is genuinely built versus described?**
Built and running: the BFF with its domain services, the MILP optimiser, the RUL estimator, the quality
risk model, the retrieval pipeline with its guards, the seven agents with deterministic routing, the audit
chain, the Blazor shell and React micro-frontend, twenty Bicep modules and seven workflows, 1,139 tests.
Described only: MES, ERP, LIMS and CMMS integrations, which are contracts and fixtures; and the Fabric
item deployment, where `cd-fabric-items.yml` is a placeholder.

**RG-16. Fifty functional requirements — how many are met?**
The proof-of-execution table lists nineteen entries, of which fifteen are met directly and four are met by
surrogate — the surrogate cases being where a fixture stands in for an integration that does not exist
yet. Marking those as "met" without the surrogate label would be the easy overclaim.

**RG-17. Is a placeholder CI workflow not worse than no workflow?**
It is worse if it is presented as working, which is why it is named in the technical analysis as the
principal completeness gap. It exists as a declared shape for the deployment that Phase 1 has to fill in.

---

## 3.6 TR-MON-01 — Logging and metrics *(claimed 5/5)*

**RG-18. What does structured logging mean here concretely?**
Correlation identifiers propagate from the UI action through the BFF, the orchestration graph and the
model call, so a single user request is one queryable trace. Logs are structured records with typed fields
— decline reason, model version, solver status, data source — not formatted strings.

**RG-19. Which metrics actually matter for this system?**
Data freshness and the `dataSource` value, because a stale or fallback source is the failure mode users
will not notice; decline-reason distribution, because a rising `no_grounded_source` rate means the
knowledge base is drifting from what people ask; approval-versus-rejection rate, because it is the
adoption signal; and solver status, because a silent slide into the heuristic path is a quality
regression.

**RG-20. What is missing from monitoring?**
📐 The Azure Monitor workbook is described but no workbook JSON is committed, and the Activator alert rules
are templates rather than provisioned monitors. Instrumentation is real; the operational dashboard layer
is not yet materialised.

---

## 3.7 TR-AI-01 — Use of AI technologies *(claimed 5/5)*

**RG-21. Where is AI actually doing work, as opposed to decorating the product?**
Four places. Grounded retrieval-augmented answering over approved procedures with enforced citation and
typed declines. Agentic orchestration across four domain specialists. Natural-language explanation of
recommendations. And speech-to-text plus structured drafting in the knowledge capture flow. The optimiser
and the RUL estimator are deliberately *not* LLM-based.

**RG-22. Why is your optimiser not AI? Is that not a weakness?**
It is the strongest architectural choice in the project. A schedule that a human must approve and an
auditor must reconstruct needs provable optimality and bit-identical reproducibility. A MILP gives both; a
learned policy gives neither. Using AI where it does not belong is a failure of judgement, not a display
of capability.

**RG-23. What is your AI governance posture?**
Grounded-only answering, unconditional AI disclosure banners, model version in every audit record,
human approval before any action, a tool deny-list, and a CI-enforced zero-tool invariant on the knowledge
agents. Mapped to EU AI Act Articles 12, 13, 14 and 50 even though the system is argued to be
high-risk-adjacent rather than high-risk.

---

## 3.8 TR-AI-02 — AI model selection and deployment *(claimed 4/5)*

**RG-24. Justify the model choices.**
`gpt-5.4-mini` as the default because most questions are explanatory and short; `gpt-5.5` for reasoning,
selected automatically when the question exceeds 120 characters or contains comparison, causal or
simulation markers. The escalation is measured on question shape rather than left to user choice, which
makes cost predictable and behaviour reproducible.

**RG-25. Why 4 and not 5?**
Two concrete absences. There is no MLflow registry artefact — the analytical models carry semantic
versions in code and in the audit record, but there is no registry with lineage and stage transitions.
And there are no live model evaluation metrics: no golden-set retrieval benchmark, no measured
hallucination rate. Both are Phase 1 items and neither should be papered over.

**RG-26. Is the deployment of these models secure?**
Regional Azure AI Foundry deployments inside the EU, reached with managed identity from the BFF, with no
key material in the application and no direct browser-to-model path. Prompts are versioned in source and
reviewed as code.

**RG-27. One Foundry project or two — and why did you change your mind?**
ADR-019 specified two projects to hard-separate knowledge agents from action agents. ADR-020 supersedes it
with a single project `novasteelv3` where the read/call boundary is enforced by a manifest plus a CI check.
It is a reduction in isolation traded for lower operational complexity and a boundary that is verified by a
test rather than assumed from configuration. I recorded it as a trade-off, not as an improvement.

---

## 3.9 TR-AGT-01 — Autonomy and orchestration *(claimed 5/5)*

**RG-28. Define what your agents are autonomous about.**
They are autonomous in *analysis*: selecting which tool to invoke, deciding whether grounding is
sufficient, choosing to decline, composing a multi-domain answer. They are autonomous in nothing that
touches the plant — every consequential action is a human approval by construction, per ADR-007.

**RG-29. Is a deterministic keyword router really orchestration?**
The router is one component; orchestration is the state graph that carries context between steps, invokes
tools, handles failure and assembles the response. The routing decision is deterministic on purpose,
because "why did it ask the maintenance agent?" must have the same answer every time. Non-determinism at
the routing layer buys elegance and costs explainability.

**RG-30. Where does autonomy stop, and is that a limitation?**
It stops at the single synchronous request. There is no persistent job queue, no long-running goal, no
agent that wakes up on a schedule and pursues an objective. That is a real limitation for the "autonomy"
half of the criterion and it is stated in the technical analysis. What earns the score is the orchestration
half, which is fully realised.

---

## 3.10 TR-AGT-02 — Multi-agent coordination *(claimed 5/5)*

**RG-31. Describe the agent topology.**
Seven agents. Two knowledge agents — a procedure agent and a web-search agent — with **zero** function
tools, an invariant enforced in CI. Four domain specialists — energy, carbon, quality and maintenance
advisors — with exactly one tool each. And one operations orchestrator holding all four tools, which
composes cross-domain answers.

**RG-32. Show me a real handoff.**
A cross-domain question — for example, whether deferring a reline changes the energy schedule — routes to
the orchestrator, which calls the maintenance tool for the RUL horizon and the energy tool for the schedule
impact, and composes a single answer with both provenances attached. The handoff carries state through the
graph, it does not re-prompt from scratch.

**RG-33. Is the handoff genuine or scripted?**
The coordination is genuine; the underlying tool responses in the demonstration come from deterministic
fixtures, and the agent roster is static rather than dynamically composed. Both are disclosed. Deterministic
fixtures are what make the demo reproducible, but they mean you are watching real coordination over
predictable data, not over live discovery.

**RG-34. Do you implement reflection?**
Not as a self-critique loop. The equivalent safety function is served by the grounding and citation
verification step, which can reject an already-generated answer with `citation_enforcement_failed`. That is
verification rather than reflection, and I would describe it as such rather than claim a pattern I did not
build.

---

## 3.11 TR-ARC-01 — Performance and reliability *(claimed 4/5)*

**RG-35. Why 4?**
Four honest absences: no load test, no formal SLA, no circuit breaker or retry policy around external
dependencies, and an untested disaster-recovery path. The SLOs are defined and instrumented, degradation is
graceful and visible, and the fallback ladder is real — but resilience engineering is where this project is
least mature and I would rather score it than defend it.

**RG-36. What reliability properties *are* demonstrated?**
Visible degradation rather than silent failure — `GET /v1/meta` reports whether you are on the lakehouse, a
fixture or a fallback. Deterministic behaviour under identical inputs. Zero-violation guarantees from the
optimiser with a labelled heuristic fallback. And the architectural property that an entire cloud outage
degrades insight without touching control.

**RG-37. What would you do first to move this to a 5?**
A load profile against the BFF and the model path to establish the real p95 under concurrency; resilience
policies with a circuit breaker on Foundry and Fabric calls; a durable idempotency store; and one
rehearsed DR failover to West Europe with a measured RTO. In that order.

---

## 3.12 TR-PRE-01 — Clarity of explanation and presentation *(claimed 5/5)*

**RG-38. How is the documentation organised?**
By audience: business and personas, architecture with the ADR set, technical analysis mapped criterion by
criterion to this rubric, security and compliance, operations, and presentation assets including the demo
runbook and two Q&A documents — a topic FAQ and this persona-based one.

**RG-39. Can you adapt to the audience level?**
That is what this document is for. The same fact has a plant-manager answer, a CISO answer and an examiner
answer, and they are written separately rather than left to improvisation under time pressure.

**RG-40. Any documentation defects you already know about?**
Three, and I would rather list them than have them found. The slide count is reported as 26 in one index
and 28 in the validation report. The test count appears as both 1,139 and 1,168 from different measurement
dates. The ADR count is stated as 16 in the development narrative while the architecture document carries
ADR-001 through ADR-020. Also, the executive summary exists only in French.

---

# Part 4 — Deployment & operations

Source: [`../architecture/deployment-topology.md`](../architecture/deployment-topology.md) and
[`../operations/operations-and-cost.md`](../operations/operations-and-cost.md).

**DP-01. Where is it deployed, and why there?**
Azure **Sweden Central** as the primary region, resource group `rg-novasteelv3-demo-sc`, with **West
Europe** as the recovery region. Sweden Central was chosen for EU residency, model availability for the
selected deployments, and a favourable carbon profile — which is defensible for a decarbonisation
platform.

**DP-02. Walk me through the environment topology.**
Six resource groups separating network, data, application, AI, observability and shared concerns, with
four Fabric workspaces per environment (`RTI-Ingress`, `DataCore`, `ML`, `Analytics`). Environments are
isolated by subscription and resource-group naming rather than by tagging alone, so a blast radius follows
a permission boundary.

**DP-03. How is infrastructure provisioned?**
Twenty Bicep modules composed into environment deployments, applied by GitHub Actions using OIDC workload
identity federation. There are no stored cloud credentials in the repository or in the pipeline — the
federation is the credential.

**DP-04. Do you run a what-if before applying?**
Bicep `what-if` is the intended preview gate on infrastructure changes, and the templates are idempotent so
re-applying a known-good version converges. 📐 Enforcing what-if as a required approval gate on every
environment is a pipeline hardening item, not a demonstrated control.

**DP-05. What are the seven workflows?**
Continuous integration for the Python and frontend stacks with the full test suite, a security scan,
infrastructure deployment, application deployment, the validation-gate suite, and the Fabric item
deployment — the last of which is a **placeholder**. Naming that one honestly is more useful than
counting seven.

**DP-06. How do you roll back?**
Redeploy the previous tagged revision through the same pipeline. 📐 There is no blue-green slot swap and
no automated rollback trigger on a failed health check. For an advisory system with no write path the
consequence of a bad deploy is downtime rather than data corruption, which is why this maturity gap was
acceptable for the demonstration and would not be for a pilot.

**DP-07. Explain the nightly capacity pause.**
A Logic App pauses the Fabric F2 capacity at 01:00 Europe/Luxembourg daily in **non-production only**, and
resumes on demand with a sub-10-minute SLO. It is the single largest cost control — it is why the
demonstration runs under €100 a month.

**DP-08. What about daylight saving? A fixed UTC schedule would drift.**
The schedule is expressed in the Europe/Luxembourg zone rather than in UTC precisely so the pause tracks
local time across DST transitions. The failure mode if it did drift is benign — a pause an hour early or
late on a non-production capacity — but the correct answer is that the schedule is zone-aware.

**DP-09. What does a user see when the capacity is paused?**
A visible degraded state. `GET /v1/meta` reports `dataSource` as `fabric-fallback:*` instead of
`fabric-lakehouse:*`, and the UI reflects that. The design principle is that a paused dependency must
never look like fresh data.

**DP-10. Would you ever auto-pause production?**
No. The pause exists to make a demonstration affordable. A production capacity backing operational
decisions is never auto-paused, and that is stated as a rule rather than left implicit.

**DP-11. How do you handle secrets and configuration across environments?**
Key Vault for the residue that cannot be a managed identity, environment configuration in the deployment
pipeline rather than in the image, and no secret material in source. The identity-based Fabric endpoint
(ADR-005) removed the largest category of secret — SAS tokens — by design.

**DP-12. What is the deployment path for the front end?**
The Blazor shell and the React micro-frontend build in CI and deploy as static assets behind the
application tier, with the micro-frontend versioned independently so a visualisation change does not
require a shell redeploy. That independence is the practical payoff of the micro-frontend split.

**DP-13. How would you deploy to a second site or a second country?**
Re-run the same Bicep with a different environment parameter set; the application is site-parameterised
rather than site-specific. 📐 The unproven parts are Fabric capacity sizing under combined load and the
per-site ingestion connectivity through each plant's DMZ — both are Phase 2 concerns.

**DP-14. What is your patching and dependency update story?**
Dependencies restore exclusively through the organisation's protected feed proxy, which is also where
update scanning happens; the CI security workflow flags vulnerable packages. 📐 There is no automated
dependency-update bot configured, so cadence is manual.

**DP-15. What are the remaining gates before this could go to production?**
The compliance roadmap enumerates them: G0.1 through G0.7 to leave demonstration status, then G1→2 and
G2→3 between phases. In engineering terms the short list is: load test, DR rehearsal, real integrations,
Fabric item deployment, Conditional Access in IaC, external security testing, and DPIA sign-off.

**DP-16. How long would a Phase 1 pilot take to stand up?**
📐 The infrastructure is hours, because it is Bicep. The pilot is months, because it is gated on works-council
consultation, DPIA, the OT connectivity through a real DMZ, and accumulating enough shadow-mode
observations to evaluate the models. The technology is not the critical path and it would be misleading to
imply otherwise.

---

# Part 5 — Evolution & roadmap

Source: [`../business/compliance/compliance-roadmap.md`](../business/compliance/compliance-roadmap.md).

**EV-01. What are the phases?**
Demonstration today. **Phase 1** (0–6 months): one site, read-only shadow pilot — the platform recommends,
humans decide, and we measure agreement. **Phase 2** (6–18 months): scale to more sites and introduce
*guarded* write-back. **Phase 3** (18+ months): steady state. The gates between phases are stop conditions,
not milestones.

**EV-02. What has to be true to leave shadow mode?**
Measured agreement between recommendations and operator decisions, an energy delta attributable to accepted
recommendations, an acceptable false-alarm rate on lining warnings, a completed DPIA, external security
testing, and validated model performance on real rather than synthetic data. If the models disagree with
experienced operators too often, the correct outcome is that Phase 2 does not start.

**EV-03. Write-back is the scary part. How would you make it safe?**
Not by trusting the model. By scoping the first write to the lowest-consequence target — a CMMS work-order
draft rather than a setpoint — keeping the human approval mandatory, adding a reversibility requirement, and
extending the Sev-1 detection rule so any write without a matching approval is an incident. And the OT
boundary does not change: write-back goes to enterprise systems, not to the control network.

**EV-04. Would you ever let the platform control the furnace?**
That is a different system with a different safety case, a different standard and a different assurance
level. ADR-007 and ADR-016 are the two decisions that keep this platform out of that category, and I would
argue against dissolving them rather than for it.

**EV-05. Why defer Azure IoT Operations, and would you revisit it?**
ADR-016 rejected IoT Hub and the device-management model because it creates an inbound control plane the
platform explicitly does not want. I would revisit it only if the plant separately adopts an edge management
strategy owned by OT — at which point the platform consumes it rather than provides it.

**EV-06. What is next for the AI layer?**
A golden-set retrieval benchmark across the five languages, a model registry with lineage and stage
transitions, an evaluation harness producing tracked metrics rather than one-off checks, and replacing the
OLS wear estimator with a learned model through the existing `MLUpliftHook` once real campaign histories
exist.

**EV-07. Would you change the optimiser?**
Only when the model outgrows CBC. The natural progression is CBC to HiGHS for open-source performance, and
to a commercial solver if the multi-site, multi-day formulation makes solve time the binding constraint. The
solver sits behind an abstraction so that is a configuration change, not a rewrite. Determinism must survive
the change — that would be the acceptance criterion.

**EV-08. What about Fabric Data Agent — why not use it?**
It is a natural fit for exploratory questions over the lakehouse and it is on the roadmap. It was not used
in the demonstration because ADR-006 puts authority in the Python service: a hosted agent querying data
directly would sit outside the tool-policy and audit path that makes recommendations reconstructable.
Adopting it means first extending the audit contract to cover it.

**EV-09. How would this become multi-tenant?**
It would not, in the SaaS sense — it is a single-enterprise platform with site scoping. Serving multiple
steel producers would require tenant isolation at the Fabric workspace and identity level and a redesign of
the knowledge base boundary, since procedures are the most competitively sensitive asset in the system.

**EV-10. What is the most valuable thing you could add in the next thirty days?**
The Phase 1 measurement harness — the thing that records every recommendation, every human decision and the
delta between them. Everything else on the roadmap is an improvement; that one is what tells you whether the
platform deserves the improvements.

**EV-11. Is there a version of this project where you would recommend not proceeding?**
Yes. If shadow mode shows operators disagreeing with recommendations at a high rate and the disagreements
are correct, the honest recommendation is to stop at the analytics layer and abandon the advisory layer. The
gates exist so that outcome is available rather than embarrassing.

---

# Part 6 — Curveballs, traps and meta questions

**CB-01. Ninety-nine commits in four days, seventy-two percent AI co-authored. Did you actually build this?**
Yes, and the provenance is the point rather than the embarrassment. The commit history, the ADR trail and
the test suite are the evidence of authorship, and the AI co-authorship is disclosed in the commit trailers
rather than laundered. The architectural decisions — refusing the inbound control plane, putting authority
in the Python service, choosing a MILP over a learned policy — are judgement calls that no model made for
me, and they are the ones I am defending today.

**CB-02. What is the weakest part of this solution?**
Resilience engineering. No load test, no circuit breakers, an in-memory idempotency store and an untested DR
path. The second weakest is that the enterprise integrations are contracts rather than connections. If you
only remember one criticism from me, make it the first one.

**CB-03. What would you do differently if you started over?**
Write the load test in the first week rather than the last, use a durable store for idempotency from the
start, and deploy the Fabric items early so the demo path and the documented path never diverged. All three
failures share one cause: I deferred operational scaffolding in favour of feature surface.

**CB-04. Your documents contradict each other in three places. Explain.**
They do, and they are: 26 versus 28 slides, 1,139 versus 1,168 tests, 16 versus 20 ADRs. The causes are a
deck revision, a measurement-date difference, and a development narrative written before ADR-017 to ADR-020
were added. The authoritative sources are the deck itself, the test runner at the current commit, and the
solution architecture document. I would rather show you the reconciliation than have you find the
discrepancy.

**CB-05. You claim 56 out of 60. Is that not self-serving?**
It is a self-assessment and should be read as one. What makes it usable is that it names a specific gap for
every criterion, including the eight where I claimed full marks. A self-assessment that finds nothing wrong
is worthless; this one costs itself four points and lists roughly a dozen more gaps that it argues do not
cost points. You are free to disagree with that argument — the evidence is all in one table.

**CB-06. Convince me this is not a dashboard with a chatbot bolted on.**
A dashboard shows state. This produces a *ranked, constrained, explainable action* — a 96-slot schedule
with zero constraint violations, a failure horizon with a confidence interval, a parameter change with a
scored outcome — and routes it through a mandatory human approval that is hash-chained for reconstruction.
Remove the optimiser, the estimator and the audit chain and you would have a dashboard with a chatbot. They
are the product.

**CB-07. Everything is synthetic. Does anything you showed transfer to reality?**
The mechanisms transfer; the magnitudes do not. The MILP formulation, the wear-physics estimator, the
grounding guards, the audit invariants and the approval flow are all indifferent to whether the numbers are
real. The 7.25% is a property of one synthetic scenario and I would not defend it as a forecast — which is
precisely why the roadmap starts with a shadow pilot that measures the real number.

**CB-08. What is the one claim in this project you are least comfortable with?**
The −22% CO₂ objective. Load-shifting alone contributes single digits — the demo shows 3.29% — and the rest
depends on grid mix, scrap ratio and process investment outside this platform. I keep the objective because
it is the plant's decarbonisation target, but I state every time that the platform's attributable share is
the small, visible part.

**CB-09. If I gave you €1M and a year, what would you build?**
Not more features. A real pilot: one site, real telemetry through a real DMZ, the measurement harness, a
validated wear model on actual campaign histories, and external security testing. The output would be a
number — the real energy delta — which is the only thing that turns this architecture into a business case.

**CB-10. Why should we believe your compliance analysis rather than treat it as decoration?**
Because it costs us things. It says CBAM is not implemented, that ETS retention is four years short of MRR
Article 66, that IEC 62443 conformance is design-only with no certification, and that the AI Act
classification needs legal confirmation. A decorative compliance section claims coverage; this one
enumerates gaps with gate identifiers.

**CB-11. Is "high-risk-adjacent" a real category, or did you invent it?**
It is not a legal category and I do not present it as one. It is a design posture: we argue the system falls
outside Annex III and outside Article 6(1), and we build to Chapter III anyway so a reclassification costs
documentation rather than architecture. The invented word is doing honest work — it flags a judgement that
needs counsel, rather than hiding it inside a claim of compliance.

**CB-12. Your KPI dashboard shows a metric in the red. Is that a bug?**
No, it is deliberate. KPI-QUA-01 reads 0.9494 against a 0.972 objective and is displayed as not met. A
demonstration in which every indicator is green is a demonstration of the demo, not of the platform.

**CB-13. What did the AI get wrong during development that you had to correct?**
The most instructive case was the retrieval layer: reciprocal rank fusion always returns a top result, so
the assistant would answer everything. The fix — a content-term overlap guard before a passage qualifies as
grounding — came from testing the decline path rather than the happy path, and it is now the single most
important safety control in the knowledge flow.

**CB-14. Thirty seconds, no jargon. Why does this matter?**
A steel plant burns energy worth a third of its conversion cost and can lose €8M when a furnace lining
fails without warning. This platform reads the plant's own data, proposes what to do in the next few hours,
explains why, and records who decided. It never touches the furnace. That last sentence is what makes the
rest of it deployable.

---

## Appendix A — Trap questions and how to defuse them

| Trap | Why it is a trap | Defusing move |
| --- | --- | --- |
| "So you achieved a 22% CO₂ reduction?" | Restates a 🎯 target as a 🔬 result | Correct immediately: "That is the objective. The measured contribution from load-shifting is 3.29%." |
| "Your optimiser saved 21.74%." | Quotes the raw transparency field | "That is against movable load only. Plant-wide it is 7.25%, which is the honest denominator." |
| "This is IEC 62443 compliant." | Conformance ≠ certification | "Design conformance, documented. No certification is claimed." |
| "You could push this setpoint automatically." | Invites dissolving the safety boundary | "That is a different system with a different safety case. ADR-007 is deliberate." |
| "Can I use this for my ETS return?" | Management information ≠ regulated MRV | "No. No approved monitoring plan, demo constants, and retention is six years against ten required." |
| "Your agents are autonomous." | Overclaims the agentic criterion | "Autonomous in analysis, never in action, and single-request rather than long-running." |
| "How accurate is the assistant?" | Invites an invented number | "I have no measured rate and will not invent one. Here is the architecture that bounds the consequence." |
| "It's all AI-generated anyway." | Attacks provenance | "Disclosed in the commit trailers. The architectural judgements are mine and they are what I am defending." |

## Appendix B — Sentences to never say

- "It's fully compliant." → say which articles, which gates, which gaps.
- "It scales." → say where it scales and where it does not.
- "The model is very accurate." → give a number with a label, or decline to give one.
- "We could easily add that." → say which seam, which phase, which gate.
- "That never happens." → say what the system does when it does happen.

## Appendix C — Persona to source-document map

| Persona | Primary sources |
| --- | --- |
| Plant Manager, Operator, Energy, Maintenance, Quality, Sustainability, Knowledge, Executive | [`../business/personas-and-journeys.md`](../business/personas-and-journeys.md) |
| OT Systems Engineer | [`../business/compliance/iec-62443.md`](../business/compliance/iec-62443.md), ADR-016 |
| Platform Ops / SRE | [`../operations/operations-and-cost.md`](../operations/operations-and-cost.md), [`../architecture/deployment-topology.md`](../architecture/deployment-topology.md) |
| CISO | [`../tech/security-governance-and-threat-model.md`](../tech/security-governance-and-threat-model.md) |
| Solution Architect | [`../architecture/solution-architecture.md`](../architecture/solution-architecture.md) (ADR-001 … ADR-020) |
| Data Architect / Data Engineer | [`../architecture/solution-architecture.md`](../architecture/solution-architecture.md), ADR-001/002/017/018 |
| AI / ML Engineer | [`../architecture/solution-architecture.md`](../architecture/solution-architecture.md), ADR-006/011/012/019/020 |
| DPO / Legal | [`../business/compliance/eu-ai-act.md`](../business/compliance/eu-ai-act.md), [`../business/compliance/other-regulations.md`](../business/compliance/other-regulations.md) |
| Compliance / Auditor | [`../business/compliance/compliance-roadmap.md`](../business/compliance/compliance-roadmap.md), [`../business/compliance/eu-ets.md`](../business/compliance/eu-ets.md) |
| CFO / FinOps | [`../operations/operations-and-cost.md`](../operations/operations-and-cost.md) |
| Examiner (rating grid) | [`../usecase/rating_grid.md`](../usecase/rating_grid.md), [`../tech/technical-analysis.md`](../tech/technical-analysis.md) |
