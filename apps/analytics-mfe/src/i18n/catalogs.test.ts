import { describe, expect, it } from 'vitest'

import { COPILOT_CATALOGS } from './copilotMessages'
import { DEVICE_CATALOGS } from './deviceMessages'
import { WEBSITE_CATALOGS } from './websiteMessages'
import { SUPPORTED_LANGUAGES, createTranslator } from './messages'

const LOCALES = SUPPORTED_LANGUAGES

describe('i18n catalogs', () => {
  it('exposes the same key set for every supported language', () => {
    for (const catalogs of [COPILOT_CATALOGS, DEVICE_CATALOGS, WEBSITE_CATALOGS]) {
      const reference = Object.keys(catalogs.en).sort()
      for (const locale of LOCALES) {
        expect(Object.keys(catalogs[locale]).sort(), `locale ${locale}`).toEqual(reference)
      }
    }
  })

  it('resolves every device key through the translator in every language', () => {
    for (const locale of LOCALES) {
      const t = createTranslator(locale)
      for (const key of Object.keys(DEVICE_CATALOGS.en)) {
        const value = t(key)
        expect(value, `${locale}:${key}`).not.toEqual(key)
        expect(value.trim().length, `${locale}:${key}`).toBeGreaterThan(0)
      }
    }
  })

  it('resolves every website key through the translator in every language', () => {
    for (const locale of LOCALES) {
      const t = createTranslator(locale)
      for (const key of Object.keys(WEBSITE_CATALOGS.en)) {
        const value = t(key)
        expect(value, `${locale}:${key}`).not.toEqual(key)
        expect(value.trim().length, `${locale}:${key}`).toBeGreaterThan(0)
      }
    }
  })

  it('keeps interpolation placeholders identical across languages', () => {
    const placeholders = (text: string): string[] =>
      [...text.matchAll(/\{(\w+)\}/g)].map((match) => match[1]!).sort()

    for (const key of Object.keys(DEVICE_CATALOGS.en)) {
      const reference = placeholders(DEVICE_CATALOGS.en[key]!)
      for (const locale of LOCALES) {
        expect(placeholders(DEVICE_CATALOGS[locale][key]!), `${locale}:${key}`).toEqual(reference)
      }
    }
  })
})
