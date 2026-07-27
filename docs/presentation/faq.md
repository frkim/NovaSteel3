# NovaSteel — Oral Defense FAQ

> **Status:** Authoritative defense FAQ v1.0
> **Date:** 2026-07-25
> **Owning workstream:** `delivery-pack`
> **Companion:** [oral-defense-and-slide-plan.md](oral-defense-and-slide-plan.md) · [solution-architecture.md](../architecture/solution-architecture.md) · [deployment-topology.md](../architecture/deployment-topology.md) · [security-governance-and-threat-model.md](../security/security-governance-and-threat-model.md)

## How to use this FAQ

These are the hardest questions the panel is likely to ask, with concise, defensible answers. Two disciplines apply to **every** answer, exactly as on the slides:

- 🔬 **EVIDENCE** = a reproducible synthetic-scenario result shown or reproducible in the demo.
- 🎯 **TARGET** = a projected business outcome (use case / requirements), **not** proven by the demo.

If you don't know, say *"that's a validation gate, not a claim,"* and log a written follow-up rather than inventing a number. Answers are time-boxed to ~60–90 seconds.

---

## A. Business value & ROI

**Q1. Are the 14% energy, 22% CO₂, 21-day warning, and 8% yield numbers proven?**
No — they are 🎯 **TARGETS**, each tied to a stated baseline so they're falsifiable: energy ~19.5→16.8 GJ/t, CO₂ ~2.10→1.64 t/t, ≥21 days lead time, high-grade yield ~90%→97%. Today's demo shows the platform *producing* those kinds of outputs on synthetic data (🔬 evidence the mechanics work), not that we've banked the savings. Realized savings get proven in a one-site pilot via an auditable savings ledger.

**Q2. What's the ROI / payback?**
Energy dispatch is the fastest payback because it acts daily against spot-price volatility, and one avoided lining failure is ~€8M. But I won't quote a single payback figure today: a credible number needs measured pilot CU consumption and realized-savings data. I can give you the cost *drivers* and controls now; the euro figure is a pilot output, not a slide claim.

**Q3. Why should the CFO fund Phase 1 rather than wait?**
Because the exposure compounds on every axis while you wait — energy at peak, carbon at ETS penalty, failures at €8M, and knowledge lost irreversibly when experts retire. Phase 1 is a bounded, read-only, single-site shadow pilot that measures real savings against the targets before any production write-back. It's the cheapest way to convert targets into defensible numbers.

**Q4. How do you attribute savings so the board trusts them?**
Every energy recommendation records expected € saved and CO₂ avoided; acceptance/rejection is logged with a reason code; and realized outcomes flow into an append-only savings ledger reconciled against the recommendation. That's how −14% becomes *proven* rather than asserted — decision, counterfactual, and outcome are correlated, not eyeballed.

**Q5. What's the single most valuable capability if we could only fund one?**
Furnace-lining RUL: it converts an ~€8M unplanned catastrophic failure into a planned intervention with ≥21 days of lead time (🎯 target). Energy dispatch has the fastest cash payback, but lining prediction removes the largest tail risk.

---

## B. Microsoft Fabric centrality

**Q6. Why is Microsoft Fabric the center of the architecture, not a bolt-on?**
Heavy-industry analytics has two clocks — a sub-second operational clock and a governed-history clock — and Fabric serves both in one governed estate: Real-Time Intelligence (Eventstream + Eventhouse/KQL) for hot telemetry, OneLake/Lakehouse bronze-silver-gold for governed history and ML, one Direct Lake semantic model so a KPI means exactly one thing, and native Power BI. That's ADR-001. Azure services exist only for integration, APIs, and domain compute Fabric doesn't provide.

**Q7. Why separate Eventhouse/KQL from the Lakehouse Delta tables?**
Different jobs, different stores (ADR-002). KQL/Eventhouse is the hot investigation layer — high-cardinality telemetry, alarms, RTI dashboards, Activator input. Lakehouse Delta is the governed historical, training, and KPI substrate. Mixing them would either make audit history volatile or make hot queries slow. We always answer a question from the right store based on its freshness need.

**Q8. Isn't Direct Lake immature / risky?**
Direct Lake reads gold Delta tables without importing or duplicating them, giving one semantic truth with no copy. We scope it deliberately: it serves the semantic model over **gold** tables only; live 1–10 second telemetry stays in KQL/RTI, not the semantic model. So we don't ask Direct Lake to do real-time streaming, which is not its job.

**Q9. Fabric is SaaS — how do you secure it without a customer VNet?**
We don't pretend Fabric is a VNet subnet. We use Fabric managed private endpoints only where the service documents them, isolate the ingress publisher in its own workspace, and treat any remaining Fabric SaaS route as an approved outbound-TLS/Entra exception with explicit firewall/DNS policy and monitoring — never with OT reachability. Deployment-topology §3.1 states this explicitly.

**Q10. What if a Fabric feature you depend on changes or is in preview?**
Nothing on the demo critical path is a preview feature (ADR-009). Version and feature choices are resolved at build time from supported channels, and §15 of the architecture lists explicit production-validation gates — Custom Endpoint identity, query-adapter identity, SKU/quota — that we re-check in the target tenant before go-live rather than assuming.

