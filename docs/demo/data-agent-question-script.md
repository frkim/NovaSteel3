# NovaSteel Data Agent — Presenter Question Script

## 1. Purpose and scope

This document is a presenter-facing script for the **Fabric Data Agent `da-novasteelv3`** live chat
session in the NovaSteel V3 demonstration. It provides verbatim questions, expected answers, backing
data sources, and presenter commentary for the agent portion of the demo.

**How this document differs from `docs/demo/demo-runbook.md`:** The runbook orchestrates the web
application — its eight browser tabs, persona transitions, minute-by-minute timing, and cue sheet
are all about driving the NovaSteel front-end screens. This document is exclusively about the
**Data Agent chat window**. Open the runbook for tab management and application-level timing; open
this document when you want to ask the agent a live, conversational question. Cross-reference:
`demo-runbook.md` §4 covers the minute-by-minute script for the application; the agent questions
here are a complement, not a substitute.

**Who reads this:** Presenters driving a live or rehearsed demo, SE/pre-sales engineers who want to
add or swap questions, and technical reviewers verifying that every question traces back to a stated
business requirement.

Every question in this document maps to one or more of the five business challenges, four expected
outcomes, or three AI infusion points defined in `docs/usecase/usecase.md`. The mapping is made
explicit in section 4.

All data in the platform is synthetic (`data_classification = 'SYNTHETIC'`, plant IDs follow the
`NS-DEMO-*` convention). State this to the audience before the first question and repeat it whenever
quoting a number.

---

## 2. Preflight

### 2.1 Before the demo session

1. **Resume the Fabric capacity.** Workspace `NovaSteelV3-Demo` runs on a capacity that is
   normally **paused** to control cost. Resume it in the Fabric Admin portal and confirm the status
   is `Active` before proceeding.
2. **Refresh the semantic model.** In the Fabric workspace, trigger a manual refresh of the semantic
   model backed by `lh_novasteelv3_core`. The Data Agent queries the lakehouse SQL endpoint directly
   and does not require the semantic model for its own answers, but other tabs in the demo do.
3. **Verify the ontology GraphModel.** Open `onto_novasteelv3` in the workspace and confirm the
   GraphModel status is current. If the GraphModel has not been deployed or has drifted, GQL queries
   return access errors rather than data — which is indistinguishable from a syntax error during
   the demo.
4. **Open the Data Agent chat.** Navigate to `da-novasteelv3` in workspace `NovaSteelV3-Demo` and
   start a new conversation.

### 2.2 Warm-up question

The first query in a new Data Agent session incurs a cold-start delay of 10–30 seconds while the
agent initialises its three data source connections. **Send a warm-up question before the audience
arrives** so the latency does not land on the first live question.

Suggested warm-up:

> `How many data sources do you have access to, and what are their names?`

The agent answers this from its own configuration without issuing a live data query, so the response
is fast. Discard the warm-up turn and start a fresh conversation before the demo begins.

---

## 3. The 10-minute happy path

The eight questions below tell a coherent story from business framing to AI outcome. Present them in
order. Where the audience is engaged, ask the follow-up; otherwise move on.

Remind the audience that all figures are **synthetic demo data** before the first question.

> **Date window — read before asking any gold-fact question**
>
> The demo gold history runs from **2024-08-08 to 2026-07-29** (confirmed from the live lakehouse
> SQL endpoint). The real-world date is 2026-08-02, creating a four-day gap. The effect is
> significant:
>
> - **"In July 2026"** and **"last month"** return a full month of gold-fact data — use these for
>   every trend and KPI question.
> - **"Today", "this week", "this month" (August 2026), and "in the last 7 days"** return nothing or
>   at most one day from the gold fact tables. An ad-libbed "how are we doing today?" will produce an
>   empty result that looks like a platform failure to the audience.
> - **Live/real-time questions are different.** Questions such as "what alarms are active right now"
>   or "show me the latest sensor readings" route to the KQL database `kql-ns-operations`, which is
>   populated by the live event stream and is not subject to the gold-history cut-off. Freely ask
>   real-time questions against KQL; always bound analytic and KPI questions to July 2026.
> - **`fact_knowledge_procedure` has no useful date filter.** Its 10 rows span published dates from
>   2025-02-04 to 2026-01-30. Ask knowledge-procedure questions without any time window — adding a
>   recent date filter will return zero rows.
>
> Every verbatim question in this document is phrased to land inside the confirmed data window.

---

### Q1 — Frame the programme targets

| Field | Detail |
|---|---|
| **Question to type** | `What are NovaSteel's four programme KPI targets? Show me the baseline and target value for each.` |
| **Expected data source** | Lakehouse `lh_novasteelv3_core` |
| **Backing table / columns** | `dim_kpi_target`: `kpi_id`, `baseline_value`, `target_value`, `unit` |
| **What a good answer looks like** | A seven-row table. The four programme KPIs: KPI-ENE-01 (baseline 19.5 → target 16.77 GJ/t, decrease), KPI-CO2-01 (2.10 → 1.638 tCO2e/t, decrease), KPI-FUR-01 (target 21.0 days, minimum), KPI-QUA-01 (0.90 → 0.972 ratio, increase). Three adoption/governance KPIs with null baselines: KPI-ENE-03 (target 0.70), KPI-ADO-01 (0.80), KPI-GOV-01 (1.00). |
| **Follow-up** | `Which KPI has the largest relative improvement target?` |

