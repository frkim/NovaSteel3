import type { ShellContext } from '../types'
import { DEMO_PLANT, demoHeaders, fixturesOnly, resolveBffBaseUrl, siteToPlant } from '../config'
import type {
  AlertEvent,
  AlertRow,
  AuditRow,
  CapacityStatus,
  CapacityTransition,
  CommandSummary,
  DataSource,
  EmissionRow,
  EnergyIntervalRow,
  EnergyRecommendation,
  FurnaceRow,
  Genealogy,
  Identity,
  LiningForecast,
  ProcedureRow,
  QualityBatchRow,
  QualityWhatIf,
  SustainabilitySummary,
  TelemetryRow,
  WorkOrderRow,
} from './domain'
import type { SingleEnvelope, TableEnvelope } from './envelope'
import { buildTableQuery, HttpClient } from './httpClient'
import * as fixtures from './fixtures'

export interface Loaded<T> {
  value: T
  source: DataSource
  asOf: string
}

function loaded<T>(value: T, source: DataSource, asOf: string): Loaded<T> {
  return { value, source, asOf }
}

const FULL_PAGE = 200

function stringValue(value: unknown): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined
}

export function alertRowsFromEvents(events: AlertEvent[]): AlertRow[] {
  const alerts = new Map<string, AlertRow>()
  for (const event of events) {
    const data = event.data
    const alertId = stringValue(data.alertId)
    if (!alertId) {
      continue
    }

    const current = alerts.get(alertId)
    if (current) {
      alerts.set(alertId, {
        ...current,
        status: stringValue(data.status) ?? current.status,
        updatedAt: stringValue(data.updatedAt) ?? current.updatedAt,
        workOrderId: stringValue(data.workOrderId) ?? current.workOrderId,
        correlationId: stringValue(data.correlationId) ?? current.correlationId,
      })
      continue
    }

    const site = stringValue(data.site)
    const assetId = stringValue(data.assetId)
    const severity = stringValue(data.severity)
    const status = stringValue(data.status)
    const message = stringValue(data.message)
    const createdAt = stringValue(data.createdAt)
    if (!site || !assetId || !severity || !status || !message || !createdAt) {
      continue
    }
    alerts.set(alertId, {
      alertId,
      site,
      assetId,
      componentId: stringValue(data.componentId),
      severity,
      status,
      message,
      confidence: typeof data.confidence === 'number' ? data.confidence : undefined,
      createdAt,
      updatedAt: stringValue(data.updatedAt),
      workOrderId: stringValue(data.workOrderId),
      correlationId: stringValue(data.correlationId),
      sourceRef: stringValue(data.sourceRef),
    })
  }
  return [...alerts.values()]
}

export function energySimulationBody(constraints: Record<string, number>) {
  return {
    site: DEMO_PLANT,
    horizonHours: 24,
    scenario: 'demo-full',
    constraints,
  }
}

export class DataClient {
  private readonly http: HttpClient | null
  private readonly fixturesOnly: boolean
  private readonly context: ShellContext

  constructor(context: ShellContext) {
    this.context = context
    const baseUrl = resolveBffBaseUrl(context)
    this.fixturesOnly = fixturesOnly()
    this.http = this.fixturesOnly
      ? null
      : new HttpClient({ baseUrl, headers: demoHeaders(context) })
  }

  /** Resolved BFF plant id for the currently selected site. */
  private get activePlant(): string {
    return siteToPlant(this.context.site)
  }

  /** True when the client is configured to never contact a live BFF. */
  get isOffline(): boolean {
    return this.http === null
  }

  private async single<T>(path: string, fallback: () => T): Promise<Loaded<T>> {
    if (!this.http) {
      return loaded(fallback(), 'fixture', fixtures.FIXTURE_AS_OF)
    }
    try {
      const envelope = await this.http.getSingle<T>(path)
      return loaded(envelope.data, 'bff', envelope.asOf)
    } catch {
      return loaded(fallback(), 'fixture', fixtures.FIXTURE_AS_OF)
    }
  }

  private async table<T>(path: string, fallback: () => T[]): Promise<Loaded<T[]>> {
    if (!this.http) {
      return loaded(fallback(), 'fixture', fixtures.FIXTURE_AS_OF)
    }
    try {
      const envelope: TableEnvelope<T> = await this.http.getTable<T>(path)
      return loaded(envelope.items, 'bff', envelope.asOf)
    } catch {
      return loaded(fallback(), 'fixture', fixtures.FIXTURE_AS_OF)
    }
  }

