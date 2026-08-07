# Diagram - Key Persona Sequences

> **Artifact:** Diagram / Key Persona Sequences · **Audience:** product owners and reviewers · **Status:** baseline · **Source of truth:** [personas and journeys](../../business/personas-and-journeys.md)

## Purpose

This page connects the architecture to the principal NovaSteel decision journeys. Each sequence ends with human review, audit evidence, and no OT write or production-system commitment from NovaSteel.

## Plant Manager - site command review

```mermaid
sequenceDiagram
  actor Marc as Marc Weber, Plant Manager
  participant Portal as Site Command Center
  participant BFF as FastAPI BFF
  participant Fabric as Fabric KQL and gold facts
  participant Copilot as Tool-free Copilot chat
  participant Audit as Decision audit
  participant Team as Energy, reliability, and quality leads

  Marc->>Portal: Open Luxembourg command center
  Portal->>BFF: Request site KPI summary
  BFF->>Fabric: Read hot alerts and gold KPI facts
  Fabric-->>BFF: Freshness, alerts, energy, CO2, RUL, and quality rollup
  BFF-->>Portal: Return summary with data provenance
  Marc->>Portal: Ask why energy cost spiked
  Portal->>Copilot: Send question with active screen grounding
  Copilot-->>Portal: Explain from supplied sources only
  Marc->>Team: Review cross-domain trade-off
  Team-->>Marc: Recommend reline discussion and energy review
  Marc->>Portal: Record management decision and rationale
  Portal->>BFF: Submit approval record
  BFF->>Audit: Append decision evidence
  Audit-->>Portal: Audit reference
  Portal-->>Marc: Show decision recorded and no OT write
```

How to read this: Marc receives a site rollup and explanation, then records a management decision. The final system action is audit evidence, not an operational schedule, recipe, interlock, or PLC change.

## Energy Manager - dispatch recommendation

```mermaid
sequenceDiagram
  actor Sofia as Sofia Lindqvist, Energy Manager
  participant Portal as Energy Dispatch Optimization
  participant BFF as FastAPI BFF
  participant Optimizer as Python optimizer worker
  participant Fabric as Gold facts and market context
  participant PlantMgr as Plant Manager approval
  participant Audit as Decision audit

  Sofia->>Portal: Open spot price and load forecast
  Portal->>BFF: Request forecast and current constraints
  BFF->>Fabric: Read energy, production, maintenance, and market inputs
  Fabric-->>BFF: Context with freshness and source refs
  Sofia->>Portal: Run feasible schedule simulation
  Portal->>BFF: POST schedule simulate
  BFF->>Optimizer: Solve MILP with hard constraints
  Optimizer-->>BFF: Proposed schedule, savings, CO2, and violations equal zero
  BFF-->>Portal: Show proposal pending human approval
  Sofia->>PlantMgr: Escalate business trade-off
  PlantMgr-->>Sofia: Approve shadow recommendation
  Sofia->>Portal: Record approval with reason code
  Portal->>BFF: POST recommendation approval
  BFF->>Audit: Append simulated approval and rationale
  Audit-->>Portal: Audit reference
  Portal-->>Sofia: Show shadow approval and no schedule write
```

How to read this: the optimizer computes a feasible proposal, but the platform records only a simulated or shadow approval in the baseline. A real production schedule connector is a separately governed future phase.

## Reliability Engineer - furnace lining forecast

```mermaid
sequenceDiagram
  actor Tomas as Tomas Rossi, Reliability Engineer
  participant Portal as Furnace Lining RUL Dashboard
  participant BFF as FastAPI BFF
  participant Scoring as Python RUL scorer
  participant Fabric as Silver features and gold RUL facts
  participant PlantMgr as Plant Manager
  participant Audit as Decision audit

  Tomas->>Portal: Open furnace lining alert
  Portal->>BFF: Request RUL forecast and drivers
  BFF->>Fabric: Read feature snapshot and prior predictions
  Fabric-->>BFF: Thermal features and audit lineage
  BFF->>Scoring: Score physics-informed RUL model
  Scoring-->>BFF: P10, P50, P90, risk score, and drivers
  BFF-->>Portal: Show forecast with confidence band
  Tomas->>Portal: Compare reline timing options
  Portal->>BFF: Request what-if maintenance window
  BFF-->>Portal: Return recommendation pending decision
  Tomas->>PlantMgr: Propose day-18 reline discussion
  PlantMgr-->>Tomas: Approve maintenance planning discussion
  Tomas->>Portal: Create synthetic work-order proposal
  Portal->>BFF: Submit proposal and rationale
  BFF->>Audit: Append work-order proposal evidence
  Audit-->>Portal: Audit reference
  Portal-->>Tomas: Show proposal recorded and no CMMS or OT write
```

How to read this: Tomás can create a synthetic CMMS-linked proposal for the demo, but NovaSteel does not update the production CMMS or plant equipment.

## Quality Engineer - in-line deviation risk