**Presenter note:** This question anchors the entire demo. `dim_kpi_target` is not time-sensitive —
no date filter is required and the question works regardless of the gold-history gap. The table
contains seven confirmed rows; the four programme KPIs are KPI-ENE-01, KPI-CO2-01, KPI-FUR-01, and
KPI-QUA-01. The remaining three (KPI-ENE-03, KPI-ADO-01, KPI-GOV-01) have null baselines and are
adoption/governance targets — they will appear in the results, so be ready to explain them briefly
if asked. Point out the units and direction: energy and CO₂ decrease; furnace warning lead-time and
quality yield ratio increase.

---

### Q2 — Energy performance in July 2026

| Field | Detail |
|---|---|
| **Question to type** | `What is the average energy intensity in GJ per tonne in July 2026 across all plants, and how does it compare to the 19.5 GJ/t baseline?` |
| **Expected data source** | Lakehouse `lh_novasteelv3_core` |
| **Backing table / columns** | `fact_energy_daily`: `date_key`, `plant_id`, `energy_gj`, `crude_steel_tons`, `baseline_energy_gj` |
| **What a good answer looks like** | Energy intensity of **10.63 GJ/t** for July 2026 — well below both the 19.5 GJ/t baseline and the 16.77 GJ/t target. Total energy cost approximately EUR 46.5M against a EUR 54.1M baseline (approximately 14% below baseline cost). Programme KPI-ENE-01 is met. |
| **Follow-up** | `Which plant shows the largest gap from the 19.5 GJ/t baseline in July 2026?` |

**Presenter note:** The agent computes energy intensity on the fly from `energy_gj` divided by
`crude_steel_tons`. The July 2026 result of 10.63 GJ/t has already exceeded the programme target —
it is not "approaching" the target, it is past it. If the audience asks "how close are we?", the
answer is that KPI-ENE-01 is met and the operation is running approximately 45% below the original
baseline. Frame this as programme success. Both `baseline_energy_gj` (per-row) and
`dim_kpi_target.baseline_value` are valid comparison points. The confirmed row count is 2,884 rows
spanning 2024-08-08 to 2026-07-29. Use "in July 2026" — do not substitute "this month" or "today".

---

### Q3 — Emissions and ETS exposure

| Field | Detail |
|---|---|
| **Question to type** | `What is our CO₂ intensity in tCO₂e per tonne in July 2026, and what is the total ETS financial exposure for that month?` |
| **Expected data source** | Lakehouse `lh_novasteelv3_core` |
| **Backing table / columns** | `fact_emissions_daily`: `date_key`, `plant_id`, `total_co2e_t`, `crude_steel_tons`, `ets_exposure_eur` |
| **What a good answer looks like** | CO₂ intensity of **1.019 tCO2e/t** for July 2026 — below the 1.638 tCO2e/t target and well below the 2.10 baseline. Programme KPI-CO2-01 is met. ETS financial exposure for the month: EUR 3,974,153. Scope 1: 355,336 t CO2e; Scope 2: 147,868 t CO2e. |
| **Follow-up** | `Break that down by scope 1 and scope 2 emissions.` |

**Presenter note:** The July 2026 result of 1.019 tCO2e/t is already below the programme target —
KPI-CO2-01 is met, not just tracked. `ets_exposure_eur` is a pre-computed column (price × excess
over free allocation). Scope 1 and scope 2 breakdowns come from `scope1_co2e_t` and `scope2_co2e_t`,
both in the same table. `free_allocation_t` and `ets_allowance_price_eur_per_t` are also available
if the audience asks how the exposure figure was derived.

---

### Q4 — Furnace alert episodes in June and July 2026

| Field | Detail |
|---|---|
| **Question to type** | `Which furnace assets went into alert during June and July 2026, and how many days of advance warning did we get before the predicted failure date?` |
| **Expected data source** | Lakehouse `lh_novasteelv3_core` |
| **Backing table / columns** | `fact_furnace_rul`: `asset_id`, `plant_id`, `scored_date`, `alert_issued_at`, `rul_days_p50`, `predicted_failure_date`, `risk_score` |
| **What a good answer looks like** | Two alert episodes. BE-EAF-01 (NS-DEMO-BE-01): alert first issued 2026-06-19 with `rul_days_p50` = 21.0, `predicted_failure_date` = 2026-07-10. LUX-RHF-01 (NS-DEMO-LUX-01): alert first issued 2026-06-09 with `rul_days_p50` = 21.0, `predicted_failure_date` = 2026-06-30. Both issued exactly 21 days of advance warning — KPI-FUR-01 demonstrably met. |
| **Follow-up** | `Was the unplanned_outage_flag set on any of those rows?` |

