import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { Box, Stack, Typography } from '@mui/material'

export interface DonutSlice {
  label: string
  value: number
  color: string
}

export interface DonutChartProps {
  slices: DonutSlice[]
  height?: number
  centerLabel?: string
  centerValue?: string
}

export function DonutChart({ slices, height = 220, centerLabel, centerValue }: DonutChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    const node = svgRef.current
    if (!node) {
      return
    }
    const size = height
    const radius = size / 2
    const svg = d3.select(node)
    svg.selectAll('*').remove()
    svg.attr('viewBox', `0 0 ${size} ${size}`)
    const group = svg.append('g').attr('transform', `translate(${radius},${radius})`)
    const pie = d3
      .pie<DonutSlice>()
      .value((slice) => slice.value)
      .sort(null)
    const arc = d3
      .arc<d3.PieArcDatum<DonutSlice>>()
      .innerRadius(radius * 0.62)
      .outerRadius(radius * 0.96)
    group
      .selectAll('path')
      .data(pie(slices.filter((slice) => slice.value > 0)))
      .join('path')
      .attr('d', arc)
      .attr('fill', (slice) => slice.data.color)
      .attr('stroke', 'var(--ns-color-surface, #fff)')
      .attr('stroke-width', 2)
      .append('title')
      .text((slice) => `${slice.data.label}: ${slice.data.value}`)

    if (centerValue) {
      group
        .append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '-0.1em')
        .attr('font-size', 22)
        .attr('font-weight', 700)
        .attr('fill', 'currentColor')
        .text(centerValue)
    }
    if (centerLabel) {
      group
        .append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '1.2em')
        .attr('font-size', 11)
        .attr('fill', 'currentColor')
        .attr('opacity', 0.7)
        .text(centerLabel)
    }
  }, [slices, height, centerLabel, centerValue])

  return (
    <Stack direction="row" spacing={2} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
      <Box sx={{ width: height, height }}>
        <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />
      </Box>
      <Stack spacing={0.5} component="ul" sx={{ listStyle: 'none', p: 0, m: 0 }}>
        {slices.map((slice) => (
          <Stack
            key={slice.label}
            component="li"
            direction="row"
            spacing={1}
            sx={{ alignItems: 'center' }}
          >
            <Box aria-hidden sx={{ width: 12, height: 12, borderRadius: '2px', bgcolor: slice.color }} />
            <Typography variant="body2">
              {slice.label}: <strong>{slice.value}</strong>
            </Typography>
          </Stack>
        ))}
      </Stack>
    </Stack>
  )
}
