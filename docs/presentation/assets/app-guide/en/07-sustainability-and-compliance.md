# 07 — Sustainability and Compliance

**Audience:** complete beginners to steelmaking and European regulation  
**Reading time:** 12 minutes  
**Persona:** Amina Haddad — Sustainability Officer  
**Routes covered:** `/{site}/sustainability-compliance/emissions-ledger`, `/{site}/sustainability-compliance/ets-exposure`, `/{site}/sustainability-compliance/audit`  
**Last updated:** 2026-07-27  
[🇫🇷 Version française](../fr/07-sustainability-and-compliance.md)

NovaSteel's sustainability area explains carbon performance, European Union Emissions Trading System (EU ETS) exposure, and decision evidence with deterministic synthetic data; the BFF and fixtures mark this data as synthetic and not for operational control (`services\bff-api\src\bff_api\repository.py`, `apps\analytics-mfe\src\api\fixtures.ts`).

## Newcomer basics

The **EU Emissions Trading System (EU ETS)** is a cap-and-trade market. A regulator limits total covered emissions, steelmakers surrender allowances called **European Union Allowances (EUAs)**, and a shortage creates financial exposure because extra allowances may need to be bought in euros per tonne of carbon dioxide (CO₂) (`docs\presentation\proof_of_execution.md`).

| Scope | Plain meaning | Steel example |
|---|---|---|
| Scope 1 | Direct emissions from the producer's own process. | Coke, blast-furnace gas, or natural gas burned on site. |
| Scope 2 | Indirect emissions from purchased electricity. | Grid electricity for mills, pumps, utilities, and reheating lines. |
| Scope 3 | Other value-chain emissions. | Mining, purchased raw materials, transport, or customer use. |

NovaSteel implements Scope 1 and Scope 2 in this area; CBAM and Industrial Emissions Directive logic are explicitly not implemented in code (`docs\presentation\proof_of_execution.md`, `apps\analytics-mfe\src\proof\proofCatalog.ts`). An **emissions ledger** is a traceable list of emission events; this demo computes Scope 2 as electricity consumption times grid carbon intensity and keeps a source reference (`services\bff-api\src\bff_api\repository.py`, `apps\analytics-mfe\src\api\fixtures.ts`). A **hash chain** links each audit record to the previous record's hash, so silent edits break later hashes and become detectable (`services\bff-api\src\bff_api\audit.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\audit.py`).

## Emissions Ledger — `/{site}/sustainability-compliance/emissions-ledger`

![Emissions ledger screen](../screenshots/sustainability-emissions-ledger.png)

**In one sentence.** The screen shows modelled CO₂, steel intensity, ETS headroom, and the ledger rows behind those numbers.

**Background for newcomers.** Amina needs to connect carbon cost to plant decisions because the use case says "CO₂ emissions" are under pressure from "EU Emissions Trading System (ETS) penalties" and targets "CO₂ emissions reduced by 22%" (`docs\usecase\usecase.md`).

**What you see on screen.**  
1. The purple **Synthetic demo data — not for operational control** banner warns that the values are fixtures, not live plant measurements (`services\bff-api\src\bff_api\repository.py`).
2. The persona pill shows **Amina Haddad - Sustainability Officer**, matching the persona responsible for CO₂ and ETS reporting (`docs\personas\personas-and-journeys.md`).
3. Four KPI cards show **CO₂ (Scope 2) 165.9 t/day**, **CO₂ / t steel 1.42 t/t**, **ETS allowances left 71%**, and **ETS € exposure €132K** at €86/t; lower CO₂ and more allowance headroom are good, while rising intensity or shrinking headroom is bad (`apps\analytics-mfe\src\components\screens\SustainabilityEmissions.tsx`, `services\bff-api\src\bff_api\repository.py`).
4. **CO₂ trend vs target** plots a blue Scope 2 line against a dotted target line, so a beginner can see whether interval emissions stay below the daily target (`apps\analytics-mfe\src\components\screens\SustainabilityEmissions.tsx`).
5. **Emissions by scope** shows a much taller Scope 1 bar, about 1,368 t, and a Scope 2 bar, about 165.9 t, reminding viewers that integrated steelmaking has major process emissions (`apps\analytics-mfe\src\components\screens\SustainabilityEmissions.tsx`, `apps\analytics-mfe\src\api\fixtures.ts`).
6. **Emissions ledger (immutable)** has badges `CHL-02` and `OUT-02`, search, column controls, export, refresh, and rows with Date, Site, and Scope 2 kgCO₂e; good means each number can be traced to a source event (`apps\analytics-mfe\src\components\screens\SustainabilityEmissions.tsx`, `docs\presentation\proof_of_execution.md`).

