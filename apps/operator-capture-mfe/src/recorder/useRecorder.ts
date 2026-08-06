import { useCallback, useEffect, useRef, useState } from 'react'

export type RecorderState =
  | 'unsupported'
  | 'idle'
  | 'requesting'
  | 'recording'
  | 'paused'
  | 'stopped'
  | 'error'

export type RecorderErrorKind = 'permission' | 'no-mic' | 'unsupported' | 'unknown'

export interface RecorderError {
  kind: RecorderErrorKind
  message: string
}

export interface RecorderResult {
  blob: Blob
  url: string
  durationSeconds: number
  mimeType: string
}

export interface RecorderController {
  state: RecorderState
  isSupported: boolean
  elapsedMs: number
  /** Live input level 0..1 for the meter/waveform. */
  level: number
  error: RecorderError | null
  result: RecorderResult | null
  start: () => Promise<void>
  pause: () => void
  resume: () => void
  stop: () => void
  reset: () => void
}

const PREFERRED_MIME_TYPES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']

function pickMimeType(): string {
  const RecorderCtor = typeof MediaRecorder !== 'undefined' ? MediaRecorder : undefined
  if (RecorderCtor && typeof RecorderCtor.isTypeSupported === 'function') {
    for (const type of PREFERRED_MIME_TYPES) {
      if (RecorderCtor.isTypeSupported(type)) {
        return type
      }
    }
  }
  return ''
}

function detectSupport(): boolean {
  return (
    typeof navigator !== 'undefined' &&
    !!navigator.mediaDevices &&
    typeof navigator.mediaDevices.getUserMedia === 'function' &&
    typeof MediaRecorder !== 'undefined'
  )
}

function classifyError(err: unknown): RecorderError {
  if (err instanceof DOMException) {
    if (err.name === 'NotAllowedError' || err.name === 'SecurityError') {
      return { kind: 'permission', message: 'Microphone access was denied. Enable it to record.' }
    }
    if (err.name === 'NotFoundError' || err.name === 'OverconstrainedError') {
      return { kind: 'no-mic', message: 'No microphone was found on this device.' }
    }
  }
  return { kind: 'unknown', message: err instanceof Error ? err.message : 'Could not start recording.' }
}

/**
 * MediaRecorder-backed capture hook. Owns a small state machine
 * (idle→recording→paused→stopped) plus a live elapsed timer and an input-level
 * meter driven by a Web Audio AnalyserNode. Backgrounding the tab auto-pauses
 * so a recording never keeps running unseen.
 */
