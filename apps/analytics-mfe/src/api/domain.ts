import type { ConfidenceBand, Driver } from './envelope'

export type DataSource = 'bff' | 'fixture'

export interface CommandSummary {
  site: string
  syntheticBanner: string
  freshness: Record<string, { asOf: string | null; stale: boolean }>
  kpis: {
    plannedTonnage: number
    energyConsumptionMwh: number
    energyDispatchSavingsTargetPct: number
    scope2KgCo2e: number
    qualityPredictedFirstPassYieldPct: number
    liningRulDaysP50: number
    openAlerts: number
  }
  scenario: { id: string; seed: number; source: string }
}

export type AlertSeverity = 'CRITICAL' | 'WARNING' | 'INFO'

export interface AlertRow {
  alertId: string
  site: string
  assetId: string
  componentId?: string
  severity: AlertSeverity | string
  status: string
  message: string
  confidence?: number
  createdAt: string
  updatedAt?: string
  workOrderId?: string
  correlationId?: string
  sourceRef?: string
}

export interface AlertEvent {
  id: string
  type: string
  data: Record<string, unknown>
}

export interface FurnaceRow {
  assetId: string
  site: string
  assetType: string
  componentId: string
  health: string
  synthetic?: boolean
}

export interface LiningForecast {
  assetId: string
  componentId: string
  value: number
  unit: string
  confidence: ConfidenceBand
  riskScore: number
  riskLevel: string
  estimatedMinimumLiningMm: number
  modelVersion: string
  scoredAt: string | null
  drivers: Driver[]
  featureSnapshot: Record<string, number>
  sourceRefs: string[]
  auditRef?: string
}

export interface EnergyIntervalRow {
  eventId: string
  eventTs: string
  site: string
  assetId: string
  intervalStart: string
  intervalEnd?: string
  priceEurMwh: number
  demandMw: number
  baselineDemandMw: number
  consumptionMwh: number
  carbonIntensityKgCo2eMwh: number
  meterId: string
  scenario: string
  sourceRef?: string
}

export interface EnergyScheduleRow {
  batchId: string
  grade: string
  urgent: boolean
  slot: number
  plannedAt: string
  scheduledAt: string
  shiftMinutes: number
  soakMinutes: number
  holdMinutes: number
  tonnage: number
  energyMwh: number
  priceEurMwh: number
  costEur: number
}

export interface EnergyRecommendation {
  recommendationId: string
  version: number
  status: string
  modelVersion: string
  site: string
  scenario: string
  baseline: {
    costEur: number
    peakDemandMw: number
    tonnage: number
    schedule: EnergyScheduleRow[]
  }
  optimized: {
    costEur: number
    peakDemandMw: number
    tonnage: number
    schedule: EnergyScheduleRow[]
  }
  constraintReport?: Array<{ name: string; status: string; detail?: string }>
  hardConstraintViolations: number
  savings: {
    costPct: number
    costEur: number
    peakPct: number
    co2Pct: number
  }
  auditRef?: string
}

export interface QualityBatchRow {
  batchId: string
  sourceBatchId?: string
  site: string
  assetId: string
  heatId: string
  grade: string
  sampleId: string
  characteristic: string
  value: number
  unit: string
  lowerSpecLimit?: number
  upperSpecLimit?: number
  resultStatus: string
  carbonEquivalent?: number
  coilingTempBiasC: number
  riskScore: number
  eventTs: string
  sourceRef?: string
}

export interface Genealogy {
  batchId: string
  site: string
  chain: {
    rawMaterialLots: string[]
    heat: string
    ladleTreatment: string
    slab: string
    reheating: { assetId: string; operation: string }
    coil: string
    sample: string
    testResult: { characteristic: string; value: number; unit: string; resultStatus: string }
    shipment: string
  }
  synthetic: boolean
  sourceRefs: string[]
}

export interface QualityWhatIf {
  value: number
  unit: string
  confidence: ConfidenceBand
  modelVersion: string
  scoredAt: string
  drivers: Driver[]
  current: { predictedFirstPassYieldPct: number; riskScore: number }
  proposed: { predictedFirstPassYieldPct: number; riskScore?: number }
  auditRef?: string
}

export interface EmissionRow {
  site: string
  eventTs: string
  scope2KgCo2e: number
  consumptionMwh: number
  carbonIntensityKgCo2eMwh: number
  sourceRef?: string
}

export interface SustainabilitySummary {
  site: string
  energyConsumptionMwh: number
  scope1KgCo2e: number
  scope2KgCo2e: number
  etsAllowancePriceEurTonne: number
  modeledDispatchCo2ReductionPct: number
  synthetic: boolean
  dataClassification: string
}

export interface ProcedureRow {
  procedureId: string
  title: string
  status: string
  version: number
  sessionId: string
  observation: string
  recommendedCheck?: string
  rationale?: string
  safetyBoundary?: string
  citations?: string[]
}

export interface AuditRow {
  auditId: string
  domain: string
  entityId: string
  correlationId: string
  action: string
  actor: string
  modelVersion?: string
  recordedAt: string
}

export type CapacityState =
  | 'Paused'
  | 'ResumeRequested'
  | 'Resuming'
  | 'ReadinessCheck'
  | 'Running'
  | 'DrainRequested'
  | 'Draining'
  | 'SuspendRequested'
  | 'Failed'

export interface CapacityStatus {
  capacityId: string
  environment: string
  state: CapacityState | string
  sku: string
  skuOptions?: string[]
  demoModeSimulated: boolean
  stale: boolean
}

export interface CapacityTransition {
  capacityId: string
  fromState: string
  toState: string
  actor: string
  reason?: string
  recordedAt?: string
  correlationId?: string
}

export interface WorkOrderRow {
  workOrderId: string
  site: string
  assetId: string
  title: string
  reason?: string
  status: string
  synthetic?: boolean
  createdBy?: string
  detectedAt?: string
}

export interface TelemetryRow {
  eventId: string
  eventTs: string
  site: string
  assetId: string
  sensorId: string
  signalCode: string
  value: number
  unit: string
  quality: string
  scenarioId?: string
}

export interface Identity {
  userId: string
  displayName: string
  roles: string[]
  plantScope: string[]
  personas: string[]
  locale: string
  permittedActions: string[]
}
