# Compliance

> **Artifact:** Compliance · **Audience:** legal, compliance, DPO, architecture · **Status:** baseline · **Source of truth:** [regulatory and compliance analysis](../business/compliance/README.md)

NovaSteel is a synthetic-data demonstration and planning baseline, not a legal opinion, conformity assessment, MRV filing, or certification claim. This artifact summarises the regulations documented in the repository, the obligations they create or would create, current evidence, and the open decisions that block non-synthetic pilot or production use.

## Regulatory scope

| Regulation | Applies because | Primary obligation | NovaSteel posture | Evidence |
|---|---|---|---|---|
| GDPR | Knowledge capture can process operator voice/text; access/audit logs may contain personal data | Lawful basis, transparency, minimisation, Art.17 erasure, records, DPIA | Demo data is synthetic/non-personal; Art.17 service exists; lawful basis and DPIA are pilot gates | [other regulations GDPR](../business/compliance/other-regulations.md), [security governance](../tech/security-governance-and-threat-model.md) |
| EU AI Act | MILP optimizer, RUL model, quality prediction, and GenAI/RAG influence industrial decisions | Risk classification, transparency, logging, oversight, AI literacy, possible high-risk duties | High-risk-adjacent and high-risk-ready; formal Legal classification is open | [EU AI Act analysis](../business/compliance/eu-ai-act.md) |
| EU ETS + MRV | AxelorMetal steel installations are ETS-covered; platform models Scope 1/2 and allowance exposure | MRV methodology, record-keeping, verifier, annual report, allowance surrender | Management information only; no approved monitoring plan or verifier | [EU ETS analysis](../business/compliance/eu-ets.md) |
| CBAM | Iron and steel embedded-emissions data is commercially relevant | Embedded-emissions provenance and verifier-grade data where applicable | Contextual; not an importer flow; lineage is useful but not implemented as CBAM filing | [EU ETS CBAM section](../business/compliance/eu-ets.md) |
| IEC 62443 | Platform is OT-adjacent to furnaces, EAFs, rolling mills, historian/DMZ gateways | Zones/conduits, SL targets, FR1-FR7, secure development | Design-conformance mapping only; no certification claimed | [IEC 62443 analysis](../business/compliance/iec-62443.md) |
| NIS2 | Basic metals manufacturing is an Annex II sector; NovaSteel is supporting ICT/OT | Risk management, incident handling, 24h/72h/1-month reporting, management accountability | Designed; entity registration and tabletop exercise are gates | [other regulations NIS2](../business/compliance/other-regulations.md) |
| CSRD / ESRS | A large EU steel producer reports climate metrics under ESRS E1 | Scope 1/2/3, energy, governance, assurance | In flux; NovaSteel can supply operational climate data, not assured statement | [other regulations CSRD](../business/compliance/other-regulations.md) |
| Machinery Regulation | Would apply if AI becomes a machinery safety component | Safety-component conformity and AI/ML safety provisions | Out of scope by advisory/no-write-back design; re-assess before write-back | [EU AI Act analysis](../business/compliance/eu-ai-act.md) |
| IEC 61508 / IEC 61511 | Plant SIS remains independent | Preserve safety loop independence and SIL claims | Out of scope; NovaSteel adds no L0-L1 control component | [other regulations functional safety](../business/compliance/other-regulations.md) |
| EU Data Act | OT/IoT data provenance, access, and cloud switching may matter | Data access, portability, interoperability | Open Delta/Parquet and IaC posture is aligned; watch item | [other regulations Data Act](../business/compliance/other-regulations.md) |
| Cyber Resilience Act | Could apply if NovaSteel is placed on EU market as product with digital elements | Secure-by-default, vulnerability handling, SBOM, reporting | Good-practice alignment; formal conformity only if commercialised | [other regulations CRA](../business/compliance/other-regulations.md) |
| DORA | Financial-sector regulation | ICT operational resilience for financial entities | Not applicable to steel manufacturer; concepts mirrored voluntarily | [other regulations DORA](../business/compliance/other-regulations.md) |
| Energy Efficiency Directive / ISO 50001 | Large energy consumers need audits or energy management | Energy-performance evidence and EnMS support | Optimizer/KPIs support evidence; certification is organisational | [other regulations EED](../business/compliance/other-regulations.md) |
| Industrial Emissions Directive | Steel installations operate under environmental permits and BAT | BAT/EMS/transformation-plan evidence | Contextual; not implemented as permit reporting system | [other regulations IED](../business/compliance/other-regulations.md) |
| ISO/IEC 27001 | Information-security management alignment | ISMS controls, risk treatment, audit evidence | Aligned, not certified | [other regulations ISO 27001](../business/compliance/other-regulations.md) |
| ISO/IEC 42001 / NIST AI RMF | AI management and risk framework | AI policy, impact assessment, lifecycle governance | Aligned as management-system target, not certified | [other regulations ISO 42001 / NIST](../business/compliance/other-regulations.md) |

