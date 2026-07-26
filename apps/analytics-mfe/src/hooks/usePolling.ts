import { useEffect, useRef, useState } from 'react'

/**
 * Calls `callback` on a fixed interval while `enabled`, pausing automatically
 * when the tab is hidden and firing once immediately when it becomes visible
 * again. Used for the live/refresh behavior on the Command Center, alert
 * center, and platform jobs surfaces (UX §16.3 poll fallback).
 */
export function usePolling(callback: () => void, intervalMs: number, enabled = true): void {
  const saved = useRef(callback)
  saved.current = callback

  useEffect(() => {
    if (!enabled || intervalMs <= 0) {
      return
    }
    let timer: ReturnType<typeof setInterval> | null = null

    const start = () => {
      if (timer === null) {
        timer = setInterval(() => saved.current(), intervalMs)
      }
    }
    const stop = () => {
      if (timer !== null) {
        clearInterval(timer)
        timer = null
      }
    }
    const onVisibility = () => {
      if (document.visibilityState === 'visible') {
        saved.current()
        start()
      } else {
        stop()
      }
    }

    if (document.visibilityState === 'visible') {
      start()
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      stop()
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [intervalMs, enabled])
}

/** Ticks a monotonically increasing counter, used to drive "x ago" freshness labels. */
export function useNow(intervalMs = 15000): number {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), intervalMs)
    return () => clearInterval(timer)
  }, [intervalMs])
  return now
}
