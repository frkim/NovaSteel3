# 06 · Quality — Batch Quality and Defect Analytics (SPC)

**Audience:** a complete newcomer to steel quality, laboratory testing, and process control.  
**Reading time:** ~15 minutes.  
**Persona:** Jens Bakker — Quality Engineer (`apps\analytics-mfe\src\personaRoutes.ts:61-70`; `docs\personas\personas-and-journeys.md:42-50`).  
**Routes covered:** `/{site}/quality/batches`, `/{site}/quality/spc`.  
**Last updated:** 2026-07-27  
**Language:** 🇫🇷 [Version française](../fr/06-quality.md)

---

## Quality basics before you open the screen

A **batch** is a traceable unit of production. In flat steel it may end as a coil. A **heat** is a batch of molten steel made with a specific chemical recipe before it is cast and rolled. **Batch genealogy** means the family tree of a product: raw material lots, heat, ladle treatment, slab, reheating, coil, sample, test result, and shipment (`apps\analytics-mfe\src\api\domain.ts:155-171`; `services\bff-api\src\bff_api\repository.py:198-226`).

**High-grade steel for automotive customers** means steel that must meet tight strength, flatness, surface, and consistency requirements. Automotive customers reject coils if mechanical properties or surface quality fall outside specification. The use case says AxelorMetal faces "**Quality consistency issues in high-grade steel for automotive customers**" (`docs\usecase\usecase.md:14-22`). The expected outcome is "**High-grade steel yield improved by 8%**" (`docs\usecase\usecase.md:37-42`).

**Yield** is the share of produced material that is good enough to sell for its intended grade. **First-pass yield** means it passed the first inspection without rework. **Scrap** is material that cannot be sold as intended. **Rework** is extra processing to fix or downgrade material. Both cost money and may delay customer orders (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:31-36`).

NovaSteel is careful about **predicted** versus **measured** quality. A predicted score is a model estimate, such as first-pass yield risk from coiling temperature bias (`services\scoring-worker\src\scoring_worker\service.py:73-97`). A lab-measured result is an actual test value, such as MPa strength with PASS/FAIL status (`apps\analytics-mfe\src\api\domain.ts:134-153`). The drawer lets you toggle **Predicted** and **Measured** labels, and it explicitly says no recipe or setpoint is written (`apps\analytics-mfe\src\components\screens\QualityBatchDrawer.tsx:117-180`).

**SPC** means **Statistical Process Control**. It is a way to tell whether a process is stable or drifting. An SPC **control chart** plots samples over time with a **centre line** (average), **UCL** (Upper Control Limit), and **LCL** (Lower Control Limit). Points outside UCL/LCL are **out of control** and need investigation (`apps\analytics-mfe\src\components\charts\ControlChart.tsx:120-184`; `apps\analytics-mfe\src\components\screens\QualitySpc.tsx:52-77`). **Cp/Cpk** are process capability indices: higher means the process fits better within specification limits; the screen target is Cpk ≥ 1.33 (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:38-43`). A **Pareto chart** orders defect causes from most frequent to least frequent and overlays a cumulative percentage line so engineers can focus on the few causes that create most defects (`apps\analytics-mfe\src\components\charts\ParetoChart.tsx:23-168`).

---

## Batch Quality — `/{site}/quality/batches`

![Batch quality screen](../screenshots/quality-batches.png)