---

## C. Architecture alternatives

**Q11. Why not Databricks, Snowflake, or a custom data lake?**
Those can store and process data, but none give us a *single governed estate* spanning sub-second RTI, OneLake lineage, one Direct Lake semantic layer, and native Power BI without stitching multiple products and copying data across trust boundaries. Fewer copies and one lineage graph directly serve our audit and EU AI Act obligations. A parallel lake is explicitly rejected in ADR-001.

**Q12. Why Python for the models instead of doing it all in Fabric/Foundry?**
Because the math must be deterministic, testable, and explainable. Python services compute RUL, quality risk, and feasible dispatch (ADR-006); Fabric Data Science trains and evaluates them with MLflow lineage. Foundry's generative agent explains and orchestrates — it never computes the authoritative answer. This keeps a confidently-wrong LLM away from any physical or financial commitment.

**Q13. Why the Blazor + React hybrid front end instead of one framework?**
The requirement asked for a C# presentation layer; the analytics needs MUI/D3 density. So a Blazor WebAssembly C# shell owns sign-in, routing, theme/locale, and host lifecycle, and a React/TypeScript microfrontend owns the data-dense dashboards (ADR-004). All business/data APIs remain Python/FastAPI. The interop contract is typed and versioned; the shell never hands a workload credential to React. A pure-React swap needs a documented waiver; a second C# BFF is rejected.

**Q14. Why Event Hubs + a relay instead of Fabric's native Event Hubs source?**
Fabric's documented basic Event Hubs connector uses a Shared Access Key, and our security policy forbids standing secrets. So the canonical route is Event Hubs as a buffer plus a managed-identity relay to an Eventstream Custom Endpoint over Entra ID (ADR-005). We accept the Custom Endpoint's Contributor-role requirement but isolate that publisher in an ingress-only workspace. Native SAS is rejected unless the CISO grants a documented exception.

**Q15. Why not let the AI act autonomously to capture more value faster?**
Because a wrong autonomous action here can damage a furnace or breach a delivery/ETS commitment. ADR-007 requires an explicit human approval event for every safety-adjacent or financial decision, and Phase 0 has no real write connector at all. Any proposal for automatic schedule/CMMS/OT action triggers security, legal, OT, and RAI-board review plus a threat-model update.

---

## D. Capacity, cost, pause & start

**Q16. What does this cost to run?**
The demo baseline is Fabric **F2**, the smallest SKU, with a bounded stream and scheduled notebooks. We move to **F4** only on measured contention, and we deliberately do **not** buy F64 just to give viewers free Power BI licensing — consumers sit on Pro/PPU/trial. The Platform Ops capacity dialog can resize the non-production capacity between **F2, F4 and F8** so a rehearsal can burst without a redeployment; that allow-list is enforced by an Azure Policy deny rule, not by the UI, and resizing deliberately does not start or stop the capacity. F2 remains the committed default that the nightly pause returns us to. I won't quote a €/hour figure: it's region-, currency-, and offer-specific, and the honest production number comes from measured pilot CU consumption, not a slide.

**Q17. How do you control cost when the demo capacity sits idle?**
A daily **01:00 Europe/Luxembourg** Logic App runs a lifecycle *check* whose default action is an orderly pause of non-production capacity, using the official ARM `suspend` operation (`api-version=2023-11-01`, treated as a 202 async operation). It only pauses if the simulator is stopped, buffers are drained, and no rehearsal is active — it will log `SKIPPED_BUSY` and leave capacity running rather than kill a rehearsal for a cost timer. Production is hard-denied by tag and resource-ID allow-list.

**Q18. Can the demo pause/resume Fabric capacity from the UI? Isn't that dangerous?**
The Demo Mode capacity toggle is **always simulated**. A real resume/pause is only available *outside* Demo Mode to a `Platform.Capacity.Manage` user, executed by the BFF via `mi-ns-capacity-demo` — a capacity-scoped identity with `read/write/suspend/resume` and **no data-plane, Fabric-workspace, or production access**. The browser never calls ARM directly, and it never touches production capacity.

**Q19. A paused capacity makes content unavailable — how do you avoid an embarrassing outage?**
Precisely because a paused F capacity makes its content unavailable, we never pause while a live demo, RTI ingest, reporting consumer, scheduled pipeline, or production monitor needs it. Resume is followed by a readiness checklist (Eventstream/KQL query, Lakehouse/semantic reachable, APIs healthy) before we mark it Running, and 202 is never treated as "started." The simulator is started intentionally afterward — resume never launches a scenario by itself.

**Q20. Does pausing lose data or reset consumption?**
No. Pausing stops availability and billing-for-compute, but OneLake data remains stored and prior consumption is not erased (paused mirroring storage still incurs charges). We "roll back" by redeploying a validated version, never by deleting source data, Eventstream history, or audit facts.

---

## E. Regions & data residency

