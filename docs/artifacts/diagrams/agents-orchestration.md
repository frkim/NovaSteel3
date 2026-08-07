# Diagram - Agents Orchestration

> **Artifact:** Diagram / AI Agents Orchestration · **Audience:** AI architects and security reviewers · **Status:** baseline · **Source of truth:** [solution architecture](../../architecture/solution-architecture.md)

## Purpose

This page shows the NovaSteel agent topology and the grounded knowledge-answer path. It distinguishes Copilot chat, which receives prompt-supplied grounding and no tools, from operations agents that can call deterministic BFF tools only as proposal surfaces.

## Orchestration topology

```mermaid
flowchart TB
  subgraph Browser["Browser and route context"]
    User["Persona user<br/>active route and site"]
    CopilotPanel["Docked Copilot chat<br/>meaning and explanation only"]
    OpsAgentPanel["Operations agent route<br/>proposal questions"]
    User --> CopilotPanel
    User --> OpsAgentPanel
  end

  subgraph BffBoundary["FastAPI BFF boundary"]
    BFF["BFF authz and audit<br/>role plant and idempotency checks"]
    ChatRoute["POST /v1/copilot/chat<br/>tool-free chat"]
    AgentRoute["POST /v1/copilot/agent<br/>tool-owning agents only"]
    KnowledgeQuery["POST /v1/knowledge/query<br/>grounded RAG"]
    BFF --> ChatRoute
    BFF --> AgentRoute
    BFF --> KnowledgeQuery
  end

  subgraph Orchestrator["knowledge-orchestrator"]
    GroundingBuilder["Grounding builder<br/>screen profile glossary corpus"]
    ConversationStore["In-process conversations<br/>owner-scoped and restart-cleared"]
    RAGPipeline["RAG safety pipeline<br/>retrieve ground generate critic safety cite"]
    AgentRouter["Deterministic agent router<br/>keyword and manifest driven"]
    Manifest["Agent manifest invariant<br/>readers have no function tools"]
  end

  subgraph FoundryPlane["Foundry Agent Service<br/>one project novasteelv3"]
    ChatModel["Chat deployment<br/>default and high reasoning tiers"]
    ProcedureAgent["Procedure agent<br/>Foundry IQ knowledge base"]
    WebAgent["Web-search reader<br/>DPO-gated and off by default"]
    EnergyAgent["Energy specialist<br/>simulate_energy_dispatch"]
    MaintenanceAgent["Maintenance specialist<br/>lining_rul_forecast"]
    CarbonAgent["Carbon specialist<br/>carbon_footprint_summary"]
    QualityAgent["Quality specialist<br/>quality_yield_what_if"]
    OpsOrchestrator["Operations orchestrator<br/>spans multiple calculation domains"]
  end

  subgraph DataAndTools["Governed data and deterministic tools"]
    Search["Azure AI Search<br/>approved procedures only"]
    PromptShields["Prompt Shields and Content Safety"]
    Optimizer["Python optimizer<br/>feasible schedule proposal"]
    Scoring["Python scoring<br/>RUL and quality proposal"]
    GoldFacts["Gold facts and audit records<br/>Fabric Lakehouse"]
    NoDataPlane["Copilot chat has no KQL Lakehouse or API tools"]
  end

  CopilotPanel --> BFF
  OpsAgentPanel --> BFF
  ChatRoute --> GroundingBuilder
  GroundingBuilder --> ConversationStore
  GroundingBuilder --> ChatModel
  GroundingBuilder --> NoDataPlane
  ChatModel --> ChatRoute
  KnowledgeQuery --> RAGPipeline
  RAGPipeline --> PromptShields
  RAGPipeline --> Search
  RAGPipeline --> ProcedureAgent
  ProcedureAgent --> RAGPipeline
  AgentRoute --> AgentRouter
  AgentRouter --> Manifest
  Manifest --> EnergyAgent
  Manifest --> MaintenanceAgent
  Manifest --> CarbonAgent
  Manifest --> QualityAgent
  Manifest --> OpsOrchestrator
  Manifest -.->|"reject readers on tool route"| ProcedureAgent
  Manifest -.->|"reject readers on tool route"| WebAgent
  EnergyAgent -->|"client-side tool through BFF"| Optimizer
  MaintenanceAgent -->|"client-side tool through BFF"| Scoring
  QualityAgent -->|"client-side tool through BFF"| Scoring
  CarbonAgent -->|"client-side tool through BFF"| GoldFacts
  OpsOrchestrator -->|"tool proposals through BFF"| Optimizer
  OpsOrchestrator -->|"tool proposals through BFF"| Scoring
  Optimizer --> GoldFacts
  Scoring --> GoldFacts
  GoldFacts --> BFF
```

