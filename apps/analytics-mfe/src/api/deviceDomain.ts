/**
 * Device / sensor / simulator contract types (api-contracts §11).
 *
 * These mirror the frozen response shapes emitted by `services/device-simulator`
 * and proxied by the BFF under `/v1/devices/*`. Keys are camelCase on the wire,
 * so no mapping layer is needed: parse and use.
 */

export type DeviceStatus = 'healthy' | 'degraded' | 'fault' | 'offline'
export type SensorStatus = 'normal' | 'warning' | 'alarm' | 'stale'
export type SensorQuality = 'good' | 'uncertain' | 'bad'
export type SensorTrend = 'rising' | 'falling' | 'flat'
export type SimulatorState = 'stopped' | 'running' | 'paused'
export type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical'

export interface DeviceRow {
  deviceId: string
  site: string
  area: string
  description: string
  status: DeviceStatus
  sensorCount: number
  activeIncidents: string[]
  lastSampleAt: string | null
  healthScore: number
  uptimePct: number
}

export interface SensorRow {
  sensorId: string
  deviceId: string
  signalCode: string
  displayName: string
  area: string
  unit: string
  low: number
  high: number
  samplePeriodMs: number
  value: number | null
  quality: SensorQuality
  status: SensorStatus
  trend: SensorTrend
  deviationPct: number
  clamped: boolean
  lastSampleAt: string | null
}

export interface DeviceDetail extends DeviceRow {
  sensors: SensorRow[]
}

export interface SeriesPoint {
  t: string
  v: number
  q: string
}

export interface NormalizedPoint {
  t: string
  v: number
}

export interface SeriesStats {
  min: number
  max: number
  mean: number
  stdDev: number
  last: number
}

export interface SensorSeries {
  sensorId: string
  deviceId: string
  displayName: string
  unit: string
  low: number
  high: number
  window: string
  pointCount: number
  points: SeriesPoint[]
  normalizedPoints: NormalizedPoint[]
  stats: SeriesStats
}

export interface IncidentCatalogEntry {
  incidentId: string
  label: string
  description: string
  severity: IncidentSeverity
  defaultDurationMinutes: number
  targetDeviceIds: string[]
  affectedSignalCodes: string[]
}

export interface ActiveIncident {
  activeIncidentId: string
  incidentId: string
  label: string
  severity: IncidentSeverity
  deviceId: string
  sensorId: string | null
  startedAt: string
  endsAt: string
  remainingMinutes: number
  progress: number
}

export interface SimulatorStatus {
  state: SimulatorState
  scenario: string
  seed: number
  speedFactor: number
  tickIntervalSeconds: number
  simulatedClock: string
  elapsedHours: number
  tickCount: number
  deviceCount: number
  sensorCount: number
  activeIncidents: ActiveIncident[]
  availableScenarios: string[]
  availableIncidents: IncidentCatalogEntry[]
  startedAt: string | null
}

export type SimulatorCommand =
  | 'start'
  | 'pause'
  | 'resume'
  | 'stop'
  | 'reset'
  | 'set-speed'
  | 'set-scenario'

export interface SimulatorCommandRequest {
  command: SimulatorCommand
  scenario?: string
  speedFactor?: number
  seed?: number
}

export interface TriggerIncidentRequest {
  incidentId: string
  deviceId?: string
  sensorId?: string
  durationMinutes?: number
}

/** Time windows the series endpoint accepts, shortest first. */
export const SERIES_WINDOWS = ['15m', '1h', '8h', '24h'] as const
export type SeriesWindow = (typeof SERIES_WINDOWS)[number]

/** Chart renderings offered by the linked sensor chart (UX §9.7). */
export const SENSOR_CHART_TYPES = ['line', 'area', 'bar', 'control'] as const
export type SensorChartType = (typeof SENSOR_CHART_TYPES)[number]

export const SIMULATOR_SPEEDS = [1, 2, 5, 10, 30] as const
