# NovaSteel — Fabric-Brain Agent Mapping and Deployment Sequence

> **Status:** Informational mapping document v1.0  
> **Date:** 2026-07-28  
> **Scope:** Documentation only. No code, Fabric item definition, or application file is
> modified by this document. No OT/PLC write is authorised at any stage.  
> **Owning workstream:** `solution-architecture`  
> **Companion documents:** [solution-architecture.md](solution-architecture.md),
> [deployment-topology.md](deployment-topology.md),
> [Fabric assets](../../fabric/README.md)

> **Safety note:** Nothing in this document authorises writing to a PLC, safety
> interlock, furnace recipe, production setpoint, or CMMS work-order commit.
> Microsoft Fabric is decision-support infrastructure; OT safety systems remain
> authoritative at every phase described below.

---

## 1. Executive summary

NovaSteel3 already has a complete **Fabric source-asset tree** (`fabric/items/`,
`fabric/kql/`, `fabric/lakehouse/`, `fabric/notebooks/`, `fabric/pipelines/`,
`fabric/semantic-model/`, `fabric/rti/`, `fabric/powerbi/`) and an isolated
demo workspace binding (`.azure/fabric/`). None of these assets has been deployed
to a real Fabric tenant — the [remaining production gates](../README.md#remaining-production-gates)
and the "Known limitations" section of the root `README.md` are explicit about
this.

**Azure-Brain / Fabric-Brain** (https://github.com/Statyx/Azure-Brain) is an
external catalogue of 26 specialised Fabric agents covering 10 capability
domains. Its **"RTI Operations / Digital Twin"** template in
`Meta-Brain/TEMPLATES.md` matches the NovaSteel steel-plant scenario almost
exactly: IoT/OT ingestion, Eventhouse/KQL operations store, OneLake medallion,
Direct Lake semantic model, Power BI reporting, and a Fabric IQ Ontology /
GraphModel-backed AI layer.

This document:

- Maps every NovaSteel3 Fabric asset and remaining gate to the responsible
  Fabric-Brain agent.
- Identifies four capability gaps where Fabric-Brain adds functionality that
  NovaSteel3 does not yet have.
- Proposes a three-phase deployment sequence that references existing scripts and
  follows the gate ordering already defined in `fabric/catalog/fabric-items.json`
  and `fabric/deployment-parameters/novasteelv3.items-manifest.json`.

**Out of scope for this document:**

- Any write to OT, PLC, or production setpoints — permanently out of scope for
  the Fabric layer.
- Data from real furnaces, sensors, or historians. All data is and remains
  **SYNTHETIC** (`dataClassification: "SYNTHETIC"` in `.azure/fabric/`).
- Deployment to a `prod`-labelled environment (hard-denied in every lifecycle
  script).
- Modification of any file under `fabric/items/`, `fabric/notebooks/`,
  `fabric/pipelines/`, `fabric/semantic-model/`, `contracts/`, `infra/`, or any
  application-service source.

---

## 2. Inventory of current NovaSteel3 Fabric assets

The tables below are derived from
`fabric/catalog/fabric-items.json` (shared item catalogue),
`fabric/deployment-parameters/novasteelv3.items-manifest.json` (isolated
demo workspace manifest), and a directory scan of the `fabric/` tree.
**No items have been invented** — every row corresponds to an artefact that
exists in the repository.

### 2.1 Automated items (deployable after tenant gate)

| Item key | Display name (novasteelv3 workspace) | Fabric type | Source file(s) | Automation tier | Blocking gate |
|---|---|---|---|---|---|
| `eventhouseOperations` | `evh-novasteelv3-operations` | Eventhouse | `items/evh-ns-operations.Eventhouse/.platform` | REST (create without definition) | Workspace assigned to running F2 capacity |
| `landingLakehouse` | `lh_novasteelv3_landing` | Lakehouse | `items/lh-ns-landing.Lakehouse/.platform` | REST (create without definition) | OneLake security roles + sensitivity label applied; no cross-workspace shortcut |
| `coreLakehouse` | `lh_novasteelv3_core` | Lakehouse | `items/lh-ns-core.Lakehouse/.platform` | REST (create without definition) | Same as above + notebook identity least-privilege confirmed |
| `kqlOperations` | `kql-novasteelv3-operations` | KQLDatabase | `items/kql-ns-operations.KQLDatabase/DatabaseProperties.json`, `DatabaseSchema.kql`, `.platform` | REST + Fabric CLI (cliDeployable) | Eventhouse running; retention/cache cost validated |
| `notebookInitialize` | `v3-initialize-lakehouses` | Notebook | `notebooks/ns-initialize-lakehouses.Notebook/notebook-content.py`, `.platform` | REST + CLI | Lakehouse identities attached |
| `notebookBronzeToSilver` | `v3-bronze-to-silver` | Notebook | `notebooks/ns-bronze-to-silver.Notebook/notebook-content.py`, `.platform` | REST + CLI | SCD joins, unit registry, watermark, and replay validated on a fixed batch |
| `notebookSilverToGold` | `v3-silver-to-gold` | Notebook | `notebooks/ns-silver-to-gold.Notebook/notebook-content.py`, `.platform` | REST + CLI | KPI definitions signed off by business owners |
| `notebookDemoScoring` | `v3-deterministic-demo-scoring` | Notebook | `notebooks/ns-deterministic-demo-scoring.Notebook/notebook-content.py`, `.platform` | REST + CLI | SYNTHETIC data only; production model requires MLflow + RAI gates |
| `notebookDataQuality` | `v3-validate-data-quality` | Notebook | `notebooks/ns-validate-data-quality.Notebook/notebook-content.py`, `.platform` | REST + CLI | Contract, physics, and scenario assertions must all pass |
| `pipelineMedallion` | `pl-novasteelv3-medallion` | DataPipeline | `pipelines/pl-ns-medallion.DataPipeline/pipeline-content.json`, `.platform` | REST + CLI | Notebook job identity bound; schedule outside capacity pause window |
| `pipelineDemoScoring` | `pl-novasteelv3-demo-scoring` | DataPipeline | `pipelines/pl-ns-demo-scoring.DataPipeline/pipeline-content.json`, `.platform` | REST + CLI | Disabled outside SYNTHETIC demo workspace |
| `semanticOperations` | `sm-novasteelv3-operations` | SemanticModel | `semantic-model/sm-ns-operations.SemanticModel/` (TMDL, 19 table files) | REST + CLI — **disabled until `semanticModelBindingValidated` gate is set** | Direct Lake binding, RLS, sensitivity label, and refresh/query validated |

### 2.2 Excluded automated item (novasteelv3 manifest)

| Item key | Fabric type | Reason for exclusion |
|---|---|---|
| `eventstreamTelemetry` (`es-ns-telemetry-v1`) | Eventstream | Custom Endpoint connection details are runtime-generated per tenant; managed-identity publisher path must be proven manually before automation is permitted |

### 2.3 Manual assets (portal / tenant-validated before automation)

| Asset key | Fabric type | Source file | Gate reason |
|---|---|---|---|
| `rtiDashboard` | KQLDashboard | `fabric/rti/dashboard-spec.json` + `fabric/kql/dashboard-queries.kql` | Datasource IDs and layout must be exported from the tenant before REST import |
| `activator` | Reflex (Data Activator) | `fabric/rti/activator-rules.template.json` | Tenant-bound Teams/email/Power Automate connections; DLP/licensing; human owner approval |
| `powerBiReports` | Report | `fabric/powerbi/report-catalog.json` + `fabric/powerbi/novasteel-theme.json` | Tenant-bound semantic model; RLS; format **must** be Legacy PBIX (not PBIR) to render visuals |
| `oneLakeSecurity` | OneLakeSecurityRole | `fabric/catalog/security-role-matrix.json` | Role APIs must be verified per tenant; workspace-level roles are not a data-security substitute |
| `tenantApiPermission` | TenantSetting | `.azure/fabric/README.md` | Fabric admin must grant the deployment identity workspace-creation and API permissions |

### 2.4 Supporting scripts and CI/CD

| File | Purpose |
|---|---|
| `fabric/scripts/Deploy-FabricAssets.ps1` | Main REST bootstrap for all automated items |
| `fabric/scripts/Deploy-FabricDefinitionsWithCli.ps1` | Post-bootstrap CLI definition push for CLI-deployable items |
| `fabric/scripts/FabricDeployment.psm1` | Shared helper module (token, polling, idempotency) |
| `fabric/scripts/Invoke-FabricCapacityLifecycle.ps1` | Resume / suspend the F2 capacity; `prod` is hard-denied |
| `fabric/scripts/Test-FabricAssetsLocal.ps1` | Structural validator — no tenant contact |
| `fabric/scripts/Test-FabricDeployment.ps1` | Post-deploy tenant validation and gate reporter |
| `fabric/scripts/bootstrap-workspaces.ps1` | Workspace creation (called from `Deploy-FabricAssets.ps1`) |
| `.azure/fabric/New-NovaSteelV3FabricWorkspace.ps1` | Isolated novasteelv3 workspace prep |
| `.azure/fabric/Deploy-NovaSteelV3FabricAssets.ps1` | Isolated novasteelv3 item deployment |
| `.azure/fabric/Test-NovaSteelV3FabricPrep.ps1` | Isolated prep validation |
| `.azure/fabric/Get-NovaSteelV3FabricVerification.ps1` | Post-prep verification |
| `.github/workflows/cd-fabric-items.yml` | GitHub Actions CI/CD for Fabric items (OIDC, protected feeds) |

---

## 3. Item-to-agent mapping table

Each row identifies the Fabric-Brain agent responsible for deploying or
validating the corresponding NovaSteel3 asset or gate, with the recommended
action.

| Asset / gate | Fabric-Brain agent | Recommended action |
|---|---|---|
| Workspace `NovaSteelV3-Demo`, F2 capacity assignment, RBAC (Contributor scope isolated to RTI-Ingress) | `workspace-admin-agent` | Run `.azure/fabric/New-NovaSteelV3FabricWorkspace.ps1`; agent validates capacity assignment, confirms four-workspace topology, and applies minimum RBAC |
| Tenant API permission (`tenantApiPermission` manual asset) | `workspace-admin-agent` | Agent confirms deployment identity has `CreateWorkspace` and API permissions in Fabric admin portal before any script runs outside `-DryRun` |
| Eventstream Custom Endpoint `es-ns-telemetry-v1` (excluded from manifest; managed-identity gate unresolved) | `rti-eventstream-agent` | Agent retrieves generated Custom Endpoint details, proves Entra managed-identity publishing, grants publisher identity Contributor on RTI-Ingress only, and tests duplicate/late/malformed-message handling |
| Eventhouse `evh-novasteelv3-operations` | `rti-kusto-agent` | Agent creates the Eventhouse via REST, validates capacity assignment and cold-start behavior |
| KQL Database `kql-novasteelv3-operations` (schema + tables + policies) | `rti-kusto-agent` | Agent deploys `DatabaseSchema.kql` via Fabric CLI, validates retention/cache, confirms KQL ingestion endpoint and item identity |
| RTI KQL Dashboard (`rtiDashboard` manual asset) | `rti-kusto-agent` | Agent runs `dashboard-queries.kql` against the live database, validates all five visual categories (freshness, gateway, alarms, model score, quarantine), and exports the tenant definition before REST import |
| Data Activator rules (`activator` manual asset; `activator-rules.template.json`) | `data-activator-agent` | Agent binds Teams/email targets, validates DLP/licensing, confirms rules are notify/enrich-only (no OT, no setpoint, no capacity action), and tests state-transition deduplication |
| Lakehouse `lh_novasteelv3_landing` (bronze / quarantine) | `lakehouse-agent` | Agent creates the Lakehouse, applies OneLake security roles and sensitivity label, validates no cross-workspace shortcut, and confirms publisher identity has no DataCore/ML/Analytics access |
| Lakehouse `lh_novasteelv3_core` (silver/gold Delta tables) | `lakehouse-agent` | Agent creates the Lakehouse, applies DDL from `fabric/lakehouse/sql/` (bronze → silver → gold), validates data-quality rules in `fabric/lakehouse/schema/data-quality-rules.json`, and confirms notebook identity is least-privilege read-landing/write-core |
| Notebooks: `v3-initialize-lakehouses`, `v3-bronze-to-silver`, `v3-silver-to-gold`, `v3-validate-data-quality` | `lakehouse-agent` + `orchestrator-agent` | `lakehouse-agent` attaches/authorises Lakehouse identities; `orchestrator-agent` deploys and tests each notebook via REST/CLI |
| Notebook `v3-deterministic-demo-scoring` | `orchestrator-agent` | Agent deploys notebook, confirms it runs only against SYNTHETIC data, and enforces the gate that prevents promotion to a production model without MLflow evaluation and RAI approval |
| Pipeline `pl-novasteelv3-medallion` | `orchestrator-agent` | Agent deploys pipeline via Fabric CLI, binds notebook job identity, runs a fixed-batch row reconciliation, and configures schedules outside the capacity pause window |
| Pipeline `pl-novasteelv3-demo-scoring` | `orchestrator-agent` | Agent deploys pipeline, enforces the gate that keeps it disabled outside the SYNTHETIC demo workspace |
| Semantic model `sm-novasteelv3-operations` (Direct Lake TMDL, 19 table files, DAX measures) | `semantic-model-agent` | Agent creates/validates the Direct Lake binding against the core Lakehouse SQL endpoint, validates RLS/persona plant scope with test identities, confirms Pro/PPU/trial for every report consumer, applies sensitivity label, then sets `semanticModelBindingValidated=true` to unblock CI/CD |
| Power BI reports (`powerBiReports` manual asset) | `report-builder-agent` | Agent builds reports in **Legacy PBIX format only** (PBIR does not render visuals), binds to `sm-novasteelv3-operations`, applies theme from `novasteel-theme.json`, and validates RLS and export permissions per persona |
| Power BI visual polish and accessibility | `pixel-design-agent` | Agent validates visual consistency, colour-contrast compliance (WCAG AA), and report-page layout before sign-off |
| CI/CD Fabric items (`.github/workflows/cd-fabric-items.yml`) | `cicd-fabric-agent` + `fabric-cli-agent` | `cicd-fabric-agent` configures OIDC identity binding and environment protection rules; `fabric-cli-agent` handles `fab auth login --identity` and CLI definition push steps in the workflow |
| OneLake security roles (`oneLakeSecurity` manual asset) | `workspace-admin-agent` | Agent applies and verifies role matrix from `fabric/catalog/security-role-matrix.json`, confirms publisher identity has no DataCore/ML/Analytics access, and retains monthly role export as release evidence |
| Capacity monitoring, audit, and alert rules | `monitoring-agent` | Agent configures Fabric Admin API audit, capacity-utilisation dashboards, and alert thresholds; integrates with the Logic App `novasteelv3-capacity-pause` already deployed to the Azure estate |
| Portal embed: Power BI app-owns-data / dashboard KQL MSAL | `operations-portal-agent` | Agent configures embed tokens for the existing FastAPI BFF and Blazor/React portal; uses **Embed for your organization (user owns data)** for internal Entra users |

---

## 4. Capability gaps — what Fabric-Brain adds

The four items below do not correspond to existing files in the repository.
They represent new Fabric capabilities that Fabric-Brain agents can introduce.
For each item, the benefit, impact on the existing architecture, and indicative
effort are described.

### 4.1 `domain-modeler-agent` — persist synthetic fixtures in Fabric

**Current state:** The 6-device/34-sensor simulator runs in-process inside the
Python BFF (`simulator/config.py`, `services/bff-api/`). Outputs stay in memory
or local fixture files; nothing is written to Fabric Delta tables or KQL.

**Benefit:** `domain-modeler-agent` generates a star-schema template for the
steel-plant domain (Furnace → Heat → Lot → Coil → Equipment → Sensor) and
produces synthetic Delta rows in `lh_novasteelv3_landing` from the same
deterministic simulator config. This makes the demo reproducible end-to-end in
Fabric without changing the simulator source.

**Impact on existing architecture:** Demonstration synthetic data remains isolated
(`NS-DEMO-*` namespace, `dataClassification: SYNTHETIC`). The medallion
notebooks and pipelines already defined in the repo consume the Delta input
without modification. No application code or contract file changes.

**Indicative effort:** 1–2 days (schema alignment + single generator notebook
using the existing `simulator/config.py` constants as parameters).

### 4.2 `ontology-agent` + `graph-agent` — governed digital twin structure

**Current state:** NovaSteel includes the Fabric IQ Ontology item
`onto_novasteelv3` and its GraphModel. It now models **two layers joined by a
bridge**, both native to the ontology item and queryable by GQL through the
graph:

- **Instance layer (ABox)** — the real synthetic fleet: `Plant -[hasAsset]->
  Asset -[hasSensor]-> Sensor`, plus `Grade`, and the instance-level process
  genealogy `Asset -[supplies]-> Asset`
  (`LUX-BF-01 → LUX-BOF-01 → LUX-CC-01 → LUX-RHF-01 / LUX-HSM-01`).
- **Knowledge model (TBox)** — a curated steel vocabulary: `EquipmentClass`
  (with a `specializes` class hierarchy and an `IsAbstract` flag),
  `ProcessStep`, `ProductType`, `Signal`, and `AlarmType`, wired by the abstract
  edges `feeds` (process flow between classes), `executes`
  (EquipmentClass → ProcessStep), `produces` (ProcessStep → ProductType),
  `triggeredBy` (AlarmType → Signal), and `halts` (AlarmType → EquipmentClass).
- **Bridge** — `Asset -[instanceOf]-> EquipmentClass` and
  `Sensor -[measures]-> Signal`, so a query can walk from a real asset up to its
  class, reason abstractly, and come back down to instances or the tabular
  facts.

This restores the abstract class / process-genealogy reasoning that briefly
lived in the retired `ns-steel-ontology` notebook and its standalone
`ontology_entity` / `ontology_relationship` / `ontology_property` Delta tables.
Those tables were dropped; the capability is now expressed **inside the ontology
item** instead of over bespoke SQL tables. The knowledge model also corrects the
old model's metallurgically wrong `BlastFurnace -feeds-> ContinuousCaster` edge:
the restored chain is `BlastFurnace → BasicOxygenFurnace → ContinuousCaster →
ReheatFurnace / RollingMill`, and the "does a blast furnace feed the caster"
question is answered with the correct two-hop `feeds*1..3` path.

**Benefit:** `ontology-agent` governs the Fabric IQ Ontology definition and
bindings, while `graph-agent` validates the GraphModel and GQL queries — both
for structural twin questions (which assets belong to a plant, which sensors
belong to an asset) and for abstract knowledge questions (what kind of unit is
this, what feeds what, what a step produces, which signals trigger the alarm
that halts a unit). Upstream/downstream instance genealogy is now carried by the
`supplies` edge rather than only in Python fixture code and DAX.

**Impact on existing architecture:** The Fabric IQ Ontology and GraphModel sit
alongside the existing Eventhouse and Lakehouse without replacing them. The BFF
`/knowledge` routes (`services/bff-api/`) can be extended with a GQL adapter;
existing REST contracts are unchanged. Adds governed ontology/graph namespaces
to the four-workspace topology defined in `fabric/catalog/fabric-items.json`.

**How the knowledge model binds:** the curated TBox seed rows (equipment
classes, process steps, products, alarm types) plus the data-derived signals are
materialised by the `ns-ontology-bindings` notebook into managed `onto_*` Delta
tables (`onto_equipment_class`, `onto_process_step`, `onto_product`,
`onto_signal`, `onto_alarm_type`, and the `onto_rel_*` edge tables). The Ontology
item binds its entity and relationship types to those tables, and the GraphModel
projects them as the node and edge types above. The instance layer continues to
bind from the gold `dim_*` / `fact_*` tables. No dangling edges are written —
every relationship row has both endpoints present in its entity tables.

**Indicative effort:** 3–5 days to validate the current
`onto_novasteelv3`/GraphModel deployment, add a GQL adapter stub for the BFF,
and keep the seed rows and derived signals in sync. The instance graph is seeded
from the existing `simulator/config.py` device/sensor catalog; the knowledge
model is a curated vocabulary materialised by `ns-ontology-bindings`.

### 4.3 `ai-skills-agent` — governed Fabric Data Agent with dual-source routing

**Current state:** The AI/knowledge layer is implemented through Azure AI
Foundry Agent Service and a local knowledge-orchestrator
(`services/knowledge-orchestrator/`). This provides grounded RAG over procedure
documents but is outside Fabric's governance boundary.

**Benefit:** `ai-skills-agent` creates a Fabric Data Agent with dual-source
routing: hot telemetry queries from `kql-novasteelv3-operations` (Eventhouse)
and governed dimension/KPI queries from `lh_novasteelv3_core` (Lakehouse via
Direct Lake). This gives a governed, auditable AI layer inside Fabric, with
OneLake lineage and Fabric sensitivity labels applied to every query path.

**Impact on existing architecture:** Additive — it complements rather than
replaces the Foundry knowledge-orchestrator. The existing `/chat` and
`/knowledge` BFF routes remain functional. The Fabric Data Agent endpoint can
be surfaced alongside the existing Copilot chat panel in the portal (ADR-009,
`solution-architecture.md`). No change to application contracts.

**Indicative effort:** 2–3 days (Data Agent configuration + integration test
with fixed KQL and Lakehouse queries; prompt/routing logic is pre-built in the
agent template).

### 4.4 `ai-skills-analysis-agent` — Data Agent evaluation and DAX quality scoring

**Current state:** The semantic model TMDL and DAX measures are source-controlled
in `fabric/semantic-model/sm-ns-operations.SemanticModel/` and validated
structurally by `Test-FabricAssetsLocal.ps1`. There is no automated BPA (Best
Practice Analyser) run, no semantic model evaluation report, and no scoring of
the Data Agent response quality.

**Benefit:** `ai-skills-analysis-agent` runs the 24-rule DAX BPA against
`sm-novasteelv3-operations`, produces a scored evaluation report, and benchmarks
Data Agent response quality against labelled question/answer pairs. This
provides an evidence artefact for release gates (§22 of
`solution-architecture.md` "Deployment acceptance gates").

**Impact on existing architecture:** Purely additive — no changes to the model
or notebooks. The evaluation output becomes a new deployment artefact alongside
`Test-FabricDeployment.ps1` output.

**Indicative effort:** 1 day (BPA run + evaluation notebook; question/answer
pairs can be seeded from the existing demo runbook scenarios in
`docs/demo/demo-runbook.md`).

---

## 5. Deployment sequence

### Pre-requisites (all phases)

Before any phase executes, the following are required:

1. F2 Fabric capacity is provisioned and **running** (not paused by the Logic
   App `novasteelv3-capacity-pause`). The capacity must be resumed before any
   deployment (see `.azure/infra/README.md`).
2. The deployment identity has Fabric workspace-creation permissions (the
   `tenantApiPermission` manual asset gate in the novasteelv3 manifest).
3. All scripts use Azure CLI managed-identity or user login — no client secrets
   or SAS tokens. Protected feeds (`packagefeedproxy.microsoft.io`) must be
   reachable.
4. `pwsh -File .\fabric\scripts\Test-FabricAssetsLocal.ps1` is green (structural
   validation; no tenant contact).

---

### Phase 1 — Persist synthetic data in Fabric

**Goal:** Load simulator-generated synthetic data into real Fabric Delta tables
and the KQL database, replacing the local-only fixture baseline.

**Gate:** All data is `SYNTHETIC`, `dataClassification: SYNTHETIC`,
`NS-DEMO-*` namespace. No OT connection.

| Step | Action | Script / agent | Exit criterion |
|---|---|---|---|
| 1.1 | Create isolated workspace + assign F2 capacity | `.azure/fabric/New-NovaSteelV3FabricWorkspace.ps1` + `workspace-admin-agent` | Workspace appears in Fabric portal with correct capacity |
| 1.2 | Create `lh_novasteelv3_landing` and `lh_novasteelv3_core` | `fabric/scripts/Deploy-FabricAssets.ps1 -deploymentOption deployLakehouses` + `lakehouse-agent` | Both Lakehouses visible; OneLake security roles applied |
| 1.3 | Initialise medallion tables | `fabric/scripts/Deploy-FabricAssets.ps1 -deploymentOption deployNotebooks` (notebookInitialize) then run notebook + `lakehouse-agent` | Delta tables `bronze_telemetry`, `silver_facts`, `gold_kpi` exist and match `fabric/lakehouse/schema/medallion-catalog.json` |
| 1.4 | Generate synthetic data into bronze | `domain-modeler-agent` — new generator notebook (gap §4.1) | ≥ 1,000 synthetic rows in `lh_novasteelv3_landing.bronze_telemetry`; all `dataClassification = SYNTHETIC` |
| 1.5 | Run bronze→silver→gold pipeline | `pl-novasteelv3-medallion` via `fabric/scripts/Deploy-FabricAssets.ps1 -deploymentOption deployPipelines` + `orchestrator-agent` | Row counts reconcile; data-quality notebook passes contract, physics, and scenario assertions |
| 1.6 | Create Eventhouse + KQL database and ingest from bronze | `fabric/scripts/Deploy-FabricAssets.ps1 -deploymentOption deployEventhouseAndKql` + `fabric/scripts/Deploy-FabricDefinitionsWithCli.ps1` + `rti-kusto-agent` | `kql-novasteelv3-operations` contains the tables defined in `DatabaseSchema.kql`; test queries from `fabric/kql/dashboard-queries.kql` return rows |
| 1.7 | Validate end-to-end | `fabric/scripts/Test-FabricDeployment.ps1 -Deep` | All automated items in manifest are green; no manual gates report failures |

---

### Phase 2 — Lift existing gates (Eventstream, semantic model, Power BI)

**Goal:** Deploy the remaining items that require explicit tenant validation:
Eventstream Custom Endpoint, Direct Lake semantic model, and Power BI reports.

**Pre-requisite:** Phase 1 exit criterion met; business owners sign off KPI
definitions in gold tables.

| Step | Action | Script / agent | Exit criterion |
|---|---|---|---|
| 2.1 | Provision and verify Eventstream Custom Endpoint | Portal + `rti-eventstream-agent` | Managed-identity publisher confirmed; test messages (duplicate, late, malformed) handled correctly; publisher has Contributor on RTI-Ingress only |
| 2.2 | Enable Eventstream definition deployment | Add `eventstreamTelemetry` to manifest `supportedItems` after 2.1 evidence | `es-ns-telemetry-v1` deployed via `Deploy-FabricDefinitionsWithCli.ps1`; destinations routing to KQL and landing Lakehouse verified |
| 2.3 | Deploy and validate RTI KQL Dashboard | Portal export → check-in → `rti-kusto-agent` | All five visual categories (freshness, gateway, alarms, model score, quarantine) render with live KQL data |
| 2.4 | Bind Data Activator rules | Portal + `data-activator-agent` | Rules activate on threshold breach; notify/enrich only; no OT action; DLP/licensing confirmed |
| 2.5 | Set `semanticModelBindingValidated=true` and deploy semantic model | `fabric/scripts/Deploy-FabricAssets.ps1 -deploymentOption deploySemanticModel` + `semantic-model-agent` | Direct Lake binding resolves to `lh_novasteelv3_core` SQL endpoint; RLS persona tests pass; refresh completes without errors |
| 2.6 | Build and publish Power BI reports | Portal (Legacy PBIX only) + `report-builder-agent` + `pixel-design-agent` | Executive, sustainability, and persona pages bind to `sm-novasteelv3-operations`; RLS and export permissions pass; WCAG AA contrast check passes |
| 2.7 | Apply OneLake security roles | Portal + `workspace-admin-agent` | Role matrix from `fabric/catalog/security-role-matrix.json` applied; monthly export retained as evidence |
| 2.8 | Full CI/CD round-trip | `.github/workflows/cd-fabric-items.yml` + `cicd-fabric-agent` + `fabric-cli-agent` | Workflow completes on protected feed; OIDC token resolves correctly against the federated credential registered in `.github/README.md` (Repository-level variables section) |

---

### Phase 3 — IQ layer (Fabric IQ Ontology, GraphModel, Data Agent) and portal reconnection

**Goal:** Add the digital-twin and governed-AI capabilities identified in §4,
then reconnect the BFF/portal.

**Pre-requisite:** Phase 2 exit criterion met; legal/DPO review for the
`onto_novasteelv3` entity types completed; no production OT data at any point.

| Step | Action | Script / agent | Exit criterion |
|---|---|---|---|
| 3.1 | Define and validate Fabric IQ Ontology `onto_novasteelv3` — instance layer (Plant, Asset, Sensor, Grade) and knowledge model (EquipmentClass, ProcessStep, ProductType, Signal, AlarmType) | `ontology-agent` | Ontology item, `onto_*` bindings (materialised by `ns-ontology-bindings`), and GraphModel are deployed and queryable |
| 3.2 | Build or extend GraphModel and GQL queries | `graph-agent` | Instance containment (Plant → Asset → Sensor) and knowledge-model traversals (class `specializes` hierarchy, `feeds` genealogy, `instanceOf` / `measures` bridge) return correct results on synthetic data; any remaining gaps are explicitly documented |
| 3.3 | Deploy Fabric Data Agent (dual-source KQL + Lakehouse) | `ai-skills-agent` | Data Agent routes telemetry queries to KQL and KPI queries to Direct Lake; responses cite source and sensitivity label |
| 3.4 | Run DAX BPA and Data Agent evaluation | `ai-skills-analysis-agent` | 24-rule BPA report produced; Data Agent scores ≥ threshold on demo question/answer pairs |
| 3.5 | Reconnect BFF and portal | `operations-portal-agent` | FastAPI BFF routes `/analytics` and `/knowledge` surface Fabric Data Agent and embed Power BI (user-owns-data, Entra MSAL); RTI dashboard tiles render in the portal |
| 3.6 | Capacity monitoring and alerts | `monitoring-agent` | Fabric Admin API audit enabled; capacity-utilisation dashboard live; Logic App `novasteelv3-capacity-pause` integrated with alert threshold |
| 3.7 | Final gate review | `fabric/scripts/Test-FabricDeployment.ps1 -Deep` | All manifest items green; all manual assets have completion evidence checked in; monitoring agent confirms no alert storms |

---

## 6. Gate traceability table

This table maps the **seven remaining production gates** from `docs/README.md`
and the `manualAssets` / `excludedItems` from
`fabric/deployment-parameters/novasteelv3.items-manifest.json` to the
deployment phase and responsible agent.

| # | Gate description (from `docs/README.md` or manifest) | Phase | Agent |
|---|---|---|---|
| 1 | Fabric capacity/SKU/quota and regional support in the target tenant | Phase 1 (step 1.1) | `workspace-admin-agent` |
| 2 | Eventstream Custom Endpoint managed-identity publishing, isolated Contributor scope, tenant switches, and permitted network paths | Phase 2 (step 2.1–2.2) | `rti-eventstream-agent` |
| 3 | Foundry model/deployment/Agent Service/Speech availability, quota, identity, evaluation, and private-network behavior | Phase 3 (step 3.5) — Fabric Data Agent is the governed Fabric-side complement | `ai-skills-agent` (Fabric side); Foundry gates remain separate |
| 4 | Entra, Fabric workspace/OneLake/item-level authorization and Power BI RLS | Phase 1 (step 1.2) + Phase 2 (step 2.5–2.7) | `workspace-admin-agent` + `semantic-model-agent` + `report-builder-agent` |
| 5 | DPO/Legal/DPIA, retention/deletion, data residency, and EU AI Act decisions | Pre-requisite for Phase 3 (`onto_novasteelv3` entity types); retention validated in Phase 1 step 1.6 | `workspace-admin-agent` (data residency) + `ontology-agent` (entity classification) |
| 6 | OT vendor/site approval for each DMZ protocol, source, rate, and boundary | Out of scope for Fabric layer at all phases — remains with the OT/DMZ workstream | N/A (not a Fabric item) |
| 7 | Market-data licensing/freshness, immutable service images, DR/performance/accessibility testing, and live-cloud fallback rehearsal | Phase 2 (accessibility — step 2.6 `pixel-design-agent`) + Phase 3 (monitoring — step 3.6 `monitoring-agent`) | `pixel-design-agent` + `monitoring-agent` |

### Manifest `excludedItems` and `manualAssets` mapping

| Manifest key | Type | Gate | Phase | Agent |
|---|---|---|---|---|
| `eventstreamTelemetry` (excluded) | Eventstream | Custom Endpoint managed-identity path unproven | Phase 2 (step 2.1) | `rti-eventstream-agent` |
| `rtiDashboard` (manual) | KQLDashboard | Datasource IDs require tenant export | Phase 2 (step 2.3) | `rti-kusto-agent` |
| `activator` (manual) | Reflex | Tenant-bound connections + DLP/licensing | Phase 2 (step 2.4) | `data-activator-agent` |
| `powerBiReports` (manual) | Report | Tenant-bound semantic model + RLS + Legacy PBIX format | Phase 2 (step 2.6) | `report-builder-agent` |
| `oneLakeSecurity` (manual) | OneLakeSecurityRole | Role API capabilities verified per tenant | Phase 1–2 | `workspace-admin-agent` |
| `tenantApiPermission` (manual) | TenantSetting | Fabric admin must grant workspace-creation and API permissions | Pre-requisite / Phase 1 (step 1.1) | `workspace-admin-agent` |

---

## 7. References

### Fabric-Brain (external)

- **Agent catalogue:** `Fabric-Brain/agents/_catalog.yaml`
  (https://github.com/Statyx/Azure-Brain/blob/main/Fabric-Brain/agents/_catalog.yaml)
- **RTI Operations / Digital Twin template:** `Meta-Brain/TEMPLATES.md`
  (https://github.com/Statyx/Azure-Brain/blob/main/Meta-Brain/TEMPLATES.md)
- **Workflow patterns:** `Meta-Brain/WORKFLOWS.md`
  (https://github.com/Statyx/Azure-Brain/blob/main/Meta-Brain/WORKFLOWS.md)
- **Repository root:** https://github.com/Statyx/Azure-Brain

### NovaSteel3 internal documents

| Document | Path |
|---|---|
| Authoritative solution architecture | [solution-architecture.md](solution-architecture.md) |
| Deployment topology | [deployment-topology.md](deployment-topology.md) |
| Fabric assets README | [../../fabric/README.md](../../fabric/README.md) |
| Fabric item catalogue | [../../fabric/catalog/fabric-items.json](../../fabric/catalog/fabric-items.json) |
| novasteelv3 items manifest | [../../fabric/deployment-parameters/novasteelv3.items-manifest.json](../../fabric/deployment-parameters/novasteelv3.items-manifest.json) |
| KQL queries | [../../fabric/kql/dashboard-queries.kql](../../fabric/kql/dashboard-queries.kql) |
| Activator rules template | [../../fabric/rti/activator-rules.template.json](../../fabric/rti/activator-rules.template.json) |
| Medallion contracts | [../../fabric/lakehouse/schema/medallion-catalog.json](../../fabric/lakehouse/schema/medallion-catalog.json) |
| Semantic model measures | [../../fabric/semantic-model/measures/measures.dax](../../fabric/semantic-model/measures/measures.dax) |
| Isolated Fabric workspace prep | [../../.azure/fabric/README.md](../../.azure/fabric/README.md) |
| CI/CD workflow | [../../.github/workflows/cd-fabric-items.yml](../../.github/workflows/cd-fabric-items.yml) |
| Documentation index | [../README.md](../README.md) |
| Synthetic data and simulators | [../data/synthetic-data-and-simulators.md](../data/synthetic-data-and-simulators.md) |
| Security, governance, and threat model | [../security/security-governance-and-threat-model.md](../security/security-governance-and-threat-model.md) |
