/**
 * Technical rating-grid catalog — the single source of truth for the
 * "Technical Requirements" screen.
 *
 * Each entry answers one criterion of `docs/tech/rating_grid.md` with a
 * self-assessed score, the evidence that supports it, the gap that keeps it
 * from a 5, and the concrete work that would close that gap. The narrative
 * long-form version lives in `docs/tech/technical-analysis.md`; this file is
 * what the running application renders, so the two must stay in step.
 *
 * Evidence labels are repo-relative paths and resolve to GitHub through
 * `githubUrlFor` in `proofCatalog.ts` — the same mechanism the proof register
 * uses, so a jury can click straight from a score to the code behind it.
 */

import type { ProofEvidence } from './proofCatalog'

export type TechCategory =
  | 'design'
  | 'development'
  | 'monitoring'
  | 'ai'
  | 'agentic'
  | 'architecture'
  | 'presentation'

/** Score awarded against the rubric's 5-point scale. */
export type TechScore = 1 | 2 | 3 | 4 | 5

export interface TechRequirement {
  id: string
  category: TechCategory
  /** Criterion name, verbatim from the rating grid. */
  criterion: string
  /** The rubric's own definition of a 5-point answer, verbatim. */
  excellentBar: string
  score: TechScore
  /** One-line self-assessment. */
  verdict: string
  /** How the solution answers the criterion, in plain language. */
  howMet: string
  evidence: ProofEvidence[]
  /** What is honestly missing. Required whenever the score is below 5. */
  gap?: string
  /** The concrete work that would raise the score. */
  uplift?: string
  /** Primary screen that demonstrates this criterion, `section/subView`. */
  primaryRoute?: string
}

export const TECH_CATEGORY_ORDER: TechCategory[] = [
  'design',
  'development',
  'monitoring',
  'ai',
  'agentic',
  'architecture',
  'presentation',
]

/** Maximum attainable score, i.e. the rubric's 60 points. */
export const TECH_MAX_SCORE = 60

export const TECH_GRADE_BANDS: Array<{ grade: string; min: number; max: number; label: string }> = [
  { grade: 'A', min: 54, max: 60, label: 'Exceptional implementation and architectural rigor' },
  { grade: 'B', min: 48, max: 53, label: 'Strong implementation with minor gaps' },
  { grade: 'C', min: 40, max: 47, label: 'Adequate implementation with room for improvement' },
  { grade: 'D/F', min: 0, max: 39, label: 'Incomplete or insufficient implementation' },
]

