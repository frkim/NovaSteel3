import type { ShellContext } from '../types'
import { demoHeaders, fixturesOnly, resolveBffBaseUrl, siteToPlant } from '../config'
import { HttpClient } from './httpClient'
import type { SingleEnvelope, TableEnvelope } from './envelope'
import type { DataSource } from './domain'
import type { Loaded } from './dataClient'
import type {
  ActiveIncident,
  DeviceDetail,
  DeviceRow,
  SensorRow,
  SensorSeries,
  SimulatorCommandRequest,
  SimulatorStatus,
  TriggerIncidentRequest,
} from './deviceDomain'
import * as deviceFixtures from './deviceFixtures'
import { fixtureAsOf } from '../utils/demoClock'

const FIXTURE_AS_OF = fixtureAsOf()
const FULL_PAGE = 200

function loaded<T>(value: T, source: DataSource, asOf: string): Loaded<T> {
  return { value, source, asOf }
}

/**
 * Client for the `/v1/devices/*` BFF surface (api-contracts §11).
 *
 * Read paths degrade to deterministic fixtures exactly like {@link DataClient},
 * so the Device Operations screens stay demonstrable if the BFF is unreachable.
 * Write paths (simulator commands, incident triggers) deliberately do NOT fall
 * back: silently pretending an incident was injected would misrepresent the
 * state of the plant, so failures surface to the caller.
 */
export class DeviceClient {
  private readonly http: HttpClient | null
  private readonly context: ShellContext

  constructor(context: ShellContext) {
    this.context = context
    this.http = fixturesOnly()
      ? null
      : new HttpClient({
          baseUrl: resolveBffBaseUrl(context),
          headers: demoHeaders(context),
        })
  }

  private get activePlant(): string {
    return siteToPlant(this.context.site)
  }

  get isOffline(): boolean {
    return this.http === null
  }

  private async single<T>(path: string, fallback: () => T): Promise<Loaded<T>> {
    if (!this.http) {
      return loaded(fallback(), 'fixture', FIXTURE_AS_OF)
    }
    try {
      const envelope: SingleEnvelope<T> = await this.http.getSingle<T>(path)
      return loaded(envelope.data, 'bff', envelope.asOf)
    } catch {
      return loaded(fallback(), 'fixture', FIXTURE_AS_OF)
    }
  }

  private async table<T>(path: string, fallback: () => T[]): Promise<Loaded<T[]>> {
    if (!this.http) {
      return loaded(fallback(), 'fixture', FIXTURE_AS_OF)
    }
    try {
      const envelope: TableEnvelope<T> = await this.http.getTable<T>(path)
      return loaded(envelope.items, 'bff', envelope.asOf)
    } catch {
      return loaded(fallback(), 'fixture', FIXTURE_AS_OF)
    }
  }

  getDevices(): Promise<Loaded<DeviceRow[]>> {
    return this.table<DeviceRow>(
      `/v1/devices?site=${encodeURIComponent(this.activePlant)}&size=${FULL_PAGE}`,
      deviceFixtures.fixtureDevices,
    )
  }

  getDevice(deviceId: string): Promise<Loaded<DeviceDetail | null>> {
    return this.single<DeviceDetail | null>(`/v1/devices/${encodeURIComponent(deviceId)}`, () =>
      deviceFixtures.fixtureDeviceDetail(deviceId),
    )
  }

  getSensors(deviceId?: string): Promise<Loaded<SensorRow[]>> {
    const params = new URLSearchParams({ site: this.activePlant, size: String(FULL_PAGE) })
    if (deviceId) {
      params.set('deviceId', deviceId)
    }
    return this.table<SensorRow>(`/v1/devices/sensors?${params.toString()}`, () => {
      const rows = deviceFixtures.fixtureSensors()
      return deviceId ? rows.filter((row) => row.deviceId === deviceId) : rows
    })
  }

  getSeries(sensorId: string, window: string, points = 120): Promise<Loaded<SensorSeries | null>> {
    const params = new URLSearchParams({ window, points: String(points) })
    return this.single<SensorSeries | null>(
      `/v1/devices/sensors/${encodeURIComponent(sensorId)}/series?${params.toString()}`,
      () => deviceFixtures.fixtureSeries(sensorId, window, points),
    )
  }

  getSimulator(): Promise<Loaded<SimulatorStatus>> {
    return this.single<SimulatorStatus>('/v1/devices/simulator', () =>
      deviceFixtures.fixtureSimulatorStatus(this.isOffline ? { state: 'stopped' } : {}),
    )
  }

  async sendCommand(request: SimulatorCommandRequest): Promise<SimulatorStatus> {
    if (!this.http) {
      throw new Error('Simulator control is unavailable while the dashboard runs on fixtures.')
    }
    const envelope = await this.http.post<SingleEnvelope<SimulatorStatus>>(
      '/v1/devices/simulator/commands',
      request,
    )
    return envelope.data
  }

  async triggerIncident(
    request: TriggerIncidentRequest,
  ): Promise<{ incident: ActiveIncident; simulator: SimulatorStatus }> {
    if (!this.http) {
      throw new Error('Incident injection is unavailable while the dashboard runs on fixtures.')
    }
    const envelope = await this.http.post<
      SingleEnvelope<{ incident: ActiveIncident; simulator: SimulatorStatus }>
    >('/v1/devices/incidents', request)
    return envelope.data
  }

  async clearIncident(activeIncidentId: string): Promise<void> {
    if (!this.http) {
      throw new Error('Incident control is unavailable while the dashboard runs on fixtures.')
    }
    await this.http.del(`/v1/devices/incidents/${encodeURIComponent(activeIncidentId)}`)
  }
}
