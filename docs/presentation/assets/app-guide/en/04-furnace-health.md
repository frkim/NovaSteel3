# 04 — Furnace Health

**Audience:** complete newcomers to steelmaking and industrial analytics  
**Reading time:** 18 minutes  
**Persona:** Elena Duarte, Furnace Operator, and Tomás Rossi, Maintenance & Reliability Engineer  
**Routes covered:** `/lu/furnace-health/lining-forecast`, `/lu/furnace-health/thermal-explorer`, `/lu/furnace-health/maintenance-planner`  
**Last updated:** 2026-07-27  
[🇫🇷 Version française](../fr/04-furnace-health.md)

Furnace Health is NovaSteel's main AI story: sensor readings show a hot pattern, the scoring worker estimates remaining useful life (RUL), and the maintenance screen turns that risk into a synthetic inspection order. This follows the use-case statements “**Furnace lining wear** impossible to predict, causing catastrophic failures costing **€8M per event**”, “**Furnace lining failure prediction** with **21-day advance warning**”, and “A **physics-informed ML model** predicts furnace lining degradation from thermal signatures”. (`docs\usecase\usecase.md`; `apps\analytics-mfe\src\components\screens\FurnaceThermal.tsx`; `apps\analytics-mfe\src\components\screens\FurnaceLiningForecast.tsx`; `apps\analytics-mfe\src\components\screens\FurnaceMaintenance.tsx`)

For a newcomer: a **blast furnace** makes molten iron. Its **hearth** is the lower vessel where hot metal collects. A **refractory lining** is the heat-resistant inner wall. A **breakout** is a dangerous escape of hot metal when that wall fails. (`docs\usecase\usecase.md`; `services\scoring-worker\src\scoring_worker\physics_features.py`)

---

## Lining Forecast — `/lu/furnace-health/lining-forecast`
![Furnace Health Lining Forecast](../screenshots/furnace-health-lining-forecast.png)

**In one sentence.** This screen predicts when the blast-furnace hearth lining may cross a risk threshold and explains the drivers behind that forecast. (`apps\analytics-mfe\src\components\screens\FurnaceLiningForecast.tsx`)

**Steel-industry background (for newcomers).** **RUL** means remaining useful life: the estimated time before an asset reaches a defined limit. **P50** is the middle estimate; **P10** is the earlier, more cautious bound; **P90** is the later bound. **Confidence band** means the model is saying “the answer is probably in this range,” not “this date is guaranteed.” (`services\scoring-worker\src\scoring_worker\rul_model.py`; `docs\presentation\proof_of_execution.md`)

**What you see on screen.**
1. A top banner states **Synthetic demo data — not for operational control**, so the page is explicitly advisory. (`docs\demo\demo-runbook.md`; `apps\analytics-mfe\src\api\dataClient.ts`)
2. The selected tab is **Lining Forecast**, and the persona chip says **Elena Duarte & Tomás Rossi — Furnace / Maintenance**. (`docs\personas\personas-and-journeys.md`; `apps\analytics-mfe\src\components\screens\FurnaceLiningForecast.tsx`)
3. The KPI cards show **Lining risk 90% HIGH**, **Days to threshold 19.7 d**, **Model confidence P10–P90 18.69–20.61 d**, and **Predicted failure date Jun 30, 2026**. Good is low risk and many days left; bad is high risk above the 80% threshold. (`apps\analytics-mfe\src\components\screens\FurnaceLiningForecast.tsx`; `services\bff-api\src\bff_api\routes.py`)
4. The **Lining risk over 21-day horizon** line chart has days on the x-axis and risk on the y-axis. The red dashed **Threshold 0.8** line is the trigger; the blue line is median risk; the pale blue band is P10–P90 uncertainty. (`apps\analytics-mfe\src\components\charts\LineChart.tsx`; `apps\analytics-mfe\src\components\screens\FurnaceLiningForecast.tsx`)
5. The **Why? · drivers · freshness** panel shows proof badges **CHL-03**, **OBJ-02**, **OUT-03**, **AI-01**, plus **Risk 90% · HIGH**, **P50 19.7 days**, and driver contributions such as refractory-thickness slope, heat-flux trend, normalized health index, and cooling efficiency. (`apps\analytics-mfe\src\proof\proofCatalog.ts`; `apps\analytics-mfe\src\components\screens\FurnaceLiningForecast.tsx`)
6. The **Feature snapshot** shows lining thickness, cooling-water ΔT, and heat flux. ΔT means the temperature difference between water entering and leaving the cooling circuit. (`services\scoring-worker\src\scoring_worker\physics_features.py`; `apps\analytics-mfe\src\components\screens\FurnaceLiningForecast.tsx`)
7. **Plan inspection work order** navigates to maintenance planning; it does not write a furnace setpoint or touch a PLC. (`apps\analytics-mfe\src\components\screens\FurnaceLiningForecast.tsx`; `docs\personas\personas-and-journeys.md`)
8. The **Furnace units** table compares **LUX-BF-01** and **LUX-RHF-01** by risk, days left, confidence, last inspection, open work orders, and health. (`apps\analytics-mfe\src\components\screens\FurnaceLiningForecast.tsx`; `apps\analytics-mfe\src\api\fixtures.ts`)

