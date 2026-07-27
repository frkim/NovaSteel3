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

  it('gives the French half a distinct style', () => {
    renderWithProviders(<BilingualText text={TEXT} bilingual />)
    const french = screen.getByText('Moiti\u00e9 fran\u00e7aise')
    const english = screen.getByText('English half')
    // Emotion emits a different generated class when the colour differs.
    expect(french.className).not.toBe(english.className)
    expect(french).toHaveAttribute('lang', 'fr')
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
