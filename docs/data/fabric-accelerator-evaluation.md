# Evaluation — Reusing the Azure-Brain / Fabric-Brain Accelerator Output in NovaSteel

**Status**: analysis, no code changed
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

**Short answer: yes, and it closes a real gap — but as a *complement*, not a replacement.**
The two artefacts were generated from the same brief and landed on opposite halves of the
same architecture. NovaSteel built the **operational plane** (event contracts, medallion
notebooks, real-time KQL, personas, agents, portal). Azure-Brain built the **analytical
plane** (star schema, 24 months of seeded history, Direct Lake semantic model, Power BI
report, Data Agent). Neither one is complete without the other, and they barely overlap.

---

## 2. Method and confidence

| Claim | How it was established | Confidence |
|---|---|---|
| Azure-Brain solution is fully deployed | `project-config.json`: all 10 pipeline steps `completed`, real Fabric item GUIDs, live SQL analytics + KQL endpoints, semantic-model refresh success at `2026-07-29T08:29Z` | High — file evidence |
| Its workspace is **not reachable** by the current identity | `GET /v1/workspaces` as `frkim@microsoft.com` lists `novasteel-dev` and `NovaSteelV3-Demo` but **not** the Azure-Brain `NovaSteel` workspace; direct `GET` returns `InsufficientPrivileges`. Re-tested with the capacity **Active** to rule out the pause | High — tested twice |
| NovaSteel *does* have a live Fabric workspace | `NovaSteelV3-Demo` (`3d9c0b49-…`) on capacity `novasteelv3fabric` (`2cb31264-…`), 14 items enumerated via the Fabric REST API | High — API listing |
| NovaSteel's runtime never calls Fabric | `services.py` wires only `LocalCapacityAdapter` (`"simulated": True`) or `UnconfiguredArmCapacityAdapter`; the implemented `ArmCapacityAdapter` is **never selected** | High — code read |
| Lakehouse table contents on either side | **Not verified** — both capacities are Paused and I did not resume them to query Delta tables | Low — inferred |

Cost discipline observed: `novasteelfab` was resumed for ~10 minutes to test the permission
hypothesis and **returned to Paused / F2**. Both capacities are Paused as of this writing.

---

## 3. What Azure-Brain produced

Generated from `usecase.md`, deployed to workspace `NovaSteel` on capacity `novasteelfab`
(F2, Sweden Central, **same subscription `3377065c-…` and same tenant** as NovaSteel).

### 3.1 Data — 15 seeded CSVs, ~200 000 rows, 13.4 MB

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

### 3.2 Analytical layer

- Lakehouse `LH_NovaSteel` — 15 Delta tables (Kimball star, surrogate `_key` columns).
- Semantic model `SM_NovaSteel` — **Direct Lake**, 15 tables, 22 relationships,
  **45 documented DAX measures** (`artifacts/semantic_model/measures.md`).
- Report **NovaSteel Production Intelligence** — 5 pages, 55 visuals, pixel-specified:
  `ExecOverview` (13), `EnergyDispatch` (10), `FurnaceHealth` (10), `QualityYield` (10),
  `KnowledgeCapture` (12).
- **Data Agent** with authored instructions, few-shots and a **25-question evaluation set**
  with recorded results.
- **Eventhouse `EH_NovaSteel`** (4 KQL tables) + **Eventstream** + a KQL dashboard.

### 3.3 Outcome targets — identical to ours

Energy per ton **−14 %**, CO₂ **−22 %**, furnace warning **21 days**, high-grade yield
**+8 pts**, avoided failure cost **€8M/event**. These are the same numbers the NovaSteel
Proof-of-Execution page already claims, because both were derived from the same use case.
That is the single most valuable property of this accelerator: **it can turn our asserted
numbers into numbers a semantic model computes from rows.**

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
without resuming the capacity, any loaded data.**

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
| Data Agent / NL-to-data | ❌ | ✅ + 25-question eval | **take theirs** |
| Eventstream | ❌ | ✅ | take theirs |
| KQL database & queries | ✅ | ✅ | keep ours |
| Personas, portal, agents, MFE, audit ledger | ✅ | ❌ | keep ours |
| Capacity lifecycle + auto-pause + GUI start | ✅ (simulated) | ✅ (`capacity.py idle`) | keep ours, wire it |

Overlap is confined to two rows. **This is close to a clean join.**

---

## 6. Frictions and blockers

### 6.1 Blocker — workspace ownership (must be resolved by the user)

The Azure-Brain workspace is invisible to `frkim@microsoft.com` even with the capacity
Active, and its deployment log references `C:\work\20260728 - NovaGlass\Azure-Brain\NovateelFab`
— a different machine and probably a different login. **Nothing live can be reused until
either** (a) that identity adds `frkim@microsoft.com` as workspace Admin, **or** (b) the
accelerator is re-run under the current identity. Option (b) is cheap: the scripts are
idempotent, the generator is seeded, and re-running targets whatever workspace/capacity we
point it at — which is also how we would consolidate onto `novasteelv3fabric`.

### 6.2 Entity mismatch

