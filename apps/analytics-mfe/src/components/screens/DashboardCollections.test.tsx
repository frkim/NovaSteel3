import { describe, expect, it } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { DashboardCollections } from './DashboardCollections'

describe('DashboardCollections', () => {
  it('renders an icon for each collection card', async () => {
    renderWithProviders(<DashboardCollections />)

    await waitFor(() => {
      const cards = screen.getAllByRole('article')
      expect(cards.length).toBeGreaterThanOrEqual(6)
      for (const card of cards) {
        const svg = card.querySelector('svg[aria-hidden]')
        expect(svg, `card "${card.getAttribute('aria-label')}" should have an icon`).toBeTruthy()
      }
    })
  })

  it('icons are aria-hidden and decorative', async () => {
    renderWithProviders(<DashboardCollections />)

    await waitFor(() => {
      const cards = screen.getAllByRole('article')
      for (const card of cards) {
        const svg = card.querySelector('svg')
        expect(svg?.getAttribute('aria-hidden')).toBe('true')
      }
    })
  })
})