**In one sentence.** This screen shows quality KPIs, a predicted yield trend, and a clickable batch table that opens genealogy and bounded what-if analysis (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:19-92`; `apps\analytics-mfe\src\components\screens\QualityBatchDrawer.tsx:42-185`).

**Steel-industry background (for newcomers).** A coil can pass or fail because its measured strength, chemistry, surface, or temperature history does not match the grade promise. NovaSteel focuses on a drifting automotive DP780 coil in the synthetic demo (`docs\demo\demo-runbook.md:84-88`; `apps\analytics-mfe\src\api\fixtures.ts:359-407`).

**What you see on screen.**

1. **Global shell and safety banner.** The screenshot shows the LU site, the left navigation, and the purple synthetic-data banner. This reminds you that the quality data is not production data (`docs\demo\demo-runbook.md:39-45`; `apps\analytics-mfe\src\api\fixtures.ts:21-29`).
2. **Persona and tabs.** The header shows Jens Bakker — Quality Engineer. "Batch Quality" is selected; "Defect Analytics (SPC)" is the next tab (`apps\analytics-mfe\src\personaRoutes.ts:61-70`).
3. **KPI card — High-grade yield.** The screenshot shows **94.8%**, **+1.2 pts**, and target **95%**. Higher is better; a drop means more steel may miss the premium grade (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:31-36`).
4. **KPI card — First-pass yield.** The card shows **97.1%** and target **97%**. Higher is better because fewer coils need rework or second inspection (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:31-36`).
5. **KPI card — Open NCRs.** The card shows **3**. NCR means **Non-Conformance Record**: a formal quality issue that needs review before release (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:30-35`).
6. **KPI card — Defect rate.** The card shows **182 ppm** with target **170**. **ppm** means parts per million; lower is better (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:35`).
7. **Chart — Yield trend.** The line is flat near the high 90s, then drops sharply around batch #7 and drifts downward. Good is a stable line near target; bad is the downward excursion shown for the drifting DP780 coil (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:25-29`; `apps\analytics-mfe\src\components\charts\LineChart.tsx:45-180`).
8. **How to read the line chart.** A line chart shows change over ordered samples. Here, left-to-right means batch order, and lower y-values mean predicted first-pass yield is worsening (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:52-68`).
9. **Batches table.** The table has global search, per-column search, proof badges, and columns **Batch**, **Grade**, **Heat**, **Value**, **Coiling bias °C**, **Risk**, **Result**, and **Updated**. Visible rows include DP780 coils with values around 810–818 MPa, risk around 57–61%, and PASS/FAIL pills (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:38-88`).
10. **PASS and FAIL labels.** The result pill is a lab status, not a prediction. The risk percentage is model-derived from process bias; the value in MPa is a measured quality characteristic (`apps\analytics-mfe\src\api\domain.ts:134-153`; `services\scoring-worker\src\scoring_worker\service.py:73-97`).
11. **Batch drawer when you click a row.** The drawer title is the batch ID and shows chips for grade, status, and coiling-temperature bias. It then lists the genealogy chain: raw material lots, heat, ladle treatment, slab, reheating operation, coil, sample, and shipment (`apps\analytics-mfe\src\components\screens\QualityBatchDrawer.tsx:31-40`; `apps\analytics-mfe\src\components\screens\QualityBatchDrawer.tsx:79-113`).
12. **Bounded what-if in the drawer.** The drawer has sliders for **Coiling temperature Δ** and **Force balance Δ**, plus a Predicted/Measured toggle. Predicted mode shows current → proposed first-pass yield and a P10–P90 confidence band. Measured mode shows the lab result and repeats that no setpoint or recipe is written (`apps\analytics-mfe\src\components\screens\QualityBatchDrawer.tsx:117-180`; `services\scoring-worker\src\scoring_worker\service.py:99-145`).

**Why this component was implemented.** It directly answers the business challenge "Quality consistency issues in high-grade steel for automotive customers" (`docs\usecase\usecase.md:14-22`) and the transformation objective "Improves steel quality" (`docs\usecase\usecase.md:26-33`). The UX spec defines Batch Quality as the quality engineer's surface for yield KPI, batch table, and drill drawer (`docs\ux\dashboard-specification.md:717-734`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| High-grade automotive quality challenge | `CHL-04` | Batch KPIs, yield trend, PASS/FAIL table, drawer what-if | `GET /v1/quality/batches`; `GET /v1/quality/batches/{batchId}/genealogy`; `POST /v1/quality/what-if`; `services\bff-api\src\bff_api\routes.py:412-492`; `apps\analytics-mfe\src\proof\proofCatalog.ts:292-310` |
| Improve steel quality | `OBJ-03` | Risk-based yield trend and bounded what-if | `services\scoring-worker\src\scoring_worker\service.py:73-145`; `apps\analytics-mfe\src\proof\proofCatalog.ts:373-393` |
| High-grade yield target | `OUT-04` | High-grade yield KPI and proof mapping | `apps\analytics-mfe\src\components\screens\QualityBatches.tsx:31-36`; `apps\analytics-mfe\src\proof\proofCatalog.ts:495-518`; `docs\presentation\proof_of_execution.md:352-357` |

