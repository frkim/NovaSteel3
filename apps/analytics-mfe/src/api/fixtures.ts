import type {
  AlertRow,
  AuditRow,
  CapacityStatus,
  CapacityTransition,
  CommandSummary,
  EmissionRow,
  EnergyIntervalRow,
  EnergyRecommendation,
  EnergyScheduleRow,
  FurnaceRow,
  Genealogy,
  LiningForecast,
  ProcedureRow,
  QualityBatchRow,
  SustainabilitySummary,
  TelemetryRow,
  WorkOrderRow,
} from './domain'

/**
 * Deterministic synthetic fixtures for resilient offline fallback (UX §20, demo
 * runbook §6 fallback ladder). Values intentionally match the runbook cue sheet
 * so an offline walkthrough tells the same story as the live BFF.
 */

export const FIXTURE_SITE = 'NS-DEMO-LUX-01'
const DAY = '2026-07-25'
export const FIXTURE_AS_OF = `${DAY}T18:45:00Z`

function iso(hour: number, minute = 0): string {
  const h = String(Math.floor(hour)).padStart(2, '0')
  const m = String(minute).padStart(2, '0')
  return `${DAY}T${h}:${m}:00Z`
}

/** Smooth day-ahead price curve peaking at the 280 €/MWh evening scarcity cue. */
function priceAt(slot: number): number {
  const hour = slot * 0.25
  const base = 58 + 26 * Math.sin(((hour - 6) / 24) * Math.PI * 2)
  const morning = 34 * Math.exp(-((hour - 8) ** 2) / 6)
  const evening = 210 * Math.exp(-((hour - 18.5) ** 2) / 1.8)
  return Math.round((base + morning + evening) * 10) / 10
}

function carbonAt(slot: number): number {
  const hour = slot * 0.25
  return Math.round(210 + 70 * Math.sin(((hour - 10) / 24) * Math.PI * 2) + 30 * Math.cos(hour / 3))
}

export function energyIntervals(): EnergyIntervalRow[] {
  const rows: EnergyIntervalRow[] = []
  for (let slot = 0; slot < 96; slot += 1) {
    const hour = slot * 0.25
    const price = priceAt(slot)
    const peakShape = 1 + 0.55 * Math.exp(-((hour - 18.5) ** 2) / 3)
    const baseline = Math.round((34 + 14 * Math.sin(((hour - 6) / 24) * Math.PI * 2)) * peakShape * 10) / 10
    // The optimizer shifts flexible load away from the evening scarcity peak.
    const shift = hour >= 17 && hour <= 20 ? -11.6 : hour >= 2 && hour <= 5 ? 8.4 : -1.2
    const demand = Math.max(12, Math.round((baseline + shift) * 10) / 10)
    rows.push({
      eventId: `fixture-energy-${slot}`,
      eventTs: iso(Math.floor(hour), (slot % 4) * 15),
      site: FIXTURE_SITE,
      assetId: 'LUX-UTIL-01',
      intervalStart: iso(Math.floor(hour), (slot % 4) * 15),
      intervalEnd: iso(Math.floor(hour), (slot % 4) * 15 + 15),
      priceEurMwh: price,
      demandMw: demand,
      baselineDemandMw: baseline,
      consumptionMwh: Math.round((baseline / 4) * 100) / 100,
      carbonIntensityKgCo2eMwh: carbonAt(slot),
      meterId: 'LUX-UTIL-01-ELEC-01',
      scenario: 'demo-full',
      sourceRef: `event:fixture-energy-${slot}`,
    })
  }
  return rows
}

const FLEXIBLE_BATCHES: Array<{ id: string; grade: string; urgent: boolean; planned: number; tonnage: number; mwh: number }> = [
  { id: 'REHEAT-BATCH-11', grade: 'NS-AUTO-DP780', urgent: true, planned: 74, tonnage: 240, mwh: 61 },
  { id: 'REHEAT-BATCH-12', grade: 'NS-STRUCT-S355', urgent: false, planned: 73, tonnage: 240, mwh: 58 },
  { id: 'REHEAT-BATCH-13', grade: 'NS-STRUCT-S355', urgent: false, planned: 75, tonnage: 240, mwh: 59 },
  { id: 'REHEAT-BATCH-14', grade: 'NS-AUTO-DP780', urgent: false, planned: 72, tonnage: 240, mwh: 60 },
]

