import { describe, expect, it } from 'vitest'
import { HELP_CATALOGS, resolveHelpCatalog } from './helpCatalogs'
import { HELP_UI_CATALOGS } from './helpUiMessages'
import { SUPPORTED_LANGUAGES } from './messages'

const TOPIC_FIELDS = ['title', 'what', 'steel', 'useIt'] as const

describe('help catalogs', () => {
  // The English catalog is assembled from the base topics plus satellite
  // catalogs (see helpCatalogs.ts), so the merged result — not the raw
  // HELP_EN export — is the contract every other locale must match.
  const english = HELP_CATALOGS.en
  const expectedTopics = Object.keys(english).sort()

  it('covers every supported language', () => {
    expect(Object.keys(HELP_CATALOGS).sort()).toEqual([...SUPPORTED_LANGUAGES].sort())
    expect(Object.keys(HELP_UI_CATALOGS).sort()).toEqual([...SUPPORTED_LANGUAGES].sort())
  })

  for (const language of SUPPORTED_LANGUAGES) {
    it(`${language} declares exactly the English topic set`, () => {
      expect(Object.keys(HELP_CATALOGS[language]).sort()).toEqual(expectedTopics)
    })

    it(`${language} declares the same optional fields as English`, () => {
      const catalog = HELP_CATALOGS[language]
      for (const topicId of expectedTopics) {
        const source = english[topicId]
        const translated = catalog[topicId]
        for (const field of TOPIC_FIELDS) {
          expect(
            field in translated,
            `${language}/${topicId}: '${field}' presence must match English`,
          ).toBe(field in source)
        }
      }
    })

    it(`${language} leaves no topic text empty`, () => {
      for (const [topicId, topic] of Object.entries(HELP_CATALOGS[language])) {
        for (const field of TOPIC_FIELDS) {
          const value = topic[field]
          if (value !== undefined) {
            expect(value.trim().length, `${language}/${topicId}/${field}`).toBeGreaterThan(0)
          }
        }
      }
    })

    it(`${language} defines every help.* chrome string`, () => {
      expect(Object.keys(HELP_UI_CATALOGS[language]).sort()).toEqual(Object.keys(HELP_UI_CATALOGS.en).sort())
    })
  }

  it('falls back to English for an unknown locale', () => {
    expect(resolveHelpCatalog('pt-BR')).toBe(HELP_CATALOGS.en)
  })

  it('resolves by language, ignoring the region', () => {
    expect(resolveHelpCatalog('fr-LU')).toBe(HELP_CATALOGS.fr)
  })

  it('stacks both languages in bilingual mode', () => {
    const topic = resolveHelpCatalog('en-GB', true)['kpi:co2']
    expect(topic.what).toContain(HELP_CATALOGS.en['kpi:co2'].what)
    expect(topic.what).toContain(HELP_CATALOGS.fr['kpi:co2'].what)
  })

  it('leads with French when the portal is French', () => {
    const topic = resolveHelpCatalog('fr-FR', true)['kpi:co2']
    expect(topic.what.indexOf(HELP_CATALOGS.fr['kpi:co2'].what)).toBeLessThan(
      topic.what.indexOf(HELP_CATALOGS.en['kpi:co2'].what),
    )
  })

  it('keeps optional fields optional in bilingual mode', () => {
    const bilingual = resolveHelpCatalog('en', true)
    for (const topicId of expectedTopics) {
      for (const field of TOPIC_FIELDS) {
        expect(field in bilingual[topicId], `${topicId}/${field}`).toBe(field in english[topicId])
      }
    }
  })
})
