import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  ButtonGroup,
  FormControlLabel,
  IconButton,
  Stack,
  Switch,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { usePolling } from '../../hooks/usePolling'
import { useTokens } from '../../hooks/useTokens'
import type { SensorChartType, SeriesWindow } from '../../api/deviceDomain'
import { SENSOR_CHART_TYPES, SERIES_WINDOWS } from '../../api/deviceDomain'
import { ChartContainer } from '../charts/ChartContainer'
import { LineChart } from '../charts/LineChart'
import { AreaChart } from '../charts/AreaChart'
import { BarChart } from '../charts/BarChart'
import { ControlChart } from '../charts/ControlChart'
import { formatNumber, formatTime } from '../../utils/format'

export interface SensorChartPanelProps {
  sensorId: string
  onClose?: () => void
}

const BAR_MAX_GROUPS = 30

function computeStats(values: number[]) {
  if (values.length === 0) {
    return { min: 0, max: 0, mean: 0, stdDev: 0, last: 0 }
  }
  const min = Math.min(...values)
  const max = Math.max(...values)
  const mean = values.reduce((a, b) => a + b, 0) / values.length
  const variance = values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length
  const stdDev = Math.sqrt(variance)
  const last = values[values.length - 1]
  return { min, max, mean, stdDev, last }
}

