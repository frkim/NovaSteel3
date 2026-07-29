# Evaluation — Reusing the Azure-Brain / Fabric-Brain Accelerator Output in NovaSteel

**Status**: analysis, no code changed. **Revision 2** — access obtained, all findings
verified against the live Fabric workspace.
**Date**: 2026-07-29
**Rollback point**: everything below is written against `milestone/2026-07-29-pre-fabric-data`
(tag *and* branch, commit `4a1bac5`). No recommendation in this document requires
that milestone to be invalidated.
**Subject under evaluation**: `D:\work\20260729 - Azure-Brain\NovateelFab` — a Microsoft
Fabric solution generated and deployed by the Azure-Brain solution accelerator
(`fabric-brain` submodule) from the *same* source use case,
[`docs/usecase/usecase.md`](../usecase/usecase.md).

---

## 1. Question asked

> NovaSteel currently runs on synthetic fixtures. No data is stored in Fabric and no Fabric
> capability is involved. Can the Azure-Brain output be reused?

**Short answer: yes — verified live, and it closes a real gap, but as a *complement*, not a
replacement.** The two artefacts were generated from the same brief and landed on opposite
halves of the same architecture. NovaSteel built the **operational plane** (event contracts,
medallion notebooks, real-time KQL, personas, agents, portal). Azure-Brain built the
**analytical plane** (star schema, 24 months of seeded history, Direct Lake semantic model,
Power BI report, Data Agent). Neither one is complete without the other, and they barely
overlap.

Three of its four headline KPIs compute correctly from real rows today. The fourth — the
21-day furnace warning — does not, and the reason is a one-line defect (§3.4).

---

## 2. Method and confidence

Access was initially blocked, then obtained. The blocker was an **identity** issue with a
trivial cause: `frkim@microsoft.com` is a **guest** in tenant `9d94eb6e-…`, whereas
`frkim@MngEnvMCAP336722.onmicrosoft.com` is the **tenant-native** account that ran the
accelerator. Signing in as the native account makes the workspace visible immediately.
Everything below was then verified against the running service.

| Claim | How it was established | Confidence |
|---|---|---|
| Azure-Brain solution is fully deployed | 11 items enumerated live via the Fabric REST API; all 10 pipeline steps `completed` in `project-config.json` | **Verified** |
| Data is actually loaded | 15 managed Delta tables in `LH_NovaSteel`; DAX row counts match the source CSVs exactly (`fact_production` 62 424, `fact_energy_market` 105 120, `fact_quality_inspection` 21 748, `fact_furnace_health` 10 220, `fact_knowledge_capture` 306, `fact_emissions` 144) | **Verified** |
| Date window | `MIN(dim_date[date])` = 2024-08-01, `MAX` = 2026-07-31 | **Verified** |
| The semantic model computes the outcome KPIs | DAX `executeQueries` against `SM_NovaSteel` — see §3.4 | **Verified** |
| The report is published and embeddable | 5 pages returned by the Power BI REST API, live `embedUrl` bound to `SM_NovaSteel` | **Verified** |
| Eventhouse holds real-time data | KQL `union withsource=T *`: `FurnaceTelemetry` 210, `EnergyTick` 204, `QualityEvent` 200, `ProductionAlert` 200 | **Verified** |
| NovaSteel *does* have a live Fabric workspace | `NovaSteelV3-Demo` (`3d9c0b49-…`) on capacity `novasteelv3fabric`, 14 items | **Verified** |
| NovaSteel's runtime never calls Fabric | `services.py` wires only `LocalCapacityAdapter` (`"simulated": True`) or `UnconfiguredArmCapacityAdapter`; `ArmCapacityAdapter` is **never selected** | **Verified** — code read |

Cost discipline observed: `novasteelfab` was resumed only for the duration of the queries
above and **returned to Paused / F2**, confirmed by ARM. Both capacities are Paused as of
this writing. Total F2 runtime consumed across this investigation: well under an hour.

---

## 3. What Azure-Brain produced

