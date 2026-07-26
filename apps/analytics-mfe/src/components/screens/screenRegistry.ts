import type { ComponentType } from 'react'
import { CommandCenter } from './CommandCenter'
import { Operations } from './Operations'
import { FurnaceLiningForecast } from './FurnaceLiningForecast'
import { FurnaceThermal } from './FurnaceThermal'
import { FurnaceMaintenance } from './FurnaceMaintenance'
import { EnergySpotSchedule } from './EnergySpotSchedule'
import { EnergySimulator } from './EnergySimulator'
import { QualityBatches } from './QualityBatches'
import { QualitySpc } from './QualitySpc'
import { SustainabilityEmissions } from './SustainabilityEmissions'
import { SustainabilityEts } from './SustainabilityEts'
import { SustainabilityAudit } from './SustainabilityAudit'
import { KnowledgeHub } from './KnowledgeHub'
import { ExecutiveOverview } from './ExecutiveOverview'
import { ExecutivePowerBi } from './ExecutivePowerBi'
import { PlatformCapacity } from './PlatformCapacity'
import { PlatformJobs } from './PlatformJobs'
import { PlatformCost } from './PlatformCost'
import { DeviceFleet } from './DeviceFleet'
import { DeviceSensors } from './DeviceSensors'
import { DeviceSimulator } from './DeviceSimulator'
import { DashboardCollections } from './DashboardCollections'

/** Maps `${section}/${subView}` to the screen component that renders it. */
export const screenRegistry: Record<string, ComponentType> = {
  'command-center/overview': CommandCenter,
  'operations/overview': Operations,
  'furnace-health/lining-forecast': FurnaceLiningForecast,
  'furnace-health/thermal-explorer': FurnaceThermal,
  'furnace-health/maintenance-planner': FurnaceMaintenance,
  'energy-optimization/spot-price-schedule': EnergySpotSchedule,
  'energy-optimization/load-shift-simulator': EnergySimulator,
  'quality/batches': QualityBatches,
  'quality/spc': QualitySpc,
  'sustainability-compliance/emissions-ledger': SustainabilityEmissions,
  'sustainability-compliance/ets-exposure': SustainabilityEts,
  'sustainability-compliance/audit': SustainabilityAudit,
  'knowledge-hub/procedures': KnowledgeHub,
  'knowledge-hub/capture-status': KnowledgeHub,
  'executive-overview/overview': ExecutiveOverview,
  'executive-overview/board-report': ExecutivePowerBi,
  'platform-ops/capacity': PlatformCapacity,
  'platform-ops/jobs': PlatformJobs,
  'platform-ops/cost-telemetry': PlatformCost,
  'device-operations/fleet': DeviceFleet,
  'device-operations/sensors': DeviceSensors,
  'device-operations/simulator': DeviceSimulator,
  'dashboards/collections': DashboardCollections,
}

export function resolveScreen(section: string, subView: string): ComponentType | null {
  return screenRegistry[`${section}/${subView}`] ?? null
}
