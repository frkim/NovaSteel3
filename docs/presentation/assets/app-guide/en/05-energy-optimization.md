# 05 · Energy optimization — Spot & Schedule and Load-Shift Simulator

**Audience:** a complete newcomer to steel, energy markets, and NovaSteel.  
**Reading time:** ~14 minutes.  
**Persona:** Sofia Lindqvist — Energy Manager (`apps\analytics-mfe\src\personaRoutes.ts:49-58`; `docs\personas\personas-and-journeys.md:158-199`).  
**Routes covered:** `/{site}/energy-optimization/spot-price-schedule`, `/{site}/energy-optimization/load-shift-simulator`.  
**Last updated:** 2026-07-27  
**Language:** 🇫🇷 [Version française](../fr/05-energy-optimization.md)

---

## Steel and electricity basics before you open the screen

Steelmaking uses a lot of heat. In NovaSteel's business brief, the problem is stated plainly: "**Energy costs represent 35% of total production cost with no real-time optimization**" (`docs\usecase\usecase.md:14-22`). The target outcome is "**Energy consumption per ton reduced by 14%**" and "**CO₂ emissions reduced by 22%**" (`docs\usecase\usecase.md:37-42`).

A **day-ahead** or **spot price** is the electricity price for a short time block, quoted in **€/MWh**: euros per megawatt-hour. A **megawatt-hour (MWh)** is energy; using 10 megawatts for one hour consumes 10 MWh. The screen also shows grid **carbon intensity**, meaning how many kilograms or grams of CO₂-equivalent emissions are linked to each MWh of electricity (`apps\analytics-mfe\src\api\domain.ts:71-86`).

Prices have **peaks** and **valleys**. A peak is an expensive hour, like the evening scarcity spike shown as 280 €/MWh in the demo fixtures (`apps\analytics-mfe\src\api\fixtures.ts:37-43`; `docs\demo\demo-runbook.md:123-133`). A valley is a cheaper hour. **Load shifting** or **demand response** means moving flexible electricity demand away from peaks and into valleys. A **dispatch schedule** is the time plan that says which batch or process runs in which time window (`apps\analytics-mfe\src\api\domain.ts:88-132`).

Not every steel process can move. A **blast furnace** is a continuous ironmaking unit: stopping or delaying it casually is unsafe and unrealistic. A **reheat furnace** heats slabs or coils before rolling; some reheat batches can move within limits if delivery, holding, soaking, and capacity rules still hold (`services\optimizer-worker\src\optimizer_worker\milp.py:1-8`; `services\optimizer-worker\src\optimizer_worker\service.py:163-190`). An **electric-arc furnace**, if available, is also more shiftable than a blast furnace because it runs in campaigns, but this NovaSteel screen currently models reheat batches (`services\bff-api\fixtures\demo-full\heat_batch.ndjson:2-8`; `services\optimizer-worker\src\optimizer_worker\service.py:372-400`).

### What the optimizer actually solves

NovaSteel uses a **mixed-integer linear program (MILP)**. In plain language: it asks a solver to choose a time slot for each eligible batch, while obeying hard rules, and to find the cheapest and cleaner combination (`services\optimizer-worker\src\optimizer_worker\milp.py:1-8`).

| Solver idea | Plain-language meaning | Evidence |
|---|---|---|
| Objective function | The score the optimizer tries to minimize: energy cost plus carbon impact. | `services\optimizer-worker\src\optimizer_worker\milp.py:110-125`; `docs\presentation\proof_of_execution.md:182-204` |
| Decision variables | Yes/no choices: "batch B starts in slot S". | `services\optimizer-worker\src\optimizer_worker\milp.py:65-89` |
| Assignment constraint | Every batch starts exactly once. | `services\optimizer-worker\src\optimizer_worker\milp.py:90-95` |
| Capacity constraint | No more than the allowed number of concurrent batches in one slot. | `services\optimizer-worker\src\optimizer_worker\milp.py:97-108` |
| Urgent fixed batch | An urgent automotive batch is pinned to its planned slot; it is not sacrificed for cheaper power. | `services\optimizer-worker\src\optimizer_worker\milp.py:71-75`; `services\bff-api\fixtures\demo-full\heat_batch.ndjson:4` |
| Shift and hold limits | Non-urgent batches may move only inside the configured shift and hold windows. | `services\optimizer-worker\src\optimizer_worker\service.py:68-74`; `services\optimizer-worker\src\optimizer_worker\milp.py:76-84` |
| Feasibility | A proposed plan is acceptable only if the hard rules are satisfied. | `services\optimizer-worker\src\optimizer_worker\service.py:159-190` |

