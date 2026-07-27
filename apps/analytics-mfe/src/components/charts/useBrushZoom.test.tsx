import { afterEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { useRef, useState } from 'react'
import { BrushOverlay } from './BrushOverlay'
import { useBrushZoom } from './useBrushZoom'

function mockSvgRect(width = 200, height = 100) {
  vi.spyOn(SVGElement.prototype, 'getBoundingClientRect').mockReturnValue({
    bottom: height,
    height,
    left: 0,
    right: width,
    top: 0,
    width,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  })
}

function BrushHarness({ onBrushEnd }: { onBrushEnd: (range: [number, number]) => void }) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [zoomed, setZoomed] = useState(false)
  const brush = useBrushZoom({
    targetRef: svgRef,
    width: 200,
    height: 100,
    bounds: { x: 20, y: 10, width: 160, height: 80 },
    isZoomed: zoomed,
    onBrushEnd: (range) => {
      setZoomed(true)
      onBrushEnd(range)
    },
    onReset: () => setZoomed(false),
  })

  return (
    <div style={{ position: 'relative', width: 200, height: 100 }}>
      <svg ref={svgRef} data-testid="brush-target" viewBox="0 0 200 100" />
      <BrushOverlay width={200} height={100} selection={brush.selection} />
    </div>
  )
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('useBrushZoom', () => {
  it('renders a selection rectangle and commits the selected range', () => {
    mockSvgRect()
    const onBrushEnd = vi.fn()
    render(<BrushHarness onBrushEnd={onBrushEnd} />)

    const target = screen.getByTestId('brush-target')
    fireEvent.pointerDown(target, { button: 0, clientX: 30, clientY: 20, pointerId: 1 })
    fireEvent.pointerMove(window, { clientX: 110, clientY: 20, pointerId: 1 })

    expect(Number(screen.getByTestId('chart-brush-selection').getAttribute('width'))).toBeCloseTo(80)

    fireEvent.pointerUp(window, { clientX: 110, clientY: 20, pointerId: 1 })

    const range = onBrushEnd.mock.calls[0]?.[0]
    expect(range?.[0]).toBeCloseTo(30)
    expect(range?.[1]).toBeCloseTo(110)
    expect(screen.queryByTestId('chart-brush-selection')).not.toBeInTheDocument()
  })

  it('cancels an in-progress brush with Escape', () => {
    mockSvgRect()
    const onBrushEnd = vi.fn()
    render(<BrushHarness onBrushEnd={onBrushEnd} />)

    const target = screen.getByTestId('brush-target')
    fireEvent.pointerDown(target, { button: 0, clientX: 30, clientY: 20, pointerId: 1 })
    fireEvent.pointerMove(window, { clientX: 110, clientY: 20, pointerId: 1 })
    fireEvent.keyDown(window, { key: 'Escape' })
    fireEvent.pointerUp(window, { clientX: 110, clientY: 20, pointerId: 1 })

    expect(onBrushEnd).not.toHaveBeenCalled()
    expect(screen.queryByTestId('chart-brush-selection')).not.toBeInTheDocument()
  })

  it('treats a drag shorter than eight pixels as a click', () => {
    mockSvgRect()
    const onBrushEnd = vi.fn()
    render(<BrushHarness onBrushEnd={onBrushEnd} />)

    const target = screen.getByTestId('brush-target')
    fireEvent.pointerDown(target, { button: 0, clientX: 30, clientY: 20, pointerId: 1 })
    fireEvent.pointerMove(window, { clientX: 36, clientY: 20, pointerId: 1 })
    fireEvent.pointerUp(window, { clientX: 36, clientY: 20, pointerId: 1 })

    expect(onBrushEnd).not.toHaveBeenCalled()
  })
})
