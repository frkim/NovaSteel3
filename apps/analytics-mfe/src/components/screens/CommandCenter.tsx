import { useMemo } from 'react'
import { Box, Button, Card, CardActionArea, CardContent, Stack, Typography } from '@mui/material'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { usePolling } from '../../hooks/usePolling'
import { useTokens } from '../../hooks/useTokens'
import type { AlertRow } from '../../api/domain'
import { StateBoundary } from '../primitives/StateBoundary'
import { SeverityPill } from '../primitives/SeverityPill'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { DonutChart } from '../charts/DonutChart'
import { ChartContainer } from '../charts/ChartContainer'
import { KpiBand, PanelCard, SectionStack, TwoColumn, revealPanel } from './common'
import { formatDateTime, formatInteger, formatNumber } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'

const SEVERITY_RANK: Record<string, number> = { CRITICAL: 0, WARNING: 1, INFO: 2 }

export function CommandCenter() {
  const { client, emit, locale, site } = useAnalytics()
  const tokens = useTokens()

  const summaryState = useResource(() => client.getCommandSummary('all'), [client])
  const alertsState = useResource(() => client.getAlerts(), [client])
  usePolling(alertsState.reload, 8000)

  const alerts = useMemo(() => alertsState.data ?? [], [alertsState.data])
  const openCritical = useMemo(
    () => alerts.filter((alert) => alert.severity === 'CRITICAL' && alert.status !== 'CLOSED'),
    [alerts],
  )

  const metrics = useMemo<KpiCardModel[]>(() => {
    const kpis = summaryState.data?.kpis
    const asOf = summaryState.asOf
    const source = summaryState.source
    return [
      {
        id: 'energy',
        label: 'Energy consumption',
        value: formatNumber(kpis?.energyConsumptionMwh, locale),
        unit: 'MWh',
        trend: 'down',
        goodDirection: 'down',
        deltaLabel: `−${formatNumber(kpis?.energyDispatchSavingsTargetPct, locale)}% target`,
        target: 'target −14% energy/t',
        asOf,
        source,
        tooltip: 'Total electrical energy consumed at this site in the current rolling window, in MWh. Sourced from meter aggregations and compared against the dispatch-savings target from energy optimisation.',
        actionHint: 'the spot-price schedule',
        onClick: () => emit('nav.intent', { route: `/${site}/energy-optimization/spot-price-schedule` }),
      },
      {
        id: 'co2',
        label: 'CO₂ (Scope 2)',
        value: formatNumber((kpis?.scope2KgCo2e ?? 0) / 1000, locale),
        unit: 't/day',
        trend: 'down',
        goodDirection: 'down',
        deltaLabel: '−22% target',
        target: 'target −22% CO₂',
        asOf,
        source,
        tooltip: 'Scope 2 market-based CO₂-equivalent emissions for today in tonnes per day, covering grid electricity consumed on site. Derived from the energy meter feed and the regional grid emission factor.',
        actionHint: 'the emissions ledger',
        onClick: () => emit('nav.intent', { route: `/${site}/sustainability-compliance/emissions-ledger` }),
      },
      {
        id: 'furnace',
        label: 'Furnace lining RUL',
        value: formatNumber(kpis?.liningRulDaysP50, locale),
        unit: 'days (P50)',
        trend: 'down',
        goodDirection: 'up',
        deltaLabel: 'HEARTH-07',
        target: 'target ≥21-day advance warning',
        asOf,
        source,
        tooltip: 'Median remaining useful life of the BF-07 hearth lining in days, from model lining-rul-piml:1.3.0-demo scored on real-time thermocouple and heat-flux sensor data. Lower values indicate increasing reline urgency.',
        actionHint: 'the lining forecast',
        why: {
          modelVersion: 'lining-rul-piml/1.3.0-demo',
          scoredAt: asOf,
          drivers: [
            { name: 'heat_flux_6h_slope', contribution: 0.29 },
            { name: 'sector_to_ring_temp_delta', contribution: 0.24 },
            { name: 'cooling_efficiency_residual', contribution: 0.18 },
          ],
          confidenceText: 'P50 19.65 days · P10 18.69 · P90 20.61 (risk 0.90).',
        },
        onClick: () => emit('nav.intent', { route: `/${site}/furnace-health/lining-forecast` }),
      },
      {
        id: 'yield',
        label: 'High-grade yield (pred.)',
        value: formatNumber(kpis?.qualityPredictedFirstPassYieldPct, locale),
        unit: '%',
        trend: 'up',
        goodDirection: 'up',
        deltaLabel: '+8% target',
        target: 'target +8% yield',
        asOf,
        source,
        tooltip: 'Predicted first-pass high-grade yield percentage for the current shift, output by the quality prediction model and aggregated over all coils scored in the last 8 hours.',
        actionHint: 'quality batches',
        onClick: () => emit('nav.intent', { route: `/${site}/quality/batches` }),
      },
      {
        id: 'alerts',
        label: 'Open alerts',
        value: formatInteger(kpis?.openAlerts ?? alerts.length, locale),
        unit: '',
        deltaLabel: `${openCritical.length} critical`,
        trend: openCritical.length > 0 ? 'up' : 'flat',
        goodDirection: 'down',
        status: openCritical.length > 0 ? 'critical' : 'ok',
        target: 'triage in Command Center',
        asOf: alertsState.asOf,
        source: alertsState.source,
        tooltip: 'Count of currently open (non-closed) alerts across all severities for this site. Polled every 8 seconds from the alerting service; the critical count is shown separately.',
        actionHint: 'the active alerts table',
        onClick: () => revealPanel('cc-alerts'),
      },
    ]
  }, [summaryState.data, summaryState.asOf, summaryState.source, alertsState.asOf, alertsState.source, alerts.length, openCritical.length, locale, emit, site])

  const severityMix = useMemo(() => {
    const counts: Record<string, number> = { CRITICAL: 0, WARNING: 0, INFO: 0 }
    for (const alert of alerts) {
      counts[alert.severity] = (counts[alert.severity] ?? 0) + 1
    }
    return [
      { label: 'Critical', value: counts.CRITICAL, color: tokens.status.critical },
      { label: 'Warning', value: counts.WARNING, color: tokens.status.warning },
      { label: 'Info', value: counts.INFO, color: tokens.status.info },
    ]
  }, [alerts, tokens])

  const actions = useMemo(
    () => [
      {
        id: 'load-shift',
        title: 'Approve simulated load-shift 17:00–20:00',
        detail: 'Modeled saving ≈ €4.2k · shifts flexible reheat away from the 280 €/MWh peak.',
        route: `/${site}/energy-optimization/load-shift-simulator`,
      },
      {
        id: 'inspect',
        title: 'Schedule BF2 hearth inspection (risk 0.90)',
        detail: 'Predicted RUL P50 19.65 days · create synthetic work order and verify sensors.',
        route: `/${site}/furnace-health/lining-forecast`,
      },
      {
        id: 'quality',
        title: 'Review NS-AUTO-DP780 drift on COIL-017',
        detail: 'Coiling temperature drift detected before first off-spec lab result.',
        route: `/${site}/quality/batches`,
      },
    ],
    [site],
  )

  const alertColumns: DataTableColumn<AlertRow>[] = [
    {
      key: 'severity',
      label: 'Severity',
      type: 'enum',
      width: 120,
      render: (row) => <SeverityPill severity={row.severity} />,
      value: (row) => SEVERITY_RANK[row.severity] ?? 3,
    },
    { key: 'createdAt', label: 'Time', type: 'date', render: (row) => formatDateTime(row.createdAt, locale) },
    { key: 'assetId', label: 'Site/Unit', type: 'text' },
    { key: 'componentId', label: 'Component', type: 'text' },
    { key: 'message', label: 'Message', type: 'text' },
    {
      key: 'confidence',
      label: 'Conf.',
      type: 'number',
      align: 'right',
      render: (row) => (row.confidence ? `${Math.round(row.confidence * 100)}%` : '—'),
    },
    { key: 'status', label: 'Status', type: 'enum' },
  ]

  const sites = useMemo(() => [
    { code: 'lu', label: 'LU', name: 'Moselle Integrated Works', health: 'WARNING' as const, alerts: openCritical.length },
    { code: 'de', label: 'DE', name: 'Saarbrücken Steelworks', health: 'INFO' as const, alerts: 0 },
    { code: 'be', label: 'BE', name: 'Liège Rolling Mill', health: 'INFO' as const, alerts: 0 },
    { code: 'es', label: 'ES', name: 'Asturias Long Products', health: 'INFO' as const, alerts: 0 },
  ], [openCritical.length])

  return (
    <SectionStack>
      <PanelCard title="Site status">
        <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))' }}>
          {sites.map((entry) => (
            <Card key={entry.code} variant="outlined">
              <CardActionArea
                aria-label={`${entry.label} — ${entry.name}`}
                onClick={() => emit('nav.intent', { route: `/${entry.code}/command-center/overview` })}
              >
                <CardContent>
                  <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="h5">{entry.label}</Typography>
                    <SeverityPill severity={entry.health} label={entry.health === 'WARNING' ? 'Attention' : 'Healthy'} />
                  </Stack>
                  <Typography variant="caption" color="text.secondary">
                    {entry.name}
                  </Typography>
                  {entry.alerts > 0 && (
                    <Typography variant="caption" color="error">
                      {entry.alerts} active alert{entry.alerts !== 1 ? 's' : ''}
                    </Typography>
                  )}
                </CardContent>
              </CardActionArea>
            </Card>
          ))}
        </Box>
      </PanelCard>

      <StateBoundary state={summaryState} skeletonRows={2} dockId="cc-kpis" dockTitle="Key metrics">
        {() => <KpiBand metrics={metrics} />}
      </StateBoundary>

      <TwoColumn
        main={
          <PanelCard id="cc-alerts" title="Active alerts">
            <Box role="log" aria-live="polite" aria-relevant="additions">
              <span className="ns-visually-hidden" role="status">
                {openCritical.length} critical alerts open
              </span>
              <StateBoundary
                state={alertsState}
                isEmpty={(rows) => rows.length === 0}
                emptyMessage="No active alerts."
              >
                {(rows) => (
                  <DataTable
                    caption="Active alerts and incidents"
                    rows={rows}
                    columns={alertColumns}
                    getRowId={(row) => row.alertId}
                    defaultSort={[
                      { key: 'severity', direction: 'asc' },
                      { key: 'createdAt', direction: 'desc' },
                    ]}
                    exportFileName="novasteel-alerts"
                    onRefresh={alertsState.reload}
                    onRowClick={(row) => emit('telemetry', { event: 'alert.open', alertId: row.alertId })}
                  />
                )}
              </StateBoundary>
            </Box>
          </PanelCard>
        }
        side={
          <Stack spacing={2}>
            <PanelCard title="Next-best actions">
              <Stack spacing={1.5}>
                {actions.map((action, index) => (
                  <Card key={action.id} variant="outlined">
                    <CardContent sx={{ py: 1.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 700 }}>
                        {index + 1}. {action.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                        {action.detail}
                      </Typography>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => emit('nav.intent', { route: action.route })}
                      >
                        Open
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            </PanelCard>
            <ChartContainer
              title="Alert severity mix"
              summary={`${severityMix.map((slice) => `${slice.label} ${slice.value}`).join(', ')}.`}
              height={180}
            >
              <DonutChart
                slices={severityMix}
                centerValue={String(alerts.length)}
                centerLabel="alerts"
                height={180}
              />
            </ChartContainer>
          </Stack>
        }
      />
    </SectionStack>
  )
}