**Presenter note:** This is the single strongest business moment in the Data Agent demo. The alert
fires the day `rul_days_p50` first reaches 21.0, which is exactly the KPI minimum. After each
predicted failure date, the asset reappears with a high RUL (BE-EAF-01 resets to ~209 days on
2026-07-11; LUX-RHF-01 resets similarly after its reline), proving the planned reline was executed
on schedule. `unplanned_outage_flag` is **False on every row of every episode** — no catastrophic
failure occurred. This is the synthetic evidence that the prediction system converted what would
have been EUR 8M unplanned failures into planned maintenance events. Say this explicitly:

> "The warning fires at exactly 21 days — the KPI minimum. We can see from the post-reline row that
> the failure date was met with a planned reline, not an emergency shutdown. The unplanned outage
> flag is false across the entire episode. That is a EUR 8M avoided-cost event, per the use case,
> demonstrated in the data."

Do not ask about "the current state at the end of July" for this KPI — on 2026-07-29 all three
scored assets are healthy (RUL 191, 468, and 271 days respectively), which is the consequence of
having acted on those alerts. The alert episode is the proof of the prediction capability; the
current healthy state is the result. Both stories are true; this question tells the better one.

Other confirmed alert episodes in the history (first alert date → predicted failure date, all with
`rul_days_p50` = 21.0 at first alert): BE-EAF-01 2024-09-27→2024-10-18; LUX-RHF-01
2024-10-17→2024-11-07; LUX-BF-01 2024-11-03→2024-11-24; BE-EAF-01 2025-04-25→2025-05-16;
LUX-RHF-01 2025-08-13→2025-09-03; BE-EAF-01 2025-11-21→2025-12-12; LUX-BF-01
2026-04-27→2026-05-18; LUX-RHF-01 2026-06-09→2026-06-30. If BE-EAF-01 is stale by a later demo
date, ask about any of these episodes by name.

---

### Q5 — Furnace degradation trajectory: BE-EAF-01

| Field | Detail |
|---|---|
| **Question to type** | `Show me how the remaining useful life and risk score for BE-EAF-01 changed between 2026-06-19 and 2026-07-09.` |
| **Expected data source** | Lakehouse `lh_novasteelv3_core` |
| **Backing table / columns** | `fact_furnace_rul`: `asset_id`, `scored_date`, `rul_days_p50`, `rul_days_p10`, `rul_days_p90`, `risk_score`, `confidence`, `predicted_failure_date` |
| **What a good answer looks like** | A monotonic degradation: `rul_days_p50` falling from 21.0 on 2026-06-19 to 1.0 on 2026-07-09; `risk_score` rising from 0.800 to 0.990; `confidence` rising from 0.904 to 0.948; `predicted_failure_date` fixed at 2026-07-10 throughout. On 2026-07-11 the asset resets to `rul_days_p50` ≈ 209 days and `risk_score` = 0.02 — the planned reline executed on schedule. |
| **Follow-up** | `What are the P10 and P90 bounds on 2026-07-09, the last day before the reline?` |

**Presenter note:** The follow-up answer on 2026-07-09 is p10 = 0.8 days, p50 = 1.0 day,
p90 = 1.3 days — a very tight band communicating near-certainty. This demonstrates the
physics-informed model (AI infusion point 1) improving its estimate as more thermal data
accumulates: compare the wider band on 2026-06-19 (the alert day, 21 days out) to the tight
band 21 days later (one day out). The progression from wide to narrow uncertainty is a visual the
audience can follow without a steel background.

Explicitly distinguish P50 from a measured outcome — say "the model estimates" rather than "the
measurement shows". The reset on 2026-07-11 to ~209 days is the key proof point: `predicted_failure_date`
was 2026-07-10, and the high RUL on the following day confirms the planned reline happened exactly
as predicted. `unplanned_outage_flag` is False on every row.

---

### Q6 — Quality yield for high-grade steel in July 2026

| Field | Detail |
|---|---|
| **Question to type** | `How does the first-pass yield for high-grade steel in July 2026 compare to the 90% baseline? Show results by plant.` |
| **Expected data source** | Lakehouse `lh_novasteelv3_core` |
| **Backing table / columns** | `fact_quality_yield`: `date_key`, `plant_id`, `high_grade_flag`, `first_pass_good_tons`, `attempted_tons` |
| **What a good answer looks like** | High-grade first-pass yield of **0.9494** for July 2026, broken down by plant. Above the 0.90 baseline but short of the 0.972 target by approximately 2.3 percentage points — KPI-QUA-01 is not yet met. Quality losses in July: downgrade 4,498 t, rework 8,996 t, scrap 1,499 t, defect count 464. |
| **Follow-up** | `Which grade code has the most downgrade tons in July 2026?` |

