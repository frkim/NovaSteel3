# 10 — Device Operations

**Audience:** complete newcomers to steelmaking, plant telemetry, and OT monitoring  
**Reading time:** 17 minutes  
**Persona:** Rui Almeida, OT Systems Engineer  
**Routes covered:** `/lu/device-operations/fleet`, `/lu/device-operations/sensors`, `/lu/device-operations/simulator`  
**Last updated:** 2026-07-27  
[🇫🇷 Version française](../fr/10-device-operations.md)

Device Operations is the operational technology (OT) layer behind the demo. **OT** means plant-floor technology that monitors physical equipment; **IT** means business information systems. NovaSteel reads simulated OT telemetry so the demo is safe and reproducible. (`docs\ux\dashboard-specification.md`; `docs\data\synthetic-data-and-simulators.md`)

On the Luxembourg site, the fleet has **6 devices** and the sensor table has **34 sensors**. The simulator itself covers all four sites, so Simulator Control shows **17 devices** and **91 sensors**. (`docs\data\synthetic-data-and-simulators.md`; `apps\analytics-mfe\src\api\deviceClient.ts`)

A **sensor** reports a physical value such as temperature, pressure, flow, or heat flux. **Telemetry** is the stream of those readings. **Event time** is when the measurement happened in the simulated plant clock; **ingestion time** is when a system receives it. (`services\bff-api\src\bff_api\routes.py`; `apps\analytics-mfe\src\api\deviceDomain.ts`)

---

## Device Fleet — `/lu/device-operations/fleet`
![Device Operations Fleet](../screenshots/device-operations-fleet.png)

**In one sentence.** This screen summarizes the health of the simulated Luxembourg device fleet that feeds NovaSteel. (`apps\analytics-mfe\src\components\screens\DeviceFleet.tsx`)

**Steel-industry background (for newcomers).** The visible Luxembourg equipment spans ironmaking, steelmaking, casting, rolling, and utilities: blast furnace, basic oxygen furnace, slab caster, reheat furnace, hot strip mill, and energy system. (`docs\data\synthetic-data-and-simulators.md`; `apps\analytics-mfe\src\api\deviceFixtures.ts`)

**What you see on screen.**
1. KPI cards show **Total devices 6**, **Healthy 5**, **Degraded 1**, **Fault / offline 0**, **Mean health score 99.4%**, and **Active incidents 2**. The **Sensors online** card is partly hidden by the dock, but the component computes it from sensor counts. Good means healthy devices, high mean health, and no incidents; bad means degraded, fault, offline, or incident counts rising. (`apps\analytics-mfe\src\components\screens\DeviceFleet.tsx`; `apps\analytics-mfe\src\api\deviceFixtures.ts`)
2. Filters **Site**, **Type**, **Status**, and **Area** narrow the table without a page reload. (`apps\analytics-mfe\src\components\screens\DeviceFleet.tsx`; `docs\ux\dashboard-specification.md`)
3. The **Device fleet** table shows device, area, description, status, sensors, health, uptime %, incidents, and last sample. The first row is **LUX-BF-01**, **Ironmaking**, **Blast furnace**, **degraded**, **11** sensors, **96%** health, **100%** uptime, and **1** incident. (`apps\analytics-mfe\src\components\screens\DeviceFleet.tsx`; `apps\analytics-mfe\src\api\deviceFixtures.ts`)
4. Other visible rows include **LUX-BOF-01**, **LUX-CC-01**, **LUX-HSM-01**, and **LUX-RHF-01**, shown as healthy. (`docs\data\synthetic-data-and-simulators.md`; `apps\analytics-mfe\src\api\deviceFixtures.ts`)
5. The health progress bar is derived from sensor states. Any stale sensor makes a device offline; any alarm makes it fault; any warning makes it degraded; all normal makes it healthy. (`docs\data\synthetic-data-and-simulators.md`; `apps\analytics-mfe\src\api\deviceFixtures.ts`)
6. Clicking a row opens a device-detail sensor list and an **Open in Sensor Explorer** action. (`apps\analytics-mfe\src\components\screens\DeviceFleet.tsx`)

