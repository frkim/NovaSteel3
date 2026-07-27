import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Box } from '@mui/material'
import { useChartDimensions } from './useChartDimensions'
import { CHART_MARGIN } from './chartUtils'
import { BrushOverlay } from './BrushOverlay'
import { selectedLinearDomain, useBrushZoom } from './useBrushZoom'

export interface StackKey {
  id: string
  label: string
  color: string
}

export interface AreaDatum {
  x: number
  values: Record<string, number>
}

export interface AreaChartProps {
  data: AreaDatum[]
  keys: StackKey[]
  height?: number
  xFormat: (value: number) => string
  yFormat: (value: number) => string
  brushZoomable?: boolean
}

export function AreaChart({ data, keys, height = 240, xFormat, yFormat, brushZoomable = true }: AreaChartProps) {
  const { ref, dimensions } = useChartDimensions(height)
  const svgRef = useRef<SVGSVGElement>(null)
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null)
  const fullDomain = useMemo<[number, number] | null>(() => {
    if (data.length === 0) return null
    return d3.extent(data, (datum) => datum.x) as [number, number]
  }, [data])
  const domainKey = fullDomain?.join(':') ?? 'empty'
  const xDomain = zoomDomain ?? fullDomain
  const xScale = useMemo(() => {
    if (!xDomain) return null
    return d3
      .scaleLinear()
      .domain(xDomain)
      .range([CHART_MARGIN.left, dimensions.width - CHART_MARGIN.right])
  }, [dimensions.width, xDomain])
  const visibleData = useMemo(
    () => (zoomDomain ? data.filter((datum) => datum.x >= zoomDomain[0] && datum.x <= zoomDomain[1]) : data),
    [data, zoomDomain],
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
    if (!node || data.length === 0 || !xScale) {
      return
    }
    const width = dimensions.width
    const stack = d3
      .stack<AreaDatum>()
      .keys(keys.map((key) => key.id))
      .value((datum, key) => datum.values[key] ?? 0)
    const stacked = stack(visibleData)
    const fullStacked = stack(data)
    const maxTotal = d3.max(fullStacked, (layer) => d3.max(layer, (point) => point[1])) ?? 1
    const y = d3
      .scaleLinear()
      .domain([0, maxTotal])
      .nice()
      .range([height - CHART_MARGIN.bottom, CHART_MARGIN.top])

    const svg = d3.select(node)
    svg.selectAll('*').remove()
    svg.attr('viewBox', `0 0 ${width} ${height}`)

    svg
      .append('g')
      .attr('transform', `translate(0,${height - CHART_MARGIN.bottom})`)
      .attr('color', 'currentColor')
      .call(d3.axisBottom(xScale).ticks(6).tickFormat((value) => xFormat(Number(value))))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))
    svg
      .append('g')
      .attr('transform', `translate(${CHART_MARGIN.left},0)`)
      .attr('color', 'currentColor')
      .call(d3.axisLeft(y).ticks(5).tickFormat((value) => yFormat(Number(value))))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))

    const area = d3
      .area<d3.SeriesPoint<AreaDatum>>()
      .x((point) => xScale(point.data.x))
      .y0((point) => y(point[0]))
      .y1((point) => y(point[1]))
      .curve(d3.curveMonotoneX)

    svg
      .append('g')
      .selectAll('path')
      .data(stacked)
      .join('path')
      .attr('fill', (layer) => keys.find((key) => key.id === layer.key)?.color ?? '#888')
      .attr('fill-opacity', 0.75)
      .attr('stroke', (layer) => keys.find((key) => key.id === layer.key)?.color ?? '#888')
      .attr('stroke-width', 1)
      .attr('d', area)
      .append('title')
      .text((layer) => keys.find((key) => key.id === layer.key)?.label ?? layer.key)
  }, [dimensions.width, height, data, visibleData, keys, xFormat, yFormat, xScale])

  return (
    <Box ref={ref} sx={{ position: 'relative', width: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height }} />
      <BrushOverlay width={dimensions.width} height={height} selection={brush.selection} />
    </Box>
  )
}