**Presenter note:** The July 2026 yield of 0.9494 is the one amber KPI in the scorecard (see section
4.5). This is deliberate — a demo where every number is green reads as a mock-up. The 2.3-point gap
to the 0.972 target is a natural opening: it gives the audience something to probe and lets the
presenter bridge into the knowledge-capture story (Q7) and the retiring-operator use case. Lead into
it rather than being caught out by it:

> "Three of our four programme targets are met in July. Quality is the one still in progress — this
> is where the GenAI knowledge-capture system becomes the next intervention."

`downgrade_tons` and `scrap_tons` are in the same table if the follow-up is asked. `grade_code`
identifies the steel grade when the agent filters by `high_grade_flag`.

---

### Q7 — Knowledge procedure governance

| Field | Detail |
|---|---|
| **Question to type** | `How many knowledge procedures have been approved, and what is the average number of source citations per approved procedure?` |
| **Expected data source** | Lakehouse `lh_novasteelv3_core` |
| **Backing table / columns** | `fact_knowledge_procedure`: `procedure_id`, `approved_flag`, `review_status`, `source_citation_count`, `equipment_id` |
| **What a good answer looks like** | Count of rows where `approved_flag = TRUE` (up to 10 total rows in the demo load), average `source_citation_count`. |
| **Follow-up** | `Show the procedures linked to furnace equipment.` |

**Presenter note:** The table contains exactly 10 rows with `published_date` values between
2025-02-04 and 2026-01-30. Do not add a date filter to this question — the table is small enough
to query in full and a recent-date filter will return zero rows. The small size is deliberate: the
point is governance chain-of-custody from operator transcript to structured procedure, not
throughput. The `equipment_id` column links a procedure to a specific asset.

---

### Q8 — Ontology: the process chain

| Field | Detail |
|---|---|
| **Question to type** | `What does a blast furnace feed, and how does the process chain continue all the way to the continuous caster?` |
| **Expected data source** | Graph `onto_novasteelv3` (GQL) |
| **GQL used by agent** | `MATCH p = (a:EquipmentClass {ClassId:'BlastFurnace'})-[:feeds*1..3]->(c:EquipmentClass {ClassId:'ContinuousCaster'}) RETURN p` |
| **What a good answer looks like** | BlastFurnace → BasicOxygenFurnace → ContinuousCaster, with metallurgical commentary for each step. |
| **Follow-up** | `Which actual assets in our fleet are blast furnaces?` |

**Presenter note:** This is the gateway to the ontology showcase. The agent must not say "a blast
furnace feeds the caster directly" — the metallurgically correct two-hop path goes via the BOF. See
section 7.2 for why this is a deliberate teaching point worth calling out to the audience.

---

## 4. Question bank by use-case section

Use these questions to extend or swap into the happy path depending on the audience and available
time. All column names are verified against `fabric/lakehouse/sql/20_gold.sql` unless explicitly
noted. Column names for `dim_plant` and `dim_calendar` are not in that file — those tables are not
cited in this section.

### 4.1 Business challenges

| `usecase.md` challenge | Question to ask | Data source | Backing table / key columns |
|---|---|---|---|
| Energy costs are 35% of production cost with no real-time optimization | `What cost saving has the dispatch optimization agent generated in July 2026 — show expected versus realized savings.` | Lakehouse | `fact_dispatch_recommendation`: `recommendation_date`, `plant_id`, `expected_cost_avoidance_eur`, `realized_cost_avoidance_eur`, `status` |
| CO₂ under EU ETS pressure | `What is the cumulative ETS financial exposure for 2026 through July, and what free allowances remain?` | Lakehouse | `fact_emissions_daily`: `date_key`, `plant_id`, `total_co2e_t`, `free_allocation_t`, `ets_allowance_price_eur_per_t`, `ets_exposure_eur` |
| Furnace lining wear — catastrophic failure costs €8M | `For furnace asset alert episodes since May 2026, how many resulted in an unplanned outage — show the unplanned_outage_flag for each episode.` | Lakehouse | `fact_furnace_rul`: `scored_date`, `plant_id`, `asset_id`, `component_id`, `alert_issued_at`, `unplanned_outage_flag` |
| Quality consistency issues in high-grade steel for automotive | `What is the defect count per 1,000 tonnes for high-grade steel in July 2026, broken down by plant?` | Lakehouse | `fact_quality_yield`: `date_key`, `plant_id`, `high_grade_flag`, `defect_count`, `attempted_tons` |
| Skilled operators retiring, knowledge disappearing | `How many knowledge procedures are still in draft or pending review — what is the review backlog?` | Lakehouse | `fact_knowledge_procedure`: `procedure_id`, `review_status`, `approved_flag`, `published_date` |

### 4.2 Transformation objectives

