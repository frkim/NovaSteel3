import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'
import { useState } from 'react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { createTranslator } from '../../i18n/messages'
import { HELP_EN } from '../../i18n/helpMessages'
import { HELP_FR } from '../../i18n/helpMessages.fr'
import { HelpAssistant } from './HelpAssistant'
import { pickHelpKey, resolveHelpTarget } from './resolveHelpTarget'

const t = createTranslator('en')

function Harness({ bilingual = false, scope = 'operations/overview' }: { bilingual?: boolean; scope?: string }) {
  const [active, setActive] = useState(true)
  const [navigated, setNavigated] = useState(false)
  return (
    <div>
      <button type="button" data-testid="nav" onClick={() => setNavigated(true)}>
        navigate
      </button>
      {navigated && <span data-testid="navigated" />}

      <article aria-label="Energy intensity" data-help="kpi:energy" data-help-detail="kWh per tonne">
        <span data-testid="kpi-value">512</span>
      </article>

      <figure aria-label="Shell temperature" data-help="chart.heatmap">
        <figcaption>Shell temperature</figcaption>
        <span data-testid="chart-body">svg</span>
      </figure>

      <table aria-label="Sensors" data-help="generic.table">
        <thead>
          <tr>
            <th data-testid="column">Sensor</th>
          </tr>
        </thead>
        <tbody>
          <tr data-testid="row">
            <td>TC-01</td>
          </tr>
        </tbody>
      </table>

      <div data-testid="unknown">nothing declared</div>

      <HelpAssistant
        active={active}
        onExit={() => setActive(false)}
        scope={scope}
        locale="en"
        bilingual={bilingual}
        t={t}
      />
    </div>
  )
}

describe('resolveHelpTarget', () => {
  it('walks up to the nearest declared topic', () => {
    document.body.innerHTML = '<article data-help="kpi:co2"><span id="inner">1.4</span></article>'
    const target = resolveHelpTarget(document.getElementById('inner'))
    expect(target?.keys).toEqual(['kpi:co2'])
  })

  it('prefers a scoped topic over the bare one', () => {
    document.body.innerHTML = '<article data-help="kpi:peak"><span id="inner">1</span></article>'
    const target = resolveHelpTarget(document.getElementById('inner'), 'furnace-health/thermal-explorer')
    expect(target?.keys).toEqual(['furnace-health/thermal-explorer:kpi:peak', 'kpi:peak'])
  })

  it('lets a column header win over the table that contains it', () => {
    document.body.innerHTML =
      '<table data-help="generic.table"><thead><tr><th id="h">Sensor</th></tr></thead></table>'
    const target = resolveHelpTarget(document.getElementById('h'))
    expect(target?.keys[0]).toBe('generic.tableHeader')
    expect(target?.keys).toContain('generic.table')
    expect(target?.label).toBe('Sensor')
  })

  it('falls back to the DOM shape when nothing declares a topic', () => {
    document.body.innerHTML = '<figure aria-label="Trend"><span id="inner">svg</span></figure>'
    const target = resolveHelpTarget(document.getElementById('inner'))
    expect(target?.keys).toEqual(['generic.chart'])
    expect(target?.label).toBe('Trend')
  })

  it('returns null when the pointer is on nothing recognisable', () => {
    document.body.innerHTML = '<span id="inner">plain</span>'
    expect(resolveHelpTarget(document.getElementById('inner'))).toBeNull()
  })

  it('lets a chart name its own type instead of the container fallback', () => {
    document.body.innerHTML =
      '<figure data-help="generic.chart"><div data-help="chart.pareto"><span id="inner">bars</span></div></figure>'
    const target = resolveHelpTarget(document.getElementById('inner'))
    expect(target?.keys).toEqual(['chart.pareto'])
  })

  it('picks the first key the catalog actually knows', () => {
    expect(pickHelpKey(['nope', 'kpi:energy'], HELP_EN)).toBe('kpi:energy')
    expect(pickHelpKey(['nope'], HELP_EN)).toBeUndefined()
  })
})

