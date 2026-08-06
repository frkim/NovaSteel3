import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { CaptureClient } from './captureClient'
import { HttpClient } from './httpClient'
import { DataClientError } from './envelope'

function jsonResponse(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: () => Promise.resolve(JSON.stringify(body)),
  } as unknown as Response
}

function makeClient(): CaptureClient {
  return new CaptureClient({ http: new HttpClient({ baseUrl: '', headers: {} }) })
}

/** Minimal fake XHR to drive multipart upload results deterministically. */
class FakeXHR {
  static queue: { status: number; body: unknown }[] = []
  static lastForm: FormData | null = null
  static lastUrl = ''

  upload = { onprogress: null as ((e: ProgressEvent) => void) | null }
  onload: (() => void) | null = null
  onerror: (() => void) | null = null
  ontimeout: (() => void) | null = null
  onabort: (() => void) | null = null
  status = 0
  responseText = ''
  responseType = ''
  timeout = 0
  private url = ''

  open(_method: string, url: string): void {
    this.url = url
    FakeXHR.lastUrl = url
  }
  setRequestHeader(): void {}
  send(form: FormData): void {
    FakeXHR.lastForm = form
    const next = FakeXHR.queue.shift() ?? { status: 500, body: {} }
    // Emit a progress tick then complete.
    this.upload.onprogress?.({ lengthComputable: true, loaded: 5, total: 10 } as ProgressEvent)
    this.status = next.status
    this.responseText = JSON.stringify(next.body)
    queueMicrotask(() => this.onload?.())
  }
  abort(): void {
    this.onabort?.()
  }
}

describe('CaptureClient', () => {
  beforeEach(() => {
    FakeXHR.queue = []
    FakeXHR.lastForm = null
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('createInterview posts with an Idempotency-Key and returns the envelope data', async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(jsonResponse(201, { data: { sessionId: 's1', consentState: 'GRANTED', auditRef: 'a1' } })),
    )
    vi.stubGlobal('fetch', fetchMock)

    const res = await makeClient().createInterview({
      operatorRef: 'op-1',
      language: 'en',
      consent: { granted: true, scope: 'knowledge-capture', retentionDays: 365 },
    })

    expect(res.sessionId).toBe('s1')
    const init = fetchMock.mock.calls[0][1] as RequestInit
    const headers = init.headers as Record<string, string>
    expect(headers['Idempotency-Key']).toBeTruthy()
    expect(init.method).toBe('POST')
  })

  describe('uploadAudio', () => {
    it('rejects a blob larger than 25 MB with a 413 before hitting the network', async () => {
      const big = { size: 26 * 1024 * 1024 } as Blob
      await expect(
        makeClient().uploadAudio('s1', { blob: big, durationSeconds: 5, language: 'en' }),
      ).rejects.toMatchObject({ status: 413, code: 'PAYLOAD_TOO_LARGE' })
    })

    it('maps a 403 consent rejection to a DataClientError', async () => {
      vi.stubGlobal('XMLHttpRequest', FakeXHR as unknown as typeof XMLHttpRequest)
      FakeXHR.queue = [{ status: 403, body: { code: 'CONSENT_REQUIRED', message: 'no consent' } }]
      const blob = new Blob(['x'], { type: 'audio/webm' })

      await expect(
        makeClient().uploadAudio('s1', { blob, durationSeconds: 5, language: 'en' }),
      ).rejects.toMatchObject({ status: 403 })
    })

    it('accepts a 202 PROCESSING response and reports progress', async () => {
      vi.stubGlobal('XMLHttpRequest', FakeXHR as unknown as typeof XMLHttpRequest)
      FakeXHR.queue = [{ status: 202, body: { data: { sessionId: 's1', status: 'PROCESSING', audioRef: 'r1' } } }]
      const blob = new Blob(['x'], { type: 'audio/webm' })
      const onProgress = vi.fn()

      const res = await makeClient().uploadAudio(
        's1',
        { blob, durationSeconds: 7, language: 'de' },
        { onProgress },
      )

      expect(res.status).toBe('PROCESSING')
      expect(onProgress).toHaveBeenCalled()
      const form = FakeXHR.lastForm as unknown as FormData
      expect(form.get('language')).toBe('de')
      expect(form.get('durationSeconds')).toBe('7')
    })
  })

  describe('pollTranscript', () => {
    it('keeps polling while 202 PROCESSING and resolves on 200 COMPLETED', async () => {
      const fetchMock = vi
        .fn()
        .mockResolvedValueOnce(jsonResponse(202, { data: { status: 'PROCESSING' } }))
        .mockResolvedValueOnce(
          jsonResponse(200, { data: { status: 'COMPLETED', segments: [{ segmentId: 'x', speaker: 'operator', start: 0, end: 1, text: 'hi', confidence: 0.9 }] } }),
        )
      vi.stubGlobal('fetch', fetchMock)

      const res = await makeClient().pollTranscript('s1', { baseDelayMs: 1, maxDelayMs: 2 })

      expect(res.status).toBe('COMPLETED')
      expect(res.segments).toHaveLength(1)
      expect(fetchMock).toHaveBeenCalledTimes(2)
    })

    it('throws TRANSCRIPT_TIMEOUT when it never completes', async () => {
      const fetchMock = vi.fn(() => Promise.resolve(jsonResponse(202, { data: { status: 'PROCESSING' } })))
      vi.stubGlobal('fetch', fetchMock)

      await expect(
        makeClient().pollTranscript('s1', { maxAttempts: 3, baseDelayMs: 1, maxDelayMs: 1 }),
      ).rejects.toBeInstanceOf(DataClientError)
    })
  })

  it('createDraft posts to the draft endpoint with an Idempotency-Key', async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(jsonResponse(201, { data: { procedureId: 'p1', status: 'DRAFT', auditRef: 'a1' } })),
    )
    vi.stubGlobal('fetch', fetchMock)

    const res = await makeClient().createDraft('s1', { title: 'Tap the furnace', domain: 'Blast Furnace' })

    expect(res.procedureId).toBe('p1')
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain('/v1/knowledge/interviews/s1/draft')
    expect((init.headers as Record<string, string>)['Idempotency-Key']).toBeTruthy()
  })

  it('submitForReview posts to the :submit action', async () => {
    const fetchMock = vi.fn(() => Promise.resolve(jsonResponse(200, { data: { procedureId: 'p1', status: 'IN_REVIEW' } })))
    vi.stubGlobal('fetch', fetchMock)

    const res = await makeClient().submitForReview('p1')

    expect(res.status).toBe('IN_REVIEW')
    const [url] = fetchMock.mock.calls[0] as [string]
    expect(url).toContain('/v1/knowledge/procedures/p1:submit')
  })
})
