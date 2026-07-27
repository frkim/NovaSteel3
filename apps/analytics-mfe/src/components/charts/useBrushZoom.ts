import { useCallback, useEffect, useRef, useState, type RefObject } from 'react'
import type { BrushSelection } from './BrushOverlay'
import { useChartZoomContext } from './ChartZoomContext'

export interface BrushZoomBounds {
  x: number
  y: number
  width: number
  height: number
}

export interface UseBrushZoomOptions {
  targetRef: RefObject<SVGSVGElement | null>
  width: number
  height: number
  bounds: BrushZoomBounds
  enabled?: boolean
  isZoomed: boolean
  minSelectionPx?: number
  onBrushEnd: (range: [number, number]) => void
  onReset: () => void
}

interface ActiveDrag {
  startX: number
  currentX: number
}

const DEFAULT_MIN_SELECTION_PX = 8

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function pointerXInViewBox(event: PointerEvent, node: SVGSVGElement, width: number): number {
  const rect = node.getBoundingClientRect()
  const rectWidth = rect.width || width || 1
  return ((event.clientX - rect.left) / rectWidth) * width
}

export function useBrushZoom({
  targetRef,
  width,
  height,
  bounds,
  enabled = true,
  isZoomed,
  minSelectionPx = DEFAULT_MIN_SELECTION_PX,
  onBrushEnd,
  onReset,
}: UseBrushZoomOptions): { enabled: boolean; selection: BrushSelection | null; reset: () => void } {
  const { brushZoomEnabled, registerDataZoom } = useChartZoomContext()
  const effectiveEnabled = enabled && brushZoomEnabled && bounds.width > 0 && bounds.height > 0
  const [selection, setSelection] = useState<BrushSelection | null>(null)
  const dragRef = useRef<ActiveDrag | null>(null)

  const clearSelection = useCallback(() => {
    dragRef.current = null
    setSelection(null)
  }, [])

  const reset = useCallback(() => {
    clearSelection()
    onReset()
  }, [clearSelection, onReset])

  const updateSelection = useCallback(
    (startX: number, currentX: number) => {
      const x1 = Math.min(startX, currentX)
      const x2 = Math.max(startX, currentX)
      setSelection({
        x: x1,
        y: bounds.y,
        width: x2 - x1,
        height: bounds.height,
      })
    },
    [bounds.height, bounds.y],
  )

  useEffect(() => {
    if (!effectiveEnabled) {
      clearSelection()
      return
    }

    const node = targetRef.current
    if (!node) {
      return
    }

    const minX = bounds.x
    const maxX = bounds.x + bounds.width
    const minY = bounds.y
    const maxY = bounds.y + bounds.height

    const xFromEvent = (event: PointerEvent) =>
      clamp(pointerXInViewBox(event, node, width), minX, maxX)

    const yFromEvent = (event: PointerEvent) => {
      const rect = node.getBoundingClientRect()
      const rectHeight = rect.height || height || 1
      return ((event.clientY - rect.top) / rectHeight) * height
    }

    const handlePointerDown = (event: PointerEvent) => {
      if (event.button !== 0) {
        return
      }

      const x = xFromEvent(event)
      const y = yFromEvent(event)
      if (x < minX || x > maxX || y < minY || y > maxY) {
        return
      }

      dragRef.current = { startX: x, currentX: x }
      updateSelection(x, x)
    }

    const handlePointerMove = (event: PointerEvent) => {
      const drag = dragRef.current
      if (!drag) {
        return
      }

      const x = xFromEvent(event)
      drag.currentX = x
      updateSelection(drag.startX, x)
      if (Math.abs(x - drag.startX) >= minSelectionPx) {
        event.preventDefault()
      }
    }

    const finishDrag = (commit: boolean) => {
      const drag = dragRef.current
      if (!drag) {
        return
      }

      dragRef.current = null
      setSelection(null)
      const distance = Math.abs(drag.currentX - drag.startX)
      if (commit && distance >= minSelectionPx) {
        onBrushEnd([Math.min(drag.startX, drag.currentX), Math.max(drag.startX, drag.currentX)])
      }
    }

    const handlePointerUp = (event: PointerEvent) => {
      const drag = dragRef.current
      if (!drag) {
        return
      }
      drag.currentX = xFromEvent(event)
      finishDrag(true)
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && dragRef.current) {
        event.preventDefault()
        finishDrag(false)
      }
    }

    node.addEventListener('pointerdown', handlePointerDown)
    window.addEventListener('pointermove', handlePointerMove)
    window.addEventListener('pointerup', handlePointerUp)
    window.addEventListener('keydown', handleKeyDown)

    return () => {
      node.removeEventListener('pointerdown', handlePointerDown)
      window.removeEventListener('pointermove', handlePointerMove)
      window.removeEventListener('pointerup', handlePointerUp)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [
    bounds.height,
    bounds.width,
    bounds.x,
    bounds.y,
    clearSelection,
    effectiveEnabled,
    height,
    minSelectionPx,
    onBrushEnd,
    targetRef,
    updateSelection,
    width,
  ])

  useEffect(() => {
    if (!effectiveEnabled || !registerDataZoom) {
      return
    }
    return registerDataZoom({ isZoomed, reset })
  }, [effectiveEnabled, isZoomed, registerDataZoom, reset])

  return { enabled: effectiveEnabled, selection: effectiveEnabled ? selection : null, reset }
}

export interface InvertibleScale {
  invert: (value: number) => number
}

export interface BandLikeScale<T extends string> {
  (value: T): number | undefined
  bandwidth: () => number
}

export function selectedLinearDomain(
  scale: InvertibleScale,
  range: [number, number],
): [number, number] | null {
  const start = scale.invert(range[0])
  const end = scale.invert(range[1])
  if (!Number.isFinite(start) || !Number.isFinite(end) || start === end) {
    return null
  }
  return start < end ? [start, end] : [end, start]
}

export function selectedBandDomain<T extends string>(
  scale: BandLikeScale<T>,
  values: readonly T[],
  range: [number, number],
): T[] {
  const [start, end] = range
  return values.filter((value) => {
    const bandStart = scale(value)
    if (bandStart === undefined) {
      return false
    }
    const bandEnd = bandStart + scale.bandwidth()
    return bandEnd >= start && bandStart <= end
  })
}
