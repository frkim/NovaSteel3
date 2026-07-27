/**
 * Deterministic device/sensor fixtures for offline fallback (UX §20).
 *
 * Mirrors the `services/device-simulator` catalog so the Device Operations
 * screens tell the same story with or without the BFF. Waveforms are a pure
 * function of (sensorId, tick) — no `Math.random`, so screenshots and the CDP
 * browser proof are byte-stable.
 */
import type {
  ActiveIncident,
  DeviceDetail,
  DeviceRow,
  IncidentCatalogEntry,
  SensorRow,
  SensorSeries,
  SeriesPoint,
  SimulatorStatus,
} from './deviceDomain'

export const DEVICE_FIXTURE_SITE = 'NS-DEMO-LUX-01'

const SITE_FOR_DEVICE: Record<string, string> = {
  LUX: 'NS-DEMO-LUX-01',
  DE: 'NS-DEMO-DE-01',
  BE: 'NS-DEMO-BE-01',
  ES: 'NS-DEMO-ES-01',
}

function siteOfDevice(deviceId: string): string {
  const prefix = deviceId.split('-')[0]
  return SITE_FOR_DEVICE[prefix] ?? DEVICE_FIXTURE_SITE
}

const CLOCK = '2026-07-25T18:45:00Z'
const CLOCK_MS = Date.parse(CLOCK)

interface CatalogDevice {
  deviceId: string
  area: string
  description: string
}

interface CatalogSignal {
  code: string
  unit: string
  low: number
  high: number
  periodMs: number
  deviceId: string
  extended: boolean
}

const DEVICES: CatalogDevice[] = [
  // LUX — Integrated steelworks
  { deviceId: 'LUX-BF-01', area: 'Ironmaking', description: 'Blast furnace' },
  { deviceId: 'LUX-BOF-01', area: 'Steelmaking', description: 'Basic oxygen furnace' },
  { deviceId: 'LUX-CC-01', area: 'Casting', description: 'Slab caster' },
  { deviceId: 'LUX-RHF-01', area: 'Rolling', description: 'Reheat furnace' },
  { deviceId: 'LUX-HSM-01', area: 'Rolling', description: 'Hot strip mill' },
  { deviceId: 'LUX-UTIL-01', area: 'Utilities', description: 'Energy system' },
  // DE — EAF steelmaking
  { deviceId: 'DE-EAF-01', area: 'Steelmaking', description: 'Electric arc furnace' },
  { deviceId: 'DE-LF-01', area: 'Steelmaking', description: 'Ladle furnace' },
  { deviceId: 'DE-BCM-01', area: 'Casting', description: 'Billet caster' },
  { deviceId: 'DE-UTIL-01', area: 'Utilities', description: 'Energy system' },
  // BE — Cold rolling and coating
  { deviceId: 'BE-CRM-01', area: 'Rolling', description: 'Cold rolling mill' },
  { deviceId: 'BE-GAL-01', area: 'Coating', description: 'Hot-dip galvanizing line' },
  { deviceId: 'BE-UTIL-01', area: 'Utilities', description: 'Energy system' },
  // ES — Mini-mill wire rod
  { deviceId: 'ES-EAF-01', area: 'Steelmaking', description: 'Electric arc furnace' },
  { deviceId: 'ES-WRM-01', area: 'Rolling', description: 'Wire rod mill' },
  { deviceId: 'ES-UTIL-01', area: 'Utilities', description: 'Energy system' },
]

function signal(
  code: string,
  unit: string,
  low: number,
  high: number,
  periodMs: number,
  deviceId: string,
  extended = false,
): CatalogSignal {
  return { code, unit, low, high, periodMs, deviceId, extended }
}