function scheduleRows(optimized: boolean): EnergyScheduleRow[] {
  return FLEXIBLE_BATCHES.map((batch, index) => {
    const slot = optimized && !batch.urgent ? Math.max(8, batch.planned - 60 - index * 2) : batch.planned
    const price = priceAt(slot)
    const shiftMinutes = (slot - batch.planned) * 15
    return {
      batchId: batch.id,
      grade: batch.grade,
      urgent: batch.urgent,
      slot,
      plannedAt: iso(Math.floor(batch.planned * 0.25), (batch.planned % 4) * 15),
      scheduledAt: iso(Math.floor(slot * 0.25), (slot % 4) * 15),
      shiftMinutes,
      soakMinutes: 45,
      holdMinutes: Math.abs(shiftMinutes),
      tonnage: batch.tonnage,
      energyMwh: batch.mwh,
      priceEurMwh: price,
      costEur: Math.round(batch.mwh * price * 100) / 100,
    }
  })
}

export function energyRecommendation(): EnergyRecommendation {
  const baseline = scheduleRows(false)
  const optimized = scheduleRows(true)
  const baselineFlexible = baseline.reduce((sum, row) => sum + row.costEur, 0)
  const optimizedFlexible = optimized.reduce((sum, row) => sum + row.costEur, 0)
  const fixedLoad = 96762.4
  const baselineCost = Math.round((baselineFlexible + fixedLoad) * 100) / 100
  const optimizedCost = Math.round((optimizedFlexible + fixedLoad) * 100) / 100
  return {
    recommendationId: 'REC-DEMO-LUX-240725',
    version: 1,
    status: 'PENDING_APPROVAL',
    modelVersion: 'energy-dispatch-milp/1.2.0-demo',
    site: FIXTURE_SITE,
    scenario: 'demo-full',
    baseline: { costEur: baselineCost, peakDemandMw: 51.81, tonnage: 960, schedule: baseline },
    optimized: { costEur: optimizedCost, peakDemandMw: 40.0, tonnage: 960, schedule: optimized },
    constraintReport: [
      { name: 'soakTimePreserved', status: 'SATISFIED' },
      { name: 'deliveryCommitments', status: 'SATISFIED' },
      { name: 'equipmentCapacity', status: 'SATISFIED' },
      { name: 'plannedTonnage', status: 'SATISFIED' },
      { name: 'urgentBatchFixed', status: 'SATISFIED' },
    ],
    hardConstraintViolations: 0,
    savings: {
      costPct: Math.round(((baselineFlexible - optimizedFlexible) / baselineFlexible) * 1000) / 10,
      costEur: Math.round((baselineCost - optimizedCost) * 100) / 100,
      peakPct: 22.8,
      co2Pct: 8.7,
    },
  }
}

export function furnaces(): FurnaceRow[] {
  return [
    {
      assetId: 'LUX-BF-01',
      site: FIXTURE_SITE,
      assetType: 'BLAST_FURNACE',
      componentId: 'HEARTH-SECTOR-07',
      health: 'HIGH_RISK',
      synthetic: true,
    },
    {
      assetId: 'LUX-RHF-01',
      site: FIXTURE_SITE,
      assetType: 'REHEAT_FURNACE',
      componentId: 'RHF-ZONE-03',
      health: 'WATCH',
      synthetic: true,
    },
  ]
}

