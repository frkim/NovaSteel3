/**
 * Persona registry for the NovaSteel platform.
 *
 * Single source of truth consumed by personaRoutes, the Copilot panel, and the
 * dashboard header. All names match the shared persona table byte-for-byte —
 * the Copilot chat agent relies on the same identifiers.
 */

export interface Persona {
  id: string
  shellKey: string
  name: string
  role: string
  initials: string
  description: string
  primaryQuestion: string
}

export const personas: Persona[] = [
  {
    id: 'plant-manager',
    shellKey: 'PlantManager',
    name: 'Marc Weber',
    role: 'Plant Manager',
    initials: 'MW',
    description: 'Owns shift output, safety, and the morning triage that sets priorities for every other role.',
    primaryQuestion: 'What changed overnight and what must this shift act on first?',
  },
  {
    id: 'furnace-operator',
    shellKey: 'FurnaceOperator',
    name: 'Elena Duarte',
    role: 'Furnace Operator',
    initials: 'ED',
    description: 'Watches the blast furnace thermal profile in real-time and adjusts burden distribution.',
    primaryQuestion: 'Is the furnace running within safe thermal limits right now?',
  },
  {
    id: 'maintenance-engineer',
    shellKey: 'MaintenanceEngineer',
    name: 'Tomás Rossi',
    role: 'Maintenance & Reliability Engineer',
    initials: 'TR',
    description: 'Translates predictive model outputs into costed maintenance windows before failures occur.',
    primaryQuestion: 'Is the lining risk real, and when is the optimal intervention window?',
  },
  {
    id: 'energy-manager',
    shellKey: 'EnergyManager',
    name: 'Sofia Lindqvist',
    role: 'Energy Manager',
    initials: 'SL',
    description: 'Dispatches flexible loads against the day-ahead price curve to minimise cost and carbon.',
    primaryQuestion: 'Where is the next megawatt-hour of saving, and what does it cost in CO₂?',
  },
  {
    id: 'quality-engineer',
    shellKey: 'QualityEngineer',
    name: 'Jens Bakker',
    role: 'Quality Engineer',
    initials: 'JB',
    description: 'Monitors SPC charts and batch genealogy to catch yield drift before it reaches the customer.',
    primaryQuestion: 'Which batches are at risk and what is the common cause?',
  },
  {
    id: 'sustainability-officer',
    shellKey: 'SustainabilityOfficer',
    name: 'Amina Haddad',
    role: 'Sustainability Officer',
    initials: 'AH',
    description: 'Ensures every automated recommendation carries auditable evidence for EU AI Act compliance.',
    primaryQuestion: 'Can we prove how every automated recommendation was decided?',
  },
  {
    id: 'knowledge-engineer',
    shellKey: 'KnowledgeEngineer',
    name: 'Pieter Claes',
    role: 'Knowledge Engineer',
    initials: 'PC',
    description: 'Governs the procedure library so only approved, version-controlled knowledge feeds the AI.',
    primaryQuestion: 'Are all retrievable procedures approved and up to date?',
  },
  {
    id: 'ot-systems-engineer',
    shellKey: 'OtSystemsEngineer',
    name: 'Rui Almeida',
    role: 'OT Systems Engineer',
    initials: 'RA',
    description: 'Maintains device fleet health, sensor calibration, and the incident simulation harness.',
    primaryQuestion: 'Which devices need attention and are the signals trustworthy?',
  },
]

export function personaById(id: string): Persona | undefined {
  return personas.find((p) => p.id === id)
}

export function personasByIds(ids: string[]): Persona[] {
  return ids.map((id) => personaById(id)).filter((p): p is Persona => p !== undefined)
}

export function personaByShellKey(key: string | undefined | null): Persona | undefined {
  if (!key) {
    return undefined
  }
  const normalizedKey = key.toLocaleLowerCase()
  return personas.find((p) => p.shellKey.toLocaleLowerCase() === normalizedKey)
}