const SIGNALS: CatalogSignal[] = [
  // LUX-BF-01 (11)
  signal('hearth_shell_temperature', 'Cel', 75, 185, 5_000, 'LUX-BF-01'),
  signal('cooling_water_inlet_temperature', 'Cel', 20, 36, 5_000, 'LUX-BF-01'),
  signal('cooling_water_outlet_temperature', 'Cel', 28, 58, 5_000, 'LUX-BF-01'),
  signal('cooling_water_flow', 'm3/h', 110, 310, 5_000, 'LUX-BF-01'),
  signal('local_heat_flux', 'kW/m2', 35, 190, 5_000, 'LUX-BF-01'),
  signal('hearth_refractory_estimate', 'mm', 280, 950, 900_000, 'LUX-BF-01'),
  signal('hot_blast_temperature', 'Cel', 1050, 1250, 10_000, 'LUX-BF-01'),
  signal('top_pressure', 'bar', 1.4, 2.6, 1_000, 'LUX-BF-01'),
  signal('pulverized_coal_injection', 'kg/t', 100, 190, 60_000, 'LUX-BF-01'),
  signal('hot_metal_temperature', 'Cel', 1440, 1530, 0, 'LUX-BF-01'),
  signal('production_rate', 't/h', 180, 360, 60_000, 'LUX-BF-01'),
  // LUX-RHF-01 (3)
  signal('reheat_zone_temperature', 'Cel', 850, 1285, 2_000, 'LUX-RHF-01'),
  signal('furnace_gas_flow', 'm3/h', 4_000, 42_000, 2_000, 'LUX-RHF-01'),
  signal('furnace_excess_o2', '%', 0.8, 4.5, 2_000, 'LUX-RHF-01'),
  // LUX-HSM-01 (4)
  signal('stand_motor_current', 'A', 1_000, 12_000, 1_000, 'LUX-HSM-01'),
  signal('rolling_force', 'MW', 4, 38, 1_000, 'LUX-HSM-01'),
  signal('strip_speed', 'm/s', 0.2, 22, 1_000, 'LUX-HSM-01'),
  signal('coiling_temperature', 'Cel', 520, 720, 0, 'LUX-HSM-01'),
  // LUX-BOF-01 (5)
  signal('oxygen_lance_flow', 'Nm3/min', 180, 920, 1_000, 'LUX-BOF-01', true),
  signal('vessel_shell_temperature', 'Cel', 180, 420, 5_000, 'LUX-BOF-01', true),
  signal('bath_temperature', 'Cel', 1_580, 1_700, 10_000, 'LUX-BOF-01', true),
  signal('slag_basicity_index', 'ratio', 2.4, 4.2, 60_000, 'LUX-BOF-01', true),
  signal('tap_to_tap_time', 'min', 32, 58, 60_000, 'LUX-BOF-01', true),
  // LUX-CC-01 (5)
  signal('mould_level', 'mm', 60, 140, 1_000, 'LUX-CC-01', true),
  signal('casting_speed', 'm/min', 0.6, 1.8, 1_000, 'LUX-CC-01', true),
  signal('secondary_cooling_flow', 'm3/h', 40, 220, 2_000, 'LUX-CC-01', true),
  signal('superheat', 'Cel', 10, 45, 10_000, 'LUX-CC-01', true),
  signal('slab_width_deviation', 'mm', -6, 6, 5_000, 'LUX-CC-01', true),
  // LUX-UTIL-01 (6)
  signal('site_active_power', 'MW', 38, 180, 1_000, 'LUX-UTIL-01', true),
  signal('power_factor', 'ratio', 0.86, 1.0, 5_000, 'LUX-UTIL-01', true),
  signal('grid_frequency', 'Hz', 49.8, 50.2, 1_000, 'LUX-UTIL-01', true),
  signal('compressed_air_pressure', 'bar', 5.8, 8.2, 2_000, 'LUX-UTIL-01', true),
  signal('spot_price', 'EUR/MWh', -15, 420, 900_000, 'LUX-UTIL-01', true),
  signal('grid_carbon_intensity', 'gCO2/kWh', 40, 480, 900_000, 'LUX-UTIL-01', true),
  // DE-EAF-01 (6)
  signal('arc_current', 'kA', 30, 80, 1_000, 'DE-EAF-01', true),
  signal('electrode_position', 'mm', 200, 900, 1_000, 'DE-EAF-01', true),
  signal('bath_temperature', 'Cel', 1550, 1680, 10_000, 'DE-EAF-01', true),
  signal('off_gas_temperature', 'Cel', 800, 1400, 2_000, 'DE-EAF-01', true),
  signal('oxygen_injection_rate', 'Nm3/min', 20, 120, 2_000, 'DE-EAF-01', true),
  signal('power_on_time', 'min', 35, 65, 60_000, 'DE-EAF-01', true),
  // DE-LF-01 (5)
  signal('ladle_temperature', 'Cel', 1540, 1640, 5_000, 'DE-LF-01', true),
  signal('argon_flow_rate', 'Nl/min', 100, 600, 2_000, 'DE-LF-01', true),
  signal('slag_height', 'mm', 50, 200, 10_000, 'DE-LF-01', true),
  signal('heating_power', 'MW', 5, 30, 1_000, 'DE-LF-01', true),
  signal('desulfurization_rate', 'ppm/min', 0.5, 4, 60_000, 'DE-LF-01', true),
  // DE-BCM-01 (5)
  signal('mould_level', 'mm', 55, 130, 1_000, 'DE-BCM-01', true),
  signal('casting_speed', 'm/min', 2, 5.5, 1_000, 'DE-BCM-01', true),
  signal('secondary_cooling_flow', 'm3/h', 30, 180, 2_000, 'DE-BCM-01', true),
  signal('strand_temperature', 'Cel', 900, 1200, 5_000, 'DE-BCM-01', true),
  signal('billet_length_deviation', 'mm', -4, 4, 5_000, 'DE-BCM-01', true),
  // DE-UTIL-01 (6)
  signal('site_active_power', 'MW', 45, 220, 1_000, 'DE-UTIL-01', true),
  signal('power_factor', 'ratio', 0.88, 1.0, 5_000, 'DE-UTIL-01', true),
  signal('grid_frequency', 'Hz', 49.8, 50.2, 1_000, 'DE-UTIL-01', true),
  signal('compressed_air_pressure', 'bar', 6, 8.5, 2_000, 'DE-UTIL-01', true),
  signal('spot_price', 'EUR/MWh', -10, 380, 900_000, 'DE-UTIL-01', true),
  signal('grid_carbon_intensity', 'gCO2/kWh', 60, 520, 900_000, 'DE-UTIL-01', true),
  // BE-CRM-01 (5)
  signal('strip_tension', 'kN', 20, 180, 1_000, 'BE-CRM-01', true),
  signal('roll_force', 'MN', 2, 18, 1_000, 'BE-CRM-01', true),
  signal('strip_speed', 'm/min', 200, 1800, 1_000, 'BE-CRM-01', true),
  signal('strip_thickness', 'mm', 0.2, 3, 2_000, 'BE-CRM-01', true),
  signal('coolant_temperature', 'Cel', 30, 65, 5_000, 'BE-CRM-01', true),
  // BE-GAL-01 (5)
  signal('zinc_bath_temperature', 'Cel', 445, 465, 5_000, 'BE-GAL-01', true),
  signal('line_speed', 'm/min', 60, 200, 1_000, 'BE-GAL-01', true),
  signal('coating_weight', 'g/m2', 40, 350, 10_000, 'BE-GAL-01', true),
  signal('air_knife_pressure', 'kPa', 3, 20, 2_000, 'BE-GAL-01', true),
  signal('strip_temperature_exit', 'Cel', 200, 320, 5_000, 'BE-GAL-01', true),
  // BE-UTIL-01 (6)
  signal('site_active_power', 'MW', 12, 55, 1_000, 'BE-UTIL-01', true),
  signal('power_factor', 'ratio', 0.90, 1.0, 5_000, 'BE-UTIL-01', true),
  signal('grid_frequency', 'Hz', 49.8, 50.2, 1_000, 'BE-UTIL-01', true),
  signal('compressed_air_pressure', 'bar', 5.5, 7.8, 2_000, 'BE-UTIL-01', true),
  signal('spot_price', 'EUR/MWh', -12, 400, 900_000, 'BE-UTIL-01', true),
  signal('grid_carbon_intensity', 'gCO2/kWh', 30, 280, 900_000, 'BE-UTIL-01', true),
  // ES-EAF-01 (4)
  signal('arc_current', 'kA', 28, 75, 1_000, 'ES-EAF-01', true),
  signal('bath_temperature', 'Cel', 1560, 1690, 10_000, 'ES-EAF-01', true),
  signal('electrode_position', 'mm', 180, 850, 1_000, 'ES-EAF-01', true),
  signal('tap_to_tap_time', 'min', 40, 70, 60_000, 'ES-EAF-01', true),
  // ES-WRM-01 (5)
  signal('stand_motor_current', 'A', 800, 6000, 1_000, 'ES-WRM-01', true),
  signal('rod_speed', 'm/s', 30, 110, 1_000, 'ES-WRM-01', true),
  signal('laying_head_temperature', 'Cel', 780, 1050, 5_000, 'ES-WRM-01', true),
  signal('cooling_conveyor_speed', 'm/min', 10, 60, 2_000, 'ES-WRM-01', true),
  signal('rod_diameter_deviation', 'mm', -0.3, 0.3, 5_000, 'ES-WRM-01', true),
  // ES-UTIL-01 (5)
  signal('site_active_power', 'MW', 25, 130, 1_000, 'ES-UTIL-01', true),
  signal('power_factor', 'ratio', 0.87, 1.0, 5_000, 'ES-UTIL-01', true),
  signal('grid_frequency', 'Hz', 49.8, 50.2, 1_000, 'ES-UTIL-01', true),
  signal('compressed_air_pressure', 'bar', 5.5, 8, 2_000, 'ES-UTIL-01', true),
  signal('spot_price', 'EUR/MWh', -5, 350, 900_000, 'ES-UTIL-01', true),
]

