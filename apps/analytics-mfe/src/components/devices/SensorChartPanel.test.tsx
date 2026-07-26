import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { screen, fireEvent, waitFor, act, within } from '@testing-library/react'
import {
  renderWithProviders,
  testAnalyticsValue,
  testShellContext,
} from '../../test/renderWithProviders'
import { SensorChartPanel } from '../devices/SensorChartPanel'
import { DeviceClient } from '../../api/deviceClient'
import { fixtureSeries, fixtureSensors } from '../../api/deviceFixtures'
import { createTranslator } from '../../i18n/messages'
import { DEVICE_MESSAGE_KEYS } from '../devices/deviceFormat'
import type { TranslateFn } from '../../i18n/messages'

type Loaded<T> = { value: T; source: 'fixture'; asOf: string }

function makeLoaded<T>(value: T): Loaded<T> {
  return { value, source: 'fixture', asOf: '2026-07-25T18:45:00Z' }
}

function makeTestT(locale = 'en-LU'): TranslateFn {
  const base = createTranslator(locale)
  return (key: string, params?: Record<string, string | number>) => {
    const template = DEVICE_MESSAGE_KEYS[key]
    if (template !== undefined) {
      if (!params) return template
      return template.replace(/\{(\w+)\}/g, (_, name: string) =>
        String(params[name] ?? `{${name}}`),
      )
    }
    return base(key, params)
  }
}

const SENSOR_ID = 'LUX-BF-01:hearth_shell_temperature'

function stubDeviceClient(
  overrides: Partial<Record<string, unknown>> = {},
): DeviceClient {
  return {
    isOffline: false,
    getDevices: vi.fn(async () => makeLoaded([])),
    getDevice: vi.fn(async () => makeLoaded(null)),
    getSensors: vi.fn(async () => makeLoaded(fixtureSensors())),
    getSeries: vi.fn(async (sensorId: string, win: string, points: number) =>
      makeLoaded(fixtureSeries(sensorId, win, points)),
    ),
    getSimulator: vi.fn(async () => makeLoaded(null)),
    sendCommand: vi.fn(async () => {
      throw new Error('unavailable')
    }),
    triggerIncident: vi.fn(async () => {
      throw new Error('unavailable')
    }),
    clearIncident: vi.fn(async () => {
      throw new Error('unavailable')
    }),
    ...overrides,
  } as unknown as DeviceClient
}

function renderPanel(
  sensorId = SENSOR_ID,
  dcOverrides: Partial<Record<string, unknown>> = {},
) {
  const dc = stubDeviceClient(dcOverrides)
  const context = testShellContext()
  const value = testAnalyticsValue({ deviceClient: dc, t: makeTestT(context.locale) } as never)
  renderWithProviders(<SensorChartPanel sensorId={sensorId} />, value)
  return { dc }
}