"Zero hard-constraint violations" matters because a cheap schedule that breaks production rules is not a usable schedule. The simulator reports this count and the target is "must be 0" (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:30-35`; `services\optimizer-worker\src\optimizer_worker\service.py:159-216`).

The modelled saving is the euro difference between the baseline schedule and the optimized schedule. For a beginner-friendly example, if flexible load is moved out of a 17:00–20:00 window priced around 280 €/MWh into lower-price hours, the saving is roughly shifted MWh multiplied by the price gap; the screen displays the confirmed result from `rec.savings.costEur` (for example, a few thousand euros such as ~€3.3k in the visible BFF screenshot or ~€4.2k in another equivalent scenario) (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:30-35`; `services\optimizer-worker\src\optimizer_worker\service.py:87-104`; `services\optimizer-worker\src\optimizer_worker\service.py:217-235`).

Recommendations are **shadow/advisory**. The UI records simulated approval only; it does not write an operational schedule or a plant setpoint (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:109-129`; `services\bff-api\src\bff_api\routes.py:305-354`; `contracts\openapi\bff-api-v1.yaml:146-185`).

---

## Spot & Schedule — `/{site}/energy-optimization/spot-price-schedule`

![Spot price and scheduled load screen](../screenshots/energy-optimization-spot-price-schedule.png)

**In one sentence.** This screen compares today's electricity price curve with the planned and optimized load, then lists which reheat batches can move and which urgent batch stays fixed (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:16-114`).

**Steel-industry background (for newcomers).** A reheat batch is a planned heating operation before rolling steel into its final shape. The business problem is that energy is a huge cost line, and the AI infusion point says "**an energy dispatch optimization agent schedules energy-intensive processes around electricity spot prices**" (`docs\usecase\usecase.md:46-50`).

**What you see on screen.**

1. **Global shell and safety banner.** The screenshot shows the NovaSteel top bar, the LU site selector, the left navigation, and a purple banner saying "Synthetic demo data — not for operational control". That banner is intentional demo transparency (`docs\demo\demo-runbook.md:39-45`; `docs\ux\dashboard-specification.md:130-183`).
2. **Persona and page actions.** The page header shows Sofia Lindqvist — Energy Manager, plus buttons such as "Reset layout", "What's this?", "Copilot", and "Start guided demo". The persona and tab names come from the route registry (`apps\analytics-mfe\src\personaRoutes.ts:49-58`).
3. **Tabs.** "Spot & Schedule" is selected; "Load-Shift Simulator" is the second tab. These are the two Energy Optimization subviews (`apps\analytics-mfe\src\personaRoutes.ts:54-58`).
4. **KPI card — Peak price today.** The card shows **280 €/MWh** with "evening scarcity" and "peak ~18:30". Good means the plant avoids running flexible load during that peak; bad means a high-load block sits on the expensive hour (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:34-49`; `apps\analytics-mfe\src\api\fixtures.ts:37-43`).
5. **KPI card — Projected savings.** The card shows a modelled saving and says "simulated / shadow". Read this as a proposal, not a measured invoice saving (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:42-50`; `services\optimizer-worker\src\optimizer_worker\service.py:191-235`).
6. **KPI card — CO₂ intensity.** The card shows average grid intensity, such as **165 gCO₂/kWh**, with a target. Lower is better because each shifted MWh carries less carbon (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:35-48`; `apps\analytics-mfe\src\api\domain.ts:71-86`).
7. **KPI card — Shiftable load.** The card shows **18 MW** within constraints. This is the flexible electrical load the optimizer can consider moving; fixed base load remains in place (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:48`).
8. **Chart — Spot price & scheduled load.** The orange line is electricity price on the right axis; the teal filled area is optimized demand on the left axis; the blue dashed line is the baseline load. In the screenshot, the orange line jumps in the evening and the optimized teal load is lower during that expensive window. Good is a dip in flexible load during high-price hours without creating a new peak elsewhere (`apps\analytics-mfe\src\components\charts\PriceLoadChart.tsx:28-224`; `apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:65-91`).
9. **How to read the dual-axis chart.** The left axis is **MW** (power demand at that moment); the right axis is **€** per MWh. Use the shared time axis: if the orange price line is high and the optimized area is low, the schedule is avoiding expensive energy (`apps\analytics-mfe\src\components\charts\PriceLoadChart.tsx:98-177`).
10. **Schedule table.** The table has a global search box, per-column search fields, proof badges, and columns **Process**, **Grade**, **Window**, **Tonnage**, **€/MWh**, **Shift (min)**, and **Status**. Visible rows include shiftable batches and one "Fixed (urgent)" batch, which is a good sign: the optimizer is respecting production urgency (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:52-111`; `services\optimizer-worker\src\optimizer_worker\milp.py:71-75`).

**Why this component was implemented.** It exists because the brief says: "Energy costs represent 35% of total production cost with no real-time optimization" (`docs\usecase\usecase.md:14-22`). The UX specification makes Energy Optimization the Energy Manager's default area for spot prices, simulated schedules, and CO₂ intensity (`docs\ux\dashboard-specification.md:47-50`; `docs\ux\dashboard-specification.md:697-715`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Energy cost is a major challenge | `CHL-01` | Peak price KPI, price/load overlay, schedule table | `GET /v1/energy/intervals`; `POST /v1/energy/schedules:simulate`; `apps\analytics-mfe\src\api\dataClient.ts:183-202`; `services\bff-api\src\bff_api\routes.py:226-279`; `apps\analytics-mfe\src\proof\proofCatalog.ts:223-244` |
| Reduce energy consumption | `OBJ-01` | Optimized schedule and energy-per-ton proof link | `services\optimizer-worker\src\optimizer_worker\metrics.py:32-39`; `apps\analytics-mfe\src\proof\proofCatalog.ts:337-357` |
| Energy dispatch AI agent | `AI-02` | The screen is mapped to `AI-02`; badges appear on the schedule panel | `services\optimizer-worker\src\optimizer_worker\milp.py:1-145`; `apps\analytics-mfe\src\proof\proofCatalog.ts:546-578` |

**How the data reaches this screen.** `EnergySpotSchedule.tsx` calls `client.getEnergyIntervals()` and `client.simulateEnergy(...)` (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:16-20`). `DataClient` maps those calls to `GET /v1/energy/intervals` and `POST /v1/energy/schedules:simulate`, with deterministic fixture fallback (`apps\analytics-mfe\src\api\dataClient.ts:183-202`). The BFF route sends simulation inputs to `EnergyDispatchOptimizer.simulate()` (`services\bff-api\src\bff_api\routes.py:255-279`; `services\bff-api\src\bff_api\services.py:128-166`). The optimizer uses PuLP/CBC when available and a deterministic heuristic fallback otherwise (`services\optimizer-worker\src\optimizer_worker\service.py:247-330`).

