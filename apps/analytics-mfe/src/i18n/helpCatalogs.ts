import type { HelpCatalog, HelpTopic } from '../components/help/helpTypes'
import { HELP_EN } from './helpMessages'
import { HELP_FR } from './helpMessages.fr'
import { HELP_DE } from './helpMessages.de'
import { HELP_NL } from './helpMessages.nl'
import { HELP_ES } from './helpMessages.es'
import { languageOf } from './messages'

export const HELP_CATALOGS: Record<string, HelpCatalog> = {
  en: HELP_EN,
  fr: HELP_FR,
  de: HELP_DE,
  nl: HELP_NL,
  es: HELP_ES,
}

function mergeField(primary?: string, secondary?: string): string | undefined {
  if (!primary) return secondary
  if (!secondary || secondary === primary) return primary
  return `${primary}\n\n${secondary}`
}

/**
 * Bilingual mode stacks the French text under the English text in the same
 * popup. Visitors who are more comfortable in one language get both without
 * having to switch the whole portal locale.
 */
function bilingual(base: HelpCatalog, other: HelpCatalog): HelpCatalog {
  const merged: HelpCatalog = {}
  for (const [key, topic] of Object.entries(base)) {
    const twin = other[key]
    if (!twin) {
      merged[key] = topic
      continue
    }
    const next: HelpTopic = {
      title: twin.title && twin.title !== topic.title ? `${topic.title} / ${twin.title}` : topic.title,
      what: mergeField(topic.what, twin.what) ?? topic.what,
    }
    const steel = mergeField(topic.steel, twin.steel)
    if (steel) next.steel = steel
    const useIt = mergeField(topic.useIt, twin.useIt)
    if (useIt) next.useIt = useIt
    merged[key] = next
  }
  return merged
}

const BILINGUAL_EN_FR = bilingual(HELP_EN, HELP_FR)
const BILINGUAL_FR_EN = bilingual(HELP_FR, HELP_EN)

/**
 * @param locale portal locale, e.g. `fr-FR`.
 * @param enFr when true, show English and French together. A French portal
 *   leads with French; every other locale leads with English.
 */
export function resolveHelpCatalog(locale: string, enFr = false): HelpCatalog {
  const language = languageOf(locale)
  if (enFr) return language === 'fr' ? BILINGUAL_FR_EN : BILINGUAL_EN_FR
  return HELP_CATALOGS[language] ?? HELP_EN
}