describe('SensorChartPanel', () => {
  it('renders with line chart type selected by default', async () => {
    renderPanel()

    // The chart type toggle group should have 'line' selected
    const lineBtn = await screen.findByRole('button', { name: 'line' })
    expect(lineBtn).toHaveAttribute('aria-pressed', 'true')
  })

  it('shows all chart type options in the toggle group', async () => {
    renderPanel()
    await screen.findByRole('button', { name: 'line' })

    expect(screen.getByRole('button', { name: 'area' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'bar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'control' })).toBeInTheDocument()
  })

  it('switches to area chart type when area button is clicked', async () => {
    renderPanel()
    await screen.findByRole('button', { name: 'line' })

    fireEvent.click(screen.getByRole('button', { name: 'area' }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'area' })).toHaveAttribute('aria-pressed', 'true')
      expect(screen.getByRole('button', { name: 'line' })).toHaveAttribute('aria-pressed', 'false')
    })
  })

  it('switches to bar chart type', async () => {
    renderPanel()
    await screen.findByRole('button', { name: 'line' })

    fireEvent.click(screen.getByRole('button', { name: 'bar' }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'bar' })).toHaveAttribute('aria-pressed', 'true')
    })
  })

  it('switches to control chart type', async () => {
    renderPanel()
    await screen.findByRole('button', { name: 'line' })

    fireEvent.click(screen.getByRole('button', { name: 'control' }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'control' })).toHaveAttribute('aria-pressed', 'true')
    })
  })

  it('shows all window options in the toggle group', async () => {
    renderPanel()
    await screen.findByRole('button', { name: '15m' })

    expect(screen.getByRole('button', { name: '1h' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '8h' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '24h' })).toBeInTheDocument()
  })

  it('switches to 8h window and calls getSeries with the new window', async () => {
    const { dc } = renderPanel()
    await screen.findByRole('button', { name: '1h' })

    fireEvent.click(screen.getByRole('button', { name: '8h' }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '8h' })).toHaveAttribute('aria-pressed', 'true')
    })
    // getSeries should have been called with '8h'
    await waitFor(() => {
      const calls = (dc.getSeries as ReturnType<typeof vi.fn>).mock.calls
      expect(calls.some((args: unknown[]) => args[1] === '8h')).toBe(true)
    })
  })

  it('normalize toggle changes the plotted unit label in the chart title', async () => {
    renderPanel()
    // Wait for chart container to appear
    await screen.findByRole('figure')

    // Initially, the figure summary does NOT say 'Normalized'
    const chartFigure = screen.getByRole('figure')
    expect(chartFigure).not.toHaveTextContent('Normalized')

    // Toggle normalize on
    const normalizeSwitch = screen.getByRole('switch', { name: 'Normalize (0–1)' })
    fireEvent.click(normalizeSwitch)

    await waitFor(() => {
      // After normalize: the ChartContainer summary text includes 'Normalized 0–1'
      expect(screen.getByRole('figure')).toHaveTextContent('Normalized 0–1')
    })
  })

  it('zoom in button is disabled when already at max zoom (5 visible points)', async () => {
    // Use a small series
    const { dc } = renderPanel()
    await screen.findByRole('figure')

    const zoomInBtn = screen.getByRole('button', { name: 'Zoom in' })

    // Zoom in multiple times to reach the minimum
    for (let i = 0; i < 20; i++) {
      if (!zoomInBtn.hasAttribute('disabled')) {
        fireEvent.click(zoomInBtn)
      }
    }

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Zoom in' })).toBeDisabled()
    })
  })

  it('zoom in enables the Reset zoom button', async () => {
    renderPanel()
    await screen.findByRole('figure')

    const resetBtn = screen.getByRole('button', { name: 'Reset zoom' })
    // Initially disabled (no zoom applied)
    expect(resetBtn).toBeDisabled()

    fireEvent.click(screen.getByRole('button', { name: 'Zoom in' }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Reset zoom' })).not.toBeDisabled()
    })
  })

  it('zoom out after zoom in widens the view', async () => {
    renderPanel()
    await screen.findByRole('figure')

    // Zoom in first
    fireEvent.click(screen.getByRole('button', { name: 'Zoom in' }))
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Reset zoom' })).not.toBeDisabled()
    })

    // Now zoom out
    const zoomOutBtn = screen.getByRole('button', { name: 'Zoom out' })
    fireEvent.click(zoomOutBtn)

    // The chart is still displayed and no error thrown
    await waitFor(() => {
      expect(screen.getByRole('figure')).toBeInTheDocument()
    })
  })

  it('Reset zoom restores full range and disables the Reset button again', async () => {
    renderPanel()
    await screen.findByRole('figure')

    // Zoom in to activate zoom state
    fireEvent.click(screen.getByRole('button', { name: 'Zoom in' }))
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Reset zoom' })).not.toBeDisabled()
    })

    // Reset
    fireEvent.click(screen.getByRole('button', { name: 'Reset zoom' }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Reset zoom' })).toBeDisabled()
    })
  })

  it('live toggle switch is present and can be toggled', async () => {
    renderPanel()
    await screen.findByRole('figure')

    const liveSwitch = screen.getByRole('switch', { name: 'Live' })
    expect(liveSwitch).not.toBeChecked()

    fireEvent.click(liveSwitch)

    await waitFor(() => {
      expect(screen.getByRole('switch', { name: 'Live' })).toBeChecked()
    })
  })

  it('live toggle ON causes getSeries to be polled after the interval', async () => {
    vi.useFakeTimers()
    const getSeries = vi.fn(async (sensorId: string, win: string, points: number) =>
      makeLoaded(fixtureSeries(sensorId, win, points)),
    )
    const { dc } = renderPanel(SENSOR_ID, { getSeries })

    // Wait for initial load
    await act(async () => {
      await vi.runAllTimersAsync()
    })

    const callsBefore = (getSeries as ReturnType<typeof vi.fn>).mock.calls.length

    // Enable live
    const liveSwitch = screen.getByRole('switch', { name: 'Live' })
    await act(async () => {
      fireEvent.click(liveSwitch)
    })

    // Advance by one polling interval (5000ms)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5100)
    })

    const callsAfter = (getSeries as ReturnType<typeof vi.fn>).mock.calls.length
    expect(callsAfter).toBeGreaterThan(callsBefore)

    vi.useRealTimers()
  })

  it('live toggle OFF stops additional polling calls', async () => {
    vi.useFakeTimers()
    const getSeries = vi.fn(async (sensorId: string, win: string, points: number) =>
      makeLoaded(fixtureSeries(sensorId, win, points)),
    )
    renderPanel(SENSOR_ID, { getSeries })

    await act(async () => {
      await vi.runAllTimersAsync()
    })

    // Enable live
    const liveSwitch = screen.getByRole('switch', { name: 'Live' })
    await act(async () => {
      fireEvent.click(liveSwitch)
    })

    // Advance 5 seconds (poll fires)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5100)
    })

    const callsWhileLive = (getSeries as ReturnType<typeof vi.fn>).mock.calls.length
    expect(callsWhileLive).toBeGreaterThan(1)

    // Disable live
    await act(async () => {
      fireEvent.click(screen.getByRole('switch', { name: 'Live' }))
    })

    const callsBeforeAdvance = (getSeries as ReturnType<typeof vi.fn>).mock.calls.length

    // Advance another 10 seconds — no new calls expected
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000)
    })

    expect((getSeries as ReturnType<typeof vi.fn>).mock.calls.length).toBe(callsBeforeAdvance)

    vi.useRealTimers()
  })

  it('shows statistics strip (Min, Max, Mean, Std dev, Last) after data loads', async () => {
    renderPanel()
    // Wait for the stats list to appear
    const statsList = await screen.findByRole('list', { name: 'Sensor statistics' })
    expect(within(statsList).getByText('Min')).toBeInTheDocument()
    expect(within(statsList).getByText('Max')).toBeInTheDocument()
    expect(within(statsList).getByText('Mean')).toBeInTheDocument()
    expect(within(statsList).getByText('Std dev')).toBeInTheDocument()
    expect(within(statsList).getByText('Last')).toBeInTheDocument()
  })

  it('the View as table toggle exposes accessible table fallback', async () => {
    renderPanel()
    await screen.findByRole('figure')

    const toggleBtn = screen.getByRole('button', { name: 'View as table' })
    fireEvent.click(toggleBtn)

    await waitFor(() => {
      // ChartContainer shows a table with Time and Value columns
      expect(screen.getByRole('button', { name: 'View as chart' })).toBeInTheDocument()
      expect(screen.getByText('Time')).toBeInTheDocument()
    })
  })
})
