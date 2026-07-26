import { describe, expect, it, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor, within, act } from '@testing-library/react'
import {
  renderWithProviders,
  testAnalyticsValue,
  testShellContext,
} from '../../test/renderWithProviders'
import { SimulatorControls } from '../devices/SimulatorControls'
import { IncidentPanel } from '../devices/IncidentPanel'
import { DeviceClient } from '../../api/deviceClient'
import {
  fixtureSensors,
  fixtureSimulatorStatus,
  INCIDENT_CATALOG,
} from '../../api/deviceFixtures'
import { createTranslator } from '../../i18n/messages'
import { DEVICE_MESSAGE_KEYS } from '../devices/deviceFormat'
import type { SimulatorStatus } from '../../api/deviceDomain'
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

function stubDeviceClient(
  overrides: Partial<Record<string, unknown>> = {},
): DeviceClient {
  return {
    isOffline: false,
    getDevices: vi.fn(async () => makeLoaded([])),
    getDevice: vi.fn(async () => makeLoaded(null)),
    getSensors: vi.fn(async () => makeLoaded(fixtureSensors())),
    getSeries: vi.fn(async () => makeLoaded(null)),
    getSimulator: vi.fn(async () => makeLoaded(fixtureSimulatorStatus())),
    sendCommand: vi.fn(async () => fixtureSimulatorStatus()),
    triggerIncident: vi.fn(async () => ({
      incident: {} as never,
      simulator: fixtureSimulatorStatus(),
    })),
    clearIncident: vi.fn(async () => undefined),
    ...overrides,
  } as unknown as DeviceClient
}

function makeValue(
  dcOverrides: Partial<Record<string, unknown>> = {},
  canOverride?: (action: string) => boolean,
) {
  const dc = stubDeviceClient(dcOverrides)
  const context = testShellContext()
  const t = makeTestT(context.locale)
  return {
    dc,
    value: testAnalyticsValue({
      deviceClient: dc,
      t,
      ...(canOverride !== undefined ? { can: canOverride } : {}),
    } as never),
  }
}

function renderControls(
  status: SimulatorStatus,
  dcOverrides: Partial<Record<string, unknown>> = {},
  canOverride?: (action: string) => boolean,
) {
  const { dc, value } = makeValue(dcOverrides, canOverride)
  const onReload = vi.fn()
  renderWithProviders(<SimulatorControls status={status} onReload={onReload} />, value)
  return { dc, onReload }
}

function renderIncidents(
  status: SimulatorStatus,
  dcOverrides: Partial<Record<string, unknown>> = {},
  canOverride?: (action: string) => boolean,
) {
  const { dc, value } = makeValue(dcOverrides, canOverride)
  const onReload = vi.fn()
  renderWithProviders(<IncidentPanel status={status} onReload={onReload} />, value)
  return { dc, onReload }
}

/* ─── SimulatorControls — button state matrix ─── */