**Why this component was implemented.** It demonstrates the quoted challenge "CO₂ emissions under increasing pressure from EU Emissions Trading System (ETS) penalties" and the outcome target "CO₂ emissions reduced by 22%" (`docs\usecase\usecase.md`). The proof catalogue maps this screen to `CHL-02` and `OUT-02`, while warning that −22% is a synthetic target, not a measured filing result (`apps\analytics-mfe\src\proof\proofCatalog.ts`, `docs\presentation\proof_of_execution.md`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| CO₂ under ETS penalty pressure | `CHL-02` | Ledger proof badge, CO₂ KPI, ETS exposure KPI. | `GET /v1/sustainability/emissions`, `GET /v1/sustainability/summary`; `apps\analytics-mfe\src\api\dataClient.ts`, `services\bff-api\src\bff_api\routes.py`, `services\bff-api\src\bff_api\repository.py`. |
| CO₂ reduction target | `OUT-02` | `target −22%` on the KPI and proof badge on the ledger. | UI in `SustainabilityEmissions.tsx`; caveat in `docs\presentation\proof_of_execution.md`. |
| ETS accounting context | `REG-03` | Ledger feeds the ETS exposure story, but proof is partial. | `GET /v1/sustainability/summary`; `apps\analytics-mfe\src\proof\proofCatalog.ts`. |

**How the data reaches this screen.** `SustainabilityEmissions.tsx` calls `client.getEmissions()` and `client.getSustainabilitySummary()`; `DataClient` maps those to `GET /v1/sustainability/emissions` and `GET /v1/sustainability/summary`; FastAPI routes read `DemoRepository.emissions_rows()` and `DemoRepository.sustainability_summary()`; offline mode falls back to `fixtures.emissions()` and `fixtures.sustainabilitySummary()` (`apps\analytics-mfe\src\components\screens\SustainabilityEmissions.tsx`, `apps\analytics-mfe\src\api\dataClient.ts`, `services\bff-api\src\bff_api\routes.py`, `services\bff-api\src\bff_api\repository.py`, `apps\analytics-mfe\src\api\fixtures.ts`).

**Honesty & caveats.** Scope 2 is modelled from energy and carbon intensity, Scope 1 is a demo formula, and no official ETS filing is produced (`services\bff-api\src\bff_api\repository.py`, `docs\presentation\proof_of_execution.md`).

**Try it yourself.** Open `http://localhost:5266/LU/sustainability-compliance/emissions-ledger` and compare the KPI cards with the ledger table (`docs\ux\dashboard-specification.md`, `apps\analytics-mfe\src\components\screens\SustainabilityEmissions.tsx`).

## ETS Exposure — `/{site}/sustainability-compliance/ets-exposure`

![ETS exposure screen](../screenshots/sustainability-ets-exposure.png)

**In one sentence.** The screen converts allowance use and modelled emissions into a simple financial risk view.

**Background for newcomers.** EU ETS exposure means the possible cost of needing more allowances when emissions exceed the allowance budget; NovaSteel uses a synthetic €86/t price and deterministic projection, not a live registry account (`apps\analytics-mfe\src\components\screens\SustainabilityEts.tsx`, `services\bff-api\src\bff_api\repository.py`).

**What you see on screen.**  
1. KPI cards show **Allowances used 71%**, **ETS price €86/t**, **Projected overage Month 5**, and **Exposure €248K**; yellow cards signal review, while the green exposure card is still only a modelled forecast (`apps\analytics-mfe\src\components\screens\SustainabilityEts.tsx`).
2. The **ETS allowance projection** chart plots cumulative use by month, with an orange **Guidance 85%** line and red **Cap 100%** line; nearing 85% is an early warning, and crossing 100% would mean the synthetic cap is exceeded (`apps\analytics-mfe\src\components\screens\SustainabilityEts.tsx`).
3. The **Allowances used vs cap** gauge repeats 71% and carries proof badge `REG-03`; good means enough headroom remains, bad means the gauge moves toward the cap (`apps\analytics-mfe\src\components\screens\SustainabilityEts.tsx`, `apps\analytics-mfe\src\proof\proofCatalog.ts`).
4. The caption says targets are modelled synthetic figures, not financial commitments, which is essential for honest EU ETS discussion (`apps\analytics-mfe\src\components\screens\SustainabilityEts.tsx`, `docs\presentation\proof_of_execution.md`).

**Why this component was implemented.** Amina's persona goal is to manage EU ETS allowance cost exposure, and the use case makes ETS penalties a central pressure (`docs\personas\personas-and-journeys.md`, `docs\usecase\usecase.md`). The proof catalogue maps ETS Exposure to `REG-03` and marks it partial because the allowance benchmark and price are demo constants (`apps\analytics-mfe\src\proof\proofCatalog.ts`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Sector EU ETS obligations | `REG-03` | Gauge badge, projection chart, price, and exposure KPI. | `GET /v1/sustainability/summary`; constants in `apps\analytics-mfe\src\components\screens\SustainabilityEts.tsx`; route in `services\bff-api\src\bff_api\routes.py`. |
| CO₂/ETS pressure | `CHL-02` | Exposure links carbon to financial risk. | Summary from `services\bff-api\src\bff_api\repository.py`; UI calculation in `SustainabilityEmissions.tsx`. |
| Filing honesty | `REG-03` caveat | Text says targets are modelled, not commitments. | `docs\presentation\proof_of_execution.md`, `apps\analytics-mfe\src\components\screens\SustainabilityEts.tsx`. |

**How the data reaches this screen.** `SustainabilityEts.tsx` calls `client.getSustainabilitySummary()`; `DataClient` requests `GET /v1/sustainability/summary`; the BFF returns `DemoRepository.sustainability_summary()`; the 71%, 85%, 100%, and €248K projection values are deterministic UI constants (`apps\analytics-mfe\src\components\screens\SustainabilityEts.tsx`, `apps\analytics-mfe\src\api\dataClient.ts`, `services\bff-api\src\bff_api\routes.py`, `services\bff-api\src\bff_api\repository.py`).

**Honesty & caveats.** The screen does not connect to the Union Registry, calculate legal free allocation, implement CBAM, or file anything with an authority (`docs\presentation\proof_of_execution.md`, `apps\analytics-mfe\src\proof\proofCatalog.ts`).

**Try it yourself.** Open `http://localhost:5266/LU/sustainability-compliance/ets-exposure` and read the 71% gauge together with the projection chart (`docs\ux\dashboard-specification.md`, `apps\analytics-mfe\src\components\screens\SustainabilityEts.tsx`).

## Audit & Reports — `/{site}/sustainability-compliance/audit`

![Audit and reports screen](../screenshots/sustainability-audit.png)

**In one sentence.** The screen is the read-only evidence table for AI-assisted decisions.

**Background for newcomers.** Auditors ask who acted, what changed, which model or rule produced it, and whether the record can be altered later; NovaSteel answers with an append-only, hash-chained audit log (`services\bff-api\src\bff_api\audit.py`, `docs\presentation\proof_of_execution.md`).

**What you see on screen.**  
1. KPI cards show **Decision records 2**, **Domains covered 2**, **Model-linked 2**, and **Immutability 100%**; good means the visible records have actor/action/entity/model linkage (`apps\analytics-mfe\src\components\screens\SustainabilityAudit.tsx`).
2. The **Audit & decision evidence (read-only)** table carries badges `REG-01` and `REG-02`, linking it to GDPR and EU AI Act proof (`apps\analytics-mfe\src\components\screens\SustainabilityAudit.tsx`, `apps\analytics-mfe\src\proof\proofCatalog.ts`).
3. Columns include Time, Actor, Action, Domain, Entity, Model version, Correlation, and Audit ref; visible rows include `energy.simulate` and `lining.score` (`apps\analytics-mfe\src\components\screens\SustainabilityAudit.tsx`).
4. Search boxes, column controls, download, and refresh make it a review/export surface, not an edit surface; the audit service exposes append and query, not public update/delete (`services\bff-api\src\bff_api\audit.py`).
5. An auditor would sample records, reconcile source references, and verify the hash chain; `verify()` recomputes the chain and fails if a record was tampered with (`services\bff-api\src\bff_api\audit.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\audit.py`).

**Why this component was implemented.** GDPR needs lawful, minimised, erasable personal data, and the EU AI Act context needs human oversight, transparency, and traceability; proof IDs `REG-01` and `REG-02` capture those controls (`docs\presentation\proof_of_execution.md`, `apps\analytics-mfe\src\proof\proofCatalog.ts`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| GDPR accountability and erasure evidence | `REG-01` | Audit badge; erasure appends a tombstone and preserves chain verification. | `GET /v1/audit/decisions`, `POST /v1/privacy/erasure-requests/{id}:execute`; `services\bff-api\src\bff_api\routes.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\erasure.py`. |
| EU AI Act traceability | `REG-02` | Read-only rows show actor, action, model version, and correlation. | `GET /v1/audit/decisions`; `services\bff-api\src\bff_api\audit.py`; `SustainabilityAudit.tsx`. |
| Operational decision lineage | `CHL-02`, related | Energy and furnace records are visible examples. | `DataClient.getAudit()` to `/v1/audit/decisions`; fallback in `apps\analytics-mfe\src\api\fixtures.ts`. |

**How the data reaches this screen.** `SustainabilityAudit.tsx` calls `client.getAudit()`; `DataClient.getAudit()` requests `GET /v1/audit/decisions`; the BFF route calls `services.audit.query()`; offline mode uses `fixtures.auditDecisions()` (`apps\analytics-mfe\src\components\screens\SustainabilityAudit.tsx`, `apps\analytics-mfe\src\api\dataClient.ts`, `services\bff-api\src\bff_api\routes.py`, `services\bff-api\src\bff_api\audit.py`, `apps\analytics-mfe\src\api\fixtures.ts`).

**Honesty & caveats.** The UI has export controls, but it is not an official filing pack. GDPR Article 17 erasure is implemented for knowledge data through hard delete, pseudonymisation, and an audit tombstone; automatic expiry after `retentionDays` is documented as an operations runbook, not a running job (`services\knowledge-orchestrator\src\knowledge_orchestrator\erasure.py`, `docs\presentation\proof_of_execution.md`).

**Try it yourself.** Open `http://localhost:5266/LU/sustainability-compliance/audit`, filter a domain, and explain the actor/action/entity/model-version chain (`apps\analytics-mfe\src\components\screens\SustainabilityAudit.tsx`, `services\bff-api\src\bff_api\routes.py`).

## What this screen would need before a real regulatory filing

| Need | Why it matters | Current status |
|---|---|---|
| Verified measurement, reporting, and verification plan | Regulators need calibrated meters, legal boundaries, and third-party verification. | Demo fixtures only (`services\bff-api\src\bff_api\repository.py`). |
| Live EU ETS registry and allowance data | Real exposure depends on actual holdings, surrenders, and free allocation. | Demo constants (`apps\analytics-mfe\src\components\screens\SustainabilityEts.tsx`). |
| Legal entity / installation mapping | ETS reports are by permitted installation, not demo site code. | App routes use `/{site}/...` and `NS-DEMO-*` data (`services\bff-api\src\bff_api\repository.py`). |
| Approved report templates and verifier workflow | Export is not a filing. | UX specifies export; proof makes no filing claim (`docs\ux\dashboard-specification.md`, `docs\presentation\proof_of_execution.md`). |
| CBAM / Industrial Emissions Directive scope | May matter for real steel permits and trade. | Not implemented (`docs\presentation\proof_of_execution.md`). |

---

[◀ Previous: 06 — Quality](06-quality.md) | [▲ Index](README.md) | [Next ▶: 08 — Knowledge Hub](08-knowledge-hub.md)
