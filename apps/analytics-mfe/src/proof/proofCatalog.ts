/**
 * Use-case requirement catalog — the single source of truth for the
 * "Proof of execution" screen and for the reference-ID badges stamped on the
 * screens that satisfy each requirement.
 *
 * Every entry is a verbatim requirement extracted from `docs/usecase/usecase.md`
 * and given a stable reference ID. The `evidence` array points at real files,
 * routes and screens; `caveat` records — honestly — where the demo falls short
 * of the production claim. A jury that greps the repository must find exactly
 * what this catalog says it will find.
 *
 * Keep this file in sync with `docs/presentation/proof_of_execution.md`.
 */

export type ProofCategory = 'regulatory' | 'challenge' | 'objective' | 'outcome' | 'ai'

/** How completely the running solution satisfies the requirement. */
export type ProofStatus = 'met' | 'partial' | 'demo'

export type EvidenceKind = 'ui' | 'api' | 'code' | 'infra' | 'doc' | 'test'

export interface ProofEvidence {
  kind: EvidenceKind
  /** Human label, e.g. a file path with line range or an HTTP route. */
  label: string
  /** Optional one-line explanation of what the reader will see there. */
  detail?: string
  /** Optional in-app deep link, `section/subView`, used by the "open" action. */
  route?: string
}

export interface ProofRequirement {
  id: string
  category: ProofCategory
  /** Verbatim (or near-verbatim) requirement text from the use-case brief. */
  statement: string
  /** The measurable target where the brief states one. */
  target?: string
  status: ProofStatus
  /** How NovaSteel satisfies the requirement, in plain language. */
  howMet: string
  evidence: ProofEvidence[]
  /** What a technical jury should know is *not* fully real in the demo. */
  caveat?: string
  /** Primary screen that demonstrates this requirement, `section/subView`. */
  primaryRoute?: string
}

export const PROOF_CATEGORY_ORDER: ProofCategory[] = [
  'regulatory',
  'challenge',
  'objective',
  'outcome',
  'ai',
]