**Why this component was implemented.** It directly addresses “**Furnace lining wear** impossible to predict, causing catastrophic failures costing **€8M per event**” and demonstrates the quoted AI infusion point about predicting degradation from thermal signatures. (`docs\usecase\usecase.md`)

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Furnace lining wear is unpredictable; failures cost €8M | `CHL-03` | Badge in **Why?** panel and high lining risk. | `GET /v1/furnaces/{assetId}/lining-forecast`; `services\scoring-worker\src\scoring_worker\physics_features.py`; `services\scoring-worker\src\scoring_worker\rul_model.py`; `apps\analytics-mfe\src\proof\proofCatalog.ts` |
| Predict equipment failures | `OBJ-02` | RUL output leads the user toward maintenance planning. | `apps\analytics-mfe\src\components\screens\FurnaceLiningForecast.tsx`; `services\bff-api\src\bff_api\routes.py` |
| Failure predicted 21 days in advance | `OUT-03` | The chart and threshold show the 21-day warning narrative. | `services\scoring-worker\src\scoring_worker\rul_model.py`; `docs\presentation\proof_of_execution.md` |
| Physics-informed ML predicts lining degradation | `AI-01` | The **Why?** panel exposes physical drivers and feature values. | `services\scoring-worker\src\scoring_worker\physics_features.py`; `services\scoring-worker\src\scoring_worker\rul_model.py` |

**How the data reaches this screen.** `FurnaceLiningForecast.tsx` calls `client.getLiningForecast('LUX-BF-01')` and `client.getFurnaces()`. `DataClient` targets `/v1/furnaces/{assetId}/lining-forecast` and `/v1/furnaces?site=...`; if the BFF is unavailable it falls back to fixtures. The BFF calls the scoring service, where ordinary least squares (OLS) fits thermal features and extrapolates time-to-failure. (`apps\analytics-mfe\src\components\screens\FurnaceLiningForecast.tsx`; `apps\analytics-mfe\src\api\dataClient.ts`; `services\bff-api\src\bff_api\routes.py`; `services\scoring-worker\src\scoring_worker\service.py`)

**Honesty & caveats.** Synthetic data is not plant evidence. A prediction is not a measurement. “Physics-informed” here means physics-derived features in a regression; it is not a full thermodynamic wear model. NovaSteel never writes setpoints, never controls PLCs, and never bypasses safety interlocks. (`docs\presentation\proof_of_execution.md`; `services\scoring-worker\src\scoring_worker\physics_features.py`; `docs\personas\personas-and-journeys.md`)

**Try it yourself.** Open http://localhost:5266 and click **Furnace Health → Lining Forecast**, or go to `http://localhost:5266/lu/furnace-health/lining-forecast`. (`docs\ux\dashboard-specification.md`; `apps\analytics-mfe\src\components\screens\FurnaceLiningForecast.tsx`)

---

## Thermal Explorer — `/lu/furnace-health/thermal-explorer`
![Furnace Health Thermal Explorer](../screenshots/furnace-health-thermal-explorer.png)

**In one sentence.** This screen shows the thermal pattern behind the lining forecast, so users can tell a real hotspot from a single bad sensor. (`apps\analytics-mfe\src\components\screens\FurnaceThermal.tsx`)

**Steel-industry background (for newcomers).** A **thermocouple** is a temperature sensor. **Tuyères** are nozzles that blow hot air into the lower furnace. A **thermal signature** is a pattern of heat across sensors and time. (`docs\demo\demo-runbook.md`; `apps\analytics-mfe\src\components\screens\FurnaceThermal.tsx`)

