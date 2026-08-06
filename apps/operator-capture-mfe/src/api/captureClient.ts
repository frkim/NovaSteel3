import { demoHeaders, demoMode, resolveBffBaseUrl } from '../config'
import { audioExtensionFor, MAX_AUDIO_FILE_BYTES } from '../audio/audioFile'
import type { CaptureLanguage } from '../types'
import type { SingleEnvelope } from './envelope'
import { DataClientError } from './envelope'
import { HttpClient, type UploadOptions } from './httpClient'

export const MAX_AUDIO_BYTES = MAX_AUDIO_FILE_BYTES

export interface Consent {
  granted: boolean
  scope: 'knowledge-capture'
  retentionDays: number
}

export interface CreateInterviewRequest {
  operatorRef: string
  language: CaptureLanguage
  consent: Consent
}

export interface CreateInterviewResponse {
  sessionId: string
  consentState: string
  auditRef?: string
}

export interface UploadAudioRequest {
  blob: Blob
  durationSeconds: number
  language: CaptureLanguage
}

export type CaptureStatus = 'PROCESSING' | 'COMPLETED'

export interface UploadAudioResponse {
  sessionId: string
  status: CaptureStatus
  audioRef?: string
  auditRef?: string
}

export interface TranscriptSegment {
  segmentId: string
  speaker: string
  start: number
  end: number
  text: string
  confidence: number
}

export interface TranscriptResponse {
  status: CaptureStatus
  language?: CaptureLanguage
  classification?: string
  segments?: TranscriptSegment[]
}

export interface CreateDraftRequest {
  title: string
  domain: string
}

export interface CreateDraftResponse {
  procedureId: string
  status: string
  auditRef?: string
}

export interface SubmitResponse {
  procedureId?: string
  status: string
}

export interface PollOptions {
  signal?: AbortSignal
  onTick?: (attempt: number, delayMs: number) => void
  maxAttempts?: number
  baseDelayMs?: number
  maxDelayMs?: number
}