Generated from `usecase.md`, deployed to workspace `NovaSteel` on capacity `novasteelfab`
(F2, Sweden Central, **same subscription `3377065c-…` and same tenant** as NovaSteel).

### 3.1 Data — 15 seeded CSVs, ~200 000 rows, 13.4 MB — **confirmed loaded into Delta**

| Dimension | Rows | Fact | Rows |
|---|---:|---|---:|
| `dim_date` | 730 | `fact_energy_market` | 105 120 |
| `dim_procedure` | 60 | `fact_production` | 62 424 |
| `dim_operator` | 40 | `fact_quality_inspection` | 21 748 |
| `dim_customer` | 18 | `fact_furnace_health` | 10 220 |
| `dim_furnace` | 14 | `fact_knowledge_capture` | 306 |
| `dim_product` | 12 | `fact_emissions` | 144 |
| `dim_plant` | 6 | | |
| `dim_energy_source` | 6 | | |
| `dim_shift` | 3 | | |

- Window **2024-08-01 → 2026-07-31** — 24 months ending *today*, deterministic seed.
- Carries an `is_optimized` flag with an **AI rollout boundary at 2025-08-01**, which is how
  the before/after deltas are computed rather than asserted.
- Produced by `generators/generate_data.py` — reproducible, no external dependency.

### 3.2 Analytical layer — live item inventory

Enumerated from workspace `ab6756eb-34fd-4bdf-8156-6a52e47ae2ec`:

| Type | Name | Id |
|---|---|---|
| Lakehouse (+SQLEndpoint) | `LH_NovaSteel` | `9f2adc94-…` |
| SemanticModel | `SM_NovaSteel` | `3e892a77-…` |
| Report | NovaSteel Production Intelligence | `f917389e-…` |
| DataAgent | NovaSteel Operations Agent | `b3017de5-…` |
| Eventhouse / KQLDatabase | `EH_NovaSteel` | `cbcc644e-…` / `3abc5927-…` |
| Eventstream | `ES_NovaSteel` | `394600e7-…` |
| KQLDashboard | NovaSteel Real-Time Operations | `b2bdeabf-…` |
| Notebook | `NB_Load_Bronze_To_Delta`, `NB_Scratch_Diagnostics` | — |

- Semantic model is **Direct Lake**, 15 tables, 22 relationships,
  **45 documented DAX measures** (`artifacts/semantic_model/measures.md`).
- Report is published with 5 pages and a live `embedUrl` bound to `SM_NovaSteel`:
  `ExecOverview`, `EnergyDispatch`, `FurnaceHealth`, `QualityYield`, `KnowledgeCapture`
  (55 visuals, pixel-specified).
- Eventhouse holds seeded real-time samples: `FurnaceTelemetry` 210, `EnergyTick` 204,
  `QualityEvent` 200, `ProductionAlert` 200.
- The config notes F2 throttles Direct Lake once CU carry-forward accumulates —
  **F4 for demos, F8 for Spark ETL, F2/Paused when idle**. Our capacity state machine
  already models exactly these three SKUs.

### 3.3 Outcome targets — identical to ours

Energy per ton **−14 %**, CO₂ **−22 %**, furnace warning **21 days**, high-grade yield
**+8 pts**, avoided failure cost **€8M/event**. These are the same numbers the NovaSteel
Proof-of-Execution page already claims, because both were derived from the same use case.
That is the single most valuable property of this accelerator: **it can turn our asserted
numbers into numbers a semantic model computes from rows.**

### 3.4 Live DAX verification — three of four claims reproduce, one does not

Executed against `SM_NovaSteel` via the Power BI `executeQueries` API, no filter context:

| Claim | Target | **Computed** | Verdict |
|---|---:|---:|---|
| Energy per ton reduction | 14 % | **14.49 %** | ✅ reproduces |
| CO₂ reduction | 22 % | **22.15 %** | ✅ reproduces |
| High-grade yield gain | +8 pts | **+8.06 pts** | ✅ reproduces |
| Furnace advance warning | 21 days | **20.0 days** | ❌ **does not reproduce** |