**What you see on screen.**
1. KPI cards show **SECTOR-07 peak 730 °C**, **6-hour slope 3.4 °C/h**, **Anomaly cells 10**, and **Cooling ΔT 9.4 °C**. Good is stable; bad is rising heat and many anomaly cells. (`apps\analytics-mfe\src\components\screens\FurnaceThermal.tsx`; `apps\analytics-mfe\src\api\fixtures.ts`)
2. **Thermal signature (hearth sectors × time)** is a heatmap: rows are **SECTOR-05** to **SECTOR-09**, columns are hours, brighter colors are hotter, and white triangles mark cells at or above 700 °C. (`apps\analytics-mfe\src\components\charts\Heatmap.tsx`; `apps\analytics-mfe\src\components\screens\FurnaceThermal.tsx`)
3. **SECTOR-07** becomes yellow toward the right side, showing a localized warm zone developing over time. (`apps\analytics-mfe\src\api\fixtures.ts`)
4. The **Selected sensor** panel has **S05–S09** buttons; **S07** is selected. The line chart rises from the mid-600s °C to about **730 °C**. (`apps\analytics-mfe\src\components\screens\FurnaceThermal.tsx`; `apps\analytics-mfe\src\components\charts\LineChart.tsx`)
5. The note says neighboring thermocouples, cooling-water ΔT, and heat-flux residual agree, which is stronger than one isolated reading. (`apps\analytics-mfe\src\components\screens\FurnaceThermal.tsx`; `docs\demo\demo-runbook.md`)
6. The **Thermal anomalies** table lists zone, time, and temperature; visible entries include **SECTOR-07** values **730**, **725**, and **724 °C**. (`apps\analytics-mfe\src\components\screens\FurnaceThermal.tsx`)

**Why this component was implemented.** It makes the use-case phrase “thermal signatures” visible and supports the AI infusion point for furnace-lining degradation. (`docs\usecase\usecase.md`; `docs\presentation\proof_of_execution.md`)

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Furnace lining wear is unpredictable | `CHL-03` | SECTOR-07 hotspot and anomaly table show a developing signal. | `apps\analytics-mfe\src\api\fixtures.ts`; `apps\analytics-mfe\src\components\screens\FurnaceThermal.tsx` |
| Predict equipment failures | `OBJ-02` | Thermal evidence feeds the RUL alert narrative. | `GET /v1/telemetry?site=...`; `apps\analytics-mfe\src\api\dataClient.ts`; `services\bff-api\src\bff_api\routes.py` |
| 21-day advance warning | `OUT-03` | The pattern is upstream evidence for the warning forecast. | `services\scoring-worker\src\scoring_worker\physics_features.py`; `services\scoring-worker\src\scoring_worker\rul_model.py` |
| Physics-informed ML | `AI-01` | Heatmap and sensor trend expose the thermal signature. | `apps\analytics-mfe\src\proof\proofCatalog.ts`; `apps\analytics-mfe\src\components\screens\FurnaceThermal.tsx` |

**How the data reaches this screen.** `FurnaceThermal.tsx` uses `thermalMatrix()` for the heatmap and `client.getTelemetry()` for table state. `DataClient.getTelemetry()` calls `/v1/telemetry?site=...&size=200`; the BFF also exposes `/v1/furnaces/{asset_id}/telemetry`. (`apps\analytics-mfe\src\components\screens\FurnaceThermal.tsx`; `apps\analytics-mfe\src\api\fixtures.ts`; `apps\analytics-mfe\src\api\dataClient.ts`; `services\bff-api\src\bff_api\routes.py`)

**Honesty & caveats.** The heatmap is synthetic. A hot color is a clue, not proof by itself. Operators should compare neighboring sensors, water ΔT, and heat flux; NovaSteel does not control furnace air, burden, cooling, PLCs, or trips. (`docs\demo\demo-runbook.md`; `docs\personas\personas-and-journeys.md`)

**Try it yourself.** Open http://localhost:5266 and click **Furnace Health → Thermal Explorer**, or go to `http://localhost:5266/lu/furnace-health/thermal-explorer`. (`apps\analytics-mfe\src\components\screens\FurnaceThermal.tsx`)

---

## Maintenance Planner — `/lu/furnace-health/maintenance-planner`
![Furnace Health Maintenance Planner](../screenshots/furnace-health-maintenance-planner.png)

**In one sentence.** This screen turns lining-risk evidence into a maintenance schedule and synthetic work orders. (`apps\analytics-mfe\src\components\screens\FurnaceMaintenance.tsx`)

