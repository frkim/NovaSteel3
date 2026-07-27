# Charts Wave 6 — Handoff Notes

## Translation strings

Zoom controls now use `t('chart.zoomIn')`, `t('chart.zoomOut')`,
`t('chart.zoomReset')`, and `t('chart.zoomLevel', { level })` — all
resolved from `chartMessages.ts` (wired by the owner into `CATALOGS`).

## SensorChartPanel collision (action required)

`SensorChartPanel.tsx` renders its own data-range zoom buttons
(`t('device.chart.zoomIn')` → "Zoom in") in a `ButtonGroup` **above**
`ChartContainer`, which now also renders visual-zoom buttons with
`t('chart.zoomIn')` → "Zoom in". The identical English labels cause
`SensorChartPanel.test.tsx` to fail on `getByRole('button', { name: 'Zoom in' })`.

**Fix:** pass `zoomable={false}` to the `<ChartContainer>` in
`SensorChartPanel.tsx` (line ~392). The panel already owns its own
data-range zoom so the container's visual zoom is redundant there.