  getIdentity(): Promise<Loaded<Identity | null>> {
    return this.single<Identity | null>('/v1/me', () => null)
  }

  getCommandSummary(site?: string): Promise<Loaded<CommandSummary>> {
    return this.single<CommandSummary>(
      `/v1/command-center/summary${buildTableQuery({ site: site ?? this.activePlant })}`,
      fixtures.commandSummary,
    )
  }

  getFurnaces(): Promise<Loaded<FurnaceRow[]>> {
    return this.table<FurnaceRow>(
      `/v1/furnaces${buildTableQuery({ site: this.activePlant, size: FULL_PAGE })}`,
      fixtures.furnaces,
    )
  }

  getLiningForecast(assetId: string): Promise<Loaded<LiningForecast>> {
    return this.single<LiningForecast>(
      `/v1/furnaces/${encodeURIComponent(assetId)}/lining-forecast`,
      fixtures.liningForecast,
    )
  }

  getTelemetry(): Promise<Loaded<TelemetryRow[]>> {
    return this.table<TelemetryRow>(
      `/v1/telemetry${buildTableQuery({ site: this.activePlant, size: FULL_PAGE })}`,
      fixtures.telemetry,
    )
  }

  getEnergyIntervals(): Promise<Loaded<EnergyIntervalRow[]>> {
    return this.table<EnergyIntervalRow>(
      `/v1/energy/intervals${buildTableQuery({ site: this.activePlant, size: FULL_PAGE, sort: ['intervalStart:asc'] })}`,
      fixtures.energyIntervals,
    )
  }

  async simulateEnergy(constraints: Record<string, number>): Promise<Loaded<EnergyRecommendation>> {
    if (!this.http) {
      return loaded(fixtures.energyRecommendation(), 'fixture', fixtures.FIXTURE_AS_OF)
    }
    try {
      const envelope = await this.http.post<SingleEnvelope<EnergyRecommendation>>(
        '/v1/energy/schedules:simulate',
        energySimulationBody(constraints),
      )
      return loaded(envelope.data, 'bff', envelope.asOf)
    } catch {
      return loaded(fixtures.energyRecommendation(), 'fixture', fixtures.FIXTURE_AS_OF)
    }
  }

  getQualityBatches(): Promise<Loaded<QualityBatchRow[]>> {
    return this.table<QualityBatchRow>(
      `/v1/quality/batches${buildTableQuery({ site: this.activePlant, size: FULL_PAGE })}`,
      fixtures.qualityBatches,
    )
  }

  getGenealogy(batchId: string): Promise<Loaded<Genealogy>> {
    return this.single<Genealogy>(
      `/v1/quality/batches/${encodeURIComponent(batchId)}/genealogy`,
      () => fixtures.genealogy(batchId),
    )
  }

  async qualityWhatIf(
    batchId: string,
    adjustments: Record<string, number>,
  ): Promise<Loaded<QualityWhatIf>> {
    if (this.http) {
      try {
        const envelope = await this.http.post<SingleEnvelope<QualityWhatIf>>('/v1/quality/what-if', {
          batchId,
          adjustments,
        })
        return loaded(envelope.data, 'bff', envelope.asOf)
      } catch {
        // fall through to local model
      }
    }
    return loaded(localWhatIf(batchId, adjustments), 'fixture', fixtures.FIXTURE_AS_OF)
  }

  getEmissions(): Promise<Loaded<EmissionRow[]>> {
    return this.table<EmissionRow>(
      `/v1/sustainability/emissions${buildTableQuery({ site: this.activePlant, size: FULL_PAGE, sort: ['eventTs:asc'] })}`,
      fixtures.emissions,
    )
  }

  getSustainabilitySummary(): Promise<Loaded<SustainabilitySummary>> {
    return this.single<SustainabilitySummary>(
      `/v1/sustainability/summary${buildTableQuery({ site: this.activePlant })}`,
      fixtures.sustainabilitySummary,
    )
  }

  getProcedures(status?: string): Promise<Loaded<ProcedureRow[]>> {
    const query = status ? `?status=${encodeURIComponent(status)}` : ''
    return this.table<ProcedureRow>(`/v1/knowledge/procedures${query}`, () =>
      status ? fixtures.procedures().filter((row) => row.status === status) : fixtures.procedures(),
    )
  }

