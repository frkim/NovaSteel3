export type ThemeMode = 'light' | 'dark' | 'system'

export type CaptureLanguage = 'en' | 'fr' | 'de' | 'nl' | 'es'

export const CAPTURE_LANGUAGES: CaptureLanguage[] = ['en', 'fr', 'de', 'nl', 'es']

/**
 * Steel-plant knowledge domains. Kept in lock-step with the `DOMAINS` list in
 * analytics-mfe `KnowledgeHub.tsx` so a procedure drafted here classifies the
 * same way it would in the Knowledge Hub.
 */
export const DOMAINS = [
  'Blast Furnace',
  'Electric Arc Furnace',
  'Ladle Metallurgy',
  'Continuous Casting',
  'Hot Rolling',
  'Cold Rolling',
  'Refractory',
  'Cooling Water',
  'Gas Cleaning',
  'Energy Management',
  'Safety & LOTO',
  'Environmental / EU ETS',
  'Quality & SPC',
  'Crane & Material Handling',
  'Coke Oven',
] as const
