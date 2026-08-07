# NovaSteel documentation

> **Documentation status:** v1.4 · **Implemented baseline:** local deterministic
> demo, application source, tests/CI, Bicep IaC, and Fabric source assets are
> present and locally validated.  
> **Cloud status:** the application is deployed to Azure Container Apps (Sweden
> Central) and the Fabric demo estate is deployed to workspace
> `NovaSteelV3-Demo` — two lakehouses, an Eventhouse/KQL database, medallion
> notebooks, pipelines, and the `es-ns-telemetry-v1` Eventstream with verified
> end-to-end ingestion. The F2 capacity is **paused outside demonstration
> windows** for cost control, so live Fabric reads fall back to the committed
> fixture pack and say so. No Power BI report or Direct Lake semantic model has
> been published into this workspace yet.  
> **Technical authority:** [solution architecture](architecture/solution-architecture.md)
> and [deployment topology](architecture/deployment-topology.md) · **Freshness:** 2026-07-30

> **Layout note (2026-07-30):** the Marp deck source that used to sit in the
> repository-root `presentation/` folder now lives with the rest of the defense
> material in [`docs/presentation/`](presentation/README.md). There is no
> top-level `presentation/` directory any more; `tools/presentation/` (PptxGenJS
> deck generator) and `tests/presentation/` (deck validation) are unchanged.

## Wave 10 summary — Fabric data streams and a single data path

Wave 10 (completed 2026-07-29) made Fabric hold real NovaSteel data and removed
the user-facing data-source mode choice:

- **Two data streams into Fabric** — a deterministic 24-month *static analytical*
  stream (eight `fact_*` gold Delta tables in `lh_novasteelv3_core`, plus nine
  operational envelope tables and a `manifest` table at the application grain)
  and a *dynamic real-time* stream (simulator → `es-ns-telemetry-v1` Eventstream
  → five Eventhouse hot tables and `bronze_event_envelope` in parallel). See
  §11.1, [synthetic-data-and-simulators.md](data/synthetic-data-and-simulators.md)
  and ADR-018, [solution-architecture.md](architecture/solution-architecture.md).
- **The BFF can read from Fabric** — `BFF_DATA_SOURCE=fabric` reads the lakehouse
  SQL analytics endpoint through a managed identity; a paused capacity is a soft
  failure that falls back to the fixture pack. `GET /v1/meta` now reports
  `dataSource`, so every screen can state whether rows came from Fabric, the
  fixture pack, or a fallback.
- **The DEMO/CLOUD toggle is gone** — the portal is always BFF-backed, a startup
  probe surfaces reachability as a connection indicator, and the synthetic-data
  banner is now **unconditional** rather than switchable (ADR-017).
- **Gold contract v2** — `contracts/data/gold.v2.json` declares the natural keys
  the tables actually use instead of surrogate `*_key` columns that no dimension
  load produces, and the validator now enforces the contract rather than a
  hard-coded column list.
- **Verification** — 1113 Python tests, 30 MFE test files, clean `dotnet build`
  and `tsc`, and a passing protected-feed scan over 619 files.

## Wave 4 summary

Wave 4 (completed 2026-07-27) added the following front-end experience
capabilities:

- **Dockview workspace on every screen** — every analytics route now renders
  through an inner Dockview workspace, with an outer Dockview host for Copilot
  when chat is open. Panels are derived from each screen's JSX, structural panels
  are non-closable, operator arrangements persist per screen, and the dashboard
  header can reset the layout (§9.7 and §22, [dashboard-specification.md](ux/dashboard-specification.md);
  §5.1.1 and ADR-014, [solution-architecture.md](architecture/solution-architecture.md)).
- **AxelorMetal corporate website** — a new `company-website` section presents
  the fictitious steel producer that operates the plant and uses NovaSteel. Its
  Home, Company, Products & Markets, Steel Knowledge, and Contact pages are
  localized in the five product locales and are docked as full-bleed,
  non-closable panels (§12.11, [dashboard-specification.md](ux/dashboard-specification.md)).
- **Front-end verification** — `dock.test.tsx` (13 tests) and
  `CompanyWebsite.test.tsx` (9 tests) cover panel derivation, layout behavior,
  tab labels, and the localized website route set. The wave-4 front-end suite is
  120 tests across 14 files, with `npx tsc -b --force` clean.

## Wave 3 summary and closed analysis findings

Wave 3 (completed 2026-07-26) added the following capabilities; all are now
documented:

