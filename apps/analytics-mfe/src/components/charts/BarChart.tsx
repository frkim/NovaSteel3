import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { Box } from '@mui/material'
import { useChartDimensions } from './useChartDimensions'
import { CHART_MARGIN } from './chartUtils'

export interface BarSeries {
  id: string
  label: string
  color: string
}

export interface BarGroup {
  label: string
  values: Record<string, number>
}

export interface BarChartProps {
  groups: BarGroup[]
  series: BarSeries[]
  height?: number
  yFormat: (value: number) => string
}

export function BarChart({ groups, series, height = 260, yFormat }: BarChartProps) {
  const { ref, dimensions } = useChartDimensions(height)
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    const node = svgRef.current
    if (!node || groups.length === 0) {
      return
    }
    const width = dimensions.width
    const x0 = d3
      .scaleBand()
      .domain(groups.map((group) => group.label))
      .range([CHART_MARGIN.left, width - CHART_MARGIN.right])
      .paddingInner(0.2)
    const x1 = d3
      .scaleBand()
      .domain(series.map((entry) => entry.id))
      .range([0, x0.bandwidth()])
      .padding(0.08)
    const maxValue =
      d3.max(groups, (group) => d3.max(series, (entry) => group.values[entry.id] ?? 0)) ?? 1
    const y = d3
      .scaleLinear()
      .domain([Math.min(0, d3.min(groups, (group) => d3.min(series, (entry) => group.values[entry.id] ?? 0)) ?? 0), maxValue])
      .nice()
      .range([height - CHART_MARGIN.bottom, CHART_MARGIN.top])

    const svg = d3.select(node)
    svg.selectAll('*').remove()
    svg.attr('viewBox', `0 0 ${width} ${height}`)

    svg
      .append('g')
      .attr('transform', `translate(0,${y(0)})`)
      .attr('color', 'currentColor')
      .call(d3.axisBottom(x0).tickSizeOuter(0))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))
    svg
      .append('g')
      .attr('transform', `translate(${CHART_MARGIN.left},0)`)
      .attr('color', 'currentColor')
      .call(d3.axisLeft(y).ticks(5).tickFormat((value) => yFormat(Number(value))))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))

    const groupNode = svg
      .append('g')
      .selectAll('g')
      .data(groups)
      .join('g')
      .attr('transform', (group) => `translate(${x0(group.label) ?? 0},0)`)

    groupNode
      .selectAll('rect')
      .data((group) => series.map((entry) => ({ entry, value: group.values[entry.id] ?? 0 })))
      .join('rect')
      .attr('x', (item) => x1(item.entry.id) ?? 0)
      .attr('y', (item) => Math.min(y(0), y(item.value)))
      .attr('width', x1.bandwidth())
      .attr('height', (item) => Math.abs(y(item.value) - y(0)))
      .attr('rx', 2)
      .attr('fill', (item) => item.entry.color)
      .append('title')
      .text((item) => `${item.entry.label}: ${yFormat(item.value)}`)
  }, [dimensions.width, height, groups, series, yFormat])

  return (
    <Box ref={ref} sx={{ width: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height }} />
    </Box>
  )
}