## EU AI Act positioning

- The repository identifies four AI/algorithmic systems: energy-dispatch optimizer, furnace-lining RUL, in-line quality prediction, and GenAI knowledge capture / grounded RAG.
- None implements an Article 5 prohibited practice: no social scoring, biometric categorisation, emotion recognition, worker performance surveillance, or predictive individual-risk profiling is present.
- Annex III high-risk classification is argued out because there is no industrial-process-optimization entry; Legal must confirm the critical-infrastructure nuance before pilot.
- Article 6(1) product-safety high-risk route is held out by design: NovaSteel is not a machinery safety component because it has no safety function and no actuator path.
- Adopted posture is conservative: high-risk-adjacent, with Art. 8-15 style controls designed so a Legal reclassification should not require architecture changes.
- Human oversight is the strongest boundary: every consequential energy, maintenance, quality, or procedure output is advisory and human-reviewed.
- Transparency is active for GenAI interactions: users see assistant/enterprise-data-protection copy and operators are informed before interviews.
- Logging is a core implemented control: SHA-256 hash-chained audit captures input reference, model version, output, human action, outcome, and verification state.
- Cybersecurity controls include Prompt Shields, spotlighting, dual-stage content safety, PII redaction, grounding/citation enforcement, and deny-by-default agent tool access.
- Open AI Act decision: formal Legal/Compliance classification of AI-1..AI-4, FRIA/DPIA coordination, deployer operating procedure, AI-literacy attendance records, and model GPAI status confirmation.

## GDPR posture

- Current demo posture uses deterministic synthetic/non-personal data, so no production lawful basis is asserted for the demo dataset.
- Non-synthetic operator voice/text would require DPO/Legal confirmation of lawful basis, consent/notice wording, retention, access rights, and DPIA before pilot.
- Data-subject rights are engineered through the Art.17 erasure service: transcripts and Copilot conversations are hard-deleted, procedure attribution is pseudonymized, and audit receives a tombstone.
- The immutable audit chain is not rewritten; `chainVerifiedBefore` and `chainVerifiedAfter` preserve accountability while personal content is removed.
- Records of processing are planned through Purview catalog and lineage rather than a manual spreadsheet.
- Data minimisation controls include in-process Copilot chat history, browser-side dictation for the chat surface, redaction of sensitive audit fields, and retention limits.
- DPIA status is open: GDPR Art.35 DPIA is a roadmap gate before real operator data or high-risk voice processing.
- DPO sign-off remains open for lawful basis, West Europe recovery copy of Highly Confidential data, Online Search/Web IQ, and production retention.

## Emissions and sustainability reporting

- EU ETS applies to the fictional operator because integrated iron-and-steel installations are covered activities; NovaSteel itself is an internal analytics surface.
- The Fabric gold model computes synthetic `fact_emissions_daily`: Scope 1, Scope 2, total CO₂e, demo free allocation, EUA price signal, exposure, and `calculation_version`.
- The sustainability UI includes an Emissions Ledger route, ETS Exposure route, and Audit & Reports route; the ledger is append-only decision support.
- The optimizer treats CO₂ as a first-class term in the dispatch objective, but explicit EUA-price weighting is documented as an extension.
- The ETS/CBAM caveat is explicit: figures are synthetic management information, not a regulated MRV report, not a verified CSRD statement, and not a CBAM filing.
- MRV-grade use still needs calibrated meters, authority-approved Monitoring Plan, accredited verifier, legal installation mapping, Union Registry linkage, real allocation/benchmark values, and 10-year ETS monitoring retention.

## Industrial cyber-security (IEC 62443)