  searchKnowledge(q: string): Promise<Loaded<ProcedureRow[]>> {
    return this.table<ProcedureRow>(`/v1/knowledge/search?q=${encodeURIComponent(q)}`, () => {
      const needle = q.trim().toLowerCase()
      if (!needle) {
        return fixtures.procedures()
      }
      return fixtures
        .procedures()
        .filter((row) => JSON.stringify(row).toLowerCase().includes(needle))
    })
  }

  getAudit(domain?: string): Promise<Loaded<AuditRow[]>> {
    const query = domain ? `?domain=${encodeURIComponent(domain)}` : ''
    return this.table<AuditRow>(`/v1/audit/decisions${query}`, () =>
      domain ? fixtures.auditDecisions().filter((row) => row.domain === domain) : fixtures.auditDecisions(),
    )
  }

  getCapacity(): Promise<Loaded<CapacityStatus>> {
    return this.single<CapacityStatus>('/v1/platform/capacity', fixtures.capacityStatus)
  }

  getWorkOrders(): Promise<Loaded<WorkOrderRow[]>> {
    // No list route exists; the offline fixture supplies the synthetic set.
    return Promise.resolve(loaded(fixtures.workOrders(), this.http ? 'bff' : 'fixture', fixtures.FIXTURE_AS_OF))
  }

  /** Poll the alert buffer; falls back to fixture alerts as SSE-like events. */
  async pollAlerts(since?: string): Promise<Loaded<AlertEvent[]>> {
    if (!this.http) {
      return loaded(
        fixtures.alerts().map((alert) => ({ id: alert.alertId, type: 'alert.created', data: alert as unknown as Record<string, unknown> })),
        'fixture',
        fixtures.FIXTURE_AS_OF,
      )
    }
    try {
      const query = since ? `?since=${encodeURIComponent(since)}` : ''
      const payload = await this.http.request<{ events: AlertEvent[]; asOf: string }>(
        `/v1/realtime/alerts:poll${query}`,
      )
      return loaded(payload.events ?? [], 'bff', payload.asOf)
    } catch {
      return loaded(
        fixtures.alerts().map((alert) => ({ id: alert.alertId, type: 'alert.created', data: alert as unknown as Record<string, unknown> })),
        'fixture',
        fixtures.FIXTURE_AS_OF,
      )
    }
  }

  getAlerts(): Promise<Loaded<AlertRow[]>> {
    // Derived from the poll buffer or fixture set for the alert center table.
    return this.pollAlerts().then((result) => ({
      value: alertRowsFromEvents(result.value),
      source: result.source,
      asOf: result.asOf,
    }))
  }

  capacityTransitions(): CapacityTransition[] {
    return fixtures.capacityTransitions()
  }
}

/** Local mirror of the scoring worker's bounded quality what-if. */
export function localWhatIf(
  batchId: string,
  adjustments: Record<string, number>,
): QualityWhatIf {
  const batch = fixtures.qualityBatches().find((row) => row.batchId === batchId) ?? fixtures.qualityBatches()[0]
  const bias = Math.abs(batch.coilingTempBiasC)
  const currentYield = bias < 4 ? 0.95 : Math.max(0.88, 0.95 - bias * 0.004)
  const correction = Math.abs(adjustments.coilingTempDeltaC ?? 0) * 0.00875
  const forceCorrection = Math.abs(adjustments.forceBalanceDeltaPct ?? 0) * 0.002
  const proposedYield = Math.min(0.95, currentYield + correction + forceCorrection)
  const proposedPct = Math.round(proposedYield * 10000) / 100
  return {
    value: proposedPct,
    unit: '%',
    confidence: {
      p10: Math.round((proposedPct - 3) * 100) / 100,
      p50: proposedPct,
      p90: Math.round(Math.min(100, proposedPct + 2) * 100) / 100,
    },
    modelVersion: 'quality-yield-gbm/2.1.0-demo',
    scoredAt: fixtures.FIXTURE_AS_OF,
    drivers: [
      { name: 'coiling_temperature_correction', contribution: Math.round(correction * 1000) / 1000 },
      { name: 'force_balance_correction', contribution: Math.round(forceCorrection * 1000) / 1000 },
    ],
    current: { predictedFirstPassYieldPct: Math.round(currentYield * 10000) / 100, riskScore: batch.riskScore },
    proposed: { predictedFirstPassYieldPct: proposedPct },
  }
}
