# Glossary

> **Artifact:** Glossary · **Audience:** all · **Status:** baseline · **Source of truth:** [solution architecture](../architecture/solution-architecture.md)

## Purpose

This glossary gives project readers one concise reference for the industrial, platform, AI, and governance vocabulary used across NovaSteel. Definitions preserve the project guardrail that NovaSteel is synthetic, advisory decision support only: it does not control PLCs, interlocks, furnaces, recipes, setpoints, production schedules, or CMMS records.

## Steel-making and industrial domain terms

| Term | Definition |
|---|---|
| EAF | Electric Arc Furnace: a furnace that melts scrap or other metallic feed with electric arcs; used by the Germany, Belgium, and Spain demo routes. |
| BOF / converter | Basic Oxygen Furnace: a vessel where oxygen is blown into hot metal to lower carbon and make steel. |
| Blast furnace | Tall furnace that turns iron ore into hot liquid iron; in NovaSteel it drives furnace-health and lining-wear scenarios. |
| Ladle | Vessel that carries molten metal between furnace, treatment, and caster stages. |
| Ladle furnace | Secondary metallurgy unit used to trim chemistry and temperature before casting. |
| Tundish | Intermediate vessel between ladle and continuous caster that stabilizes flow into the mould. |
| Caster | Continuous casting equipment that solidifies liquid steel into slabs, billets, or other semi-finished shapes. |
| Reheat furnace | Furnace that reheats slabs, billets, or bars before rolling. NovaSteel may advise energy-aware timing but never changes soak rules or recipes. |
| Refractory lining | Heat-resistant inner furnace wall. Worn lining raises thermal risk and is central to the 21-day RUL warning scenario. |
| Heat | One molten-metal batch processed together, identified by a heat number in genealogy data. |
| Tap-to-tap | Time from one furnace tap to the next; a common EAF productivity metric. |
| Billet | Long-products semi-finished steel shape, typically square or rectangular, used for bar or wire rod. |
| Slab | Flat semi-finished steel shape used for plate, hot strip, and coil production. |
| Scrap charge | Mix of scrap and other metallic inputs loaded into an EAF. |
| Tapping temperature | Molten-metal temperature at tapping; it affects downstream treatment, energy use, and quality. |
| Yield | Share of material that becomes acceptable product rather than scrap or rework. |
| Genealogy / batch genealogy | Trace from raw material lots to heat, ladle treatment, slab or billet, reheating, coil or bar, sample, test result, and shipment. |
| RUL | Remaining Useful Life: estimated time before an asset reaches a failure or intervention threshold. |
| OT | Operational Technology: plant equipment, automation, historians, and controls. NovaSteel reads only approved outbound data paths. |
| PLC | Programmable Logic Controller: industrial controller for equipment. NovaSteel does not write to PLCs. |
| SCADA | Supervisory Control and Data Acquisition: operator monitoring/control system. NovaSteel remains outside the SCADA control loop. |
| DCS | Distributed Control System: plant control platform common in process industries; not a NovaSteel command target. |
| CMMS | Computerized Maintenance Management System for assets, jobs, and work orders. NovaSteel simulates work-order flow only. |
| MES | Manufacturing Execution System for production execution and batch context; treated as a source system, not replaced. |
| ISA-95 / Purdue levels | Reference models separating enterprise IT, operations systems, control systems, and physical process layers. NovaSteel stays above control layers. |
| Setpoint | Target value sent to equipment or automation. NovaSteel may explain recommendations but never sends setpoints. |
| Interlock | Safety or equipment-protection logic that blocks unsafe actions. NovaSteel never bypasses or drives interlocks. |
| Industrial DMZ | Protected zone between OT and IT/cloud where gateways validate and buffer outbound telemetry. |

## Platform, Azure, and Fabric terms

