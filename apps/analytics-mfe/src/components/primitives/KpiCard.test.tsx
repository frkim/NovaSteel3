import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { KpiCard, deriveKpiStatus, type KpiCardModel } from './KpiCard'
import { kpiSemanticPalette } from '../../designTokens'

const metric: KpiCardModel = {
  id: 'furnace',
  label: 'Furnace lining RUL',
  value: '21',
  unit: 'days (P50)',
  trend: 'down',
  goodDirection: 'up',
  deltaLabel: 'HEARTH-07',
  target: '21-day advance warning',
  sparkline: [10, 12, 9, 14, 8],
  asOf: '2026-07-25T18:45:00Z',
  source: 'fixture',
  why: {
    modelVersion: 'lining-rul-piml/1.3.0-demo',
    scoredAt: '2026-07-25T18:45:00Z',
    drivers: [{ name: 'heat_flux_6h_slope', contribution: 0.29 }],
    confidenceText: 'P50 21.0 days.',
  },
}

describe('KpiCard', () => {
  it('renders the label, value, unit, and target', () => {
    renderWithProviders(<KpiCard metric={metric} />)
    expect(screen.getByText('Furnace lining RUL')).toBeInTheDocument()
    expect(screen.getByText('21')).toBeInTheDocument()
    expect(screen.getByText('days (P50)')).toBeInTheDocument()
    expect(screen.getByText('21-day advance warning')).toBeInTheDocument()
  })

  it('exposes a "Why?" affordance for AI-derived values', () => {
    renderWithProviders(<KpiCard metric={metric} />)
    expect(screen.getByRole('button', { name: 'Why?' })).toBeInTheDocument()
  })

  it('keeps the Why affordance outside the clickable KPI action', () => {
    const onClick = vi.fn()
    renderWithProviders(<KpiCard metric={{ ...metric, onClick }} />)

    fireEvent.click(screen.getByRole('button', { name: 'Why?' }))

    expect(onClick).not.toHaveBeenCalled()
  })

  it('exposes the explanation tooltip on hover and to assistive technology', async () => {
    const tooltip = 'Remaining useful life of the furnace lining at the P50 confidence level.'
    renderWithProviders(<KpiCard metric={{ ...metric, tooltip }} />)

    const labelGroup = screen.getByLabelText(`Furnace lining RUL. ${tooltip}`)
    expect(labelGroup).toBeInTheDocument()

    fireEvent.mouseOver(labelGroup)
    await waitFor(() => expect(screen.getByRole('tooltip')).toHaveTextContent(tooltip))
  })

  it('names the drill-down action with its destination', () => {
    const onClick = vi.fn()
    renderWithProviders(
      <KpiCard metric={{ ...metric, onClick, actionHint: 'the lining forecast' }} />,
    )

    const action = screen.getByRole('button', {
      name: 'Furnace lining RUL: open the lining forecast',
    })
    fireEvent.click(action)

    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('stays inert when no drill-down is available', () => {
    renderWithProviders(<KpiCard metric={metric} />)

    expect(
      screen.queryByRole('button', { name: /Furnace lining RUL: open/ }),
    ).not.toBeInTheDocument()
  })

  describe('semantic status', () => {
    it('derives OK when the metric moves in the good direction', () => {
      expect(deriveKpiStatus({ trend: 'up', goodDirection: 'up' })).toBe('ok')
    })

    it('derives warning when the metric moves in the bad direction', () => {
      expect(deriveKpiStatus({ trend: 'down', goodDirection: 'up' })).toBe('warning')
    })

    it('derives neutral for flat, missing trend, or missing good direction', () => {
      expect(deriveKpiStatus({ trend: 'flat', goodDirection: 'up' })).toBe('neutral')
      expect(deriveKpiStatus({ goodDirection: 'up' })).toBe('neutral')
      expect(deriveKpiStatus({ trend: 'up' })).toBe('neutral')
    })

    it('lets an explicit status override the derived status on the tile', () => {
      renderWithProviders(<KpiCard metric={{ ...metric, status: 'critical', trend: 'up', goodDirection: 'up' }} />)

      expect(screen.getByRole('article', { name: 'Furnace lining RUL; status: Alert' })).toBeInTheDocument()
    })

    it('adds the non-colour status cue to the accessible name', () => {
      renderWithProviders(<KpiCard metric={metric} />)

      expect(screen.getByRole('article', { name: 'Furnace lining RUL; status: At risk' })).toBeInTheDocument()
    })
  })

  describe('semantic background', () => {
    it('maps statuses to distinct semantic accents', () => {
      const palette = kpiSemanticPalette('light')
      const accents = new Set(Object.values(palette).map((entry) => entry.accent))

      expect(accents.size).toBe(4)
      expect(palette.ok.accent).toBe('#0F7B0F')
      expect(palette.warning.accent).toBe('#B26A00')
      expect(palette.critical.accent).toBe('#C42B1C')
      expect(palette.neutral.accent).toBe('#0B5FFF')
    })

    it('keeps light and dark washes available for every semantic status', () => {
      const light = kpiSemanticPalette('light')
      const dark = kpiSemanticPalette('dark')

      for (const status of ['ok', 'warning', 'critical', 'neutral'] as const) {
        expect(light[status].background).toMatch(/^#[0-9A-F]{6}$/)
        expect(dark[status].background).toMatch(/^#[0-9A-F]{6}$/)
        expect(light[status].background).not.toBe(dark[status].background)
      }
    })
  })
})
