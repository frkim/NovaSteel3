/** Response envelope shapes owned by the BFF v1 contract (shared with analytics-mfe). */

export interface SingleEnvelope<T> {
  data: T
  asOf?: string
  correlationId?: string
}

export interface ApiErrorEnvelope {
  code: string
  message: string
  correlationId?: string
  retryable?: boolean
}

/** Normalized error thrown by the capture client for error surfaces. */
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
