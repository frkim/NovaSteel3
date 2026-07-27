import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Box } from '@mui/material'
import { useChartDimensions } from './useChartDimensions'
import { CHART_MARGIN, niceExtent, type TooltipState } from './chartUtils'
import { BrushOverlay } from './BrushOverlay'
import { selectedLinearDomain, useBrushZoom } from './useBrushZoom'

export interface LinePoint {
  x: number
  y: number
}

export interface LineSeries {
  id: string
  label: string
  color: string
  points: LinePoint[]
  dashed?: boolean
}

export interface ConfidenceArea {
  points: Array<{ x: number; low: number; high: number }>
  color: string
  label: string
}

export interface ThresholdMarker {
  value: number
  label: string
  color: string
}

export interface LineChartProps {
  series: LineSeries[]
  band?: ConfidenceArea
  threshold?: ThresholdMarker
  height?: number
  xFormat: (value: number) => string
  yFormat: (value: number) => string
  tooltipFormat?: (value: number) => string
  brushZoomable?: boolean
}

export function LineChart({
  series,
  band,
  threshold,
  height = 260,
  xFormat,
  yFormat,
  tooltipFormat,
  brushZoomable = true,
}: LineChartProps) {
  const { ref, dimensions } = useChartDimensions(height)
  const svgRef = useRef<SVGSVGElement>(null)
  const [tooltip, setTooltip] = useState<TooltipState | null>(null)
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null)
  const allX = useMemo(() => series.flatMap((entry) => entry.points.map((point) => point.x)), [series])
  const fullDomain = useMemo<[number, number] | null>(() => {
    if (allX.length === 0) return null
    return [Math.min(...allX), Math.max(...allX)]
  }, [allX])
  const domainKey = fullDomain?.join(':') ?? 'empty'
  const xDomain = zoomDomain ?? fullDomain
  const xScale = useMemo(() => {
    if (!xDomain) return null
    return d3
      .scaleLinear()
      .domain(xDomain)
      .range([CHART_MARGIN.left, dimensions.width - CHART_MARGIN.right])
  }, [dimensions.width, xDomain])
  const visibleSeries = useMemo(
    () =>
      zoomDomain
        ? series.map((entry) => ({
            ...entry,
            points: entry.points.filter((point) => point.x >= zoomDomain[0] && point.x <= zoomDomain[1]),
          }))
        : series,
    [series, zoomDomain],
  )
  const visibleBand = useMemo(
    () =>
      band && zoomDomain
        ? { ...band, points: band.points.filter((point) => point.x >= zoomDomain[0] && point.x <= zoomDomain[1]) }
        : band,
    [band, zoomDomain],
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
      x: CHART_MARGIN.left,
      y: CHART_MARGIN.top,
      width: Math.max(0, dimensions.width - CHART_MARGIN.left - CHART_MARGIN.right),
      height: Math.max(0, height - CHART_MARGIN.top - CHART_MARGIN.bottom),
    },
    enabled: brushZoomable && Boolean(xScale),
    isZoomed: Boolean(zoomDomain),
    onBrushEnd: handleBrushEnd,
    onReset: () => setZoomDomain(null),
  })

  useEffect(() => {
    const node = svgRef.current
    if (!node || !xScale || !fullDomain) {
      return
    }
    const width = dimensions.width
    const allY = [
      ...series.flatMap((entry) => entry.points.map((point) => point.y)),
      ...(band ? band.points.flatMap((point) => [point.low, point.high]) : []),
      ...(threshold ? [threshold.value] : []),
    ]
    const y = d3
      .scaleLinear()
      .domain(niceExtent(allY))
      .nice()
      .range([height - CHART_MARGIN.bottom, CHART_MARGIN.top])

    const svg = d3.select(node)
    svg.selectAll('*').remove()
    svg.attr('viewBox', `0 0 ${width} ${height}`)

    svg
      .append('g')
      .attr('transform', `translate(0,${height - CHART_MARGIN.bottom})`)
      .attr('color', 'currentColor')
      .call(d3.axisBottom(xScale).ticks(Math.min(6, allX.length)).tickFormat((value) => xFormat(Number(value))))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))
    svg
      .append('g')
      .attr('transform', `translate(${CHART_MARGIN.left},0)`)
      .attr('color', 'currentColor')
      .call(d3.axisLeft(y).ticks(5).tickFormat((value) => yFormat(Number(value))))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))

    if (visibleBand) {
      const area = d3
        .area<{ x: number; low: number; high: number }>()
        .x((point) => xScale(point.x))
        .y0((point) => y(point.low))
        .y1((point) => y(point.high))
        .curve(d3.curveMonotoneX)
      svg
        .append('path')
        .datum(visibleBand.points)
        .attr('fill', visibleBand.color)
        .attr('fill-opacity', 0.18)
        .attr('stroke', 'none')
        .attr('d', area)
    }

    if (threshold) {
      svg
        .append('line')
        .attr('x1', CHART_MARGIN.left)
        .attr('x2', width - CHART_MARGIN.right)
        .attr('y1', y(threshold.value))
        .attr('y2', y(threshold.value))
        .attr('stroke', threshold.color)
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '6 4')
      svg
        .append('text')
        .attr('x', width - CHART_MARGIN.right)
        .attr('y', y(threshold.value) - 4)
        .attr('text-anchor', 'end')
        .attr('fill', threshold.color)
        .attr('font-size', 11)
        .text(threshold.label)
    }

    const lineGenerator = d3
      .line<LinePoint>()
      .x((point) => xScale(point.x))
      .y((point) => y(point.y))
      .curve(d3.curveMonotoneX)

    for (const entry of visibleSeries) {
      svg
        .append('path')
        .datum(entry.points)
        .attr('fill', 'none')
        .attr('stroke', entry.color)
        .attr('stroke-width', 2.5)
        .attr('stroke-dasharray', entry.dashed ? '6 4' : null)
        .attr('d', lineGenerator)
      svg
        .append('g')
        .selectAll('circle')
        .data(entry.points)
        .join('circle')
        .attr('cx', (point) => xScale(point.x))
        .attr('cy', (point) => y(point.y))
        .attr('r', 2.5)
        .attr('fill', entry.color)
    }

    const focus = svg
      .append('line')
      .attr('stroke', 'currentColor')
      .attr('stroke-opacity', 0.4)
      .attr('y1', CHART_MARGIN.top)
      .attr('y2', height - CHART_MARGIN.bottom)
      .style('display', 'none')

    const primary = visibleSeries[0]
    const bisect = d3.bisector<LinePoint, number>((point) => point.x).center

    svg
      .append('rect')
      .attr('x', CHART_MARGIN.left)
      .attr('y', CHART_MARGIN.top)
      .attr('width', Math.max(0, width - CHART_MARGIN.left - CHART_MARGIN.right))
      .attr('height', Math.max(0, height - CHART_MARGIN.top - CHART_MARGIN.bottom))
      .attr('fill', 'transparent')
      .on('mousemove', (event: MouseEvent) => {
        if (!primary || primary.points.length === 0) {
          return
        }
        const [pointerX] = d3.pointer(event)
        const value = xScale.invert(pointerX)
        const index = bisect(primary.points, value)
        const point = primary.points[index]
        if (!point) {
          return
        }
        focus.attr('x1', xScale(point.x)).attr('x2', xScale(point.x)).style('display', null)
        setTooltip({
          x: xScale(point.x),
          y: y(point.y),
          content: `${xFormat(point.x)} · ${(tooltipFormat ?? yFormat)(point.y)}`,
        })
      })
      .on('mouseleave', () => {
        focus.style('display', 'none')
        setTooltip(null)
      })
  }, [
    dimensions.width,
    height,
    series,
    visibleSeries,
    band,
    visibleBand,
    threshold,
    xFormat,
    yFormat,
    tooltipFormat,
    allX.length,
    xScale,
    fullDomain,
  ])

  return (
    <Box ref={ref} sx={{ position: 'relative', width: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height }} />
      <BrushOverlay width={dimensions.width} height={height} selection={brush.selection} />
      {tooltip && (
        <div
          className="ns-chart-tooltip"
          style={{ left: tooltip.x, top: tooltip.y }}
          role="presentation"
        >
          {tooltip.content}
        </div>
      )}
    </Box>
  )
}