| Term | Definition |
|---|---|
| Microsoft Fabric | NovaSteel's canonical analytics core for Eventstream, Eventhouse/KQL, OneLake/Lakehouse, notebooks, Direct Lake models, and Power BI. |
| OneLake | Fabric's unified storage layer for lakehouse files and Delta tables. |
| Lakehouse | Fabric data store combining lake files with managed tables; NovaSteel uses landing and core lakehouses. |
| Eventhouse | Fabric real-time analytical store for hot telemetry, alarms, gateway health, and operational investigation. |
| KQL Database | Kusto Query Language database inside Eventhouse; used for time-series operational queries, not long-term master data. |
| Eventstream | Fabric streaming ingestion component. NovaSteel uses `es-ns-telemetry-v1` with a Custom Endpoint. |
| Real-Time Intelligence (RTI) | Fabric capability set for streaming ingestion, Eventhouse, real-time dashboards, and event-driven notifications. |
| Direct Lake | Power BI mode reading Fabric Lakehouse tables directly, avoiding a separate imported dataset for governed semantic reporting. |
| Power BI semantic model | Business model of facts, dimensions, measures, roles, and security over gold tables. |
| Delta table | Transactional table format used by Lakehouse bronze, silver, and gold data. |
| Medallion bronze / silver / gold | Data quality layers: raw immutable envelopes, cleaned/conformed facts and dimensions, then business-ready star-schema facts. |
| Azure Container Apps | Azure hosting target for the portal, BFF, relays, and jobs in the Sweden Central demo deployment. |
| Event Hubs | Azure ingestion buffer and replay boundary for outbound plant telemetry before the managed-identity relay. |
| Key Vault | Azure secret and key store; production design favours identity over stored secrets. |
| Managed Identity | Workload identity assigned by Azure so services authenticate without embedded credentials. |
| Entra ID | Microsoft identity platform used for workload identity, user access, RBAC, OIDC, and MSAL-based browser sign-in. |
| Azure AI Foundry / Microsoft Foundry | Azure platform used for governed model, agent, and knowledge capabilities when tenant gates are met. |
| Foundry Agent Service | Hosted agent runtime. NovaSteel keeps deterministic calculations in Python and exposes only restricted proposal tools to operations agents. |
| Foundry IQ / Web IQ | Foundry knowledge sources for procedure and optionally web-grounded retrieval; web mode is off by default and DPO-gated. |
| Azure AI Search | Approved procedure search index with hybrid retrieval; drafts and unapproved transcripts are excluded. |
| Application Insights | Azure observability component for traces, metrics, logs, and agent-run telemetry. |
| Bicep | Azure infrastructure-as-code language used for NovaSteel resource definitions. |
| OIDC | OpenID Connect federation used by CI/CD and workloads to avoid long-lived deployment secrets. |

## NovaSteel-specific terms

| Term | Definition |
|---|---|
| AxelorMetal | Fictitious four-country steel producer used by the NovaSteel demo. |
| BFF | Backend for Frontend: the FastAPI layer that shapes browser APIs, applies authorization, mediates adapters, and hides backend complexity. |
| Portal shell | Blazor WebAssembly outer shell that owns routing, navigation, locale, chrome, capacity status, and MFE hosting. |
| Analytics MFE | React/TypeScript MUI/D3 analytics microfrontend embedded in the shell for data-dense operational screens. |
| Dockview workspace | Dockable panel layout used on every analytics route; operators can rearrange panels and reset screen layouts. |
| Copilot chat panel | Outer Dockview chat surface that explains screen meaning from grounding material; it has no tools and does not query operational stores. |
| Screen profile | Structured context for the active route, including concepts, permitted explanations, and source hints for Copilot grounding. |
| Grounding corpus | Approved screen profile, glossary definitions, and optional curated public context used to ground AI answers. |
| Fixture pack | Checksummed deterministic synthetic data pack used for offline and fallback reads. |
| Demo scope `NS-DEMO-*` | Synthetic namespace prefix for plants, data, and Fabric demo assets; never mixed with production workspaces or topics. |
| Synthetic demo data banner | Always-visible UI statement that the data is synthetic and not for operational control. |
| Audit hash-chain | Append-only audit pattern where each record references the previous hash so tampering becomes visible. |
| Capacity mediation | BFF state machine for Fabric demo capacity start, pause, and SKU requests with role checks, drain checks, and audit. |
| Simulated capacity action | Demo-mode capacity transition that updates UI and audit state without making an ARM call. |
| Critic loop | Review step where an AI-generated draft or recommendation is checked against rules, citations, and safety boundaries before presentation. |
| Agent handoff | Controlled routing from one advisory agent role to another; tool access remains restricted and authorization is rechecked. |
| Device simulator | In-process BFF simulator producing deterministic, clock-driven sensor telemetry for 17 devices and 91 sensors across four sites. |
| Fault incident catalog | Seven parameterized simulator incidents such as degrading furnace, cooling-water loss, sensor drift, dropout, energy spike, quality drift, and edge outage recovery. |
| Approach band | Sensor-status rule that marks warning/alarm near or beyond limits, avoiding a false healthy state when simulated values are clamped. |
| Gold contract v2 | `contracts/data/gold.v2.json`, the authoritative contract for gold tables and natural keys. |
| Data source indicator | `GET /v1/meta` provenance shown to the UI: Fabric lakehouse, simulator fixture, or visible Fabric fallback. |
| Proof of execution | Evidence that implemented screens, routes, checks, and artifacts support the claimed demo outcome. |
| Rating grid | Rubric-style scoring view used to evidence technical requirements and defense criteria. |
| Persona routes | Implemented route map from user personas to screen sections and default proof points. |