| `usecase.md` objective | Question to ask | Data source | Backing table / key columns |
|---|---|---|---|
| Reduce energy consumption | `Show me the month-over-month energy cost trend comparing June 2026 to July 2026 versus the baseline, across all plants.` | Lakehouse | `fact_energy_daily`: `date_key`, `plant_id`, `energy_cost_eur`, `baseline_cost_eur` |
| Predict equipment failures before they occur | `For all furnace assets, what is the average model confidence of the latest RUL inference as of July 2026?` | Lakehouse | `fact_furnace_rul`: `asset_id`, `scored_date`, `confidence`, `model_version` |
| Improve steel quality | `What fraction of total production tonnage in July 2026 is first-pass good versus rework versus scrap?` | Lakehouse | `fact_quality_yield`: `date_key`, `plant_id`, `first_pass_good_tons`, `rework_tons`, `scrap_tons`, `attempted_tons` |
| Capture and structure operational expertise before it is lost | `Which knowledge procedures cite more than three sources, and what equipment do they cover?` | Lakehouse | `fact_knowledge_procedure`: `procedure_id`, `equipment_id`, `source_citation_count`, `approved_flag` |

### 4.3 Expected outcomes

| `usecase.md` outcome | Question to ask | Data source | Backing table / key columns |
|---|---|---|---|
| Energy consumption per ton reduced by 14% (KPI-ENE-01, 19.5 → 16.77 GJ/t) | `Show the KPI target for energy intensity and how close we came to the 16.77 GJ/t goal in July 2026.` | Lakehouse | `dim_kpi_target`: `kpi_id`, `baseline_value`, `target_value`, `unit`; `fact_energy_daily`: `date_key`, `energy_gj`, `crude_steel_tons` |
| CO₂ emissions reduced by 22% (KPI-CO2-01, 2.10 → 1.638 tCO2e/t) | `How much has specific CO₂ intensity improved against the 2.10 tCO2e/t baseline — show the July 2026 average.` | Lakehouse | `dim_kpi_target`: `kpi_id`, `baseline_value`, `target_value`; `fact_emissions_daily`: `date_key`, `total_co2e_t`, `crude_steel_tons` |
| Furnace lining failure prediction with 21-day advance warning (KPI-FUR-01) | `What are the P50 remaining useful life estimates for all scored furnace assets as of the end of July 2026 — are any in the warning zone?` | Lakehouse | `fact_furnace_rul`: `asset_id`, `rul_days_p50`, `confidence`, `predicted_failure_date`, `risk_score` |
| High-grade steel yield improved by 8% (KPI-QUA-01, 0.90 → 0.972 ratio) | `What was the high-grade first-pass yield ratio in July 2026 compared to the 0.972 target, aggregated across all plants?` | Lakehouse | `fact_quality_yield`: `date_key`, `plant_id`, `high_grade_flag`, `first_pass_good_tons`, `attempted_tons`; `dim_kpi_target`: `kpi_id`, `target_value` |

### 4.4 AI infusion points

| `usecase.md` infusion point | Question to ask | Data source | Backing table / key columns |
|---|---|---|---|
| Physics-informed ML model predicts furnace lining degradation from thermal signatures | `What model version is currently scoring furnace RUL, and what is the result of the most recent model evaluation gate?` | Lakehouse | `fact_furnace_rul`: `asset_id`, `model_version`; `fact_model_evaluation`: `evaluation_date`, `domain`, `model_version`, `passed_gate`, `drift_score` |
| Energy dispatch optimization agent schedules processes around electricity spot prices | `How many dispatch recommendations were accepted in July 2026, and what is the total expected CO₂ avoided?` | Lakehouse | `fact_dispatch_recommendation`: `recommendation_date`, `plant_id`, `status`, `expected_co2_avoided_t`, `shiftable_mw`, `hard_constraint_violations`. Expected answer: 100 ACCEPTED out of 116 total (86.2% adoption, above KPI-ENE-03 target of 0.70), expected CO₂ avoided 11,431 t, zero hard constraint violations. |
| GenAI knowledge-capture system interviews operators and structures expertise into procedure libraries | `Show all approved procedures with their source citation counts and publication dates.` | Lakehouse | `fact_knowledge_procedure`: `procedure_id`, `topic_id`, `approved_flag`, `source_citation_count`, `published_date` |

---

### 4.5 Verified July 2026 KPI scorecard

Use this as the presenter's reference for what the agent should confirm when asked about programme
status. All figures are verified from the live lakehouse SQL endpoint.

| KPI | Target | July 2026 actual | Verdict |
|---|---|---|---|
| KPI-ENE-01 energy intensity | ≤ 16.77 GJ/t | **10.63 GJ/t** | Met |
| KPI-CO2-01 CO₂ intensity | ≤ 1.638 tCO2e/t | **1.019 tCO2e/t** | Met |
| KPI-FUR-01 lining warning lead-time | ≥ 21 days | **21.0 days** at every alert episode | Met |
| KPI-QUA-01 high-grade first-pass yield | ≥ 0.972 | **0.9494** | **Not met** |
| KPI-ENE-03 dispatch adoption | ≥ 0.70 | **0.862** (100 of 116 recommendations accepted) | Met |