**Q21. Where is data processed, and is it EU-only?**
The target design is EU-only. Fabric, Event Hubs, application services, the Foundry project, and Speech are planned for **Sweden Central**. Foundry model inference uses a **Data Zone (EU)** deployment, which keeps processing within the EU data zone and storage at rest in region. Tenant-specific provisioning, quota, and data-residency evidence are production gates rather than completed deployment claims.

**Q22. Data Zone (EU) can route within the EU — what if policy requires single-region?**
Then we switch that model to a **regional** Standard/Provisioned deployment so processing and storage stay in Sweden Central, accepting a narrower model catalog. This is ADR-003 and an explicit §15 validation gate: we confirm the required model, deployment type, and quota in-region immediately before deployment. We do not silently assume single-region.

**Q23. What about disaster recovery / the Sweden Central BCDR caveat?**
We're transparent: Power BI business-continuity/DR is not available by default in Sweden Central because its paired region doesn't support it, so we make **no automatic cross-region Fabric failover claim**. West Europe is an EU recovery target to *validate*, not an automatic replica. A production recovery copy requires a data inventory, DPO approval, encryption/retention controls, and a tested restore runbook before any RTO/RPO is promised.

**Q24. Why not North Europe or West Europe as the primary?**
North Europe is not in the current Foundry Agent Service / Responses API region list, so it is not an agent anchor. West Europe is a tested EU contingency, not an implicit replica. Sweden Central is the primary design target because it supports the required agent and interview path at research time; exact model, tool, quota, and Speech-feature availability are revalidated in the tenant before deployment. Specialized speech training or recovery needs require a separately approved design.

---

## F. AI governance & Responsible AI

**Q25. How is this classified under the EU AI Act?**
Formal classification is a Legal/Compliance gate before non-synthetic processing. Until then, the lining and energy capabilities follow a conservative **high-risk-adjacent** posture, while the knowledge-capture system has at least transparency obligations. If a capability is classified high-risk, the full control set applies: risk management, technical documentation and logging, human oversight, accuracy/robustness/cybersecurity, and conformity assessment (security §16.2).

**Q26. What stops a hallucinating LLM from causing harm?**
Architecture, not hope. Python computes every authoritative answer; the LLM only explains, retrieves, and calls allow-listed tools (ADR-006). It cannot be the sole calculation, relax a hard constraint, or make a commitment. Its tools are read/simulate by default; the "commit" endpoint is separately policy-gated and disabled outside approved production. A model response is never authorization.

**Q27. How do you defend against prompt injection through retrieved documents or market data?**
We treat all retrieved content and payloads as **untrusted**: Prompt Shields for direct and indirect injection on every deployment, instructions separated from data (spotlighting), safety meta-prompts that refuse embedded instructions, narrow tool allow-lists, full tool-call input/output logging, and human-in-the-loop approval for any write. Neither an interview transcript nor a market payload is ever trusted as agent instruction (architecture §8.2, security §12).

**Q28. Who signs off before an AI capability goes to production?**
A cross-functional **Responsible AI review board** — Data Scientist, Compliance/DPO, OT/ICS Engineer, and Maintenance Engineer — is a mandatory sign-off gate (security §15). Nothing reaches production on an engineer's say-so.

**Q29. How is every AI decision made auditable?**
Every consequential output records inputs/feature snapshot, model/config version, output, confidence, rationale, the human decision, and the outcome, correlated by a `correlation_id`. The authoritative audit table is append-only through the BFF, with a scheduled evidence export to immutable storage as the tamper-evidence boundary. Model prediction-vs-outcome and drift are monitored continuously.

**Q30. How do you know the model is right — what about drift and accuracy?**
We track prediction-vs-actual and drift metrics as first-class telemetry, and the physics-informed design constrains the model to physically valid outputs. On synthetic scenarios we score against a truth ledger. But fleet-wide accuracy is a 🎯 target to validate in the pilot against real relines and lab results — the demo proves the *mechanism and uncertainty reporting*, not field accuracy.

---

## G. Security & identity

**Q31. Where are the secrets / connection strings?**
There are no standing application secrets. Humans use Entra user tokens; supported workloads use separate managed identities; GitHub deployment uses OIDC/workload-identity federation, not client secrets. Public package registries are explicitly prohibited in favor of Microsoft-protected feeds, and every build emits an SBOM. Breach notification is within 72 hours; audit logs are retained 1 year hot + 6 years archive.

**Q32. If one identity is compromised, what's the blast radius?**
Contained by design. Azure RBAC, Fabric workspace/OneLake roles, Foundry RBAC, and application app-roles are **four separate planes** — holding one grants nothing in another. A per-plant gateway identity can only produce to its own Event Hub; the ingress relay is Contributor only in the isolated ingress workspace; the BFF identity can't touch capacity lifecycle; the capacity identity has no data plane. The browser never receives a workload token.

**Q33. Isn't the Eventstream Custom Endpoint Contributor role a security hole?**
It's wider than we'd like, and we say so. It's the documented Custom-Endpoint managed-identity requirement, so we isolate that publisher in an ingress-only workspace (`NS-<env>-RTI-Ingress`) with no access to curated, ML, BI, or knowledge workspaces — a narrow blast radius (ADR-005). We re-evaluate when Fabric ships a finer publisher role, and it's an explicit production-validation gate.

