# Diagram - System Context (C4)

> **Artifact:** Diagram / System Context · **Audience:** architects · **Status:** baseline · **Source of truth:** [solution architecture](../../architecture/solution-architecture.md)

## Purpose

This page shows NovaSteel as a C4-style decision-support platform for AxelorMetal. It separates users, external systems, the NovaSteel system boundary, and the container responsibilities that keep analytics advisory-only with no OT control write path.

## System context

```mermaid
flowchart TB
  PlantManager["Plant Manager<br/>site decisions"]
  EnergyManager["Energy Manager<br/>dispatch review"]
  ReliabilityEngineer["Reliability Engineer<br/>RUL review"]
  QualityEngineer["Quality Engineer<br/>genealogy and risk"]
  KnowledgeEngineer["Knowledge Engineer<br/>procedure approval"]
  SustainabilityOfficer["Sustainability Officer<br/>CO2 and ETS review"]

  subgraph AxelorMetal["AxelorMetal decision makers"]
    PlantManager
    EnergyManager
    ReliabilityEngineer
    QualityEngineer
    KnowledgeEngineer
    SustainabilityOfficer
  end

  NovaSteel["NovaSteel decision-support platform<br/>Fabric-centered analytics and advisory AI"]

  subgraph PlantEstate["Four-country steel estate"]
    Luxembourg["Luxembourg HQ plant<br/>NS-DEMO-LUX-01"]
    Germany["Germany plant"]
    Belgium["Belgium plant"]
    Spain["Spain plant"]
    OTGateway["Industrial DMZ gateway<br/>outbound only"]
    Luxembourg --> OTGateway
    Germany --> OTGateway
    Belgium --> OTGateway
    Spain --> OTGateway
  end

  subgraph ExternalSystems["External systems and services"]
    PlantOT["PLC SCADA historian<br/>no cloud inbound path"]
    BusinessSystems["MES ERP LIMS CMMS<br/>batch extracts only"]
    MarketFeed["Licensed energy market feed"]
    Entra["Microsoft Entra ID"]
    AzureFabric["Microsoft Fabric and Azure<br/>EU primary services"]
    PowerBI["Power BI reports<br/>internal viewer access"]
  end

  PlantManager -->|"reviews KPIs and approvals"| NovaSteel
  EnergyManager -->|"simulates and approves recommendations"| NovaSteel
  ReliabilityEngineer -->|"reviews forecast and work-order proposal"| NovaSteel
  QualityEngineer -->|"reviews risk and root cause"| NovaSteel
  KnowledgeEngineer -->|"approves procedures"| NovaSteel
  SustainabilityOfficer -->|"reviews emissions and audit evidence"| NovaSteel

  PlantOT -->|"plant-local protocols"| OTGateway
  OTGateway -->|"schema-valid telemetry<br/>outbound TLS only"| NovaSteel
  BusinessSystems -->|"incremental extracts"| NovaSteel
  MarketFeed -->|"licensed price and carbon context"| NovaSteel
  NovaSteel -->|"user authentication"| Entra
  NovaSteel -->|"Eventstream Eventhouse OneLake Lakehouse Foundry"| AzureFabric
  AzureFabric -->|"semantic model and reports"| PowerBI
  NovaSteel -.->|"no OT command path"| PlantOT

  classDef person fill:#e8f4f8,stroke:#0078d4,color:#1f1f1f
  classDef system fill:#d5e8d4,stroke:#107c10,color:#1f1f1f
  classDef external fill:#fff2cc,stroke:#d6b656,color:#1f1f1f
  classDef boundary fill:#f5f5f5,stroke:#666666,color:#1f1f1f

  class PlantManager,EnergyManager,ReliabilityEngineer,QualityEngineer,KnowledgeEngineer,SustainabilityOfficer person
  class NovaSteel system
  class PlantOT,BusinessSystems,MarketFeed,Entra,AzureFabric,PowerBI,Luxembourg,Germany,Belgium,Spain,OTGateway external
  class AxelorMetal,PlantEstate,ExternalSystems boundary
```

How to read this: the central system is NovaSteel, not a plant controller. Human personas consume recommendations and evidence, while OT gateways send only outbound telemetry. The dotted edge marks a deliberate absence: NovaSteel does not send commands to PLCs, interlocks, recipes, schedules, or CMMS production connectors.

## Container view

