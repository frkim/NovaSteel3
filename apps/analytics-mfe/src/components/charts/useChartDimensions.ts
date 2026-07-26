import { useCallback, useEffect, useRef, useState } from 'react'

export interface Dimensions {
  width: number
  height: number
}

/**
 * Observes a container element and returns its content-box size so D3 charts
 * can render responsively (UX §14.2 container observer, <100ms resize budget).
 */
export function useChartDimensions(defaultHeight = 260): {
  ref: (node: HTMLDivElement | null) => void
  dimensions: Dimensions
} {
  const [dimensions, setDimensions] = useState<Dimensions>({ width: 640, height: defaultHeight })
  const observerRef = useRef<ResizeObserver | null>(null)
  const ref = useCallback((node: HTMLDivElement | null) => {
    if (observerRef.current) {
      observerRef.current.disconnect()
      observerRef.current = null
    }
    if (node && typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver((entries) => {
        for (const entry of entries) {
          const width = entry.contentRect.width
          if (width > 0) {
            setDimensions((current) =>
              current.width === width && current.height === defaultHeight
                ? current
                : { width, height: defaultHeight },
            )
          }
        }
      })
      observer.observe(node)
      observerRef.current = observer
      const rect = node.getBoundingClientRect()
      if (rect.width > 0) {
        setDimensions((current) =>
          current.width === rect.width && current.height === defaultHeight
            ? current
            : { width: rect.width, height: defaultHeight },
        )
      }
    }
  }, [defaultHeight])

  useEffect(() => {
    return () => {
      observerRef.current?.disconnect()
    }
  }, [])

  return { ref, dimensions }
}