Supporting values: Tons Produced 11 847 274 · Energy Savings €40.3M · ETS Cost Avoided
€34.5M · Avoided Failure Cost €88M.

**The 21-day claim is an off-by-one in the generator, not a rounding artefact.**
`Early Warning Days` returns exactly `20.00` for **all 14 furnaces** — a constant, not an
average. The cause is the risk-band definition in `fact_furnace_health`:

| Band | `predicted_days_to_failure` range | Rows |
|---|---|---:|
| Critical | 0 – 6 | 24 |
| **High** | **7 – 20** | 294 |
| Watch | 21 – 59 | 585 |
| Healthy | 60 – 913 | 9 317 |

The measure reads the predicted days at the moment a furnace *first* enters `High`, and the
`High` band opens at 20. So the data can only ever produce 20 days, or 59 if `Watch` were
the alerting band. **Fix**: shift the boundary to `High = 8–21`. One constant in
`generators/generate_data.py`, after which the claim is reproducible from rows.

This single finding justifies the numeric-equality gate proposed in §8 — it was found in
the first five minutes of running it, and it is exactly the kind of number a defence panel
would ask to see derived.

### 3.5 Two further quality caveats

- **`Avoided Failure Cost` = €88M is not defensible as stated.** It is
  `(14 flagged − 3 actually failed) × €8M`, i.e. it assumes *every* furnace ever flagged
  High/Critical would otherwise have failed. NovaSteel's honesty conventions require the
  conservative framing (cost avoided *per prevented event*, with the counterfactual stated).
  This measure must be reworded or re-scoped before it appears in the defence.
- **The Data Agent's "25/25 = 100 %" is a DAX-execution score, not an accuracy score.**
  The rubric awards a pass when a DAX step runs and half the expected measures are named.
  The recorded transcript for question E09 passes while answering *"No data was found for
  Energy Savings EUR or Energy Reduction %"* — because the agent filtered
  `is_optimized = TRUE()`, which blanks the baseline half of those measures by design.
  **Wiring this agent into Copilot as-is would ship an assistant that denies our headline
  KPI.** It must be re-gated on answer correctness first.

### 3.6 Everything is reproducible from source on disk

`artifacts/` contains the complete definitions, not just deployment logs:
`semantic_model/model.bim` (114 KB TMSL) and `definition.pbism`, `report/report.json`
(143 KB) and `definition.pbir` plus its theme, `rti/kql_schema.kql`,
`data_agent/instructions.md` + `fewshots.md` + the published datasource config, and the
`build_*.py` / `validate_*.py` scripts for each.

**Consequence: reuse never requires access to their workspace.** The ownership question is
informative, not blocking — we can rebuild the whole analytical layer from these files into
our own workspace.

---

## 4. What NovaSteel already has

### 4.1 Deployed Fabric workspace `NovaSteelV3-Demo` (previously believed absent)

| Type | Items |
|---|---|
| Lakehouse (+SQL endpoint) | `lh_novasteelv3_landing`, `lh_novasteelv3_core` |
| Eventhouse / KQL DB | `evh-novasteelv3-operations`, `kql-novasteelv3-operations` |
| Notebook | `v3-initialize-lakehouses`, `v3-bronze-to-silver`, `v3-silver-to-gold`, `v3-deterministic-demo-scoring`, `v3-validate-data-quality` |
| Data pipeline | `pl-novasteelv3-medallion`, `pl-novasteelv3-demo-scoring` |

Deployed from `fabric/deployment-parameters/novasteelv3.parameters.json`. **Missing:
`SemanticModel`, `Report`, `Eventstream`, Data Agent — and, as far as can be determined
without resuming the capacity, any loaded data.** That is precisely the accelerator's
contribution.

Note the contrast worth keeping: our fixture pack's own `manifest.json` records
`lining_rul_p50_days: 21.0` — **our operational simulator does produce 21 days**. The
accelerator's analytical data produces 20 (§3.4). Aligning them is a prerequisite for a
coherent story, and the simulator is the one that is already correct.

