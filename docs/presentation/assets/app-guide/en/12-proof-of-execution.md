# 12 · Proof of Execution

**Audience:** jury, examiner, auditor, developer, or newcomer who wants proof  
**Reading time:** 22 minutes  
**Persona:** all personas; especially a defense panel  
**Routes covered:** `/{site}/proof-of-execution/requirements`, `/{site}/proof-of-execution/use-case`  
**Last updated:** 2026-07-27  
**Language:** 🇫🇷 [Version française](../fr/12-proof-of-execution.md)

---

## Requirement Register — `/{site}/proof-of-execution/requirements`
![Proof of execution requirements](../screenshots/proof-of-execution-requirements.png)

**In one sentence.** The evidence ledger: every statement in the use-case brief has a stable ID, status, proving screen, evidence and caveat (`apps\analytics-mfe\src\components\screens\ProofOfExecution.tsx`; `apps\analytics-mfe\src\proof\proofCatalog.ts`).

**Background for newcomers.** A proof register is a checklist for an examiner. Instead of claiming “NovaSteel satisfies the brief,” the app lists what is proven, where to see it, and what remains simulated. The same IDs are stamped on proving screens, so `OUT-03` always means the 21-day furnace-lining warning (`docs\presentation\proof_of_execution.md`; `ProofOfExecution.tsx`).

**Status vocabulary.**

| Status | Meaning | Why it matters |
|---|---|---|
| Met | Capability exists and runs in the demo. | A reviewer can click to a proving screen (`proofCatalog.ts`). |
| Partial | Capability exists but is narrower than the brief. | The limitation is stated before anyone discovers it by search (`docs\presentation\proof_of_execution.md`). |
| Demo surrogate | Mechanism is real; headline number is a synthetic target. | It separates “control built” from “real plant achieved it” (`proofCatalog.ts`). |

**What you see on screen.**
1. KPI cards show **19** requirements, **15** met, **4** partial/demo and **78.9%** coverage, computed by `proofCoverage()` (`proofCatalog.ts`; `ProofOfExecution.tsx`).
2. Category chips split the register into Regulatory context, Business challenge, Transformation objective, Expected outcome and AI infusion point (`proofCatalog.ts`).
3. The search box matches IDs, statements, targets, caveats and evidence (`ProofOfExecution.tsx`).
4. The progress bar is not 100%, deliberately, because caveats remain visible (`ProofOfExecution.tsx`; `docs\presentation\proof_of_execution.md`).
5. The register table has Ref, Category, Requirement, Target and Status columns, with sorting, search and export (`ProofOfExecution.tsx`; `docs\ux\dashboard-specification.md`).
6. The detail panel shows the selected row, explanation, evidence links and **Open the screen** when a proving route exists (`ProofOfExecution.tsx`).
7. The screenshot selects `REG-01`, explaining GDPR consent, personal-data minimization, erasure and audit tombstones (`proofCatalog.ts`).

**Why this component was implemented.** The brief lists regulatory context, five business challenges, four objectives, four expected outcomes and three AI infusion points (`docs\usecase\usecase.md`). The register turns those statements into traceable evidence instead of slideware (`docs\presentation\proof_of_execution.md`; `proofCatalog.ts`).

**Full requirement register.** This table reproduces the catalog in beginner-friendly wording (`apps\analytics-mfe\src\proof\proofCatalog.ts`).