describe('HelpAssistant', () => {
  it('shows the explain-mode banner while active', () => {
    renderWithProviders(<Harness />)
    expect(screen.getByTestId('help-mode-banner')).toBeInTheDocument()
    expect(document.body.classList.contains('novasteel-help-mode')).toBe(true)
  })

  it('explains a KPI tile instead of letting it navigate', () => {
    renderWithProviders(<Harness />)
    fireEvent.click(screen.getByTestId('nav'))
    expect(screen.queryByTestId('navigated')).not.toBeInTheDocument()
  })

  it('describes the clicked element and frames it', () => {
    renderWithProviders(<Harness />)
    fireEvent.click(screen.getByTestId('kpi-value'))

    const popup = screen.getByTestId('help-popup')
    expect(popup).toHaveAttribute('data-help-topic', 'kpi:energy')
    expect(popup).toHaveTextContent(HELP_EN['kpi:energy'].what)
    expect(popup).toHaveTextContent('Energy intensity')
    expect(screen.getByTestId('help-selection-frame')).toBeInTheDocument()
  })

  it('replaces the popup when another element is selected', () => {
    renderWithProviders(<Harness />)
    fireEvent.click(screen.getByTestId('kpi-value'))
    expect(screen.getByTestId('help-popup')).toHaveAttribute('data-help-topic', 'kpi:energy')

    fireEvent.click(screen.getByTestId('chart-body'))
    const popups = screen.getAllByTestId('help-popup')
    expect(popups).toHaveLength(1)
    expect(popups[0]).toHaveAttribute('data-help-topic', 'chart.heatmap')
  })

  it('prefers the column-header topic when a header is clicked', () => {
    renderWithProviders(<Harness />)
    fireEvent.click(screen.getByTestId('column'))
    expect(screen.getByTestId('help-popup')).toHaveAttribute('data-help-topic', 'generic.tableHeader')
  })

  it('borrows the table topic for a body row that has none of its own', () => {
    renderWithProviders(<Harness />)
    fireEvent.click(screen.getByTestId('row'))
    expect(screen.getByTestId('help-popup')).toHaveAttribute('data-help-topic', 'generic.tableRow')
  })

  it('says so when no explanation exists for the element', () => {
    renderWithProviders(<Harness />)
    fireEvent.click(screen.getByTestId('unknown'))
    expect(screen.queryByTestId('help-popup')).not.toBeInTheDocument()
  })

  it('closes only the popup from its close button, staying in explain mode', () => {
    renderWithProviders(<Harness />)
    fireEvent.click(screen.getByTestId('kpi-value'))
    fireEvent.click(screen.getByTestId('help-popup-close'))

    expect(screen.queryByTestId('help-popup')).not.toBeInTheDocument()
    expect(screen.getByTestId('help-mode-banner')).toBeInTheDocument()
  })

  it('leaves explain mode on Escape', () => {
    renderWithProviders(<Harness />)
    fireEvent.click(screen.getByTestId('kpi-value'))
    fireEvent.keyDown(window, { key: 'Escape' })

    expect(screen.queryByTestId('help-mode-banner')).not.toBeInTheDocument()
    expect(screen.queryByTestId('help-popup')).not.toBeInTheDocument()
    expect(document.body.classList.contains('novasteel-help-mode')).toBe(false)
  })

  it('leaves explain mode from the banner exit button', () => {
    renderWithProviders(<Harness />)
    fireEvent.click(screen.getByTestId('help-mode-exit'))
    expect(screen.queryByTestId('help-mode-banner')).not.toBeInTheDocument()
  })

  it('lets clicks through again once explain mode is off', () => {
    renderWithProviders(<Harness />)
    fireEvent.keyDown(window, { key: 'Escape' })
    fireEvent.click(screen.getByTestId('nav'))
    expect(screen.getByTestId('navigated')).toBeInTheDocument()
  })

  it('shows English and French together in bilingual mode', () => {
    renderWithProviders(<Harness bilingual />)
    fireEvent.click(screen.getByTestId('kpi-value'))

    const popup = screen.getByTestId('help-popup')
    expect(popup).toHaveTextContent(HELP_EN['kpi:energy'].what)
    expect(popup).toHaveTextContent(HELP_FR['kpi:energy'].what)
  })

  it('renders nothing at all when inactive', () => {
    const onExit = vi.fn()
    renderWithProviders(
      <HelpAssistant active={false} onExit={onExit} scope="operations/overview" locale="en" t={t} />,
    )
    expect(screen.queryByTestId('help-mode-banner')).not.toBeInTheDocument()
    expect(document.body.classList.contains('novasteel-help-mode')).toBe(false)
  })
})