export const INCIDENT_CATALOG: IncidentCatalogEntry[] = [
  {
    incidentId: 'degrading-furnace',
    label: 'Degrading furnace lining',
    description:
      'Accelerated hearth wear on the blast furnace: local heat flux ramps up, refractory thickness falls, shell temperature rises.',
    severity: 'high',
    defaultDurationMinutes: 30,
    targetDeviceIds: ['LUX-BF-01'],
    affectedSignalCodes: [
      'local_heat_flux',
      'hearth_refractory_estimate',
      'hearth_shell_temperature',
    ],
  },
  {
    incidentId: 'cooling-water-loss',
    label: 'Cooling water loss',
    description: 'Cooling circuit flow collapses and outlet temperature climbs towards the trip band.',
    severity: 'critical',
    defaultDurationMinutes: 15,
    targetDeviceIds: ['LUX-BF-01'],
    affectedSignalCodes: ['cooling_water_flow', 'cooling_water_outlet_temperature'],
  },
  {
    incidentId: 'sensor-drift',
    label: 'Sensor drift',
    description: 'A slow additive bias builds on the selected sensor while the process stays nominal.',
    severity: 'medium',
    defaultDurationMinutes: 60,
    targetDeviceIds: [],
    affectedSignalCodes: [],
  },
  {
    incidentId: 'sensor-dropout',
    label: 'Sensor dropout',
    description: 'The selected sensor stops publishing; quality degrades to bad and the row goes stale.',
    severity: 'medium',
    defaultDurationMinutes: 10,
    targetDeviceIds: [],
    affectedSignalCodes: [],
  },
  {
    incidentId: 'energy-price-spike',
    label: 'Energy price spike',
    description: 'Spot price and site active power spike together, opening a load-shift opportunity.',
    severity: 'medium',
    defaultDurationMinutes: 45,
    targetDeviceIds: ['LUX-UTIL-01'],
    affectedSignalCodes: ['spot_price', 'site_active_power'],
  },
  {
    incidentId: 'quality-drift',
    label: 'Quality drift',
    description: 'Caster width deviation and coiling temperature drift out of the control band.',
    severity: 'high',
    defaultDurationMinutes: 45,
    targetDeviceIds: ['LUX-CC-01', 'LUX-HSM-01'],
    affectedSignalCodes: ['slab_width_deviation', 'mould_level', 'coiling_temperature'],
  },
  {
    incidentId: 'edge-outage-recovery',
    label: 'Edge outage and recovery',
    description: 'The edge gateway drops, sensors go stale, then a catch-up burst replays the buffer.',
    severity: 'low',
    defaultDurationMinutes: 20,
    targetDeviceIds: [],
    affectedSignalCodes: [],
  },
]