How to read this: the chat route and agent route are separate admission surfaces. The chat route cannot call tools or query Fabric directly. The operations route admits only agents that declare calculation tools in the manifest, and the BFF tool body re-applies the caller's role and plant scope before returning a proposal.

## Grounded knowledge question sequence

```mermaid
sequenceDiagram
  actor Persona as Persona user
  participant Portal as Copilot panel
  participant BFF as FastAPI BFF
  participant Orch as knowledge-orchestrator
  participant SafetyIn as Input safety screen
  participant Retrieve as Hybrid retrieval
  participant Ground as Grounding guard
  participant Model as Foundry or local generator
  participant Critic as Critic loop
  participant SafetyOut as Output safety screen
  participant Cite as Citation enforcer

  Persona->>Portal: Ask screen-aware knowledge question
  Portal->>BFF: Send question, route, site, and locale
  BFF->>Orch: Authorize caller and create correlation id
  Orch->>SafetyIn: Check input content policy
  SafetyIn-->>Orch: Allowed or blocked
  Orch->>Retrieve: Retrieve approved procedure chunks
  Retrieve-->>Orch: BM25 and vector candidates
  Orch->>Ground: Apply content-term overlap guard
  Ground-->>Orch: Grounded chunks or no grounded source
  Orch->>Model: Generate answer from supplied grounding
  Model-->>Orch: Draft answer with source references
  Orch->>Critic: Check faithfulness and scope
  Critic-->>Orch: Accept or request repair
  Orch->>SafetyOut: Check output content policy and redact PII
  SafetyOut-->>Orch: Allowed or blocked
  Orch->>Cite: Enforce per-sentence citations
  Cite-->>Orch: Citation result
  alt Grounding, safety, and citations pass
    Orch-->>BFF: Answer with citations, sources, and resolved tier
    BFF-->>Portal: Respond with grounded answer
    Portal-->>Persona: Show answer and source list
  else Any guard fails
    Orch-->>BFF: Structured decline with reason
    BFF-->>Portal: Respond with decline
    Portal-->>Persona: Show decline and next safe action
  end
```

How to read this: a knowledge answer must retrieve approved content, survive grounding checks, pass safety screens, and carry citations. If any control fails, the service declines rather than inventing or using ungrounded model knowledge.

## Guardrails and ADR alignment

| Guardrail | Repository baseline |
|---|---|
| Copilot chat has no tools | ADR-011 states chat receives no tools and answers only from prompt-supplied grounding material. |
| Chat has no data-plane access | Chat does not query KQL, Lakehouse, operational APIs, or Fabric values; the dashboard remains the source of values. |
| Conversations are in-process | ADR-012 keeps Copilot chat history in the BFF process, owner-scoped, restart-cleared, and not persisted to Fabric. |
| Deterministic compute remains in Python | ADR-006 keeps MILP dispatch, RUL, quality, and carbon calculations outside LLM reasoning. |
| Human approval remains mandatory | ADR-007 requires explicit approval for safety-adjacent or financial decisions and forbids automatic operational commitments. |
| Single Foundry project with manifest boundary | ADR-020 places reader and tool-calling agents in one project but enforces the no-reader-tools invariant in the agent manifest and tests. |
| RAG safety pipeline | Input and output safety, hybrid retrieval, overlap guard, PII redaction, citation enforcement, and structured decline are required. |
| Online search is gated | Web IQ or web-search grounding is off by default and needs DPO approval because it leaves the Azure compliance boundary. |

## Related artifacts

[Glossary](../glossary.md) · [Solution Architecture](../solution-architecture.md) · [Data Baseline](../data-baseline.md) · [AI Design](../ai-design.md) · [Security Baseline](../security-baseline.md) · [Compliance](../compliance.md) · [Operating Model](../operating-model.md) · [Test Strategy](../test-strategy.md) · [Business Value Assessment](../business-value-assessment.md)