**Q34. How is operator voice data protected?**
Interview audio/transcripts are **Highly Confidential**: explicit informed consent before recording, DLP, a restricted EU store, raw audio retained 30 days by default, transcripts kept only after de-identification, and full consent-withdrawal/deletion propagation. Personal-data processing carries a DPIA and lawful basis; it's a legal gate before any non-synthetic interview.

**Q35. Can the platform reach into the plant and change something?**
No — this is the strongest guardrail. No application, agent, Activator rule, pipeline, or demo control writes to a PLC, safety interlock, furnace, or setpoint. The OT/IT boundary is never flatly bridged; the per-plant DMZ gateway is outbound-only and no cloud session initiates into the OT network. Existing OT safety systems remain authoritative (architecture §1.1, security §11).

**Q36. What does the STRIDE threat model actually mitigate?**
Spoofing → per-plant managed identity + mTLS + Conditional Access MFA; Tampering → protocol break at the DMZ, model-registry versioning + RAI sign-off, Purview lineage; Repudiation → full tool-call logging + immutable Sentinel audit; Information disclosure → OneLake roles + sensitivity labels + DLP + CMK; DoS → firewall, private endpoints, AI quotas, DDoS Protection; Elevation → least-privilege app roles, tool allow-listing, PIM JIT (security §17.2).

---

## H. OT realism & domain credibility

**Q37. This is synthetic data — how do I know it reflects a real steel plant?**
Because it's physics-*first*, not curve-fitting. We simulate true process state — mass/energy balance, operating modes, shift schedules, material genealogy — and then modeled sensors observe that state, adding calibration bias, quantization, noise, lag, and missingness. Signals therefore can't contradict each other, and physical invariants are enforced. That mirrors the causal structure of a real plant; what it can't claim is real-plant *accuracy*, which is a pilot validation.

**Q38. What OT signals and structures are actually modeled?**
Furnace thermal (hearth shell temperature, cooling-water in/out and flow, local heat flux, refractory estimate, hot-blast temperature, top pressure, PCI, hot-metal temperature, production rate); full rolling/quality genealogy (raw lots → heat → ladle → slab/billet → reheat → coil/bar → sample → test → shipment); and energy (electricity, gas, oxygen, steam, grid carbon intensity, ETS and spot price, process emissions). Integration standards include OPC-UA and ERP/MES/CMMS APIs.

**Q39. How would this connect to real OT without compromising plant safety?**
Via a per-plant gateway at Purdue Level 3.5 in an industrial DMZ that terminates OPC-UA/MQTT/historian-export and emits only allow-listed, schema-validated telemetry outbound over TLS to an Event Hubs buffer, with disk-backed store-and-forward preserving event time. No cloud-originated session ever reaches the OT network. The OT/ICS owner signs off the DMZ design before any real site onboards.

---

## I. Synthetic data & reproducibility

**Q40. How reproducible are the demo results?**
Bit-for-bit. Everything derives from root seed **240725**; child seeds are `SHA-256(root | scenario | plant | asset | signal)`; the generator is versioned (`novasteel-sim/1.0.0`); and each run records seed, scenario, generator version, configuration checksum, simulated clock, row counts, and a truth-ledger checksum. The same manifest yields identical output within floating-point tolerance, so any number I show regenerates.

**Q41. What scenarios exist, and can you show a "bad" case, not just a happy path?**
Yes. Named scenarios: healthy baseline (`240725`), 21-day lining warning (`240726`), evening energy spike (`240727`), quality drift (`240728`), and edge outage/recovery (`240729`). The outage scenario deliberately exercises buffering, duplicate replay, and late events; quarantine on invalid/late/duplicate data is visible, never silently repaired.

**Q42. How do you prevent synthetic and production data from mixing?**
Physical and logical isolation. The demo uses only `NS-DEMO-*` namespaces on separate capacity; no Fabric workspace, OneLake shortcut, Eventstream connection, Key Vault secret, or managed identity may bridge demo and prod. Every record carries `data_classification: SYNTHETIC` / `privacy_label: DEMO-NONPERSONAL`, enforced in schema validation and shown as a persistent UI banner (ADR-008).

**Q43. Are the demo's live numbers trustworthy or cherry-picked?**
They're deterministic outputs of a signed scenario, validated by contract, physics, and scenario assertions before the run is presentable, with an expected cue sheet (e.g., RUL P50 19.65 / P10 18.69 / P90 20.61 / risk 0.90 / confidence 0.78; energy cost −7.25% / CO₂ −3.29% / peak −7.89%). If a live value lands outside its expected band, we switch to the cached deterministic result rather than change the narrative or hide the discrepancy.

---

## J. Models & ML approach

**Q44. What is a "physics-informed" model and why not pure ML?**
It's an ML model constrained by furnace physics — heat-flux and cooling relationships, monotonic lining wear (thickness can't increase except after a reline), non-negative RUL, and energy/mass balance. Pure black-box ML can fit noise and produce physically impossible outputs; physics constraints make it explainable and safer for a safety-adjacent decision, and give the drivers we show (heat-flux slope, spatial temperature contrast, cooling residual).

