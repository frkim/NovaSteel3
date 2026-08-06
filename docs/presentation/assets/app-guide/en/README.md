# NovaSteel — Application guide for newcomers

**What this is.** A complete, screenshot-by-screenshot walkthrough of the **NovaSteel
front-end application**, written for someone who has never worked in the steel industry.
Every screen is explained twice: once in plain language ("what am I looking at?") and
once as evidence ("which line of the business case does this prove, and where does the
number come from?").

**Languages.** 🇬🇧 English (this folder) · 🇫🇷 [Version française](../fr/LISEZMOI.md)

**Last updated:** 2026-07-28 · **Screenshots:** 37, captured from the running
application at `http://localhost:5266` (Blazor portal shell + FastAPI BFF, synthetic
demo data).

---

## The 60-second version

| | |
|---|---|
| **The company** | *AxelorMetal* — a fictitious Luxembourg integrated steel producer running blast furnaces and rolling mills in Luxembourg, Germany, Belgium and Spain. |
| **The platform** | *NovaSteel* — the AI-powered production optimization platform AxelorMetal uses to decide what to do next. |
| **The problem** | Energy is 35 % of production cost; CO₂ is taxed under the EU Emissions Trading System; an unpredicted furnace lining failure costs **€8 M**; high-grade automotive steel quality drifts; and the operators who know how to fix all of this are retiring. |
| **The promise** | −14 % energy per ton, −22 % CO₂, a **21-day** advance warning before a lining failure, +8 points of high-grade yield. |
| **The honest caveat** | All data is **synthetic**. NovaSteel is **advisory-only**: it never writes a setpoint, never talks to a PLC, never touches a safety interlock. |

---

## Read in this order

### Start here

| # | Chapter | What you get |
|---|---|---|
| 00 | [Getting started](00-getting-started.md) | Steel making in 3 minutes, the business problem, the 10 personas, and how to run the app yourself. |
| 01 | [Shell and navigation](01-shell-and-navigation.md) | Every button in the permanent application frame: site selector, persona selector, capacity pill, theme, locale, demo banner, navigation rail. |
| 02 | [AxelorMetal public website](02-company-website.md) | The 5-page corporate site that sets up the story — including *Steel Knowledge*, the best on-ramp for a newcomer. |

### The working screens

| # | Chapter | Persona | Proves |
|---|---|---|---|
| 03 | [Command Center & Operations](03-command-center-and-operations.md) | Plant Manager | Cross-plant triage, the 5 headline KPIs |
| 04 | [Furnace Health](04-furnace-health.md) | Furnace Operator, Maintenance Engineer | `CHL-03`, `OBJ-02`, `OUT-03`, `AI-01` |
| 05 | [Energy Optimization](05-energy-optimization.md) | Energy Manager | `CHL-01`, `OBJ-01`, `AI-02` |
| 06 | [Quality](06-quality.md) | Quality Engineer | `CHL-04`, `OBJ-03`, `OUT-04` |
| 07 | [Sustainability & Compliance](07-sustainability-and-compliance.md) | Sustainability Officer | `CHL-02`, `OUT-02`, `REG-01`…`REG-03` |
| 08 | [Knowledge Hub](08-knowledge-hub.md) | Knowledge Engineer | `CHL-05`, `OBJ-04`, `AI-03` |
| 09 | [Executive Overview](09-executive-overview.md) | Executive | `OUT-01`…`OUT-04` roll-up |
| 10 | [Device Operations](10-device-operations.md) | OT Systems Engineer | Where the sensor data comes from |
| 11 | [Dashboard Collections](11-dashboard-collections.md) | All | Curated, question-driven dashboard bundles |
| 12 | [Proof of Execution](12-proof-of-execution.md) | All | The full requirement register, the brief in-app, and the technical rubric |
| 13 | [Platform Ops](13-platform-ops.md) | Platform Ops | Fabric capacity, jobs, cost |

### Cross-cutting and reference

| # | Chapter | What you get |
|---|---|---|
| 14 | [Cross-cutting features](14-cross-cutting-features.md) | The Dockview workspace, Copilot chat, "What's this?" help, guided tour, settings, theming, localization, shared UI primitives. |
| 15 | [Glossary](15-glossary.md) | Every steel and platform term, EN ↔ FR, with "where you meet it in NovaSteel". |
| 16 | [Traceability matrix](16-traceability-matrix.md) | Screen ↔ use case ↔ requirement ID ↔ evidence ↔ test, for all 31 screens. |
| 17 | [How it works behind the screens](17-how-it-works-behind-the-screens.md) | What happens between a click and a chart: shell, microfrontend, BFF, workers, and the target Fabric architecture. |
| 18 | [Guided demo walkthrough](18-guided-demo-walkthrough.md) | A self-guided tour you can run alone, plus a jury Q&A table and troubleshooting. |

---

## Suggested reading paths

| If you are… | Read |
|---|---|
| **New to steel and to the app** | 00 → 02 → 15 → 03 → 04 → 05 → 06 |
| **Preparing to present or defend it** | 00 → 16 → 12 → 18 → 17 |
| **A developer joining the project** | 17 → 01 → 14 → then the screen chapter you are changing |
| **An auditor or compliance reviewer** | 07 → 08 → 12 → 16 |
| **Short on time (15 minutes)** | 00 §"The 60-second version" → 16 §2 → 18 |

---

## How each screen chapter is structured

Every screen is documented with the same seven blocks, so you always know where to look:

1. **In one sentence** — what the screen is for.
2. **Steel-industry background** — the domain concepts the screen assumes, explained from zero.
3. **What you see on screen** — a numbered walkthrough of every visible panel and widget, with how to read it and what good vs bad looks like.
4. **Why this component was implemented** — the business driver, tied to a quoted line of the use-case brief.
5. **Objective & evidence** — a table mapping the use-case element → requirement ID → evidence in the running app → the API route and source file the number comes from.
6. **Honesty & caveats** — synthetic data, prediction vs measurement, advisory-only.
7. **Try it yourself** — a click path you can follow at `http://localhost:5266`.

---

## Where things live

| Item | Path |
|---|---|
| This guide (English) | `docs/presentation/assets/app-guide/en/` |
| This guide (French) | `docs/presentation/assets/app-guide/fr/` |
| Screenshots (37 PNG) | `docs/presentation/assets/app-guide/screenshots/` |
| Annotated demo cue cards (19 PNG) | `docs/demo/screenshots/` |
| Requirement catalog (source of truth) | `apps/analytics-mfe/src/proof/proofCatalog.ts` |
| Use-case brief | `docs/usecase/usecase.md` |
| Proof-of-execution document | `docs/presentation/proof_of_execution.md` |
| Demo runbook (10-minute script) | `docs/demo/demo-runbook.md` |
| Front-end source | `apps/portal-shell/` (Blazor shell), `apps/analytics-mfe/` (React) |
| Back-end source | `services/bff-api/`, `services/optimizer-worker/`, `services/scoring-worker/`, `services/knowledge-orchestrator/` |

Screenshots are **self-authored captures of this repository's own application** — no
third-party imagery is committed. See [`../../PROVENANCE.md`](../../PROVENANCE.md).

---

## Regenerating the screenshots

The screenshots were captured from the running application, not mocked. To refresh them:

1. Start the BFF: `npm run run:bff` (serves `http://localhost:8080`).
2. Build the React bundle if you changed it: `npm run build:analytics`.
3. Start the shell: `dotnet run --project apps\portal-shell\PortalShell.csproj` (serves `http://localhost:5266`).
4. Visit each route `/{site}/{section}/{subView}` and capture the full page at a 1680 px-wide viewport, saving to `docs/presentation/assets/app-guide/screenshots/<screen-slug>.png`.

Package restores must use the Microsoft-protected feeds only — see
[`docs/tech/security_requirement.md`](../../../../tech/security_requirement.md).

---

▶ Start with [00 · Getting started](00-getting-started.md).