export function SensorChartPanel({ sensorId, onClose }: SensorChartPanelProps) {
  const { deviceClient, locale, t } = useAnalytics()
  const tokens = useTokens()

  const [chartType, setChartType] = useState<SensorChartType>('line')
  const [window, setWindow] = useState<SeriesWindow>('1h')
  const [normalize, setNormalize] = useState(false)
  const [live, setLive] = useState(false)
  const [zoomState, setZoomState] = useState<{ start: number; end: number } | null>(null)

  const seriesState = useResource(
    () => deviceClient.getSeries(sensorId, window, 120),
    [deviceClient, sensorId, window],
  )

  // Reset zoom when sensor or window changes
  useEffect(() => {
    setZoomState(null)
  }, [sensorId, window])

  // Reload when the zoom state was just reset by a sensor/window change
  // (useResource already reloads on dep change; this just clears any stale zoom)

  // Live polling every 5 seconds
  usePolling(seriesState.reload, 5000, live)

  const series = seriesState.data

  const totalPoints = series ? (normalize ? series.normalizedPoints.length : series.points.length) : 0
  const zoomStart = zoomState?.start ?? 0
  const zoomEnd = zoomState?.end ?? Math.max(0, totalPoints - 1)

  const visiblePoints = useMemo(() => {
    if (!series) return []
    const src = normalize ? series.normalizedPoints : series.points
    return src.slice(zoomStart, zoomEnd + 1)
  }, [series, normalize, zoomStart, zoomEnd])

  const unit = normalize ? '(0–1)' : (series?.unit ?? '')

  const stats = useMemo(() => {
    return computeStats(visiblePoints.map((p) => p.v))
  }, [visiblePoints])

  const spanText = useMemo(() => {
    if (visiblePoints.length < 2) return ''
    return `${formatTime(visiblePoints[0].t, locale)} – ${formatTime(visiblePoints[visiblePoints.length - 1].t, locale)}`
  }, [visiblePoints, locale])

  // Zoom handlers
  const zoomIn = () => {
    const range = zoomEnd - zoomStart + 1
    const newRange = Math.max(5, Math.round(range * 0.6))
    const center = Math.round((zoomStart + zoomEnd) / 2)
    const newStart = Math.max(0, center - Math.floor(newRange / 2))
    const newEnd = Math.min(Math.max(0, totalPoints - 1), newStart + newRange - 1)
    setZoomState({ start: newStart, end: newEnd })
  }

  const zoomOut = () => {
    const range = zoomEnd - zoomStart + 1
    const newRange = Math.min(totalPoints, Math.round(range / 0.6))
    const center = Math.round((zoomStart + zoomEnd) / 2)
    const newStart = Math.max(0, center - Math.floor(newRange / 2))
    const newEnd = Math.min(Math.max(0, totalPoints - 1), newStart + newRange - 1)
    setZoomState({ start: newStart, end: newEnd })
  }

  const zoomReset = () => setZoomState(null)

  const isAtMaxZoom = visiblePoints.length <= 5
  const isAtMinZoom = visiblePoints.length >= totalPoints

  // Format helpers
  const yFmt = (v: number) =>
    formatNumber(v, locale, {
      maximumFractionDigits: normalize ? 4 : Math.abs(v) >= 100 ? 1 : 2,
    })
  const xFmt = (v: number) => String(Math.round(v))

  // Build chart data
  const linePoints = useMemo(
    () => visiblePoints.map((p, i) => ({ x: zoomStart + i, y: p.v })),
    [visiblePoints, zoomStart],
  )

  const areaData = useMemo(
    () => visiblePoints.map((p, i) => ({ x: zoomStart + i, values: { v: p.v } })),
    [visiblePoints, zoomStart],
  )

  const barPoints = useMemo(() => {
    const step = Math.max(1, Math.ceil(visiblePoints.length / BAR_MAX_GROUPS))
    return visiblePoints.filter((_, i) => i % step === 0)
  }, [visiblePoints])

  const barGroups = useMemo(
    () => barPoints.map((p) => ({ label: formatTime(p.t, locale), values: { v: p.v } })),
    [barPoints, locale],
  )

  const controlPoints = useMemo(
    () =>
      visiblePoints.map((p, i) => ({
        index: zoomStart + i,
        value: p.v,
        label: formatTime(p.t, locale),
      })),
    [visiblePoints, zoomStart, locale],
  )

  // Reference band for LineChart (nominal low/high range)
  const nominalBand = useMemo(() => {
    if (!series || normalize) return undefined
    return {
      points: linePoints.map((pt) => ({ x: pt.x, low: series.low, high: series.high })),
      color: tokens.status.warning,
      label: `Nominal ${series.low}–${series.high} ${series.unit}`,
    }
  }, [series, normalize, linePoints, tokens.status.warning])

  // UCL / LCL for control chart (use nominal limits if sensor range given, else ±3σ)
  const { ucl, lcl } = useMemo(() => {
    if (!series) return { ucl: stats.mean + 3 * stats.stdDev, lcl: stats.mean - 3 * stats.stdDev }
    // Prefer the domain limits as control limits so the chart is meaningful even with few points
    return { ucl: series.high, lcl: series.low }
  }, [series, stats.mean, stats.stdDev])

  // Summary text for ChartContainer
  const summary = useMemo(() => {
    if (!series) return ''
    const rangeNote = normalize
      ? 'Normalized 0–1.'
      : `Nominal range: ${series.low}–${series.high} ${series.unit}.`
    const spanNote = spanText ? `Window: ${spanText}.` : ''
    const statsNote = `Mean: ${yFmt(stats.mean)} · StdDev: ${yFmt(stats.stdDev)}.`
    const controlNote =
      chartType === 'area' || chartType === 'bar'
        ? ` Reference band: ${series.low}–${series.high} ${series.unit}.`
        : ''
    return `${series.displayName} time series (${window}). ${rangeNote} ${spanNote} ${statsNote}${controlNote}`
  }, [series, normalize, spanText, stats.mean, stats.stdDev, chartType, window, yFmt])

  // Table data for WCAG "View as table" fallback
  const tableColumns = [
    { key: 'time', label: 'Time' },
    { key: 'value', label: `Value${unit ? ` (${unit})` : ''}` },
  ]
  const tableRows = useMemo(
    () =>
      visiblePoints.map((p) => ({
        time: formatTime(p.t, locale),
        value: yFmt(p.v),
      })),
    [visiblePoints, locale, yFmt],
  )

  const chartTitle = series ? `${series.displayName} · ${window}${spanText ? ` · ${spanText}` : ''}` : t('device.chart.title')

  function renderChart() {
    if (!series || visiblePoints.length === 0) return null

    switch (chartType) {
      case 'line':
        return (
          <LineChart
            series={[
              { id: 'v', label: series.displayName, color: tokens.palette[0], points: linePoints },
            ]}
            band={nominalBand}
            height={260}
            xFormat={xFmt}
            yFormat={yFmt}
          />
        )
      case 'area':
        return (
          <AreaChart
            data={areaData}
            keys={[{ id: 'v', label: series.displayName, color: tokens.palette[0] }]}
            height={260}
            xFormat={xFmt}
            yFormat={yFmt}
          />
        )
      case 'bar':
        return (
          <BarChart
            groups={barGroups}
            series={[{ id: 'v', label: series.displayName, color: tokens.palette[0] }]}
            height={260}
            yFormat={yFmt}
          />
        )
      case 'control':
        return (
          <ControlChart
            points={controlPoints}
            mean={stats.mean}
            ucl={ucl}
            lcl={lcl}
            color={tokens.palette[0]}
            violationColor={tokens.status.critical}
            height={260}
            yFormat={yFmt}
          />
        )
    }
  }

  return (
    <Box
      component="section"
      aria-label={chartTitle}
      sx={{ scrollMarginTop: 16 }}
    >
      {/* Controls row */}
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        spacing={1}
        sx={{ alignItems: { sm: 'center' }, flexWrap: 'wrap', mb: 1 }}
      >
        {/* Chart type */}
        <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            {t('device.chart.type.label')}
          </Typography>
          <ToggleButtonGroup
            value={chartType}
            exclusive
            onChange={(_, val) => val && setChartType(val as SensorChartType)}
            aria-label={t('device.chart.type.label')}
            size="small"
          >
            {SENSOR_CHART_TYPES.map((type) => (
              <ToggleButton key={type} value={type} aria-label={type}>
                {type}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Stack>

        {/* Window */}
        <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            {t('device.chart.window.label')}
          </Typography>
          <ToggleButtonGroup
            value={window}
            exclusive
            onChange={(_, val) => val && setWindow(val as SeriesWindow)}
            aria-label={t('device.chart.window.label')}
            size="small"
          >
            {SERIES_WINDOWS.map((w) => (
              <ToggleButton key={w} value={w} aria-label={w}>
                {w}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Stack>

        {/* Normalize */}
        <FormControlLabel
          control={
            <Switch
              checked={normalize}
              onChange={(e) => setNormalize(e.target.checked)}
              size="small"
            />
          }
          label={
            <Typography variant="caption">{t('device.chart.normalize')}</Typography>
          }
        />

        {/* Live */}
        <FormControlLabel
          control={
            <Switch
              checked={live}
              onChange={(e) => setLive(e.target.checked)}
              size="small"
            />
          }
          label={
            <Typography variant="caption">{t('device.chart.live')}</Typography>
          }
        />

        <Box sx={{ flex: 1 }} />

        {/* Zoom */}
        <ButtonGroup size="small" aria-label="Zoom controls">
          <Button
            onClick={zoomIn}
            disabled={!series || isAtMaxZoom}
            aria-label={t('device.chart.zoomIn')}
          >
            +
          </Button>
          <Button
            onClick={zoomOut}
            disabled={!series || isAtMinZoom}
            aria-label={t('device.chart.zoomOut')}
          >
            −
          </Button>
          <Button
            onClick={zoomReset}
            disabled={!series || zoomState === null}
            aria-label={t('device.chart.zoomReset')}
          >
            {t('device.chart.zoomReset')}
          </Button>
        </ButtonGroup>

        {/* Close */}
        {onClose && (
          <Tooltip title={t('device.chart.close')}>
            <IconButton aria-label={t('device.chart.close')} onClick={onClose} size="small">
              <CloseIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Stack>

      {/* Loading / error */}
      {seriesState.status === 'error' && (
        <Alert severity="error" sx={{ mb: 1 }}>
          {seriesState.error?.message ?? 'Failed to load series data.'}
        </Alert>
      )}

      {/* No data */}
      {seriesState.status === 'ready' && !series && (
        <Alert severity="info">{t('device.chart.noData')}</Alert>
      )}

      {/* Chart */}
      {series && (
        <>
          <ChartContainer
            title={chartTitle}
            summary={summary}
            height={260}
            tableColumns={tableColumns}
            tableRows={tableRows}
          >
            {renderChart()}
          </ChartContainer>

          {/* Stats strip */}
          <Stack
            direction="row"
            spacing={2}
            sx={{ flexWrap: 'wrap', mt: 1, px: 1 }}
            role="list"
            aria-label="Sensor statistics"
          >
            {(
              [
                { key: 'min', value: stats.min },
                { key: 'max', value: stats.max },
                { key: 'mean', value: stats.mean },
                { key: 'stdDev', value: stats.stdDev },
                { key: 'last', value: stats.last },
              ] as const
            ).map(({ key, value }) => (
              <Tooltip
                key={key}
                title={t(`device.chart.stats.${key}.tooltip`)}
                placement="top"
                arrow
              >
                <Box role="listitem" sx={{ cursor: 'help' }}>
                  <Typography variant="caption" color="text.secondary">
                    {t(`device.chart.stats.${key}`)}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 700 }}>
                    {yFmt(value)}
                    {unit ? ` ${unit}` : ''}
                  </Typography>
                </Box>
              </Tooltip>
            ))}
          </Stack>
        </>
      )}
    </Box>
  )
}
