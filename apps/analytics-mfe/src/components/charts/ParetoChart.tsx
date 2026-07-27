import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Box } from '@mui/material'
import { useChartDimensions } from './useChartDimensions'
import { BrushOverlay } from './BrushOverlay'
import { selectedBandDomain, useBrushZoom } from './useBrushZoom'

export interface ParetoItem {
  label: string
  count: number
}

export interface ParetoChartProps {
  items: ParetoItem[]
  barColor: string
  lineColor: string
  height?: number
  brushZoomable?: boolean
}

const PARETO_MARGIN = { top: 12, right: 44, bottom: 60, left: 44 }

export function ParetoChart({ items, barColor, lineColor, height = 260, brushZoomable = true }: ParetoChartProps) {
  const { ref, dimensions } = useChartDimensions(height)
  const svgRef = useRef<SVGSVGElement>(null)
  const [zoomLabels, setZoomLabels] = useState<string[] | null>(null)
  const ordered = useMemo(() => [...items].sort((a, b) => b.count - a.count), [items])
  const labels = useMemo(() => ordered.map((item) => item.label), [ordered])
  const labelsKey = labels.join('\u0000')
  const visibleOrdered = useMemo(
    () => (zoomLabels ? ordered.filter((item) => zoomLabels.includes(item.label)) : ordered),
    [ordered, zoomLabels],
  )
  const xScale = useMemo(
    () =>
      d3
        .scaleBand<string>()
        .domain(visibleOrdered.map((item) => item.label))
        .range([PARETO_MARGIN.left, dimensions.width - PARETO_MARGIN.right])
        .padding(0.25),
    [dimensions.width, visibleOrdered],
  )

  useEffect(() => {
    setZoomLabels(null)
  }, [labelsKey])

  const handleBrushEnd = useCallback(
    (range: [number, number]) => {
      const selected = selectedBandDomain(xScale, visibleOrdered.map((item) => item.label), range)
      if (selected.length > 0 && selected.length < visibleOrdered.length) {
        setZoomLabels(selected)
      }
    },
    [visibleOrdered, xScale],
  )

  const brush = useBrushZoom({
    targetRef: svgRef,
    width: dimensions.width,
    height,
    bounds: {
      x: PARETO_MARGIN.left,
      y: PARETO_MARGIN.top,
      width: Math.max(0, dimensions.width - PARETO_MARGIN.left - PARETO_MARGIN.right),
      height: Math.max(0, height - PARETO_MARGIN.top - PARETO_MARGIN.bottom),
    },
    enabled: brushZoomable && visibleOrdered.length > 1,
    isZoomed: Boolean(zoomLabels),
    onBrushEnd: handleBrushEnd,
    onReset: () => setZoomLabels(null),
  })

  useEffect(() => {
    const node = svgRef.current
    if (!node || items.length === 0) {
      return
    }
    const width = dimensions.width
    const margin = PARETO_MARGIN
    const total = d3.sum(visibleOrdered, (item) => item.count) || 1
    let cumulative = 0
    const cumulativePoints = visibleOrdered.map((item) => {
      cumulative += item.count
      return { label: item.label, pct: (cumulative / total) * 100 }
    })

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
      .call(d3.axisBottom(xScale))
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
      .data(visibleOrdered)
      .join('rect')
      .attr('x', (item) => xScale(item.label) ?? 0)
      .attr('y', (item) => yLeft(item.count))
      .attr('width', xScale.bandwidth())
      .attr('height', (item) => yLeft(0) - yLeft(item.count))
      .attr('rx', 2)
      .attr('fill', barColor)
      .append('title')
      .text((item) => `${item.label}: ${item.count}`)

    const line = d3
      .line<{ label: string; pct: number }>()
      .x((point) => (xScale(point.label) ?? 0) + xScale.bandwidth() / 2)
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
      .attr('cx', (point) => (xScale(point.label) ?? 0) + xScale.bandwidth() / 2)
      .attr('cy', (point) => yRight(point.pct))
      .attr('r', 3)
      .attr('fill', lineColor)
      .append('title')
      .text((point) => `${point.label}: ${point.pct.toFixed(1)}% cumulative`)
  }, [dimensions.width, height, items, ordered, visibleOrdered, barColor, lineColor, xScale])

  return (
    <Box ref={ref} sx={{ position: 'relative', width: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height }} />
      <BrushOverlay width={dimensions.width} height={height} selection={brush.selection} />
    </Box>
  )
}
