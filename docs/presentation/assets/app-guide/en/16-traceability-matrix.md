# 16 · Traceability matrix — screen ↔ use case ↔ evidence

**Audience:** anyone who has to prove that NovaSteel actually answers the AxelorMetal use case — examiner, jury member, new team member.
**Reading time:** ~12 minutes (or 30 seconds if you only need one row).
**Routes covered:** all 31 screens.
**Last updated:** 2026-07-27
**Language:** 🇫🇷 [Version française](../fr/16-traceability-matrix.md)

---

## 1. Why this page exists

A demo that *looks* impressive proves nothing on its own. What proves something is a
**closed loop**:

```
business problem  →  a screen that addresses it  →  a number on that screen
      →  the API route that produced the number  →  the source file that computed it
      →  a test that pins the behaviour
```

This page is that loop, written out once for every screen and every requirement. If
you can only read one file in this guide before defending the application, read this
one and [12 · Proof of Execution](12-proof-of-execution.md).

Two conventions used throughout:

| Convention | Meaning |
|---|---|
| **Requirement ID** | A stable identifier (`REG-01`, `CHL-03`, `OUT-02`, `AI-01`…) for one line of the use-case brief. Defined in `apps/analytics-mfe/src/proof/proofCatalog.ts`. |
| **Status** | `Met` = it runs. `Partial` = it runs but is narrower than the brief. `Demo surrogate` = the *mechanism* is real, the *headline number* is a target computed from synthetic data and is labelled as a target everywhere in the UI. |

> **Honesty first.** Every number you see in the running application comes from a
> deterministic **synthetic** dataset. NovaSteel is **advisory-only**: it never writes a
> setpoint, never talks to a PLC, and never touches a safety interlock.

---

## 2. The use case in one table

Source: [`docs/usecase/usecase.md`](../../../../usecase/usecase.md).

| Business challenge | What it costs AxelorMetal | Requirement ID | Primary screen |
|---|---|---|---|
| Energy is 35 % of production cost, with no real-time optimization | The single largest controllable cost line | `CHL-01` | Energy Optimization › Spot & Schedule |
| CO₂ under EU ETS penalty pressure | A carbon bill that grows with the allowance price | `CHL-02` | Sustainability › Emissions Ledger |
| Furnace lining wear is impossible to predict | **€8 M per catastrophic failure** | `CHL-03` | Furnace Health › Lining Forecast |
| Quality inconsistency in high-grade automotive steel | Rejected coils, lost contracts | `CHL-04` | Quality › Batch Quality |
| Skilled operators retiring faster than knowledge is captured | Irreplaceable tacit expertise walks out of the gate | `CHL-05` | Knowledge Hub › Procedures |

| Transformation objective | Requirement ID | Primary screen |
|---|---|---|
| Reduce energy consumption | `OBJ-01` | Energy Optimization › Spot & Schedule |
| Predict equipment failures | `OBJ-02` | Furnace Health › Lining Forecast |
| Improve steel quality | `OBJ-03` | Quality › Batch Quality |
| Capture and structure operational expertise | `OBJ-04` | Knowledge Hub › Capture Status |

| Expected outcome | Target | Requirement ID | Status | Primary screen |
|---|---|---|---|---|
| Energy consumption per ton | −14 % kWh/t | `OUT-01` | Demo surrogate | Command Center › Overview |
| CO₂ emissions | −22 % | `OUT-02` | Demo surrogate | Sustainability › Emissions Ledger |
| Furnace lining failure warning | 21 days | `OUT-03` | **Met** | Furnace Health › Lining Forecast |
| High-grade steel yield | +8 pts first-pass | `OUT-04` | Demo surrogate | Quality › Batch Quality |

| AI infusion point | Requirement ID | Status | Primary screen |
|---|---|---|---|
| Physics-informed ML predicts lining degradation from thermal signatures | `AI-01` | Met | Furnace Health › Thermal Explorer |
| Energy dispatch optimization agent schedules around spot prices | `AI-02` | Met | Energy Optimization › Load-Shift Simulator |
| GenAI knowledge capture interviews operators into a procedure library | `AI-03` | Met | Knowledge Hub › Procedures |