- **Device Operations** — 6-device, 34-sensor deterministic fleet simulator
  running in-process inside the BFF; Device Fleet, Sensor Explorer, and Device
  Simulator UI screens; 7 fault-incident catalog; approach-band sensor status
  rule (§13, [synthetic-data-and-simulators.md](data/synthetic-data-and-simulators.md);
  §5.4 and ADR-013, [solution-architecture.md](architecture/solution-architecture.md)).
- **Dashboard Collections** — 6 predefined role-scoped dashboard bundles
  (screen S-23, [dashboard-specification.md](ux/dashboard-specification.md)).
- **GDPR Art. 17 erasure** — 4-store targeting (hard delete / pseudonymization /
  tombstone); hash-chained audit log invariant preserved through erasure
  (§25.1, [security-governance-and-threat-model.md](tech/security-governance-and-threat-model.md)).
- **Grounded RAG with safety pipeline** — hybrid BM25+cosine retrieval, RRF
  fusion, content-term overlap guard, citation enforcement, PII redaction,
  dual Azure Content Safety screens, structured decline (FR-KNW-08;
  §4.7, [api-contracts.md](tech/api-contracts.md)).

Two findings from `docs/_upgrade/` are now **closed**:

| Finding | Status | Implementing artifacts |
|---|---|---|
| Medallion (bronze/silver/gold) pattern missing | **Closed** | `fabric/notebooks/ns-bronze-to-silver.Notebook`, `fabric/notebooks/ns-silver-to-gold.Notebook`, `fabric/kql/dashboard-queries.kql` |
| Fabric Real-Time Intelligence (RTI) missing | **Closed** | `fabric/rti/activator-rules.template.json`, `fabric/rti/dashboard-spec.json` |

All remaining `docs/_upgrade/` items addressed in wave 3 are noted in
§14 of [solution-architecture.md](architecture/solution-architecture.md).

## Executive summary

NovaSteel is an EU-oriented decision-support platform for AxelorMetal's
four-country steel estate. The runnable local implementation combines a C#
Blazor WebAssembly
shell, React/TypeScript MUI/D3 dashboard, Python/FastAPI BFF, deterministic
optimizer/scoring/knowledge workflows, and synthetic simulator fixtures. The
target cloud architecture remains Fabric-centered: Eventstream/Eventhouse for
hot operations, OneLake/Lakehouse for governed history, Direct Lake/Power BI
for semantic reporting, and managed-identity services for integration and AI.

The local defense is intentionally synthetic and advisory-only. It does not
connect to production OT, PLCs, safety interlocks, furnaces, recipe/setpoint
systems, CMMS, or production schedules.

## Current delivery state

| Area | Implemented and evidenced | Not yet deployed/proven |
|---|---|---|
| Application | Portal shell, analytics MFE (including Device Fleet, Sensor Explorer, Device Simulator, Dashboard Collections, Dockview workspace, and AxelorMetal corporate website screens), Dockview Copilot chat, BFF routes, authorization stubs, audit hash-chain (durable via Table Storage), simulated capacity control | Entra production validation, cloud query adapters |
| Data/demo | Deterministic simulator, committed fixture, PuLP/CBC MILP optimizer, physics-informed RUL regressor, six persona moments, offline fallback | OT ingestion and non-synthetic data |
| Fabric | Source-controlled item/catalog/KQL/Lakehouse/notebook/pipeline/semantic/RTI assets; local structural validator | Fabric tenant workspace, capacity, item deployment, RLS/query behavior |
| Azure IaC | Bicep, policy, OIDC deployment scripts, alert rules, static validation — **deployed to Sweden Central** | Private-network hardening proof, DR rehearsal |
| Observability | OpenTelemetry traces, JSON logs with correlation_id, four business KPI metrics | Production dashboards and alert tuning |
| AI/knowledge | Consent, draft/review, grounding, restricted tools, critic loop, agent handoff, live GPT-5-series adapter with local fallback, AI Search procedure store, Foundry IQ knowledge base, hosted Agent Service procedure agent, screen-aware Copilot chat (5 languages, tool-free, per-tier agents incl. high-reasoning) | Tenant Agent Service capability host, model/quota, live Speech, private-network proof |
| Defense | 28-slide PowerPoint, Marp deck source, runbook, FAQ, scripted rehearsal, response/fallback evidence | Live-cloud rehearsal and presenter-browser screenshots |

The rehearsal passed 66/66 BFF checks and 12/12 offline-fallback checks; 571
automated tests and all 19 validation gates pass — 8 contract, 60 simulator, 112
backend/integration, 230 knowledge/Copilot, 47 frontend, and 114 infrastructure.
See [the rehearsal report](../artifacts/demo-validation/rehearsal-report.md),
[final handoff](../artifacts/final-handoff.md), and the root
[`README.md`](../README.md) for exact commands and the live endpoint URLs.