### 4.2 Runtime

The BFF serves the checksum-protected fixture pack `services/bff-api/fixtures/demo-full`
— 9 NDJSON streams totalling **2 244 events over a single 24-hour window** (1.6 MB), in
schema-versioned envelopes carrying `data_classification`, `privacy_label`, `scenario_id`,
`seed` and `correlation_id`. Its `manifest.json` summary already encodes the demo's proof
points (`lining_rul_p50_days: 21.0`, `quality_predicted_yield_before/after: 0.88 → 0.95`,
`energy_baseline_cost_eur` vs `energy_optimized_cost_eur`, `energy_hard_constraint_violations: 0`).

That pack proves **one shift**. It cannot prove a **programme** — a 24-month
`−14 % / −22 % / +8 pts` trend has no rows behind it anywhere in the repo today.

`ExecutivePowerBi.tsx` renders a **capacity-aware placeholder** where the board report
should be. `/v1/platform/capacity` is simulated.

**So the "Fabric is the central core component" claim is currently architectural, not
executed.** That is precisely the gap the accelerator fills.

---

## 5. Gap analysis — the complementarity

| Layer | NovaSteel | Azure-Brain | Verdict |
|---|---|---|---|
| Event contracts, provenance, governance labels | ✅ strong | ❌ none | keep ours |
| Medallion bronze→silver→gold notebooks | ✅ | ❌ (single-hop load) | keep ours |
| Seeded historical data at analytical grain | ❌ 24 h only | ✅ 24 months | **take theirs** |
| Star schema + relationships | ❌ (gold contract is grain+keys only) | ✅ | **take theirs, renamed** |
| DAX / semantic model | ❌ logic re-implemented in Python + TS | ✅ 45 measures | **take theirs** |
| Power BI report | ❌ placeholder in portal | ✅ 5 pages | **take theirs** |
| Data Agent / NL-to-data | ❌ | ⚠️ present, but eval measures DAX execution not accuracy (§3.5) | take theirs, re-gate |
| Eventstream | ❌ | ✅ | take theirs |
| KQL database & queries | ✅ | ✅ | keep ours |
| Personas, portal, agents, MFE, audit ledger | ✅ | ❌ | keep ours |
| Capacity lifecycle + auto-pause + GUI start | ✅ (simulated) | ✅ (`capacity.py idle`) | keep ours, wire it |

Overlap is confined to two rows. **This is close to a clean join.**

---

## 6. Frictions and blockers

### 6.1 Workspace ownership — **resolved, not a blocker**

The workspace was invisible to `frkim@microsoft.com` because that account is a **guest** in
tenant `9d94eb6e-…`. The accelerator ran as `frkim@MngEnvMCAP336722.onmicrosoft.com`, the
**tenant-native** account for the same person, which sees the workspace immediately:

```powershell
az login --tenant MngEnvMCAP336722.onmicrosoft.com --use-device-code
```

Both accounts map to the same subscription `3377065c-…` ("Contoso Fx"). Use the native
account for all Fabric work; the guest account is fine for ARM.

Even without this, §3.6 shows the full definitions are on disk, so nothing depends on
inheriting their workspace.

### 6.2 Data-residency check to run before the defence

The report's `embedUrl` resolves through cluster `WABI-WEST-US3-A-PRIMARY`, i.e. the
**Power BI tenant home region is West US 3** while the capacity is Sweden Central. Fabric
content on a capacity is stored and processed in the capacity region, so this is very
likely a routing artefact rather than a residency breach — but for a GDPR-framed defence
the tenant home region versus capacity region distinction **must be checked and stated
explicitly**, not assumed. It is a predictable FAQ question.

### 6.3 Entity mismatch

