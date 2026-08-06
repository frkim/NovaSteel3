import { vi } from 'vitest'

/**
 * Minimal fake MediaRecorder + getUserMedia so the recorder state machine can
 * be exercised under jsdom. `emitData`/`triggerStop` let a test drive the
 * lifecycle deterministically.
 */
export class FakeMediaRecorder {
  static instances: FakeMediaRecorder[] = []
  static isTypeSupported = vi.fn(() => true)

  state: 'inactive' | 'recording' | 'paused' = 'inactive'
  ondataavailable: ((event: { data: Blob }) => void) | null = null
  onstop: (() => void) | null = null
  mimeType: string

  constructor(_stream: MediaStream, options?: { mimeType?: string }) {
    this.mimeType = options?.mimeType ?? 'audio/webm'
    FakeMediaRecorder.instances.push(this)
  }

  start(): void {
    this.state = 'recording'
  }

  pause(): void {
    this.state = 'paused'
  }

  resume(): void {
    this.state = 'recording'
  }

  stop(): void {
    this.state = 'inactive'
    this.ondataavailable?.({ data: new Blob(['audio-bytes'], { type: this.mimeType }) })
    this.onstop?.()
  }
}

export interface MediaMocks {
  getUserMedia: ReturnType<typeof vi.fn>
  restore: () => void
}

export function installMediaMocks(options: { deny?: boolean; noMic?: boolean } = {}): MediaMocks {
  const tracks = [{ stop: vi.fn() }]
  const stream = { getTracks: () => tracks } as unknown as MediaStream

  const getUserMedia = vi.fn(() => {
    if (options.deny) {
      return Promise.reject(new DOMException('denied', 'NotAllowedError'))
    }
    if (options.noMic) {
      return Promise.reject(new DOMException('no device', 'NotFoundError'))
    }
    return Promise.resolve(stream)
  })

  const originalMediaDevices = navigator.mediaDevices
  const originalRecorder = (globalThis as { MediaRecorder?: unknown }).MediaRecorder
  const originalCreateObjectURL = URL.createObjectURL
  const originalRevokeObjectURL = URL.revokeObjectURL

  Object.defineProperty(navigator, 'mediaDevices', {
    configurable: true,
    value: { getUserMedia },
  })
  ;(globalThis as { MediaRecorder?: unknown }).MediaRecorder = FakeMediaRecorder as unknown
  URL.createObjectURL = vi.fn(() => 'blob:fake-url') as unknown as typeof URL.createObjectURL
  URL.revokeObjectURL = vi.fn() as unknown as typeof URL.revokeObjectURL

  FakeMediaRecorder.instances = []

  return {
    getUserMedia,
    restore: () => {
      Object.defineProperty(navigator, 'mediaDevices', {
        configurable: true,
        value: originalMediaDevices,
      })
      ;(globalThis as { MediaRecorder?: unknown }).MediaRecorder = originalRecorder
      URL.createObjectURL = originalCreateObjectURL
      URL.revokeObjectURL = originalRevokeObjectURL
    },
  }
}

export function removeMediaSupport(): () => void {
  const originalMediaDevices = navigator.mediaDevices
  const originalRecorder = (globalThis as { MediaRecorder?: unknown }).MediaRecorder
  Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: undefined })
  ;(globalThis as { MediaRecorder?: unknown }).MediaRecorder = undefined
  return () => {
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: originalMediaDevices })
    ;(globalThis as { MediaRecorder?: unknown }).MediaRecorder = originalRecorder
  }
}
