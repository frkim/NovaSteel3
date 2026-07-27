import { useMemo } from 'react'
import { Button, Card, CardContent, Stack, Typography } from '@mui/material'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { useTokens } from '../../hooks/useTokens'
import type { FurnaceRow, LiningForecast } from '../../api/domain'
import { StateBoundary } from '../primitives/StateBoundary'
import { SeverityPill } from '../primitives/SeverityPill'
import { ConfidenceMeter } from '../primitives/ConfidenceMeter'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { LineChart } from '../charts/LineChart'
import { ChartContainer } from '../charts/ChartContainer'
import { KpiBand, PanelCard, SectionStack, TwoColumn, revealPanel } from './common'
import { formatDateTime, formatNumber } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'

const FURNACE_ASSET = 'LUX-BF-01'
const RISK_THRESHOLD = 0.8

function logistic(day: number, center: number, spread: number): number {
  return 1 / (1 + Math.exp(-(day - center) / spread))
}

/** Build a 21-day-horizon risk projection with a P10–P90 uncertainty band. */
function riskProjection(forecast: LiningForecast) {
  const { p10, p50, p90 } = forecast.confidence
  const spread = Math.max(1.5, (p90 - p10) / 5)
  const days = Array.from({ length: 31 }, (_, day) => day)
  const median = days.map((day) => ({ x: day, y: Number(logistic(day, p50, spread).toFixed(3)) }))
  const band = days.map((day) => ({
    x: day,
    // Earlier failure (p10) => higher risk sooner (upper bound); later (p90) => lower bound.
    high: Number(logistic(day, p10, spread).toFixed(3)),
    low: Number(logistic(day, p90, spread).toFixed(3)),
  }))
  return { median, band }
}

interface UnitRow {
  assetId: string
  risk: number
  daysLeft: number
  confidence: number
  lastInspection: string
  openWorkOrders: number
  health: string
}