export function liningForecast(): LiningForecast {
  return {
    assetId: 'LUX-BF-01',
    componentId: 'HEARTH-SECTOR-07',
    value: 21.0,
    unit: 'd',
    confidence: { p10: 16.8, p50: 21.0, p90: 27.5 },
    riskScore: 0.8706,
    riskLevel: 'HIGH',
    estimatedMinimumLiningMm: 300.0,
    modelVersion: 'lining-rul-piml/1.3.0-demo',
    scoredAt: FIXTURE_AS_OF,
    drivers: [
      { name: 'heat_flux_6h_slope', contribution: 0.29 },
      { name: 'sector_to_ring_temp_delta', contribution: 0.24 },
      { name: 'cooling_efficiency_residual', contribution: 0.18 },
    ],
    featureSnapshot: {
      liningThicknessMm: 363,
      coolingDeltaC: 9.4,
      coolingFlowM3h: 198,
      heatFluxKwM2: 118,
      waterHeatProxyKw: 214.7,
      apparentThermalResistance: 8.73,
    },
    sourceRefs: ['simulator:fixture:offline'],
  }
}

/** Thermal signature matrix for the heatmap: hearth sectors × hourly window. */
export function thermalMatrix(): { zones: string[]; hours: string[]; values: number[][] } {
  const zones = ['SECTOR-05', 'SECTOR-06', 'SECTOR-07', 'SECTOR-08', 'SECTOR-09']
  const hours: string[] = []
  const values: number[][] = zones.map(() => [])
  for (let hour = 0; hour < 24; hour += 1) {
    hours.push(iso(hour))
    zones.forEach((zone, zoneIndex) => {
      const base = 640 + zoneIndex * 6
      const isHotspot = zone === 'SECTOR-07'
      const drift = isHotspot ? hour * 3.4 : hour * 0.4
      const noise = ((hour * 7 + zoneIndex * 13) % 5) - 2
      values[zoneIndex].push(Math.round(base + drift + noise))
    })
  }
  return { zones, hours, values }
}

export function thermalSeries(): Array<{ ts: string; value: number }> {
  const rows: Array<{ ts: string; value: number }> = []
  for (let hour = 0; hour < 24; hour += 1) {
    rows.push({ ts: iso(hour), value: Math.round(646 + hour * 3.4 + Math.sin(hour / 2) * 4) })
  }
  return rows
}

export function alerts(): AlertRow[] {
  return [
    {
      alertId: 'ALERT-HEARTH-SECTOR-07-260725',
      site: FIXTURE_SITE,
      assetId: 'LUX-BF-01',
      componentId: 'HEARTH-SECTOR-07',
      severity: 'CRITICAL',
      status: 'OPEN',
      message: 'Predicted RUL P50 21.0 days (risk 0.87) for HEARTH-SECTOR-07.',
      confidence: 0.8706,
      createdAt: iso(17, 58),
      updatedAt: iso(17, 58),
      correlationId: 'run-demo-full-240725',
      sourceRef: 'event:fixture-alert-07',
    },
    {
      alertId: 'ALERT-ENERGY-SCARCITY-1830',
      site: FIXTURE_SITE,
      assetId: 'LUX-UTIL-01',
      componentId: 'GRID',
      severity: 'WARNING',
      status: 'OPEN',
      message: 'Evening scarcity spike to 280 €/MWh forecast for 18:30–19:00.',
      confidence: 0.74,
      createdAt: iso(15, 12),
      updatedAt: iso(15, 12),
      sourceRef: 'event:fixture-alert-energy',
    },
    {
      alertId: 'ALERT-QUALITY-DRIFT-DP780',
      site: FIXTURE_SITE,
      assetId: 'LUX-HSM-01',
      componentId: 'COIL-LUX-260725-017',
      severity: 'WARNING',
      status: 'ACKNOWLEDGED',
      message: 'Coiling temperature and force balance drifting on NS-AUTO-DP780.',
      confidence: 0.68,
      createdAt: iso(4, 0),
      updatedAt: iso(9, 5),
      sourceRef: 'event:fixture-alert-quality',
    },
    {
      alertId: 'ALERT-RHF-ZONE-03-WATCH',
      site: FIXTURE_SITE,
      assetId: 'LUX-RHF-01',
      componentId: 'RHF-ZONE-03',
      severity: 'INFO',
      status: 'OPEN',
      message: 'Reheat furnace zone 03 flagged for routine watch inspection.',
      confidence: 0.52,
      createdAt: iso(11, 30),
      updatedAt: iso(11, 30),
      sourceRef: 'event:fixture-alert-rhf',
    },
  ]
}

