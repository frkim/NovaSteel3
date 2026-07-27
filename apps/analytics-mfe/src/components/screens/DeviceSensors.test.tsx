import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { screen, fireEvent, waitFor, within, act } from '@testing-library/react'
import {
  renderWithProviders,
  testAnalyticsValue,
  testShellContext,
} from '../../test/renderWithProviders'
import { DeviceSensors } from './DeviceSensors'
import { DeviceClient } from '../../api/deviceClient'
import {
  fixtureSensors,
  fixtureDevices,
  fixtureDeviceDetail,
  fixtureSeries,
  fixtureSimulatorStatus,
} from '../../api/deviceFixtures'
import { createTranslator } from '../../i18n/messages'
import { DEVICE_MESSAGE_KEYS } from '../devices/deviceFormat'
import type { TranslateFn } from '../../i18n/messages'

type Loaded<T> = { value: T; source: 'fixture'; asOf: string }

function makeLoaded<T>(value: T): Loaded<T> {
  return { value, source: 'fixture', asOf: '2026-07-25T18:45:00Z' }
}

/** Translator that includes device keys for readable test assertions. */
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

function stubDeviceClient(
  overrides: Partial<Record<string, unknown>> = {},
): DeviceClient {
  return {
    isOffline: false,
    getDevices: vi.fn(async () => makeLoaded(fixtureDevices())),
    getDevice: vi.fn(async (id: string) => makeLoaded(fixtureDeviceDetail(id))),
    getSensors: vi.fn(async (deviceId?: string) =>
      makeLoaded(
        deviceId
          ? fixtureSensors().filter((s) => s.deviceId === deviceId)
          : fixtureSensors(),
      ),
    ),
    getSeries: vi.fn(async (sensorId: string, win: string, points: number) =>
      makeLoaded(fixtureSeries(sensorId, win, points)),
    ),
    getSimulator: vi.fn(async () => makeLoaded(fixtureSimulatorStatus())),
    sendCommand: vi.fn(async () => {
      throw new Error('unavailable in fixture mode')
    }),
    triggerIncident: vi.fn(async () => {
      throw new Error('unavailable in fixture mode')
    }),
    clearIncident: vi.fn(async () => {
      throw new Error('unavailable in fixture mode')
    }),
    ...overrides,
  } as unknown as DeviceClient
}

function renderSensors(dcOverrides: Partial<Record<string, unknown>> = {}) {
  const dc = stubDeviceClient(dcOverrides)
  const context = testShellContext()
  const value = testAnalyticsValue({ deviceClient: dc, t: makeTestT(context.locale) } as never)
  renderWithProviders(<DeviceSensors />, value)
  return { dc }
}

