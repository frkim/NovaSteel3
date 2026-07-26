import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AnalyticsDashboard } from './AnalyticsDashboard'
import { testShellContext } from '../test/renderWithProviders'

describe('AnalyticsDashboard (UI smoke)', () => {
  it('renders the Command Center with the demo banner and KPI band', async () => {
    render(<AnalyticsDashboard context={testShellContext()} emit={() => undefined} />)

    expect(screen.getByText(/Synthetic demo data/i)).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Command Center', level: 1 })).toBeInTheDocument()
    expect(await screen.findByText('Furnace lining RUL')).toBeInTheDocument()
    expect(await screen.findByText('Active alerts')).toBeInTheDocument()
  })

  it('renders the furnace lining forecast screen with the RUL uncertainty band', async () => {
    render(
      <AnalyticsDashboard
        context={testShellContext({
          activePersona: 'FurnaceOperator',
          navigation: { section: 'furnace-health', subView: 'lining-forecast', site: 'de' },
        })}
        emit={() => undefined}
      />,
    )

    expect(await screen.findByRole('heading', { name: 'Furnace Health', level: 1 })).toBeInTheDocument()
    expect(await screen.findByText('Days to threshold')).toBeInTheDocument()
    expect(await screen.findByText(/21-day horizon/i)).toBeInTheDocument()
  })

  it('keeps quality detail requests dormant until a batch is selected', async () => {
    render(
      <AnalyticsDashboard
        context={testShellContext({
          activePersona: 'QualityEngineer',
          navigation: { section: 'quality', subView: 'batches', site: 'de' },
        })}
        emit={() => undefined}
      />,
    )

    expect(await screen.findByRole('heading', { name: 'Quality', level: 1 })).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: /Batch .* detail/ })).not.toBeInTheDocument()
  })
})
