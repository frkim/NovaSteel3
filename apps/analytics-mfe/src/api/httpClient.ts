import type { ApiErrorEnvelope, SingleEnvelope, TableEnvelope } from './envelope'
import { DataClientError } from './envelope'

export interface TableQuery {
  site?: string
  page?: number
  size?: number
  q?: string
  sort?: string[]
  from?: string
  to?: string
  /** Per-column filters serialized as `col:value` (AND across columns). */
  columnFilters?: Record<string, string>
  extra?: Record<string, string>
}

const DEFAULT_TIMEOUT_MS = 9000

export function buildTableQuery(query: TableQuery = {}): string {
  const params = new URLSearchParams()
  if (query.site) {
    params.set('site', query.site)
  }
  if (query.page) {
    params.set('page', String(query.page))
  }
  if (query.size) {
    params.set('size', String(query.size))
  }
  if (query.q && query.q.trim()) {
    params.set('q', query.q.trim())
  }
  for (const sort of query.sort ?? []) {
    params.append('sort', sort)
  }
  if (query.from) {
    params.set('from', query.from)
  }
  if (query.to) {
    params.set('to', query.to)
  }
  for (const [column, value] of Object.entries(query.columnFilters ?? {})) {
    if (value && value.trim()) {
      params.append('filter', `${column}:${value.trim()}`)
    }
  }
  for (const [key, value] of Object.entries(query.extra ?? {})) {
    params.set(key, value)
  }
  const serialized = params.toString()
  return serialized ? `?${serialized}` : ''
}

function correlationId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `mfe-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export interface HttpClientOptions {
  baseUrl: string
  headers: Record<string, string>
  timeoutMs?: number
}

export class HttpClient {
  private readonly baseUrl: string
  private readonly headers: Record<string, string>
  private readonly timeoutMs: number

  constructor(options: HttpClientOptions) {
    this.baseUrl = options.baseUrl
    this.headers = options.headers
    this.timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS
  }

  private url(path: string): string {
    if (/^https?:\/\//i.test(path)) {
      return path
    }
    return `${this.baseUrl}${path}`
  }

  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), this.timeoutMs)
    const cid = correlationId()
    try {
      const response = await fetch(this.url(path), {
        ...init,
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          'X-Correlation-ID': cid,
          ...this.headers,
          ...(init.headers ?? {}),
        },
      })
      const text = await response.text()
      const payload = text ? (JSON.parse(text) as unknown) : null
      if (!response.ok) {
        const envelope = (payload ?? {}) as Partial<ApiErrorEnvelope>
        throw new DataClientError({
          code: envelope.code ?? `HTTP_${response.status}`,
          message: envelope.message ?? `Request failed with status ${response.status}.`,
          correlationId: envelope.correlationId ?? cid,
          retryable: envelope.retryable ?? response.status >= 500,
          status: response.status,
        })
      }
      return payload as T
    } catch (error) {
      if (error instanceof DataClientError) {
        throw error
      }
      const aborted = error instanceof DOMException && error.name === 'AbortError'
      throw new DataClientError({
        code: aborted ? 'TIMEOUT' : 'NETWORK_ERROR',
        message: aborted
          ? 'The request timed out before the BFF responded.'
          : 'The BFF could not be reached from the browser.',
        correlationId: cid,
        retryable: true,
      })
    } finally {
      clearTimeout(timer)
    }
  }

  getSingle<T>(path: string): Promise<SingleEnvelope<T>> {
    return this.request<SingleEnvelope<T>>(path)
  }

  getTable<T>(path: string): Promise<TableEnvelope<T>> {
    return this.request<TableEnvelope<T>>(path)
  }

  post<T>(path: string, body: unknown, headers: Record<string, string> = {}): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: JSON.stringify(body),
      headers: { 'Content-Type': 'application/json', ...headers },
    })
  }
}
