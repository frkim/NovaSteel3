# 11 · Dashboard Collections

**Audience:** complete newcomer to steel and NovaSteel  
**Reading time:** 12 minutes  
**Persona:** all personas  
**Routes covered:** `/{site}/dashboards/collections`  
**Last updated:** 2026-07-27  
**Language:** 🇫🇷 [Version française](../fr/11-dashboard-collections.md)

---

## Dashboard Collections — `/{site}/dashboards/collections`
![Dashboard collections](../screenshots/dashboards-collections.png)

**In one sentence.** A curated launcher: six role-scoped dashboard bundles grouped by the question each answers (`apps\analytics-mfe\src\components\screens\DashboardCollections.tsx`; `apps\analytics-mfe\src\components\screens\dashboardCollectionCatalog.ts`).

**Background for newcomers.** NovaSteel has many screens because steel decisions cross energy, carbon dioxide (CO₂), furnace health, quality, knowledge capture, sensors and cloud operations (`docs\ux\dashboard-specification.md`). A beginner should not have to know whether “Thermal Explorer” comes before “Maintenance Planner.” Collections reduce navigation cost, onboard each persona, and make demos reliable by opening evidence in a known order (`DashboardCollections.tsx`; `docs\README.md`).

**What you see on screen.**
1. The heading says collections are ready-to-open sets grouped by question (`DashboardCollections.tsx`).
2. The search field filters title, question, persona, tags, narrative and card text (`DashboardCollections.tsx`).
3. Tag chips such as `audit`, `compliance`, `cost`, `daily`, `energy`, `platform`, `quality`, `reliability` and `root-cause` narrow the cards (`dashboardCollectionCatalog.ts`).
4. Six cards are visible: **Morning shift handover**, **Furnace risk investigation**, **Energy and cost review**, **Quality escape review**, **Compliance evidence pack**, and **Platform health and spend** (`dashboardCollectionCatalog.ts`).
5. The right detail panel shows the selected path. In the screenshot, Morning shift handover opens Command Center, Operations, Device Fleet and Lining Forecast, with **Open** buttons and a **Start** button (`DashboardCollections.tsx`).
6. The grid and detail panel are Dockview panels, inherited from the shared screen layout (`apps\analytics-mfe\src\components\screens\common.tsx`).

**Every collection in the catalog.**

| Collection | Question it answers | Target persona | Screens it opens |
|---|---|---|---|
| Morning shift handover | What changed overnight and what must this shift act on first? | Plant Manager | Command Center → Operations → Device Fleet → Lining Forecast (`dashboardCollectionCatalog.ts`) |
| Furnace risk investigation | Is the lining risk real, and what is driving it? | Maintenance / Reliability Engineer | Lining Forecast → Thermal Explorer → Sensor Explorer → Maintenance Planner (`dashboardCollectionCatalog.ts`) |
| Energy and cost review | Where is the next megawatt-hour of saving, and what does it cost in CO₂? | Energy Manager | Spot & Schedule → Load-Shift Simulator → Emissions Ledger → ETS Exposure (`dashboardCollectionCatalog.ts`) |
| Quality escape review | Which batches are at risk and what is the common cause? | Quality Engineer | Batch Quality → Defect Analytics (SPC) → Sensor Explorer (`dashboardCollectionCatalog.ts`) |
| Compliance evidence pack | Can we prove how every automated recommendation was decided? | Sustainability Officer / Auditor | Audit & Reports → Emissions Ledger → Procedures (`dashboardCollectionCatalog.ts`) |
| Platform health and spend | Is the platform healthy, and what is it costing us? | Platform Ops | Fabric Capacity → Jobs & Pipelines → Simulator Control → Cost & Telemetry (`dashboardCollectionCatalog.ts`) |

**Why this component was implemented.** The brief asks NovaSteel to reduce energy, predict equipment failures, improve quality, and capture expertise (`docs\usecase\usecase.md`). Those proofs span many screens. This launcher turns a 30-screen application into guided journeys for a role, a demo, or an examiner (`docs\ux\dashboard-specification.md`; `docs\demo\demo-runbook.md`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Energy and CO₂ optimization | `CHL-01`, `CHL-02`, `OBJ-01`, `AI-02` | “Energy and cost review” opens energy and sustainability screens | Launcher is static in `dashboardCollectionCatalog.ts`; proving routes include `POST /v1/energy/schedules:simulate` and sustainability routes via `dataClient.ts`. |
| Furnace failure prediction | `CHL-03`, `OBJ-02`, `OUT-03`, `AI-01` | “Furnace risk investigation” orders forecast, thermal, sensors, maintenance | Static catalog; proving route `GET /v1/furnaces/{assetId}/lining-forecast` (`dataClient.ts`; `proofCatalog.ts`). |
| Quality consistency | `CHL-04`, `OBJ-03`, `OUT-04` | “Quality escape review” opens batch quality, SPC and sensors | Proving routes `GET /v1/quality/batches` and `POST /v1/quality/what-if` (`dataClient.ts`; `proofCatalog.ts`). |
| Human oversight and audit | `REG-02`, `REG-03` | “Compliance evidence pack” starts at Audit & Reports | Audit and sustainability routes are documented in `docs\implementation\api-contracts.md`; cards in `dashboardCollectionCatalog.ts`. |
| Platform health and cost | Platform support | “Platform health and spend” opens capacity, jobs, simulator and cost | Capacity route `GET /v1/platform/capacity`; route list in `dashboardCollectionCatalog.ts` and `routes.py`. |

**How the data reaches this screen.** `DashboardCollections.tsx` → `dashboardCollections` and `dashboardCollectionTags` from `dashboardCollectionCatalog.ts` → no BFF route for the launcher. **Start** and **Open** emit `nav.intent` to `/{site}/{section}/{subView}`; the destination screen then calls its own `DataClient` method if needed (`DashboardCollections.tsx`; `apps\analytics-mfe\src\api\dataClient.ts`).

**Honesty & caveats.** Collections prove navigation and onboarding, not the business result by themselves. The evidence remains in the destination screens and in the proof catalog (`apps\analytics-mfe\src\proof\proofCatalog.ts`). Static route lists must be updated if a screen route changes (`dashboardCollectionCatalog.ts`).

**Try it yourself.** Open `http://localhost:5266/{site}/dashboards/collections`, select a card, read the right-hand sequence, then click **Start** or **Open**.

---

[◀ Previous: 10 · Device Operations](10-device-operations.md) · [▲ Index](README.md) · [Next ▶ 12 · Proof of Execution](12-proof-of-execution.md)