export const TECH_REQUIREMENTS: TechRequirement[] = [
  // -------------------------------------------------------------------- design
  {
    id: 'TR-DES-01',
    category: 'design',
    criterion: 'System architecture, modularity, scalability',
    excellentBar:
      'Clear, well-documented architecture with modular components and scalability considerations',
    score: 5,
    verdict: 'Documented, modular, and horizontally scalable by construction.',
    howMet:
      'The architecture is written down before it is coded: a Mermaid-documented solution architecture, an explicit deployment topology, and an OpenAPI 3.1 contract that the BFF is generated against. Six services deploy independently as Container Apps, each with its own managed identity and its own scale rule, over a Fabric lakehouse with enforced bronze/silver/gold contracts. Nothing shares a database; services talk over the contract or over the lake.',
    evidence: [
      {
        kind: 'doc',
        label: 'docs/architecture/solution-architecture.md',
        detail: 'Authoritative architecture: component map, data contracts, sequence diagrams.',
      },
      {
        kind: 'doc',
        label: 'docs/architecture/deployment-topology.md',
        detail: 'EU region placement (Sweden Central primary), network topology, DR posture.',
      },
      {
        kind: 'infra',
        label: 'infra/bicep/modules/containerapps.bicep',
        detail: 'Per-service Container App with VNet integration, zone redundancy and its own identity.',
      },
      {
        kind: 'infra',
        label: 'infra/bicep/modules/network.bicep',
        detail: 'Hub-and-spoke VNet with five subnets and deny-internet-inbound NSGs.',
      },
      {
        kind: 'infra',
        label: 'infra/bicep/modules/identity.bicep',
        detail: 'One user-assigned identity per service, plus GitHub OIDC federation.',
      },
      {
        kind: 'code',
        label: 'contracts/openapi/bff-api-v1.yaml',
        detail: 'OpenAPI 3.1 contract the front end and the BFF are both bound to.',
      },
      { kind: 'code', label: 'services/bff-api/.../routes.py', detail: 'The complete BFF domain route surface.' },
      { kind: 'ui', label: 'Platform Ops \u2192 Fabric Capacity', route: 'platform-ops/capacity' },
    ],
    primaryRoute: 'platform-ops/capacity',
  },
  {
    id: 'TR-DES-02',
    category: 'design',
    criterion: 'Use of design patterns',
    excellentBar: 'Appropriate and effective use of relevant design patterns',
    score: 5,
    verdict: 'Six named patterns, each chosen for a specific pressure, each unit-tested.',
    howMet:
      'Patterns are applied where they earn their keep rather than decoratively. Ports-and-adapters isolates every external dependency behind a Python Protocol, so the demo runs offline with the same code path. Strategy lets the energy optimizer fall back from MILP to a heuristic when the solver is unavailable. A State Graph makes the knowledge-capture workflow inspectable (it can render itself as Mermaid). Reciprocal Rank Fusion merges BM25 and semantic retrieval. An append-only hash chain makes the audit log tamper-evident.',
    evidence: [
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../state_graph.py',
        detail: 'StateGraph finite-state machine with to_mermaid() self-documentation.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../adapter_factory.py',
        detail: 'Hexagonal adapter selection: live Azure adapter or deterministic offline adapter.',
      },
      {
        kind: 'code',
        label: 'services/optimizer-worker/.../service.py',
        detail: 'Strategy: MILP first, deterministic heuristic as the documented fallback.',
      },
      { kind: 'code', label: 'services/optimizer-worker/.../milp.py', detail: 'PuLP/CBC MILP formulation.' },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../retrieval.py',
        detail: 'Hybrid retriever combining BM25 and cosine similarity via Reciprocal Rank Fusion.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../audit.py',
        detail: 'Append-only hash-chained audit log with verify().',
      },
      {
        kind: 'code',
        label: 'services/bff-api/.../idempotency.py',
        detail: 'Idempotency boundary keyed on the client-supplied request key.',
      },
      {
        kind: 'code',
        label: 'services/bff-api/.../errors.py',
        detail: 'Typed ApiError over a 15-value ErrorCode enum \u2014 no stringly-typed failures.',
      },
    ],
    primaryRoute: 'knowledge-hub/capture-status',
  },
  {
    id: 'TR-DES-03',
    category: 'design',
    criterion: 'Security',
    excellentBar: 'Thoughtful implementation of security',
    score: 5,
    verdict: 'Threat-modelled first, then implemented \u2014 not bolted on.',
    howMet:
      'An 80-page threat model drives the controls. Zero Trust throughout: managed identity for every service-to-service call, no connection strings, RBAC-only Key Vault behind a private endpoint, and Azure Policy guardrails that block non-compliant deployments. On the AI path specifically: consent is a state machine that gates capture, PII is detected and redacted across seven categories before any model sees a transcript, prompt injection is scanned and spotlighted, tool use runs against an allow-list with explicitly forbidden actions, and GDPR erasure crypto-shreds the source while appending a tombstone rather than rewriting the audit chain. Package restoration is pinned to Microsoft-protected feeds.',
    evidence: [
      {
        kind: 'doc',
        label: 'docs/security/security-governance-and-threat-model.md',
        detail: 'STRIDE threat model, control mapping, and the residual-risk register.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../pii.py',
        detail: 'Seven-category detection: email, phone, IBAN (mod-97), names, employee IDs, IPv4, DOB.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../consent.py',
        detail: 'ConsentRecord state machine; capture is refused without a live, in-scope grant.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../erasure.py',
        detail: 'GDPR Art. 17 crypto-shredding, pseudonymisation and tombstone append.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../prompt_defense.py',
        detail: 'Spotlighting plus injection scanning on every untrusted span.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../tools.py',
        detail: 'ToolRegistry with FORBIDDEN_TOOL_NAMES enforced at call time.',
      },
      { kind: 'code', label: 'services/bff-api/.../auth.py', detail: 'Nine app roles with per-role action maps.' },
      {
        kind: 'infra',
        label: 'infra/bicep/modules/keyvault.bicep',
        detail: 'RBAC-only Key Vault reachable solely through a private endpoint.',
      },
      {
        kind: 'infra',
        label: 'infra/bicep/modules/policy-assignments.bicep',
        detail: 'Azure Policy guardrails, including the Fabric SKU ceiling.',
      },
      { kind: 'infra', label: 'pip.conf', detail: 'Python restore pinned to the Microsoft-protected feed proxy.' },
      { kind: 'infra', label: 'NuGet.Config', detail: 'NuGet restore locked to the approved feed.' },
      { kind: 'ui', label: 'Compliance \u2192 GDPR & Consent', route: 'sustainability-compliance/audit' },
    ],
    primaryRoute: 'sustainability-compliance/audit',
  },

  // --------------------------------------------------------------- development
  {
    id: 'TR-DEV-01',
    category: 'development',
    criterion: 'Application Demo',
    excellentBar:
      'Clean and clear demonstration of the use case. Provides a compelling hook for executive audience',
    score: 4,
    verdict: 'Rehearsed, executive-legible, and resilient offline \u2014 but not every Fabric asset runs live.',
    howMet:
      'The demo is scripted to the minute against a 26-slide deck, and the application opens on a cross-persona Command Center that states the business problem before showing any telemetry. Every screen carries a use-case reference ID, so a non-technical audience can always see which line of the brief is being answered. Because the demo must not depend on network conditions, every Azure adapter has a deterministic offline twin that produces the same shapes \u2014 the demo degrades rather than fails.',
    evidence: [
      {
        kind: 'doc',
        label: 'docs/presentation/oral-defense-and-slide-plan.md',
        detail: '26 slides with per-slide timing against the 30/15/15 split.',
      },
      { kind: 'doc', label: 'docs/presentation/fiche-repetition-presentateur.md', detail: 'Presenter rehearsal sheet.' },
      { kind: 'doc', label: 'docs/presentation/faq.md', detail: 'Prepared answers for the 15-minute FAQ.' },
      {
        kind: 'code',
        label: 'apps/analytics-mfe/src/proof/proofCatalog.ts',
        detail: 'The 19-requirement register the reference badges resolve against.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../adapter_factory.py',
        detail: 'Graceful degradation: live adapter when configured, deterministic twin otherwise.',
      },
      { kind: 'ui', label: 'Command Center', route: 'command-center/overview' },
      { kind: 'ui', label: 'Proof of Execution', route: 'proof-of-execution/requirements' },
    ],
    gap: 'Some Fabric artefacts (notebooks, Activator rules, the RTI eventstream) are provisioned as templates and are demonstrated from captured output rather than executed live during the 10-minute demo window.',
    uplift:
      'Run one end-to-end Fabric pipeline live on the F2 capacity during the demo \u2014 eventstream ingest through the silver-to-gold notebook to an Activator alert \u2014 rather than replaying captured output.',
    primaryRoute: 'command-center/overview',
  },
  {
    id: 'TR-DEV-02',
    category: 'development',
    criterion: 'Implementation completeness',
    excellentBar: 'Fully implements all required features',
    score: 4,
    verdict: 'Every brief requirement is implemented and traceable; a few enterprise integrations are design-only.',
    howMet:
      'All 19 requirements of the use-case brief are implemented, each mapped to running code by the proof catalog, and a 20-gate repository validator enforces the mapping on every run. Four GitHub Actions workflows cover CI, infrastructure CD, service CD and CodeQL scanning. The BFF exposes the full contracted route surface, and 14 Bicep modules deploy the whole estate from one orchestrator.',
    evidence: [
      {
        kind: 'test',
        label: 'tools/validation/Validate-Repository.ps1',
        detail: '20 gates across 12 suites; fails the build on any contract or evidence drift.',
      },
      {
        kind: 'code',
        label: 'apps/analytics-mfe/src/proof/proofCatalog.ts',
        detail: '19 requirements, each with evidence and an explicit caveat where the demo is a surrogate.',
      },
      { kind: 'infra', label: '.github/workflows/ci.yml', detail: 'Component-scoped continuous integration.' },
      { kind: 'infra', label: '.github/workflows/cd-services.yml', detail: 'OIDC service deployment, no stored secrets.' },
      { kind: 'infra', label: '.github/workflows/codeql.yml', detail: 'CodeQL scanning for Python and TypeScript.' },
      { kind: 'infra', label: 'infra/bicep/main.bicep', detail: 'One orchestrator over 14 Bicep modules.' },
      { kind: 'ui', label: 'Proof of Execution', route: 'proof-of-execution/requirements' },
    ],
    gap: 'MES and batch-historian integrations are specified in the architecture but not implemented; the demo reads a synthetic feed in their place.',
    uplift:
      'Implement one real ingestion adapter against an OPC UA or MES test endpoint, so at least one integration is live rather than simulated.',
    primaryRoute: 'proof-of-execution/requirements',
  },

  // ---------------------------------------------------------------- monitoring
  {
    id: 'TR-MON-01',
    category: 'monitoring',
    criterion: 'Logging and metrics',
    excellentBar: 'Implements structured logging and relevant metrics',
    score: 5,
    verdict: 'OpenTelemetry end to end, with business KPIs treated as first-class metrics.',
    howMet:
      'Every service emits OpenTelemetry traces to Azure Monitor and structured JSON logs carrying the trace and span IDs, so a single correlation ID walks a request from the browser through the BFF into the workers. Beyond infrastructure metrics, the workers publish the business KPIs the brief actually asks about \u2014 energy per tonne, CO\u2082 intensity, RUL confidence, first-pass yield \u2014 as OTel gauges. Ten Bicep-defined alert rules and Fabric Activator rules turn those signals into notifications.',
    evidence: [
      {
        kind: 'code',
        label: 'services/bff-api/.../telemetry.py',
        detail: 'OTel tracer and JSON log formatter injecting trace/span context.',
      },
      {
        kind: 'code',
        label: 'services/scoring-worker/.../metrics.py',
        detail: 'RUL and quality KPI gauges.',
      },
      {
        kind: 'code',
        label: 'services/optimizer-worker/.../metrics.py',
        detail: 'Energy and CO\u2082 KPI gauges.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../telemetry.py',
        detail: 'handoff_span and critic_span helpers make agent steps visible in the trace.',
      },
      { kind: 'infra', label: 'infra/bicep/modules/alerts.bicep', detail: 'Ten alert rules over the KPI signals.' },
      {
        kind: 'infra',
        label: 'infra/bicep/modules/monitoring.bicep',
        detail: 'Log Analytics, Application Insights and Sentinel onboarding.',
      },
      {
        kind: 'infra',
        label: 'fabric/rti/activator-rules.template.json',
        detail: 'Real-Time Intelligence Activator notification rules.',
      },
      { kind: 'ui', label: 'Platform Ops \u2192 Cost & Telemetry', route: 'platform-ops/cost-telemetry' },
    ],
    primaryRoute: 'platform-ops/cost-telemetry',
  },

  // ------------------------------------------------------------------------ ai
  {
    id: 'TR-AI-01',
    category: 'ai',
    criterion: 'Use of AI technologies',
    excellentBar: 'Effective integration of AI models or services with clear purpose',
    score: 5,
    verdict: 'Four distinct AI techniques, each answering a named line of the brief.',
    howMet:
      'The brief names three AI infusion points and the solution implements all three with the appropriate technique for each. Furnace lining prediction is a physics-informed model: thermal features feed an OLS degradation fit, and the remaining useful life is reported as a P10/P50/P90 band via the delta method, not a bare point estimate. Energy dispatch is a genuine MILP solved with PuLP/CBC over spot prices and process constraints. Knowledge capture is consent-gated speech-to-text feeding a hybrid BM25-plus-semantic RAG pipeline with enforced grounding. A screen-aware Copilot spans all of it in five languages.',
    evidence: [
      {
        kind: 'code',
        label: 'services/scoring-worker/.../physics_features.py',
        detail: 'Thermal feature extraction and the OLS degradation fit.',
      },
      {
        kind: 'code',
        label: 'services/scoring-worker/.../rul_model.py',
        detail: 'Delta-method RUL with P10/P50/P90 confidence bands and MODEL_VERSION.',
      },
      { kind: 'code', label: 'services/optimizer-worker/.../milp.py', detail: 'PuLP/CBC MILP energy dispatch.' },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../retrieval.py',
        detail: 'Hybrid BM25 + cosine retrieval fused by RRF.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../grounding.py',
        detail: 'Answers without a supporting citation are refused, not guessed.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../audio.py',
        detail: 'Consent-gated Azure Speech transcription.',
      },
      { kind: 'test', label: 'tests/backend/test_physics_rul_model.py', detail: 'Physics model regression tests.' },
      { kind: 'test', label: 'tests/backend/test_optimizer_milp.py', detail: 'MILP solver tests.' },
      { kind: 'ui', label: 'Furnace Health \u2192 Lining Forecast', route: 'furnace-health/lining-forecast' },
      { kind: 'ui', label: 'Energy & Carbon \u2192 Dispatch Plan', route: 'energy-optimization/spot-price-schedule' },
    ],
    primaryRoute: 'furnace-health/lining-forecast',
  },
  {
    id: 'TR-AI-02',
    category: 'ai',
    criterion: 'AI model selection and deployment',
    excellentBar: 'Appropriate model choice and secure deployment strategy',
    score: 4,
    verdict: 'Tiered model choice deployed securely in the EU \u2014 but the lifecycle story is documented, not tooled.',
    howMet:
      'Models are chosen per task rather than uniformly: a general chat tier for conversational work and a reasoning tier for multi-step analysis, both served through Azure AI Foundry. Access uses DefaultAzureCredential with managed identity \u2014 there is no API key anywhere in the repository. Deployment is pinned to an EU Data Zone, and both the RUL model and the optimizer carry an explicit model version in their output so a prediction can be attributed to the code that made it. An offline evaluation runner scores retrieval and grounding quality.',
    evidence: [
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../copilot/agents.py',
        detail: 'Chat versus reasoning tier selection and the Foundry token scope.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../adapter_factory.py',
        detail: 'DefaultAzureCredential \u2014 managed identity, never a key.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../evaluation.py',
        detail: 'Offline evaluation runner over the retrieval and grounding corpora.',
      },
      {
        kind: 'infra',
        label: 'infra/bicep/modules/foundry-speech.bicep',
        detail: 'Foundry and Speech provisioning with identity-based access.',
      },
      { kind: 'doc', label: 'docs/architecture/deployment-topology.md', detail: 'EU Data Zone and region placement.' },
      { kind: 'test', label: 'tests/knowledge/test_evaluation.py', detail: 'Evaluation-runner tests.' },
    ],
    gap: 'There is no model registry artefact, training notebook or automated evaluation gate in the repository. Model versioning is a constant in code, and the physics model is fitted analytically rather than trained \u2014 so the lifecycle is described in documentation rather than enforced by tooling.',
    uplift:
      'Register the RUL model in an MLflow registry on Fabric, publish the training/fitting notebook, and wire the existing evaluation runner into CI as a release gate that blocks a regression in grounding or retrieval quality.',
    primaryRoute: 'knowledge-hub/procedures',
  },

  // ------------------------------------------------------------------- agentic
  {
    id: 'TR-AGT-01',
    category: 'agentic',
    criterion: 'Autonomy and orchestration',
    excellentBar: 'Agent demonstrates autonomous behavior and orchestrates tasks effectively',
    score: 5,
    verdict: 'A real state graph with autonomous safety work and a deliberate human gate.',
    howMet:
      'Knowledge capture is not a prompt chain \u2014 it is an explicit StateGraph whose nodes and transitions are declared, testable and renderable as a diagram. The agent runs the whole safety pipeline autonomously: consent verification, PII redaction, prompt-injection scanning, content safety screening, retrieval, grounding enforcement and a critic reflection pass. It then stops at a gated node and waits for an expert. Autonomy is bounded by design: the agent may draft, but only a human may publish.',
    evidence: [
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../state_graph.py',
        detail: 'Declared nodes, transitions and gated human-in-the-loop steps.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../orchestrator.py',
        detail: 'KnowledgeOrchestrator driving the graph end to end.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../procedure_workflow.py',
        detail: 'Draft \u2192 review \u2192 approve \u2192 publish transitions with role checks.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../tools.py',
        detail: 'Allow-listed tools; forbidden actions are rejected before execution.',
      },
      { kind: 'test', label: 'tests/knowledge/test_state_graph.py', detail: 'Graph transition and gate tests.' },
      { kind: 'test', label: 'tests/knowledge/test_orchestrator.py', detail: 'End-to-end orchestration tests.' },
      { kind: 'ui', label: 'Knowledge Hub \u2192 Capture Workflow', route: 'knowledge-hub/capture-status' },
    ],
    primaryRoute: 'knowledge-hub/capture-status',
  },
  {
    id: 'TR-AGT-02',
    category: 'agentic',
    criterion: 'Multi-agent coordination',
    excellentBar: 'Implements coordination patterns such as handoffs, reflections, or state graphs',
    score: 5,
    verdict: 'All three named patterns \u2014 handoff, reflection and state graph \u2014 are implemented and traced.',
    howMet:
      'The rubric names handoffs, reflections and state graphs; the solution implements each. The energy-dispatch agent hands off to the RUL/scoring agent through a typed protocol with a structured payload rather than shared mutable state, so a maintenance window discovered by one agent constrains the plan produced by the other. A critic agent reviews drafted procedures and returns structured findings, looping at most twice so the cost is bounded. Every handoff and critic iteration opens its own OpenTelemetry span, so the coordination is observable rather than implied.',
    evidence: [
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../handoff.py',
        detail: 'Typed handoff protocol between the dispatch and scoring agents.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../critic.py',
        detail: 'Critic/reflection loop capped at two iterations.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../telemetry.py',
        detail: 'handoff_span and critic_span \u2014 coordination visible in the trace.',
      },
      { kind: 'test', label: 'tests/knowledge/test_handoff.py', detail: 'Handoff protocol tests.' },
      { kind: 'test', label: 'tests/knowledge/test_critic.py', detail: 'Reflection-loop and bound tests.' },
      { kind: 'ui', label: 'AI Copilot \u2192 Agent Trace', route: 'knowledge-hub/procedures' },
    ],
    primaryRoute: 'knowledge-hub/procedures',
  },

  // -------------------------------------------------------------- architecture
  {
    id: 'TR-ARC-01',
    category: 'architecture',
    criterion: 'Performance and reliability',
    excellentBar: 'Performance optimization and reliability clearly addressed',
    score: 4,
    verdict: 'Reliability is engineered into the design; it is not yet backed by measurement.',
    howMet:
      'The reliability posture is deliberate: zone-redundant Container Apps behind VNet integration, an idempotency boundary so a retried command cannot double-apply, a verifiable hash-chained audit log, telemetry that fails open rather than taking the request down with it, and adapters that degrade to a deterministic offline twin instead of erroring. Cost-driven availability is handled explicitly \u2014 a Logic App parks the Fabric capacity nightly and the portal can resume it on demand.',
    evidence: [
      {
        kind: 'infra',
        label: 'infra/bicep/modules/containerapps.bicep',
        detail: 'Zone redundancy and per-service scale rules.',
      },
      {
        kind: 'infra',
        label: 'infra/bicep/modules/logicapp-capacity-lifecycle.bicep',
        detail: 'Nightly capacity pause with an on-demand resume path.',
      },
      {
        kind: 'code',
        label: 'services/bff-api/.../idempotency.py',
        detail: 'Replayed commands return the original result instead of re-executing.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../audit.py',
        detail: 'AuditLog.verify() detects any break in the hash chain.',
      },
      { kind: 'doc', label: 'docs/architecture/deployment-topology.md', detail: 'DR posture and RTO/RPO intent.' },
      { kind: 'ui', label: 'Platform Ops \u2192 Fabric Capacity', route: 'platform-ops/capacity' },
    ],
    gap: 'No load-test results, no published SLO/SLA targets, and no circuit-breaker middleware in code. The reliability claims rest on infrastructure configuration and design intent rather than on measured behaviour under load.',
    uplift:
      'Publish an SLO sheet with latency and availability targets, run a k6 or Azure Load Testing profile against the BFF and commit the results, and add a circuit breaker in front of the Foundry and Speech calls.',
    primaryRoute: 'platform-ops/capacity',
  },

  // --------------------------------------------------------------- presentation
  {
    id: 'TR-PRE-01',
    category: 'presentation',
    criterion: 'Clarity of explanation and presentation',
    excellentBar:
      'Clear, concise, and thorough presentation. Demonstrates ability to adapt to target audience level',
    score: 5,
    verdict: 'Three audience registers \u2014 executive, technical and novice \u2014 each served deliberately.',
    howMet:
      'The same content is prepared for three audiences. Executives get a 26-slide deck and a French executive summary that lead with cost and compliance. A technical jury gets the architecture, threat model, API contracts and this rating-grid analysis, plus 45-plus pages of anticipated FAQ. Someone who knows nothing about steelmaking gets the in-app Help Assistant, which explains any element on screen in plain language, optionally in English and French side by side. Every screen is stamped with the use-case reference it answers, so the thread from brief to pixel is never lost.',
    evidence: [
      { kind: 'doc', label: 'docs/presentation/oral-defense-and-slide-plan.md', detail: '26 slides with timing.' },
      { kind: 'doc', label: 'docs/presentation/faq.md', detail: 'Anticipated jury questions with prepared answers.' },
      { kind: 'doc', label: 'docs/presentation/resume-executif-fr.md', detail: 'French executive summary.' },
      { kind: 'doc', label: 'docs/tech/technical-analysis.md', detail: 'This rating-grid analysis, in long form.' },
      { kind: 'doc', label: 'docs/architecture/solution-architecture.md', detail: 'Authoritative architecture.' },
      { kind: 'doc', label: 'docs/README.md', detail: 'The reading path through the documentation set.' },
      { kind: 'ui', label: 'Proof of Execution \u2192 Use Case', route: 'proof-of-execution/use-case' },
    ],
    primaryRoute: 'proof-of-execution/use-case',
  },
]