export const PROOF_REQUIREMENTS: ProofRequirement[] = [
  // ---------------------------------------------------------------- regulatory
  {
    id: 'REG-01',
    category: 'regulatory',
    statement: 'GDPR - personal data captured from operators must be lawful, minimised and erasable.',
    status: 'met',
    howMet:
      'Interviews cannot start without a recorded, scoped consent grant. Transcripts are PII-scanned and redacted before any model sees them. A right-to-erasure request hard-deletes the source transcript, pseudonymises the derived procedure attribution and appends a tombstone to the audit chain rather than rewriting it.',
    evidence: [
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../erasure.py',
        detail: 'ErasureService: crypto-shredding, pseudonymisation, tombstone append, chain re-verification.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../pii.py',
        detail: 'Detects email, phone, IBAN (mod-97 checked), person names, EMP-##### IDs, IPv4, DOB.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../consent.py',
        detail: 'ConsentRecord state machine; is_capture_allowed() enforces scope and expiry.',
      },
      {
        kind: 'api',
        label: 'POST /v1/privacy/erasure-requests and .../{id}:execute',
        detail: 'Requires the Compliance.Auditor role.',
      },
      {
        kind: 'ui',
        label: 'Sustainability & Compliance > Audit & Reports',
        route: 'sustainability-compliance/audit',
      },
    ],
    caveat:
      'Scheduled deletion once retentionDays expires is an operations runbook, not a running job in this repository.',
    primaryRoute: 'sustainability-compliance/audit',
  },
  {
    id: 'REG-02',
    category: 'regulatory',
    statement: 'EU AI Act - AI that influences industrial operations needs human oversight and transparency.',
    status: 'met',
    howMet:
      'No agent can act on the plant. Every consequential transition is a gated node in an explicit state graph that a human must clear, and the agents are physically unable to approve their own work: approve, publish, commit, schedule and delete are on a forbidden-tool list the registry refuses to dispatch. Prompt-injection spotlighting and content-safety screening run on every input and output.',
    evidence: [
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../state_graph.py',
        detail: 'IN_REVIEW is a gated node; to_mermaid() renders the graph for the deck.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../tools.py',
        detail: 'AGENT_TOOL_ALLOWLIST per agent identity plus FORBIDDEN_TOOL_NAMES (human-only actions).',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../prompt_defense.py',
        detail: 'SAFETY_META_PROMPT, scan_for_injection(), spotlight(), build_grounded_prompt().',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../content_safety.py',
        detail: 'Six-category severity scoring; blocks at severity 4 or above on both input and output.',
      },
      {
        kind: 'infra',
        label: 'infra/bicep/modules/alerts.bicep',
        detail: 'Sev-1 alert if an energy dispatch executes with no matching human approval event.',
      },
      {
        kind: 'ui',
        label: 'Energy Optimization > Spot & Schedule (approval gate)',
        route: 'energy-optimization/spot-price-schedule',
      },
    ],
    caveat:
      'Annex III risk classification and a formal model card exist as documentation; there is no structured RiskClassification object in code.',
    primaryRoute: 'sustainability-compliance/audit',
  },
  {
    id: 'REG-03',
    category: 'regulatory',
    statement: 'Sector-specific EU directives - EU ETS emissions accounting and reporting obligations.',
    status: 'partial',
    howMet:
      'The Fabric gold layer computes Scope 1 and Scope 2 tonnes, subtracts the free allocation benchmark and prices the residual exposure in euro. The ETS Exposure screen shows allowance consumption against the period cap, and the emissions ledger is append-only.',
    evidence: [
      {
        kind: 'code',
        label: 'fabric/notebooks/ns-silver-to-gold.Notebook',
        detail: 'scope1_co2e_t, scope2_co2e_t, free_allocation_t, ets_exposure_eur.',
      },
      {
        kind: 'ui',
        label: 'Sustainability & Compliance > ETS Exposure',
        route: 'sustainability-compliance/ets-exposure',
      },
      { kind: 'api', label: 'GET /v1/sustainability/summary and GET /v1/sustainability/emissions' },
    ],
    caveat:
      'The allowance benchmark (1.50 t per tonne of steel) and the allowance price are demo constants. CBAM and the Industrial Emissions Directive are described in the documentation but not implemented in code.',
    primaryRoute: 'sustainability-compliance/ets-exposure',
  },

  // ---------------------------------------------------------------- challenges
  {
    id: 'CHL-01',
    category: 'challenge',
    statement: 'Energy costs are 35% of total production cost with no real-time optimization.',
    status: 'met',
    howMet:
      'Energy-intensive batches are re-placed against the half-hourly spot price and carbon-intensity curve by a mixed-integer program, so the plant gets a concrete, costed schedule instead of a static plan.',
    evidence: [
      {
        kind: 'code',
        label: 'services/optimizer-worker/.../milp.py',
        detail: 'PuLP/CBC LpProblem, binary placement variables, assignment and capacity constraints.',
      },
      { kind: 'api', label: 'POST /v1/energy/schedules:simulate' },
      {
        kind: 'ui',
        label: 'Energy Optimization > Load-Shift Simulator',
        route: 'energy-optimization/load-shift-simulator',
      },
    ],
    caveat: 'The demo runs on fixture spot prices, not a live ENTSO-E feed.',
    primaryRoute: 'energy-optimization/spot-price-schedule',
  },
  {
    id: 'CHL-02',
    category: 'challenge',
    statement: 'CO2 emissions are under increasing pressure from EU ETS penalties.',
    status: 'met',
    howMet:
      'Carbon intensity is a first-class term in the dispatch objective, not an afterthought: the solver trades euro against kilograms with an explicit weight. Emissions land in an immutable ledger and drive the ETS exposure figure.',
    evidence: [
      {
        kind: 'code',
        label: 'services/optimizer-worker/.../milp.py',
        detail: 'Objective = co2_weight x MWh x carbon + cost_weight x MWh x price.',
      },
      {
        kind: 'ui',
        label: 'Sustainability & Compliance > Emissions Ledger',
        route: 'sustainability-compliance/emissions-ledger',
      },
      { kind: 'infra', label: 'Custom metric novasteel.emissions.co2_kg' },
    ],
    primaryRoute: 'sustainability-compliance/emissions-ledger',
  },
  {
    id: 'CHL-03',
    category: 'challenge',
    statement:
      'Furnace lining wear is impossible to predict, causing catastrophic failures costing 8 million euro per event.',
    status: 'met',
    howMet:
      'Refractory thickness and heat flux are regressed over a rolling window; the fit is extrapolated to the minimum-safe thickness to give a remaining-useful-life estimate with P10/P50/P90 bands and a stated confidence, so maintenance is planned rather than reactive.',
    evidence: [
      {
        kind: 'code',
        label: 'services/scoring-worker/.../physics_features.py',
        detail: 'OLS on hearth_refractory_estimate and local_heat_flux.',
      },
      {
        kind: 'code',
        label: 'services/scoring-worker/.../rul_model.py',
        detail: 'TTF extrapolation with slope-standard-error uncertainty propagation.',
      },
      { kind: 'api', label: 'GET /v1/furnaces/{assetId}/lining-forecast' },
      { kind: 'ui', label: 'Furnace Health > Lining Forecast', route: 'furnace-health/lining-forecast' },
    ],
    primaryRoute: 'furnace-health/lining-forecast',
  },
  {
    id: 'CHL-04',
    category: 'challenge',
    statement: 'Quality consistency issues in high-grade steel for automotive customers.',
    status: 'met',
    howMet:
      'Every batch is scored for first-pass yield risk from its process bias, plotted on SPC charts, and exposed to a bounded what-if so an engineer can test a corrective set-point before committing it.',
    evidence: [
      {
        kind: 'code',
        label: 'services/scoring-worker/.../service.py',
        detail: 'score_quality() and quality_what_if().',
      },
      { kind: 'api', label: 'GET /v1/quality/batches and POST /v1/quality/what-if' },
      { kind: 'ui', label: 'Quality > Batch Quality and Defect Analytics (SPC)', route: 'quality/batches' },
    ],
    caveat:
      'The yield model is a calibrated surrogate over the coiling-temperature bias, not a trained metallurgical model.',
    primaryRoute: 'quality/batches',
  },
  {
    id: 'CHL-05',
    category: 'challenge',
    statement: 'Skilled operators are retiring and knowledge disappears faster than it can be captured.',
    status: 'met',
    howMet:
      'A consent-bound interview is transcribed, mined for procedure steps, criticised by a second agent, and only then offered to a human publisher. Approved procedures become searchable, cited source material for everyone else.',
    evidence: [
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../procedure_workflow.py',
        detail: 'DRAFT to IN_REVIEW to APPROVED with role and optimistic-concurrency checks.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../retrieval.py',
        detail: 'Lexical and cosine hybrid retrieval over approved procedures only.',
      },
      { kind: 'api', label: 'POST /v1/knowledge/interviews and GET /v1/knowledge/search' },
      { kind: 'ui', label: 'Knowledge Hub > Procedures and Capture Status', route: 'knowledge-hub/procedures' },
    ],
    primaryRoute: 'knowledge-hub/procedures',
  },

  // ---------------------------------------------------------------- objectives
  {
    id: 'OBJ-01',
    category: 'objective',
    statement: 'Reduce energy consumption.',
    status: 'met',
    howMet:
      'The dispatch optimiser produces a re-timed schedule whose energy per tonne is computed from the solved plan and emitted as a telemetry metric, then surfaced against the target on the Command Center.',
    evidence: [
      {
        kind: 'code',
        label: 'services/optimizer-worker/.../metrics.py',
        detail: 'novasteel.energy.kwh_per_tonne derived from the solved schedule.',
      },
      { kind: 'ui', label: 'Command Center > Overview', route: 'command-center/overview' },
      {
        kind: 'ui',
        label: 'Energy Optimization > Spot & Schedule',
        route: 'energy-optimization/spot-price-schedule',
      },
    ],
    primaryRoute: 'energy-optimization/spot-price-schedule',
  },
  {
    id: 'OBJ-02',
    category: 'objective',
    statement: 'Predict equipment failures.',
    status: 'met',
    howMet:
      'Lining remaining-useful-life is scored continuously; a Real-Time Intelligence activator rule fires when risk crosses 0.80 and P50 life falls to 21 days or less, and the maintenance planner turns that into scheduled work.',
    evidence: [
      { kind: 'code', label: 'services/scoring-worker/.../rul_model.py' },
      { kind: 'infra', label: 'fabric/rti/activator-rules.template.json', detail: 'ACT-FUR-001 lining risk rule.' },
      { kind: 'ui', label: 'Furnace Health > Maintenance Planner', route: 'furnace-health/maintenance-planner' },
    ],
    primaryRoute: 'furnace-health/lining-forecast',
  },
  {
    id: 'OBJ-03',
    category: 'objective',
    statement: 'Improve steel quality.',
    status: 'met',
    howMet:
      'Predicted first-pass yield, defect Pareto and SPC control limits are computed per grade and per batch and fed back to the caster set-points through the bounded what-if.',
    evidence: [
      {
        kind: 'code',
        label: 'services/scoring-worker/.../metrics.py',
        detail: 'novasteel.quality.high_grade_yield_pct.',
      },
      {
        kind: 'code',
        label: 'fabric/notebooks/ns-silver-to-gold.Notebook',
        detail: 'fact_quality_yield aggregated by grade and date.',
      },
      { kind: 'ui', label: 'Quality > Defect Analytics (SPC)', route: 'quality/spc' },
    ],
    primaryRoute: 'quality/batches',
  },
  {
    id: 'OBJ-04',
    category: 'objective',
    statement: 'Capture and structure operational expertise before it is lost.',
    status: 'met',
    howMet:
      'The knowledge pipeline turns a spoken interview into a structured, cited, reviewed and versioned procedure. Nothing reaches the library without a named human publisher and a full audit trail.',
    evidence: [
      { kind: 'code', label: 'services/knowledge-orchestrator/.../orchestrator.py' },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../grounding.py',
        detail: 'Rejects drafts containing un-sourced transcript segments.',
      },
      { kind: 'ui', label: 'Knowledge Hub > Capture Status', route: 'knowledge-hub/capture-status' },
    ],
    primaryRoute: 'knowledge-hub/capture-status',
  },

  // ------------------------------------------------------------------ outcomes
  {
    id: 'OUT-01',
    category: 'outcome',
    statement: 'Energy consumption per ton reduced by 14%.',
    target: '-14% kWh/t',
    status: 'demo',
    howMet:
      'Energy per tonne is computed from the solved dispatch schedule and compared to the gold-layer baseline. The Command Center shows the target alongside the live modelled saving, which is deliberately smaller.',
    evidence: [
      {
        kind: 'code',
        label: 'services/optimizer-worker/.../metrics.py',
        detail: 'kwh_per_tonne = total_mwh x 1000 / total_tonnage.',
      },
      {
        kind: 'code',
        label: 'fabric/notebooks/ns-silver-to-gold.Notebook',
        detail: 'baseline_energy_gj = energy_gj / 0.86 in the demo environment.',
      },
      { kind: 'ui', label: 'Command Center > Overview', route: 'command-center/overview' },
    ],
    caveat:
      'The -14% figure is the synthetic-data baseline ratio, presented in the UI as a target. The live modelled saving on the demo dataset is materially smaller and is shown as such.',
    primaryRoute: 'command-center/overview',
  },
  {
    id: 'OUT-02',
    category: 'outcome',
    statement: 'CO2 emissions reduced by 22%.',
    target: '-22% CO2',
    status: 'demo',
    howMet:
      'Scope 2 emissions are recomputed from the optimised schedule against the carbon-intensity curve and tracked in the emissions ledger and as a custom metric.',
    evidence: [
      {
        kind: 'code',
        label: 'fabric/notebooks/ns-silver-to-gold.Notebook',
        detail: 'baseline_co2e_t = total_co2e_t / 0.78 in the demo environment.',
      },
      { kind: 'code', label: 'services/optimizer-worker/.../metrics.py', detail: 'novasteel.emissions.co2_kg.' },
      {
        kind: 'ui',
        label: 'Sustainability & Compliance > Emissions Ledger',
        route: 'sustainability-compliance/emissions-ledger',
      },
    ],
    caveat:
      'Load-shifting alone yields a single-digit CO2 reduction on the demo dataset. The -22% ambition assumes the accompanying grid-mix and scrap-ratio measures described in the business case; the UI labels it a target, never a measurement.',
    primaryRoute: 'sustainability-compliance/emissions-ledger',
  },
  {
    id: 'OUT-03',
    category: 'outcome',
    statement: 'Furnace lining failure predicted with 21-day advance warning.',
    target: '21 days',
    status: 'met',
    howMet:
      'The regression extrapolates time-to-failure and the P10 lower bound is the actionable warning. The Real-Time Intelligence activator raises the alert as soon as P50 life drops to 21 days with risk at or above 0.80, which is exactly the demo scenario.',
    evidence: [
      {
        kind: 'code',
        label: 'services/scoring-worker/.../rul_model.py',
        detail: 'ttf_days = remaining_mm / wear_rate with P10/P90 from the slope standard error.',
      },
      {
        kind: 'infra',
        label: 'fabric/rti/activator-rules.template.json',
        detail: 'risk_score >= 0.80 and P50 <= 21 days for 5 minutes.',
      },
      {
        kind: 'infra',
        label: 'infra/bicep/modules/alerts.bicep',
        detail: 'Model-drift alert on novasteel.rul.confidence below 0.5.',
      },
      { kind: 'ui', label: 'Furnace Health > Lining Forecast', route: 'furnace-health/lining-forecast' },
    ],
    caveat:
      'The estimator is a least-squares regression over physical signals with propagated uncertainty, not a thermodynamic wear model. The residual-learning hook is an interface, not a trained model.',
    primaryRoute: 'furnace-health/lining-forecast',
  },
  {
    id: 'OUT-04',
    category: 'outcome',
    statement: 'High-grade steel yield improved by 8%.',
    target: '+8 pts first-pass yield',
    status: 'demo',
    howMet:
      'Predicted first-pass yield per batch is scored from process bias and aggregated by grade in the gold layer; the Command Center compares it to the pre-platform baseline in the scenario manifest.',
    evidence: [
      {
        kind: 'code',
        label: 'services/scoring-worker/.../service.py',
        detail: 'score_quality() derives base_yield from the coiling-temperature bias.',
      },
      {
        kind: 'code',
        label: 'fabric/notebooks/ns-silver-to-gold.Notebook',
        detail: 'fact_quality_yield = first_pass_good_tons / attempted_tons.',
      },
      { kind: 'ui', label: 'Quality > Batch Quality', route: 'quality/batches' },
    ],
    caveat:
      'The improvement is the delta between the manifest baseline and the scored prediction on synthetic data, presented as a target.',
    primaryRoute: 'quality/batches',
  },

  // ------------------------------------------------------------ AI infusion
  {
    id: 'AI-01',
    category: 'ai',
    statement: 'A physics-informed ML model predicts furnace lining degradation from thermal signatures.',
    status: 'met',
    howMet:
      'Thermal signatures - refractory thickness, local heat flux, cooling-water delta - are turned into physical features (apparent thermal resistance, heat proxy, normalised health index) and regressed. Failure time and its uncertainty come out of the fit, and every driver is explained on screen.',
    evidence: [
      {
        kind: 'code',
        label: 'services/scoring-worker/.../physics_features.py',
        detail: 'extract_thermal_features(); apparent thermal resistance R = dT / q.',
      },
      {
        kind: 'code',
        label: 'services/scoring-worker/.../rul_model.py',
        detail: 'confidence_score() weights fit quality, window length, slope and heat-flux corroboration.',
      },
      { kind: 'ui', label: 'Furnace Health > Thermal Explorer', route: 'furnace-health/thermal-explorer' },
    ],
    caveat:
      'Physics-informed here means physics-derived features in a regression with propagated uncertainty. There is no Arrhenius kinetics term, and the gradient-boosted residual learner is a declared interface with no trained artefact.',
    primaryRoute: 'furnace-health/thermal-explorer',
  },
  {
    id: 'AI-02',
    category: 'ai',
    statement:
      'An energy dispatch optimization agent schedules energy-intensive processes around electricity spot prices.',
    status: 'met',
    howMet:
      'A named agent identity with its own tool allow-list solves a mixed-integer placement problem over price and carbon, then proposes - never commits - a schedule. When a proposal would push a furnace past its remaining-useful-life limit, the agent hands off to the scoring agent, receives a constraint back, and re-plans.',
    evidence: [
      {
        kind: 'code',
        label: 'services/optimizer-worker/.../milp.py',
        detail: 'PuLP/CBC solver with a deterministic heuristic fallback.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../handoff.py',
        detail: 'execute_handoff(): dispatch to scoring, RULConstraint returned, dispatch replans; traced end to end.',
      },
      {
        kind: 'api',
        label: 'POST /v1/energy/recommendations/{id}:approve',
        detail: 'Human approval gate, EnergyPlanner.Approve role.',
      },
      {
        kind: 'ui',
        label: 'Energy Optimization > Load-Shift Simulator',
        route: 'energy-optimization/load-shift-simulator',
      },
    ],
    caveat:
      'The handoff counterparties are in-process deterministic scorers in the demo; the cross-service HTTP hop is not exercised.',
    primaryRoute: 'energy-optimization/load-shift-simulator',
  },
  {
    id: 'AI-03',
    category: 'ai',
    statement:
      'A GenAI knowledge-capture system interviews operators and structures expertise into searchable procedure libraries.',
    status: 'met',
    howMet:
      'Speech-to-text feeds a grounded extraction prompt; a critic agent then reviews the draft for uncited claims and unsafe steps and returns APPROVE or REVISE, re-running extraction at most twice. Retrieval is hybrid lexical plus cosine over approved procedures only, with citation enforcement and an explicit decline path when nothing grounds the answer.',
    evidence: [
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../critic.py',
        detail: 'run_reflection_loop(), capped at 2 iterations, every pass audited.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../retrieval.py',
        detail: 'Hybrid retrieval, citation enforcement, decline path.',
      },
      {
        kind: 'code',
        label: 'services/knowledge-orchestrator/.../evaluation.py',
        detail: 'Offline scorecard: injection resistance, grounding, citation, safe prompt.',
      },
      { kind: 'ui', label: 'Knowledge Hub > Procedures', route: 'knowledge-hub/procedures' },
    ],
    caveat:
      'In offline demo mode the extraction and critic adapters are local deterministic stand-ins; the Azure AI Foundry adapter is wired but requires a deployed model and the manual Agent Service validation gate.',
    primaryRoute: 'knowledge-hub/procedures',
  },
]

/** Lookup by reference ID, used by the in-situ badges. */
export const PROOF_BY_ID: Record<string, ProofRequirement> = Object.fromEntries(
  PROOF_REQUIREMENTS.map((requirement) => [requirement.id, requirement]),
)

export interface ProofCoverage {
  total: number
  met: number
  partial: number
  demo: number
  /** Percentage of requirements fully met (status === 'met'). */
  coveragePct: number
}

export function proofCoverage(requirements: ProofRequirement[] = PROOF_REQUIREMENTS): ProofCoverage {
  const met = requirements.filter((requirement) => requirement.status === 'met').length
  const partial = requirements.filter((requirement) => requirement.status === 'partial').length
  const demo = requirements.filter((requirement) => requirement.status === 'demo').length
  const total = requirements.length
  return {
    total,
    met,
    partial,
    demo,
    coveragePct: total === 0 ? 0 : Math.round((met / total) * 1000) / 10,
  }
}
