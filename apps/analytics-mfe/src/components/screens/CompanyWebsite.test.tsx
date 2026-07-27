import { describe, expect, it, vi } from 'vitest'
import { screen, fireEvent, waitFor, within } from '@testing-library/react'
import { renderWithProviders, testAnalyticsValue } from '../../test/renderWithProviders'
import { CompanyWebsiteHome } from './CompanyWebsiteHome'
import { CompanyWebsiteSteelKnowledge } from './CompanyWebsiteSteelKnowledge'

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderHome(emitOverride?: ReturnType<typeof vi.fn>) {
  const emit = emitOverride ?? vi.fn()
  const value = testAnalyticsValue({ emit })
  renderWithProviders(<CompanyWebsiteHome />, value)
  return { emit }
}

function renderSteelKnowledge() {
  const emit = vi.fn()
  const value = testAnalyticsValue({ emit })
  renderWithProviders(<CompanyWebsiteSteelKnowledge />, value)
  return { emit }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('CompanyWebsiteHome', () => {
  it('renders the main headline', async () => {
    renderHome()
    expect(await screen.findByRole('heading', { name: /engineering the future of steel/i })).toBeInTheDocument()
  })

  it('renders both CTA buttons', async () => {
    renderHome()
    // Primary CTA: "Discover AxelorMetal"
    expect(await screen.findByRole('button', { name: /discover axelormetal/i })).toBeInTheDocument()
    // Secondary CTA: "Explore our products"
    expect(screen.getByRole('button', { name: /explore our products/i })).toBeInTheDocument()
  })

  it('clicking Discover AxelorMetal emits the expected nav.intent route', async () => {
    const emit = vi.fn()
    renderHome(emit)

    const discoverBtn = await screen.findByRole('button', { name: /discover axelormetal/i })
    fireEvent.click(discoverBtn)

    expect(emit).toHaveBeenCalledWith('nav.intent', {
      route: expect.stringContaining('/company-website/company'),
    })
  })

  it('clicking Explore our products emits the expected nav.intent route', async () => {
    const emit = vi.fn()
    renderHome(emit)

    const productsBtn = await screen.findByRole('button', { name: /explore our products/i })
    fireEvent.click(productsBtn)

    expect(emit).toHaveBeenCalledWith('nav.intent', {
      route: expect.stringContaining('/company-website/products'),
    })
  })

  it('does not leak raw i18n key patterns into the DOM', async () => {
    renderHome()
    await screen.findByRole('heading', { name: /engineering the future of steel/i })
    // Raw keys look like "website.nav.home" — a string with a dot following "website"
    const bodyText = document.body.textContent ?? ''
    expect(bodyText).not.toMatch(/\bwebsite\.\w+/)
  })

  it('docks the page as a single, non-closable panel', async () => {
    renderHome()
    const tab = await screen.findByTestId('dock-tab-website-home')
    expect(tab).toHaveTextContent('AxelorMetal')
    // A marketing page has no detail panels to dismiss, so the tab shows no X.
    expect(tab.querySelector('.dv-default-tab-action')).toBeNull()
  })
})

describe('CompanyWebsiteSteelKnowledge — process diagrams', () => {
  it('illustrates both steelmaking routes plus the EAF deep dive', async () => {
    renderSteelKnowledge()
    await screen.findByRole('table', { name: /glossary/i })

    for (const stem of [
      'steel-route-blast-furnace',
      'steel-route-electric-arc-furnace',
      'eaf-process-detail',
    ]) {
      const img = document.querySelector(`img[src="/media/${stem}.webp"]`)
      expect(img, `${stem} diagram must be on the page`).not.toBeNull()
      // Informative artwork, so it must carry real alternative text.
      expect(img?.getAttribute('alt')?.length ?? 0).toBeGreaterThan(40)
    }
  })
})

describe('CompanyWebsiteSteelKnowledge — glossary', () => {
  it('renders the glossary table with all 10 rows visible', async () => {
    renderSteelKnowledge()
    const table = await screen.findByRole('table', { name: /glossary/i })
    // 2 header rows (sort row + search row) + 10 data rows = 12
    const rows = within(table).getAllByRole('row')
    expect(rows.length).toBe(12)
  })

  it('global search narrows the glossary to matching rows', async () => {
    renderSteelKnowledge()
    const table = await screen.findByRole('table', { name: /glossary/i })

    // The global search field has accessible label from t('table.search') = 'Search all columns'
    const searchField = screen.getByLabelText('Search all columns')
    fireEvent.change(searchField, { target: { value: 'blast furnace' } })

    // "Blast furnace" row (term) + "Pig iron (hot metal)" row (meaning mentions blast furnace)
    await waitFor(() => {
      const bodyRows = within(table).getAllByRole('row').slice(2)
      expect(bodyRows.length).toBeGreaterThanOrEqual(1)
      expect(bodyRows.length).toBeLessThan(10)
    })
  })

  it('does not leak raw i18n key patterns into the DOM', async () => {
    renderSteelKnowledge()
    await screen.findByRole('table', { name: /glossary/i })
    const bodyText = document.body.textContent ?? ''
    expect(bodyText).not.toMatch(/\bwebsite\.\w+/)
  })
})