**Q45. Which foundation model does the GenAI use, and what if it's deprecated?**
We deliberately don't hard-code an unverified model family or future version (ADR-009). A currently-supported general-purpose model is selected at deployment time, only after a release gate verifies the required model, tools, quota, and Data Zone (EU) availability in Sweden Central. Model choice is a build/release decision captured in provenance, not an architectural assumption.

**Q46. How often do the models score? Is it real-time?**
Pilot lining RUL scoring is **daily**, and I state that plainly — near-real-time is a measured later enhancement, not an MVP claim. Quality is batch/nearline over genealogy features; energy dispatch runs against the day-ahead cycle before market gate closure. "Real-time" in this platform means promptly visible operational data, not a deterministic safety-latency SLA.

**Q47. How are models trained and promoted — can they self-update?**
No autonomous promotion. Training/evaluation runs in Fabric Data Science with MLflow lineage; promotion requires review and RAI-board sign-off. Workers do approved scoring only and cannot retrain or promote. A dependency or model upgrade requires lockfile-diff review, SBOM, vulnerability scan, and contract/integration tests.

---

## K. Deployment & operations

**Q48. What's the deployment sequence and how do you know each step is safe?**
Contract → simulator/validators → Fabric items → Python services → shell/MFE → integration, with evidence gates at each step: `what-if` review, identity path proven with no SAS, bronze/silver/gold reconciliation, Entra-only auth with no OT path, persona/RLS/accessibility checks, and two consecutive clean 15-minute demo runs with every fallback exercised. Production onboarding needs DPO/legal, OT, security/RAI, capacity/DR, and source/market-license gates signed.

**Q49. What are the environments and are they really separated?**
`dev`, `test`, `demo`, `prod` are separate resource groups, identities, Fabric workspaces, data paths, and capacity assignments. Demo is `NS-DEMO-*`, 100% synthetic, F2 initial. Production capacity is never automatically paused. Nothing bridges demo and prod — no shortcut, secret, connection, or identity.

**Q50. What happens operationally if Fabric, Foundry, Speech, market data, or the network fails?**
Each has a degraded mode: OT buffers locally and in Event Hubs with visible freshness/gap; the Fabric hot path replays from buffer/bronze; human procedure review is independent of Foundry/Speech availability; price provider falls back to the last licensed snapshot with an expiry (no new recommendation past freshness threshold). For the demo, the binding ladder is live cloud → local deterministic replay → cached interactive → recorded flow → static proof pack, rehearsed offline.

---

## L. Scalability

**Q51. Does this scale from the demo to four countries without a rewrite?**
Yes — scaling is a capacity and per-plant-relay decision, not a redesign. The event envelope and `/v1` API contracts are stable and versioned; each plant gets its own gateway, Event Hub authorization, and relay, and production capacity is sized from measured concurrent ingestion/query/Power BI/Spark load. The requirements mandate supporting 4 sites today with a path to more without rework.

**Q52. Can it handle the data volumes?**
The synthetic profile already models realistic rates — furnace telemetry at 1–10 s (~5.2M events/day), rolling telemetry at 100 ms–10 s, energy intervals, quality measurements, and alarms — routed through Eventstream to hot KQL and immutable bronze in parallel. Production throughput per plant is measured and the F SKU sized accordingly; we don't overprovision on assumption, and Spark autoscale is off until workload/cost evidence justifies it.

**Q53. What's the path to more sites or new capabilities later?**
The same contract-first pattern: additive event fields within a major version are tolerated; new capabilities plug in as new Python workers and gold facts behind the same BFF and semantic model. Removals or semantic changes require a new major contract. Production write-back (CMMS/scheduling) is a Phase 2+ capability gated behind human approval and the full acceptance gates.

---

## M. Limitations & candor

**Q54. What are the honest limitations of what you're showing today?**
Four I'll name unprompted: (1) all demo data is **synthetic** — the four headline numbers are targets, not realized results; (2) pilot RUL scoring is **daily**, not real-time; (3) the Eventstream Custom Endpoint requires a **Contributor** publisher role, mitigated by workspace isolation, not eliminated; (4) there is **no automatic Fabric BCDR** in Sweden Central, and **no production €/hour cost figure** yet — that needs measured pilot load.

**Q55. What could still go wrong in production that the demo can't prove?**
Real-plant model accuracy against actual relines and lab results; real OT protocol/rate integration per plant; live Fabric capacity/quota provisioning and Custom-Endpoint identity in the target tenant; market-data licensing and freshness SLAs; and legal AI Act classification and lawful basis for real operator interviews. These are the §15 validation gates — deliberately open items, not weaknesses in the design.

**Q56. Why should we trust the platform if you keep saying "target" and "not proven"?**
Because that discipline *is* the trustworthiness. A vendor who converts every synthetic result into a banked saving is the one to distrust. We prove the mechanics — data core, models with uncertainty, governance, and human approval — end to end and reproducibly, and we've engineered exactly the phased, audited, human-in-the-loop path that turns targets into measured outcomes without risking a furnace or breaking a regulation.