const GRADES = ['NS-AUTO-DP780', 'NS-STRUCT-S355', 'NS-AUTO-DP780', 'NS-ELEC-M400']

export function qualityBatches(): QualityBatchRow[] {
  const rows: QualityBatchRow[] = []
  for (let index = 0; index < 20; index += 1) {
    const grade = GRADES[index % GRADES.length]
    const bias = index === 0 ? 11.4 : Math.round((((index * 37) % 17) - 8) * 10) / 10
    const status = Math.abs(bias) > 9 ? 'FAIL' : Math.abs(bias) > 6 ? 'REVIEW' : 'PASS'
    const risk = Math.min(0.95, Math.round((0.11 + Math.abs(bias) * 0.028) * 1000) / 1000)
    rows.push({
      batchId: index === 0 ? 'COIL-LUX-260725-017' : `COIL-LUX-260725-${String(30 + index).padStart(3, '0')}`,
      site: FIXTURE_SITE,
      assetId: 'LUX-HSM-01',
      heatId: `H-LUX-260725-${String(40 + index).padStart(4, '0')}`,
      grade,
      sampleId: `SMP-${String(1000 + index)}`,
      characteristic: index % 2 === 0 ? 'YIELD_STRENGTH' : 'TENSILE_STRENGTH',
      value: Math.round((420 + bias * 3 + index) * 10) / 10,
      unit: 'MPa',
      lowerSpecLimit: 380,
      upperSpecLimit: 520,
      resultStatus: status,
      carbonEquivalent: Math.round((0.42 + index * 0.002) * 1000) / 1000,
      coilingTempBiasC: bias,
      riskScore: risk,
      eventTs: iso(Math.max(0, 18 - index), (index % 4) * 15),
      sourceRef: `event:fixture-quality-${index}`,
    })
  }
  return rows
}

export function genealogy(batchId: string): Genealogy {
  const suffix = batchId.slice(-4)
  return {
    batchId,
    site: FIXTURE_SITE,
    chain: {
      rawMaterialLots: [`LOT-FE-${suffix}`],
      heat: `H-LUX-260725-${suffix}`,
      ladleTreatment: `LADLE-${suffix}`,
      slab: `SLAB-${suffix}`,
      reheating: { assetId: 'LUX-RHF-01', operation: `REHEAT-${suffix}` },
      coil: batchId,
      sample: `SMP-${suffix}`,
      testResult: { characteristic: 'YIELD_STRENGTH', value: 452.4, unit: 'MPa', resultStatus: 'REVIEW' },
      shipment: `SHIP-DEMO-${suffix}`,
    },
    synthetic: true,
    sourceRefs: [`event:fixture-quality-${batchId}`],
  }
}

/** SPC control chart series (I-MR) for high-grade coiling temperature bias. */
export function spcSeries(): { points: Array<{ index: number; value: number; label: string }>; mean: number; ucl: number; lcl: number } {
  const raw = [1.2, -0.6, 0.9, 2.1, -1.1, 0.4, 1.8, 3.4, 2.9, 4.6, 5.8, 3.2, 2.4, 1.1, -0.4, 0.8, 2.2, 1.6, 0.3, 11.4]
  const mean = 1.9
  const sigma = 2.2
  return {
    points: raw.map((value, index) => ({ index: index + 1, value, label: `#${index + 1}` })),
    mean,
    ucl: Math.round((mean + 3 * sigma) * 10) / 10,
    lcl: Math.round((mean - 3 * sigma) * 10) / 10,
  }
}

export function defectPareto(): Array<{ defect: string; count: number; cause: string }> {
  return [
    { defect: 'Coiling temperature drift', count: 34, cause: 'Process' },
    { defect: 'Edge crack', count: 21, cause: 'Material' },
    { defect: 'Surface scale', count: 14, cause: 'Reheat' },
    { defect: 'Thickness variance', count: 9, cause: 'Mill' },
    { defect: 'Coating porosity', count: 5, cause: 'Finishing' },
    { defect: 'Other', count: 3, cause: 'Mixed' },
  ]
}

