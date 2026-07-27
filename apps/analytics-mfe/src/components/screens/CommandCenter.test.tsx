import { describe, expect, it, vi } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders, testAnalyticsValue } from '../../test/renderWithProviders'
import { CommandCenter } from './CommandCenter'

describe('CommandCenter', () => {
  it('every KPI tile has an onClick handler', async () => {
    const emit = vi.fn()
    const value = testAnalyticsValue({ emit })

    renderWithProviders(<CommandCenter />, value)

    await waitFor(() => {
      const tiles = screen.getAllByRole('button', { name: /Energy|CO₂|Furnace|yield|alerts/i })
      expect(tiles.length).toBeGreaterThanOrEqual(5)
    })
  })

  it('clicking the energy KPI tile emits a nav intent to energy-optimization', async () => {
    const emit = vi.fn()
    const value = testAnalyticsValue({ emit })

    renderWithProviders(<CommandCenter />, value)

    await waitFor(() => {
      const tile = screen.getByRole('button', { name: /Energy consumption/i })
      tile.click()
    })

    expect(emit).toHaveBeenCalledWith('nav.intent', {
      route: expect.stringContaining('/energy-optimization/spot-price-schedule'),
    })
  })

  it('clicking the CO₂ KPI tile emits a nav intent to sustainability-compliance', async () => {
    const emit = vi.fn()
    const value = testAnalyticsValue({ emit })

    renderWithProviders(<CommandCenter />, value)

    await waitFor(() => {
      const tile = screen.getByRole('button', { name: /CO₂/i })
      tile.click()
    })

    expect(emit).toHaveBeenCalledWith('nav.intent', {
      route: expect.stringContaining('/sustainability-compliance/emissions-ledger'),
    })
  })

  it('clicking a site card emits a nav intent to that site', async () => {
    const emit = vi.fn()
    const value = testAnalyticsValue({ emit })

    renderWithProviders(<CommandCenter />, value)

    await waitFor(() => {
      const siteCard = screen.getByRole('button', { name: /LU — Moselle Integrated Works/i })
      siteCard.click()
    })

    expect(emit).toHaveBeenCalledWith('nav.intent', {
      route: '/lu/command-center/overview',
    })
  })

  it('renders site status panel', async () => {
    renderWithProviders(<CommandCenter />)

    await waitFor(() => {
      expect(screen.getByText('Site status')).toBeInTheDocument()
      expect(screen.getByText('Moselle Integrated Works')).toBeInTheDocument()
    })
  })
})