**Honesty & caveats.** The data is synthetic, market prices are fixture values rather than a licensed live feed, and the screen shows predictions/proposals, not measured financial savings (`apps\analytics-mfe\src\api\fixtures.ts:21-29`; `apps\analytics-mfe\src\proof\proofCatalog.ts:223-244`). The UI never writes a schedule or setpoint (`contracts\openapi\bff-api-v1.yaml:146-185`; `docs\ux\dashboard-specification.md:711-715`). Whole-dispatch savings are deliberately more conservative than flexible-only savings because fixed base load is included (`services\optimizer-worker\src\optimizer_worker\service.py:87-94`).

**Try it yourself.** Open `http://localhost:5266/lu/energy-optimization/spot-price-schedule`, look for the 280 €/MWh evening peak, then check whether "Fixed (urgent)" remains fixed in the schedule table (`apps\analytics-mfe\src\personaRoutes.ts:49-58`; `apps\analytics-mfe\src\components\screens\screenRegistry.ts:39-40`).

---

## Load-Shift Simulator — `/{site}/energy-optimization/load-shift-simulator`

![Load-shift simulator screen](../screenshots/energy-optimization-load-shift-simulator.png)

**In one sentence.** This screen lets Sofia change safe scheduling guardrails, run a simulated dispatch, and compare baseline cost and peak demand with the optimized result (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:14-136`).

**Steel-industry background (for newcomers).** A simulator is a safe "what if?" area. The steel plant can ask, "What if I allow shifts up to 180 minutes and at most two batches at once?" without changing a real production schedule (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:17-21`; `apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:109-129`).

**What you see on screen.**

