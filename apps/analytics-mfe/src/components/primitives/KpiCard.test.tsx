import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { KpiCard, type KpiCardModel } from './KpiCard'

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
})
