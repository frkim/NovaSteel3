import { describe, expect, it, vi } from 'vitest'
import { screen, waitFor, within } from '@testing-library/react'
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

  it('scopes the alert table to the selected site', async () => {
    // The default test context selects DE, so Luxembourg alerts must not leak in.
    renderWithProviders(<CommandCenter />)

    const table = await screen.findByRole('table', { name: /Active alerts and incidents/i })
    await waitFor(() => {
      expect(within(table).getByText(/Caster 01 mould level oscillation/i)).toBeInTheDocument()
    })
    expect(within(table).queryByText(/Evening scarcity spike/i)).not.toBeInTheDocument()
    expect(within(table).queryByText(/HEARTH-SECTOR-07/i)).not.toBeInTheDocument()
    expect(within(table).queryByText(/LUX-/i)).not.toBeInTheDocument()
  })

  it('counts open alerts per site on the status strip', async () => {
    renderWithProviders(<CommandCenter />)

    await waitFor(() => {
      expect(screen.getByText(/open alerts · 1 critical/i)).toBeInTheDocument()
    })
    // Luxembourg carries the seeded critical lining alarm; DE only warnings/info.
    const luCard = screen.getByRole('button', { name: /LU — Moselle Integrated Works/i })
    expect(luCard.textContent).toMatch(/critical/i)
    const deCard = screen.getByRole('button', { name: /DE — Saarbrücken Steelworks/i })
    expect(deCard.textContent).not.toMatch(/critical/i)
    expect(deCard.textContent).toMatch(/open alert/i)
  })
})
