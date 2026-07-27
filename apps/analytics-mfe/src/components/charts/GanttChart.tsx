import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Box } from '@mui/material'
import { useChartDimensions } from './useChartDimensions'
import { BrushOverlay } from './BrushOverlay'
import { selectedLinearDomain, useBrushZoom } from './useBrushZoom'

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
  brushZoomable?: boolean
}

const GANTT_MARGIN = { top: 10, right: 20, bottom: 30, left: 120 }

export function GanttChart({ tasks, height = 240, xFormat, brushZoomable = true }: GanttChartProps) {
  const { ref, dimensions } = useChartDimensions(height)
  const svgRef = useRef<SVGSVGElement>(null)
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null)
  const fullDomain = useMemo<[number, number] | null>(() => {
    if (tasks.length === 0) return null
    return [Math.min(...tasks.map((task) => task.start)), Math.max(...tasks.map((task) => task.end))]
  }, [tasks])
  const domainKey = fullDomain?.join(':') ?? 'empty'
  const xDomain = zoomDomain ?? fullDomain
  const xScale = useMemo(() => {
    if (!xDomain) return null
    return d3
      .scaleLinear()
      .domain(xDomain)
      .range([GANTT_MARGIN.left, dimensions.width - GANTT_MARGIN.right])
  }, [dimensions.width, xDomain])
  const visibleTasks = useMemo(
    () =>
      zoomDomain
        ? tasks.filter((task) => task.end >= zoomDomain[0] && task.start <= zoomDomain[1])
        : tasks,
    [tasks, zoomDomain],
  )

  useEffect(() => {
    setZoomDomain(null)
  }, [domainKey])

  const handleBrushEnd = useCallback(
    (range: [number, number]) => {
      if (!xScale) return
      const nextDomain = selectedLinearDomain(xScale, range)
      if (nextDomain) {
        setZoomDomain(nextDomain)
      }
    },
    [xScale],
  )

  const brush = useBrushZoom({
    targetRef: svgRef,
    width: dimensions.width,
    height,
    bounds: {
      x: GANTT_MARGIN.left,
      y: GANTT_MARGIN.top,
      width: Math.max(0, dimensions.width - GANTT_MARGIN.left - GANTT_MARGIN.right),
      height: Math.max(0, height - GANTT_MARGIN.top - GANTT_MARGIN.bottom),
    },
    enabled: brushZoomable && Boolean(xScale),
    isZoomed: Boolean(zoomDomain),
    onBrushEnd: handleBrushEnd,
    onReset: () => setZoomDomain(null),
  })

  useEffect(() => {
    const node = svgRef.current
    if (!node || tasks.length === 0 || !xScale || !xDomain) {
      return
    }
    const width = dimensions.width
    const margin = GANTT_MARGIN
    const y = d3
      .scaleBand<string>()
      .domain(visibleTasks.map((task) => task.id))
      .range([margin.top, height - margin.bottom])
      .padding(0.3)

    const svg = d3.select(node)
    svg.selectAll('*').remove()
    svg.attr('viewBox', `0 0 ${width} ${height}`)

    svg
      .append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .attr('color', 'currentColor')
      .call(d3.axisBottom(xScale).ticks(6).tickFormat((value) => xFormat(Number(value))))
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
      .data(visibleTasks)
      .join('rect')
      .attr('x', (task) => xScale(Math.max(task.start, xDomain[0])))
      .attr('y', (task) => y(task.id) ?? 0)
      .attr('width', (task) => Math.max(3, xScale(Math.min(task.end, xDomain[1])) - xScale(Math.max(task.start, xDomain[0]))))
      .attr('height', y.bandwidth())
      .attr('rx', 3)
      .attr('fill', (task) => task.color)
      .attr('stroke', (task) => (task.urgent ? 'currentColor' : 'none'))
      .attr('stroke-dasharray', (task) => (task.urgent ? '4 2' : null))
      .append('title')
      .text((task) => `${task.label}: ${xFormat(task.start)} → ${xFormat(task.end)}`)
  }, [dimensions.width, height, tasks, visibleTasks, xFormat, xScale, xDomain])

  return (
    <Box ref={ref} sx={{ position: 'relative', width: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height }} />
      <BrushOverlay width={dimensions.width} height={height} selection={brush.selection} />
    </Box>
  )
}
