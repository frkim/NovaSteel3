import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { KpiCard, kpiBackgroundColor, type KpiCardModel } from './KpiCard'
import { KPI_PASTEL_LIGHT } from '../../designTokens'

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

  describe('pastel background', () => {
    it('assigns the same colour for the same id deterministically', () => {
      const color1 = kpiBackgroundColor('furnace', KPI_PASTEL_LIGHT)
      const color2 = kpiBackgroundColor('furnace', KPI_PASTEL_LIGHT)
      expect(color1).toBe(color2)
    })

    it('assigns different colours for different ids in a typical band', () => {
      const ids = ['furnace', 'energy', 'defects', 'throughput', 'scrap', 'uptime']
      const colors = ids.map((id) => kpiBackgroundColor(id, KPI_PASTEL_LIGHT))
      const unique = new Set(colors)
      expect(unique.size).toBeGreaterThanOrEqual(4)
    })

    it('returns a value from the palette', () => {
      const color = kpiBackgroundColor('anything', KPI_PASTEL_LIGHT)
      expect(KPI_PASTEL_LIGHT).toContain(color)
    })
  })
})