| | NovaSteel | Azure-Brain |
|---|---|---|
| Sites | 4 — `NS-DEMO-LUX-01` Moselle Integrated Works, `NS-DEMO-DE-01` Saarbrücken, `NS-DEMO-BE-01` Liège Melt & Rolling Works, `NS-DEMO-ES-01` Asturias | 6 — `PL-LU-01` Esch-Belval, `PL-LU-02` Differdange, `PL-DE-01` Bremen, `PL-DE-02` Duisburg, `PL-BE-01` Ghent, `PL-ES-01` Bilbao |
| Furnaces | `LUX-BF-01`, `LUX-RHF-01`, `BE-EAF-01` | 14, e.g. `FN-LU-01-A` |
| Naming rule | `NS-DEMO-` prefix is **mandatory** (`docs/data/synthetic-data-and-simulators.md` §1) | not applied |

The accelerator's entities **violate our synthetic-data naming guardrail**. They must be
regenerated against our site catalogue, not adopted verbatim. This is a change to
`generators/generate_data.py` constants plus a regeneration run — hours, not days.

### 6.3 Schema-style mismatch

Azure-Brain is Kimball (`dim_`/`fact_`, surrogate keys). NovaSteel's
`contracts/data/gold.v1.json` declares 8 facts by **grain and keys only, with no column
lists** — deliberately flexible. So the gold contract can *absorb* the star schema by
adding column specs; it does not contradict it. The bronze/silver contracts are untouched
because the accelerator has no equivalent layer.

### 6.4 Narrative mismatch

`is_optimized` / 2025-08-01 has no equivalent in our fixture story, and our demo clock
rebasing logic (`DEMO_CLOCK_REBASE`, `demoClock.ts`) is built around a 24-hour pack. A
24-month history that already ends today does **not** need rebasing — which simplifies the
analytical path but means two different time regimes coexist. Acceptable if the split is
explicit: **operational screens = rebased 24 h fixtures (one shift, proven in detail);
analytical/board screens = 24-month Fabric history (the programme trend).**

### 6.5 Cost

Capacity is the entire bill and only bills while Active (~USD 263/month for F2 at 730 h;
OneLake storage bills while paused but is negligible at 13 MB). **Running two F2 capacities
is pure waste.** Consolidate on `novasteelv3fabric`, which the existing Logic App auto-pause
at 01:00 and the portal start button already target conceptually.

### 6.6 Honesty conventions

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
| E | **Wire the Data Agent** as a Copilot grounding source alongside AI Search | High — answers "why" from rows | M | Med (needs the eval set as a gate) |
| F | **Wire real capacity control** — select `ArmCapacityAdapter` in `services.py` against `novasteelv3fabric` | High — the GUI start/stop stops being simulated | S | Med (managed-identity RBAC, LRO handling) |
| G | Adopt their Eventstream | Low — our KQL path already works | S | Low |
| H | Adopt their workspace/capacity wholesale | Negative — second capacity, foreign identity, non-compliant names | — | High |

**Reject H.** Everything else is additive.

---

## 8. Recommendation

**Reuse the accelerator's *content* — generator, schema, measures, report layout, agent
instructions — and deploy it into NovaSteel's own workspace `NovaSteelV3-Demo` on capacity
`novasteelv3fabric`, under the current identity. Do not adopt its workspace, its capacity or
its entity names.**

Rationale: it supplies exactly the four artefacts our Fabric workspace lacks
(data, semantic model, report, data agent), it was generated from the same brief so the KPI
targets already agree, it is EU/Sweden Central like the rest of the estate, and it costs
nothing extra once consolidated onto one capacity. The only hard blocker — workspace
permissions — disappears entirely under this recommendation, because we redeploy rather
than inherit.

### Phased plan

| Phase | Work | Gate |
|---|---|---|
| 0 | Confirm with the user which identity ran Azure-Brain; decide consolidate-vs-share | user decision |
| 1 | Port the generator to `NS-DEMO-` sites/furnaces; commit CSV or parquet output under `fabric/seed/`; extend `gold.v1.json` with column specs | protected-feed scan, contract tests, checksum manifest |
| 2 | Load into `lh_novasteelv3_core` through `pl-novasteelv3-medallion`; run `v3-validate-data-quality` | data-quality notebook passes; capacity returns to Paused |
| 3 | Publish the semantic model with the 45 measures renamed to our vocabulary; **assert the model's KPI outputs equal the Proof-of-Execution claims** | numeric equality test — this is the whole point |
| 4 | Publish the 5-page report; embed it in `ExecutivePowerBi.tsx` behind the BFF token flow; add the synthetic-data banner | portal test + live check with capacity Active |
| 5 | Wire `ArmCapacityAdapter` for real start/pause; verify the 01:00 Logic App targets `novasteelv3fabric` | live start/pause via GUI |
| 6 | Data Agent as a Copilot grounding source, gated on its 25-question eval | eval pass rate recorded |

Phases 1–3 are the substance; phase 4 is the demo payoff; 5–6 are optional polish.

### Deck impact

This changes the honest answer to the FAQ *"is Fabric actually used, or just drawn?"* from
"provisioned and contract-defined" to "holds the data, computes the KPIs and renders the
board report." Worth a slide, and worth doing before the defence for that reason alone.

---

## 9. What must not be reused

- The `PL-LU-01` / `FN-LU-01-A` entity vocabulary — breaks the `NS-DEMO-` guardrail.
- The `novasteelfab` capacity — a second F2 doubles the only line item that bills.
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
