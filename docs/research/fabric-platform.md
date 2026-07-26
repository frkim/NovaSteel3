# Microsoft Fabric platform research — steel-production demo

**Research date:** 2026-07-25 (all links accessed on that date).  
**Purpose:** a cost-conscious, demonstrable path from steel-plant telemetry and operational data to live operational insight, governed historical analytics, and alerts/actions. This is not a production sizing commitment.

## Recommendation at a glance

Use **Microsoft Fabric in Sweden Central** as the central analytics platform:

```text
PLC/edge gateway, MES, quality and maintenance systems
  -> Azure Event Hubs raw replay buffer
  -> managed-identity relay
  -> Fabric Eventstream Custom Endpoint (validate/shape/route)
  -> KQL Database in an Eventhouse  -> Real-Time dashboard / KQL / alert rules
  -> Lakehouse in OneLake            -> notebook + curated Delta tables
  -> Direct Lake semantic model      -> Power BI operations and management reports
                                           |
                                      Activator -> Teams/email/Power Automate
```

Start a short-lived proof of concept on **F2 (2 CU)**, the smallest purchasable Fabric F SKU, with one small workspace and a bounded synthetic/replayed sensor feed. Use **F4** if the demo must concurrently run sustained streaming ingestion, Spark notebooks, and interactive reports; measure first rather than assume an SKU is sufficient. Keep the real-time path narrow (hot operational signals in KQL) and land only selected/raw batches in the lakehouse. Do not use a paused capacity for a live demo.

The architecture deliberately separates:

* **Hot path:** casting/furnace/rolling-line signals, alarms, equipment health, and quality events flow through Eventstreams into a KQL database for low-latency queries and operational dashboards.
* **Historical/curated path:** MES work orders, quality certificates, shifts, and maintenance extracts are copied/orchestrated into a bronze/silver/gold Lakehouse. Delta tables are the governed reporting and ML substrate.
* **Action path:** Activator detects sustained unsafe temperature, vibration, energy, or production-rate conditions per asset; it sends a low-risk notification/workflow. A human or an existing safety/OT control system remains authoritative for plant control.

> **Safety caveat:** Fabric alerts are suitable for observability and business workflows, not a safety instrumented system or a direct PLC-control loop. Preserve OT segmentation, validation, auditability, and human approval for any action that can affect production or safety.

## Capability decision record

Status terminology below is intentionally conservative: **Documented / no preview label** means the linked current Microsoft Learn overview does not mark the core feature preview; it is not a claim that every connector, subfeature, or region is GA. **Preview** is explicitly labelled by Microsoft. **Roadmap** is not a delivery promise.

