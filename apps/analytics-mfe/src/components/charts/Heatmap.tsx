import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Box } from '@mui/material'
import { useChartDimensions } from './useChartDimensions'
import type { TooltipState } from './chartUtils'

export interface HeatmapProps {
  zones: string[]
  columns: string[]
  values: number[][]
  columnFormat: (value: string) => string
  height?: number
  /** Cells at or above this value get an anomaly ring (icon, not color-only). */
  anomalyThreshold?: number
}

export function Heatmap({
  zones,
  columns,
  values,
  columnFormat,
  height = 260,
  anomalyThreshold,
}: HeatmapProps) {
  const { ref, dimensions } = useChartDimensions(height)
  const svgRef = useRef<SVGSVGElement>(null)
  const [tooltip, setTooltip] = useState<TooltipState | null>(null)

  useEffect(() => {
    const node = svgRef.current
    if (!node || values.length === 0) {
      return
    }
    const width = dimensions.width
    const margin = { top: 10, right: 16, bottom: 34, left: 90 }
    const flat = values.flat()
    const color = d3
      .scaleSequential(d3.interpolateInferno)
      .domain([Math.min(...flat), Math.max(...flat)])

    const x = d3
      .scaleBand<string>()
      .domain(columns)
      .range([margin.left, width - margin.right])
      .padding(0.04)
    const y = d3
      .scaleBand<string>()
      .domain(zones)
      .range([margin.top, height - margin.bottom])
      .padding(0.06)

    const svg = d3.select(node)
    svg.selectAll('*').remove()
    svg.attr('viewBox', `0 0 ${width} ${height}`)

    svg
      .append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .attr('color', 'currentColor')
      .call(
        d3
          .axisBottom(x)
          .tickValues(columns.filter((_, index) => index % 4 === 0))
          .tickFormat((value) => columnFormat(String(value))),
      )
      .call((axis) => axis.selectAll('text').attr('font-size', 10))
    svg
      .append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .attr('color', 'currentColor')
      .call(d3.axisLeft(y))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))

    zones.forEach((zone, rowIndex) => {
      columns.forEach((column, columnIndex) => {
        const value = values[rowIndex]?.[columnIndex]
        if (value === undefined) {
          return
        }
        const cx = x(column) ?? 0
        const cy = y(zone) ?? 0
        svg
          .append('rect')
          .attr('x', cx)
          .attr('y', cy)
          .attr('width', x.bandwidth())
          .attr('height', y.bandwidth())
          .attr('fill', color(value))
          .attr('rx', 1)
          .on('mousemove', (event: MouseEvent) => {
            const [px, py] = d3.pointer(event, node)
            setTooltip({ x: px, y: py, content: `${zone} · ${columnFormat(column)}: ${value}` })
          })
          .on('mouseleave', () => setTooltip(null))
          .append('title')
          .text(`${zone} · ${columnFormat(column)}: ${value}`)
        if (anomalyThreshold !== undefined && value >= anomalyThreshold) {
          svg
            .append('text')
            .attr('x', cx + x.bandwidth() / 2)
            .attr('y', cy + y.bandwidth() / 2 + 4)
            .attr('text-anchor', 'middle')
            .attr('font-size', 12)
            .attr('fill', '#fff')
            .attr('aria-hidden', 'true')
            .text('▲')
        }
      })
    })
  }, [dimensions.width, height, zones, columns, values, columnFormat, anomalyThreshold])

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