**How the data reaches this screen.** `QualityBatches.tsx` calls `client.getQualityBatches()` for the table (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:19-23`). `DataClient.getQualityBatches()` calls `GET /v1/quality/batches`; `getGenealogy()` calls `GET /v1/quality/batches/{batchId}/genealogy`; `qualityWhatIf()` calls `POST /v1/quality/what-if` (`apps\analytics-mfe\src\api\dataClient.ts:205-235`). The BFF reads quality rows and genealogy from the repository and sends what-if requests to the scoring worker (`services\bff-api\src\bff_api\routes.py:412-492`; `services\bff-api\src\bff_api\repository.py:161-226`; `services\scoring-worker\src\scoring_worker\service.py:99-145`).

**Honesty & caveats.** The quality data is deterministic synthetic data (`apps\analytics-mfe\src\api\fixtures.ts:21-29`). The yield model is a calibrated surrogate over coiling-temperature bias, not a production-trained metallurgical model (`apps\analytics-mfe\src\proof\proofCatalog.ts:292-310`). The +8% high-grade yield is a demo target/surrogate, not a measured customer outcome (`docs\presentation\proof_of_execution.md:352-357`). The what-if is advisory and writes no recipe or setpoint (`services\scoring-worker\src\scoring_worker\service.py:140-144`; `contracts\openapi\bff-api-v1.yaml:243-255`).

**Try it yourself.** Open `http://localhost:5266/lu/quality/batches`, click a DP780 row such as `COIL-LUX-260725-017`, inspect the genealogy, move the coiling-temperature slider, then toggle from Predicted to Measured (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:76-89`; `apps\analytics-mfe\src\components\screens\QualityBatchDrawer.tsx:117-180`).

---

## Defect Analytics (SPC) — `/{site}/quality/spc`

![Defect analytics SPC screen](../screenshots/quality-spc.png)

**In one sentence.** This screen shows whether the process is statistically stable and which defect causes deserve the first corrective action (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:20-101`).

**Steel-industry background (for newcomers).** Even if individual coils pass, the process can still be drifting. SPC catches that drift early by asking whether recent samples still behave like normal process variation or have crossed a control limit (`apps\analytics-mfe\src\components\charts\ControlChart.tsx:120-184`).

**What you see on screen.**

1. **KPI card — Out-of-control points.** The screenshot shows **1** with target "I-MR, 3σ limits". Good is zero; one point means at least one sample crossed a statistical control limit (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:26-43`).
2. **KPI card — Process Cpk.** The screenshot shows **1.18** with target **≥ 1.33**. Higher is better; below target means the process is not capable enough for the desired high-grade consistency (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:38-43`).
3. **KPI card — Top defect share.** The screenshot shows **39.5%** and "Pareto 80/20". This means the biggest defect type accounts for a large share of all defects (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:28-42`; `apps\analytics-mfe\src\api\fixtures.ts:423-431`).
4. **KPI card — Defects (30d).** The screenshot shows **86** total defects in the synthetic 30-day window (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:42`; `apps\analytics-mfe\src\api\fixtures.ts:423-431`).
5. **Control chart panel.** The main panel is titled **SPC control chart (coiling temperature bias)**. The blue line plots 20 samples. The dotted centre line is **x̄ 1.9**. The red dashed UCL is about **8.5** and the LCL is about **−4.7**. The last point at **11.4** is red and marked as out of control (`apps\analytics-mfe\src\api\fixtures.ts:410-420`; `apps\analytics-mfe\src\components\charts\ControlChart.tsx:120-184`).
6. **How to read UCL, LCL, and centre line.** The centre line is the normal average. UCL and LCL are not customer specification limits; they are statistical warning rails, commonly set at about three standard deviations from the centre. A point outside them says "investigate the process," not automatically "scrap the coil" (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:57-77`; `apps\analytics-mfe\src\components\charts\ControlChart.tsx:139-184`).
7. **Defect Pareto panel.** The right panel is titled **Defect Pareto**. Orange bars show counts by defect type, sorted highest to lowest, and the red line shows cumulative percentage. In the screenshot, "Coiling temperature drift" dominates with 34 counts, followed by "Edge crack" with 21 (`apps\analytics-mfe\src\api\fixtures.ts:423-431`; `apps\analytics-mfe\src\components\charts\ParetoChart.tsx:23-168`).
8. **How to read the Pareto 80/20 chart.** Start from the tallest bar. If the first few bars explain most of the cumulative red line, fix those first. Good is a shrinking top bar over time; bad is one root cause staying dominant (`apps\analytics-mfe\src\components\charts\ParetoChart.tsx:81-160`; `docs\ux\dashboard-specification.md:986-993`).
9. **Defects table.** The table below the Pareto has search boxes and columns **Defect**, **Cause**, and **Count**. Visible rows include **Coiling temperature drift / Process / 34**, **Edge crack / Material / 21**, **Surface scale / Reheat / 14**, and **Thickness variance / Mill / 9** (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:45-98`; `apps\analytics-mfe\src\api\fixtures.ts:423-431`).

**Why this component was implemented.** The screen exists because the brief calls out quality consistency problems in high-grade automotive steel (`docs\usecase\usecase.md:14-22`). The UX spec says the Quality area must include SPC control charts, UCL/LCL rule-violation markers, Pareto ordering, and a defect table (`docs\ux\dashboard-specification.md:717-734`; `docs\ux\dashboard-specification.md:986-993`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Quality consistency challenge | `CHL-04` | Out-of-control KPI, SPC chart, Pareto root-cause view | Current SPC screen uses deterministic frontend fixtures: `apps\analytics-mfe\src\components\screens\QualitySpc.tsx:1-101`; `apps\analytics-mfe\src\api\fixtures.ts:410-431`; proof mapping in `apps\analytics-mfe\src\proof\proofCatalog.ts:292-310` |
| Improve steel quality | `OBJ-03` | Cpk, control limits, defect analysis | `apps\analytics-mfe\src\proof\proofCatalog.ts:373-393`; scoring and what-if route for corrective exploration: `POST /v1/quality/what-if`, `services\scoring-worker\src\scoring_worker\service.py:99-145` |
| High-grade yield target | `OUT-04` | SPC supports the same quality target shown in Batch Quality | `docs\presentation\proof_of_execution.md:352-357`; `apps\analytics-mfe\src\proof\proofCatalog.ts:495-518` |

**How the data reaches this screen.** In the current implementation, `QualitySpc.tsx` imports `spcSeries()` and `defectPareto()` directly from frontend fixtures (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:1-24`; `apps\analytics-mfe\src\api\fixtures.ts:410-431`). The broader quality workflow routes are `GET /v1/quality/batches`, `GET /v1/quality/batches/{batchId}/genealogy`, and `POST /v1/quality/what-if` (`docs\implementation\api-contracts.md:209-216`; `contracts\openapi\bff-api-v1.yaml:209-255`).

**Honesty & caveats.** The SPC values are synthetic fixture values, not a live laboratory feed (`apps\analytics-mfe\src\api\fixtures.ts:410-431`). The Cpk and defect counts teach the workflow; they do not prove real process capability. A control-limit breach is a signal for root-cause investigation, not automatic rejection of every product. No corrective setpoint is written from the SPC screen (`docs\ux\dashboard-specification.md:1190-1195`).

**Try it yourself.** Open `http://localhost:5266/lu/quality/spc`, find the red final point above UCL, then use the Pareto table to identify the top defect cause before returning to Batch Quality for a bounded what-if (`apps\analytics-mfe\src\components\screens\screenRegistry.ts:41-42`; `apps\analytics-mfe\src\components\screens\QualitySpc.tsx:52-98`).

---

◀ [05 · Energy optimization](05-energy-optimization.md) · ▲ [Index](README.md) · [07 · Sustainability and compliance](07-sustainability-and-compliance.md) ▶