describe('SimulatorControls – button state matrix', () => {
  it('when stopped: Start enabled; Pause, Resume, Stop disabled; Reset enabled', () => {
    renderControls(fixtureSimulatorStatus({ state: 'stopped' }))

    expect(screen.getByRole('button', { name: 'Start' })).not.toBeDisabled()
    expect(screen.getByRole('button', { name: 'Pause' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Resume' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Stop' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Reset' })).not.toBeDisabled()
  })

  it('when running: Pause and Stop enabled; Start, Resume, Reset disabled', () => {
    renderControls(fixtureSimulatorStatus({ state: 'running' }))

    expect(screen.getByRole('button', { name: 'Start' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Pause' })).not.toBeDisabled()
    expect(screen.getByRole('button', { name: 'Resume' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Stop' })).not.toBeDisabled()
    expect(screen.getByRole('button', { name: 'Reset' })).toBeDisabled()
  })

  it('when paused: Resume and Stop enabled; Start, Pause, Reset disabled', () => {
    renderControls(fixtureSimulatorStatus({ state: 'paused' }))

    expect(screen.getByRole('button', { name: 'Start' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Pause' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Resume' })).not.toBeDisabled()
    expect(screen.getByRole('button', { name: 'Stop' })).not.toBeDisabled()
    expect(screen.getByRole('button', { name: 'Reset' })).toBeDisabled()
  })
})

/* ─── SimulatorControls — command calls ─── */

describe('SimulatorControls – command dispatch', () => {
  it('clicking Start calls sendCommand with command: start', async () => {
    const sendCommand = vi.fn(async () => fixtureSimulatorStatus({ state: 'running' }))
    const { onReload } = renderControls(
      fixtureSimulatorStatus({ state: 'stopped' }),
      { sendCommand },
    )

    fireEvent.click(screen.getByRole('button', { name: 'Start' }))

    await waitFor(() => {
      expect(sendCommand).toHaveBeenCalledWith(
        expect.objectContaining({ command: 'start' }),
      )
    })
    await waitFor(() => expect(onReload).toHaveBeenCalled())
  })

  it('clicking Pause calls sendCommand with command: pause', async () => {
    const sendCommand = vi.fn(async () => fixtureSimulatorStatus({ state: 'paused' }))
    const { onReload } = renderControls(
      fixtureSimulatorStatus({ state: 'running' }),
      { sendCommand },
    )

    fireEvent.click(screen.getByRole('button', { name: 'Pause' }))

    await waitFor(() => {
      expect(sendCommand).toHaveBeenCalledWith(expect.objectContaining({ command: 'pause' }))
    })
    await waitFor(() => expect(onReload).toHaveBeenCalled())
  })

  it('clicking Resume calls sendCommand with command: resume', async () => {
    const sendCommand = vi.fn(async () => fixtureSimulatorStatus({ state: 'running' }))
    const { onReload } = renderControls(
      fixtureSimulatorStatus({ state: 'paused' }),
      { sendCommand },
    )

    fireEvent.click(screen.getByRole('button', { name: 'Resume' }))

    await waitFor(() => {
      expect(sendCommand).toHaveBeenCalledWith(expect.objectContaining({ command: 'resume' }))
    })
    await waitFor(() => expect(onReload).toHaveBeenCalled())
  })

  it('clicking Stop calls sendCommand with command: stop', async () => {
    const sendCommand = vi.fn(async () => fixtureSimulatorStatus({ state: 'stopped' }))
    const { onReload } = renderControls(
      fixtureSimulatorStatus({ state: 'running' }),
      { sendCommand },
    )

    fireEvent.click(screen.getByRole('button', { name: 'Stop' }))

    await waitFor(() => {
      expect(sendCommand).toHaveBeenCalledWith(expect.objectContaining({ command: 'stop' }))
    })
    await waitFor(() => expect(onReload).toHaveBeenCalled())
  })

  it('offline write (sendCommand throws) shows an error Alert', async () => {
    const sendCommand = vi.fn(async () => {
      throw new Error('Simulator control is unavailable while the dashboard runs on fixtures.')
    })
    renderControls(fixtureSimulatorStatus({ state: 'stopped' }), { sendCommand })

    fireEvent.click(screen.getByRole('button', { name: 'Start' }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('unavailable')
  })

  it('no platform.capacity.manage permission disables all command buttons', () => {
    renderControls(
      fixtureSimulatorStatus({ state: 'stopped' }),
      {},
      () => false, // can() returns false for all actions
    )

    expect(screen.getByRole('button', { name: 'Start' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Reset' })).toBeDisabled()
  })

  it('shows permission hint text when lacking manage permission', () => {
    renderControls(
      fixtureSimulatorStatus({ state: 'stopped' }),
      {},
      () => false,
    )

    expect(
      screen.getByText(DEVICE_MESSAGE_KEYS['device.simulator.permissionHint']!),
    ).toBeInTheDocument()
  })
})

/* ─── IncidentPanel — incident triggering ─── */

describe('IncidentPanel – incident triggering', () => {
  it('trigger button calls triggerIncident for a specific incident', async () => {
    const triggerIncident = vi.fn(async () => ({
      incident: {} as never,
      simulator: fixtureSimulatorStatus(),
    }))
    const { onReload } = renderIncidents(
      fixtureSimulatorStatus({ state: 'running' }),
      { triggerIncident },
    )

    // "Degrading furnace lining" is a specific incident (has targetDeviceIds)
    const triggerBtn = screen.getByRole('button', {
      name: /trigger degrading furnace lining/i,
    })
    fireEvent.click(triggerBtn)

    await waitFor(() => {
      expect(triggerIncident).toHaveBeenCalledWith(
        expect.objectContaining({
          incidentId: 'degrading-furnace',
          deviceId: 'LUX-BF-01',
        }),
      )
    })
    await waitFor(() => expect(onReload).toHaveBeenCalled())
  })

  it('trigger for a generic incident opens a dialog for target selection', async () => {
    const getSensors = vi.fn(async () => makeLoaded(fixtureSensors()))
    renderIncidents(
      fixtureSimulatorStatus({ state: 'running' }),
      { getSensors },
    )

    // "Sensor drift" is a generic incident (empty targetDeviceIds)
    const triggerBtn = screen.getByRole('button', { name: /trigger sensor drift/i })
    fireEvent.click(triggerBtn)

    // Dialog should open
    const dialog = await screen.findByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(dialog).toHaveTextContent('Sensor drift')
  })

  it('generic incident dialog requires device selection before confirming', async () => {
    const getSensors = vi.fn(async () => makeLoaded(fixtureSensors()))
    renderIncidents(fixtureSimulatorStatus({ state: 'running' }), { getSensors })

    fireEvent.click(screen.getByRole('button', { name: /trigger sensor drift/i }))
    await screen.findByRole('dialog')

    // The confirm button is disabled until a device is selected
    const confirmBtn = screen.getByRole('button', { name: 'Trigger' })
    expect(confirmBtn).toBeDisabled()
  })

  it('selecting a device in the dialog enables the confirm button', async () => {
    const getSensors = vi.fn(async () => makeLoaded(fixtureSensors()))
    renderIncidents(fixtureSimulatorStatus({ state: 'running' }), { getSensors })

    fireEvent.click(screen.getByRole('button', { name: /trigger sensor drift/i }))
    await screen.findByRole('dialog')

    // Open target device dropdown
    const deviceSelect = screen.getByRole('combobox', { name: 'Target device' })
    fireEvent.mouseDown(deviceSelect)
    const deviceOption = await screen.findByRole('option', { name: 'LUX-BF-01' })
    fireEvent.click(deviceOption)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Trigger' })).not.toBeDisabled()
    })
  })

  it('confirming generic incident calls triggerIncident with the selected deviceId', async () => {
    const getSensors = vi.fn(async () => makeLoaded(fixtureSensors()))
    const triggerIncident = vi.fn(async () => ({
      incident: {} as never,
      simulator: fixtureSimulatorStatus(),
    }))
    const { onReload } = renderIncidents(
      fixtureSimulatorStatus({ state: 'running' }),
      { getSensors, triggerIncident },
    )

    fireEvent.click(screen.getByRole('button', { name: /trigger sensor drift/i }))
    await screen.findByRole('dialog')

    // Select target device
    const deviceSelect = screen.getByRole('combobox', { name: 'Target device' })
    fireEvent.mouseDown(deviceSelect)
    const deviceOption = await screen.findByRole('option', { name: 'LUX-BF-01' })
    fireEvent.click(deviceOption)

    // Confirm
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Trigger' })).not.toBeDisabled()
    })
    fireEvent.click(screen.getByRole('button', { name: 'Trigger' }))

    await waitFor(() => {
      expect(triggerIncident).toHaveBeenCalledWith(
        expect.objectContaining({
          incidentId: 'sensor-drift',
          deviceId: 'LUX-BF-01',
        }),
      )
    })
  })

  it('offline triggerIncident shows an error alert', async () => {
    const getSensors = vi.fn(async () => makeLoaded(fixtureSensors()))
    const triggerIncident = vi.fn(async () => {
      throw new Error('Incident injection is unavailable while the dashboard runs on fixtures.')
    })
    renderIncidents(
      fixtureSimulatorStatus({ state: 'running' }),
      { getSensors, triggerIncident },
    )

    // Trigger a specific (non-generic) incident so no dialog needed
    fireEvent.click(
      screen.getByRole('button', { name: /trigger degrading furnace lining/i }),
    )

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('unavailable')
  })

  it('clear button calls clearIncident with the correct activeIncidentId', async () => {
    const clearIncident = vi.fn(async () => undefined)
    const activeIncident = {
      activeIncidentId: 'active-001',
      incidentId: 'degrading-furnace',
      label: 'Degrading furnace lining',
      severity: 'high' as const,
      deviceId: 'LUX-BF-01',
      sensorId: null,
      startedAt: '2026-07-25T18:00:00Z',
      endsAt: '2026-07-25T18:30:00Z',
      remainingMinutes: 15,
      progress: 0.5,
    }
    const statusWithIncident = fixtureSimulatorStatus(
      { state: 'running' },
      [activeIncident],
    )
    const { onReload } = renderIncidents(statusWithIncident, { clearIncident })

    const clearBtn = screen.getByRole('button', {
      name: /clear degrading furnace lining/i,
    })
    fireEvent.click(clearBtn)

    await waitFor(() => {
      expect(clearIncident).toHaveBeenCalledWith('active-001')
    })
    await waitFor(() => expect(onReload).toHaveBeenCalled())
  })

  it('no permission disables Trigger buttons on the catalog', () => {
    renderIncidents(
      fixtureSimulatorStatus({ state: 'running' }),
      {},
      () => false,
    )

    const triggerBtns = screen.getAllByRole('button', { name: /trigger/i })
    for (const btn of triggerBtns) {
      expect(btn).toBeDisabled()
    }
  })
})