| Regulatory context | Requirement ID | Status | Primary screen |
|---|---|---|---|
| GDPR — lawful, minimised, erasable personal data | `REG-01` | Met | Sustainability › Audit & Reports |
| EU AI Act — human oversight and transparency | `REG-02` | Met | Sustainability › Audit & Reports |
| Sector directives — EU ETS accounting and reporting | `REG-03` | Partial | Sustainability › ETS Exposure |

**Totals:** 19 requirements — 15 fully met, 1 partial, 3 demo surrogates.

---

## 3. Screen → requirement matrix (all 31 screens)

Route grammar is `/{site}/{section}/{subView}`, e.g. `http://localhost:5266/lu/furnace-health/lining-forecast`.
`{site}` is one of `lu`, `de`, `be`, `es`.

### Daily operations

| # | Screen | Route | Persona | Proves | Guide chapter |
|---|---|---|---|---|---|
| 1 | Command Center | `command-center/overview` | Marc Weber — Plant Manager | `OUT-01`, and triage entry to all others | [03](03-command-center-and-operations.md) |
| 2 | Operations | `operations/overview` | Marc Weber — Plant Manager | `CHL-01`…`CHL-04` (operational surface) | [03](03-command-center-and-operations.md) |
| 3 | Lining Forecast | `furnace-health/lining-forecast` | Elena Duarte / Tomás Rossi | `CHL-03`, `OBJ-02`, `OUT-03` | [04](04-furnace-health.md) |
| 4 | Thermal Explorer | `furnace-health/thermal-explorer` | Elena Duarte — Furnace Operator | `AI-01` | [04](04-furnace-health.md) |
| 5 | Maintenance Planner | `furnace-health/maintenance-planner` | Tomás Rossi — Maintenance Engineer | `OBJ-02`, `OUT-03` | [04](04-furnace-health.md) |
| 6 | Spot & Schedule | `energy-optimization/spot-price-schedule` | Sofia Lindqvist — Energy Manager | `CHL-01`, `OBJ-01`, `REG-02` (approval gate) | [05](05-energy-optimization.md) |
| 7 | Load-Shift Simulator | `energy-optimization/load-shift-simulator` | Sofia Lindqvist — Energy Manager | `AI-02` | [05](05-energy-optimization.md) |
| 8 | Batch Quality | `quality/batches` | Jens Bakker — Quality Engineer | `CHL-04`, `OBJ-03`, `OUT-04` | [06](06-quality.md) |
| 9 | Defect Analytics (SPC) | `quality/spc` | Jens Bakker — Quality Engineer | `OBJ-03` | [06](06-quality.md) |

### Insight & governance

| # | Screen | Route | Persona | Proves | Guide chapter |
|---|---|---|---|---|---|
| 10 | Executive Overview | `executive-overview/overview` | Isabelle Moreau — Executive | `OUT-01`…`OUT-04` (roll-up) | [09](09-executive-overview.md) |
| 11 | Board Report | `executive-overview/board-report` | Isabelle Moreau — Executive | `OUT-01`…`OUT-04` (reporting) | [09](09-executive-overview.md) |
| 12 | Emissions Ledger | `sustainability-compliance/emissions-ledger` | Amina Haddad — Sustainability Officer | `CHL-02`, `OUT-02` | [07](07-sustainability-and-compliance.md) |
| 13 | ETS Exposure | `sustainability-compliance/ets-exposure` | Amina Haddad — Sustainability Officer | `REG-03` | [07](07-sustainability-and-compliance.md) |
| 14 | Audit & Reports | `sustainability-compliance/audit` | Amina Haddad — Sustainability Officer | `REG-01`, `REG-02` | [07](07-sustainability-and-compliance.md) |
| 15 | Procedures | `knowledge-hub/procedures` | Pieter Claes — Knowledge Engineer | `CHL-05`, `AI-03` | [08](08-knowledge-hub.md) |
| 16 | Capture Status | `knowledge-hub/capture-status` | Pieter Claes — Knowledge Engineer | `OBJ-04`, `REG-01` | [08](08-knowledge-hub.md) |
| 17 | Dashboard Collections | `dashboards/collections` | All personas | Navigation / onboarding | [11](11-dashboard-collections.md) |
| 18 | Requirement Register | `proof-of-execution/requirements` | All personas | **All 19 IDs** | [12](12-proof-of-execution.md) |
| 19 | Use Case | `proof-of-execution/use-case` | All personas | The brief itself, rendered in-app | [12](12-proof-of-execution.md) |
| 20 | Technical Requirements | `technical-requirements/criteria` | All personas | The technical rubric, self-scored 56/60 | [12](12-proof-of-execution.md) |