**Presenter note on the amber KPI:** KPI-QUA-01 is the only unmet target, and this is deliberate.
A demo where every number is green is less credible and leaves the audience with nothing to probe.
The quality gap (0.9494 vs 0.972, about 2.3 percentage points short) gives the presenter a natural
bridge into the knowledge-capture story and illustrates that the platform reports honestly on
performance rather than cherry-picking results. Lead into it:

> "Three of our four programme targets are met in July. Quality is the one still in progress — this
> is where the GenAI knowledge-capture system becomes the next intervention."

---

## 5. Ontology showcase questions

These questions can only be answered by the property graph (`onto_novasteelv3`) because they ask
about the *structure* of the manufacturing knowledge model rather than measured numbers. The GQL is
provided for the presenter's reference — show it if challenged by a technical audience member, or
copy it into the chat to demonstrate that the agent's answer is backed by a queryable graph.

Approximate node counts in the demo graph: 4 Plant, 8 Asset, 100 Sensor, 3 Grade, 12 EquipmentClass,
7 ProcessStep, 7 ProductType, 10 Signal, 6 AlarmType.

---

### O1 — What does a blast furnace feed directly?

> Type: `What does a blast furnace feed?`

```gql
MATCH (a:EquipmentClass {ClassId:'BlastFurnace'})-[:feeds]->(b)
RETURN b.ClassName
```

Expected answer: `BasicOxygenFurnace`. The blast furnace feeds the BOF, not the caster. See section
7.2 for the teaching point.

---

### O2 — Two-hop path from blast furnace to caster

> Type: `How does steel get from the blast furnace to the continuous caster — show me the full path.`

```gql
MATCH p = (a:EquipmentClass {ClassId:'BlastFurnace'})-[:feeds*1..3]->(c:EquipmentClass {ClassId:'ContinuousCaster'})
RETURN p
```

Expected answer: BlastFurnace → BasicOxygenFurnace → ContinuousCaster, with the agent explaining
each step: iron-making in the BF, steelmaking in the BOF, solidification in the CC.

---

### O3 — What kinds of production unit do we operate?

> Type: `What types of production unit do we operate? Include which ones are abstract classes.`

```gql
MATCH (c:EquipmentClass)-[:specializes]->(:EquipmentClass {ClassId:'ProductionUnit'})
RETURN c.ClassName, c.IsAbstract AS is_abstract
```

Expected answer: A list of EquipmentClass nodes below ProductionUnit — including BlastFurnace,
BasicOxygenFurnace, ContinuousCaster, ReheatFurnace, RollingMill, and others. Abstract classes
(`is_abstract = true`) are category nodes with no direct asset instances of their own.

**Important:** The alias must be `is_abstract`, not `abstract`. See section 7.1.

---

### O4 — Which real assets are blast furnaces?

> Type: `Which actual assets in our fleet are blast furnaces?`

```gql
MATCH (a:Asset)-[:instanceOf]->(:EquipmentClass {ClassId:'BlastFurnace'})
RETURN a.AssetId
```

Expected answer: The concrete Asset instances whose equipment class is BlastFurnace (e.g.
`LUX-BF-01`). This walks the bridge from the TBox (abstract class) down to the ABox (real fleet).

---

### O5 — What does continuous casting produce?

> Type: `What product does continuous casting produce?`

```gql
MATCH (:EquipmentClass {ClassId:'ContinuousCaster'})-[:executes]->(s:ProcessStep)-[:produces]->(p:ProductType)
RETURN p.ProductName
```

Expected answer: The ProductType node(s) associated with the continuous casting process step —
typically slab, bloom, or billet. Note the label is `ProductType`, not `Product` (see section 7.1).

---

### O6 — Signals that trigger a halt on the blast furnace

> Type: `Which measurement signals can trigger an alarm that halts a blast furnace?`

```gql
MATCH (t:AlarmType)-[:halts]->(:EquipmentClass {ClassId:'BlastFurnace'}),
      (t)-[:triggeredBy]->(s:Signal)
RETURN t.AlarmTypeName, s.SignalCodeKey
```

Expected answer: One or more AlarmType nodes from the 6 in the demo, each paired with
its triggering signal. Not all 6 alarm types necessarily halt the blast furnace specifically — the
answer reflects whichever `AlarmType` nodes have a `halts` edge pointing at `BlastFurnace`.
This shows the full alarm–signal chain encoded in the ontology.

---

### O7 — What does LUX-BF-01 supply downstream?

> Type: `What does asset LUX-BF-01 supply downstream — trace the full process chain.`

```gql
MATCH (a:Asset {AssetId:'LUX-BF-01'})-[:supplies*1..3]->(d:Asset)
RETURN d.AssetId
```

Expected answer: LUX-BOF-01, then LUX-CC-01, then LUX-RHF-01 and/or LUX-HSM-01. This is the
instance-level genealogy (`supplies` edges) in the ABox, mirroring the abstract `feeds` chain in
the TBox.

---

### O8 — Which casters are in the fleet via the class hierarchy?

> Type: `List all continuous casters in our fleet by resolving through the equipment class hierarchy.`