```mermaid
sequenceDiagram
  actor Jens as Jens Bakker, Quality Engineer
  participant Portal as Quality Batches and Genealogy
  participant BFF as FastAPI BFF
  participant Scoring as Python quality scorer
  participant Fabric as Genealogy and model facts
  participant Procedure as Approved plant procedure
  participant Audit as Decision audit

  Jens->>Portal: Open active heat risk view
  Portal->>BFF: Request batch genealogy and risk
  BFF->>Fabric: Read quality, chemistry, asset, and inference context
  Fabric-->>BFF: Genealogy and current risk features
  BFF->>Scoring: Score bounded quality what-if
  Scoring-->>BFF: Risk, drivers, and corrective-action suggestion
  BFF-->>Portal: Show suggestion pending review
  Jens->>Procedure: Check approved plant procedure
  Procedure-->>Jens: Confirm allowed escalation path
  Jens->>Portal: Approve corrective-action documentation
  Portal->>BFF: Submit investigation note and decision
  BFF->>Audit: Append quality decision evidence
  Audit-->>Portal: Audit reference
  Portal-->>Jens: Show record saved and no recipe or setpoint write
```

How to read this: quality recommendations stay bounded and documentary. Any real process intervention happens through existing plant procedures outside NovaSteel, then the outcome is recorded for evidence and model feedback.

## Knowledge Engineer - procedure publication

```mermaid
sequenceDiagram
  actor Pieter as Pieter Claes, Knowledge Engineer
  participant Studio as Knowledge Capture Studio
  participant BFF as FastAPI BFF
  participant Speech as Azure Speech
  participant Orch as knowledge-orchestrator
  participant Foundry as Foundry Agent Service
  participant Search as AI Search approved index
  participant Audit as Decision audit

  Pieter->>Studio: Start consent-bound interview workflow
  Studio->>BFF: Create interview session
  BFF->>Speech: Submit approved audio for fast transcription
  Speech-->>BFF: Transcript with metadata
  BFF->>Orch: Build structured draft request
  Orch->>Foundry: Generate procedure draft from approved context
  Foundry-->>Orch: Draft with citations and risk notes
  Orch-->>Studio: Present draft for human review
  Pieter->>Studio: Edit and approve publication
  Studio->>BFF: Submit reviewed procedure version
  BFF->>Search: Index approved version only
  BFF->>Audit: Append publication evidence
  Audit-->>Studio: Audit reference
  Studio-->>Pieter: Show published procedure and no unreviewed instruction
```

How to read this: the agent drafts, but Pieter publishes. Drafts and unapproved transcripts do not become operational instructions or generally retrievable knowledge.

## Sustainability Officer - emissions and audit review

```mermaid
sequenceDiagram
  actor Amina as Amina Haddad, Sustainability Officer
  participant Portal as Sustainability and ETS Cockpit
  participant BFF as FastAPI BFF
  participant Fabric as Gold emissions and decision facts
  participant EnergyMgr as Energy Manager
  participant PlantMgr as Plant Manager
  participant Audit as Audit trail

  Amina->>Portal: Open emissions ledger
  Portal->>BFF: Request portfolio CO2 and ETS exposure
  BFF->>Fabric: Read emissions, energy, and dispatch audit facts
  Fabric-->>BFF: Trend, target gap, allowance exposure, and drivers
  BFF-->>Portal: Show portfolio and lagging site drill-down
  Amina->>EnergyMgr: Review rejected recommendation reasons
  EnergyMgr-->>Amina: Confirm mitigation options
  Amina->>PlantMgr: Escalate site trajectory risk
  PlantMgr-->>Amina: Approve mitigation review
  Amina->>Portal: Generate board-ready summary
  Portal->>BFF: Request report evidence package
  BFF->>Audit: Read decision lineage and export event
  Audit-->>Portal: Evidence package reference
  Portal-->>Amina: Show report generated and no operational control write
```

How to read this: Amina influences action through escalation and reporting. NovaSteel provides traceable evidence, not direct control of schedules, process parameters, or plant systems.

## Persona-to-route table

| Persona | Primary route from the root README | Decision supported | Human approval point |
|---|---|---|---|
| Plant Manager | `/lu/command-center` | Cross-domain site trade-offs and audit review | Manager records decision and rationale. |
| Energy Manager | `/lu/energy-optimization/spot-price-schedule` | Accept, modify, or reject dispatch recommendation | Energy Manager and Plant Manager approve shadow decision. |
| Reliability Engineer | `/lu/furnace-health/lining-forecast` | Recommend reline timing based on RUL forecast | Reliability Engineer proposes and Plant Manager approves discussion. |
| Quality Engineer | `/lu/quality/batches` | Quarantine, release, or document corrective action | Quality Engineer approves documentation under plant procedure. |
| Knowledge Engineer | `/lu/knowledge-hub/procedures` | Approve and publish reviewed procedures | Knowledge Engineer edits and approves publication. |
| Sustainability Officer | `/lu/sustainability-compliance/emissions-ledger` | Escalate emissions trajectory and prepare evidence | Sustainability Officer escalates and leadership approves mitigation review. |

## Related artifacts

[Glossary](../glossary.md) · [Solution Architecture](../solution-architecture.md) · [Data Baseline](../data-baseline.md) · [AI Design](../ai-design.md) · [Security Baseline](../security-baseline.md) · [Compliance](../compliance.md) · [Operating Model](../operating-model.md) · [Test Strategy](../test-strategy.md) · [Business Value Assessment](../business-value-assessment.md)
