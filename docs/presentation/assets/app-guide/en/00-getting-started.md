# 00 · Getting started

**Audience:** complete newcomers to steelmaking and to the NovaSteel front-end.  
**Reading time:** ~14 minutes.  
**Related routes:** `/lu/command-center/overview`, `/lu/dashboards/collections`, `/lu/company-website/home`, `/lu/proof-of-execution/use-case`.  
**Last updated:** 2026-07-27  
**Language:** 🇫🇷 [Version française](../fr/00-getting-started.md)

---

![Command Center overview](../screenshots/command-center-overview.png)

## What NovaSteel is, in 5 lines

NovaSteel is a demo front-end for an AI-powered steel production optimization platform. Its fictitious operator is AxelorMetal, a Luxembourg steel producer with plants in Luxembourg, Germany, Belgium, and Spain (`docs\usecase\usecase.md:7-10`).

The app helps people understand energy use, carbon emissions, furnace health, steel quality, and expert knowledge capture from one portal (`docs\ux\dashboard-specification.md:24-35`).

It is **advisory-only**: no screen writes a furnace setpoint, a PLC command, or a safety action (`docs\architecture\solution-architecture.md:22-29`).

All data in this guide is **synthetic demo data**. It is useful for learning and proof, not plant control (`docs\architecture\solution-architecture.md:24-27`; `apps\portal-shell\Layout\MainLayout.razor:118-122`).

Where a number is a prediction or a target, the guide says so. A prediction is not the same thing as a measured plant result (`docs\presentation\proof_of_execution.md:317-352`, `docs\presentation\proof_of_execution.md:476-480`).

## Steel making in 3 minutes

| Step | Plain meaning | Why NovaSteel cares |
|---|---|---|
| Iron ore | Rock containing iron. It is the raw mineral input. | It starts the material chain that later becomes steel (`docs\architecture\solution-architecture.md:17-18`). |
| Blast furnace | A tall furnace that turns iron ore, coke, and limestone into hot liquid iron. | Furnace heat and lining wear are central to the 21-day warning use case (`docs\usecase\usecase.md:16-20`). |
| Hot metal | Liquid iron from the blast furnace. It still has too much carbon for most steel uses. | It becomes the input to steel conversion. |
| BOF / converter | Basic Oxygen Furnace. Oxygen is blown into hot metal to reduce carbon and make steel. | Quality and carbon results depend on process stability (`docs\usecase\usecase.md:21`, `docs\architecture\solution-architecture.md:18`). |
| Casting | Liquid steel is solidified into slabs, blooms, or billets. | Genealogy links later defects back to heats and slabs (`docs\personas\personas-and-journeys.md:275-287`). |
| Rolling mill | Heavy rollers shape steel into coil, plate, or long products. | Screens track throughput and quality across rolling assets (`apps\analytics-mfe\src\personaRoutes.ts:27-33`, `apps\analytics-mfe\src\personaRoutes.ts:61-70`). |
| Coil / plate | Finished or near-finished steel products. A coil is a rolled strip wound like a giant roll; plate is flat heavy steel. | Automotive customers care about consistent high-grade output (`docs\usecase\usecase.md:21`). |

A **refractory lining** is the heat-resistant inner wall of a furnace. It protects the steel shell from extreme heat. When it wears too far, a failure can be catastrophic; the use case says such failures cost **€8M per event** (`docs\usecase\usecase.md:20`).

A **heat** is one batch of molten metal processed together. A **batch** is a group of production records handled as one unit. NovaSteel often follows a heat through slab, coil, quality result, and recommendation so users can trace cause and effect (`apps\analytics-mfe\src\personaRoutes.ts:61-70`; `docs\personas\personas-and-journeys.md:275-287`).

Energy and CO₂ dominate the case because steel needs very high temperatures and because EU carbon regulation puts a price on emissions. The brief says energy is **35% of production cost** and CO₂ is under EU ETS pressure (`docs\usecase\usecase.md:18-19`).

## The business problem NovaSteel solves

The brief states: “A Luxembourg-based integrated steel producer operating blast furnaces and rolling mills across four countries” faces five linked problems (`docs\usecase\usecase.md:14-22`).