| | NovaSteel | Azure-Brain |
|---|---|---|
| Sites | 4 — `NS-DEMO-LUX-01` Moselle Integrated Works, `NS-DEMO-DE-01` Saarbrücken, `NS-DEMO-BE-01` Liège Melt & Rolling Works, `NS-DEMO-ES-01` Asturias | 6 — `PL-LU-01` Esch-Belval, `PL-LU-02` Differdange, `PL-DE-01` Bremen, `PL-DE-02` Duisburg, `PL-BE-01` Ghent, `PL-ES-01` Bilbao |
| Furnaces | `LUX-BF-01`, `LUX-RHF-01`, `BE-EAF-01` | 14, e.g. `FN-LU-01-A` |
| Naming rule | `NS-DEMO-` prefix is **mandatory** (`docs/data/synthetic-data-and-simulators.md` §1) | not applied |

The accelerator's entities **violate our synthetic-data naming guardrail**. They must be
regenerated against our site catalogue, not adopted verbatim. This is a change to
`generators/generate_data.py` constants plus a regeneration run — hours, not days.

### 6.4 Schema-style mismatch

Azure-Brain is Kimball (`dim_`/`fact_`, surrogate keys). NovaSteel's
`contracts/data/gold.v1.json` declares 8 facts by **grain and keys only, with no column
lists** — deliberately flexible. So the gold contract can *absorb* the star schema by
adding column specs; it does not contradict it. The bronze/silver contracts are untouched
because the accelerator has no equivalent layer.

### 6.5 Narrative mismatch

`is_optimized` / 2025-08-01 has no equivalent in our fixture story, and our demo clock
rebasing logic (`DEMO_CLOCK_REBASE`, `demoClock.ts`) is built around a 24-hour pack. A
24-month history that already ends today does **not** need rebasing — which simplifies the
analytical path but means two different time regimes coexist. Acceptable if the split is
explicit: **operational screens = rebased 24 h fixtures (one shift, proven in detail);
analytical/board screens = 24-month Fabric history (the programme trend).**

### 6.6 Cost

Capacity is the entire bill and only bills while Active (~USD 263/month for F2 at 730 h;
OneLake storage bills while paused but is negligible at 13 MB). **Running two F2 capacities
is pure waste.** Consolidate on `novasteelv3fabric`, which the existing Logic App auto-pause
at 01:00 and the portal start button already target conceptually.

### 6.7 Honesty conventions

Our rules — advisory-only, zero unsupportable claims, visible synthetic banner, dual-%
reporting — must be carried into the Power BI report and the Data Agent instructions.
The report as generated has a brand slot but no synthetic-data banner.

---

## 7. Reuse options

| # | Option | Value | Effort | Risk |
|---|---|---|---|---|
| A | **Adopt the generator** — port `generate_data.py` to our site catalogue and `NS-DEMO-` naming; emit 24 months at gold grain | High — turns asserted KPIs into computed ones | M | Low (offline, deterministic) |
| B | **Adopt the star schema** into `contracts/data/gold.v1.json` column specs and load it into `lh_novasteelv3_core` via the existing medallion pipeline | High — makes Fabric actually hold NovaSteel data | M | Low |
| C | **Adopt the semantic model** — rebuild `SM_NovaSteel` (Direct Lake, 45 measures) over our lakehouse | High — one authoritative measure definition instead of Python+TS duplicates | M | Med (measure/UI drift) |
| D | **Embed the report** in `ExecutivePowerBi.tsx`, replacing the placeholder | **Highest demo value per hour** | S | Low |
| E | **Wire the Data Agent** as a Copilot grounding source alongside AI Search | High — answers "why" from rows | M | **High** — its eval scores DAX execution, not accuracy (§3.5); must be re-gated first |
| F | **Wire real capacity control** — select `ArmCapacityAdapter` in `services.py` against `novasteelv3fabric` | High — the GUI start/stop stops being simulated | S | Med (managed-identity RBAC, LRO handling) |
| G | Adopt their Eventstream | Low — our KQL path already works | S | Low |
| H | Adopt their workspace/capacity wholesale | Negative — second capacity, non-compliant entity names | — | High |

**Reject H.** Everything else is additive.

---

## 8. Recommendation