**Steel-industry background (for newcomers).** **Preventive maintenance** is calendar-based. **Predictive maintenance** is condition-based. A **campaign** is the operating period between major furnace rebuilds, and a **reline** replaces the refractory lining. (`docs\personas\personas-and-journeys.md`; `docs\presentation\proof_of_execution.md`)

**What you see on screen.**
1. KPI cards show **Open work orders 1**, **Urgent 1 BF-01**, **Relining window 18–24 d**, and **Completed (30d) 7**. Good is planned work inside the safe window; bad is urgent work without a slot. (`apps\analytics-mfe\src\components\screens\FurnaceMaintenance.tsx`)
2. **Maintenance schedule** is a Gantt chart: each horizontal bar is work over calendar time. **BF-01 hearth inspection** is urgent with a red dashed outline; **Refractory relining window** is the later green planned window. (`apps\analytics-mfe\src\components\charts\GanttChart.tsx`; `apps\analytics-mfe\src\components\screens\FurnaceMaintenance.tsx`)
3. The chart also includes **RHF-01 zone 03 watch** and **Cooling circuit ultrasound** as planned tasks. (`apps\analytics-mfe\src\components\screens\FurnaceMaintenance.tsx`)
4. The **Work orders** table shows **WO-DEMO-LUX-1042**, **LUX-BF-01**, **Synthetic planned inspection — HEARTH-SECTOR-07**, and reason **Predicted RUL below 21-day threshold; verify neighboring sensors and cooling ΔT**. (`apps\analytics-mfe\src\api\fixtures.ts`; `apps\analytics-mfe\src\components\screens\FurnaceMaintenance.tsx`)
5. **PLANNED_INSPECTION** means the demo created a planned inspection record, not a completed repair and not an automatic plant command. (`services\bff-api\src\bff_api\repository.py`; `services\bff-api\src\bff_api\routes.py`)
6. **WO-DEMO-RHF-1043** is a routine reheat-furnace watch with **COMPLETED** status. (`apps\analytics-mfe\src\api\fixtures.ts`)

**Why this component was implemented.** It shows how the €8M risk and 21-day warning become scheduled work instead of a chart with no owner. (`docs\usecase\usecase.md`; `docs\presentation\proof_of_execution.md`)

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Furnace lining wear risk | `CHL-03` | Urgent BF-01 inspection is linked to hearth forecast evidence. | `apps\analytics-mfe\src\api\fixtures.ts`; `services\bff-api\src\bff_api\repository.py` |
| Predict equipment failures | `OBJ-02` | Schedule converts risk into planned work. | `apps\analytics-mfe\src\proof\proofCatalog.ts`; `apps\analytics-mfe\src\components\screens\FurnaceMaintenance.tsx` |
| 21-day advance warning | `OUT-03` | Relining window is aligned with RUL planning. | `apps\analytics-mfe\src\components\screens\FurnaceMaintenance.tsx`; `docs\presentation\proof_of_execution.md` |
| Physics-informed ML | `AI-01` | Work-order reason references model output and sensor checks. | `services\scoring-worker\src\scoring_worker\service.py`; `apps\analytics-mfe\src\api\fixtures.ts` |

**How the data reaches this screen.** `FurnaceMaintenance.tsx` calls `client.getWorkOrders()`. The current front-end uses deterministic fixture work orders for the list. Creating a synthetic order is supported by `POST /v1/workorders`; the BFF requires an `Idempotency-Key`, writes **PLANNED_INSPECTION**, links the alert, and records an audit entry. (`apps\analytics-mfe\src\components\screens\FurnaceMaintenance.tsx`; `apps\analytics-mfe\src\api\dataClient.ts`; `services\bff-api\src\bff_api\routes.py`; `services\bff-api\src\bff_api\repository.py`)

**Honesty & caveats.** These work orders are synthetic. The Gantt chart is not a real CMMS integration. NovaSteel does not stop furnaces, book crews, write setpoints, or touch PLC safety logic. (`services\bff-api\src\bff_api\routes.py`; `services\bff-api\src\bff_api\repository.py`; `docs\demo\demo-runbook.md`)

**Try it yourself.** Open http://localhost:5266 and click **Furnace Health → Maintenance Planner**, or go to `http://localhost:5266/lu/furnace-health/maintenance-planner`. (`apps\analytics-mfe\src\components\screens\FurnaceMaintenance.tsx`)

---

[◀ Previous: Command Center and Operations](03-command-center-and-operations.md) | [▲ Index](README.md) | [Next ▶ Energy Optimization](05-energy-optimization.md)