**Q57. If the whole cloud is down during the defense, can you still make your case?**
Yes. The demo is rehearsed once online and once fully offline; a checksummed fallback pack (screenshots, thermal sequences, alert/optimizer/quality JSON, licensed synthetic WAV/transcript, Fabric lineage image, 90-second recording) lets the presenter finish the entire story with no network — announced honestly as replay/cached, never as live.

---

## N. Copilot chat assistant

**Q58. What is the Copilot chat actually allowed to do?**
Explain, not retrieve. The chat agents are given **no tools at all** (ADR-011). `knowledge-orchestrator` assembles the grounding material — the profile of the screen the user is on, the glossary definitions matching the question, and, only if the user ticks *Online search*, a curated corpus of public-context entries — and the model answers from that. It cannot query the lakehouse, the KQL database, or any operational API, so it cannot surface a value the caller was not already entitled to see. The dashboard remains the only source of numbers; the chat is the source of meaning.

**Q59. How does it know what "the risk" means when I don't say?**
Every question carries the active section, sub-view, and site. On Furnace Health, an under-specified "what is the risk" resolves to **lining risk** because that screen's profile declares it. Twenty-five concepts are matched against the question, each pinned to a glossary entry, and the answer names the sources it used so the resolution is visible rather than magical. Concept matching is token-aware and handles compound nouns, which is why it also works in German (*Zustellungsrisiko*) and Dutch (*vuurvastrisico*).

**Q60. Is this just a wrapper that hallucinates in five languages?**
The five languages are first-class data, not machine translation at runtime: 36 glossary terms, nine screen profiles, and the suggested questions all exist in EN/FR/DE/NL/ES and are verified by test. More importantly, the answer is constrained by the same grounding in every language — including the TARGET-versus-EVIDENCE discipline, so the assistant will not convert the 22 % CO₂ *target* into a measured result any more than the presenter will.

**Q61. Why isn't "Online search" a real web search?**
Deliberate. A live search engine would make the demo non-reproducible, would put untrusted third-party text into the prompt, and would let a page that changed overnight contradict the rehearsed narrative. The tick instead consults a small curated corpus of durable public-context entries — each with its official source URL — and the answer states that the corpus was used. It is honest about its own limits: the assistant tells you when it cannot answer rather than inventing a citation.

**Q62. Where do the conversations go? Is this a new GDPR surface?**
Nowhere durable. History lives **in the API process**, scoped to the calling user, and is dropped on restart (ADR-012). Free-text questions attributable to a named operator never enter the governed Fabric estate, so no new retention, classification, or subject-access obligation is created for a demonstration. A temporary-chat toggle skips storage entirely — and it genuinely skips the store, it is not a cosmetic switch — and any conversation can be deleted by its owner. A conversation belonging to another user returns `404`, not `403`, so history is not even enumerable.

**Q63. What does the green shield claim, and is the claim true?**
It reads "Enterprise data protection applies to this chat." That holds because the traffic stays inside the same Entra-authenticated BFF as every other call, the model is an Azure-hosted Foundry deployment reached with managed identity (no key, no consumer endpoint), prompts are not used for training, and nothing the chat touches leaves the tenant. Dictation is likewise **browser-side only** (Web Speech API), so audio never reaches the backend and creates no consent or retention obligation.

**Q64. Why multiple agents for reasoning tiers instead of one model?**
Because the honest answer to "which model answered this?" should never be hidden. *Default* serves short definitional questions cheaply; *High reasoning* serves multi-step questions; *Auto* picks between them from the shape of the question and then **echoes back the tier that actually answered**, so the user sees the trade-off rather than trusting a black box. If Foundry is unconfigured or a call fails, a deterministic local agent answers from exactly the same grounding material and the sources are identical — degraded, but never fabricated.

**Q65. What does the dock buy you that a modal or drawer would not?**
Dockview gives the user a real workspace: the chat can sit at any edge and be resized against the dashboard, so a question can be asked *while* the chart that provoked it is still visible — which is the whole point of screen-aware grounding. Floating groups are disabled, so the panel can never detach into a stray window that gets lost behind the browser. The layout is remembered per browser, and a stored layout that does not restore cleanly is discarded in favour of the default. While the chat is closed no grid is mounted at all, so the default dashboard render path is unchanged.

---

## O. Device Operations and Simulator

**Q66. If the device simulator is synthetic, does it represent a real OT connection?**
No — it has no connection to any OT system, PLC, historian, or real plant network, and no code path in the device simulator or BFF adapter has the capability to reach one. All 34 sensor values are generated from a seeded pseudo-random number generator advancing a deterministic clock. The Device Fleet, Sensor Explorer, and Device Simulator screens show only this synthetic ring-buffer data. The safety boundary is architectural, not a configuration toggle: the adapter has no network socket, no Event Hubs consumer, no historian client, and no write-back path. (ADR-013 and security §25.4.)

