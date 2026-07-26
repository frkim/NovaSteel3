import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { Box } from '@mui/material'

export interface GaugeChartProps {
  value: number
  min: number
  max: number
  threshold?: number
  color: string
  thresholdColor: string
  trackColor: string
  valueLabel: string
  height?: number
}

export function GaugeChart({
  value,
  min,
  max,
  threshold,
  color,
  thresholdColor,
  trackColor,
  valueLabel,
  height = 180,
}: GaugeChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    const node = svgRef.current
    if (!node) {
      return
    }
    const width = height * 1.7
    const radius = Math.min(width / 2, height) - 10
    const svg = d3.select(node)
    svg.selectAll('*').remove()
    svg.attr('viewBox', `0 0 ${width} ${height + 10}`)
    const group = svg.append('g').attr('transform', `translate(${width / 2},${height})`)

    const scale = d3.scaleLinear().domain([min, max]).range([-Math.PI / 2, Math.PI / 2]).clamp(true)
    const arc = d3
      .arc<{ start: number; end: number }>()
      .innerRadius(radius * 0.68)
      .outerRadius(radius)
      .startAngle((datum) => datum.start)
      .endAngle((datum) => datum.end)

    group
      .append('path')
      .datum({ start: -Math.PI / 2, end: Math.PI / 2 })
      .attr('fill', trackColor)
      .attr('d', arc)
    group
      .append('path')
      .datum({ start: -Math.PI / 2, end: scale(value) })
      .attr('fill', threshold !== undefined && value >= threshold ? thresholdColor : color)
      .attr('d', arc)

    if (threshold !== undefined) {
      const angle = scale(threshold)
      const inner = radius * 0.64
      const outer = radius * 1.04
      group
        .append('line')
        .attr('x1', Math.cos(angle - Math.PI / 2) * inner)
        .attr('y1', Math.sin(angle - Math.PI / 2) * inner)
        .attr('x2', Math.cos(angle - Math.PI / 2) * outer)
        .attr('y2', Math.sin(angle - Math.PI / 2) * outer)
        .attr('stroke', thresholdColor)
        .attr('stroke-width', 2)
    }

    group
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-0.2em')
      .attr('font-size', 24)
      .attr('font-weight', 700)
      .attr('fill', 'currentColor')
      .text(valueLabel)
  }, [value, min, max, threshold, color, thresholdColor, trackColor, valueLabel, height])

  return (
    <Box sx={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
      <svg ref={svgRef} style={{ width: '100%', maxWidth: height * 1.7, height: height + 10 }} />
    </Box>
  )
}
