# 15 · Glossary

**Audience:** complete newcomers who need steel, industry, platform, and AI terms in plain language.  
**Reading time:** ~18 minutes.  
**Related routes:** all guide routes; especially `/lu/furnace-health/lining-forecast`, `/lu/energy-optimization/spot-price-schedule`, `/lu/quality/batches`, `/lu/sustainability-compliance/emissions-ledger`.  
**Last updated:** 2026-07-27  
**Language:** 🇫🇷 [Version française](../fr/15-glossary.md)

---

Every “where you meet it” screen name below is drawn from the implemented persona routes and proof map (`apps\analytics-mfe\src\personaRoutes.ts:16-182`; `docs\presentation\proof_of_execution.md:439-447`). Data is synthetic and advisory-only throughout (`apps\portal-shell\Layout\MainLayout.razor:118-122`; `docs\architecture\solution-architecture.md:22-29`).

## A. Steel & industry terms

| English term | French term | Plain-language definition | Where you meet it in NovaSteel |
|---|---|---|---|
| BOF / converter | Convertisseur BOF | Basic Oxygen Furnace: a vessel where oxygen is blown into hot metal to reduce carbon and make steel. | Quality; AxelorMetal Steel Knowledge |
| Blast furnace | Haut fourneau | A tall furnace that uses coke and hot air to turn iron ore into hot liquid iron. It is where much of the heat, energy, and lining-wear risk begins. | Furnace Health; AxelorMetal public website |
| CMMS | GMAO / CMMS | Computerized Maintenance Management System: software for maintenance jobs, assets, and work orders. NovaSteel simulates CMMS-linked work-order flow only. | Furnace Health › Maintenance Planner |
| Campaign | Campagne | The operating period between major furnace rebuilds or relines. A longer campaign means more production before a costly stop. | Furnace Health › Maintenance Planner |
| Carbon intensity | Intensité carbone | CO₂ emitted per unit of output, usually per tonne of steel or per MWh. Lower is better for EU ETS and sustainability tracking. | Sustainability › Emissions Ledger |
| Coil | Bobine | A long strip of rolled steel wound into a giant roll. Coils are common final products for automotive and manufacturing customers. | Quality › Batch Quality |
| Control chart | Carte de contrôle | A chart used in statistical process control to show whether a process is stable or drifting. | Quality › Defect Analytics (SPC) |
| Cp / Cpk | Cp / Cpk | Capability indices: simple statistics that show whether a process can stay inside specification limits and how centered it is. | Quality › Defect Analytics (SPC) |
| Day-ahead market | Marché day-ahead | Electricity market where prices for tomorrow are set today, often hour by hour. | Energy Optimization › Spot & Schedule |
| Demand response | Effacement / réponse à la demande | Changing electricity use when the grid or price signal asks for it. In NovaSteel this is advisory scheduling, not automatic plant control. | Energy Optimization › Load-Shift Simulator |
| EU ETS | SEQE-UE / EU ETS | European Union Emissions Trading System: companies need allowances for CO₂ emissions. | Sustainability › ETS Exposure |
| Genealogy | Généalogie matière | Trace from heat to slab to coil to lab result or defect. It helps explain where a quality issue came from. | Quality › Batch Quality |
| Hearth | Creuset | Lower part of a blast furnace where hot metal collects. Its thermal condition matters for lining health. | Furnace Health › Thermal Explorer |
| Heat / batch | Coulée / lot | A heat is one molten-metal batch processed together; a batch is a group of production records treated as one unit. | Quality › Batch Quality |
| Hot metal | Fonte liquide | Liquid iron from a blast furnace before final steel conversion. | Operations; AxelorMetal Steel Knowledge |
| Industrial DMZ | DMZ industrielle | A protected network zone between operational technology and IT/cloud systems. It reduces the risk of direct cloud-to-plant access. | Device Operations; Architecture guide |
| Load shifting | Déplacement de charge | Moving flexible energy-intensive work away from expensive or high-carbon hours. NovaSteel proposes it for humans to approve. | Energy Optimization › Spot & Schedule |
| MTBF | MTBF | Mean Time Between Failures: average time an asset runs before failing. | Device Operations › Device Fleet |
| MWh | MWh | Megawatt-hour: a unit of energy. One MWh is one megawatt used for one hour. | Command Center; Energy Optimization |
| OT / IT | OT / IT | Operational Technology runs plant equipment; Information Technology runs business/cloud systems. NovaSteel keeps advisory analytics separate from control. | Device Operations; Platform Ops |
| PLC | Automate programmable / PLC | Programmable Logic Controller: industrial computer that controls equipment. NovaSteel does not write to PLCs. | Device Operations |
| Pareto | Pareto | A ranking chart that shows the few causes responsible for most defects or losses. | Quality › Defect Analytics (SPC) |
| RUL | Durée de vie résiduelle (RUL) | Remaining Useful Life: estimated time before an asset reaches a failure or intervention threshold. | Furnace Health › Lining Forecast |
| Refractory lining | Revêtement réfractaire | Heat-resistant inner wall of a furnace. Worn lining increases failure risk and drives the 21-day warning use case. | Furnace Health › Lining Forecast |
| SCADA | SCADA | Supervisory Control and Data Acquisition: systems operators use to monitor/control plant equipment. NovaSteel is outside that control loop. | Device Operations |
| SPC | MSP / SPC | Statistical Process Control: using statistics to detect process drift before defects grow. | Quality › Defect Analytics (SPC) |
| Scope 1 / 2 / 3 | Scopes 1 / 2 / 3 | Greenhouse-gas categories: direct emissions, purchased energy emissions, and value-chain emissions. | Sustainability › Emissions Ledger |
| Scrap / rework | Rebut / reprise | Material rejected or requiring extra processing. Less scrap/rework means better yield and lower cost. | Quality › Batch Quality |
| Spot price | Prix spot | Current market price for electricity, often changing by hour. | Energy Optimization › Spot & Schedule |
| Taphole | Trou de coulée | Opening used to drain hot metal from a blast furnace. | Furnace Health › Thermal Explorer |
| Thermal signature | Signature thermique | Pattern of temperatures, heat flux, and cooling behavior that can indicate lining condition. | Furnace Health › Thermal Explorer |
| Tuyère | Tuyère | Nozzle that blows hot air into a blast furnace. Problems around tuyères can affect heat patterns. | Furnace Health › Thermal Explorer |
| Work order | Ordre de travail | A maintenance task record: what to inspect, when, and who owns it. NovaSteel creates synthetic examples only. | Furnace Health › Maintenance Planner |
| Yield | Rendement | Share of production that becomes acceptable product instead of scrap or rework. | Quality; Executive Overview |
| t CO₂e | t CO₂e | Tonnes of carbon-dioxide equivalent: a standard way to compare greenhouse gases. | Sustainability › Emissions Ledger |

