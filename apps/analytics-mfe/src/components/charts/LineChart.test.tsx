import { afterEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { createTranslator } from '../../i18n/messages'
import { ChartContainer } from './ChartContainer'
import { LineChart, type LineSeries } from './LineChart'

const series: LineSeries[] = [
  {
    id: 'risk',
    label: 'Median risk',
    color: '#0078d4',
    points: [
      { x: 0, y: 0.1 },
      { x: 10, y: 0.5 },
      { x: 20, y: 0.9 },
    ],
  },
]

const xFormat = (value: number) => `d${value}`
const yFormat = (value: number) => value.toFixed(1)
const t = createTranslator('en-LU')

function mockChartRect(width = 640, height = 300) {
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

function renderLineInContainer() {
  return renderWithProviders(
    <ChartContainer title="Line" summary="Line summary">
      <LineChart series={series} height={300} xFormat={xFormat} yFormat={yFormat} />
    </ChartContainer>,
  )
}

function findChartSvg(container: HTMLElement): SVGSVGElement {
  const svg = [...container.querySelectorAll('svg')].find((candidate) =>
    candidate.getAttribute('viewBox')?.startsWith('0 0 640 '),
  )
  if (!svg) throw new Error('Chart SVG not found')
  return svg
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('LineChart', () => {
  it('does not trigger a render loop when the measured width updates', () => {
    mockChartRect(720, 300)

    const { container, rerender } = render(
      <LineChart series={series} height={300} xFormat={xFormat} yFormat={yFormat} />,
    )

    rerender(<LineChart series={series} height={300} xFormat={xFormat} yFormat={yFormat} />)

    expect(container.querySelectorAll('svg')).toHaveLength(1)
    expect(container.querySelector('svg')).toHaveAttribute('viewBox', '0 0 720 300')
  })

  it('brush zooms the x domain and reset restores it', () => {
    mockChartRect()
    const { container } = renderLineInContainer()
    const chartSvg = findChartSvg(container)

    expect(container.querySelectorAll('circle')).toHaveLength(3)

    fireEvent.pointerDown(chartSvg, { button: 0, clientX: 44, clientY: 40, pointerId: 1 })
    fireEvent.pointerMove(window, { clientX: 332, clientY: 40, pointerId: 1 })
    fireEvent.pointerUp(window, { clientX: 332, clientY: 40, pointerId: 1 })

    expect(container.querySelectorAll('circle')).toHaveLength(2)

    fireEvent.click(screen.getByRole('button', { name: t('chart.selectZoomReset') }))

    expect(container.querySelectorAll('circle')).toHaveLength(3)
  })

  it('ignores brush drags shorter than eight pixels', () => {
    mockChartRect()
    const { container } = renderLineInContainer()
    const chartSvg = findChartSvg(container)

    fireEvent.pointerDown(chartSvg, { button: 0, clientX: 100, clientY: 40, pointerId: 1 })
    fireEvent.pointerMove(window, { clientX: 106, clientY: 40, pointerId: 1 })
    fireEvent.pointerUp(window, { clientX: 106, clientY: 40, pointerId: 1 })

    expect(container.querySelectorAll('circle')).toHaveLength(3)
    expect(screen.queryByRole('button', { name: t('chart.selectZoomReset') })).not.toBeInTheDocument()
  })
})