export function emissions(): EmissionRow[] {
  return energyIntervals().map((row) => ({
    site: FIXTURE_SITE,
    eventTs: row.intervalStart,
    scope2KgCo2e: Math.round(row.consumptionMwh * row.carbonIntensityKgCo2eMwh * 100) / 100,
    consumptionMwh: row.consumptionMwh,
    carbonIntensityKgCo2eMwh: row.carbonIntensityKgCo2eMwh,
    sourceRef: row.sourceRef,
  }))
}

export function sustainabilitySummary(): SustainabilitySummary {
  const total = emissions().reduce((sum, row) => sum + row.scope2KgCo2e, 0)
  return {
    site: FIXTURE_SITE,
    energyConsumptionMwh: Math.round(energyIntervals().reduce((sum, row) => sum + row.consumptionMwh, 0) * 100) / 100,
    scope1KgCo2e: Math.round(960 * 1425 * 100) / 100,
    scope2KgCo2e: Math.round(total * 100) / 100,
    etsAllowancePriceEurTonne: 86.0,
    modeledDispatchCo2ReductionPct: 8.7,
    synthetic: true,
    dataClassification: 'SYNTHETIC',
  }
}

export function commandSummary(): CommandSummary {
  const energy = energyIntervals()
  const scope2 = energy.reduce((sum, row) => sum + row.consumptionMwh * row.carbonIntensityKgCo2eMwh, 0)
  return {
    site: FIXTURE_SITE,
    syntheticBanner: 'Synthetic demo data — not for operational control',
    freshness: {
      energy: { asOf: FIXTURE_AS_OF, stale: false },
      furnace: { asOf: FIXTURE_AS_OF, stale: false },
      quality: { asOf: FIXTURE_AS_OF, stale: false },
    },
    kpis: {
      plannedTonnage: 960,
      energyConsumptionMwh: Math.round(energy.reduce((sum, row) => sum + row.consumptionMwh, 0) * 100) / 100,
      energyDispatchSavingsTargetPct: 10.4,
      scope2KgCo2e: Math.round(scope2 * 100) / 100,
      qualityPredictedFirstPassYieldPct: 88.0,
      liningRulDaysP50: 21.0,
      openAlerts: alerts().filter((alert) => alert.status !== 'CLOSED').length,
    },
    scenario: { id: 'demo-full', seed: 240725, source: 'built-in-fixture' },
  }
}

export function procedures(): ProcedureRow[] {
  return [
    {
      procedureId: 'PROC-DEMO-0001',
      title: 'Hearth sector over-temperature verification',
      status: 'IN_REVIEW',
      version: 2,
      sessionId: 'SESS-DEMO-014',
      observation:
        'When a hearth sector warms but cooling flow appears normal, compare neighboring shell thermocouples before acting.',
      recommendedCheck: 'Compare cooling-water inlet/outlet ΔT and recent flow history, not only current flow.',
      rationale: 'Persistence across taps and slower post-tap cooling distinguishes lining degradation from a bad sensor.',
      safetyBoundary: 'Never bypass alarms or change furnace/cooling controls from interview guidance.',
      citations: ['transcript:SESS-DEMO-014#seg-4', 'transcript:SESS-DEMO-014#seg-7'],
    },
    {
      procedureId: 'PROC-DEMO-0002',
      title: 'Cooling-circuit inspection and ultrasound escalation',
      status: 'APPROVED',
      version: 3,
      sessionId: 'SESS-DEMO-015',
      observation: 'Request cooling-circuit inspection and ultrasound measurement when independent signals agree.',
      recommendedCheck: 'Validate sensor health and recent calibration before escalation.',
      rationale: 'Agreement across thermocouples, water ΔT, and heat-flux residual raises confidence in real degradation.',
      safetyBoundary: 'Escalate for engineering approval; do not actuate the furnace.',
      citations: ['transcript:SESS-DEMO-015#seg-2'],
    },
    {
      procedureId: 'PROC-DEMO-0003',
      title: 'Reheat furnace zone soak recovery',
      status: 'DRAFT',
      version: 1,
      sessionId: 'SESS-DEMO-016',
      observation: 'Draft awaiting expert review for reheat zone soak-time recovery after a trip.',
      recommendedCheck: 'Confirm soak minutes restored before releasing the batch.',
      rationale: 'Preserves delivery commitments and grade recipe integrity.',
      safetyBoundary: 'Requires reliability, operations, and safety sign-off before publication.',
      citations: ['transcript:SESS-DEMO-016#seg-1'],
    },
  ]
}

