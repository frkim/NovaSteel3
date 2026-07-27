import { describe, expect, it, beforeEach } from 'vitest'
import { screen, waitFor, within, fireEvent } from '@testing-library/react'
import { useState } from 'react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { KpiBand, PanelCard, SectionStack, TwoColumn } from '../screens/common'
import { collectDockPanels } from './dockPanels'
import type { KpiCardModel } from '../primitives/KpiCard'

const metrics: KpiCardModel[] = [
  { id: 'energy', label: 'Energy', value: '512', unit: 'kWh/t' },
  { id: 'co2', label: 'CO2', value: '1.4', unit: 't' },
]

describe('collectDockPanels', () => {
  it('derives one panel per layout primitive, in declaration order', () => {
    const specs = collectDockPanels([
      <KpiBand key="k" metrics={metrics} />,
      <PanelCard key="a" id="alpha" title="Alpha">
        <p>a</p>
      </PanelCard>,
      <PanelCard key="b" id="beta" title="Beta">
        <p>b</p>
      </PanelCard>,
    ])

    expect(specs.map((spec) => spec.id)).toEqual(['kpi-band', 'alpha', 'beta'])
    expect(specs.map((spec) => spec.title)).toEqual(['Key metrics', 'Alpha', 'Beta'])
  })

  it('marks a panel closable only when the screen supplies onDockClose', () => {
    const specs = collectDockPanels([
      <PanelCard key="a" id="alpha" title="Alpha">
        <p>a</p>
      </PanelCard>,
      <PanelCard key="b" id="beta" title="Beta" onDockClose={() => {}}>
        <p>b</p>
      </PanelCard>,
    ])

    expect(specs.map((spec) => spec.closable)).toEqual([false, true])
  })

  it('places the side column of a TwoColumn to the right of the main column', () => {
    const specs = collectDockPanels([
      <TwoColumn
        key="split"
        main={
          <PanelCard id="main" title="Main">
            <p>main</p>
          </PanelCard>
        }
        side={
          <PanelCard id="side" title="Side">
            <p>side</p>
          </PanelCard>
        }
      />,
    ])

    expect(specs.map((spec) => spec.id)).toEqual(['main', 'side'])
    expect(specs[0].placement).toBe('below')
    expect(specs[1].placement).toBe('right')
    expect(specs[1].reference).toBe('main')
  })

  it('treats a render-function child as a single opaque panel', () => {
    function Boundary({ children }: { children: () => JSX.Element }) {
      return children()
    }
    const specs = collectDockPanels([
      <Boundary key="guard">{() => <KpiBand metrics={metrics} />}</Boundary>,
    ])

    expect(specs).toHaveLength(1)
    expect(specs[0].title).toBe('Key metrics')
    expect(specs[0].closable).toBe(false)
  })

  it('de-duplicates ids so two untitled panels cannot collide', () => {
    const specs = collectDockPanels([
      <PanelCard key="a" id="same" title="A">
        <p>a</p>
      </PanelCard>,
      <PanelCard key="b" id="same" title="B">
        <p>b</p>
      </PanelCard>,
    ])

    expect(new Set(specs.map((spec) => spec.id)).size).toBe(2)
  })

  it('lets an opaque child name itself through dockTitle / dockId', () => {
    function Boundary({ children }: { children: () => JSX.Element; dockId?: string; dockTitle?: string }) {
      return children()
    }
    const specs = collectDockPanels([
      <Boundary key="guard" dockId="lining-risk" dockTitle="Lining risk">
        {() => <p>body</p>}
      </Boundary>,
    ])

    expect(specs).toHaveLength(1)
    expect(specs[0].id).toBe('lining-risk')
    expect(specs[0].title).toBe('Lining risk')
  })

  it('reads data-dock-* from a host element, including a preferred height', () => {
    const specs = collectDockPanels([
      <div key="host" data-dock-id="collections" data-dock-title="Collections" data-dock-height={140}>
        <span>body</span>
      </div>,
    ])

    expect(specs[0].id).toBe('collections')
    expect(specs[0].title).toBe('Collections')
    expect(specs[0].initialHeight).toBe(140)
  })

  it('finds a name nested below a wrapper element', () => {
    function Boundary({ children }: { children: () => JSX.Element }) {
      return children()
    }
    const specs = collectDockPanels([
      <div key="wrap">
        <section data-dock-title="Nested name">
          <Boundary>{() => <p>body</p>}</Boundary>
        </section>
      </div>,
    ])

    expect(specs[0].title).toBe('Nested name')
  })
})