### Platform & reference

| # | Screen | Route | Persona | Proves | Guide chapter |
|---|---|---|---|---|---|
| 21 | Device Fleet | `device-operations/fleet` | Rui Almeida — OT Systems Engineer | Data provenance for `AI-01` | [10](10-device-operations.md) |
| 22 | Sensor Explorer | `device-operations/sensors` | Rui Almeida — OT Systems Engineer | Data provenance for `AI-01` | [10](10-device-operations.md) |
| 23 | Simulator Control | `device-operations/simulator` | Rui Almeida — OT Systems Engineer | Determinism / reproducibility | [10](10-device-operations.md) |
| 24 | Fabric Capacity | `platform-ops/capacity` | Nils Andersen — Platform Ops | Cost control, role gating | [13](13-platform-ops.md) |
| 25 | Jobs & Pipelines | `platform-ops/jobs` | Nils Andersen — Platform Ops | Data-pipeline observability | [13](13-platform-ops.md) |
| 26 | Cost & Telemetry | `platform-ops/cost-telemetry` | Nils Andersen — Platform Ops | Run cost transparency | [13](13-platform-ops.md) |
| 27 | AxelorMetal — Home | `company-website/home` | Public site | Business narrative | [02](02-company-website.md) |
| 28 | AxelorMetal — Company | `company-website/company` | Public site | Business narrative | [02](02-company-website.md) |
| 29 | AxelorMetal — Products & Markets | `company-website/products` | Public site | Business narrative | [02](02-company-website.md) |
| 30 | AxelorMetal — Steel Knowledge | `company-website/steel-knowledge` | Public site | Newcomer on-ramp | [02](02-company-website.md) |
| 31 | AxelorMetal — Contact | `company-website/contact` | Public site | Business narrative | [02](02-company-website.md) |

---

## 4. Requirement → evidence matrix

The authoritative, machine-readable version of this table is
[`apps/analytics-mfe/src/proof/proofCatalog.ts`](../../../../../apps/analytics-mfe/src/proof/proofCatalog.ts).
The in-app **Proof of Execution** screen and
[`docs/presentation/proof_of_execution.md`](../../../proof_of_execution.md) are both
projections of that one file, so they cannot silently drift apart.

