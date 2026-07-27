/**
 * Persona-related message catalogs.
 *
 * These must be spread into CATALOGS in messages.ts by the integration owner.
 * Until then, components can import PERSONA_CATALOGS directly for compile-time
 * safety (keys resolve to themselves at runtime when not wired into the main
 * translator, which is acceptable for labels that are persona names).
 */
type Catalog = Record<string, string>

const EN: Catalog = {
  'persona.plantManager': 'Marc Weber - Plant Manager',
  'persona.furnaceOperator': 'Elena Duarte - Furnace Operator',
  'persona.maintenanceEngineer': 'Tomás Rossi - Maintenance & Reliability Engineer',
  'persona.energyManager': 'Sofia Lindqvist - Energy Manager',
  'persona.qualityEngineer': 'Jens Bakker - Quality Engineer',
  'persona.sustainabilityOfficer': 'Amina Haddad - Sustainability Officer',
  'persona.knowledgeEngineer': 'Pieter Claes - Knowledge Engineer',
  'persona.executive': 'Isabelle Moreau - Executive',
  'persona.otSystemsEngineer': 'Rui Almeida - OT Systems Engineer',
  'persona.platformOps': 'Nils Andersen - Platform Ops',
}

const FR: Catalog = {
  'persona.plantManager': 'Marc Weber - Directeur d\'usine',
  'persona.furnaceOperator': 'Elena Duarte - Opératrice haut-fourneau',
  'persona.maintenanceEngineer': 'Tomás Rossi - Ingénieur fiabilité',
  'persona.energyManager': 'Sofia Lindqvist - Responsable énergie',
  'persona.qualityEngineer': 'Jens Bakker - Ingénieur qualité',
  'persona.sustainabilityOfficer': 'Amina Haddad - Responsable développement durable',
  'persona.knowledgeEngineer': 'Pieter Claes - Ingénieur connaissances',
  'persona.executive': 'Isabelle Moreau - Direction',
  'persona.otSystemsEngineer': 'Rui Almeida - Ingénieur systèmes OT',
  'persona.platformOps': 'Nils Andersen - Ops plateforme',
}

const DE: Catalog = {
  'persona.plantManager': 'Marc Weber - Werksleiter',
  'persona.furnaceOperator': 'Elena Duarte - Hochofenbedienerin',
  'persona.maintenanceEngineer': 'Tomás Rossi - Instandhaltungsingenieur',
  'persona.energyManager': 'Sofia Lindqvist - Energiemanagerin',
  'persona.qualityEngineer': 'Jens Bakker - Qualitätsingenieur',
  'persona.sustainabilityOfficer': 'Amina Haddad - Nachhaltigkeitsbeauftragte',
  'persona.knowledgeEngineer': 'Pieter Claes - Wissensingenieur',
  'persona.executive': 'Isabelle Moreau - Geschäftsführung',
  'persona.otSystemsEngineer': 'Rui Almeida - OT-Systemingenieur',
  'persona.platformOps': 'Nils Andersen - Plattform-Ops',
}

const NL: Catalog = {
  'persona.plantManager': 'Marc Weber - Fabrieksmanager',
  'persona.furnaceOperator': 'Elena Duarte - Hoogovenoperator',
  'persona.maintenanceEngineer': 'Tomás Rossi - Onderhoudsingenieur',
  'persona.energyManager': 'Sofia Lindqvist - Energiemanager',
  'persona.qualityEngineer': 'Jens Bakker - Kwaliteitsingenieur',
  'persona.sustainabilityOfficer': 'Amina Haddad - Duurzaamheidsmanager',
  'persona.knowledgeEngineer': 'Pieter Claes - Kennisingenieur',
  'persona.executive': 'Isabelle Moreau - Directie',
  'persona.otSystemsEngineer': 'Rui Almeida - OT-systeemingenieur',
  'persona.platformOps': 'Nils Andersen - Platform-ops',
}

const ES: Catalog = {
  'persona.plantManager': 'Marc Weber - Director de planta',
  'persona.furnaceOperator': 'Elena Duarte - Operadora de horno',
  'persona.maintenanceEngineer': 'Tomás Rossi - Ingeniero de mantenimiento',
  'persona.energyManager': 'Sofia Lindqvist - Responsable de energía',
  'persona.qualityEngineer': 'Jens Bakker - Ingeniero de calidad',
  'persona.sustainabilityOfficer': 'Amina Haddad - Responsable de sostenibilidad',
  'persona.knowledgeEngineer': 'Pieter Claes - Ingeniero del conocimiento',
  'persona.executive': 'Isabelle Moreau - Dirección',
  'persona.otSystemsEngineer': 'Rui Almeida - Ingeniero de sistemas OT',
  'persona.platformOps': 'Nils Andersen - Ops de plataforma',
}

export const PERSONA_CATALOGS: Record<string, Catalog> = { en: EN, fr: FR, de: DE, nl: NL, es: ES }
