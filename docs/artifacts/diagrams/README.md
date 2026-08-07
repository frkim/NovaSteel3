# Diagram artifacts

> **Artifact:** Diagram index · **Audience:** architects and reviewers · **Status:** baseline · **Source of truth:** [solution architecture](../../architecture/solution-architecture.md)

## Purpose

This index collects the Mermaid diagram artifacts for the NovaSteel baseline. The diagrams align with the editable Excalidraw masters and keep the same advisory-only, synthetic-data, Microsoft Fabric-centered architecture story.

## Diagram set

| Page | Description |
|---|---|
| [System Context](system-context.md) | C4-style system context and container view for the portal, BFF, advisory services, Fabric core, ingestion boundary, and external actors. |
| [Medallion Data Flow](medallion-data-flow.md) | End-to-end telemetry and analytical data flow through Event Hubs, Eventstream, Eventhouse, OneLake bronze, silver, gold, BFF, and Power BI. |
| [Agents Orchestration](agents-orchestration.md) | Knowledge orchestrator, Foundry Agent Service, Copilot grounding boundary, operations-agent handoff, and grounded RAG safety loop. |
| [Deployment and Region](deployment-and-region.md) | EU deployment topology across plant sites, Azure Sweden Central, Fabric SaaS, and tested-not-automatic West Europe recovery. |
| [Key Persona Sequence](key-persona-sequence.md) | Sequence diagrams for the core Plant Manager, Energy Manager, Reliability Engineer, Quality Engineer, Knowledge Engineer, and Sustainability journeys. |

## Editable diagram masters

The editable masters live in [architecture diagrams](../../architecture/diagrams/README.md) and should remain the source for hand-edited visual variants.

| Excalidraw master | Use with this diagram set |
|---|---|
| [end-to-end-architecture.excalidraw](../../architecture/diagrams/end-to-end-architecture.excalidraw) | System context, container view, medallion data flow, and AI topology. |
| [deployment-topology.excalidraw](../../architecture/diagrams/deployment-topology.excalidraw) | Deployment, regional placement, recovery posture, and managed-service boundaries. |
| [demo-flow.excalidraw](../../architecture/diagrams/demo-flow.excalidraw) | Persona sequence diagrams and the 10-minute defense storyline. |
| [business-value-chain.excalidraw](../../architecture/diagrams/business-value-chain.excalidraw) | Executive context, persona outcomes, governance guardrails, and value-chain explanations. |

## Reading order

1. Start with [System Context](system-context.md) to understand NovaSteel as a decision-support system.
2. Continue to [Medallion Data Flow](medallion-data-flow.md) to see why Fabric is the analytical core.
3. Read [Agents Orchestration](agents-orchestration.md) for the AI and Copilot safety boundary.
4. Use [Deployment and Region](deployment-and-region.md) to place the components in the EU deployment model.
5. Finish with [Key Persona Sequence](key-persona-sequence.md) to connect the architecture to the live demonstration routes.

## Related artifacts

[Glossary](../glossary.md) · [Solution Architecture](../solution-architecture.md) · [Data Baseline](../data-baseline.md) · [AI Design](../ai-design.md) · [Security Baseline](../security-baseline.md) · [Compliance](../compliance.md) · [Operating Model](../operating-model.md) · [Test Strategy](../test-strategy.md) · [Business Value Assessment](../business-value-assessment.md)
