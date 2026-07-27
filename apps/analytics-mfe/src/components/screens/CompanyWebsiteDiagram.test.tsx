import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, within } from '@testing-library/react'
import { renderWithProviders, testAnalyticsValue } from '../../test/renderWithProviders'
import { ProcessDiagram } from './CompanyWebsiteDiagram'

const PROPS = {
  stem: 'steel-route-blast-furnace',
  title: 'The integrated route, end to end',
  alt: 'Illustrated overview of the steps of steel creation.',
  caption: 'Iron ore enters on the left; finished products leave on the right.',
}

function renderDiagram(overrides: Partial<typeof PROPS> = {}) {
  const emit = vi.fn()
  renderWithProviders(<ProcessDiagram {...PROPS} {...overrides} />, testAnalyticsValue({ emit }))
}

function image() {
  return screen.getByAltText(PROPS.alt)
}

describe('ProcessDiagram', () => {
  it('renders the artwork with a responsive source set', () => {
    renderDiagram()
    const img = image()
    expect(img).toHaveAttribute('src', '/media/steel-route-blast-furnace.webp')
    expect(img.getAttribute('srcset')).toContain('/media/steel-route-blast-furnace-sm.webp 900w')
    expect(img.getAttribute('srcset')).toContain('/media/steel-route-blast-furnace.webp 1800w')
  })

  it('serves a figure from a single rendition so every figure shares one frame', () => {
    renderWithProviders(
      <ProcessDiagram {...PROPS} stem="rolling-mill-stand" variant="figure" />,
      testAnalyticsValue({}),
    )
    const img = image()
    expect(img).toHaveAttribute('src', '/media/rolling-mill-stand.webp')
    expect(img).not.toHaveAttribute('srcset')
    expect(img).not.toHaveAttribute('sizes')
  })

  it('defers loading the artwork so it never blocks first paint', () => {
    renderDiagram()
    expect(image()).toHaveAttribute('loading', 'lazy')
  })

  it('exposes the title and caption to the reader', () => {
    renderDiagram()
    expect(screen.getByText(/The integrated route, end to end/)).toBeInTheDocument()
    expect(screen.getByText(/Iron ore enters on the left/)).toBeInTheDocument()
  })

  it('declares a help topic so the Help Assistant can explain the diagram', () => {
    const { container } = { container: document.body }
    renderDiagram()
    const figure = container.querySelector('[data-help="website.processDiagram"]')
    expect(figure).not.toBeNull()
    expect(figure).toHaveAttribute('data-help-label', PROPS.title)
  })

  it('hides itself when the asset cannot be served instead of showing a broken image', () => {
    renderDiagram()
    fireEvent.error(image())
    expect(screen.queryByAltText(PROPS.alt)).not.toBeInTheDocument()
  })

  it('opens a lightbox when the figure is clicked', () => {
    renderDiagram()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: new RegExp(PROPS.title, 'i') }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('starts the lightbox at 100 % with zoom-out and reset disabled', () => {
    renderDiagram()
    fireEvent.click(screen.getByRole('button', { name: new RegExp(PROPS.title, 'i') }))
    const dialog = within(screen.getByRole('dialog'))

    expect(dialog.getByText('100%')).toBeInTheDocument()
    expect(dialog.getByRole('button', { name: /zoom out/i })).toBeDisabled()
    expect(dialog.getByRole('button', { name: /reset zoom/i })).toBeDisabled()
    expect(dialog.getByRole('button', { name: /zoom in/i })).toBeEnabled()
  })

  it('magnifies and restores the artwork, clamped to 400 %', () => {
    renderDiagram()
    fireEvent.click(screen.getByRole('button', { name: new RegExp(PROPS.title, 'i') }))
    const dialog = within(screen.getByRole('dialog'))
    const zoomIn = dialog.getByRole('button', { name: /zoom in/i })

    fireEvent.click(zoomIn)
    expect(dialog.getByText('150%')).toBeInTheDocument()

    for (let i = 0; i < 10; i += 1) fireEvent.click(zoomIn)
    expect(dialog.getByText('400%')).toBeInTheDocument()
    expect(zoomIn).toBeDisabled()

    fireEvent.click(dialog.getByRole('button', { name: /reset zoom/i }))
    expect(dialog.getByText('100%')).toBeInTheDocument()
  })

  it('resets the zoom level when the lightbox is reopened', () => {
    renderDiagram()
    const figure = screen.getByRole('button', { name: new RegExp(PROPS.title, 'i') })

    fireEvent.click(figure)
    let dialog = within(screen.getByRole('dialog'))
    fireEvent.click(dialog.getByRole('button', { name: /zoom in/i }))
    expect(dialog.getByText('150%')).toBeInTheDocument()
    fireEvent.click(dialog.getByRole('button', { name: /close the diagram/i }))

    fireEvent.click(figure)
    dialog = within(screen.getByRole('dialog'))
    expect(dialog.getByText('100%')).toBeInTheDocument()
  })

  it('keeps the lightbox chrome out of the Help Assistant click interception', () => {
    renderDiagram()
    fireEvent.click(screen.getByRole('button', { name: new RegExp(PROPS.title, 'i') }))
    // The assistant exempts a subtree via closest('[data-help-surface]'), so
    // the marker on the dialog root covers every control inside it.
    expect(screen.getByRole('dialog').closest('[data-help-surface]')).not.toBeNull()
  })
})