function idempotencyKey(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `idem-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

const delay = (ms: number, signal?: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DataClientError({ code: 'CANCELLED', message: 'Polling cancelled.' }))
      return
    }
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort)
      resolve()
    }, ms)
    const onAbort = () => {
      clearTimeout(timer)
      reject(new DataClientError({ code: 'CANCELLED', message: 'Polling cancelled.' }))
    }
    signal?.addEventListener('abort', onAbort, { once: true })
  })

export interface CaptureClientDeps {
  /** Inject an HttpClient (tests) or `null` to force demo mode. */
  http?: HttpClient | null
  locale?: string
}

/**
 * Voice-capture API client. Follows the analytics-mfe `{ data: ... }` envelope
 * and demo-mode short-circuit conventions: when no backend is configured every
 * call resolves against deterministic synthetic data so the flow is demoable
 * end-to-end without a live BFF.
 */
export class CaptureClient {
  private readonly http: HttpClient | null

  constructor(deps: CaptureClientDeps = {}) {
    if (deps.http !== undefined) {
      this.http = deps.http
    } else if (demoMode()) {
      this.http = null
    } else {
      this.http = new HttpClient({
        baseUrl: resolveBffBaseUrl(),
        headers: demoHeaders(deps.locale ?? 'en-LU'),
      })
    }
  }

  get isDemo(): boolean {
    return this.http === null
  }

  async createInterview(req: CreateInterviewRequest): Promise<CreateInterviewResponse> {
    if (!this.http) {
      return {
        sessionId: `demo-session-${Date.now().toString(36)}`,
        consentState: req.consent.granted ? 'GRANTED' : 'DENIED',
        auditRef: 'demo-audit',
      }
    }
    const envelope = await this.http.post<SingleEnvelope<CreateInterviewResponse>>(
      '/v1/knowledge/interviews',
      req,
      { 'Idempotency-Key': idempotencyKey() },
    )
    return envelope.data
  }

  async uploadAudio(
    sessionId: string,
    req: UploadAudioRequest,
    options: UploadOptions = {},
  ): Promise<UploadAudioResponse> {
    if (req.blob.size > MAX_AUDIO_BYTES) {
      throw new DataClientError({
        code: 'PAYLOAD_TOO_LARGE',
        message: 'Recording exceeds the 25 MB limit. Please record a shorter procedure.',
        status: 413,
      })
    }
    if (!this.http) {
      options.onProgress?.(1)
      return { sessionId, status: 'PROCESSING', audioRef: 'demo-audio', auditRef: 'demo-audit' }
    }
    const form = new FormData()
    // Extension must match the blob's content type: the BFF allow-lists the
    // multipart content type, and imported files are not always WebM.
    const filename = `capture-${sessionId}.${audioExtensionFor(req.blob.type)}`
    form.append('file', req.blob, filename)
    form.append('durationSeconds', String(Math.round(req.durationSeconds)))
    form.append('language', req.language)
    const envelope = await this.http.postForm<SingleEnvelope<UploadAudioResponse>>(
      `/v1/knowledge/interviews/${encodeURIComponent(sessionId)}/audio`,
      form,
      {},
      options,
    )
    return envelope.data
  }

  async getTranscript(sessionId: string): Promise<TranscriptResponse> {
    if (!this.http) {
      return {
        status: 'COMPLETED',
        language: 'en',
        classification: 'Continuous Casting',
        segments: [
          {
            segmentId: 'demo-1',
            speaker: 'operator',
            start: 0,
            end: 6.2,
            text: 'First, confirm the tundish level is stable before opening the slide gate.',
            confidence: 0.94,
          },
          {
            segmentId: 'demo-2',
            speaker: 'operator',
            start: 6.2,
            end: 13.8,
            text: 'If the mould level alarm triggers, reduce casting speed in five percent steps.',
            confidence: 0.88,
          },
        ],
      }
    }
    const envelope = await this.http.getSingle<TranscriptResponse>(
      `/v1/knowledge/interviews/${encodeURIComponent(sessionId)}/transcript`,
    )
    return envelope.data
  }

  /**
   * Poll the transcript endpoint with exponential backoff, respecting the 202
   * PROCESSING state, until COMPLETED or the attempt budget is exhausted.
   */
  async pollTranscript(sessionId: string, options: PollOptions = {}): Promise<TranscriptResponse> {
    const maxAttempts = options.maxAttempts ?? 12
    const baseDelayMs = options.baseDelayMs ?? 1500
    const maxDelayMs = options.maxDelayMs ?? 15000
    // First read is immediate; demo mode returns COMPLETED on the first tick.
    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      const transcript = await this.getTranscript(sessionId)
      if (transcript.status === 'COMPLETED') {
        return transcript
      }
      const wait = Math.min(baseDelayMs * 2 ** attempt, maxDelayMs)
      options.onTick?.(attempt + 1, wait)
      await delay(wait, options.signal)
    }
    throw new DataClientError({
      code: 'TRANSCRIPT_TIMEOUT',
      message: 'Transcription is taking longer than expected. Try refreshing shortly.',
      retryable: true,
    })
  }

  async createDraft(sessionId: string, req: CreateDraftRequest): Promise<CreateDraftResponse> {
    if (!this.http) {
      return {
        procedureId: `demo-proc-${Date.now().toString(36)}`,
        status: 'DRAFT',
        auditRef: 'demo-audit',
      }
    }
    const envelope = await this.http.post<SingleEnvelope<CreateDraftResponse>>(
      `/v1/knowledge/interviews/${encodeURIComponent(sessionId)}/draft`,
      req,
      { 'Idempotency-Key': idempotencyKey() },
    )
    return envelope.data
  }

  async submitForReview(procedureId: string): Promise<SubmitResponse> {
    if (!this.http) {
      return { procedureId, status: 'IN_REVIEW' }
    }
    const envelope = await this.http.post<SingleEnvelope<SubmitResponse>>(
      `/v1/knowledge/procedures/${encodeURIComponent(procedureId)}:submit`,
      {},
    )
    return envelope.data
  }
}