```gql
MATCH (a:Asset)-[:instanceOf]->(:EquipmentClass {ClassId:'ContinuousCaster'})
RETURN a.AssetId
```

Expected answer: The Asset instances whose class is ContinuousCaster. This demonstrates that the
`instanceOf` bridge makes the abstract class hierarchy directly useful for querying real equipment.

---

## 6. The cross-layer question

> Type: `Which of our blast furnaces used the most energy last month?`

This is the single most technically impressive question in the demo. Ask it as a deliberate,
standalone moment and narrate what the agent is doing under the hood.

**Why it is load-bearing:** The question is phrased at the *class* level ("blast furnaces") but the
energy data is stored at the *plant* level in the gold schema. The agent must chain three steps:

1. Walk the graph to resolve `EquipmentClass {ClassId:'BlastFurnace'}` to concrete `Asset`
   instances via `[:instanceOf]`.
2. Determine which `plant_id` each blast furnace asset belongs to, via the ABox relationship
   `Plant -[hasAsset]-> Asset`.
3. Query `fact_energy_daily` for those plant IDs over the previous calendar month, aggregating
   `energy_gj` and dividing by `crude_steel_tons` for intensity.

**GQL fragment — step 1 and 2:**

```gql
MATCH (pl:Plant)-[:hasAsset]->(a:Asset)-[:instanceOf]->(:EquipmentClass {ClassId:'BlastFurnace'})
RETURN pl.plant_code, a.AssetId
```

**SQL fragment — step 3:**

```sql
SELECT plant_id,
       SUM(energy_gj) / SUM(crude_steel_tons) AS energy_intensity_gj_per_t
FROM   fact_energy_daily
WHERE  date_key >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
  AND  date_key <  DATE_TRUNC('month', CURRENT_DATE)
  AND  plant_id IN (/* plant_id values resolved from step 1 */)
GROUP BY plant_id
ORDER BY energy_intensity_gj_per_t DESC
```

**Granularity note:** `fact_energy_daily` is at plant level, not asset level. If a plant operates
more than one blast furnace, the result is the plant's combined energy figure. The agent should
state this limitation explicitly in its answer; that is the correct answer, not an error.

**What to say to the audience:**

> "I never told the agent which table to look in, which column to aggregate, or which assets are
> blast furnaces. It treated 'blast furnace' as an equipment class, walked the ontology to identify
> the real asset instances, traced those to their plants, and joined that resolved set to the energy
> fact table — all from a single natural-language question. The ontology is not decorative: without
> it, this question cannot be answered automatically because the fact table has no column that says
> 'this row belongs to a blast furnace'."

---

## 7. Presenter notes and known limitations

### 7.1 GQL reserved-word gotchas

Two reserved words appear in the NovaSteel ontology schema and cause GQL syntax errors or
access-rule violations if used incorrectly.

**`Product` is a GQL reserved word.** The product class in the ontology is labelled `ProductType`,
not `Product`. A query written as `MATCH (p:Product)` will be rejected. Always use
`(p:ProductType)`.

**`abstract` is a GQL reserved word as an alias.** The `EquipmentClass` node has a boolean property
called `IsAbstract`. Writing `RETURN c.IsAbstract AS abstract` will produce a parse error. Use
`RETURN c.IsAbstract AS is_abstract` instead. The agent's system prompt instructs it to follow this
convention; the gotcha is most relevant if a technical audience member writes their own query live.

### 7.2 The blast furnace / caster teaching point

The process chain in the ontology is metallurgically correct:

```
BlastFurnace → BasicOxygenFurnace → ContinuousCaster → ReheatFurnace / RollingMill
```

A blast furnace makes hot metal, which goes to the basic oxygen furnace for steelmaking, and only
then to the caster for solidification. The blast furnace does **not** feed the caster directly.

If an audience member asks "does a blast furnace feed the caster?", the agent answers with the
two-hop path (`feeds*1..3`) rather than denying the relationship. Call this out as a deliberate
design choice:

> "The answer is *yes, via the BOF* — the ontology is accurate enough to show the correct
> intermediate step rather than returning 'no relationship found'. Ontology errors that deny real
> relationships are harder to detect and more dangerous than correct two-hop answers. This is the
> kind of industrial precision that matters when an operator trusts the system."

### 7.3 Synthetic data disclaimer

All data in the platform has `data_classification = 'SYNTHETIC'`. Plant IDs follow the `NS-DEMO-*`
convention (NS-DEMO-LUX-01, NS-DEMO-BE-01, NS-DEMO-NL-01, NS-DEMO-DE-01). State this to the
audience before the first question, and repeat it whenever quoting a specific number.

Predictions — RUL P50, dispatch cost avoidance, quality yield forecasts — must be clearly
distinguished from measured outcomes. Qualify with "the model estimates..." or "synthetic data
shows..." rather than stating a number as a measured fact.

### 7.4 Gold-history date window — exact figures

The following row counts and date ranges are confirmed from the live lakehouse SQL endpoint. Use
these when a technical audience member asks about data coverage.

