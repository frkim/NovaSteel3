# NovaSteel artifacts

> **Artifact:** Artifact index · **Audience:** all · **Status:** baseline · **Source of truth:** [solution architecture](../architecture/solution-architecture.md)

## Purpose

This folder holds the condensed, one-page **artifact set** for NovaSteel: a
consistent series of single-page documents that summarise the project for
architecture review, security review, compliance review, operations handover,
and business sign-off. Each page is a *summary* artifact — the authoritative,
long-form documents remain under [`docs/`](../README.md) and are linked from
every page as the source of truth.

## Artifact set

| # | Artifact | Audience | Answers the question |
|---|---|---|---|
| 1 | [Glossary](glossary.md) | All | What does this term mean in NovaSteel? |
| 2 | [Diagrams](diagrams/README.md) | Architects | What does the system look like? |
| 3 | [Solution Architecture](solution-architecture.md) | Architects, engineering | How is it built and why? |
| 4 | [Data Baseline](data-baseline.md) | Data engineering, governance | What data exists, at what grain, under what contract? |
| 5 | [AI Design](ai-design.md) | Data science, risk | What do the models and agents do, and where is the human? |
| 6 | [Security Baseline](security-baseline.md) | Security, risk | How is it protected, and what is still open? |
| 7 | [Compliance](compliance.md) | Legal, compliance, DPO | Which regulations apply, and what is the posture? |
| 8 | [Operating Model](operating-model.md) | Operations, platform team | Who runs it, how, and to what service level? |
| 9 | [Test Strategy](test-strategy.md) | QA, engineering | How do we know it works? |
| 10 | [Business Value Assessment](business-value-assessment.md) | Executives, sponsors | Is it worth doing, and on what evidence? |

## Diagram set

| Diagram | Purpose |
|---|---|
| [System Context (C4)](diagrams/system-context.md) | Actors, systems, and boundaries around NovaSteel |
| [Medallion data flow](diagrams/medallion-data-flow.md) | Bronze / silver / gold path through Microsoft Fabric |
| [Agents orchestration](diagrams/agents-orchestration.md) | Knowledge orchestration, critic loop, and grounding boundary |
| [Deployment and region](diagrams/deployment-and-region.md) | Azure topology, EU residency, and recovery posture |
| [Key persona sequence](diagrams/key-persona-sequence.md) | End-to-end decision journeys per persona |

Editable diagram masters (Excalidraw) live in
[`docs/architecture/diagrams/`](../architecture/diagrams/README.md).

## How to read this set

1. **New to the project?** Start with the [Glossary](glossary.md), then the
   [System Context diagram](diagrams/system-context.md).
2. **Reviewing the design?** Read [Solution Architecture](solution-architecture.md),
   then [Data Baseline](data-baseline.md) and [AI Design](ai-design.md).
3. **Reviewing risk?** Read [Security Baseline](security-baseline.md) and
   [Compliance](compliance.md).
4. **Taking it into service?** Read [Operating Model](operating-model.md) and
   [Test Strategy](test-strategy.md).
5. **Deciding whether to fund a pilot?** Read
   [Business Value Assessment](business-value-assessment.md).

## Honesty rules applied to every artifact

- NovaSteel is **decision support only**. No page may describe an OT control,
  PLC, interlock, furnace, recipe, setpoint, schedule-commit, or CMMS write,
  because none exists on any path.
- All demonstration data is **deterministic synthetic and non-personal**.
- Measured demonstration results are reported separately from **pilot targets**;
  the two are never merged into a single headline figure.
- Anything not yet provisioned or validated in a target tenant is labelled
  **gated** rather than presented as delivered.

## Related documentation

| Topic | Document |
|---|---|
| Documentation index | [`docs/README.md`](../README.md) |
| Authoritative architecture and ADRs | [`docs/architecture/solution-architecture.md`](../architecture/solution-architecture.md) |
| Deployment topology | [`docs/architecture/deployment-topology.md`](../architecture/deployment-topology.md) |
| Business brief | [`docs/usecase/usecase.md`](../usecase/usecase.md) |
| Illustrated application guide (EN) | [`docs/presentation/assets/app-guide/en/README.md`](../presentation/assets/app-guide/en/README.md) |
| Demo runbook | [`docs/demo/demo-runbook.md`](../demo/demo-runbook.md) |
| Package-feed security policy | [`docs/tech/security_requirement.md`](../tech/security_requirement.md) |
