import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { Box } from '@mui/material'
import { useChartDimensions } from './useChartDimensions'

export interface GanttTask {
  id: string
  label: string
  start: number
  end: number
  color: string
  urgent?: boolean
}

export interface GanttChartProps {
  tasks: GanttTask[]
  height?: number
  xFormat: (value: number) => string
}

export function GanttChart({ tasks, height = 240, xFormat }: GanttChartProps) {
  const { ref, dimensions } = useChartDimensions(height)
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    const node = svgRef.current
    if (!node || tasks.length === 0) {
      return
    }
    const width = dimensions.width
    const margin = { top: 10, right: 20, bottom: 30, left: 120 }
    const x = d3
      .scaleLinear()
      .domain([Math.min(...tasks.map((task) => task.start)), Math.max(...tasks.map((task) => task.end))])
      .range([margin.left, width - margin.right])
    const y = d3
      .scaleBand<string>()
      .domain(tasks.map((task) => task.id))
      .range([margin.top, height - margin.bottom])
      .padding(0.3)

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
      .call(d3.axisLeft(y).tickFormat((id) => tasks.find((task) => task.id === id)?.label ?? String(id)))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))

    svg
      .append('g')
      .selectAll('rect')
      .data(tasks)
      .join('rect')
      .attr('x', (task) => x(task.start))
      .attr('y', (task) => y(task.id) ?? 0)
      .attr('width', (task) => Math.max(3, x(task.end) - x(task.start)))
      .attr('height', y.bandwidth())
      .attr('rx', 3)
      .attr('fill', (task) => task.color)
      .attr('stroke', (task) => (task.urgent ? 'currentColor' : 'none'))
      .attr('stroke-dasharray', (task) => (task.urgent ? '4 2' : null))
      .append('title')
      .text((task) => `${task.label}: ${xFormat(task.start)} → ${xFormat(task.end)}`)
  }, [dimensions.width, height, tasks, xFormat])

  return (
    <Box ref={ref} sx={{ width: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height }} />
    </Box>
  )
}