**Q67. Why does the simulator run inside the BFF rather than as a separate service?**
Because the ring buffer's memory footprint is small (~2 MB for 34 sensors × 1440 samples) and the Device Operations routes are the only consumer. Adding a separate Container App would cost approximately the same as the BFF itself and would add a network hop, a new deployment artifact, and an extra health-check surface — all for a subsystem with no independently scalable load. The pattern mirrors `optimizer-worker` and `scoring-worker`, both of which are importable Python libraries rather than microservices. The standalone FastAPI app and Dockerfile are also shipped for teams that need out-of-process deployment; that path requires only a change to `device_adapter.py` and no API contract modification.

**Q68. The Device Fleet shows `LUX-BF-01` as degraded from the start — is that a bug?**
No — it is intentional. The BFF demo-mode adapter starts with the `lining-degradation-21d` seed (240726) and pre-seeds a `degrading-furnace` incident on `LUX-BF-01` during warm-up. On every read it re-arms the incident once it expires. This ensures the Device Fleet page always shows meaningful sensor deviation without the presenter having to manually inject an incident. Any explicit operator command (e.g., `stop`, `reset`, `set-scenario`) disables the auto-seeding permanently for that process lifetime. It is a deliberate UX choice: a perfectly green all-OK fleet is not a compelling opening for a reliability conversation.

---

## P. GDPR Erasure and the Immutable Audit Chain

**Q69. GDPR Art. 17 requires data deletion — but you say the audit chain is immutable. How do you reconcile those two requirements?**
By separating data categories. Personal data (operator voice recordings, interview transcripts, and Copilot conversation text attributable to a named user) is held in stores that support hard deletion. The hash-chained audit log records *decision events* — model version, inputs, output, confidence, human action — and these are retained for safety and regulatory traceability. GDPR Art. 17(3)(d) provides an exemption for processing necessary for scientific or historical research and for reasons of public interest where erasure would seriously impair the achievement of that processing. For a blast-furnace decision trail, the exemption is engaged.

Practically: executing an erasure request appends an `erasure.executed` tombstone to the audit chain. The chain is never mutated. `verify()` returns `True` both before and after. The receipt carries `chainVerifiedBefore` and `chainVerifiedAfter`, both `true`. This lets an auditor confirm that (a) the personal data was erased and (b) the decision evidence is intact, without one claim contradicting the other.

**Q70. The erasure receipt carries `subjectPseudonym` instead of the original ID — can the subject be re-identified?**
The pseudonym is a salted SHA-256 digest of the `subjectId`. Without the salt, computing the digest from a known `subjectId` is possible but the digest cannot be reversed to recover the `subjectId`. The salt is held in the Key Vault under the same access controls as other production secrets. The raw `subjectId` is write-only at the API level: it is accepted in the request body, hashed on receipt, and never echoed in any response, list view, or audit export. This limits re-identification risk even if an audit log is exported to a less-controlled environment.

---

## Q. Grounded RAG and the Decline Behaviour

**Q71. Why does the knowledge query endpoint decline rather than always returning an answer?**
Because a confident wrong answer to a furnace-safety procedure question is more dangerous than a clear refusal. The pipeline retrieves from approved procedures only, then applies a content-term overlap guard before generating an answer. If no approved chunk shares a content term with the question, the system returns `declined: true, declineReason: "no_grounded_source"` rather than fabricating an answer from the model's parametric knowledge. The same decline fires for content-policy violations and for generated sentences that lack mandatory inline citations. This is the correct posture for a safety-critical knowledge system: the absence of a grounded source is information, not a failure.

**Q72. The pipeline uses "reciprocal rank fusion." Why not just threshold the relevance score?**
Because RRF scores are rank-aggregation artefacts with no absolute meaning. RRF fuses BM25 lexical ranking and cosine-similarity ranking by position, not by magnitude: a `fusedScore` of 0.8 from RRF does not mean "80% confidence of relevance" — it means the chunk ranked highly on both individual methods. Even a completely unrelated query will always produce a "best" chunk from RRF, because RRF always produces an ordered list. A hard threshold on `fusedScore` would therefore be arbitrary and would not prevent ungrounded answers. The content-term overlap guard is the correct semantic gate: it checks whether the retrieved chunk shares domain vocabulary with the query, which is a meaningful relevance signal independent of rank arithmetic.

---

## R. Learnability & user enablement

**Q73. How does a non-expert user learn what the platform is showing them?**
A question-mark toggle in the dashboard header activates "explain mode." The cursor becomes a help cursor; clicking any visual element — a KPI tile, a chart, a table row, a dock tab — frames it and opens a floating popup that explains it in plain language. Each topic has four fields: a title, a "what" (what this element is), a "steel" section (the industrial process behind the number), and a "useIt" section (how to interact with this screen). The audience is explicitly someone who has never seen a steel plant and has never used this portal — the same position as a defense juror. Clicking another element replaces the popup; Esc or the close button exits. The feature is implemented in `apps/analytics-mfe/src/components/help/HelpAssistant.tsx`.

