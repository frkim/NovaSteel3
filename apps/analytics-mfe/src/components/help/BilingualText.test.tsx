import { describe, expect, it } from 'vitest'
import { screen } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { BilingualText } from './BilingualText'
import { BILINGUAL_SEPARATOR, isFrenchFirst } from '../../i18n/helpCatalogs'

const TEXT = `English half${BILINGUAL_SEPARATOR}Moiti\u00e9 fran\u00e7aise`

describe('BilingualText', () => {
  it('renders a single paragraph when bilingual mode is off', () => {
    renderWithProviders(<BilingualText text="Just English" />)
    expect(screen.getByText('Just English')).toBeInTheDocument()
    expect(document.querySelector('[data-bilingual-segment]')).toBeNull()
  })

  it('splits the two languages into separate paragraphs', () => {
    renderWithProviders(<BilingualText text={TEXT} bilingual />)
    expect(screen.getByText('English half').tagName).toBe('P')
    expect(screen.getByText('Moiti\u00e9 fran\u00e7aise').tagName).toBe('P')
  })

  it('marks the second half as French when English leads', () => {
    renderWithProviders(<BilingualText text={TEXT} bilingual />)
    expect(screen.getByText('Moiti\u00e9 fran\u00e7aise')).toHaveAttribute('data-bilingual-segment', 'fr')
    expect(screen.getByText('English half')).toHaveAttribute('data-bilingual-segment', 'en')
  })

  it('marks the first half as French when French leads', () => {
    const frenchFirstText = `Moiti\u00e9 fran\u00e7aise${BILINGUAL_SEPARATOR}English half`
    renderWithProviders(<BilingualText text={frenchFirstText} bilingual frenchFirst />)
    expect(screen.getByText('Moiti\u00e9 fran\u00e7aise')).toHaveAttribute('data-bilingual-segment', 'fr')
    expect(screen.getByText('English half')).toHaveAttribute('data-bilingual-segment', 'en')
  })

  it('paints the French half in dark blue', () => {
    renderWithProviders(<BilingualText text={TEXT} bilingual />)
    const french = screen.getByText('Moiti\u00e9 fran\u00e7aise')
    const english = screen.getByText('English half')
    // Guards a real regression: MUI v9 silently drops the color prop on
    // Typography for raw values and palette paths, so it has to come through sx.
    expect(getComputedStyle(french).color).toBe('rgb(10, 47, 134)')
    expect(getComputedStyle(english).color).not.toBe('rgb(10, 47, 134)')
    expect(french.className).not.toBe(english.className)
    expect(french).toHaveAttribute('lang', 'fr')
  })

  it('lays the two languages out side by side with the translation second', () => {
    renderWithProviders(<BilingualText text={TEXT} bilingual />)
    const columns = document.querySelector('[data-bilingual-columns="true"]')
    expect(columns).not.toBeNull()
    expect(getComputedStyle(columns as Element).gridTemplateColumns).toBe('1fr 1fr')
    const children = Array.from((columns as Element).children)
    expect(children).toHaveLength(2)
    expect(children[0]).toHaveAttribute('data-bilingual-segment', 'en')
    expect(children[1]).toHaveAttribute('data-bilingual-segment', 'fr')
  })

  it('keeps the portal language in the left column when French leads', () => {
    const frenchFirstText = `Moiti\u00e9 fran\u00e7aise${BILINGUAL_SEPARATOR}English half`
    renderWithProviders(<BilingualText text={frenchFirstText} bilingual frenchFirst />)
    const children = Array.from(
      (document.querySelector('[data-bilingual-columns="true"]') as Element).children,
    )
    expect(children[0]).toHaveAttribute('data-bilingual-segment', 'fr')
    expect(children[1]).toHaveAttribute('data-bilingual-segment', 'en')
  })

  it('does not build columns for a single language', () => {
    renderWithProviders(<BilingualText text="Same in both" bilingual />)
    expect(document.querySelector('[data-bilingual-columns="true"]')).toBeNull()
  })

  it('does not tag a language when only one half is present', () => {
    renderWithProviders(<BilingualText text="Same in both" bilingual />)
    expect(screen.getByText('Same in both')).not.toHaveAttribute('data-bilingual-segment')
  })
})

describe('isFrenchFirst', () => {
  it('is true only for French locales', () => {
    expect(isFrenchFirst('fr-LU')).toBe(true)
    expect(isFrenchFirst('fr')).toBe(true)
    expect(isFrenchFirst('en-LU')).toBe(false)
    expect(isFrenchFirst('nl-BE')).toBe(false)
  })
})