export function knowledgeCoverage(): Array<{ domain: string; coveragePct: number }> {
  return [
    { domain: 'Blast furnace', coveragePct: 82 },
    { domain: 'Reheat furnace', coveragePct: 64 },
    { domain: 'Hot strip mill', coveragePct: 71 },
    { domain: 'Energy & utilities', coveragePct: 58 },
    { domain: 'Quality lab', coveragePct: 77 },
  ]
}

export function auditDecisions(): AuditRow[] {
  return [
    {
      auditId: 'AUD-0001',
      domain: 'furnace',
      entityId: 'LUX-BF-01',
      correlationId: 'run-demo-full-240725',
      action: 'lining.score',
      actor: 'scoring-worker',
      modelVersion: 'lining-rul-piml/1.3.0-demo',
      recordedAt: iso(18, 2),
    },
    {
      auditId: 'AUD-0002',
      domain: 'energy',
      entityId: 'REC-DEMO-LUX-240725',
      correlationId: 'run-demo-full-240725',
      action: 'energy.simulate',
      actor: 'demo-energy-manager',
      modelVersion: 'energy-dispatch-milp/1.2.0-demo',
      recordedAt: iso(15, 20),
    },
    {
      auditId: 'AUD-0003',
      domain: 'quality',
      entityId: 'COIL-LUX-260725-017',
      correlationId: 'run-demo-full-240725',
      action: 'quality.what_if',
      actor: 'demo-quality-engineer',
      modelVersion: 'quality-yield-gbm/2.1.0-demo',
      recordedAt: iso(16, 40),
    },
    {
      auditId: 'AUD-0004',
      domain: 'knowledge',
      entityId: 'PROC-DEMO-0002',
      correlationId: 'seed-knowledge-approved',
      action: 'knowledge.procedure.approve',
      actor: 'ke-demo',
      recordedAt: iso(10, 15),
    },
    {
      auditId: 'AUD-0005',
      domain: 'capacity',
      entityId: 'cap-novasteel-demo-sc',
      correlationId: 'run-demo-full-240725',
      action: 'capacity.start',
      actor: 'demo-platform-ops',
      recordedAt: iso(7, 30),
    },
  ]
}

export function capacityStatus(): CapacityStatus {
  return {
    capacityId: 'cap-novasteel-demo-sc',
    environment: 'demo',
    state: 'Running',
    sku: 'F2',
    demoModeSimulated: true,
    stale: false,
  }
}

export function capacityTransitions(): CapacityTransition[] {
  return [
    { capacityId: 'cap-novasteel-demo-sc', fromState: 'ReadinessCheck', toState: 'Running', actor: 'demo-platform-ops', reason: 'rehearsal', recordedAt: iso(7, 30), correlationId: '01JB...A1' },
    { capacityId: 'cap-novasteel-demo-sc', fromState: 'Resuming', toState: 'ReadinessCheck', actor: 'demo-platform-ops', reason: 'rehearsal', recordedAt: iso(7, 28), correlationId: '01JB...A1' },
    { capacityId: 'cap-novasteel-demo-sc', fromState: 'Paused', toState: 'Resuming', actor: 'demo-platform-ops', reason: 'rehearsal', recordedAt: iso(7, 27), correlationId: '01JB...A1' },
  ]
}