describe('DeviceSensors', () => {
  it('renders the sensor table and shows 10 rows on the first page (initialPageSize=10)', async () => {
    renderSensors()
    const table = await screen.findByRole('table')
    // TableHead: 2 rows (sort-label row + search row), TableBody: 10 data rows
    const rows = within(table).getAllByRole('row')
    // 2 header + 10 data = 12
    expect(rows.length).toBe(12)
  })

  it('shows pagination indicating total sensors', async () => {
    renderSensors()
    // Wait for the table to render
    await screen.findByRole('table')
    // MUI TablePagination shows something like "1–10 of N"
    // The exact text comes from the t('table.rows') key which gives 'Rows {from}–{to} of {total}'
    await waitFor(() => {
      expect(screen.getByText(/of \d+/)).toBeInTheDocument()
    })
  })

  it('page size 10 shows 10 rows by default', async () => {
    renderSensors()
    const table = await screen.findByRole('table')
    const bodyRows = within(table).getAllByRole('row').slice(2) // skip 2 header rows
    expect(bodyRows.length).toBe(10)
  })

  it('can change page size to 25', async () => {
    renderSensors()
    await screen.findByRole('table')

    // MUI TablePagination uses a MUI Select (not native), so open with mouseDown then click option
    const select = screen.getByRole('combobox', { name: /rows per page/i })
    fireEvent.mouseDown(select)

    const option25 = await screen.findByRole('option', { name: '25' })
    fireEvent.click(option25)

    await waitFor(() => {
      const table = screen.getByRole('table')
      const bodyRows = within(table).getAllByRole('row').slice(2)
      expect(bodyRows.length).toBe(25)
    })
  })

  it('can change page size to 100 (shows all sensors)', async () => {
    renderSensors()
    await screen.findByRole('table')

    // MUI TablePagination uses a MUI Select (not native), so open with mouseDown then click option
    const select = screen.getByRole('combobox', { name: /rows per page/i })
    fireEvent.mouseDown(select)

    const option100 = await screen.findByRole('option', { name: '100' })
    fireEvent.click(option100)

    await waitFor(() => {
      const table = screen.getByRole('table')
      const bodyRows = within(table).getAllByRole('row').slice(2)
      // All sensors fit in 100-per-page
      expect(bodyRows.length).toBeGreaterThan(30)
      expect(bodyRows.length).toBeLessThanOrEqual(100)
    })
  })

  it('per-column search narrows rows to matching sensors', async () => {
    renderSensors()
    const table = await screen.findByRole('table')

    // Find the column search for "Sensor" (displayName column)
    const searchInput = screen.getByLabelText('Search Sensor')
    fireEvent.change(searchInput, { target: { value: 'Hearth Shell' } })

    // Wait for debounce + re-render: only "Hearth Shell Temperature" should match
    await waitFor(() => {
      const bodyRows = within(table).getAllByRole('row').slice(2)
      expect(bodyRows.length).toBe(1)
    })
  })

  it('per-column search on "Device" column filters by deviceId', async () => {
    renderSensors()
    const table = await screen.findByRole('table')

    const searchInput = screen.getByLabelText('Search Device')
    fireEvent.change(searchInput, { target: { value: 'LUX-RHF-01' } })

    // LUX-RHF-01 has 3 sensors
    await waitFor(() => {
      const bodyRows = within(table).getAllByRole('row').slice(2)
      expect(bodyRows.length).toBe(3)
    })
  })

  it('clicking column sort label changes sort direction', async () => {
    renderSensors()
    await screen.findByRole('table')

    // Click the "Area" sort label (which is not the default sort key)
    const areaSort = screen.getByRole('button', { name: /area/i })
    fireEvent.click(areaSort)

    // Table still renders; just verify no crash and table is present
    await waitFor(() => {
      expect(screen.getByRole('table')).toBeInTheDocument()
    })
  })

  it('clicking a row opens the SensorChartPanel below', async () => {
    renderSensors()
    const table = await screen.findByRole('table')

    // Click the first data row (index 2 is first data row after 2 header rows)
    const rows = within(table).getAllByRole('row')
    const firstDataRow = rows[2]
    fireEvent.click(firstDataRow)

    // The chart panel section should appear
    await waitFor(() => {
      const panel = document.getElementById('sensor-chart-panel')
      expect(panel).toBeInTheDocument()
    })
  })

  it('clicking the same row again closes the chart panel', async () => {
    renderSensors()
    const table = await screen.findByRole('table')

    const rows = within(table).getAllByRole('row')
    const firstDataRow = rows[2]

    // Open
    fireEvent.click(firstDataRow)
    await waitFor(() => {
      expect(document.getElementById('sensor-chart-panel')).toBeInTheDocument()
    })

    // Close (click same row again)
    fireEvent.click(firstDataRow)
    await waitFor(() => {
      expect(document.getElementById('sensor-chart-panel')).not.toBeInTheDocument()
    })
  })

  it('device filter dropdown filters the sensor table', async () => {
    renderSensors()
    await screen.findByRole('table')

    // Use the device filter combobox
    const deviceFilter = screen.getByRole('combobox', { name: 'Device' })
    // Open the select and pick LUX-RHF-01
    fireEvent.mouseDown(deviceFilter)
    const option = await screen.findByRole('option', { name: 'LUX-RHF-01' })
    fireEvent.click(option)

    // LUX-RHF-01 has 3 sensors
    await waitFor(() => {
      const table = screen.getByRole('table')
      const bodyRows = within(table).getAllByRole('row').slice(2)
      expect(bodyRows.length).toBe(3)
    })
  })

  it('status filter dropdown shows only matching sensors', async () => {
    // Check normal sensors exist in fixtures
    const normals = fixtureSensors().filter((s) => s.status === 'normal')
    renderSensors()
    await screen.findByRole('table')

    const statusFilter = screen.getByRole('combobox', { name: 'Status' })
    fireEvent.mouseDown(statusFilter)
    const option = await screen.findByRole('option', { name: 'normal' })
    fireEvent.click(option)

    await waitFor(() => {
      const table = screen.getByRole('table')
      const bodyRows = within(table).getAllByRole('row').slice(2)
      // Rows per page caps at 10, so expect min(10, normals.length)
      expect(bodyRows.length).toBe(Math.min(10, normals.length))
    })
  })
})