| ID | Requirement, in plain language | Status | Proving screen(s) | Evidence |
|---|---|---|---|---|
| `REG-01` | Operator personal data must be lawful, minimized and erasable under the General Data Protection Regulation (GDPR). | Met | Sustainability & Compliance → Audit & Reports | Consent, PII redaction, erasure, tombstone audit; privacy routes (`proofCatalog.ts`). |
| `REG-02` | AI affecting industrial operations needs human oversight and transparency under the EU AI Act. | Met | Energy Optimization; Audit & Reports | Gated state graph, forbidden tools, prompt defense, content safety, approval alert (`proofCatalog.ts`). |
| `REG-03` | EU Emissions Trading System (EU ETS) accounting must be reportable. | Partial | ETS Exposure; Emissions Ledger | Gold-layer emissions and summary routes; demo constants caveat (`proofCatalog.ts`). |
| `CHL-01` | Energy is 35% of production cost and needs real-time optimization. | Met | Spot & Schedule; Load-Shift Simulator | Mixed-integer linear program (MILP); `POST /v1/energy/schedules:simulate` (`proofCatalog.ts`). |
| `CHL-02` | CO₂ is under EU ETS penalty pressure. | Met | Emissions Ledger | Carbon term in optimizer objective, emissions metric and ledger (`proofCatalog.ts`). |
| `CHL-03` | Furnace lining wear must be predicted before €8M failures. | Met | Lining Forecast | Physics features, remaining-useful-life (RUL) model, `GET /v1/furnaces/{assetId}/lining-forecast` (`proofCatalog.ts`). |
| `CHL-04` | High-grade automotive steel quality is inconsistent. | Met | Batch Quality; Defect Analytics (SPC) | Batch risk, statistical process control (SPC), quality what-if (`proofCatalog.ts`). |
| `CHL-05` | Retiring skilled operators are taking knowledge with them. | Met | Procedures; Capture Status | Consent-bound interviews, reviewed procedures, approved-only retrieval (`proofCatalog.ts`). |
| `OBJ-01` | Reduce energy consumption. | Met | Energy Optimization; Command Center | Energy per tonne from solved schedule (`proofCatalog.ts`). |
| `OBJ-02` | Predict equipment failures. | Met | Lining Forecast; Maintenance Planner | Continuous RUL scoring and Real-Time Intelligence activator (`proofCatalog.ts`). |
| `OBJ-03` | Improve steel quality. | Met | Quality screens | Predicted first-pass yield, defect Pareto, SPC and bounded what-if (`proofCatalog.ts`). |
| `OBJ-04` | Capture and structure operational expertise. | Met | Capture Status | Spoken interview to cited, reviewed, versioned procedure (`proofCatalog.ts`). |
| `OUT-01` | Energy consumption per tonne reduced by 14%. | Demo surrogate | Command Center; Executive Overview | Mechanism computes energy per tonne; −14% is synthetic target (`proofCatalog.ts`). |
| `OUT-02` | CO₂ emissions reduced by 22%. | Demo surrogate | Emissions Ledger; Executive Overview | Scope 2 recomputation; −22% is wider ambition, not demo result (`proofCatalog.ts`). |
| `OUT-03` | Furnace lining failure predicted with 21-day advance warning. | Met | Lining Forecast | Alert threshold P50 ≤ 21 days and risk ≥ 0.80 (`proofCatalog.ts`). |
| `OUT-04` | High-grade steel yield improved by 8 percentage points. | Demo surrogate | Batch Quality; Executive Overview | Scored synthetic yield; +8 is manifest target (`proofCatalog.ts`). |
| `AI-01` | Physics-informed machine learning predicts lining degradation from thermal signatures. | Met | Thermal Explorer | Thermal features and regression with uncertainty (`proofCatalog.ts`). |
| `AI-02` | Energy-dispatch agent schedules energy-intensive work around spot prices. | Met | Load-Shift Simulator | MILP solver, agent handoff and human approval route (`proofCatalog.ts`). |
| `AI-03` | Generative AI captures operator knowledge into searchable procedures. | Met | Procedures | Speech-to-text, grounded extraction, critic loop, hybrid retrieval (`proofCatalog.ts`). |

