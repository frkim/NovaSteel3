import { existsSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { renderWithProviders, testAnalyticsValue } from '../../test/renderWithProviders'
import { UseCaseBrief } from './UseCaseBrief'
import { screenRegistry } from './screenRegistry'
import { personaSections } from '../../personaRoutes'
import {
  GITHUB_REPO_URL,
  PROOF_BY_ID,
  PROOF_REQUIREMENTS,
  githubUrlFor,
  resolveEvidencePath,
} from '../../proof/proofCatalog'

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../../../../..')

describe('evidence GitHub links', () => {
  it('expands every abbreviated service path to a file that exists in the repository', () => {
    const checked: string[] = []
    for (const requirement of PROOF_REQUIREMENTS) {
      for (const entry of requirement.evidence) {
        const path = resolveEvidencePath(entry)
        if (!path) continue
        expect(path, `${requirement.id}: "${entry.label}" was not expanded`).not.toContain('/.../')
        expect(existsSync(resolve(REPO_ROOT, path)), `${requirement.id}: ${path} does not exist`).toBe(true)
        checked.push(path)
      }
    }
    // Guard against the resolver silently returning `undefined` for everything.
    expect(checked.length).toBeGreaterThan(20)
  })

  it('links code, infra and doc evidence to the public repository', () => {
    const codeEvidence = PROOF_REQUIREMENTS.flatMap((requirement) => requirement.evidence).filter(
      (entry) => entry.kind === 'code',
    )
    expect(codeEvidence.length).toBeGreaterThan(0)
    for (const entry of codeEvidence) {
      const url = githubUrlFor(entry)
      expect(url, `no GitHub URL for "${entry.label}"`).toBeTruthy()
      expect(url).toMatch(new RegExp(`^${GITHUB_REPO_URL}/(blob|tree)/main/`))
    }
  })

  it('does not fabricate links for screens or HTTP routes', () => {
    const uiEvidence = PROOF_REQUIREMENTS.flatMap((requirement) => requirement.evidence).filter(
      (entry) => entry.kind === 'ui' || entry.kind === 'api',
    )
    for (const entry of uiEvidence) {
      if (entry.label.includes('/') && /\.(ts|tsx|py|cs|razor)$/.test(entry.label)) continue
      expect(githubUrlFor(entry), `unexpected link for "${entry.label}"`).toBeUndefined()
    }
  })

  it('renders the cited file as an external link in the evidence panel', async () => {
    const { ProofOfExecution } = await import('./ProofOfExecution')
    renderWithProviders(<ProofOfExecution />)
    const table = await screen.findByRole('table')
    fireEvent.click(within(table).getByText('REG-01'))

    await waitFor(() => {
      const link = screen.getByRole('link', { name: /erasure\.py/ })
      expect(link.getAttribute('href')).toBe(
        `${GITHUB_REPO_URL}/blob/main/services/knowledge-orchestrator/src/knowledge_orchestrator/erasure.py`,
      )
      expect(link.getAttribute('target')).toBe('_blank')
      expect(link.getAttribute('rel')).toContain('noopener')
    })
  })
})

describe('UseCaseBrief screen', () => {
  it('is registered as the second tab of the proof-of-execution section', () => {
    expect(screenRegistry['proof-of-execution/use-case']).toBe(UseCaseBrief)
    const section = personaSections.find((entry) => entry.section === 'proof-of-execution')
    expect(section?.tabs.map((tab) => tab.slug)).toContain('use-case')
  })

  it('reproduces the brief verbatim, including the measurable targets', async () => {
    renderWithProviders(<UseCaseBrief />)
    await waitFor(() => {
      expect(screen.getByText(/Heavy Industry & Metals/)).toBeTruthy()
      expect(screen.getByText(/represent 35% of total production cost/)).toBeTruthy()
      expect(screen.getByText('\u20ac8M per event')).toBeTruthy()
      expect(screen.getByText('21\u2011day advance warning')).toBeTruthy()
      expect(screen.getByText(/searchable procedure libraries/)).toBeTruthy()
    })
  })

  it('stamps every use-case statement with a resolvable proof reference', async () => {
    renderWithProviders(<UseCaseBrief />)
    await waitFor(() => expect(screen.getAllByText('CHL-01').length).toBeGreaterThan(0))
    for (const id of ['REG-01', 'CHL-03', 'OBJ-04', 'OUT-02', 'AI-03']) {
      expect(screen.getAllByText(id).length, `${id} badge missing`).toBeGreaterThan(0)
      expect(PROOF_BY_ID[id], `${id} not in catalog`).toBeTruthy()
    }
  })

  it('presents the whole brief as a single dock tab', async () => {
    renderWithProviders(<UseCaseBrief />)
    const tabs = await screen.findAllByTestId(/^dock-tab-/)
    expect(tabs.map((tab) => tab.getAttribute('data-testid'))).toEqual(['dock-tab-usecase-document'])
    // Every heading of the source Markdown reads inside that one tab.
    for (const heading of [
      'Industry profile',
      'Business challenge',
      'Transformation objective',
      'Expected outcomes',
      'AI infusion point',
    ]) {
      expect(screen.getByRole('heading', { name: heading }), `${heading} missing`).toBeTruthy()
    }
  })

  it('links back to the Markdown brief on GitHub', async () => {
    renderWithProviders(<UseCaseBrief />)
    const link = await screen.findByRole('link', { name: /docs\/usecase\/usecase\.md/ })
    expect(link.getAttribute('href')).toBe(`${GITHUB_REPO_URL}/blob/main/docs/usecase/usecase.md`)
  })

  it('navigates to the requirement register when a reference badge is used', async () => {
    const emit = vi.fn()
    renderWithProviders(<UseCaseBrief />, testAnalyticsValue({ emit }))
    const badges = await screen.findAllByText('OUT-01')
    fireEvent.click(badges[0]!)
    expect(emit).toHaveBeenCalledWith(
      'nav.intent',
      expect.objectContaining({ route: expect.stringContaining('proof-of-execution/requirements') }),
    )
  })
})
