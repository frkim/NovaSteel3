import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Box } from '@mui/material'
import { useChartDimensions } from './useChartDimensions'
import type { TooltipState } from './chartUtils'

export interface PriceLoadPoint {
  t: number
  price: number
  baseline: number
  optimized: number
}

export interface PriceLoadChartProps {
  data: PriceLoadPoint[]
  priceColor: string
  baselineColor: string
  optimizedColor: string
  height?: number
  xFormat: (value: number) => string
}

/** Dual-axis energy overlay: spot price line + baseline/optimized load (C-LINE + C-AREA, §12.3). */
export function PriceLoadChart({
  data,
  priceColor,
  baselineColor,
  optimizedColor,
  height = 280,
  xFormat,
}: PriceLoadChartProps) {
  const { ref, dimensions } = useChartDimensions(height)
  const svgRef = useRef<SVGSVGElement>(null)
  const [tooltip, setTooltip] = useState<TooltipState | null>(null)

  useEffect(() => {
    const node = svgRef.current
    if (!node || data.length === 0) {
      return
    }
    const width = dimensions.width
    const margin = { top: 14, right: 52, bottom: 30, left: 48 }
    const x = d3
      .scaleLinear()
      .domain(d3.extent(data, (point) => point.t) as [number, number])
      .range([margin.left, width - margin.right])
    const yLoad = d3
      .scaleLinear()
      .domain([0, (d3.max(data, (point) => Math.max(point.baseline, point.optimized)) ?? 1) * 1.1])
      .nice()
      .range([height - margin.bottom, margin.top])
    const yPrice = d3
      .scaleLinear()
      .domain([0, (d3.max(data, (point) => point.price) ?? 1) * 1.1])
      .nice()
      .range([height - margin.bottom, margin.top])

    const svg = d3.select(node)
    svg.selectAll('*').remove()
    svg.attr('viewBox', `0 0 ${width} ${height}`)

    svg
      .append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .attr('color', 'currentColor')
      .call(d3.axisBottom(x).ticks(6).tickFormat((value) => xFormat(Number(value))))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))
    svg
      .append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .attr('color', 'currentColor')
      .call(d3.axisLeft(yLoad).ticks(5).tickFormat((value) => `${value} MW`))
      .call((axis) => axis.selectAll('text').attr('font-size', 10))
    svg
      .append('g')
      .attr('transform', `translate(${width - margin.right},0)`)
      .attr('color', priceColor)
      .call(d3.axisRight(yPrice).ticks(5).tickFormat((value) => `€${value}`))
      .call((axis) => axis.selectAll('text').attr('font-size', 10))

    const optimizedArea = d3
      .area<PriceLoadPoint>()
      .x((point) => x(point.t))
      .y0(yLoad(0))
      .y1((point) => yLoad(point.optimized))
      .curve(d3.curveMonotoneX)
    svg
      .append('path')
      .datum(data)
      .attr('fill', optimizedColor)
      .attr('fill-opacity', 0.22)
      .attr('d', optimizedArea)

    const loadLine = (accessor: (point: PriceLoadPoint) => number, color: string, dash: string | null) =>
      svg
        .append('path')
        .datum(data)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', dash)
        .attr(
          'd',
          d3
            .line<PriceLoadPoint>()
            .x((point) => x(point.t))
            .y((point) => yLoad(accessor(point)))
            .curve(d3.curveMonotoneX),
        )
    loadLine((point) => point.baseline, baselineColor, '6 4')
    loadLine((point) => point.optimized, optimizedColor, null)

    svg
      .append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', priceColor)
      .attr('stroke-width', 2.5)
      .attr(
        'd',
        d3
          .line<PriceLoadPoint>()
          .x((point) => x(point.t))
          .y((point) => yPrice(point.price))
          .curve(d3.curveMonotoneX),
      )

    const focus = svg
      .append('line')
      .attr('stroke', 'currentColor')
      .attr('stroke-opacity', 0.4)
      .attr('y1', margin.top)
      .attr('y2', height - margin.bottom)
      .style('display', 'none')
    const bisect = d3.bisector<PriceLoadPoint, number>((point) => point.t).center
    svg
      .append('rect')
      .attr('x', margin.left)
      .attr('y', margin.top)
      .attr('width', Math.max(0, width - margin.left - margin.right))
      .attr('height', Math.max(0, height - margin.top - margin.bottom))
      .attr('fill', 'transparent')
      .on('mousemove', (event: MouseEvent) => {
        const [pointerX] = d3.pointer(event)
        const point = data[bisect(data, x.invert(pointerX))]
        if (!point) {
          return
        }
        focus.attr('x1', x(point.t)).attr('x2', x(point.t)).style('display', null)
        setTooltip({
          x: x(point.t),
          y: margin.top,
          content: `${xFormat(point.t)} · €${point.price}/MWh · ${point.optimized} MW`,
        })
      })
      .on('mouseleave', () => {
        focus.style('display', 'none')
        setTooltip(null)
      })
  }, [dimensions.width, height, data, priceColor, baselineColor, optimizedColor, xFormat])

  return (
    <Box ref={ref} sx={{ position: 'relative', width: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height }} />
      {tooltip && (
        <div className="ns-chart-tooltip" style={{ left: tooltip.x, top: tooltip.y }} role="presentation">
          {tooltip.content}
        </div>
      )}
    </Box>
  )
}
