import { describe, expect, it, vi } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import {
  renderWithProviders,
  testAnalyticsValue,
  testShellContext,
} from '../../test/renderWithProviders'
import { DeviceFleet } from './DeviceFleet'
import type { DeviceClient } from '../../api/deviceClient'
import {
  fixtureDevices,
  fixtureDeviceDetail,
  fixtureSensors,
  fixtureSeries,
  fixtureSimulatorStatus,
} from '../../api/deviceFixtures'
import { createTranslator, type TranslateFn } from '../../i18n/messages'
import { DEVICE_MESSAGE_KEYS } from '../devices/deviceFormat'

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

function stubDeviceClient(
  overrides: Partial<Record<string, unknown>> = {},
): DeviceClient {
  return {
    isOffline: false,
    getDevices: vi.fn(async () => makeLoaded(fixtureDevices())),
    getDevice: vi.fn(async (id: string) => makeLoaded(fixtureDeviceDetail(id))),
    getSensors: vi.fn(async () => makeLoaded(fixtureSensors())),
    getSeries: vi.fn(async (sensorId: string, win: string, points: number) =>
      makeLoaded(fixtureSeries(sensorId, win, points)),
    ),
    getSimulator: vi.fn(async () => makeLoaded(fixtureSimulatorStatus())),
    sendCommand: vi.fn(),
    triggerIncident: vi.fn(),
    clearIncident: vi.fn(),
    ...overrides,
  } as unknown as DeviceClient
}

function renderFleet(dcOverrides: Partial<Record<string, unknown>> = {}) {
  const dc = stubDeviceClient(dcOverrides)
  const context = testShellContext()
  const value = testAnalyticsValue({ deviceClient: dc, t: makeTestT(context.locale) } as never)
  renderWithProviders(<DeviceFleet />, value)
  return { dc }
}

function kpiBand() {
  return screen.getByRole('region', { name: 'Key performance indicators' })
}

async function findKpiBand() {
  return screen.findByRole('region', { name: 'Key performance indicators' })
}

describe('DeviceFleet KPI band', () => {
  it('shows placeholders instead of derived zeros while the first fetch is in flight', async () => {
    let release: (() => void) | undefined
    const pending = new Promise<void>((resolve) => {
      release = resolve
    })

    renderFleet({
      getDevices: vi.fn(async () => {
        await pending
        return makeLoaded(fixtureDevices())
      }),
    })

    const band = await findKpiBand()
    expect(band).toHaveAttribute('aria-busy', 'true')
    // No tile may claim a measured value (e.g. "0" devices or "0" mean health) yet.
    expect(band.textContent).not.toMatch(/\b0\b/)
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)

    release?.()

    await waitFor(() => {
      expect(kpiBand()).not.toHaveAttribute('aria-busy')
    })
  })

  it('shows the real counts once devices have loaded', async () => {
    const expected = fixtureDevices()
    renderFleet()

    await waitFor(() => {
      expect(kpiBand().textContent).toContain(String(expected.length))
    })
    expect(kpiBand()).not.toHaveAttribute('aria-busy')
  })
})
