import { describe, expect, it, vi, afterEach } from 'vitest'
import { act, screen } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { StateBoundary } from './StateBoundary'
import type { ResourceState } from '../../hooks/useResource'

function loadingState(): ResourceState<string[]> {
  return {
    status: 'loading',
    data: null,
    error: null,
    source: null,
    asOf: null,
    reload: vi.fn(),
    refreshing: false,
  }
}

describe('StateBoundary loading gauge', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows skeleton rows by default', () => {
    renderWithProviders(<StateBoundary state={loadingState()}>{() => <div />}</StateBoundary>)
    expect(screen.queryByRole('status')).toBeNull()
  })

  it('shows an animated gauge with a progress message when asked', () => {
    renderWithProviders(
      <StateBoundary state={loadingState()} loadingVariant="gauge" loadingCaption="Fetching device data">
        {() => <div />}
      </StateBoundary>,
    )

    const status = screen.getByRole('status')
    expect(status).toHaveAttribute('aria-busy', 'true')
    expect(screen.getByText('Loading in progress…')).toBeInTheDocument()
    expect(screen.getByText('Fetching device data')).toBeInTheDocument()
    expect(status.querySelectorAll('.MuiCircularProgress-root').length).toBe(2)
  })

  it('counts elapsed seconds while the load runs', () => {
    vi.useFakeTimers()
    renderWithProviders(
      <StateBoundary state={loadingState()} loadingVariant="gauge">
        {() => <div />}
      </StateBoundary>,
    )
    expect(screen.getByText('0s')).toBeInTheDocument()

    act(() => {
      vi.advanceTimersByTime(2000)
    })
    expect(screen.getByText('2s')).toBeInTheDocument()
  })
})