- The zone/conduit model maps Purdue L0-L3 plant systems, L3.5 industrial DMZ, and L4-L5 enterprise/cloud analytics.
- NovaSteel supplies no L0-L2 control component and no software conduit below the DMZ; any operator action occurs through existing separately governed plant systems.
- Target security levels documented in the IEC analysis: Z-CTRL SL 3, Z-SUP SL 2-3, Z-HIST SL 2, Z-DMZ SL 3, and Z-CLOUD SL 2.
- Foundational requirements are addressed through Entra/managed identity/OIDC, RBAC/PIM, mTLS and hash-chain integrity, encryption/labels, restricted data flow, Sentinel/Defender for IoT response, and store-and-forward/replay.
- Current status is design conformance on a synthetic demo; gateway BOM, physical DMZ appliance, SPAN/TAP sensors, 62443-4-1 formal assessment, and third-party SL-C assessment remain pilot/production gates.

## Current posture summary

| Domain | Green evidence | Yellow / designed | Red / open gate |
|---|---|---|---|
| Advisory boundary | No OT write path, no PLC/setpoint/recipe/schedule commit, simulator is synthetic only | Future human-approved write-back is discussed only as Phase 2 | Any write-back requires new safety case and threat model |
| Synthetic demo data | Demo entities use `NS-DEMO-*`; UI and README label data as synthetic/non-personal | Cloud demo still needs target-tenant Fabric proof | Real data cannot flow before DPO/Legal/OT gates |
| AI governance | Human oversight, logging, transparency, Prompt Shields, content safety, and redaction are documented | High-risk-adjacent posture is conservative | Formal Legal AI Act classification and FRIA are open |
| Privacy | Art.17 erasure design and pseudonymized receipts exist | Purview records of processing are the target operating model | DPIA and lawful basis are open |
| Emissions | Synthetic Scope 1/2 and ETS exposure are computed and surfaced | `calculation_version` gives methodology traceability | Accredited verifier and Monitoring Plan are absent |
| Industrial cyber | IEC 62443 zone/conduit model and SL targets are documented | Cloud-side controls are IaC-backed | Live OT gateway and third-party assessment are absent |
| Supply chain | Protected feeds, SBOM, scans, OIDC CI/CD are present | Dependency SLAs and release approvals need operations cadence | Public-registry fallback is prohibited |

## Decision-support boundary

- The platform can recommend, explain, simulate, and log; it cannot actuate, commit, schedule, trade, or publish without a human-controlled workflow.
- A human approval event is compliance evidence, not a hidden automation step; the model or agent cannot approve its own recommendation.
- Demonstration capacity and device operations are synthetic/simulated; they do not manage production capacity or production devices.
- The emissions ledger is valuable audit evidence for a future MRV process, but it is not a filed report and must not be presented as verified.
- If a future phase introduces CMMS/MES write-back, machinery safety functions, or closed-loop control, the current scoping conclusions no longer apply until Legal, Safety, OT, DPO, CISO, and RAI Board re-approve.

## Compliance roadmap

| Item | Owner | Status | Gate |
|---|---|---|---|
| DPIA completed and accepted for real operator data | DPO | Open | G0.1 enter shadow pilot |
| DPO/Legal sign-off on lawful basis, retention, consent | DPO / Legal | Open | G0.2 enter shadow pilot |
| NIS2 entity registration | CISO | Open | G0.3 enter shadow pilot |
| Responsible-AI review of four AI systems and oversight design | RAI Board | Designed | G0.4 enter shadow pilot |
| OT/site approval for read-only historian tap and DMZ BOM | OT/ICS Engineer | Open | G0.5 enter shadow pilot |
| AI-literacy training for pilot users | RAI Board / HR | Open | G0.6 enter shadow pilot |
| Evidence spine live: hash-chain, lineage, retention | Platform Lead | Implemented/design | G0.7 enter shadow pilot |
| Shadow-mode accuracy validated against real outcomes | Data Science Lead | Open | G1.1 enable guarded write-back |
| AI Act conformity documentation / Annex IV-style file | RAI Board / Legal | Open | G1.2 enable guarded write-back |
| Write-back safety case and Machinery / AI Act reassessment | Safety Engineer / Legal | Open | G1.3 enable guarded write-back |
| 62443 SL-C assessment for any write-back conduit | OT/ICS Engineer | Open | G1.4 enable guarded write-back |
| Approval guardrails tested for reason-coded human approval | Product Lead | Designed | G1.5 enable guarded write-back |
| NIS2 incident-reporting tabletop | CISO | Open | G1.6 enable guarded write-back |
| Accredited verifier for ETS/CSRD figures | Sustainability Lead | Open | G2.1 steady-state governance |
| Approved Monitoring Plan and MRR-tiered metering | Sustainability Lead | Open | G2.2 steady-state governance |
| Continuous human-oversight audit stable | RAI Board | Open | G2.3 steady-state governance |
| 10-year ETS audit retention operational | Platform Lead | Open | G2.4 steady-state governance |
| Notified-body / product questions resolved if commercialised | Legal | Open | G2.5 steady-state governance |

