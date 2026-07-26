import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { Box } from '@mui/material'
import { useChartDimensions } from './useChartDimensions'

export interface ParetoItem {
  label: string
  count: number
}

export interface ParetoChartProps {
  items: ParetoItem[]
  barColor: string
  lineColor: string
  height?: number
}

export function ParetoChart({ items, barColor, lineColor, height = 260 }: ParetoChartProps) {
  const { ref, dimensions } = useChartDimensions(height)
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    const node = svgRef.current
    if (!node || items.length === 0) {
      return
    }
    const width = dimensions.width
    const margin = { top: 12, right: 44, bottom: 60, left: 44 }
    const ordered = [...items].sort((a, b) => b.count - a.count)
    const total = d3.sum(ordered, (item) => item.count) || 1
    let cumulative = 0
    const cumulativePoints = ordered.map((item) => {
      cumulative += item.count
      return { label: item.label, pct: (cumulative / total) * 100 }
    })

    const x = d3
      .scaleBand<string>()
      .domain(ordered.map((item) => item.label))
      .range([margin.left, width - margin.right])
      .padding(0.25)
    const yLeft = d3
      .scaleLinear()
      .domain([0, d3.max(ordered, (item) => item.count) ?? 1])
      .nice()
      .range([height - margin.bottom, margin.top])
    const yRight = d3.scaleLinear().domain([0, 100]).range([height - margin.bottom, margin.top])

    const svg = d3.select(node)
    svg.selectAll('*').remove()
    svg.attr('viewBox', `0 0 ${width} ${height}`)

    svg
      .append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .attr('color', 'currentColor')
      .call(d3.axisBottom(x))
      .call((axis) =>
        axis
          .selectAll('text')
          .attr('font-size', 10)
          .attr('transform', 'rotate(-22)')
          .attr('text-anchor', 'end'),
      )
    svg
      .append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .attr('color', 'currentColor')
      .call(d3.axisLeft(yLeft).ticks(5))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))
    svg
      .append('g')
      .attr('transform', `translate(${width - margin.right},0)`)
      .attr('color', 'currentColor')
      .call(d3.axisRight(yRight).ticks(5).tickFormat((value) => `${value}%`))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))

    svg
      .append('g')
      .selectAll('rect')
      .data(ordered)
      .join('rect')
      .attr('x', (item) => x(item.label) ?? 0)
      .attr('y', (item) => yLeft(item.count))
      .attr('width', x.bandwidth())
      .attr('height', (item) => yLeft(0) - yLeft(item.count))
      .attr('rx', 2)
      .attr('fill', barColor)
      .append('title')
      .text((item) => `${item.label}: ${item.count}`)

    const line = d3
      .line<{ label: string; pct: number }>()
      .x((point) => (x(point.label) ?? 0) + x.bandwidth() / 2)
      .y((point) => yRight(point.pct))
    svg
      .append('path')
      .datum(cumulativePoints)
      .attr('fill', 'none')
      .attr('stroke', lineColor)
      .attr('stroke-width', 2)
      .attr('d', line)
    svg
      .append('g')
      .selectAll('circle')
      .data(cumulativePoints)
      .join('circle')
      .attr('cx', (point) => (x(point.label) ?? 0) + x.bandwidth() / 2)
      .attr('cy', (point) => yRight(point.pct))
      .attr('r', 3)
      .attr('fill', lineColor)
      .append('title')
      .text((point) => `${point.label}: ${point.pct.toFixed(1)}% cumulative`)
  }, [dimensions.width, height, items, barColor, lineColor])

  return (
    <Box ref={ref} sx={{ width: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height }} />
    </Box>
  )
}