## AI and analytics terms

| Term | Definition |
|---|---|
| MILP | Mixed-Integer Linear Programming: optimization with linear constraints and integer decisions, used for feasible energy-dispatch advice. |
| PuLP | Python modeling library used to express the NovaSteel energy optimizer. |
| CBC solver | Open-source MILP solver used by the PuLP optimization worker. |
| Physics-informed model | Predictive model constrained by process relationships, such as thermal and cooling features for refractory lining RUL. |
| OLS regression | Ordinary Least Squares regression used in the local RUL implementation over thermal features. |
| P10 / P50 / P90 band | Uncertainty band showing low, median, and high forecast estimates, for example around RUL days. |
| R-squared | Fit statistic describing how much variation a regression explains; useful but not sufficient as safety evidence. |
| RAG | Retrieval-Augmented Generation: retrieving approved facts before an LLM answers. |
| Hybrid retrieval BM25 + cosine | Search combining keyword relevance with vector similarity for procedure and knowledge lookup. |
| RRF fusion | Reciprocal Rank Fusion: method for combining ranked retrieval results into one list. |
| Citation enforcement | Rule that grounded answers must cite the sources used or decline when support is insufficient. |
| PII redaction | Removal or masking of personal identifiers before content enters prompts, indexes, logs, or persisted records. |
| Content safety | Screening for unsafe, disallowed, or policy-sensitive content before or after model use. |
| Reasoning tier | Resolved model/effort level returned to the browser, such as default low-latency or high-reasoning mode. |
| Hallucination guard | Checks that prevent unsupported AI claims, including grounding overlap, source requirements, and structured refusal. |
| Deterministic fixture | Repeatable synthetic input/output set where the same seed and scenario produce the same evidence. |
| Feature snapshot | Versioned set of input features used by an optimizer or scorer so results can be reproduced. |

## Governance and regulatory acronyms

| Term | Definition |
|---|---|
| GDPR | General Data Protection Regulation. NovaSteel demo data is synthetic/non-personal, but production would still need privacy controls and erasure paths. |
| EU AI Act | EU risk-based AI regulation covering governance, transparency, human oversight, and conformity obligations. |
| EU ETS | EU Emissions Trading System for carbon allowances; NovaSteel tracks synthetic emissions and allowance exposure. |
| CBAM | Carbon Border Adjustment Mechanism for carbon costs on certain imported goods, including steel. |
| IEC 62443 | Industrial cybersecurity standards for OT systems, zones, conduits, and secure operations. |
| NIS2 | EU cybersecurity directive for essential and important entities, including incident and governance duties. |
| DPIA | Data Protection Impact Assessment, required when processing may create high privacy risk. |
| DPO | Data Protection Officer, the role that reviews privacy posture and gates options such as online search. |
| RAI | Responsible AI: governance practices for safe, fair, transparent, human-supervised AI use. |
| SBOM | Software Bill of Materials listing packages and components for supply-chain review. |
| CFS protected feed | Microsoft-protected package feed backed by Central Feed Services; restores must use approved feeds and not public fallbacks. |

## Related artifacts

[Solution Architecture](solution-architecture.md), [Data Baseline](data-baseline.md), [AI Design](ai-design.md), [Security Baseline](security-baseline.md), [Compliance](compliance.md), [Operating Model](operating-model.md), [Test Strategy](test-strategy.md), [Business Value Assessment](business-value-assessment.md), [Diagrams](diagrams/README.md).
