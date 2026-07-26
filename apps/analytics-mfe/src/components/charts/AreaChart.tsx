import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { Box } from '@mui/material'
import { useChartDimensions } from './useChartDimensions'
import { CHART_MARGIN } from './chartUtils'

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
}

export function AreaChart({ data, keys, height = 240, xFormat, yFormat }: AreaChartProps) {
  const { ref, dimensions } = useChartDimensions(height)
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    const node = svgRef.current
    if (!node || data.length === 0) {
      return
    }
    const width = dimensions.width
    const stack = d3
      .stack<AreaDatum>()
      .keys(keys.map((key) => key.id))
      .value((datum, key) => datum.values[key] ?? 0)
    const stacked = stack(data)
    const x = d3
      .scaleLinear()
      .domain(d3.extent(data, (datum) => datum.x) as [number, number])
      .range([CHART_MARGIN.left, width - CHART_MARGIN.right])
    const maxTotal = d3.max(stacked, (layer) => d3.max(layer, (point) => point[1])) ?? 1
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
      .call(d3.axisBottom(x).ticks(6).tickFormat((value) => xFormat(Number(value))))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))
    svg
      .append('g')
      .attr('transform', `translate(${CHART_MARGIN.left},0)`)
      .attr('color', 'currentColor')
      .call(d3.axisLeft(y).ticks(5).tickFormat((value) => yFormat(Number(value))))
      .call((axis) => axis.selectAll('text').attr('font-size', 11))

    const area = d3
      .area<d3.SeriesPoint<AreaDatum>>()
      .x((point) => x(point.data.x))
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
  }, [dimensions.width, height, data, keys, xFormat, yFormat])

  return (
    <Box ref={ref} sx={{ width: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height }} />
    </Box>
  )
}
