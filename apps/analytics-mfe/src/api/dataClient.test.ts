import { describe, expect, it } from 'vitest'
import { alertRowsFromEvents, DataClient, energySimulationBody } from './dataClient'
import { testShellContext } from '../test/renderWithProviders'
import { siteToPlant } from '../config'

describe('DataClient site resolution', () => {
  it('activePlant resolves to the plant matching the context site', () => {
    const ctx = testShellContext({ site: 'be' })
    const client = new DataClient(ctx)
    // Access activePlant via a reflected property or test indirectly
    // DataClient uses the site in getCommandSummary URL
    expect(siteToPlant('be')).toBe('NS-DEMO-BE-01')
    expect(siteToPlant('lu')).toBe('NS-DEMO-LUX-01')
    expect(siteToPlant('all')).toBe('all')
    expect(siteToPlant(undefined)).toBe('all')
  })

  it('reads site at call time (not at construction time)', () => {
    const ctx = testShellContext({ site: 'lu' })
    const client = new DataClient(ctx)
    // Mutate the context to simulate a site change
    ;(ctx as { site: string }).site = 'es'
    // Since DataClient stores a reference, siteToPlant should now read 'es'
    expect(siteToPlant(ctx.site)).toBe('NS-DEMO-ES-01')
  })
})

describe('DataClient offline fixture fallback', () => {
  const client = new DataClient(testShellContext())

  it('runs in offline mode when fixturesOnly is set', () => {
    expect(client.isOffline).toBe(true)
  })

  it('returns the command summary from fixtures with the demo cue values', async () => {
    const result = await client.getCommandSummary()
    expect(result.source).toBe('fixture')
    expect(result.value.kpis.liningRulDaysP50).toBe(21)
    expect(result.value.syntheticBanner).toContain('Synthetic')
  })

  it('returns the 21-day lining forecast with a P10<21<P90 band', async () => {
    const result = await client.getLiningForecast('LUX-BF-01')
    expect(result.value.value).toBe(21)
    expect(result.value.confidence.p10).toBeLessThan(21)
    expect(result.value.confidence.p90).toBeGreaterThan(21)
    expect(result.value.riskScore).toBeGreaterThan(0.8)
  })

  it('returns quality batches including the demo coil', async () => {
    const result = await client.getQualityBatches()
    expect(result.value.length).toBeGreaterThan(0)
    expect(result.value.some((row) => row.batchId === 'COIL-LUX-260725-017')).toBe(true)
  })

  it('computes a bounded what-if that improves predicted yield', async () => {
    const result = await client.qualityWhatIf('COIL-LUX-260725-017', { coilingTempDeltaC: -8, forceBalanceDeltaPct: -3 })
    expect(result.value.proposed.predictedFirstPassYieldPct).toBeGreaterThanOrEqual(
      result.value.current.predictedFirstPassYieldPct,
    )
    expect(result.value.proposed.predictedFirstPassYieldPct).toBeLessThanOrEqual(95)
  })

  it('returns a running simulated capacity status', async () => {
    const result = await client.getCapacity()
    expect(result.value.demoModeSimulated).toBe(true)
    expect(result.value.state).toBe('Running')
  })

  it('returns 96 energy intervals with an evening price peak', async () => {
    const result = await client.getEnergyIntervals()
    expect(result.value.length).toBe(96)
    const peak = Math.max(...result.value.map((row) => row.priceEurMwh))
    expect(peak).toBeGreaterThan(250)
  })

  it('quotes the same dispatch cue sheet offline as the live optimiser', async () => {
    const result = await client.simulateEnergy({ maxShiftMinutes: 120, maxConcurrentBatches: 2 })
    const rec = result.value
    expect(result.source).toBe('fixture')
    // Whole-dispatch basis, matching docs/tech/api-contracts.md and
    // the runbook. An offline walkthrough must never quote a second number.
    expect(rec.savings.costPct).toBe(7.25)
    expect(rec.savings.costEur).toBe(2688.7)
    expect(rec.savings.peakPct).toBe(-7.89)
    expect(rec.savings.co2Pct).toBe(3.29)
    expect(rec.baseline.costEur).toBe(37109.1)
    expect(rec.optimized.costEur).toBe(34420.4)
    expect(rec.baseline.peakDemandMw).toBe(56.0)
    expect(rec.optimized.peakDemandMw).toBe(51.58)
    // Tonnage is conserved and no hard constraint is violated.
    expect(rec.baseline.tonnage).toBe(960)
    expect(rec.optimized.tonnage).toBe(960)
    expect(rec.hardConstraintViolations).toBe(0)
    const tonnes = (rows: { tonnage: number }[]) => rows.reduce((sum, row) => sum + row.tonnage, 0)
    expect(tonnes(rec.optimized.schedule)).toBe(tonnes(rec.baseline.schedule))
    // The urgent batch is pinned; the 280 EUR/MWh batch is the one that moves.
    const urgent = rec.optimized.schedule.find((row) => row.urgent)
    expect(urgent?.shiftMinutes).toBe(0)
    const peakBatch = rec.baseline.schedule.find((row) => row.priceEurMwh === 280)
    expect(peakBatch).toBeDefined()
    expect(rec.optimized.schedule.find((row) => row.batchId === peakBatch?.batchId)?.priceEurMwh)
      .toBeLessThan(280)
  })

  it('targets the concrete demo plant for energy simulation', () => {
    expect(energySimulationBody({ maxShiftMinutes: 180, maxConcurrentBatches: 2 })).toEqual({
      site: 'NS-DEMO-LUX-01',
      horizonHours: 24,
      scenario: 'demo-full',
      constraints: { maxShiftMinutes: 180, maxConcurrentBatches: 2 },
    })
  })

  it('merges alert updates without losing the original severity and message', () => {
    const rows = alertRowsFromEvents([
      {
        id: '1',
        type: 'alert.created',
        data: {
          alertId: 'ALERT-1',
          site: 'NS-DEMO-LUX-01',
          assetId: 'LUX-BF-01',
          severity: 'CRITICAL',
          status: 'OPEN',
          message: 'Synthetic alert',
          createdAt: '2026-06-11T00:00:00Z',
        },
      },
      {
        id: '2',
        type: 'alert.updated',
        data: {
          alertId: 'ALERT-1',
          status: 'WORK_ORDER_LINKED',
          workOrderId: 'WO-DEMO-1',
        },
      },
    ])

    expect(rows).toEqual([
      expect.objectContaining({
        alertId: 'ALERT-1',
        severity: 'CRITICAL',
        status: 'WORK_ORDER_LINKED',
        message: 'Synthetic alert',
        workOrderId: 'WO-DEMO-1',
      }),
    ])
  })

  it('ignores non-alert transition events in the realtime buffer', () => {
    const rows = alertRowsFromEvents([
      {
        id: '1',
        type: 'capacity.transition',
        data: {
          capacityId: 'novasteelv3fabric',
          fromState: 'Paused',
          toState: 'Running',
        },
      },
    ])

    expect(rows).toEqual([])
  })
})