## Architecture at a glance

1. Per-plant industrial-DMZ gateways validate and buffer outbound telemetry.
2. Azure Event Hubs buffers the target ingress; a managed-identity relay is the
   intended Fabric Eventstream Custom Endpoint publisher.
3. Fabric is the target analytics core: Eventhouse/KQL for hot operations,
   OneLake/Lakehouse bronze-silver-gold for governed data, and Direct Lake/Power
   BI for semantic reporting.
4. Python services calculate RUL, quality, and dispatch results. Dispatch is a
   PuLP/CBC mixed-integer program and RUL is an OLS regression over thermal
   features, so both respond to their inputs rather than restating constants.
   Foundry agents can only explain/retrieve/propose through restricted tools,
   with a critic loop and a dispatch↔RUL handoff between them.
5. Adapters select their Azure implementation when configuration is present and
   fall back to deterministic, checksummed synthetic fixtures otherwise, so the
   API and contract boundaries are identical in both modes.
6. The React MFE is a Dockview workspace. Screen panels are derived from the JSX
   each route already declares, and a two-level dock keeps the Copilot chat
   mounted while the current workspace changes. `knowledge-orchestrator`
   assembles the chat grounding — screen profile, glossary, and an optional
   curated public-context corpus — and the chat agents have no tools, so the
   assistant answers about meaning while the dashboard remains the only source
   of values.

## Reading paths

| Audience | Start here | Then read |
|---|---|---|
| Newcomer to the app or to steel making | [Illustrated application guide (EN)](presentation/assets/app-guide/en/README.md) / [(FR)](presentation/assets/app-guide/fr/LISEZMOI.md) | [Use case](usecase/usecase.md), [proof of execution](presentation/proof_of_execution.md) |
| Defense panel / presenter | [Root handoff](../README.md) and the [defense material index](presentation/README.md) | [Proof of execution](presentation/proof_of_execution.md), [technical analysis](tech/technical-analysis.md), [runbook](demo/demo-runbook.md), [slide plan](presentation/archives/oral-defense-and-slide-plan.md), [FAQ](presentation/faq.md) |
| Product owner | [Requirements](business/solution-requirements.md) | [Personas](business/personas-and-journeys.md), [UX specification](ux/dashboard-specification.md) |
| Solution/data architect | [Solution architecture](architecture/solution-architecture.md) | [Deployment topology](architecture/deployment-topology.md), [Fabric assets](../fabric/README.md) |
| Application engineer | [Root quick start](../README.md) | [API contracts](tech/api-contracts.md), [implementation guide](implementation/implementation-guide.md) |
| Security, DPO, OT, platform engineer | [Security governance](tech/security-governance-and-threat-model.md) | [Operations](operations/operations-and-cost.md), [deployment topology](architecture/deployment-topology.md), [compliance analyses](business/compliance/README.md) |
| Programme manager / delivery lead | [Implementation process](business/implementation-process.md) | [Agentic development and SDLC](business/agentic-development.md), [compliance roadmap](business/compliance/compliance-roadmap.md) |
| Data/simulator engineer | [Synthetic-data specification](data/synthetic-data-and-simulators.md) | [Simulator README](../simulator/README.md), [contracts](../contracts) |

## Defense clock and assets

| Clock | Segment | Asset |
|---|---|---|
| 00:00–35:00 | Architecture, value and compliance narrative | [Plan](presentation/archives/oral-defense-and-slide-plan.md) and `docs\presentation\archives\NovaSteel-Oral-Defense.pptx` |
| 35:00–45:00 | Six-moment deterministic persona demo | [Runbook](demo/demo-runbook.md) and `..\artifacts\demo-validation\drive_demo.py` |
| 45:00–60:00 | Moderated FAQ / validation-gate discussion | [FAQ](presentation/faq.md), [proof of execution](presentation/proof_of_execution.md) and [technical analysis](tech/technical-analysis.md) |

The delivered PowerPoint has 28 slides: 20 primary narrative/demo-handoff slides
and eight FAQ backup slides. The package validator found no placeholders and
confirms alignment to the demo transitions.