describe('SectionStack docking', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('renders the declared panels as dock tabs', async () => {
    renderWithProviders(
      <SectionStack>
        <PanelCard id="alpha" title="Alpha panel">
          <p>alpha body</p>
        </PanelCard>
        <PanelCard id="beta" title="Beta panel">
          <p>beta body</p>
        </PanelCard>
      </SectionStack>,
    )

    expect(await screen.findByTestId('workspace-dock')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByTestId('dock-tab-alpha')).toHaveTextContent('Alpha panel')
      expect(screen.getByTestId('dock-tab-beta')).toHaveTextContent('Beta panel')
    })
  })

  it('gives structural panels no close button', async () => {
    renderWithProviders(
      <SectionStack>
        <PanelCard id="alpha" title="Alpha panel">
          <p>alpha body</p>
        </PanelCard>
        <PanelCard id="beta" title="Beta panel">
          <p>beta body</p>
        </PanelCard>
      </SectionStack>,
    )

    const tab = await screen.findByTestId('dock-tab-alpha')
    expect(within(tab).queryByTitle('Close')).toBeNull()
    expect(tab.querySelector('.dv-default-tab-action')).toBeNull()
  })

  it('closes a dismissible panel through the screen state, not behind it', async () => {
    function Harness() {
      const [detailOpen, setDetailOpen] = useState(true)
      return (
        <SectionStack>
          <PanelCard id="alpha" title="Alpha panel">
            <p>alpha body</p>
          </PanelCard>
          {detailOpen && (
            <PanelCard id="detail" title="Detail panel" onDockClose={() => setDetailOpen(false)}>
              <p>detail body</p>
            </PanelCard>
          )}
        </SectionStack>
      )
    }

    renderWithProviders(<Harness />)

    const tab = await screen.findByTestId('dock-tab-detail')
    const close = tab.querySelector('.dv-default-tab-action')
    expect(close).not.toBeNull()

    fireEvent.click(close as Element)

    await waitFor(() => {
      expect(screen.queryByTestId('dock-tab-detail')).toBeNull()
    })
    // The panel that must survive is still there.
    expect(screen.getByTestId('dock-tab-alpha')).toBeInTheDocument()
  })

  it('anchors a late-appearing panel above its declared successor', async () => {
    function Harness() {
      const [ready, setReady] = useState(false)
      return (
        <>
          <button type="button" onClick={() => setReady(true)}>
            load
          </button>
          <SectionStack>
            {ready && <KpiBand metrics={metrics} />}
            <PanelCard id="table" title="Table panel">
              <p>table body</p>
            </PanelCard>
          </SectionStack>
        </>
      )
    }

    const { container } = renderWithProviders(<Harness />)
    await screen.findByTestId('dock-tab-table')

    fireEvent.click(screen.getByRole('button', { name: 'load' }))

    await screen.findByTestId('dock-tab-kpi-band')
    await waitFor(() => {
      const order = Array.from(container.querySelectorAll('[data-testid^="dock-tab-"]')).map(
        (node) => node.getAttribute('data-testid'),
      )
      expect(order).toEqual(['dock-tab-kpi-band', 'dock-tab-table'])
    })
  })

  it('falls back to a plain stack when docking is disabled', () => {    window.NOVASTEEL_ANALYTICS_CONFIG = { fixturesOnly: true, disableDock: true }
    try {
      renderWithProviders(
        <SectionStack>
          <PanelCard id="alpha" title="Alpha panel">
            <p>alpha body</p>
          </PanelCard>
          <PanelCard id="beta" title="Beta panel">
            <p>beta body</p>
          </PanelCard>
        </SectionStack>,
      )
      expect(screen.queryByTestId('workspace-dock')).toBeNull()
      expect(screen.getByText('Alpha panel')).toBeInTheDocument()
    } finally {
      window.NOVASTEEL_ANALYTICS_CONFIG = { fixturesOnly: true }
    }
  })
})