export const SCENARIOS = [
  'healthy-baseline',
  'demo-full',
  'lining-degradation-21d',
  'energy-price-spike',
  'quality-drift',
  'edge-outage-recovery',
]

/** Stable 32-bit hash so a sensor's waveform never changes between reloads. */
function hash(value: string): number {
  let h = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    h ^= value.charCodeAt(index)
    h = Math.imul(h, 16777619)
  }
  return (h >>> 0) / 4294967295
}

function waveform(sensor: CatalogSignal, tick: number): number {
  const phase = hash(sensor.code) * Math.PI * 2
  const period = 24 + hash(`${sensor.code}:period`) * 40
  const base = Math.sin((tick / period) * Math.PI * 2 + phase)
  const harmonic = 0.35 * Math.sin((tick / (period / 3)) * Math.PI * 2 + phase * 1.7)
  const jitter = 0.08 * Math.sin(tick * 1.9 + phase * 3.1)
  const unit = (base * 0.55 + harmonic * 0.25 + jitter + 1) / 2
  const span = sensor.high - sensor.low
  const value = sensor.low + span * (0.14 + 0.72 * Math.min(1, Math.max(0, unit)))
  return Math.round(value * 1000) / 1000
}

function statusOf(sensor: CatalogSignal, value: number): SensorRow['status'] {
  const span = sensor.high - sensor.low
  if (value < sensor.low - span * 0.05 || value > sensor.high + span * 0.05) {
    return 'alarm'
  }
  if (value < sensor.low || value > sensor.high) {
    return 'warning'
  }
  return 'normal'
}