**Reuse the accelerator's *content* — generator, schema, measures, report definition, agent
instructions, all of which are on disk (§3.6) — and deploy it into NovaSteel's own workspace
`NovaSteelV3-Demo` on capacity `novasteelv3fabric`, signed in as
`frkim@MngEnvMCAP336722.onmicrosoft.com`. Do not adopt their workspace, their capacity or
their entity names.**

Rationale: it supplies exactly the four artefacts our Fabric workspace lacks (data, semantic
model, report, data agent); it was generated from the same brief, and three of its four
headline KPIs **verifiably compute** to our targets from real rows (§3.4); it is
EU/Sweden Central like the rest of the estate; and it costs nothing extra once consolidated
onto one capacity. The ownership question turned out to be a guest-vs-native account
artefact and is not a blocker.

Two defects must be fixed on the way in, both found by simply running the numbers:
the **20-vs-21-day band boundary** (§3.4) and the **€88M avoided-cost framing** (§3.5).
Neither is hard; both would have been embarrassing in the FAQ.

### Phased plan

| Phase | Work | Gate |
|---|---|---|
| 0 | ~~Identify the owning identity~~ **done** — use the tenant-native account; decide consolidate-vs-share capacity | user decision |
| 1 | Port the generator to `NS-DEMO-` sites/furnaces; **fix the High band to 8–21 days**; commit output under `fabric/seed/`; extend `gold.v1.json` with column specs | protected-feed scan, contract tests, checksum manifest |
| 2 | Load into `lh_novasteelv3_core` through `pl-novasteelv3-medallion`; run `v3-validate-data-quality` | data-quality notebook passes; capacity returns to Paused |
| 3 | Publish the semantic model with the 45 measures renamed to our vocabulary; rework `Avoided Failure Cost` to the conservative framing; **assert the model's KPI outputs equal the Proof-of-Execution claims, including 21 days** | numeric equality test — this is the whole point, and it has already caught two defects |
| 4 | Publish the 5-page report; embed it in `ExecutivePowerBi.tsx` behind the BFF token flow; add the synthetic-data banner; confirm tenant-vs-capacity region (§6.2) | portal test + live check with capacity Active |
| 5 | Wire `ArmCapacityAdapter` for real start/pause; verify the 01:00 Logic App targets `novasteelv3fabric` | live start/pause via GUI |
| 6 | Data Agent as a Copilot grounding source — **only after re-gating the eval on answer correctness rather than DAX execution** | new pass rate recorded against the corrected rubric |

Phases 1–3 are the substance; phase 4 is the demo payoff; 5 is high value for low effort;
6 should be deferred unless its rubric is fixed.

### Deck impact

This changes the honest answer to the FAQ *"is Fabric actually used, or just drawn?"* from
"provisioned and contract-defined" to "holds the data, computes the KPIs and renders the
board report" — with a live DAX result to show. Worth a slide, and worth doing before the
defence for that reason alone.

---

## 9. What must not be reused

- The `PL-LU-01` / `FN-LU-01-A` entity vocabulary — breaks the `NS-DEMO-` guardrail.
- The `novasteelfab` capacity — a second F2 doubles the only line item that bills.
- The **`High` risk band as generated** (7–20 days) — it makes the 21-day claim unprovable.
- The **`Avoided Failure Cost` measure as written** — assumes every flagged furnace would
  have failed; not defensible under our honesty conventions.
- The **Data Agent evaluation rubric** — it scores DAX execution, not answer accuracy, and
  passes a transcript that denies our own headline KPI.
- Any claim computed from their data before phase 3's numeric-equality gate passes.
- Public package registries: the accelerator's scripts must be checked against
  `docs/tech/security_requirement.md` before any of them is run from this repo.

## 10. Rollback

No phase requires rewriting history. If the data work goes wrong:

```powershell
git checkout milestone/2026-07-29-pre-fabric-data
```

The deployed images at that milestone are recorded in the tag message. The Fabric side is
reversible independently: drop the Delta tables and republish, or delete the semantic model
and report — the portal falls back to the existing placeholder.