| Problem in the brief | Beginner translation | Requirement ID evidence |
|---|---|---|
| Energy costs are 35% of production cost | Electricity and fuel are so expensive that small scheduling changes matter. | `CHL-01` (`docs\presentation\proof_of_execution.md:182-208`) |
| CO₂ under EU ETS penalties | The company must manage the cost of carbon allowances. | `CHL-02`, `REG-03` (`docs\presentation\proof_of_execution.md:208-221`, `docs\presentation\proof_of_execution.md:152-154`) |
| Furnace lining failures cost €8M | The company wants warning before a furnace wall becomes dangerous. | `CHL-03` (`docs\presentation\proof_of_execution.md:221-241`) |
| Automotive quality consistency | Car makers need steel grades to be repeatable and traceable. | `CHL-04` (`docs\presentation\proof_of_execution.md:241-259`) |
| Retiring operators | Expert know-how is leaving faster than it is written down. | `CHL-05` (`docs\presentation\proof_of_execution.md:259-276`) |

### Target outcomes from the brief

| Expected outcome | Target | How to read it honestly | Requirement ID |
|---|---:|---|---|
| Energy consumption per ton | −14% | Demo screens show a target/surrogate, not a measured real-plant saving. | `OUT-01` (`docs\usecase\usecase.md:39`, `docs\presentation\proof_of_execution.md:317-328`) |
| CO₂ emissions | −22% | A target based on synthetic evidence; not a live EU ETS filing. | `OUT-02` (`docs\usecase\usecase.md:40`, `docs\presentation\proof_of_execution.md:328-340`) |
| Furnace lining warning | 21 days | The lining forecast demonstrates the mechanism and is marked met. | `OUT-03` (`docs\usecase\usecase.md:41`, `docs\presentation\proof_of_execution.md:340-352`) |
| High-grade steel yield | +8% | A modeled quality target on synthetic batches. | `OUT-04` (`docs\usecase\usecase.md:42`, `docs\presentation\proof_of_execution.md:352-362`) |

## Who uses it

The app is persona-based. A persona is a named role used to decide which screen is most useful first. The canonical names come from the personas document and are mirrored in `personaRoutes.ts` (`docs\personas\personas-and-journeys.md:44-53`, `docs\personas\personas-and-journeys.md:524-525`).

| Persona | Beginner role description | Main section / route |
|---|---|---|
| Marc Weber — Plant Manager | Runs the daily plant and triages trade-offs. | Command Center and Operations (`apps\analytics-mfe\src\personaRoutes.ts:18-33`) |
| Elena Duarte — Furnace Operator | Watches furnace signals during the shift. | Furnace Health (`apps\analytics-mfe\src\personaRoutes.ts:36-46`) |
| Tomás Rossi — Maintenance & Reliability Engineer | Plans inspections and relines from remaining-life risk. | Furnace Health (`apps\analytics-mfe\src\personaRoutes.ts:36-46`) |
| Sofia Lindqvist — Energy Manager | Reviews spot-price and load-shift recommendations. | Energy Optimization (`apps\analytics-mfe\src\personaRoutes.ts:49-58`) |
| Jens Bakker — Quality Engineer | Protects batch quality, genealogy, and SPC. | Quality (`apps\analytics-mfe\src\personaRoutes.ts:61-70`) |
| Amina Haddad — Sustainability Officer | Tracks emissions, ETS exposure, and evidence. | Sustainability & Compliance (`apps\analytics-mfe\src\personaRoutes.ts:73-83`) |
| Pieter Claes — Knowledge Engineer | Reviews captured expertise and publishes procedures. | Knowledge Hub (`apps\analytics-mfe\src\personaRoutes.ts:86-95`) |
| Isabelle Moreau — Executive | Reviews portfolio outcomes and board evidence. | Executive Overview (`apps\analytics-mfe\src\personaRoutes.ts:98-107`) |
| Rui Almeida — OT Systems Engineer | Checks simulated devices and sensor feeds. | Device Operations (`apps\analytics-mfe\src\personaRoutes.ts:110-121`) |
| Nils Andersen — Platform Ops | Manages non-production capacity, jobs, and cost telemetry. | Platform Ops (`apps\analytics-mfe\src\personaRoutes.ts:154-164`) |

## Architecture in one picture-in-words

`Blazor WebAssembly shell → React analytics microfrontend → Python FastAPI BFF → deterministic workers and fixtures → target cloud shape in Microsoft Fabric.`