export function FurnaceLiningForecast() {
  const { client, emit, locale, site, can } = useAnalytics()
  const tokens = useTokens()

  const forecastState = useResource(() => client.getLiningForecast(FURNACE_ASSET), [client])
  const furnacesState = useResource(() => client.getFurnaces(), [client])

  const predictedFailure = useMemo(() => {
    if (!forecastState.data) {
      return null
    }
    const scored = forecastState.data.scoredAt ? new Date(forecastState.data.scoredAt) : new Date()
    return new Date(scored.getTime() + forecastState.data.value * 86400000)
  }, [forecastState.data])

  const metrics = useMemo<KpiCardModel[]>(() => {
    const forecast = forecastState.data
    const why = forecast
      ? {
          modelVersion: forecast.modelVersion,
          scoredAt: forecast.scoredAt,
          drivers: forecast.drivers,
          confidenceText: `P50 ${forecast.confidence.p50} d · P10 ${forecast.confidence.p10} · P90 ${forecast.confidence.p90}.`,
        }
      : undefined
    return [
      { id: 'risk', label: 'Lining risk', value: forecast ? formatNumber(forecast.riskScore * 100, locale) : '—', unit: '%', trend: 'up', goodDirection: 'down', status: forecast ? (forecast.riskScore >= RISK_THRESHOLD ? 'critical' : forecast.riskScore >= RISK_THRESHOLD * 0.75 ? 'warning' : 'ok') : 'neutral', deltaLabel: forecast?.riskLevel, target: `threshold ${RISK_THRESHOLD * 100}%`, asOf: forecastState.asOf, source: forecastState.source, why, tooltip: 'Physics-informed regression risk score (0–100%) for BF-01\'s hearth lining, output by the lining-rul-piml model; values above 80% trigger an immediate inspection recommendation.', onClick: () => revealPanel('lining-drivers'), actionHint: 'the risk drivers and confidence panel' },
      { id: 'days', label: 'Days to threshold', value: forecast ? formatNumber(forecast.value, locale) : '—', unit: 'd', target: 'inspect HEARTH-07', asOf: forecastState.asOf, source: forecastState.source, why, tooltip: 'P50 remaining-useful-life estimate from the lining-rul-piml model: the days until the hearth lining is projected to wear down to its minimum safe thickness, obtained by extrapolating the fitted wear-rate slope. P50 is the central estimate of a normal band derived from the regression standard error, not a Monte Carlo simulation.', onClick: () => revealPanel('lining-drivers'), actionHint: 'the confidence meter and model drivers' },
      { id: 'confidence', label: 'Model confidence', value: forecast ? `P10–P90 ${forecast.confidence.p10}–${forecast.confidence.p90}` : '—', unit: 'd', target: 'uncertainty band', asOf: forecastState.asOf, source: forecastState.source, why, tooltip: 'P10–P90 uncertainty band in days, derived from the standard error of the fitted wear-rate regression; a narrower band means the thickness measurements fit the wear trend more tightly. Reported separately from the model confidence score, which grades the input data quality.', onClick: () => revealPanel('lining-drivers'), actionHint: 'the confidence meter' },
      { id: 'failDate', label: 'Predicted failure date', value: predictedFailure ? formatDateTime(predictedFailure, locale, { dateStyle: 'medium' }) : '—', target: 'P50 estimate', asOf: forecastState.asOf, source: forecastState.source, why, tooltip: 'Projected calendar date of lining failure, computed by adding the P50 RUL days to the model scoring timestamp; treat as a planning target, not a hard deadline.', onClick: () => revealPanel('lining-units'), actionHint: 'the furnace units forecast table' },
    ]
  }, [forecastState.data, forecastState.asOf, forecastState.source, predictedFailure, locale])

  const unitRows = useMemo<UnitRow[]>(() => {
    const list = furnacesState.data ?? []
    return list.map((furnace: FurnaceRow) => {
      const isPrimary = furnace.assetId === FURNACE_ASSET
      const forecast = forecastState.data
      return {
        assetId: furnace.assetId,
        risk: isPrimary && forecast ? Math.round(forecast.riskScore * 100) : furnace.health === 'WATCH' ? 34 : 12,
        daysLeft: isPrimary && forecast ? forecast.value : 120,
        confidence: isPrimary && forecast ? Math.round((1 - (forecast.confidence.p90 - forecast.confidence.p10) / forecast.confidence.p50 / 2) * 100) : 82,
        lastInspection: isPrimary ? '2026-06-02' : '2026-07-01',
        openWorkOrders: isPrimary ? 1 : 0,
        health: furnace.health,
      }
    })
  }, [furnacesState.data, forecastState.data])

  const unitColumns: DataTableColumn<UnitRow>[] = [
    { key: 'assetId', label: 'Unit', type: 'text' },
    { key: 'risk', label: 'Risk %', type: 'number', align: 'right', render: (row) => `${row.risk}%` },
    { key: 'daysLeft', label: 'Days left', type: 'number', align: 'right' },
    { key: 'confidence', label: 'Confidence', type: 'number', align: 'right', render: (row) => `${row.confidence}%` },
    { key: 'lastInspection', label: 'Last inspection', type: 'date' },
    { key: 'openWorkOrders', label: 'Open WOs', type: 'number', align: 'right' },
    { key: 'health', label: 'Health', type: 'enum', render: (row) => <SeverityPill severity={row.health === 'HIGH_RISK' ? 'CRITICAL' : row.health === 'WATCH' ? 'WARNING' : 'INFO'} label={row.health} /> },
  ]

  return (
    <SectionStack>
      <StateBoundary state={forecastState} skeletonRows={2} dockId="lining-kpis" dockTitle="Key metrics">
        {() => <KpiBand metrics={metrics} />}
      </StateBoundary>

      <TwoColumn
        main={
          <StateBoundary state={forecastState} dockId="lining-risk-chart" dockTitle="Lining risk forecast">
            {(forecast) => {
              const projection = riskProjection(forecast)
              return (
                <ChartContainer
                  title="Lining risk over 21-day horizon"
                  summary={`Risk crosses the ${RISK_THRESHOLD * 100}% threshold around day ${forecast.confidence.p50}; the shaded band spans the P10 (${forecast.confidence.p10}d) to P90 (${forecast.confidence.p90}d) uncertainty.`}
                  height={300}
                  tableColumns={[
                    { key: 'day', label: 'Day' },
                    { key: 'risk', label: 'Median risk' },
                  ]}
                  tableRows={projection.median.filter((_, index) => index % 3 === 0).map((point) => ({ day: point.x, risk: point.y }))}
                >
                  <LineChart
                    series={[{ id: 'risk', label: 'Median risk', color: tokens.palette[0], points: projection.median }]}
                    band={{ points: projection.band, color: tokens.palette[0], label: 'P10–P90' }}
                    threshold={{ value: RISK_THRESHOLD, label: `Threshold ${RISK_THRESHOLD}`, color: tokens.status.critical }}
                    height={300}
                    xFormat={(value) => `d${Math.round(value)}`}
                    yFormat={(value) => value.toFixed(1)}
                  />
                </ChartContainer>
              )
            }}
          </StateBoundary>
        }
        side={
          <StateBoundary state={forecastState} dockId="lining-drivers" dockTitle="Why? · drivers · freshness">
            {(forecast) => (
              <PanelCard id="lining-drivers" title="Why? · drivers · freshness">
                <Stack spacing={2}>
                  <SeverityPill severity="HIGH" label={`Risk ${(forecast.riskScore * 100).toFixed(0)}% · ${forecast.riskLevel}`} />
                  <ConfidenceMeter band={forecast.confidence} unit="days" label="Remaining useful life (P10–P90)" />
                  <Stack spacing={0.75}>
                    <Typography variant="caption" sx={{ fontWeight: 700 }}>
                      Top drivers ({forecast.modelVersion})
                    </Typography>
                    {forecast.drivers.map((driver) => (
                      <Stack key={driver.name} direction="row" sx={{ justifyContent: 'space-between' }}>
                        <Typography variant="caption">{driver.name}</Typography>
                        <Typography variant="caption" sx={{ fontWeight: 700 }}>
                          {(driver.contribution * 100).toFixed(0)}%
                        </Typography>
                      </Stack>
                    ))}
                  </Stack>
                  <Card variant="outlined">
                    <CardContent sx={{ py: 1.25 }}>
                      <Typography variant="caption" color="text.secondary">
                        Feature snapshot
                      </Typography>
                      <Typography variant="body2">
                        Lining {forecast.featureSnapshot.liningThicknessMm} mm · ΔT {forecast.featureSnapshot.coolingDeltaC} °C · flux{' '}
                        {forecast.featureSnapshot.heatFluxKwM2} kW/m²
                      </Typography>
                    </CardContent>
                  </Card>
                  <Button
                    variant="contained"
                    disabled={!can('workorder.createSynthetic')}
                    onClick={() => emit('nav.intent', { route: `/${site}/furnace-health/maintenance-planner` })}
                  >
                    Plan inspection work order
                  </Button>
                </Stack>
              </PanelCard>
            )}
          </StateBoundary>
        }
      />

      <PanelCard id="lining-units" title="Furnace units">
        <StateBoundary state={furnacesState} isEmpty={(rows) => rows.length === 0}>
          {() => (
            <DataTable
              caption="Furnace units with lining risk"
              rows={unitRows}
              columns={unitColumns}
              getRowId={(row) => row.assetId}
              defaultSort={[{ key: 'risk', direction: 'desc' }]}
              exportFileName="novasteel-furnace-units"
              onRefresh={furnacesState.reload}
            />
          )}
        </StateBoundary>
      </PanelCard>
    </SectionStack>
  )
}
