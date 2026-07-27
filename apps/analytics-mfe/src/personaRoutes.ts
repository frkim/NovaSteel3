export interface PersonaTab {
  slug: string
  label: string
}

export interface PersonaSection {
  section: string
  title: string
  persona: string
  personaIds: string[]
  description: string
  defaultSubView: string
  tabs: PersonaTab[]
}

export const personaSections: PersonaSection[] = [
  {
    section: 'command-center',
    title: 'Command Center',
    persona: 'Marc Weber - Plant Manager',
    personaIds: ['plant-manager'],
    description: 'Cross-persona triage with the highest-severity signals and next-best actions.',
    defaultSubView: 'overview',
    tabs: [{ slug: 'overview', label: 'Overview' }],
  },
  {
    section: 'operations',
    title: 'Operations',
    persona: 'Marc Weber - Plant Manager',
    personaIds: ['plant-manager'],
    description: 'Live production health, throughput versus target, and incident triage.',
    defaultSubView: 'overview',
    tabs: [{ slug: 'overview', label: 'Overview' }],
  },
  {
    section: 'furnace-health',
    title: 'Furnace Health',
    persona: 'Elena Duarte & Tomás Rossi - Furnace / Maintenance',
    personaIds: ['furnace-operator', 'maintenance-engineer'],
    description: 'Lining wear forecasting, thermal signatures, and maintenance planning.',
    defaultSubView: 'lining-forecast',
    tabs: [
      { slug: 'lining-forecast', label: 'Lining Forecast' },
      { slug: 'thermal-explorer', label: 'Thermal Explorer' },
      { slug: 'maintenance-planner', label: 'Maintenance Planner' },
    ],
  },
  {
    section: 'energy-optimization',
    title: 'Energy Optimization',
    persona: 'Sofia Lindqvist - Energy Manager',
    personaIds: ['energy-manager'],
    description: 'Constrained dispatch proposals against spot prices and carbon intensity.',
    defaultSubView: 'spot-price-schedule',
    tabs: [
      { slug: 'spot-price-schedule', label: 'Spot & Schedule' },
      { slug: 'load-shift-simulator', label: 'Load-Shift Simulator' },
    ],
  },
  {
    section: 'quality',
    title: 'Quality',
    persona: 'Jens Bakker - Quality Engineer',
    personaIds: ['quality-engineer'],
    description: 'Batch quality, genealogy, bounded what-if, and SPC.',
    defaultSubView: 'batches',
    tabs: [
      { slug: 'batches', label: 'Batch Quality' },
      { slug: 'spc', label: 'Defect Analytics (SPC)' },
    ],
  },
  {
    section: 'sustainability-compliance',
    title: 'Sustainability & Compliance',
    persona: 'Amina Haddad - Sustainability Officer',
    personaIds: ['sustainability-officer'],
    description: 'Emissions ledger, ETS exposure, and auditable decision evidence.',
    defaultSubView: 'emissions-ledger',
    tabs: [
      { slug: 'emissions-ledger', label: 'Emissions Ledger' },
      { slug: 'ets-exposure', label: 'ETS Exposure' },
      { slug: 'audit', label: 'Audit & Reports' },
    ],
  },
  {
    section: 'knowledge-hub',
    title: 'Knowledge Hub',
    persona: 'Pieter Claes - Knowledge Engineer',
    personaIds: ['knowledge-engineer'],
    description: 'Search approved procedures and govern consent-bound capture and review.',
    defaultSubView: 'procedures',
    tabs: [
      { slug: 'procedures', label: 'Procedures' },
      { slug: 'capture-status', label: 'Capture Status' },
    ],
  },
  {
    section: 'executive-overview',
    title: 'Executive Overview',
    persona: 'Isabelle Moreau - Executive',
    personaIds: ['executive'],
    description: 'Cross-site KPIs, targets versus actuals, and an optional board report.',
    defaultSubView: 'overview',
    tabs: [
      { slug: 'overview', label: 'Overview' },
      { slug: 'board-report', label: 'Board Report' },
    ],
  },
  {
    section: 'device-operations',
    title: 'Device Operations',
    persona: 'Rui Almeida - OT Systems Engineer',
    personaIds: ['ot-systems-engineer'],
    description:
      'Fleet health for every simulated device, a searchable sensor explorer, and the incident simulator that drives the demo.',
    defaultSubView: 'fleet',
    tabs: [
      { slug: 'fleet', label: 'Device Fleet' },
      { slug: 'sensors', label: 'Sensor Explorer' },
      { slug: 'simulator', label: 'Simulator Control' },
    ],
  },
  {
    section: 'dashboards',
    title: 'Dashboard Collections',
    persona: 'All personas',
    personaIds: [
      'plant-manager', 'furnace-operator', 'maintenance-engineer', 'energy-manager',
      'quality-engineer', 'sustainability-officer', 'knowledge-engineer', 'executive',
      'ot-systems-engineer', 'platform-ops',
    ],
    description: 'Curated, ready-to-open dashboard sets grouped by the question each one answers.',
    defaultSubView: 'collections',
    tabs: [{ slug: 'collections', label: 'Collections' }],
  },
  {
    section: 'platform-ops',
    title: 'Platform Ops',
    persona: 'Nils Andersen - Platform Ops',
    personaIds: ['platform-ops'],
    description: 'Restricted non-production capacity lifecycle, jobs, and cost telemetry.',
    defaultSubView: 'capacity',
    tabs: [
      { slug: 'capacity', label: 'Fabric Capacity' },
      { slug: 'jobs', label: 'Jobs & Pipelines' },
      { slug: 'cost-telemetry', label: 'Cost & Telemetry' },
    ],
  },
  {
    section: 'company-website',
    title: 'AxelorMetal',
    persona: 'Public site',
    personaIds: [],
    description:
      'The public corporate site of AxelorMetal, the Luxembourg steel producer that runs the NovaSteel platform.',
    defaultSubView: 'home',
    tabs: [
      { slug: 'home', label: 'Home' },
      { slug: 'company', label: 'Company' },
      { slug: 'products', label: 'Products & Markets' },
      { slug: 'steel-knowledge', label: 'Steel Knowledge' },
      { slug: 'contact', label: 'Contact' },
    ],
  },
]

export function resolveSection(
  section: string,
  subView: string | null,
): { section: PersonaSection; tab: PersonaTab } {
  const resolved = personaSections.find((candidate) => candidate.section === section) ?? personaSections[0]
  const tab =
    resolved.tabs.find((candidate) => candidate.slug === subView) ??
    resolved.tabs.find((candidate) => candidate.slug === resolved.defaultSubView) ??
    resolved.tabs[0]
  return { section: resolved, tab }
}
