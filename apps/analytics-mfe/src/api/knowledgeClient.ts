import type { ShellContext } from '../types'
import { demoHeaders, fixturesOnly, resolveBffBaseUrl } from '../config'
import type { ProcedureRow } from './domain'
import type { SingleEnvelope } from './envelope'
import { HttpClient } from './httpClient'
import * as fixtures from './fixtures'

export interface KnowledgeAuditRecord {
  sequence: number
  correlationId: string
  domain: string
  action: string
  entityId: string
  actor: string
  decision: string
  at: string
  recordHash: string
}

export interface CreateInterviewRequest {
  operatorRef: string
  language: string
  consent: {
    granted: boolean
    scope: 'knowledge-capture'
    retentionDays: number
  }
}

export interface CreateInterviewResponse {
  sessionId: string
  consentState: string
  draftProcedureId?: string
  auditRef?: string
}

export interface SeedResponse {
  seeded: number
  procedures: ProcedureRow[]
  auditRef?: string
}

export interface ResetResponse {
  reset: boolean
  procedureCount: number
}

const FIXTURE_AS_OF = fixtures.FIXTURE_AS_OF

export class KnowledgeClient {
  private readonly http: HttpClient | null

  constructor(context: ShellContext) {
    const baseUrl = resolveBffBaseUrl(context)
    this.http = fixturesOnly()
      ? null
      : new HttpClient({ baseUrl, headers: demoHeaders(context) })
  }

  get isOffline(): boolean {
    return this.http === null
  }

  async getProcedures(status?: string): Promise<{ items: ProcedureRow[]; source: 'bff' | 'fixture'; asOf: string }> {
    if (!this.http) {
      const items = status
        ? fixtures.procedures().filter((r) => r.status === status)
        : fixtures.procedures()
      return { items, source: 'fixture', asOf: FIXTURE_AS_OF }
    }
    const query = status ? `?status=${encodeURIComponent(status)}` : ''
    const envelope = await this.http.getTable<ProcedureRow>(`/v1/knowledge/procedures${query}`)
    return { items: envelope.items, source: 'bff', asOf: envelope.asOf }
  }

  async searchProcedures(q: string): Promise<{ items: ProcedureRow[]; source: 'bff' | 'fixture'; asOf: string }> {
    if (!this.http) {
      const needle = q.trim().toLowerCase()
      const items = needle
        ? fixtures.procedures().filter((r) => JSON.stringify(r).toLowerCase().includes(needle))
        : fixtures.procedures()
      return { items, source: 'fixture', asOf: FIXTURE_AS_OF }
    }
    const envelope = await this.http.getTable<ProcedureRow>(`/v1/knowledge/search?q=${encodeURIComponent(q)}`)
    return { items: envelope.items, source: 'bff', asOf: envelope.asOf }
  }

  async getProcedure(procedureId: string): Promise<ProcedureRow> {
    if (!this.http) {
      const found = fixtures.procedures().find((r) => r.procedureId === procedureId)
      if (!found) throw new Error(`Procedure ${procedureId} not found`)
      return found
    }
    const envelope = await this.http.getSingle<ProcedureRow>(`/v1/knowledge/procedures/${encodeURIComponent(procedureId)}`)
    return envelope.data
  }

  async createInterview(req: CreateInterviewRequest): Promise<CreateInterviewResponse> {
    if (!this.http) throw new Error('Cannot create interviews in offline mode')
    const envelope = await this.http.post<SingleEnvelope<CreateInterviewResponse>>(
      '/v1/knowledge/interviews',
      req,
      { 'Idempotency-Key': crypto.randomUUID() },
    )
    return envelope.data
  }

  async submitForReview(procedureId: string): Promise<ProcedureRow> {
    if (!this.http) throw new Error('Cannot submit in offline mode')
    const envelope = await this.http.post<SingleEnvelope<ProcedureRow>>(
      `/v1/knowledge/procedures/${encodeURIComponent(procedureId)}:submit`,
      {},
    )
    return envelope.data
  }

  async approve(procedureId: string, expectedVersion: number): Promise<ProcedureRow> {
    if (!this.http) throw new Error('Cannot approve in offline mode')
    const envelope = await this.http.post<SingleEnvelope<ProcedureRow>>(
      `/v1/knowledge/procedures/${encodeURIComponent(procedureId)}:approve`,
      { expectedVersion },
      { 'Idempotency-Key': crypto.randomUUID() },
    )
    return envelope.data
  }

  async reject(procedureId: string, reason: string): Promise<ProcedureRow> {
    if (!this.http) throw new Error('Cannot reject in offline mode')
    const envelope = await this.http.post<SingleEnvelope<ProcedureRow>>(
      `/v1/knowledge/procedures/${encodeURIComponent(procedureId)}:reject`,
      { reason },
    )
    return envelope.data
  }

  async seedDemo(): Promise<SeedResponse> {
    if (!this.http) throw new Error('Cannot seed in offline mode')
    const envelope = await this.http.post<SingleEnvelope<SeedResponse>>(
      '/v1/knowledge/demo/seed',
      {},
    )
    return envelope.data
  }

  async resetDemo(): Promise<ResetResponse> {
    if (!this.http) throw new Error('Cannot reset in offline mode')
    const envelope = await this.http.post<SingleEnvelope<ResetResponse>>(
      '/v1/knowledge/demo/reset',
      {},
    )
    return envelope.data
  }

  async getAudit(): Promise<KnowledgeAuditRecord[]> {
    if (!this.http) return []
    const envelope = await this.http.getTable<KnowledgeAuditRecord>('/v1/knowledge/audit')
    return envelope.items
  }

  async getTranscript(sessionId: string): Promise<{ status: string; segments?: Array<{ text: string; speaker: string }> }> {
    if (!this.http) {
      return { status: 'COMPLETED', segments: [{ text: 'Synthetic transcript for demo purposes.', speaker: 'operator' }] }
    }
    const envelope = await this.http.getSingle<{ status: string; segments?: Array<{ text: string; speaker: string }> }>(
      `/v1/knowledge/interviews/${encodeURIComponent(sessionId)}/transcript`,
    )
    return envelope.data
  }
}
