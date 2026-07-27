import { existsSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { renderWithProviders, testAnalyticsValue } from '../../test/renderWithProviders'
import { TechnicalRequirements } from './TechnicalRequirements'
import { screenRegistry } from './screenRegistry'
import { personaSections } from '../../personaRoutes'
import { GITHUB_REPO_URL, resolveEvidencePath } from '../../proof/proofCatalog'
import {
  TECH_BY_ID,
  TECH_CATEGORY_ORDER,
  TECH_MAX_SCORE,
  TECH_REQUIREMENTS,
  gradeFor,
  techScorecard,
} from '../../proof/technicalCatalog'

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../../../../..')

describe('technical rating-grid catalog', () => {
  it('answers all twelve rubric criteria across all seven categories', () => {
    expect(TECH_REQUIREMENTS).toHaveLength(12)
    expect(TECH_MAX_SCORE).toBe(60)
    const ids = TECH_REQUIREMENTS.map((requirement) => requirement.id)
    expect(new Set(ids).size).toBe(ids.length)
    for (const category of TECH_CATEGORY_ORDER) {
      expect(
        TECH_REQUIREMENTS.some((requirement) => requirement.category === category),
        `category ${category} has no criterion`,
      ).toBe(true)
    }
  })

  it('requires an explicit gap and uplift wherever the score is below five', () => {
    for (const requirement of TECH_REQUIREMENTS) {
      if (requirement.score < 5) {
        expect(requirement.gap, `${requirement.id} must state its gap`).toBeTruthy()
        expect(requirement.uplift, `${requirement.id} must state its uplift`).toBeTruthy()
      }
    }
  })

  it('gives every criterion a verdict, a rationale and evidence', () => {
    for (const requirement of TECH_REQUIREMENTS) {
      expect(requirement.verdict.length, requirement.id).toBeGreaterThan(10)
      expect(requirement.howMet.length, requirement.id).toBeGreaterThan(50)
      expect(requirement.excellentBar.length, requirement.id).toBeGreaterThan(10)
      expect(requirement.evidence.length, requirement.id).toBeGreaterThan(2)
    }
  })

  it('cites only files that actually exist in the repository', () => {
    let checked = 0
    for (const requirement of TECH_REQUIREMENTS) {
      for (const entry of requirement.evidence) {
        const path = resolveEvidencePath(entry)
        if (!path) continue
        expect(path, `${requirement.id}: "${entry.label}" was not expanded`).not.toContain('/.../')
        expect(existsSync(resolve(REPO_ROOT, path)), `${requirement.id}: ${path} does not exist`).toBe(true)
        checked += 1
      }
    }
    expect(checked).toBeGreaterThan(50)
  })

  it('only deep-links to routes that a screen is registered for', () => {
    const routes = new Set<string>()
    for (const requirement of TECH_REQUIREMENTS) {
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

  it('scores 56 of 60, placing the solution in grade band A', () => {
    const scorecard = techScorecard()
    expect(scorecard.max).toBe(TECH_MAX_SCORE)
    expect(scorecard.total).toBe(56)
    expect(scorecard.grade).toBe('A')
    expect(scorecard.criteria).toBe(12)
    expect(scorecard.byCategory.reduce((sum, row) => sum + row.score, 0)).toBe(scorecard.total)
    expect(scorecard.byCategory.reduce((sum, row) => sum + row.max, 0)).toBe(TECH_MAX_SCORE)
  })

  it('maps totals onto the rubric grade bands', () => {
    expect(gradeFor(60).grade).toBe('A')
    expect(gradeFor(54).grade).toBe('A')
    expect(gradeFor(53).grade).toBe('B')
    expect(gradeFor(48).grade).toBe('B')
    expect(gradeFor(47).grade).toBe('C')
    expect(gradeFor(40).grade).toBe('C')
    expect(gradeFor(39).grade).toBe('D/F')
    expect(gradeFor(0).grade).toBe('D/F')
  })

  it('indexes every criterion by ID', () => {
    for (const requirement of TECH_REQUIREMENTS) {
      expect(TECH_BY_ID[requirement.id]).toBe(requirement)
    }
  })
})

describe('TechnicalRequirements screen', () => {
  it('is reachable through its own registered route and persona section', () => {
    expect(screenRegistry['technical-requirements/criteria']).toBe(TechnicalRequirements)
    const section = personaSections.find((entry) => entry.section === 'technical-requirements')
    expect(section).toBeTruthy()
    expect(section?.tabs.some((tab) => tab.slug === section.defaultSubView)).toBe(true)
  })

  it('lists the scorecard with every reference ID', async () => {
    renderWithProviders(<TechnicalRequirements />)
    await waitFor(() => {
      expect(screen.getAllByText('TR-DES-01').length).toBeGreaterThan(0)
      expect(screen.getAllByText('TR-PRE-01').length).toBeGreaterThan(0)
    })
  })

  it('narrows the scorecard when a category filter is applied', async () => {
    renderWithProviders(<TechnicalRequirements />)
    const table = await screen.findByRole('table')
    const before = within(table).getAllByRole('row').length

    fireEvent.click(screen.getByText(/^Design \(15\/15\)$/))

    await waitFor(() => {
      const after = within(screen.getByRole('table')).getAllByRole('row').length
      expect(after).toBeLessThan(before)
    })
    expect(within(screen.getByRole('table')).queryByText('TR-PRE-01')).toBeNull()
  })

  it('shows the gap and the uplift for a criterion scored below five', async () => {
    renderWithProviders(<TechnicalRequirements />)
    const table = await screen.findByRole('table')
    fireEvent.click(within(table).getByText('TR-AI-02'))

    await waitFor(() => {
      expect(screen.getByText(/What is missing/i)).toBeTruthy()
      expect(screen.getByText(/no model registry artefact/i)).toBeTruthy()
      expect(screen.getByText(/What would raise the score/i)).toBeTruthy()
      expect(screen.getByText(/MLflow registry/i)).toBeTruthy()
    })
  })

  it('links its evidence to the public repository', async () => {
    renderWithProviders(<TechnicalRequirements />)
    await waitFor(() => {
      const link = screen.getByRole('link', { name: /docs\/architecture\/solution-architecture\.md/ })
      expect(link.getAttribute('href')).toBe(
        `${GITHUB_REPO_URL}/blob/main/docs/architecture/solution-architecture.md`,
      )
      expect(link.getAttribute('target')).toBe('_blank')
    })
  })

  it('emits a navigation intent when the proving screen is opened', async () => {
    const emit = vi.fn()
    renderWithProviders(<TechnicalRequirements />, testAnalyticsValue({ emit }))

    const open = await screen.findByRole('button', { name: /Open the screen/i })
    fireEvent.click(open)

    expect(emit).toHaveBeenCalledWith(
      'nav.intent',
      expect.objectContaining({ route: expect.stringContaining(TECH_REQUIREMENTS[0].primaryRoute as string) }),
    )
  })
})
