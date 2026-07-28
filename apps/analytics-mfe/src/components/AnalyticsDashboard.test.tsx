import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

  it('opens the screen narrative from the affordance beside the page title', async () => {
    const user = userEvent.setup()
    render(<AnalyticsDashboard context={testShellContext()} emit={() => undefined} />)

    await screen.findByRole('heading', { name: 'Command Center', level: 1 })
    await user.click(screen.getByTestId('section-insight-toggle'))

    const popup = await screen.findByTestId('section-insight-popup')
    expect(popup).toHaveTextContent('How this platform creates value')

    await user.keyboard('{Escape}')
    expect(screen.queryByTestId('section-insight-popup')).not.toBeInTheDocument()
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

  it('keeps quality detail requests dormant until a batch is selected', async () => {    render(
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

  it('docks the Copilot chat beside the dashboard only once it is opened', async () => {
    const user = userEvent.setup({ delay: null })
    render(<AnalyticsDashboard context={testShellContext()} emit={() => undefined} />)

    await screen.findByRole('heading', { name: 'Command Center', level: 1 })
    expect(screen.queryByTestId('copilot-dock')).not.toBeInTheDocument()
    expect(screen.queryByTestId('copilot-panel')).not.toBeInTheDocument()

    await user.click(screen.getByTestId('copilot-toggle'))

    expect(await screen.findByTestId('copilot-dock')).toBeInTheDocument()
    expect(await screen.findByTestId('copilot-panel')).toBeInTheDocument()
    expect(screen.getByText('Enterprise data protection applies to this chat.')).toBeInTheDocument()
    // The dashboard itself stays mounted inside the dock.
    expect(await screen.findByRole('heading', { name: 'Command Center', level: 1 })).toBeInTheDocument()

    await user.click(screen.getByTestId('copilot-toggle'))
    expect(screen.queryByTestId('copilot-dock')).not.toBeInTheDocument()
  }, 20000)
})