**Q74. What is the engineering design, and why does it scale to new screens without effort?**
Topics are resolved **from the DOM at click time** by the walker in `resolveHelpTarget.ts`, not from a per-screen registry. Three shared primitives (`KpiCard`, `ChartContainer`, `DataTable`) carry a `data-help` attribute automatically, and the walker additionally detects structural elements — Dockview tabs, table headers, table body rows — by tag name and CSS class without any attribute. Any new screen composed from these primitives is explainable the moment it renders, with zero additional wiring. The trade-off is stated honestly: a bespoke one-off component that does not use the shared primitives and does not declare its own `data-help` attribute will receive only a generic fallback explanation (e.g., "No explanation has been written for this element yet.") unless a developer adds a topic. That limitation is by design — it keeps the system honest about what it knows rather than inventing content.

**Q75. How do you guarantee content quality and multilingual support?**
The catalog follows a strict house style: two short sentences per field, no unexpanded acronym, no marketing language, written for a reader with no steel background (see `helpMessages.ts` header comment). There are 87 topics (79 in the base catalog, 1 satellite diagram topic and 7 satellite Knowledge Hub topics) maintained across five locales (EN, FR, DE, NL, ES). A bilingual EN+FR mode — toggled in settings, off by default — stacks both languages in the same popup so a Luxembourg audience comfortable in either language sees both without switching the portal locale (`helpCatalogs.ts`, `bilingual()` function). Each language gets its own paragraph and the French half is rendered in blue with a `lang="fr"` attribute, so the two are never mistaken for one run-on sentence (`BilingualText.tsx`). Key parity is enforced by the test suite (`helpCatalogs.test.ts`): every locale must declare exactly the English topic set, with the same optional fields present, and no text may be empty. Missing or extra keys in any locale fail the build, which matters because i18n keys that fall out of sync fail silently at runtime — the test is the only safety net.

**Q76. The Copilot Chat assistant also explains things. Why do both exist rather than one?**
They serve different cognitive moments. Explain mode answers "what is this thing I am looking at?" — a closed-vocabulary, instant, deterministic lookup with no network call and no model invocation. The Copilot Chat answers "what does this mean for my decision?" — an open-ended, conversational question requiring LLM reasoning grounded in glossary terms and screen context. Explain mode is offline-capable and bit-for-bit reproducible; Chat depends on a Foundry model endpoint and may return a degraded local answer if that endpoint is unreachable. Combining them into one system would force every quick "what is this?" click through a model call, adding latency and a failure surface to the simplest interaction on the platform. Keeping them separate lets explain mode stay instant and deterministic while Chat handles the questions that genuinely need reasoning.


---

## S. Data-visual affordances and mode honesty

**Q77. Your charts have both a zoom percentage and a drag-select. Is that not two ways to do the same thing?**
No, and the distinction matters when a juror is watching a dense 24-hour series on a projector. The percentage control is *magnification*: it widens the chart's inner box and every D3 chart re-renders at the larger geometry, so axes, tick density and labels are drawn natively rather than scaled as a bitmap. Drag-select is *data windowing*: pressing inside the plot area and dragging horizontally re-scales the x domain to the selected range, so a 24-hour series becomes a 40-minute series with its own axis ticks. One makes the same data bigger; the other changes which data is drawn. They are deliberately surfaced in a single zoom cluster with one reset, so a presenter never has to explain two controls. Implementation is generic (`useBrushZoom`, `BrushOverlay`) and applied to the seven chart types that have a meaningful x range; donuts, gauges, bullets, sparklines and the heatmap are excluded because an x-band selection there would be meaningless. A drag under 8 pixels is treated as a click, so tooltips and navigation on top of a chart still work, and Escape cancels a drag in progress.

**Q78. The KPI tiles are coloured. Is that decoration, or does the colour mean something?**
It means something, and it did not always. An earlier iteration tinted tiles from a hash of the metric id, which looked deliberate but carried no information — a fair criticism, and it was replaced. Each tile now resolves to one of four semantic states: `ok`, `warning`, `critical` or `neutral`. Screens that know a real threshold set the state explicitly (Command Center, Device Fleet, furnace lining forecast, platform capacity, quality batches); everywhere else it is derived from the metric's trend against its declared good direction, so a metric moving the wrong way is amber without any per-screen wiring. Colour is never the only channel: every tile also carries a status icon and localized status text in its accessible name, which is WCAG 1.4.1. Contrast of body text against the tile background was measured at 12.7–15.4:1 across both light and dark themes.

**Q79. The badge says CLOUD. What is actually different from DEMO, and is the data suddenly real?**
The data is synthetic in both modes — that is a property of the whole platform, not of a toggle, and we do not claim otherwise. What changes is that demo scaffolding (synthetic-data banners, seed and reset affordances) is hidden and the shell asserts which backend it reached. Switching to cloud mode calls the unauthenticated bootstrap route `GET /v1/meta` and reports what answered: service name, API version, environment and auth mode. If nothing answers within eight seconds the shell reverts to demo mode and says why, so a `CLOUD` badge is never displayed without a backend behind it. This replaced an earlier placeholder message claiming live mode was not yet configured, which had become false once the micro-frontend was calling the deployed BFF in both modes.