export const TECH_BY_ID: Record<string, TechRequirement> = Object.fromEntries(
  TECH_REQUIREMENTS.map((requirement) => [requirement.id, requirement]),
)

export interface TechScorecard {
  total: number
  max: number
  pct: number
  grade: string
  gradeLabel: string
  perfect: number
  criteria: number
  byCategory: Array<{ category: TechCategory; score: number; max: number }>
}

export function gradeFor(total: number): { grade: string; gradeLabel: string } {
  const band = TECH_GRADE_BANDS.find((entry) => total >= entry.min && total <= entry.max)
  return { grade: band?.grade ?? 'D/F', gradeLabel: band?.label ?? '' }
}

export function techScorecard(): TechScorecard {
  const total = TECH_REQUIREMENTS.reduce((sum, requirement) => sum + requirement.score, 0)
  const max = TECH_REQUIREMENTS.length * 5
  const { grade, gradeLabel } = gradeFor(total)
  const byCategory = TECH_CATEGORY_ORDER.map((category) => {
    const rows = TECH_REQUIREMENTS.filter((requirement) => requirement.category === category)
    return {
      category,
      score: rows.reduce((sum, requirement) => sum + requirement.score, 0),
      max: rows.length * 5,
    }
  })
  return {
    total,
    max,
    pct: (total / max) * 100,
    grade,
    gradeLabel,
    perfect: TECH_REQUIREMENTS.filter((requirement) => requirement.score === 5).length,
    criteria: TECH_REQUIREMENTS.length,
    byCategory,
  }
}