**Why this component was implemented.** It supports the use-case line “A **physics-informed ML model** predicts furnace lining degradation from thermal signatures” by showing whether the device estate producing those signatures is healthy. (`docs\usecase\usecase.md`; `docs\data\synthetic-data-and-simulators.md`)

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| OT foundation for thermal signatures | Supporting evidence for `AI-01`; no direct Device Operations proof badge in `proofCatalog.ts` | Fleet KPIs show 6 LU devices, health, and incidents. | `GET /v1/devices?site=NS-DEMO-LUX-01&size=200`; `apps\analytics-mfe\src\api\deviceClient.ts`; `services\bff-api\src\bff_api\routes.py` |
| Predict equipment failures | Supporting evidence for `OBJ-02` | **LUX-BF-01** is degraded with one incident. | `services\bff-api\src\bff_api\device_adapter.py`; `docs\data\synthetic-data-and-simulators.md` |
| Furnace lining wear story | Supporting evidence for `CHL-03` | The degraded blast-furnace device is the OT source behind Furnace Health. | `apps\analytics-mfe\src\api\deviceFixtures.ts`; `apps\analytics-mfe\src\components\screens\DeviceFleet.tsx` |

**How the data reaches this screen.** `DeviceFleet.tsx` calls `deviceClient.getDevices()` and, after row selection, `deviceClient.getDevice(deviceId)`. `DeviceClient` calls `/v1/devices?site=...&size=200` and `/v1/devices/{deviceId}`. The BFF `DeviceAdapter` reads the in-process device simulator; front-end fixtures are used if the BFF is unavailable. (`apps\analytics-mfe\src\components\screens\DeviceFleet.tsx`; `apps\analytics-mfe\src\api\deviceClient.ts`; `services\bff-api\src\bff_api\routes.py`; `services\bff-api\src\bff_api\device_adapter.py`; `apps\analytics-mfe\src\api\deviceFixtures.ts`)

**Honesty & caveats.** This is a synthetic fleet for a repeatable demo. NovaSteel reads simulated telemetry and never connects to real PLCs, safety interlocks, or actuators. (`docs\data\synthetic-data-and-simulators.md`; `docs\demo\demo-runbook.md`)

**Try it yourself.** Open http://localhost:5266 and click **Device Operations → Device Fleet**, or go to `http://localhost:5266/lu/device-operations/fleet`. (`apps\analytics-mfe\src\components\screens\DeviceFleet.tsx`)

---

## Sensor Explorer — `/lu/device-operations/sensors`
![Device Operations Sensor Explorer](../screenshots/device-operations-sensors.png)

**In one sentence.** This screen lets users search, filter, and chart the individual sensors behind the simulated devices. (`apps\analytics-mfe\src\components\screens\DeviceSensors.tsx`)

**Steel-industry background (for newcomers).** A **signal code** is the technical short name of a measurement, such as `cooling_water_flow` or `local_heat_flux`. A **sample period** tells how often a new reading is expected. (`apps\analytics-mfe\src\api\deviceFixtures.ts`; `apps\analytics-mfe\src\components\devices\deviceFormat.ts`)

**What you see on screen.**
1. Filters show **Device: All devices** and **Status: All statuses**, with global and per-column search boxes. (`apps\analytics-mfe\src\components\screens\DeviceSensors.tsx`)
2. The table shows **1–10 of 34** sensors. Columns include Sensor, Device, Area, Signal code, Value, Unit, Status, Trend, Deviation %, Range, Sample period, and Last sample. (`docs\data\synthetic-data-and-simulators.md`; `apps\analytics-mfe\src\components\screens\DeviceSensors.tsx`)
3. Visible LUX-BF-01 rows include **Cooling Water Flow 281.5 m3/h**, inlet temperature **29.1 Cel**, outlet temperature **51.57 Cel**, hot blast temperature **1,129.5 Cel**, hot metal temperature **1,462.9 Cel**, **Local Heat Flux 165.6 kW/m2**, production rate **284 t/h**, pulverized coal injection **125.2 kg/t**, and top pressure **1.562 bar**. (`apps\analytics-mfe\src\api\deviceFixtures.ts`; `../screenshots/device-operations-sensors.png`)
4. The blue **normal** chip means the value is within its normal band. Trend glyphs show rising, falling, or flat movement. (`apps\analytics-mfe\src\components\devices\deviceFormat.ts`; `apps\analytics-mfe\src\components\screens\DeviceSensors.tsx`)
5. **Deviation %** compares the value with the middle of its configured range. (`apps\analytics-mfe\src\api\deviceFixtures.ts`)
6. Clicking a row opens `SensorChartPanel`, where users can choose line, area, bar, or control chart; select 15m, 1h, 8h, or 24h windows; normalize values to 0–1; enable live polling; and zoom. (`apps\analytics-mfe\src\components\devices\SensorChartPanel.tsx`; `apps\analytics-mfe\src\api\deviceDomain.ts`; `apps\analytics-mfe\src\components\charts\useBrushZoom.ts`)
7. Chart basics: a **line chart** shows change over time; an **area chart** fills the magnitude under a line; a **bar chart** compares sampled points; a **control chart** adds mean, UCL, and LCL so out-of-band points stand out. (`apps\analytics-mfe\src\components\charts\LineChart.tsx`; `apps\analytics-mfe\src\components\charts\AreaChart.tsx`; `apps\analytics-mfe\src\components\charts\BarChart.tsx`; `apps\analytics-mfe\src\components\charts\ControlChart.tsx`)