export function jobs(): Array<{ runId: string; pipeline: string; status: string; startedAt: string; durationSec: number; actor: string }> {
  return [
    { runId: 'RUN-4821', pipeline: 'bronze-to-silver', status: 'SUCCEEDED', startedAt: iso(17, 45), durationSec: 214, actor: 'system' },
    { runId: 'RUN-4820', pipeline: 'silver-to-gold', status: 'SUCCEEDED', startedAt: iso(17, 30), durationSec: 176, actor: 'system' },
    { runId: 'RUN-4819', pipeline: 'semantic-refresh', status: 'RUNNING', startedAt: iso(18, 40), durationSec: 62, actor: 'system' },
    { runId: 'RUN-4818', pipeline: 'contract-assertions', status: 'SUCCEEDED', startedAt: iso(17, 10), durationSec: 41, actor: 'system' },
    { runId: 'RUN-4817', pipeline: 'quarantine-negative-tests', status: 'SUCCEEDED', startedAt: iso(16, 55), durationSec: 33, actor: 'system' },
  ]
}

export function costTrend(): Array<{ ts: string; costEur: number; utilizationPct: number }> {
  const rows: Array<{ ts: string; costEur: number; utilizationPct: number }> = []
  for (let hour = 6; hour <= 18; hour += 1) {
    rows.push({ ts: iso(hour), costEur: Math.round((2.8 + Math.sin(hour / 3) * 0.4) * 100) / 100, utilizationPct: Math.round(38 + Math.sin(hour / 2) * 12) })
  }
  return rows
}

export function workOrders(): WorkOrderRow[] {
  return [
    {
      workOrderId: 'WO-DEMO-LUX-1042',
      site: FIXTURE_SITE,
      assetId: 'LUX-BF-01',
      title: 'Synthetic planned inspection — HEARTH-SECTOR-07',
      reason: 'Predicted RUL below 21-day threshold; verify neighboring sensors and cooling ΔT.',
      status: 'PLANNED_INSPECTION',
      synthetic: true,
      createdBy: 'demo-reliability-engineer',
      detectedAt: iso(18, 0),
    },
    {
      workOrderId: 'WO-DEMO-RHF-1043',
      site: FIXTURE_SITE,
      assetId: 'LUX-RHF-01',
      title: 'Routine reheat zone 03 watch',
      reason: 'Scheduled inspection.',
      status: 'COMPLETED',
      synthetic: true,
      createdBy: 'system',
      detectedAt: iso(9, 0),
    },
  ]
}

export function telemetry(): TelemetryRow[] {
  const rows: TelemetryRow[] = []
  for (let hour = 0; hour < 24; hour += 1) {
    rows.push({
      eventId: `fixture-telemetry-${hour}`,
      eventTs: iso(hour),
      site: FIXTURE_SITE,
      assetId: 'LUX-BF-01',
      sensorId: 'LUX-BF-01-HERE-H07',
      signalCode: 'hearth_refractory_estimate',
      value: Math.round((372 - hour * 0.4) * 10) / 10,
      unit: 'mm',
      quality: 'GOOD',
      scenarioId: 'demo-full',
    })
  }
  return rows
}

export function executiveSites(): Array<{ site: string; energyDeltaPct: number; co2DeltaPct: number; yieldDeltaPct: number; alerts: number }> {
  return [
    { site: 'Moselle (LU)', energyDeltaPct: -14.2, co2DeltaPct: -22.4, yieldDeltaPct: 8.1, alerts: 3 },
    { site: 'Bremen (DE)', energyDeltaPct: -11.8, co2DeltaPct: -18.6, yieldDeltaPct: 6.4, alerts: 2 },
    { site: 'Ghent (BE)', energyDeltaPct: -13.1, co2DeltaPct: -20.2, yieldDeltaPct: 7.2, alerts: 1 },
    { site: 'Bilbao (ES)', energyDeltaPct: -12.5, co2DeltaPct: -19.4, yieldDeltaPct: 7.9, alerts: 2 },
  ]
}
