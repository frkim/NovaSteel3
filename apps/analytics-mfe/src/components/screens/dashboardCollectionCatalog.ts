/**
 * Curated dashboard collections (UX §9.8).
 *
 * A collection answers one question with an ordered set of existing screens, so
 * a persona can open a whole investigation path instead of hunting through the
 * navigation. Routes are relative to the active site and resolved by the shell.
 */

export interface DashboardCard {
  id: string
  title: string
  description: string
  section: string
  subView: string
  /** What the viewer should conclude from this panel. */
  takeaway: string
}

export interface DashboardCollection {
  id: string
  title: string
  question: string
  persona: string
  /** Why this ordering answers the question. */
  narrative: string
  estimatedMinutes: number
  tags: string[]
  cards: DashboardCard[]
}

export const dashboardCollections: DashboardCollection[] = [
  {
    id: 'morning-shift-handover',
    title: 'Morning shift handover',
    question: 'What changed overnight and what must this shift act on first?',
    persona: 'Plant Manager',
    narrative:
      'Start from cross-plant triage, confirm the production picture, then close on the two assets most likely to constrain the shift.',
    estimatedMinutes: 6,
    tags: ['daily', 'triage'],
    cards: [
      {
        id: 'handover-command',
        title: 'Command Center',
        description: 'Highest-severity signals and next-best actions across every persona.',
        section: 'command-center',
        subView: 'overview',
        takeaway: 'The ranked action list is the agenda for the handover meeting.',
      },
      {
        id: 'handover-operations',
        title: 'Operations',
        description: 'Throughput against target with live incident triage.',
        section: 'operations',
        subView: 'overview',
        takeaway: 'Confirms whether the overnight plan actually landed.',
      },
      {
        id: 'handover-fleet',
        title: 'Device Fleet',
        description: 'Health score and active incidents for all six simulated assets.',
        section: 'device-operations',
        subView: 'fleet',
        takeaway: 'Any device out of "healthy" needs an owner before the shift starts.',
      },
      {
        id: 'handover-lining',
        title: 'Lining Forecast',
        description: 'Remaining useful life with its P10/P50/P90 band.',
        section: 'furnace-health',
        subView: 'lining-forecast',
        takeaway: 'The single longest-lead constraint on the production plan.',
      },
    ],
  },
  {
    id: 'furnace-risk-investigation',
    title: 'Furnace risk investigation',
    question: 'Is the lining risk real, and what is driving it?',
    persona: 'Maintenance / Reliability Engineer',
    narrative:
      'Move from the model output, to the raw thermal evidence behind it, to the individual sensors, and finish on the maintenance decision.',
    estimatedMinutes: 8,
    tags: ['reliability', 'root-cause'],
    cards: [
      {
        id: 'risk-lining',
        title: 'Lining Forecast',
        description: 'Physics-informed RUL with drivers and confidence band.',
        section: 'furnace-health',
        subView: 'lining-forecast',
        takeaway: 'Establishes the claim: how many days of warning the model gives.',
      },
      {
        id: 'risk-thermal',
        title: 'Thermal Explorer',
        description: 'Heat-flux and shell-temperature signatures over the wear window.',
        section: 'furnace-health',
        subView: 'thermal-explorer',
        takeaway: 'Shows the physical signature the model is reading.',
      },
      {
        id: 'risk-sensors',
        title: 'Sensor Explorer',
        description: 'The individual signals, with a linked chart per sensor.',
        section: 'device-operations',
        subView: 'sensors',
        takeaway: 'Proves the signature is in the raw data, not an artefact of the model.',
      },
      {
        id: 'risk-maintenance',
        title: 'Maintenance Planner',
        description: 'Candidate intervention windows and their production cost.',
        section: 'furnace-health',
        subView: 'maintenance-planner',
        takeaway: 'Turns the risk into a dated, costed decision.',
      },
    ],
  },
  {
    id: 'energy-cost-review',
    title: 'Energy and cost review',
    question: 'Where is the next megawatt-hour of saving, and what does it cost in CO₂?',
    persona: 'Energy Manager',
    narrative:
      'Price signal first, then the optimiser proposal, then the emissions and ETS consequence of accepting it.',
    estimatedMinutes: 7,
    tags: ['energy', 'cost'],
    cards: [
      {
        id: 'energy-spot',
        title: 'Spot & Schedule',
        description: 'Day-ahead price curve against the planned load.',
        section: 'energy-optimization',
        subView: 'spot-price-schedule',
        takeaway: 'Identifies the scarcity hours worth shifting away from.',
      },
      {
        id: 'energy-simulator',
        title: 'Load-Shift Simulator',
        description: 'Constrained MILP dispatch under operator-set bounds.',
        section: 'energy-optimization',
        subView: 'load-shift-simulator',
        takeaway: 'Quantifies the achievable saving without breaking process constraints.',
      },
      {
        id: 'energy-emissions',
        title: 'Emissions Ledger',
        description: 'Scope 1/2 ledger with the grid carbon intensity applied.',
        section: 'sustainability-compliance',
        subView: 'emissions-ledger',
        takeaway: 'Converts the megawatt-hours into reportable CO₂e.',
      },
      {
        id: 'energy-ets',
        title: 'ETS Exposure',
        description: 'Allowance position and price sensitivity.',
        section: 'sustainability-compliance',
        subView: 'ets-exposure',
        takeaway: 'Puts a euro figure on the emissions delta.',
      },
    ],
  },
  {
    id: 'quality-escape-review',
    title: 'Quality escape review',
    question: 'Which batches are at risk and what is the common cause?',
    persona: 'Quality Engineer',
    narrative:
      'Batch-level risk, then statistical process control to separate signal from noise, then the process sensors that explain it.',
    estimatedMinutes: 6,
    tags: ['quality', 'root-cause'],
    cards: [
      {
        id: 'quality-batches',
        title: 'Batch Quality',
        description: 'Predicted first-pass yield per batch with genealogy.',
        section: 'quality',
        subView: 'batches',
        takeaway: 'Narrows the population to the batches actually at risk.',
      },
      {
        id: 'quality-spc',
        title: 'Defect Analytics (SPC)',
        description: 'Control charts and Pareto of defect modes.',
        section: 'quality',
        subView: 'spc',
        takeaway: 'Distinguishes a real special cause from normal variation.',
      },
      {
        id: 'quality-sensors',
        title: 'Sensor Explorer',
        description: 'Caster and mill signals over the affected window.',
        section: 'device-operations',
        subView: 'sensors',
        takeaway: 'Links the defect mode to a measurable process excursion.',
      },
    ],
  },
  {
    id: 'compliance-evidence-pack',
    title: 'Compliance evidence pack',
    question: 'Can we prove how every automated recommendation was decided?',
    persona: 'Sustainability Officer / Auditor',
    narrative:
      'The audit trail first, then the emissions figures it underwrites, then the knowledge base that grounds the AI answers.',
    estimatedMinutes: 7,
    tags: ['compliance', 'audit', 'eu-ai-act'],
    cards: [
      {
        id: 'compliance-audit',
        title: 'Audit & Reports',
        description: 'Hash-chained decision log with approver and correlation id.',
        section: 'sustainability-compliance',
        subView: 'audit',
        takeaway: 'Every AI proposal has a human approval record that verifies.',
      },
      {
        id: 'compliance-emissions',
        title: 'Emissions Ledger',
        description: 'The reported figures and their derivation.',
        section: 'sustainability-compliance',
        subView: 'emissions-ledger',
        takeaway: 'The numbers an auditor will ask you to reproduce.',
      },
      {
        id: 'compliance-knowledge',
        title: 'Procedures',
        description: 'Approved procedures that ground every retrieval answer.',
        section: 'knowledge-hub',
        subView: 'procedures',
        takeaway: 'Drafts are never retrievable; only approved procedures can be cited.',
      },
    ],
  },
  {
    id: 'platform-health-review',
    title: 'Platform health and spend',
    question: 'Is the platform healthy, and what is it costing us?',
    persona: 'Platform Ops',
    narrative:
      'Capacity state first because everything downstream depends on it, then pipeline health, then the cost telemetry.',
    estimatedMinutes: 5,
    tags: ['platform', 'cost'],
    cards: [
      {
        id: 'platform-capacity',
        title: 'Fabric Capacity',
        description: 'Capacity SKU, run state, and the lifecycle controls.',
        section: 'platform-ops',
        subView: 'capacity',
        takeaway: 'A paused capacity explains most downstream staleness.',
      },
      {
        id: 'platform-jobs',
        title: 'Jobs & Pipelines',
        description: 'Medallion pipeline runs and data-quality gate outcomes.',
        section: 'platform-ops',
        subView: 'jobs',
        takeaway: 'Confirms bronze→silver→gold actually completed.',
      },
      {
        id: 'platform-simulator',
        title: 'Simulator Control',
        description: 'Device simulator state and injected incidents.',
        section: 'device-operations',
        subView: 'simulator',
        takeaway: 'Tells you whether an anomaly is real or deliberately injected.',
      },
      {
        id: 'platform-cost',
        title: 'Cost & Telemetry',
        description: 'Per-service cost and the emitted custom metrics.',
        section: 'platform-ops',
        subView: 'cost-telemetry',
        takeaway: 'Ties the run-rate back to the capacity and container footprint.',
      },
    ],
  },
]

export function collectionById(id: string): DashboardCollection | undefined {
  return dashboardCollections.find((collection) => collection.id === id)
}

export const dashboardCollectionTags = Array.from(
  new Set(dashboardCollections.flatMap((collection) => collection.tags)),
).sort()
