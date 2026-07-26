import type { ReactNode } from 'react'

export const CHART_MARGIN = { top: 16, right: 20, bottom: 30, left: 44 }

export interface TooltipState {
  x: number
  y: number
  content: ReactNode
}

export function niceExtent(values: number[], padRatio = 0.08): [number, number] {
  if (values.length === 0) {
    return [0, 1]
  }
  const min = Math.min(...values)
  const max = Math.max(...values)
  if (min === max) {
    const pad = Math.abs(min) * padRatio || 1
    return [min - pad, max + pad]
  }
  const pad = (max - min) * padRatio
  return [min - pad, max + pad]
}