| Platform capability | Recommendation for this demo | Status at research date | Important caveat |
|---|---|---|---|
| [Real-Time Intelligence](https://learn.microsoft.com/fabric/real-time-intelligence/overview) | Make it the live operations layer: discover streams, query, dashboard and detect exceptions. Manufacturing, IoT, time-series and anomaly scenarios are explicitly described. | Documented / no preview label | “Real-time” is not a hard real-time or safety-control SLA. Test end-to-end latency with the actual source and region. |
| [Eventstreams](https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/overview) | Use the Custom Endpoint as the canonical identity-based ingress; perform only lightweight shaping/routing and deliver to KQL and landing Lakehouse. | Documented / no preview label | The architecture uses an edge gateway → Event Hubs buffer → managed-identity relay → Custom Endpoint path. Confirm tenant settings and the current contributor-role requirement before design lock; a native secret-based source is not the canonical route. |
| [Eventhouse and KQL Database](https://learn.microsoft.com/fabric/real-time-intelligence/eventhouse) | Create one Eventhouse and KQL database for high-cardinality telemetry, alarms, logs and fast time-window investigations. Use KQL for operational queries/materialized views. | Documented / no preview label | Eventhouse can suspend when inactive; reactivation can add seconds of latency. It is not the primary long-term relational master-data store. |
| [Eventhouse Capacity Planner](https://learn.microsoft.com/fabric/real-time-intelligence/eventhouse-smart-capacity-control) | Do **not** depend on it for the first demo. Consider only if cold-start latency or a guaranteed baseline proves necessary. | **Preview** | Preview scheduling/behavior can change. Always-on/minimum capacity trades cost for latency/performance. |
| [Fabric Activator](https://learn.microsoft.com/fabric/real-time-intelligence/data-activator/activator-introduction) | Use per-asset rules for threshold, state transition, or missing-heartbeat notifications; target Teams/email/Power Automate or a controlled Fabric job. | Documented / no preview label | Rate limits and action semantics apply. Tune with historical replay and use state transitions/deduplication to prevent alert storms. “Publish business event” and warehouse-SQL alerting are explicitly **preview**. |
| [Data Factory](https://learn.microsoft.com/fabric/data-factory/data-factory-overview) | Use pipelines/copy jobs for scheduled MES, ERP, LIMS and maintenance loads; use Dataflow Gen2 for low-code cleanup where appropriate. | Documented / no preview label | Fabric Data Factory supports 170+ sources, but availability/authentication of each connector must be confirmed. Prefer incremental/CDC patterns over repeated full extracts. |
| [OneLake](https://learn.microsoft.com/fabric/onelake/onelake-overview) + [Lakehouse](https://learn.microsoft.com/fabric/data-engineering/lakehouse-overview) | Keep bronze/silver/gold Delta tables in one lake; use shortcuts only where read-through/no-copy access is appropriate. | Documented / no preview label | A shortcut is a reference, not an isolation or source-SLA substitute. Apply workspace/OneLake security and sensitivity labels before sharing. |
| [Notebooks and Data Science](https://learn.microsoft.com/fabric/data-science/data-science-overview) | Use Python/PySpark notebooks for quality prediction, anomaly exploration and batch scoring; record experiments with MLflow. Write predictions back to gold Delta tables. | Documented / no preview label | Start with offline/batch scoring; validate drift, labels and governance before claiming predictive maintenance value. Do not introduce Autoscale Spark billing until normal capacity measurements justify it. |
| [Direct Lake](https://learn.microsoft.com/power-bi/enterprise/directlake-overview) semantic model + Power BI | Build a gold star schema (asset, line, product/heat, shift, time; facts for telemetry aggregates, quality and production). Publish Power BI operational and management reports from Direct Lake. | Documented / no preview label | Direct Lake loads from OneLake Delta into memory; model design and capacity headroom still matter. On F2–F32 every report consumer needs Pro/PPU/trial; free viewers are supported only at F64+. |
| [Fabric REST APIs](https://learn.microsoft.com/rest/api/fabric/) | Automate workspace/item lifecycle, deployment and selected pipeline operations after proving a manual demo. Treat definitions, scopes, throttling, long-running operations and pagination as API design requirements. | Documented / no preview label | Use an Entra application/service principal only where the individual endpoint supports it; least privilege, secretless identity where possible, retry/backoff, and audit logs are required. |

## Concrete implementation outline

1. **Create isolated Fabric workspaces on an F2 capacity in Sweden Central.** Separate RTI ingress, DataCore, ML, Analytics, and `NS-DEMO-*` assets as defined by the architecture. Give report consumers Pro/PPU/trial access for the demo; never use a shared production workspace/capacity for pause, scale, or RBAC tests.
2. **Ingest safely.** Have the plant edge gateway publish a compact, versioned event contract (`timestamp_utc`, `asset_id`, `line_id`, `signal`, `value`, `unit`, `quality`, `sequence`) to Event Hubs. A scoped managed-identity relay publishes to the Eventstream Custom Endpoint; Eventstream performs only lightweight shaping/routing while the source path retains buffering and replay capability.
3. **Model hot and cold data differently.** In KQL, partition/query by event time and asset/line for last-minute/shift investigations. In Lakehouse, preserve immutable bronze input, then produce validated silver and aggregated gold Delta tables. Maintain a data-quality/quarantine table for late, duplicate, invalid-unit and missing-asset events.
4. **Build two kinds of visualisation.** Use a Real-Time dashboard/KQL for line operators’ current throughput, temperature/vibration bands and alarms. Use a Direct Lake semantic model and Power BI for OEE-style aggregates, yield/scrap, energy intensity, quality trends and maintenance planning. Establish definitions with operations before calling a KPI “OEE”.
5. **Automate only low-risk response.** An Activator rule should first notify a Teams channel and create a workflow/ticket; trigger a notebook/pipeline only for enrichment or diagnosis. Include asset ID, observed time, threshold, correlation ID and a link to the KQL investigation. Suppress repeated alerts until recovery.
6. **Prove failure behavior.** Replay a day of signals; deliberately inject missing heartbeats, duplicates, out-of-order readings and a threshold breach. Record ingestion-to-dashboard time, KQL latency, notification delay, capacity utilization/throttling and cost before deciding whether F2 is adequate.

## Automation, pause/resume, and Logic Apps

### What is supported

* Fabric REST APIs are explicitly intended to automate Fabric processes. Use them for repeatable provisioning/deployment only after validating endpoint-specific permissions and supported identities.
* Capacity lifecycle is an **Azure Resource Manager** operation, separate from the Fabric REST API. The documented endpoints are:
  * `POST .../providers/Microsoft.Fabric/capacities/{capacityName}/suspend?api-version=2023-11-01` — [Suspend API](https://learn.microsoft.com/rest/api/microsoftfabric/fabric-capacities/suspend)
  * `POST .../providers/Microsoft.Fabric/capacities/{capacityName}/resume?api-version=2023-11-01` — [Resume API](https://learn.microsoft.com/rest/api/microsoftfabric/fabric-capacities/resume)
* Both operations can return `202 Accepted`; automation must poll the operation URL/retry according to the response rather than assuming the request immediately completed.
* The pause/resume guidance explicitly permits Azure Automation runbooks and requires the Azure RBAC read/write plus `Microsoft.Fabric/capacities/suspend/action` and `.../resume/action` actions.
* Activator’s documented external workflow target is **Power Automate**, and it can also run Fabric pipeline/notebook/dataflow/Spark/UDF/copy-job actions, notify Teams, or send email.

### Logic Apps feasibility and recommendation

A **Logic Apps Standard/Consumption workflow is feasible for scheduled capacity control**: call the ARM suspend/resume operation over HTTPS using a managed identity or service principal granted only the capacity-level actions above. Implement a weekday schedule, operation polling, alert-on-failure, and an explicit denylist/approval window around demonstrations.

For data-condition alerts, use Activator’s native Power Automate action first. There is no claim here that Activator has a native Logic Apps action. If a Logic App is required (for example, an enterprise connector or integration boundary), have the Power Automate flow call a secured intermediary/HTTP endpoint or invoke an approved Logic Apps trigger; validate licensing, DLP policy, identity propagation and retry/idempotency in the tenant. Never let an alert directly pause a capacity that is serving live operations.

### Pause/suspend behavior and cost

Pausing an F capacity stops capacity availability and prevents Fabric content assigned to it from being available; resuming restores availability and resumes billing. It is useful overnight only if no viewers, scheduled pipelines, ingestion or alert rules need the capacity. A pause also ends current throttling, but Microsoft states that remaining cumulative overages/smoothed operations are summed and added to the Azure bill. It is therefore not a way to erase prior consumption.

Plan for persistent storage cost: OneLake data remains stored; the pricing page says free mirroring storage is charged when its capacity is paused. Eventhouse may itself reactivate after a few seconds when idle, so avoid promising an instantaneous first query unless its cost/latency configuration has been tested.

## Capacity, licensing, and cost controls

### Practical demo SKU

| Choice | Why | Constraints |
|---|---|---|
| **F2, 2 CU — recommended initial demo** | The documented capacity table starts at F2. Azure F capacities are per-second PAYG (one-minute minimum), can be scaled and paused; this minimizes idle-demo compute spend. | It is a shared pool for every workload. Limit concurrent Spark, KQL ingestion and Power BI workloads; use Pro/PPU for every Power BI consumer. |
| **F4, 4 CU — measurement-driven fallback** | Gives headroom if the scripted live demonstration concurrently refreshes/queries reports and executes notebook transformations. | Still requires Pro/PPU users to view Power BI content. Do not choose it merely as an untested “production” size. |
| **F64+ — not cost-conscious for this demo** | Allows free-license users with viewer role to consume Power BI content. | This licensing convenience alone does not justify it for a small demo. |
| **60-day Fabric trial (F64 equivalent)** | Good only for hands-on exploration without procurement. | It expires; do not base a repeatable customer demo or cost model on it. |

F SKUs are the recommended Azure capacity type; PPU alone does **not** provision non-Power-BI Fabric workloads. F capacities are billed per second with a one-minute minimum and have no commitment; reservations may make sense only after stable utilization is demonstrated. The exact F2/F4 unit rate is region, currency, offer and agreement dependent. Use the [official Fabric pricing page](https://azure.microsoft.com/pricing/details/microsoft-fabric/) with **Sweden Central** and the [Azure pricing calculator](https://azure.microsoft.com/pricing/calculator/?service=microsoft-fabric) at purchase time; do not copy an unverified price into the proposal.

Cost controls:

* Tag the capacity/resource group (`demo`, `owner`, `expiry`), set Azure budgets/alerts and Fabric capacity quotas; review the Capacity Metrics app after each rehearsal.
* Keep the demo capacity PAYG and pause only during confirmed off-hours. Resume before a rehearsal, account for warm-up, and avoid scheduled work while paused.
* Cap retention/cache intentionally. OneLake storage and KQL cache/Data Activator retained data have separate charging considerations; avoid retaining high-frequency raw signals indefinitely.
* Do not enable capacity overage by default for a cost-controlled demo. Microsoft describes it as a way to pay for excess consumption; enable only with a small 24-hour limit and an owner.
* Keep Spark autoscale billing opt-in and off initially. It uses dedicated serverless PAYG Spark resources and reservation discounts do not apply.

## Region decision

Microsoft’s current Fabric region table marks all four requested regions as supporting **Power BI and all Fabric workloads**. This is the best available portfolio-level statement, not a reservation that an exact SKU, preview, connector, or capacity quota can be created today. Attempt capacity creation in the target subscription and confirm the target workload in a proof of concept.

| Region | Current Fabric table result | Recommendation/caveat |
|---|---|---|
| **Sweden Central** | Power BI ✅; all Fabric workloads ✅. The table notes that Power BI business-continuity/disaster-recovery is not available by default because the paired region does not support it. | **Preferred** for Swedish data residency/latency. Treat the BCDR note as a decision risk; verify the required recovery design before production. |
| **West Europe** | Power BI ✅; all Fabric workloads ✅. The table lists Schema Registry as unavailable. | Good European alternative. Do not design around Schema Registry there without a later availability check. |
| **North Europe** | Power BI ✅; all Fabric workloads ✅. The table lists Digital twin builder (preview) and Fabric App (preview) as unavailable. | Valid alternative, but do not use the unavailable preview items in the demo. |
| **France Central** | Power BI ✅; all Fabric workloads ✅; no unavailable features are listed in the table. | Valid alternative where French placement is required; still validate the purchased SKU/tenant before committing. |

Select the capacity region, then ensure workspaces and data residency choices meet policy. If cross-region capacity is used for a tenant whose home region has a limitation, Microsoft’s region guidance points to Multi-Geo; assess governance and transfer implications rather than casually moving plant data.

## Preview and roadmap guardrails

* **Use in the demo:** the core RTI, Eventstream, Eventhouse/KQL, OneLake/Lakehouse, Data Factory, notebook/Data Science, Direct Lake/Power BI, Fabric REST API, and F-capacity capabilities listed as “documented/no preview label” above.
* **Explicit preview—exclude from the critical path:** Eventhouse Capacity Planner scheduling; Digital twin builder; warehouse SQL-query Activator alerts; Activator’s publish-business-event action; and any region-table item marked preview/unavailable. They may be evaluated behind a feature flag only.
* **Roadmap/announcement:** the [Fabric Roadmap](https://roadmap.fabric.microsoft.com/) page is a Microsoft community/roadmap source and explicitly says planned functionality, timing and projected behavior can change or never release. No 2026 RTI/Eventstreams roadmap commitment was used to justify this design. Re-check that page and the [Fabric blog](https://blog.fabric.microsoft.com/) before each release decision.

## Source table

All sources are official Microsoft sources and were accessed **2026-07-25**. “Current document” indicates the source is live documentation, not a dated GA announcement; its status labels were used only where explicit.

| Source | Type/status used | Accessed |
|---|---|---|
| [Fabric region availability](https://learn.microsoft.com/fabric/admin/region-availability) | Current Learn region table; Sweden Central, West Europe, North Europe, France Central | 2026-07-25 |
| [Understand Microsoft Fabric licenses](https://learn.microsoft.com/fabric/enterprise/licenses) | Current Learn; F SKUs/CUs, F64 viewer rule, Pro/PPU requirement | 2026-07-25 |
| [Buy a Fabric subscription](https://learn.microsoft.com/fabric/enterprise/buy-subscription) | Current Learn; PAYG billing, scale/pause, RBAC | 2026-07-25 |
| [Pause and resume capacity](https://learn.microsoft.com/fabric/enterprise/pause-resume) | Current Learn; availability, throttling/overage and runbook guidance | 2026-07-25 |
| [Fabric capacity Suspend API](https://learn.microsoft.com/rest/api/microsoftfabric/fabric-capacities/suspend) and [Resume API](https://learn.microsoft.com/rest/api/microsoftfabric/fabric-capacities/resume) | Current ARM REST reference, API version `2023-11-01` | 2026-07-25 |
| [Fabric pricing](https://azure.microsoft.com/pricing/details/microsoft-fabric/) | Current Azure pricing page; regional pricing/currency qualifiers, storage, overage and autoscale billing | 2026-07-25 |
| [Real-Time Intelligence overview](https://learn.microsoft.com/fabric/real-time-intelligence/overview) | Current Learn; RTI architecture and manufacturing/IoT use cases | 2026-07-25 |
| [Eventstreams overview](https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/overview) | Current Learn; no-code ingestion, transformation and routing | 2026-07-25 |
| [Eventhouse overview](https://learn.microsoft.com/fabric/real-time-intelligence/eventhouse) | Current Learn; KQL databases, OneLake and idle reactivation behavior | 2026-07-25 |
| [Fabric Activator introduction](https://learn.microsoft.com/fabric/real-time-intelligence/data-activator/activator-introduction) | Current Learn; rules/actions and explicit previews | 2026-07-25 |
| [Data Factory overview](https://learn.microsoft.com/fabric/data-factory/data-factory-overview) | Current Learn; connectors, copy, pipelines, dataflows | 2026-07-25 |
| [OneLake overview](https://learn.microsoft.com/fabric/onelake/onelake-overview) and [Lakehouse overview](https://learn.microsoft.com/fabric/data-engineering/lakehouse-overview) | Current Learn; open tables, shortcuts, security, SQL/Spark | 2026-07-25 |
| [Data Science overview](https://learn.microsoft.com/fabric/data-science/data-science-overview) and [Direct Lake overview](https://learn.microsoft.com/power-bi/enterprise/directlake-overview) | Current Learn; notebooks/MLflow and Direct Lake semantic models | 2026-07-25 |
| [Fabric REST API documentation](https://learn.microsoft.com/rest/api/fabric/) | Current Learn; automation/API architecture | 2026-07-25 |
| [Fabric Roadmap](https://roadmap.fabric.microsoft.com/) | Microsoft roadmap/announcement; explicitly non-binding | 2026-07-25 |
