import { describe, expect, it, afterEach, vi } from 'vitest'
import { act, renderHook, waitFor } from '@testing-library/react'
import { useRecorder } from './useRecorder'
import { FakeMediaRecorder, installMediaMocks, removeMediaSupport } from '../test/mediaMocks'

// jsdom never loads media, so the real probe would sit on its timeout.
vi.mock('../audio/audioFile', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../audio/audioFile')>()),
  probeAudioDuration: vi.fn(async () => 67.9),
}))

function audioFile(name: string, type: string, size = 1024): File {
  const file = new File(['x'], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

describe('useRecorder', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('reports unsupported when the browser has no MediaRecorder', () => {
    const restore = removeMediaSupport()
    const { result } = renderHook(() => useRecorder())
    expect(result.current.state).toBe('unsupported')
    expect(result.current.isSupported).toBe(false)
    restore()
  })

  it('walks idle -> recording -> paused -> recording -> stopped and yields a blob', async () => {
    const mocks = installMediaMocks()
    const { result } = renderHook(() => useRecorder())

    expect(result.current.state).toBe('idle')

    await act(async () => {
      await result.current.start()
    })
    expect(result.current.state).toBe('recording')
    expect(mocks.getUserMedia).toHaveBeenCalled()

    act(() => result.current.pause())
    expect(result.current.state).toBe('paused')

    act(() => result.current.resume())
    expect(result.current.state).toBe('recording')

    act(() => result.current.stop())
    await waitFor(() => expect(result.current.state).toBe('stopped'))
    expect(result.current.result?.blob).toBeInstanceOf(Blob)
    expect(result.current.result?.blob.size).toBeGreaterThan(0)

    act(() => result.current.reset())
    expect(result.current.state).toBe('idle')
    expect(result.current.result).toBeNull()

    mocks.restore()
  })

  it('classifies a denied permission as an error', async () => {
    const mocks = installMediaMocks({ deny: true })
    const { result } = renderHook(() => useRecorder())

    await act(async () => {
      await result.current.start()
    })

    expect(result.current.state).toBe('error')
    expect(result.current.error?.kind).toBe('permission')
    mocks.restore()
  })

  it('classifies a missing microphone as a no-mic error', async () => {
    const mocks = installMediaMocks({ noMic: true })
    const { result } = renderHook(() => useRecorder())

    await act(async () => {
      await result.current.start()
    })

    expect(result.current.state).toBe('error')
    expect(result.current.error?.kind).toBe('no-mic')
    mocks.restore()
  })

  it('auto-pauses when the tab is backgrounded mid-recording', async () => {
    const mocks = installMediaMocks()
    const { result } = renderHook(() => useRecorder())

    await act(async () => {
      await result.current.start()
    })
    expect(result.current.state).toBe('recording')

    act(() => {
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' })
      document.dispatchEvent(new Event('visibilitychange'))
    })

    expect(result.current.state).toBe('paused')
    expect(FakeMediaRecorder.instances[0].state).toBe('paused')
    mocks.restore()
  })

  describe('importFile', () => {
    it('accepts an audio file and lands in the same stopped state as a recording', async () => {
      const mocks = installMediaMocks()
      const { result } = renderHook(() => useRecorder())

      await act(async () => {
        await result.current.importFile(audioFile('hearth-cooling.wav', 'audio/wav'))
      })

      expect(result.current.state).toBe('stopped')
      expect(result.current.result?.source).toBe('file')
      expect(result.current.result?.fileName).toBe('hearth-cooling.wav')
      expect(result.current.result?.mimeType).toBe('audio/wav')
      expect(result.current.result?.durationSeconds).toBeCloseTo(67.9)
      expect(result.current.error).toBeNull()

      mocks.restore()
    })

    it('rewrites an aliased content type to one the backend allows', async () => {
      const mocks = installMediaMocks()
      const { result } = renderHook(() => useRecorder())

      await act(async () => {
        await result.current.importFile(audioFile('handover.m4a', 'audio/x-m4a'))
      })

      expect(result.current.result?.mimeType).toBe('audio/mp4')
      expect(result.current.result?.blob.type).toBe('audio/mp4')

      mocks.restore()
    })

    it('works when the browser cannot record at all', async () => {
      // A tablet with no usable microphone must still be able to contribute audio.
      const mocks = installMediaMocks()
      const restore = removeMediaSupport()
      const { result } = renderHook(() => useRecorder())
      expect(result.current.state).toBe('unsupported')

      await act(async () => {
        await result.current.importFile(audioFile('hearth-cooling.wav', 'audio/wav'))
      })

      expect(result.current.state).toBe('stopped')
      expect(result.current.result?.source).toBe('file')

      restore()
      mocks.restore()
    })

    it('rejects a file that is not audio', async () => {
      const mocks = installMediaMocks()
      const { result } = renderHook(() => useRecorder())

      await act(async () => {
        await result.current.importFile(audioFile('procedure.pdf', 'application/pdf'))
      })

      expect(result.current.state).toBe('error')
      expect(result.current.error?.kind).toBe('file-type')
      expect(result.current.result).toBeNull()

      mocks.restore()
    })

    it('rejects a file above the 25 MB upload ceiling before any network call', async () => {
      const mocks = installMediaMocks()
      const { result } = renderHook(() => useRecorder())

      await act(async () => {
        await result.current.importFile(audioFile('long-shift.wav', 'audio/wav', 26 * 1024 * 1024))
      })

      expect(result.current.state).toBe('error')
      expect(result.current.error?.kind).toBe('file-size')

      mocks.restore()
    })

    it('rejects an empty file', async () => {
      const mocks = installMediaMocks()
      const { result } = renderHook(() => useRecorder())

      await act(async () => {
        await result.current.importFile(audioFile('empty.wav', 'audio/wav', 0))
      })

      expect(result.current.state).toBe('error')
      expect(result.current.error?.kind).toBe('file-empty')

      mocks.restore()
    })

    it('abandons an in-flight recording when a file is imported instead', async () => {
      const mocks = installMediaMocks()
      const { result } = renderHook(() => useRecorder())

      await act(async () => {
        await result.current.start()
      })
      expect(result.current.state).toBe('recording')

      await act(async () => {
        await result.current.importFile(audioFile('hearth-cooling.wav', 'audio/wav'))
      })

      expect(result.current.state).toBe('stopped')
      expect(result.current.result?.source).toBe('file')
      expect(FakeMediaRecorder.instances[0].state).toBe('inactive')

      mocks.restore()
    })
  })
})