function trendOf(sensor: CatalogSignal, tick: number): SensorRow['trend'] {
  const delta = waveform(sensor, tick) - waveform(sensor, tick - 4)
  const epsilon = (sensor.high - sensor.low) * 0.01
  if (delta > epsilon) {
    return 'rising'
  }
  if (delta < -epsilon) {
    return 'falling'
  }
  return 'flat'
}

const BASE_TICK = 720

export function fixtureSensors(): SensorRow[] {
  return SIGNALS.map((sensor) => {
    const value = waveform(sensor, BASE_TICK)
    const device = DEVICES.find((entry) => entry.deviceId === sensor.deviceId)
    const mid = (sensor.low + sensor.high) / 2
    const span = sensor.high - sensor.low || 1
    return {
      sensorId: `${sensor.deviceId}:${sensor.code}`,
      deviceId: sensor.deviceId,
      signalCode: sensor.code,
      displayName: sensor.code
        .split('_')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' '),
      area: device?.area ?? 'Unknown',
      unit: sensor.unit,
      low: sensor.low,
      high: sensor.high,
      samplePeriodMs: sensor.periodMs,
      value,
      quality: 'good' as const,
      status: statusOf(sensor, value),
      trend: trendOf(sensor, BASE_TICK),
      deviationPct: Math.round(((value - mid) / span) * 1000) / 10,
      clamped: false,
      lastSampleAt: CLOCK,
    }
  })
}