| Table | Rows | Earliest `date_key` | Latest `date_key` |
|---|---|---|---|
| `fact_energy_daily` | 2,884 | 2024-08-08 | 2026-07-29 |
| `fact_emissions_daily` | 2,884 | 2024-08-08 | 2026-07-29 |
| `fact_quality_yield` | 8,652 | 2024-08-08 | 2026-07-29 |
| `fact_furnace_rul` | 2,160 | 2024-08-08 | 2026-07-29 |
| `fact_dispatch_recommendation` | 2,884 | 2024-08-08 | 2026-07-29 |
| `fact_knowledge_procedure` | 10 | 2025-02-04 (`published_date`) | 2026-01-30 |

`dim_kpi_target` carries all seven confirmed rows: KPI-ENE-01 (19.5 → 16.77 GJ/t, decrease),
KPI-CO2-01 (2.10 → 1.638 tCO2e/t, decrease), KPI-FUR-01 (target 21.0 days, minimum),
KPI-QUA-01 (0.90 → 0.972 ratio, increase), KPI-ENE-03 (target 0.70, minimum, null baseline),
KPI-ADO-01 (target 0.80, minimum, null baseline), KPI-GOV-01 (target 1.00, minimum, null baseline).

**The critical consequence for demo questioning:**

The real-world date is 2026-08-02 and the gold history ends 2026-07-29. Always use **"in July
2026"** or **"last month"** for gold-fact questions — these return a full month of data. Never
ad-lib "today", "this week", "this month", or "in the last 7 days": those windows fall in the gap
between the data end-date and the current date, and the gold tables return zero rows.

**Why KQL questions are different:** Questions phrased as "right now", "what alarms are active",
or "what is the latest sensor reading" route to the KQL database `kql-ns-operations`, which
receives live event-stream data and is not subject to the gold-history cut-off. A "right now"
question against KQL will succeed even though the same question against gold facts would fail.
Make this distinction explicit if the audience notices the inconsistency: the gold schema is the
governed analytic layer; the KQL database is the operational real-time layer.

**`fact_knowledge_procedure` does not benefit from a date filter.** With only 10 rows and a
`published_date` ceiling of 2026-01-30, any filter to "recent months" will return zero rows.
Always ask knowledge-procedure questions without a time window.

Questions that do not specify a time window may scan the full two-year history, which increases
query time. If a response takes more than 15 seconds, prompt: `"Limit that to July 2026."` Narrow
windows consistently produce faster, cleaner answers.

### 7.5 Distinguishing predictions from measurements

The demo contains both predicted values (RUL scores in `fact_furnace_rul`, yield forecasts implied
by the what-if analysis) and measured outcomes (energy in `fact_energy_daily`, production in
`fact_production_shift`). Never present a predicted value as a measured one. The `fact_ai_decision_audit`
table records which recommendations were followed and whether an outcome was subsequently recorded —
it is the traceability layer that connects predictions to eventual measurements.

---

## 8. Troubleshooting

| Symptom | Likely cause | Resolution |
|---|---|---|
| Agent answers generically ("I don't have access to that data" or only describes its own capabilities) | Fabric capacity is paused | Resume the capacity in the Fabric Admin portal and wait approximately 2 minutes for data source connections to re-establish. Do not rephrase the question until capacity is confirmed active. |
| Agent answers generically but the capacity is confirmed active | Agent configuration not published in the workspace | Verify `da-novasteelv3` is published and active in workspace `NovaSteelV3-Demo`. Re-publish the agent if needed. |
| GQL query fails with "syntax error" or "access rule violation" | A node label or return-column alias has collided with a GQL reserved word, or the GraphModel projection is stale | Check for `Product` used as a label (use `ProductType`), `abstract` used as an alias (use `is_abstract`), or `contains` used as a relationship name (it is reserved). Also re-deploy the GraphModel if the projection has not been refreshed since the ontology was last modified. |
| A fact table query returns zero rows | The date window falls outside the gold history, or "today"/"this month" (August 2026) was used | The confirmed gold history runs from 2024-08-08 to 2026-07-29. The real-world date is 2026-08-02. Always use "in July 2026" or "last month" for gold-fact questions — not "today", "this week", or "this month". Questions against the KQL database (`kql-ns-operations`) are unaffected: they return live data. If using a clock-rebased session, confirm `demoClockShiftDays` in `/v1/meta`. |
| First query in a session is slow (15–30 seconds) | Cold-start initialisation of data source connections | Expected on the first query of a new conversation. Send the warm-up question before the audience arrives (section 2.2). |
| Agent returns multiple rows per asset from `fact_furnace_rul` | The table stores one row per inference run, not one per asset | Prompt: `"Show only the most recent scored_date per asset."` |
| Ontology returns no results for an ABox instance query | GraphModel not deployed, or ABox data not loaded | Confirm the ontology item is published and that the GraphModel includes both the ABox (instance) and TBox (vocabulary) layers. A TBox-only deployment answers class-structure questions but returns nothing for instance queries such as `MATCH (a:Asset)...`. |