**Anti-drift design.** The markdown projection `docs\presentation\proof_of_execution.md`, the in-app screen, proof badges and this guide all point back to `apps\analytics-mfe\src\proof\proofCatalog.ts`. `ProofOfExecution.tsx` imports `PROOF_REQUIREMENTS`, and badges resolve through `PROOF_BY_ID`; an ID cannot silently mean different things on different screens (`ProofOfExecution.tsx`; `proofCatalog.ts`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Whole brief | `REG-01`…`AI-03` | Searchable register with caveats and open-screen links | No BFF route; `ProofOfExecution.tsx` imports `PROOF_REQUIREMENTS` from `proofCatalog.ts`. |
| Coverage score | All 19 | 19 total, 15 met, 4 partial/demo, 78.9% | `proofCoverage()` in `proofCatalog.ts`. |
| Stable IDs on screens | All 19 | Proof chips and detail panel | `ProofBadge` resolves `PROOF_BY_ID` (`ProofOfExecution.tsx`; `proofCatalog.ts`). |

**How the data reaches this screen.** `ProofOfExecution.tsx` → `PROOF_REQUIREMENTS`, `PROOF_CATEGORY_ORDER`, `proofCoverage()` → no BFF route → local catalog (`apps\analytics-mfe\src\proof\proofCatalog.ts`). Clicking a proving screen navigates to the destination, which then uses its own `DataClient` and BFF path if required (`apps\analytics-mfe\src\api\dataClient.ts`).

**Honesty & caveats.** The register is credible because it is not all green: `REG-03` is Partial; `OUT-01`, `OUT-02` and `OUT-04` are Demo surrogate (`proofCatalog.ts`). The proof document explicitly says caveats should be stated before a jury finds them by grep (`docs\presentation\proof_of_execution.md`).

**Try it yourself.** Open `http://localhost:5266/{site}/proof-of-execution/requirements`, search for `OUT-02` or `GDPR`, select a row and use **Open the screen**.

---

## Use Case — `/{site}/proof-of-execution/use-case`
![Proof of execution use case](../screenshots/proof-of-execution-use-case.png)

**In one sentence.** The Use Case tab brings the original brief into the app and binds each brief line to proof IDs (`apps\analytics-mfe\src\components\screens\UseCaseBrief.tsx`).

**Background for newcomers.** A use-case brief is the short business story: industry, challenge, transformation objective, expected outcomes and AI mechanisms. NovaSteel’s source brief is `docs\usecase\usecase.md`; the component reproduces those sections with proof badges (`UseCaseBrief.tsx`; `docs\usecase\usecase.md`).

**What you see on screen.** The supplied screenshot currently shows the same visible register layout as Requirements: KPI cards, filters, progress bar, requirement table and `REG-01` detail panel (`../screenshots/proof-of-execution-use-case.png`; `ProofOfExecution.tsx`). The source component for the Use Case tab defines these panels:
1. a use-case KPI band using `proofCoverage()` (`UseCaseBrief.tsx`; `proofCatalog.ts`);
2. a source panel linking `docs/usecase/usecase.md` (`UseCaseBrief.tsx`);
3. industry profile: Heavy Industry & Metals, Luxembourg headquarters, LU/DE/BE/ES, GDPR/EU AI Act/EU directives (`UseCaseBrief.tsx`; `docs\usecase\usecase.md`);
4. business challenges, objectives, expected outcomes and AI infusion points, each with proof badges (`UseCaseBrief.tsx`).

**Why this component was implemented.** The brief says to implement an “AI-driven production optimization platform” and lists measurable outcomes (`docs\usecase\usecase.md`). Rendering the brief inside the app prevents a gap between what the presenter says and what the application proves (`UseCaseBrief.tsx`; `docs\presentation\proof_of_execution.md`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Brief rendered in app | All 19 | Use Case component maps brief lines to badges | No BFF route; arrays `PROFILE`, `CHALLENGES`, `OBJECTIVES`, `OUTCOMES`, `AI_POINTS` in `UseCaseBrief.tsx`. |
| Source traceability | All 19 | Source link to `docs/usecase/usecase.md` | `USECASE_SOURCE_URL` in `UseCaseBrief.tsx`; source file `docs\usecase\usecase.md`. |
| Honest status display | All 19 | Badge color derives from linked proof IDs | `statusOf()` reads `PROOF_BY_ID` (`UseCaseBrief.tsx`; `proofCatalog.ts`). |

**How the data reaches this screen.** `UseCaseBrief.tsx` → local arrays lifted from `docs\usecase\usecase.md` → `PROOF_BY_ID` and `proofCoverage()` → no BFF route. Proving screens then use their own data routes (`UseCaseBrief.tsx`; `dataClient.ts`).

**Honesty & caveats.** If the current captured image still shows the register, describe the visible register widgets and cite the source component for intended Use Case content. The Use Case tab is a projection, not a separate source of truth (`ProofOfExecution.tsx`; `UseCaseBrief.tsx`; `proofCatalog.ts`).

**Try it yourself.** Open `http://localhost:5266/{site}/proof-of-execution/use-case` and switch between Requirements and Use Case if the tab state is not already selected.

---

[◀ Previous: 11 · Dashboard Collections](11-dashboard-collections.md) · [▲ Index](README.md) · [Next ▶ 13 · Platform Ops](13-platform-ops.md)
