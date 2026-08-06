import { describe, expect, it, afterEach, vi } from 'vitest'
import { act, renderHook, waitFor } from '@testing-library/react'
import { useRecorder } from './useRecorder'
import { FakeMediaRecorder, installMediaMocks, removeMediaSupport } from '../test/mediaMocks'

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
})
