import { createContext, useContext } from 'react'

export interface ChartDataZoomRegistration {
  isZoomed: boolean
  reset: () => void
}

export interface ChartZoomContextValue {
  brushZoomEnabled: boolean
  registerDataZoom?: (registration: ChartDataZoomRegistration) => () => void
}

const DEFAULT_CHART_ZOOM_CONTEXT: ChartZoomContextValue = {
  brushZoomEnabled: true,
}

export const ChartZoomContext = createContext<ChartZoomContextValue>(DEFAULT_CHART_ZOOM_CONTEXT)

export function useChartZoomContext(): ChartZoomContextValue {
  return useContext(ChartZoomContext)
}