**Why this component was implemented.** It lets users inspect the raw signals behind the phrase “thermal signatures” before trusting a forecast. (`docs\usecase\usecase.md`; `apps\analytics-mfe\src\components\screens\DeviceSensors.tsx`)

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Thermal signatures for physics-informed ML | Supporting evidence for `AI-01`; no direct Device Operations proof badge in `proofCatalog.ts` | Sensor table exposes cooling, heat, pressure, and production signals. | `GET /v1/devices/sensors?site=NS-DEMO-LUX-01&size=200`; `apps\analytics-mfe\src\api\deviceClient.ts`; `services\bff-api\src\bff_api\routes.py` |
| Predict equipment failures | Supporting evidence for `OBJ-02` | Row click opens a time-series chart for drift investigation. | `GET /v1/devices/sensors/{sensor_id}/series?window=...&points=120`; `apps\analytics-mfe\src\components\devices\SensorChartPanel.tsx` |
| Furnace lining wear story | Supporting evidence for `CHL-03` | LUX-BF-01 includes heat flux, refractory estimate, cooling temperatures, and shell temperature signals. | `apps\analytics-mfe\src\api\deviceFixtures.ts`; `docs\data\synthetic-data-and-simulators.md` |

**How the data reaches this screen.** `DeviceSensors.tsx` calls `deviceClient.getSensors()`. `DeviceClient` calls `/v1/devices/sensors?site=...&size=200`; when a row is selected, `SensorChartPanel` calls `/v1/devices/sensors/{sensor_id}/series?window=...&points=120`. The BFF filters rows by plant scope and site. (`apps\analytics-mfe\src\components\screens\DeviceSensors.tsx`; `apps\analytics-mfe\src\components\devices\SensorChartPanel.tsx`; `apps\analytics-mfe\src\api\deviceClient.ts`; `services\bff-api\src\bff_api\routes.py`)

**Honesty & caveats.** The signals are simulated. The **approach-band rule** classifies sensors as normal, warning, alarm, or stale: inner 90% of range is normal, within 5% of a limit is warning, beyond a limit by more than 5% is alarm, and bad or old samples are stale. (`docs\data\synthetic-data-and-simulators.md`; `apps\analytics-mfe\src\api\deviceFixtures.ts`)

**Try it yourself.** Open http://localhost:5266 and click **Device Operations → Sensor Explorer**, or go to `http://localhost:5266/lu/device-operations/sensors`. (`apps\analytics-mfe\src\components\screens\DeviceSensors.tsx`)

---

## Simulator Control — `/lu/device-operations/simulator`
![Device Operations Simulator Control](../screenshots/device-operations-simulator.png)

**In one sentence.** This screen controls the deterministic simulator and injects the catalogued fault incidents that drive the demo. (`apps\analytics-mfe\src\components\screens\DeviceSimulator.tsx`; `apps\analytics-mfe\src\components\devices\SimulatorControls.tsx`; `apps\analytics-mfe\src\components\devices\IncidentPanel.tsx`)

**Steel-industry background (for newcomers).** A **fault incident** is a controlled abnormal scenario. **Determinism** means the same seed and scenario produce the same readings every time; a **seed** is the starting number for that repeatable sequence. (`docs\data\synthetic-data-and-simulators.md`; `services\bff-api\src\bff_api\device_adapter.py`)

