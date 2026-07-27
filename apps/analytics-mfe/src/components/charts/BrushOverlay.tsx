export interface BrushSelection {
  x: number
  y: number
  width: number
  height: number
}

export interface BrushOverlayProps {
  width: number
  height: number
  selection: BrushSelection | null
}

export function BrushOverlay({ width, height, selection }: BrushOverlayProps) {
  if (!selection) {
    return null
  }

  return (
    <svg
      aria-hidden="true"
      viewBox={`0 0 ${width} ${height}`}
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height,
        pointerEvents: 'none',
      }}
    >
      <rect
        data-testid="chart-brush-selection"
        x={selection.x}
        y={selection.y}
        width={selection.width}
        height={selection.height}
        fill="rgba(0, 120, 212, 0.16)"
        stroke="#0078d4"
        strokeWidth={1}
      />
    </svg>
  )
}