| ID | Requirement (short) | Status | Where the number comes from | Stated caveat |
|---|---|---|---|---|
| `REG-01` | GDPR: lawful, minimised, erasable operator data | Met | `services/knowledge-orchestrator/src/knowledge_orchestrator/erasure.py`, `pii.py`, `consent.py`; `POST /v1/privacy/erasure-requests` | Scheduled retention expiry is a runbook, not a running job |
| `REG-02` | EU AI Act: human oversight, no self-approval | Met | `state_graph.py` (gated `IN_REVIEW`), `tools.py` (forbidden-tool list), `prompt_defense.py`, `content_safety.py`, `infra/bicep/modules/alerts.bicep` | Annex III classification and model card are documentation, not code objects |
| `REG-03` | EU ETS accounting and reporting | **Partial** | `fabric/notebooks/ns-silver-to-gold.Notebook`; `GET /v1/sustainability/summary`, `/v1/sustainability/emissions` | Allowance benchmark (1.50 t/t steel) and allowance price are demo constants; CBAM not implemented |
| `CHL-01` | Energy = 35 % of cost, no real-time optimization | Met | `services/optimizer-worker` MILP (PuLP/CBC); `POST /v1/energy/schedules:simulate` | Fixture spot prices, not a live ENTSO-E feed |
| `CHL-02` | CO₂ under ETS penalty pressure | Met | Emissions ledger + gold-layer Scope 1/2 computation | Synthetic emission factors |
| `CHL-03` | Lining wear unpredictable, €8 M per failure | Met | `services/scoring-worker` regression over refractory thickness and heat flux, P10/P50/P90 + confidence | Synthetic thermal history |
| `CHL-04` | Quality inconsistency in automotive-grade steel | Met | Batch quality + genealogy + SPC screens | Predicted vs lab-measured clearly separated |
| `CHL-05` | Retiring operators, disappearing knowledge | Met | Knowledge orchestrator capture → review → publish pipeline | Speech-to-text runs against fixtures locally |
| `OBJ-01` | Reduce energy consumption | Met | Optimizer proposal + approval gate | Advisory only |
| `OBJ-02` | Predict equipment failures | Met | RUL forecast + work-order creation (`POST /v1/workorders`) | Work orders are synthetic; no CMMS integration |
| `OBJ-03` | Improve steel quality | Met | Batch quality, bounded what-if, SPC | Advisory only |
| `OBJ-04` | Capture and structure expertise | Met | Consent → interview → draft → review → publish | Consent-bound, human-approved |
| `OUT-01` | −14 % energy per ton | **Demo surrogate** | Command Center KPI card, labelled as *target* | Number derived from the synthetic dataset |
| `OUT-02` | −22 % CO₂ | **Demo surrogate** | Emissions Ledger, labelled as *target* | Number derived from the synthetic dataset |
| `OUT-03` | 21-day lining warning | **Met** | RUL P50 ≥ 21 days, pinned by `tests/e2e/test_local_demo_persona_journeys.py` | The mechanism and the 21-day horizon are real against synthetic input |
| `OUT-04` | +8 pts high-grade yield | **Demo surrogate** | Batch Quality, labelled as *target* | Number derived from the synthetic dataset |
| `AI-01` | Physics-informed ML on thermal signatures | Met | `services/scoring-worker` OLS regression over thermal features | Not a trained deep model; a transparent, explainable regression |
| `AI-02` | Energy dispatch optimization agent | Met | Named agent identity + tool allow-list + MILP + RUL hand-off | Proposes, never commits |
| `AI-03` | GenAI knowledge capture | Met | Grounded extraction + critic loop (`critic.py`) + hybrid retrieval with citation enforcement | Local fixture adapter when no Foundry endpoint is configured |

---

## 5. Evidence you can run yourself

| Claim | Command (from the repository root) |
|---|---|
| The front end behaves as documented | `npm run test:frontend` |
| The BFF API behaves as documented | `npm run test:bff` |
| The persona journeys close end to end | `pytest tests/e2e` |
| The Fabric capacity SKU allow-list is enforced in all four places | `pytest tests/infra/test_capacity_sku_allow_list.py` |
| The whole solution builds | `npm run build` |

Aggregate results are recorded in [`docs/validation-report.md`](../../../../validation-report.md)
and `artifacts/demo-validation/rehearsal-report.md`.

---

## 6. How to use this matrix in a defense

1. **Open the in-app register** (`/lu/proof-of-execution/requirements`) next to this page.
   Anything you claim here can be shown there, live, in one click.
2. **Never claim an outcome number as achieved.** Say: *"the mechanism runs; the −14 %
   is a target computed from the synthetic dataset, and the UI labels it as a target."*
   The catalog says the same thing, so a jury that greps the repository finds agreement,
   not a contradiction.
3. **Lead with `OUT-03`.** It is the one outcome marked **Met**: the 21-day lining
   warning is produced by a real regression and pinned by an automated test.
4. **Answer "where does this number come from?" with a path**, not an adjective.
   Column 4 of §4 gives you that path for every requirement.

---

◀ [15 · Glossary](15-glossary.md) · ▲ [Index](README.md) · [17 · How it works behind the screens](17-how-it-works-behind-the-screens.md) ▶
