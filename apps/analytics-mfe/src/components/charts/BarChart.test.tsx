import { afterEach, describe, expect, it, vi } from 'vitest'
import { fireEvent } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { ChartContainer } from './ChartContainer'
import { BarChart, type BarGroup, type BarSeries } from './BarChart'

const groups: BarGroup[] = [
  { label: 'A', values: { baseline: 10, actual: 12 } },
  { label: 'B', values: { baseline: 20, actual: 22 } },
  { label: 'C', values: { baseline: 30, actual: 32 } },
  { label: 'D', values: { baseline: 40, actual: 42 } },
]

const series: BarSeries[] = [
  { id: 'baseline', label: 'Baseline', color: '#0078d4' },
  { id: 'actual', label: 'Actual', color: '#107c10' },
]

function mockChartRect(width = 640, height = 260) {
  const rect = {
    bottom: height,
    height,
    left: 0,
    right: width,
    top: 0,
    width,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  }
  vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue(rect)
  vi.spyOn(SVGElement.prototype, 'getBoundingClientRect').mockReturnValue(rect)
}

afterEach(() => {
  vi.restoreAllMocks()
})

function findChartSvg(container: HTMLElement): SVGSVGElement {
  const svg = [...container.querySelectorAll('svg')].find((candidate) =>
    candidate.getAttribute('viewBox')?.startsWith('0 0 640 '),
  )
  if (!svg) throw new Error('Chart SVG not found')
  return svg
}

describe('BarChart brush zoom', () => {
  it('filters ordinal x groups after a horizontal brush', () => {
    mockChartRect()
    const { container } = renderWithProviders(
      <ChartContainer title="Bars" summary="Bar summary">
        <BarChart groups={groups} series={series} yFormat={(value) => String(value)} />
      </ChartContainer>,
    )
    const chartSvg = findChartSvg(container)

    expect(container.querySelectorAll('rect')).toHaveLength(8)

    fireEvent.pointerDown(chartSvg, { button: 0, clientX: 185, clientY: 40, pointerId: 1 })
    fireEvent.pointerMove(window, { clientX: 455, clientY: 40, pointerId: 1 })
    fireEvent.pointerUp(window, { clientX: 455, clientY: 40, pointerId: 1 })

    expect(container.querySelectorAll('rect')).toHaveLength(4)
  })
})