The same narrative is also maintained as Markdown in
[`presentation/slides.md`](presentation/slides.md) and rebuilt autonomously with
[Marp](https://marp.app/) — 22 timed main slides plus 14 FAQ/appendix backups —
by the `Presentation` workflow, which publishes the HTML deck, both PDFs and the
PPTX. See the [presentation folder index](presentation/README.md).

## Repository/document index

| Area | Primary artifacts |
|---|---|
| **Artifact set (one-page summaries)** | [Artifact index](artifacts/README.md) — [glossary](artifacts/glossary.md), [diagrams](artifacts/diagrams/README.md), [solution architecture](artifacts/solution-architecture.md), [data baseline](artifacts/data-baseline.md), [AI design](artifacts/ai-design.md), [security baseline](artifacts/security-baseline.md), [compliance](artifacts/compliance.md), [operating model](artifacts/operating-model.md), [test strategy](artifacts/test-strategy.md), [business value](artifacts/business-value-assessment.md) |
| Business | [Use case](usecase/usecase.md), [requirements](business/solution-requirements.md), [personas](business/personas-and-journeys.md) |
| Business & compliance | [Regulatory compliance analyses](business/compliance/README.md) — [EU AI Act](business/compliance/eu-ai-act.md), [EU ETS](business/compliance/eu-ets.md), [IEC 62443](business/compliance/iec-62443.md), [other regulations](business/compliance/other-regulations.md), [roadmap](business/compliance/compliance-roadmap.md) |
| Delivery method | [Implementation process](business/implementation-process.md), [agentic development and SDLC](business/agentic-development.md) |
| Architecture | [Solution architecture](architecture/solution-architecture.md), [deployment topology](architecture/deployment-topology.md), [editable diagrams](architecture/diagrams/README.md) |
| Implementation | [Root quick start](../README.md), [implementation guide](implementation/implementation-guide.md), [API contracts](tech/api-contracts.md) |
| Data/Fabric | [Synthetic data](data/synthetic-data-and-simulators.md), [Fabric README](../fabric/README.md), [Fabric research](research/fabric-platform.md), [Fabric-Brain mapping](architecture/fabric-brain-mapping.md) |
| Experience | [Illustrated application guide](presentation/assets/app-guide/en/README.md), [UX spec §9.7](ux/dashboard-specification.md#97-dockview-workspace-model-all-screens), [UX spec §12.11](ux/dashboard-specification.md#1211-axelormetal-corporate-website-company-website-s-24), [Solution architecture ADR-014](architecture/solution-architecture.md#adr-014--two-level-dockview-workspace-with-jsx-derived-panels) |
| Defense / presentation | [Folder index](presentation/README.md), [slide plan](presentation/archives/oral-defense-and-slide-plan.md), [FAQ](presentation/faq.md), [proof of execution](presentation/proof_of_execution.md), [Marp deck source](presentation/slides.md), [French executive summary](presentation/resume-executif-fr.md) |
| Device Operations | [Synthetic data §13](data/synthetic-data-and-simulators.md#13-device-simulator-estate), [UX spec §12.9–12.10](ux/dashboard-specification.md), [API contracts §4.12](tech/api-contracts.md#412-device-operations), [Operations §12](operations/operations-and-cost.md) |
| Security/operations | [Security governance](tech/security-governance-and-threat-model.md), [operations](operations/operations-and-cost.md), [package-feed policy](tech/security_requirement.md) |
| Rating grid | [Rubric](usecase/rating_grid.md), [technical analysis](tech/technical-analysis.md), in-app **Technical Requirements** screen (`/{site}/technical-requirements/criteria`) |
| Validation | [Validation report](validation-report.md), [local evidence](../artifacts/validation/final/evidence-manifest.json), [rehearsal report](../artifacts/demo-validation/rehearsal-report.md) |

## Remaining production gates

The local baseline does not establish a production claim. Before a cloud
deployment or any non-synthetic pilot, clear the following:

1. Fabric capacity/SKU/quota and regional support in the target tenant.
2. Eventstream Custom Endpoint managed-identity publishing, isolated
   Contributor scope, tenant switches, and permitted network paths.
3. Foundry model/deployment/Agent Service/Speech availability, quota, identity,
   evaluation, and private-network behavior.
4. Entra, Fabric workspace/OneLake/item-level authorization and Power BI RLS.
5. DPO/Legal/DPIA, retention/deletion, data residency, and EU AI Act decisions —
   see the [compliance roadmap](business/compliance/compliance-roadmap.md).
6. OT vendor/site approval for each DMZ protocol, source, rate, and boundary.
7. Market-data licensing/freshness, immutable service images, DR/performance/
   accessibility testing, and a live-cloud fallback rehearsal.

Use the root handoff's gated deployment sequence only after these conditions are
approved. The protected Python/NuGet feeds remain mandatory in every environment;
no public fallback is permitted.