```mermaid
flowchart TB
  subgraph Browser["Browser experience"]
    Shell["Blazor WebAssembly portal shell<br/>routing MSAL locale host bridge"]
    MFE["React TypeScript analytics MFE<br/>MUI D3 Dockview workspaces"]
    CopilotPanel["Docked Copilot panel<br/>screen-aware explanations"]
    Shell <--> MFE
    MFE <--> CopilotPanel
  end

  subgraph ApiLayer["Application API layer"]
    BFF["FastAPI BFF<br/>authz shaping SSE audit mediation"]
    DeviceAdapter["In-process device simulator adapter<br/>six devices and thirty-four sensors"]
    KnowledgeOrchestrator["knowledge-orchestrator<br/>grounding workflow and RAG"]
    BFF <--> DeviceAdapter
    BFF <--> KnowledgeOrchestrator
  end

  subgraph AdvisoryServices["Python advisory services"]
    Optimizer["optimizer-worker<br/>PuLP CBC feasible energy schedule"]
    Scoring["scoring-worker<br/>RUL and quality risk"]
    IngestRelay["ingest-relay<br/>Event Hubs to Eventstream"]
    CapacityOperator["capacity-operator<br/>demo capacity requests"]
  end

  subgraph AzureIngress["Azure Sweden Central ingress"]
    EventHubs["Azure Event Hubs<br/>raw replay buffer"]
    KeyVault["Key Vault<br/>managed identity secrets"]
    AppInsights["Application Insights<br/>OpenTelemetry"]
  end

  subgraph FabricCore["Microsoft Fabric core"]
    Eventstream["Eventstream<br/>es-ns-telemetry-v1"]
    Eventhouse["Eventhouse and KQL<br/>hot telemetry"]
    Landing["Lakehouse landing<br/>bronze envelopes"]
    CoreLakehouse["Lakehouse core<br/>silver and gold Delta"]
    Semantic["Direct Lake semantic model<br/>sm-novasteelv3-operations"]
    Reports["Power BI and RTI dashboards"]
    Eventstream --> Eventhouse
    Eventstream --> Landing
    Landing --> CoreLakehouse
    CoreLakehouse --> Semantic
    Semantic --> Reports
    Eventhouse --> Reports
  end

  subgraph AiPlane["AI services"]
    Foundry["Foundry Agent Service<br/>one project roster"]
    Speech["Azure Speech<br/>fast transcription"]
    Search["Azure AI Search<br/>approved procedures only"]
  end

  Simulators["Deterministic synthetic simulators<br/>fixed seeds and manifests"]
  OTGateway["Industrial DMZ gateway<br/>outbound producer"]

  Shell -->|"HTTPS user token"| BFF
  MFE -->|"BFF APIs and SSE"| BFF
  CopilotPanel -->|"question and active screen"| BFF
  BFF --> Optimizer
  BFF --> Scoring
  BFF -->|"read adapters"| Eventhouse
  BFF -->|"read adapters"| CoreLakehouse
  BFF --> KeyVault
  BFF --> AppInsights
  Optimizer --> CoreLakehouse
  Scoring --> CoreLakehouse
  KnowledgeOrchestrator --> Foundry
  KnowledgeOrchestrator --> Speech
  KnowledgeOrchestrator --> Search
  Foundry -->|"restricted tools through BFF only"| BFF
  OTGateway -->|"AMQP over TLS"| EventHubs
  EventHubs --> IngestRelay
  IngestRelay -->|"managed identity"| Eventstream
  Simulators -->|"cloud demo publish or offline pack"| Eventstream
  Simulators -->|"fixture fallback"| BFF
  CapacityOperator -->|"ARM capacity operations<br/>demo only"| FabricCore
```

How to read this: browser code never receives Fabric, Foundry, Key Vault, or Azure management credentials. The BFF is the enforcement point for role, plant, idempotency, audit, and fallback behavior. Advisory workers compute proposals, not committed operational actions.

## C4 notation legend

| C4 element | Used here as | NovaSteel examples |
|---|---|---|
| Person | Human role making a decision or approval | Plant Manager, Energy Manager, Reliability Engineer, Quality Engineer, Knowledge Engineer, Sustainability Officer |
| Software system | The system whose responsibilities are being explained | NovaSteel decision-support platform |
| External system | System outside the NovaSteel boundary | PLC and historian estate, MES, ERP, LIMS, CMMS, market feed, Entra ID, Power BI |
| Container | Deployable or separately owned runtime or data store | Blazor shell, React MFE, FastAPI BFF, Python workers, Event Hubs, Fabric Lakehouses, Foundry, AI Search |
| Boundary | Trust, ownership, location, or deployment grouping | Browser, Azure ingress, Fabric core, AI plane, four-country plant estate |

## Key constraints captured

| Constraint | Diagram cue |
|---|---|
| Decision support only | Human personas approve or reject proposals before any real-world action. |
| No OT write path | The only OT edge is outbound telemetry from the industrial DMZ gateway. |
| Fabric is the analytics core | Eventstream, Eventhouse, OneLake, Lakehouse, Direct Lake, and reports sit in the central data plane. |
| Synthetic demo fallback | Simulators publish to cloud demo paths and also feed the offline fixture fallback. |
| Tool boundary for agents | Foundry can reach calculations only through BFF-governed, role-checked tools. |

## Related artifacts

[Glossary](../glossary.md) · [Solution Architecture](../solution-architecture.md) · [Data Baseline](../data-baseline.md) · [AI Design](../ai-design.md) · [Security Baseline](../security-baseline.md) · [Compliance](../compliance.md) · [Operating Model](../operating-model.md) · [Test Strategy](../test-strategy.md) · [Business Value Assessment](../business-value-assessment.md)