1. **KPI card — Estimated saving (live).** The screenshot shows **11.5%** and "client estimate". This updates immediately when sliders move, using a lightweight client-side heuristic; it is not the final optimizer result (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:23-32`).
2. **KPI card — Confirmed saving.** The screenshot shows a confirmed saving from the BFF optimizer, such as **9%**, with a euro value. This replaces the live estimate after pressing "Simulate schedule" (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:30-35`; `apps\analytics-mfe\src\api\dataClient.ts:190-203`).
3. **KPI card — Peak reduction.** The screenshot shows about **−7.9%** and "lower evening peak". Good means the highest MW demand during the expensive window falls; bad would mean a new operational peak is created (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:33`; `services\optimizer-worker\src\optimizer_worker\service.py:106-135`).
4. **KPI card — Hard violations.** The screenshot shows **0** and "must be 0". Any non-zero value means the proposal is infeasible and should not be approved (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:34`; `services\optimizer-worker\src\optimizer_worker\service.py:159-216`).
5. **Chart — Baseline vs optimized.** The grouped bar chart has two groups: **Cost (k€)** and **Peak (MW)**. Each group compares baseline bars against optimized bars. Lower optimized bars are good if tonnage and constraints remain unchanged (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:43-72`; `apps\analytics-mfe\src\components\charts\BarChart.tsx:28-145`).
6. **How to read a grouped bar chart.** A bar chart compares categories, not time. Here each category is a business metric. The baseline bar answers "what happens if we do nothing?" and the optimized bar answers "what happens under the submitted scenario?" (`apps\analytics-mfe\src\components\charts\BarChart.tsx:88-137`).
7. **Scenario controls.** The side panel shows two sliders: **Max shift window: 180 min** and **Max concurrent batches: 2**. These are guardrails, not commands to equipment (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:77-108`).
8. **Simulate schedule button.** Pressing it commits the slider values to the simulation request and calls the BFF route; it does not commit a plant schedule (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:109-114`; `apps\analytics-mfe\src\api\dataClient.ts:190-203`).
9. **Record simulated approval button.** The screenshot shows this as an outlined button. The source emits a toast saying "Simulated/shadow approval recorded — no operational schedule was written" (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:115-129`). The production-style approval route records a `SIMULATED_APPROVED` audit decision (`services\bff-api\src\bff_api\routes.py:305-354`).
10. **Caption under the buttons.** The screen states: "No UI action writes an operational schedule. Approval is simulated/shadow in the demonstration and pilot phases and is fully audited by the BFF." This is the key safety boundary (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:127-129`).

**Why this component was implemented.** The simulator answers the use-case line "an energy dispatch optimization agent schedules energy-intensive processes around electricity spot prices" (`docs\usecase\usecase.md:46-50`). It also implements the UX requirement for scenario controls, before/after bars, "Simulate schedule", and demonstration/pilot simulated approval (`docs\ux\dashboard-specification.md:711-715`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Constrained energy optimization | `CHL-01` | Slider scenario, confirmed saving, zero hard violations | `POST /v1/energy/schedules:simulate`; `services\optimizer-worker\src\optimizer_worker\service.py:52-235`; `apps\analytics-mfe\src\proof\proofCatalog.ts:223-244` |
| Reduce energy consumption | `OBJ-01` | Baseline vs optimized comparison and tonnage-preserving schedule | `services\optimizer-worker\src\optimizer_worker\service.py:96-104`; `services\optimizer-worker\src\optimizer_worker\metrics.py:32-39`; `apps\analytics-mfe\src\proof\proofCatalog.ts:337-357` |
| Energy dispatch optimization agent | `AI-02` | MILP/CBC or deterministic fallback returns advisory proposal | `services\optimizer-worker\src\optimizer_worker\milp.py:65-145`; `services\optimizer-worker\src\optimizer_worker\service.py:247-330`; `apps\analytics-mfe\src\proof\proofCatalog.ts:546-578` |
| Energy and CO₂ outcome targets | `OUT-01`, `OUT-02` | Modelled saving contributes to target tracking; targets are not claimed as measured | `docs\presentation\proof_of_execution.md:307-338`; `apps\analytics-mfe\src\proof\proofCatalog.ts:415-462` |

**How the data reaches this screen.** `EnergySimulator.tsx` keeps slider state in React, calculates an instant estimate locally, and calls `client.simulateEnergy(committed)` for the confirmed result (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:14-35`). `DataClient.simulateEnergy()` posts `site`, `horizonHours`, `scenario`, and constraints to `POST /v1/energy/schedules:simulate` (`apps\analytics-mfe\src\api\dataClient.ts:94-100`; `apps\analytics-mfe\src\api\dataClient.ts:190-203`). The BFF records an audit row for the simulation output (`services\bff-api\src\bff_api\services.py:128-166`).

**Honesty & caveats.** The scenario is deterministic synthetic data; the example 17:00–20:00 load shift away from a 280 €/MWh peak is modelled, not a verified utility bill (`apps\analytics-mfe\src\api\fixtures.ts:37-43`; `docs\demo\demo-runbook.md:123-133`). The screenshot's saving values depend on whether the live local BFF or frontend fixture fallback is serving the page; both are labelled synthetic/shadow (`apps\analytics-mfe\src\api\dataClient.ts:127-149`). No setpoint, PLC command, furnace recipe, or operational schedule is written (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:127-129`; `contracts\openapi\bff-api-v1.yaml:146-185`).

**Try it yourself.** Open `http://localhost:5266/lu/energy-optimization/load-shift-simulator`, move "Max shift window" from 180 to another value, watch the live estimate change, then click "Simulate schedule" and verify that "Hard violations" remains 0 (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:17-35`; `apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:77-129`).

---

◀ [04 · Furnace health](04-furnace-health.md) · ▲ [Index](README.md) · [06 · Quality](06-quality.md) ▶

