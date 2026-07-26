import { useMemo } from 'react'
import * as d3 from 'd3'

export interface SparklineProps {
  values: number[]
  color: string
  width?: number
  height?: number
  ariaLabel?: string
}

/** Compact inline micro-trend for KPI cards (C-SPARK, §14.3). */
export function Sparkline({ values, color, width = 96, height = 28, ariaLabel }: SparklineProps) {
  const path = useMemo(() => {
    if (values.length < 2) {
      return ''
    }
    const x = d3
      .scaleLinear()
      .domain([0, values.length - 1])
      .range([2, width - 2])
    const y = d3
      .scaleLinear()
      .domain([Math.min(...values), Math.max(...values)])
      .range([height - 2, 2])
    const line = d3
      .line<number>()
      .x((_, index) => x(index))
      .y((value) => y(value))
      .curve(d3.curveMonotoneX)
    return line(values) ?? ''
  }, [values, width, height])

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={ariaLabel ?? 'trend sparkline'}
      focusable="false"
    >
      <path d={path} fill="none" stroke={color} strokeWidth={1.75} strokeLinecap="round" />
    </svg>
  )
}
