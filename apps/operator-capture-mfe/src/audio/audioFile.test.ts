import { afterEach, describe, expect, it, vi } from 'vitest'
import { audioExtensionFor, normalizeAudioType, probeAudioDuration } from './audioFile'

describe('normalizeAudioType', () => {
  it('folds platform spellings onto the type the backend accepts', () => {
    expect(normalizeAudioType('audio/x-wav', 'proc.wav')).toBe('audio/wav')
    expect(normalizeAudioType('audio/wave', 'proc.wav')).toBe('audio/wav')
    expect(normalizeAudioType('audio/mp3', 'proc.mp3')).toBe('audio/mpeg')
    expect(normalizeAudioType('audio/x-m4a', 'proc.m4a')).toBe('audio/mp4')
    expect(normalizeAudioType('video/webm', 'proc.webm')).toBe('audio/webm')
  })

  it('ignores codec parameters', () => {
    expect(normalizeAudioType('audio/webm;codecs=opus', 'proc.webm')).toBe('audio/webm')
    expect(normalizeAudioType('audio/ogg; codecs=opus', 'proc.ogg')).toBe('audio/ogg')
  })

  it('falls back to the extension when the browser reports nothing useful', () => {
    // iOS and some Android file providers hand over octet-stream for real audio.
    expect(normalizeAudioType('application/octet-stream', 'shift-handover.m4a')).toBe('audio/mp4')
    expect(normalizeAudioType('', 'shift-handover.WAV')).toBe('audio/wav')
    expect(normalizeAudioType(undefined, 'shift-handover.mp3')).toBe('audio/mpeg')
  })

  it('rejects anything that is not usable audio', () => {
    expect(normalizeAudioType('application/pdf', 'procedure.pdf')).toBeNull()
    expect(normalizeAudioType('image/png', 'photo.png')).toBeNull()
    expect(normalizeAudioType('', 'notes')).toBeNull()
  })
})

describe('audioExtensionFor', () => {
  it('matches the extension to the content type so the multipart part is consistent', () => {
    expect(audioExtensionFor('audio/webm')).toBe('webm')
    expect(audioExtensionFor('audio/wav')).toBe('wav')
    expect(audioExtensionFor('audio/mpeg')).toBe('mp3')
    expect(audioExtensionFor('audio/mp4')).toBe('m4a')
    expect(audioExtensionFor('audio/ogg')).toBe('ogg')
  })

  it('does not claim an audio extension for an unknown type', () => {
    expect(audioExtensionFor('application/pdf')).toBe('bin')
  })
})

describe('probeAudioDuration', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  function stubAudioElement(): Record<string, unknown> {
    const element: Record<string, unknown> = {
      preload: '',
      duration: 0,
      onloadedmetadata: null,
      onerror: null,
      removeAttribute: vi.fn(),
    }
    vi.spyOn(document, 'createElement').mockReturnValue(element as unknown as HTMLElement)
    return element
  }

  it('resolves the metadata duration', async () => {
    const element = stubAudioElement()
    const pending = probeAudioDuration('blob:x')
    element.duration = 67.9
    ;(element.onloadedmetadata as () => void)()
    await expect(pending).resolves.toBeCloseTo(67.9)
  })

  it('resolves 0 rather than rejecting when the browser cannot read the file', async () => {
    // Duration is only review metadata, so an unreadable header must not block an import.
    const element = stubAudioElement()
    const pending = probeAudioDuration('blob:x')
    ;(element.onerror as () => void)()
    await expect(pending).resolves.toBe(0)
  })

  it('resolves 0 for a stream with no finite duration', async () => {
    const element = stubAudioElement()
    const pending = probeAudioDuration('blob:x')
    element.duration = Number.POSITIVE_INFINITY
    ;(element.onloadedmetadata as () => void)()
    await expect(pending).resolves.toBe(0)
  })

  it('gives up after the timeout instead of hanging the import', async () => {
    vi.useFakeTimers()
    stubAudioElement()
    const pending = probeAudioDuration('blob:x', 100)
    vi.advanceTimersByTime(101)
    await expect(pending).resolves.toBe(0)
    vi.useRealTimers()
  })
})