**What you see on screen.**
1. KPI cards show **Simulator state running**, **Scenario demo-full**, **Speed 1×**, **Elapsed hours 2.4 h**, **Ticks 1759**, and **Active incidents 2**. (`apps\analytics-mfe\src\components\screens\DeviceSimulator.tsx`; `services\bff-api\src\bff_api\device_adapter.py`)
2. The control panel shows state **running**, simulated clock **Jul 25, 2024, 10:26 AM**, elapsed **2.4 h**, **1,759** ticks, **17** devices, and **91** sensors. This is the full four-site simulator, not just Luxembourg. (`docs\data\synthetic-data-and-simulators.md`; `apps\analytics-mfe\src\components\devices\SimulatorControls.tsx`)
3. Controls include **Scenario demo-full**, **Speed 1×**, seed **240726**, and **Start**, **Pause**, **Resume**, **Stop**, **Reset** buttons. Buttons depend on simulator state and `Platform.Capacity.Manage` permission. (`apps\analytics-mfe\src\components\devices\SimulatorControls.tsx`; `services\bff-api\src\bff_api\routes.py`)
4. **Active incidents** lists **Accelerated hearth lining wear** on **LUX-BF-01** with high severity and about **3 min remaining**, plus **Day-ahead energy price spike** on **LUX-UTIL-01** with medium severity and about **18 min remaining**. (`apps\analytics-mfe\src\components\devices\IncidentPanel.tsx`; `docs\data\synthetic-data-and-simulators.md`)
5. **Available incidents** cards show the seven catalogued incidents: lining wear, cooling water loss, sensor drift, sensor dropout, energy price spike, quality drift, and edge outage/recovery. (`apps\analytics-mfe\src\api\deviceFixtures.ts`; `docs\data\synthetic-data-and-simulators.md`)
6. Some incidents have default targets; generic incidents open a target-selection dialog. (`apps\analytics-mfe\src\components\devices\IncidentPanel.tsx`)

**Why this component was implemented.** The demo needs repeatable abnormal behavior to prove the AI story safely, especially the 21-day lining warning scenario. (`docs\usecase\usecase.md`; `docs\data\synthetic-data-and-simulators.md`; `services\bff-api\src\bff_api\device_adapter.py`)

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Physics-informed ML input stream | Supporting evidence for `AI-01`; no direct Device Operations proof badge in `proofCatalog.ts` | Simulator exposes reproducible sensor signals and incidents. | `GET /v1/devices/simulator`; `services\bff-api\src\bff_api\routes.py`; `services\bff-api\src\bff_api\device_adapter.py` |
| Predict equipment failures | Supporting evidence for `OBJ-02` | `degrading-furnace` creates the lining-wear conditions. | `POST /v1/devices/incidents`; `apps\analytics-mfe\src\api\deviceFixtures.ts`; `docs\data\synthetic-data-and-simulators.md` |
| 21-day warning demo | Supporting evidence for `OUT-03` | The `demo-full` scenario (seed `240726`) seeds the degrading-furnace incident. | `services\bff-api\src\bff_api\device_adapter.py`; `docs\data\synthetic-data-and-simulators.md` |

**How the data reaches this screen.** `DeviceSimulator.tsx` calls `deviceClient.getSimulator()` and polls every 5 seconds while running. Buttons call `POST /v1/devices/simulator/commands`; triggers call `POST /v1/devices/incidents`; **Clear** calls `DELETE /v1/devices/incidents/{activeIncidentId}`. (`apps\analytics-mfe\src\components\screens\DeviceSimulator.tsx`; `apps\analytics-mfe\src\api\deviceClient.ts`; `services\bff-api\src\bff_api\routes.py`; `apps\analytics-mfe\src\components\devices\SimulatorControls.tsx`; `apps\analytics-mfe\src\components\devices\IncidentPanel.tsx`)

**Honesty & caveats.** The simulator controls only an in-memory ring buffer inside the BFF. It has no path to real OT, no PLC connection, no safety-interlock connection, and no actuator path. (`docs\demo\demo-runbook.md`; `docs\data\synthetic-data-and-simulators.md`; `services\bff-api\src\bff_api\device_adapter.py`)

**Try it yourself.** Open http://localhost:5266 and click **Device Operations → Simulator Control**, or go to `http://localhost:5266/lu/device-operations/simulator`. (`apps\analytics-mfe\src\components\screens\DeviceSimulator.tsx`)

---

[◀ Previous: Executive Overview](09-executive-overview.md) | [▲ Index](README.md) | [Next ▶ Dashboard Collections](11-dashboard-collections.md)
