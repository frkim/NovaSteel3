import type { ApiErrorEnvelope, SingleEnvelope } from './envelope'
import { DataClientError } from './envelope'

const DEFAULT_TIMEOUT_MS = 12000

function correlationId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `mfe-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export interface UploadOptions {
  onProgress?: (fraction: number) => void
  /** Abort the in-flight upload (cancel button). */
  signal?: AbortSignal
}

export interface HttpClientOptions {
  baseUrl: string
  headers: Record<string, string>
  timeoutMs?: number
}

function parseError(status: number, payload: unknown, cid: string): DataClientError {
  const envelope = (payload ?? {}) as Partial<ApiErrorEnvelope>
  return new DataClientError({
    code: envelope.code ?? `HTTP_${status}`,
    message: envelope.message ?? `Request failed with status ${status}.`,
    correlationId: envelope.correlationId ?? cid,
    retryable: envelope.retryable ?? status >= 500,
    status,
  })
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
        throw parseError(response.status, payload, cid)
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
          ? 'The request timed out before the backend responded.'
          : 'The backend could not be reached from the browser.',
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

  post<T>(path: string, body: unknown, headers: Record<string, string> = {}): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: JSON.stringify(body),
      headers: { 'Content-Type': 'application/json', ...headers },
    })
  }

  /**
   * Multipart upload via XHR so we get real upload-progress events and can
   * cancel mid-flight — `fetch` still cannot report request-body progress.
   */
  postForm<T>(
    path: string,
    form: FormData,
    headers: Record<string, string>,
    options: UploadOptions = {},
  ): Promise<T> {
    const cid = correlationId()
    return new Promise<T>((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', this.url(path))
      xhr.responseType = 'text'
      xhr.timeout = 120000
      xhr.setRequestHeader('Accept', 'application/json')
      xhr.setRequestHeader('X-Correlation-ID', cid)
      for (const [key, value] of Object.entries({ ...this.headers, ...headers })) {
        xhr.setRequestHeader(key, value)
      }

      const onAbort = () => xhr.abort()
      if (options.signal) {
        if (options.signal.aborted) {
          reject(new DataClientError({ code: 'CANCELLED', message: 'Upload cancelled.', correlationId: cid }))
          return
        }
        options.signal.addEventListener('abort', onAbort, { once: true })
      }

      const cleanup = () => options.signal?.removeEventListener('abort', onAbort)

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable && options.onProgress) {
          options.onProgress(event.loaded / event.total)
        }
      }
      xhr.onload = () => {
        cleanup()
        const text = xhr.responseText
        let payload: unknown = null
        try {
          payload = text ? JSON.parse(text) : null
        } catch {
          payload = null
        }
        if (xhr.status >= 200 && xhr.status < 300) {
          options.onProgress?.(1)
          resolve(payload as T)
        } else {
          reject(parseError(xhr.status, payload, cid))
        }
      }
      xhr.onerror = () => {
        cleanup()
        reject(
          new DataClientError({
            code: 'NETWORK_ERROR',
            message: 'The upload could not reach the backend.',
            correlationId: cid,
            retryable: true,
          }),
        )
      }
      xhr.ontimeout = () => {
        cleanup()
        reject(
          new DataClientError({
            code: 'TIMEOUT',
            message: 'The upload timed out.',
            correlationId: cid,
            retryable: true,
          }),
        )
      }
      xhr.onabort = () => {
        cleanup()
        reject(new DataClientError({ code: 'CANCELLED', message: 'Upload cancelled.', correlationId: cid }))
      }

      xhr.send(form)
    })
  }
}
