import { afterEach, describe, expect, it, vi } from 'vitest'
import { render } from '@testing-library/react'
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

afterEach(() => {
  vi.restoreAllMocks()
})

describe('LineChart', () => {
  it('does not trigger a render loop when the measured width updates', () => {
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      bottom: 300,
      height: 300,
      left: 0,
      right: 720,
      top: 0,
      width: 720,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    })

    const { container, rerender } = render(
      <LineChart series={series} height={300} xFormat={xFormat} yFormat={yFormat} />,
    )

    rerender(<LineChart series={series} height={300} xFormat={xFormat} yFormat={yFormat} />)

    expect(container.querySelectorAll('svg')).toHaveLength(1)
    expect(container.querySelector('svg')).toHaveAttribute('viewBox', '0 0 720 300')
  })
})
