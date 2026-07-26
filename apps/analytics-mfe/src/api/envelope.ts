/** Response envelope shapes owned by the BFF v1 contract (§16 UX spec). */

export interface SingleEnvelope<T> {
  data: T
  asOf: string
  correlationId: string
}

export interface TableEnvelope<T> {
  items: T[]
  total: number
  page: number
  size: number
  asOf: string
  correlationId: string
}

export interface ApiErrorEnvelope {
  code: string
  message: string
  correlationId: string
  retryable?: boolean
}

/** Confidence band shared by AI-derived payloads (`{ p10, p50, p90 }`). */
export interface ConfidenceBand {
  p10: number
  p50: number
  p90: number
}

export interface Driver {
  name: string
  contribution: number
}

/** Normalized error thrown by the data client for STATE-ERROR surfaces. */
export class DataClientError extends Error {
  readonly code: string
  readonly correlationId: string
  readonly retryable: boolean
  readonly status: number

  constructor(params: {
    code: string
    message: string
    correlationId?: string
    retryable?: boolean
    status?: number
  }) {
    super(params.message)
    this.name = 'DataClientError'
    this.code = params.code
    this.correlationId = params.correlationId ?? 'local'
    this.retryable = params.retryable ?? false
    this.status = params.status ?? 0
  }
}