export function useRecorder(): RecorderController {
  const supported = detectSupport()
  const [state, setState] = useState<RecorderState>(supported ? 'idle' : 'unsupported')
  const [elapsedMs, setElapsedMs] = useState(0)
  const [level, setLevel] = useState(0)
  const [error, setError] = useState<RecorderError | null>(null)
  const [result, setResult] = useState<RecorderResult | null>(null)

  const recorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const mimeRef = useRef<string>('')
  const startedAtRef = useRef<number>(0)
  const accumulatedRef = useRef<number>(0)
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const rafRef = useRef<number | null>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const resultUrlRef = useRef<string | null>(null)

  const stopTimer = useCallback(() => {
    if (tickRef.current !== null) {
      clearInterval(tickRef.current)
      tickRef.current = null
    }
  }, [])

  const startTimer = useCallback(() => {
    startedAtRef.current = Date.now()
    stopTimer()
    tickRef.current = setInterval(() => {
      setElapsedMs(accumulatedRef.current + (Date.now() - startedAtRef.current))
    }, 200)
  }, [stopTimer])

  const stopMeter = useCallback(() => {
    if (rafRef.current !== null && typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(rafRef.current)
    }
    rafRef.current = null
    analyserRef.current = null
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => undefined)
      audioCtxRef.current = null
    }
    setLevel(0)
  }, [])

  const startMeter = useCallback((stream: MediaStream) => {
    const Ctor =
      typeof window !== 'undefined'
        ? window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
        : undefined
    if (!Ctor || typeof requestAnimationFrame !== 'function') {
      return
    }
    try {
      const ctx = new Ctor()
      const source = ctx.createMediaStreamSource(stream)
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      audioCtxRef.current = ctx
      analyserRef.current = analyser
      const data = new Uint8Array(analyser.frequencyBinCount)
      const loop = () => {
        const node = analyserRef.current
        if (!node) {
          return
        }
        node.getByteTimeDomainData(data)
        let sum = 0
        for (let i = 0; i < data.length; i += 1) {
          const v = (data[i] - 128) / 128
          sum += v * v
        }
        const rms = Math.sqrt(sum / data.length)
        setLevel(Math.min(1, rms * 2.2))
        rafRef.current = requestAnimationFrame(loop)
      }
      rafRef.current = requestAnimationFrame(loop)
    } catch {
      // Level meter is best-effort; recording still works without it.
    }
  }, [])

  const teardownStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
  }, [])

  const start = useCallback(async () => {
    if (!supported) {
      setState('unsupported')
      return
    }
    setError(null)
    setResult(null)
    setElapsedMs(0)
    accumulatedRef.current = 0
    chunksRef.current = []
    setState('requesting')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const mimeType = pickMimeType()
      mimeRef.current = mimeType
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream)
      recorderRef.current = recorder
      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }
      recorder.onstop = () => {
        const type = mimeRef.current || chunksRef.current[0]?.type || 'audio/webm'
        const blob = new Blob(chunksRef.current, { type })
        if (resultUrlRef.current) {
          URL.revokeObjectURL(resultUrlRef.current)
        }
        const url = typeof URL !== 'undefined' && URL.createObjectURL ? URL.createObjectURL(blob) : ''
        resultUrlRef.current = url
        setResult({
          blob,
          url,
          durationSeconds: accumulatedRef.current / 1000,
          mimeType: type,
        })
        setState('stopped')
        stopMeter()
        teardownStream()
      }
      recorder.start()
      startTimer()
      startMeter(stream)
      setState('recording')
    } catch (err) {
      teardownStream()
      setError(classifyError(err))
      setState('error')
    }
  }, [supported, startTimer, startMeter, stopMeter, teardownStream])

  const pause = useCallback(() => {
    const recorder = recorderRef.current
    if (recorder && recorder.state === 'recording') {
      recorder.pause()
      accumulatedRef.current += Date.now() - startedAtRef.current
      stopTimer()
      setElapsedMs(accumulatedRef.current)
      setState('paused')
    }
  }, [stopTimer])

  const resume = useCallback(() => {
    const recorder = recorderRef.current
    if (recorder && recorder.state === 'paused') {
      recorder.resume()
      startTimer()
      setState('recording')
    }
  }, [startTimer])

  const stop = useCallback(() => {
    const recorder = recorderRef.current
    if (recorder && recorder.state !== 'inactive') {
      if (recorder.state === 'recording') {
        accumulatedRef.current += Date.now() - startedAtRef.current
      }
      stopTimer()
      setElapsedMs(accumulatedRef.current)
      recorder.stop()
    }
  }, [stopTimer])

  const reset = useCallback(() => {
    stopTimer()
    stopMeter()
    teardownStream()
    recorderRef.current = null
    chunksRef.current = []
    accumulatedRef.current = 0
    if (resultUrlRef.current) {
      URL.revokeObjectURL(resultUrlRef.current)
      resultUrlRef.current = null
    }
    setResult(null)
    setElapsedMs(0)
    setError(null)
    setState(supported ? 'idle' : 'unsupported')
  }, [stopTimer, stopMeter, teardownStream, supported])

  // Auto-pause if the operator backgrounds the tab mid-recording.
  useEffect(() => {
    if (typeof document === 'undefined') {
      return
    }
    const onVisibility = () => {
      if (document.visibilityState === 'hidden' && recorderRef.current?.state === 'recording') {
        pause()
      }
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => document.removeEventListener('visibilitychange', onVisibility)
  }, [pause])

  useEffect(() => {
    return () => {
      stopTimer()
      stopMeter()
      teardownStream()
      if (resultUrlRef.current) {
        URL.revokeObjectURL(resultUrlRef.current)
      }
    }
  }, [stopTimer, stopMeter, teardownStream])

  return {
    state,
    isSupported: supported,
    elapsedMs,
    level,
    error,
    result,
    start,
    pause,
    resume,
    stop,
    reset,
  }
}
