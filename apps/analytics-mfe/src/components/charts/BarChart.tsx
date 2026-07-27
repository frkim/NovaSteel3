import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Box } from '@mui/material'
import { useChartDimensions } from './useChartDimensions'
import { CHART_MARGIN } from './chartUtils'
import { BrushOverlay } from './BrushOverlay'
import { selectedBandDomain, useBrushZoom } from './useBrushZoom'

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
  brushZoomable?: boolean
}

export function BarChart({ groups, series, height = 260, yFormat, brushZoomable = true }: BarChartProps) {
  const { ref, dimensions } = useChartDimensions(height)
  const svgRef = useRef<SVGSVGElement>(null)
  const [zoomLabels, setZoomLabels] = useState<string[] | null>(null)
  const labels = useMemo(() => groups.map((group) => group.label), [groups])
  const labelsKey = labels.join('\u0000')
  const visibleGroups = useMemo(
    () => (zoomLabels ? groups.filter((group) => zoomLabels.includes(group.label)) : groups),
    [groups, zoomLabels],
  )
  const x0 = useMemo(
    () =>
      d3
        .scaleBand<string>()
        .domain(visibleGroups.map((group) => group.label))
        .range([CHART_MARGIN.left, dimensions.width - CHART_MARGIN.right])
        .paddingInner(0.2),
    [dimensions.width, visibleGroups],
  )

  useEffect(() => {
    setZoomLabels(null)
  }, [labelsKey])

  const handleBrushEnd = useCallback(
    (range: [number, number]) => {
      const selected = selectedBandDomain(
        x0,
        visibleGroups.map((group) => group.label),
        range,
      )
      if (selected.length > 0 && selected.length < visibleGroups.length) {
        setZoomLabels(selected)
      }
    },
    [visibleGroups, x0],
  )

  const brush = useBrushZoom({
    targetRef: svgRef,
    width: dimensions.width,
    height,
    bounds: {
      x: CHART_MARGIN.left,
      y: CHART_MARGIN.top,
      width: Math.max(0, dimensions.width - CHART_MARGIN.left - CHART_MARGIN.right),
      height: Math.max(0, height - CHART_MARGIN.top - CHART_MARGIN.bottom),
    },
    enabled: brushZoomable && visibleGroups.length > 1,
    isZoomed: Boolean(zoomLabels),
    onBrushEnd: handleBrushEnd,
    onReset: () => setZoomLabels(null),
  })

  useEffect(() => {
    const node = svgRef.current
    if (!node || groups.length === 0) {
      return
    }
    const width = dimensions.width
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
      .data(visibleGroups)
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
  }, [dimensions.width, height, groups, visibleGroups, series, yFormat, x0])

  return (
    <Box ref={ref} sx={{ position: 'relative', width: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height }} />
      <BrushOverlay width={dimensions.width} height={height} selection={brush.selection} />
    </Box>
  )
}
