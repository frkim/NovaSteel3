import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { Box } from '@mui/material'
import { useChartDimensions } from './useChartDimensions'
import { CHART_MARGIN } from './chartUtils'

export interface ControlPoint {
  index: number
  value: number
  label: string
}

export interface ControlChartProps {
  points: ControlPoint[]
  mean: number
  ucl: number
  lcl: number
  color: string
  violationColor: string
  height?: number
  yFormat: (value: number) => string
}

export function ControlChart({
  points,
  mean,
  ucl,
  lcl,
  color,
  violationColor,
  height = 260,
  yFormat,
}: ControlChartProps) {
  const { ref, dimensions } = useChartDimensions(height)
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    const node = svgRef.current
    if (!node || points.length === 0) {
      return
    }
    const width = dimensions.width
    const x = d3
      .scaleLinear()
      .domain([points[0].index, points[points.length - 1].index])
      .range([CHART_MARGIN.left, width - CHART_MARGIN.right])
    const values = points.map((point) => point.value)
    const y = d3
      .scaleLinear()
      .domain([Math.min(lcl, ...values) - 1, Math.max(ucl, ...values) + 1])
      .nice()
      .range([height - CHART_MARGIN.bottom, CHART_MARGIN.top])

    const svg = d3.select(node)
    svg.selectAll('*').remove()
    svg.attr('viewBox', `0 0 ${width} ${height}`)

    svg
      .append('g')
      .attr('transform', `translate(0,${height - CHART_MARGIN.bottom})`)
      .attr('color', 'currentColor')
      .call(d3.axisBottom(x).ticks(Math.min(points.length, 10)).tickFormat(d3.format('d')))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))
    svg
      .append('g')
      .attr('transform', `translate(${CHART_MARGIN.left},0)`)
      .attr('color', 'currentColor')
      .call(d3.axisLeft(y).ticks(5).tickFormat((value) => yFormat(Number(value))))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))

    const limitLine = (value: number, label: string, dash: string, stroke: string) => {
      svg
        .append('line')
        .attr('x1', CHART_MARGIN.left)
        .attr('x2', width - CHART_MARGIN.right)
        .attr('y1', y(value))
        .attr('y2', y(value))
        .attr('stroke', stroke)
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', dash)
      svg
        .append('text')
        .attr('x', width - CHART_MARGIN.right)
        .attr('y', y(value) - 3)
        .attr('text-anchor', 'end')
        .attr('font-size', 10)
        .attr('fill', stroke)
        .text(label)
    }
    limitLine(ucl, `UCL ${yFormat(ucl)}`, '6 4', violationColor)
    limitLine(mean, `x̄ ${yFormat(mean)}`, '2 2', 'currentColor')
    limitLine(lcl, `LCL ${yFormat(lcl)}`, '6 4', violationColor)

    const line = d3
      .line<ControlPoint>()
      .x((point) => x(point.index))
      .y((point) => y(point.value))
    svg
      .append('path')
      .datum(points)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', 2)
      .attr('d', line)

    svg
      .append('g')
      .selectAll('g')
      .data(points)
      .join('g')
      .each(function (point) {
        const outOfControl = point.value > ucl || point.value < lcl
        const cell = d3.select(this)
        cell
          .append('circle')
          .attr('cx', x(point.index))
          .attr('cy', y(point.value))
          .attr('r', outOfControl ? 5 : 3)
          .attr('fill', outOfControl ? violationColor : color)
          .attr('stroke', outOfControl ? 'currentColor' : 'none')
          .attr('role', 'img')
          .attr('aria-label', `${point.label}: ${yFormat(point.value)}${outOfControl ? ' out of control' : ''}`)
          .append('title')
          .text(`${point.label}: ${yFormat(point.value)}${outOfControl ? ' — out of control' : ''}`)
        if (outOfControl) {
          cell
            .append('text')
            .attr('x', x(point.index))
            .attr('y', y(point.value) - 9)
            .attr('text-anchor', 'middle')
            .attr('font-size', 12)
            .attr('fill', violationColor)
            .attr('aria-hidden', 'true')
            .text('⛔')
        }
      })
  }, [dimensions.width, height, points, mean, ucl, lcl, color, violationColor, yFormat])

  return (
    <Box ref={ref} sx={{ width: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height }} />
    </Box>
  )
}