export function fixtureDevices(): DeviceRow[] {
  const sensors = fixtureSensors()
  return DEVICES.map((device) => {
    const owned = sensors.filter((sensor) => sensor.deviceId === device.deviceId)
    const alarms = owned.filter((sensor) => sensor.status === 'alarm').length
    const warnings = owned.filter((sensor) => sensor.status === 'warning').length
    const healthScore =
      owned.length === 0 ? 1 : Math.max(0, 1 - (alarms * 0.25 + warnings * 0.08) / owned.length)
    return {
      deviceId: device.deviceId,
      site: siteOfDevice(device.deviceId),
      area: device.area,
      description: device.description,
      status: alarms > 0 ? 'fault' : warnings > 0 ? 'degraded' : 'healthy',
      sensorCount: owned.length,
      activeIncidents: [],
      lastSampleAt: CLOCK,
      healthScore: Math.round(healthScore * 1000) / 1000,
      uptimePct: Math.round((99.1 + hash(device.deviceId) * 0.85) * 100) / 100,
    }
  })
}

export function fixtureDeviceDetail(deviceId: string): DeviceDetail | null {
  const device = fixtureDevices().find((entry) => entry.deviceId === deviceId)
  if (!device) {
    return null
  }
  return { ...device, sensors: fixtureSensors().filter((sensor) => sensor.deviceId === deviceId) }
}

const WINDOW_MINUTES: Record<string, number> = { '15m': 15, '1h': 60, '8h': 480, '24h': 1440 }

export function fixtureSeries(sensorId: string, window: string, points = 120): SensorSeries | null {
  const signalCode = sensorId.split(':')[1] ?? ''
  const sensor = SIGNALS.find(
    (entry) => entry.code === signalCode && `${entry.deviceId}:${entry.code}` === sensorId,
  )
  if (!sensor) {
    return null
  }
  const minutes = WINDOW_MINUTES[window] ?? 60
  const count = Math.max(2, Math.min(points, 400))
  const stepMs = (minutes * 60_000) / (count - 1)
  const series: SeriesPoint[] = []
  for (let index = 0; index < count; index += 1) {
    const tick = BASE_TICK - (count - 1 - index)
    series.push({
      t: new Date(CLOCK_MS - (count - 1 - index) * stepMs).toISOString(),
      v: waveform(sensor, tick),
      q: 'good',
    })
  }
  const values = series.map((point) => point.v)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length
  const variance = values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length
  const range = max - min || 1
  const row = fixtureSensors().find((entry) => entry.sensorId === sensorId)
  return {
    sensorId,
    deviceId: sensor.deviceId,
    displayName: row?.displayName ?? signalCode,
    unit: sensor.unit,
    low: sensor.low,
    high: sensor.high,
    window,
    pointCount: series.length,
    points: series,
    normalizedPoints: series.map((point) => ({
      t: point.t,
      v: Math.round(((point.v - min) / range) * 10000) / 10000,
    })),
    stats: {
      min: Math.round(min * 1000) / 1000,
      max: Math.round(max * 1000) / 1000,
      mean: Math.round(mean * 1000) / 1000,
      stdDev: Math.round(Math.sqrt(variance) * 1000) / 1000,
      last: values[values.length - 1],
    },
  }
}

export function fixtureSimulatorStatus(
  overrides: Partial<SimulatorStatus> = {},
  activeIncidents: ActiveIncident[] = [],
): SimulatorStatus {
  return {
    state: 'running',
    scenario: 'demo-full',
    seed: 240726,
    speedFactor: 1,
    tickIntervalSeconds: 5,
    simulatedClock: CLOCK,
    elapsedHours: 6,
    tickCount: BASE_TICK,
    deviceCount: DEVICES.length,
    sensorCount: SIGNALS.length,
    activeIncidents,
    availableScenarios: SCENARIOS,
    availableIncidents: INCIDENT_CATALOG,
    startedAt: '2026-07-25T12:45:00Z',
    ...overrides,
  }
}
