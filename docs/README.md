# NovaSteel documentation

> **Documentation status:** v1.1 · **Implemented baseline:** local deterministic
> demo, application source, tests/CI, Bicep IaC, and Fabric source assets are
> present and locally validated.  
> **Cloud status:** no Azure, Fabric, Foundry, Speech, Eventstream, or Power BI
> tenant deployment has been performed.  
> **Technical authority:** [solution architecture](architecture/solution-architecture.md)
> and [deployment topology](architecture/deployment-topology.md) · **Freshness:** 2026-07-25

## Executive summary

NovaSteel is an EU-oriented decision-support platform for a four-country steel
estate. The runnable local implementation combines a C# Blazor WebAssembly
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
| Application | Portal shell, analytics MFE, Dockview Copilot chat, BFF routes, authorization stubs, audit hash-chain (durable via Table Storage), simulated capacity control | Entra production validation, cloud query adapters |
| Data/demo | Deterministic simulator, committed fixture, PuLP/CBC MILP optimizer, physics-informed RUL regressor, six persona moments, offline fallback | OT ingestion and non-synthetic data |
| Fabric | Source-controlled item/catalog/KQL/Lakehouse/notebook/pipeline/semantic/RTI assets; local structural validator | Fabric tenant workspace, capacity, item deployment, RLS/query behavior |
| Azure IaC | Bicep, policy, OIDC deployment scripts, alert rules, static validation — **deployed to Sweden Central** | Private-network hardening proof, DR rehearsal |
| Observability | OpenTelemetry traces, JSON logs with correlation_id, four business KPI metrics | Production dashboards and alert tuning |
| AI/knowledge | Consent, draft/review, grounding, restricted tools, critic loop, agent handoff, live GPT-4o adapter with local fallback, screen-aware Copilot chat (5 languages, tool-free, per-tier agents) | Tenant Foundry Agent Service, model/quota, live Speech, private-network proof |
| Defense | 26-slide PowerPoint, runbook, FAQ, scripted rehearsal, response/fallback evidence | Live-cloud rehearsal and presenter-browser screenshots |

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
6. A docked Copilot chat explains what is on screen. `knowledge-orchestrator`
   assembles the grounding — screen profile, glossary, and an optional curated
   public-context corpus — and the chat agents have no tools, so the assistant
   answers about meaning while the dashboard remains the only source of values.

## Reading paths

| Audience | Start here | Then read |
|---|---|---|
| Defense panel / presenter | [Root handoff](../README.md) | [Runbook](demo/demo-runbook.md), [slide plan](presentation/oral-defense-and-slide-plan.md), [FAQ](presentation/faq.md) |
| Product owner | [Requirements](specs/solution-requirements.md) | [Personas](personas/personas-and-journeys.md), [UX specification](ux/dashboard-specification.md) |
| Solution/data architect | [Solution architecture](architecture/solution-architecture.md) | [Deployment topology](architecture/deployment-topology.md), [Fabric assets](../fabric/README.md) |
| Application engineer | [Root quick start](../README.md) | [API contracts](implementation/api-contracts.md), [implementation guide](implementation/implementation-guide.md) |
| Security, DPO, OT, platform engineer | [Security governance](security/security-governance-and-threat-model.md) | [Operations](operations/operations-and-cost.md), [deployment topology](architecture/deployment-topology.md) |
| Data/simulator engineer | [Synthetic-data specification](data/synthetic-data-and-simulators.md) | [Simulator README](../simulator/README.md), [contracts](../contracts) |

## Defense clock and assets

| Clock | Segment | Asset |
|---|---|---|
| 00:00–30:00 | 20-slide architecture and value narrative | [Plan](presentation/oral-defense-and-slide-plan.md) and `presentation\NovaSteel-Oral-Defense.pptx` |
| 30:00–45:00 | Six-moment deterministic persona demo | [Runbook](demo/demo-runbook.md) and `..\artifacts\demo-validation\drive_demo.py` |
| 45:00–60:00 | Moderated FAQ / validation-gate discussion | [FAQ](presentation/faq.md) |

The PowerPoint has 26 slides: 20 primary narrative/demo-handoff slides and six
FAQ backup slides. The package validator found no placeholders and confirms
alignment to the demo transitions.

## Repository/document index

| Area | Primary artifacts |
|---|---|
| Business | [Use case](usecase/usecase.md), [requirements](specs/solution-requirements.md), [personas](personas/personas-and-journeys.md) |
| Architecture | [Solution architecture](architecture/solution-architecture.md), [deployment topology](architecture/deployment-topology.md), [editable diagrams](diagrams/README.md) |
| Implementation | [Root quick start](../README.md), [implementation guide](implementation/implementation-guide.md), [API contracts](implementation/api-contracts.md) |
| Data/Fabric | [Synthetic data](data/synthetic-data-and-simulators.md), [Fabric README](../fabric/README.md), [Fabric research](research/fabric-platform.md) |
| Security/operations | [Security governance](security/security-governance-and-threat-model.md), [operations](operations/operations-and-cost.md), [package-feed policy](tech/security_requirement.md) |
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
5. DPO/Legal/DPIA, retention/deletion, data residency, and EU AI Act decisions.
6. OT vendor/site approval for each DMZ protocol, source, rate, and boundary.
7. Market-data licensing/freshness, immutable service images, DR/performance/
   accessibility testing, and a live-cloud fallback rehearsal.

Use the root handoff's gated deployment sequence only after these conditions are
approved. The protected Python/NuGet feeds remain mandatory in every environment;
no public fallback is permitted.