## B. Platform & tech terms

| English term | French term | Plain-language definition | Where you meet it in NovaSteel |
|---|---|---|---|
| Audit hash-chain | Chaîne de hachage d’audit | An append-only audit pattern where each record references the previous hash, making tampering visible. | Proof of Execution; Sustainability › Audit & Reports |
| Azure AI Foundry | Azure AI Foundry | Microsoft platform for building and governing AI apps and agents. In the demo, local deterministic adapters may stand in for live Foundry calls. | Knowledge Hub; Proof of Execution |
| BFF | BFF | Backend for Frontend: an API layer shaped for the browser so the UI does not call every backend directly. | Portal shell; Platform Ops |
| Blazor WebAssembly | Blazor WebAssembly | C# front-end runtime used for the NovaSteel outer shell, routing, chrome, theme, locale, and capacity panel. | Every route / shell |
| Deterministic seed | Graine déterministe | A fixed starting value that makes synthetic data repeatable. The same demo inputs produce the same demo story. | Device Operations; guided demo |
| Direct Lake | Direct Lake | Power BI mode that reads Fabric Lakehouse data efficiently without importing every row into a separate dataset. | Architecture; Executive Overview |
| Dockview | Dockview | React docking layout library used for draggable/resizable panels. | Every dashboard screen |
| EU AI Act | Règlement européen sur l’IA | EU law focused on AI risk, transparency, human oversight, and governance. | Proof of Execution; Sustainability › Audit & Reports |
| Eventhouse / KQL | Eventhouse / KQL | Fabric real-time analytical store queried with Kusto Query Language. | Architecture; Device Operations |
| Eventstream | Eventstream | Fabric streaming ingestion component for real-time events. | Architecture; Device Operations |
| GDPR | RGPD | EU privacy law governing personal data. NovaSteel uses synthetic/non-personal data in the demo. | Proof of Execution; Sustainability › Audit & Reports |
| Grounding | Ancrage | Connecting an AI answer to approved facts, screen context, or documents so it is not free-floating text. | Copilot; Knowledge Hub |
| Idempotency key | Clé d’idempotence | Unique key that lets a server safely treat repeated requests as the same action. | Platform Ops › Capacity |
| LLM | Grand modèle de langage (LLM) | Large Language Model: AI that generates or summarizes text from prompts and context. | Copilot; Knowledge Hub |
| Lakehouse | Lakehouse | Data store that combines file-based lake storage with warehouse-like tables. | Architecture; Sustainability |
| MILP / PuLP / CBC | MILP / PuLP / CBC | Mixed-integer linear optimization and common Python/open-source solver tools for schedule recommendations. | Energy Optimization |
| Managed identity | Identité managée | Cloud identity assigned to a workload so it can authenticate without stored secrets. | Architecture; Platform Ops |
| Medallion bronze / silver / gold | Médaillon bronze / silver / gold | Data quality layers: raw/landing, cleaned/conformed, and business-ready facts. | Architecture; Proof of Execution |
| Microfrontend | Microfrontend | A front-end app embedded inside another front-end shell. NovaSteel uses React inside a Blazor shell. | Every dashboard screen |
| Microsoft Fabric | Microsoft Fabric | Microsoft analytics platform that can host streaming, lakehouse, KQL, semantic models, and Power BI. | Platform Ops; Architecture |
| OLS regression | Régression OLS | Ordinary Least Squares: a simple regression method used to fit a line and estimate relationships. | Furnace Health › Lining Forecast |
| OneLake | OneLake | Fabric’s unified data lake storage layer. | Architecture |
| Power BI | Power BI | Microsoft reporting and dashboard tool. NovaSteel target architecture can surface governed semantic-model reports. | Executive Overview; Architecture |
| RAG | RAG | Retrieval-Augmented Generation: retrieving relevant facts before asking an LLM to answer. | Copilot; Knowledge Hub |
| Semantic model | Modèle sémantique | Business-friendly model of tables, measures, relationships, and security used by reports. | Executive Overview; Sustainability |
| Synthetic data | Données synthétiques | Artificial data built for demo and tests, not real plant or personal data. | Every screen |
| WCAG 2.2 AA | WCAG 2.2 AA | Accessibility target for keyboard, screen reader, contrast, focus, and non-color-only cues. | Shell footer; all screens |

---

◀ Previous [14 · Cross-cutting features](14-cross-cutting-features.md) · ▲ Index ([README.md](README.md)) · Next ▶ [16 · Traceability matrix](16-traceability-matrix.md)