The Blazor shell owns the global chrome, routing, identity context, locale, theme, and Fabric capacity panel (`apps\portal-shell\README.md:1-6`). The React microfrontend owns data-dense dashboards, KPI cards, D3-style charts, and virtualized tables (`docs\ux\dashboard-specification.md:64-78`). The BFF and domain APIs are Python/FastAPI in the architecture (`docs\architecture\solution-architecture.md:92-101`). Phase 0 uses deterministic simulator/replay assets, not production plant systems (`docs\architecture\solution-architecture.md:32-38`). The target cloud core is Microsoft Fabric: Eventstream, Eventhouse/KQL, OneLake/Lakehouse, semantic model, and Power BI (`docs\architecture\solution-architecture.md:72-86`).

Honesty boundary: this platform never controls a furnace. It supports human decisions and synthetic rehearsal only (`docs\architecture\solution-architecture.md:24-29`; `README.md:35-39`).

## How to run it locally yourself

Use the repository root. Do not add public Python or NuGet package sources. The repository requires Microsoft-protected feeds for Python and NuGet (`README.md:41-55`; `docs\tech\security_requirement.md:5-27`).

```powershell
npm run build:analytics
dotnet restore .\apps\portal-shell\PortalShell.csproj --configfile .\NuGet.Config --locked-mode
npm run build:portal
```

This builds the React bundle and the portal shell (`README.md:102-108`). The shell README says the React library must exist under `wwwroot\analytics-mfe` before serving the Blazor project (`apps\portal-shell\README.md:45-47`).

Start the BFF:

```powershell
npm run run:bff
```

Then verify it:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health/ready
```

Those are the authoritative local BFF commands (`README.md:110-120`).

Start the shell:

```powershell
dotnet run --project .\apps\portal-shell\PortalShell.csproj `
    --launch-profile http `
    --no-restore
```

The root README opens `http://localhost:5266/lu/command-center`; every route in this guide follows the same grammar `http://localhost:5266/{site}/{section}/{subView}`. If you start the shell without the `http` launch profile, .NET may fall back to `http://localhost:5000` — the paths are identical, only the port changes, and the BFF's default CORS list allows both (`README.md:122-134`; `apps\portal-shell\Properties\launchSettings.json:4-10`; `services\bff-api\src\bff_api\config.py:141-146`).

Optional uvicorn example for the standalone device simulator is documented separately; the default web demo runs the device simulator in-process inside the BFF (`README.md:201-216`).

## How to read this guide

| File | What it explains |
|---|---|
| README / LISEZMOI | The guide index and suggested reading paths. |
| 00 Getting started | Steel basics, the use case, personas, local run commands. |
| 01 Shell & navigation | The persistent chrome: top bar, rail, menus, routes, bridge. |
| 02 AxelorMetal public website | The fictitious company website inside the portal. |
| 03 Command Center & Operations | Daily triage, site status, alerts, and next-best actions. |
| 04 Furnace Health | Lining RUL, thermal signatures, and maintenance planning. |
| 05 Energy Optimization | Spot prices, load shifting, and advisory dispatch. |
| 06 Quality | Batch quality, genealogy, defects, SPC, and what-if. |
| 07 Sustainability & Compliance | CO₂ ledger, ETS exposure, audit evidence. |
| 08 Knowledge Hub | Procedure search and GenAI knowledge capture governance. |
| 09 Executive Overview | Portfolio targets, board report, and target-vs-actual roll-up. |
| 10 Device Operations | Simulated device fleet, sensor explorer, and incident controls. |
| 11 Dashboard Collections | Curated journeys that open related screens in order. |
| 12 Proof of Execution | Requirement IDs and evidence trail. |
| 13 Platform Ops | Capacity, jobs, and platform cost telemetry. |
| 14 Cross-cutting features | Dock panels, Copilot, Help, settings, localization, primitives. |
| 15 Glossary | Beginner definitions for steel, industry, platform, and AI terms. |
| 16 Traceability matrix | Screen-to-use-case-to-evidence map. |
| 17 How it works behind the screens | Data flow, adapters, and implementation mechanics. |
| 18 Guided demo walkthrough | Step-by-step rehearsal narrative. |

---

▲ Index ([README.md](README.md)) · Next ▶ [01 · Shell & navigation](01-shell-and-navigation.md)
