import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { renderWithProviders, testAnalyticsValue } from '../../test/renderWithProviders'
import { ProofOfExecution } from './ProofOfExecution'
import { screenRegistry } from './screenRegistry'
import { personaSections } from '../../personaRoutes'
import {
  PROOF_BY_ID,
  PROOF_CATEGORY_ORDER,
  PROOF_REQUIREMENTS,
  proofCoverage,
} from '../../proof/proofCatalog'

describe('proof catalog', () => {
  it('covers all five use-case categories with unique reference IDs', () => {
    const ids = PROOF_REQUIREMENTS.map((requirement) => requirement.id)
    expect(new Set(ids).size).toBe(ids.length)
    for (const category of PROOF_CATEGORY_ORDER) {
      expect(
        PROOF_REQUIREMENTS.some((requirement) => requirement.category === category),
        `category ${category} has no requirement`,
      ).toBe(true)
    }
  })

  it('gives every requirement a statement, a rationale and at least one piece of evidence', () => {
    for (const requirement of PROOF_REQUIREMENTS) {
      expect(requirement.statement.length, requirement.id).toBeGreaterThan(10)
      expect(requirement.howMet.length, requirement.id).toBeGreaterThan(20)
      expect(requirement.evidence.length, requirement.id).toBeGreaterThan(0)
    }
  })

  it('requires an explicit caveat wherever the demo is a surrogate', () => {
    for (const requirement of PROOF_REQUIREMENTS) {
      if (requirement.status !== 'met') {
        expect(requirement.caveat, `${requirement.id} must state its caveat`).toBeTruthy()
      }
    }
  })

  it('only deep-links to routes that a screen is registered for', () => {
    const routes = new Set<string>()
    for (const requirement of PROOF_REQUIREMENTS) {
      if (requirement.primaryRoute) routes.add(requirement.primaryRoute)
      for (const entry of requirement.evidence) {
        if (entry.route) routes.add(entry.route)
      }
    }
    expect(routes.size).toBeGreaterThan(0)
    for (const route of routes) {
      expect(screenRegistry[route], `no screen registered for "${route}"`).toBeTruthy()
    }
  })

  it('is reachable through its own registered route and persona section', () => {
    expect(screenRegistry['proof-of-execution/requirements']).toBe(ProofOfExecution)
    const section = personaSections.find((entry) => entry.section === 'proof-of-execution')
    expect(section).toBeTruthy()
    expect(section?.tabs.some((tab) => tab.slug === section.defaultSubView)).toBe(true)
  })

  it('indexes every requirement by ID', () => {
    for (const requirement of PROOF_REQUIREMENTS) {
      expect(PROOF_BY_ID[requirement.id]).toBe(requirement)
    }
  })

  it('computes coverage as met over total', () => {
    const coverage = proofCoverage()
    expect(coverage.total).toBe(PROOF_REQUIREMENTS.length)
    expect(coverage.met + coverage.partial + coverage.demo).toBe(coverage.total)
    expect(coverage.coveragePct).toBeCloseTo((coverage.met / coverage.total) * 100, 1)
  })
})

describe('ProofOfExecution screen', () => {
  it('lists the requirement register with reference IDs', async () => {
    renderWithProviders(<ProofOfExecution />)
    await waitFor(() => {
      expect(screen.getAllByText('REG-01').length).toBeGreaterThan(0)
      expect(screen.getAllByText('AI-03').length).toBeGreaterThan(0)
    })
  })

  it('narrows the register when a category filter is applied', async () => {
    renderWithProviders(<ProofOfExecution />)
    const table = await screen.findByRole('table')

    const before = within(table).getAllByRole('row').length
    fireEvent.click(screen.getByText(/Regulatory context \(3\)/))

    await waitFor(() => {
      const after = within(screen.getByRole('table')).getAllByRole('row').length
      expect(after).toBeLessThan(before)
    })
    expect(within(screen.getByRole('table')).queryByText('AI-03')).toBeNull()
  })

  it('shows the caveat for a surrogate outcome when its row is selected', async () => {
    renderWithProviders(<ProofOfExecution />)
    const table = await screen.findByRole('table')
    fireEvent.click(within(table).getByText('OUT-02'))

    await waitFor(() => {
      expect(screen.getByText(/Honest caveat/i)).toBeTruthy()
      expect(screen.getByText(/single-digit CO2 reduction/i)).toBeTruthy()
    })
  })

  it('emits a navigation intent when the proving screen is opened', async () => {
    const emit = vi.fn()
    renderWithProviders(<ProofOfExecution />, testAnalyticsValue({ emit }))

    const open = await screen.findByRole('button', { name: /Open the screen/i })
    fireEvent.click(open)

    expect(emit).toHaveBeenCalledWith(
      'nav.intent',
      expect.objectContaining({ route: expect.stringContaining(PROOF_REQUIREMENTS[0].primaryRoute as string) }),
    )
  })
})