## Evidence register

| Obligation | Evidence artifact | Location in repo |
|---|---|---|
| Advisory-only / no OT write | Architecture guardrails and deployment topology | `docs/architecture/solution-architecture.md`, `docs/architecture/deployment-topology.md` |
| Security governance and STRIDE | Security architecture, gates, threat model | `docs/tech/security-governance-and-threat-model.md` |
| GDPR Art.17 erasure | Erasure service and audit invariant | `services/knowledge-orchestrator/src/knowledge_orchestrator/erasure.py`, security §25.1 |
| AI Act logging / accountability | Hash-chained audit implementations | `services/bff-api/src/bff_api/audit.py`, `services/knowledge-orchestrator/src/knowledge_orchestrator/audit.py` |
| Durable audit in cloud mode | Azure Table adapter and storage module | `services/bff-api/src/bff_api/adapters/azure_audit.py`, `infra/bicep/modules/storage.bicep` |
| PII redaction | Redaction module and RAG pipeline | `services/knowledge-orchestrator/src/knowledge_orchestrator/pii.py`, security §25.2 |
| Protected package feeds | Feed config and validation scan | `pip.conf`, `NuGet.Config`, `.npmrc`, `tools/validation/verify_protected_feeds.py` |
| SBOM and security scan | Validation scripts and CI jobs | `tools/validation/generate_sbom.py`, `tools/validation/security_scan.py`, `.github/workflows/ci.yml` |
| OIDC-only deployment | Infra scripts and workflows | `infra/scripts/deploy.ps1`, `.github/workflows/cd-infra.yml`, `.github/workflows/cd-services.yml` |
| Network guardrails | Azure Policy definitions | `infra/policy/definitions/deny-public-network-access.json`, `infra/policy/README.md` |
| ETS management information | Gold emissions model and UI screens | `fabric/lakehouse/sql/20_gold.sql`, `apps/analytics-mfe/src/components/screens/SustainabilityEmissions.tsx` |
| Compliance roadmap | Phase gates, RACI, residual risks | `docs/business/compliance/compliance-roadmap.md` |

## Open decisions

- DPO/Legal/DPIA sign-off for non-synthetic operator data, lawful basis, retention, consent, and subject-rights workflow.
- Formal EU AI Act classification for each AI system and decision on FRIA/deployer operating procedure before pilot.
- `ONLINE_SEARCH_MODE` / Web IQ / web-search grounding: off by default because it leaves the Azure compliance and geo boundary; DPO approval and domain restriction are required.
- Market-data licensing and price-provider terms before production recommendations use live market feeds.
- OT vendor, historian protocol, physical DMZ gateway BOM, and plant approval for read-only integration.
- Fabric tenant capacity/SKU/quota, Fabric item-level authorization, Custom Endpoint identity/network proof, and private-network validation for Foundry/Speech.
- ETS/CSRD status boundary: accredited verifier and approved Monitoring Plan before any figure is presented as regulated MRV or assured sustainability reporting.
- Production DR, performance, accessibility, live-cloud fallback rehearsal, and long-term ETS retention targets.

## Related artifacts

- [Glossary](glossary.md)
- [Diagrams](diagrams/README.md)
- [Solution Architecture](solution-architecture.md)
- [Data Baseline](data-baseline.md)
- [AI Design](ai-design.md)
- [Security Baseline](security-baseline.md)
- [Operating Model](operating-model.md)
- [Test Strategy](test-strategy.md)
- [Business Value Assessment](business-value-assessment.md)
