import { useMemo } from 'react'
import { Card, CardContent, Stack, Typography } from '@mui/material'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { usePolling } from '../../hooks/usePolling'
import { useTokens } from '../../hooks/useTokens'
import type { AlertRow } from '../../api/domain'
import { StateBoundary } from '../primitives/StateBoundary'
import { SeverityPill } from '../primitives/SeverityPill'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { LineChart } from '../charts/LineChart'
import { ChartContainer } from '../charts/ChartContainer'
import { KpiBand, PanelCard, SectionStack, TwoColumn } from './common'
import { formatDateTime, formatNumber } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'

const SEVERITY_RANK: Record<string, number> = { CRITICAL: 0, WARNING: 1, INFO: 2 }

export function Operations() {
  const { client, locale } = useAnalytics()
  const tokens = useTokens()
  const alertsState = useResource(() => client.getAlerts(), [client])
  usePolling(alertsState.reload, 10000)

  const throughput = useMemo(
    () =>
      Array.from({ length: 24 }, (_, hour) => ({
        x: hour,
        y: Math.round((122 + Math.sin(hour / 3) * 8 + (hour > 17 && hour < 20 ? -6 : 0)) * 10) / 10,
      })),
    [],
  )
  const target = useMemo(() => throughput.map((point) => ({ x: point.x, y: 130 })), [throughput])

  const metrics: KpiCardModel[] = [
    { id: 'throughput', label: 'Throughput', value: '128.4', unit: 't/h', trend: 'up', goodDirection: 'up', deltaLabel: '+3.2%', target: 'target 130 t/h', sparkline: throughput.map((point) => point.y) },
    { id: 'oee', label: 'OEE', value: '84.1', unit: '%', trend: 'up', goodDirection: 'up', deltaLabel: '+0.8 pts', target: 'target 85%' },
    { id: 'alerts', label: 'Active alerts', value: String(alertsState.data?.length ?? 0), deltaLabel: `${(alertsState.data ?? []).filter((a) => a.severity === 'CRITICAL').length} critical`, trend: 'flat', target: 'triage now', asOf: alertsState.asOf, source: alertsState.source },
    { id: 'energy', label: 'Energy intensity', value: '312', unit: '€/t', trend: 'down', goodDirection: 'down', deltaLabel: '−4.1%', target: 'target 300' },
    { id: 'ontime', label: 'On-time', value: '96.4', unit: '%', trend: 'up', goodDirection: 'up', deltaLabel: '+0.4 pts', target: 'target 97%' },
  ]

  const columns: DataTableColumn<AlertRow>[] = [
    { key: 'severity', label: 'Severity', type: 'enum', render: (row) => <SeverityPill severity={row.severity} />, value: (row) => SEVERITY_RANK[row.severity] ?? 3 },
    { key: 'createdAt', label: 'Time', type: 'date', render: (row) => formatDateTime(row.createdAt, locale) },
    { key: 'assetId', label: 'Unit', type: 'text' },
    { key: 'message', label: 'Type / message', type: 'text' },
    { key: 'status', label: 'Owner / status', type: 'enum' },
  ]

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />
      <TwoColumn
        main={
          <ChartContainer
            title="Throughput vs target"
            summary="Hourly throughput oscillates around 122–130 t/h with an evening dip during the price peak; target line at 130 t/h."
            tableColumns={[
              { key: 'hour', label: 'Hour' },
              { key: 'throughput', label: 't/h' },
            ]}
            tableRows={throughput.map((point) => ({ hour: `${point.x}:00`, throughput: point.y }))}
          >
            <LineChart
              series={[
                { id: 'throughput', label: 'Throughput', color: tokens.palette[0], points: throughput },
                { id: 'target', label: 'Target', color: tokens.palette[1], points: target, dashed: true },
              ]}
              height={280}
              xFormat={(value) => `${Math.round(value)}:00`}
              yFormat={(value) => formatNumber(value, locale)}
            />
          </ChartContainer>
        }
        side={
          <PanelCard title="Shift board">
            <Stack spacing={1.5}>
              {[
                { crew: 'Crew A (current)', shift: '06:00–14:00', lead: 'A. Weber', status: 'On shift' },
                { crew: 'Crew B (next)', shift: '14:00–22:00', lead: 'M. Dupont', status: 'Handover 13:45' },
                { crew: 'Crew C', shift: '22:00–06:00', lead: 'S. García', status: 'Rest' },
              ].map((entry) => (
                <Card key={entry.crew} variant="outlined">
                  <CardContent sx={{ py: 1.25 }}>
                    <Typography variant="body2" sx={{ fontWeight: 700 }}>
                      {entry.crew}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {entry.shift} · {entry.lead} · {entry.status}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Stack>
          </PanelCard>
        }
      />
      <PanelCard title="Alerts & incidents">
        <StateBoundary state={alertsState} isEmpty={(rows) => rows.length === 0}>
          {(rows) => (
            <DataTable
              caption="Operations alerts and incidents"
              rows={rows}
              columns={columns}
              getRowId={(row) => row.alertId}
              defaultSort={[{ key: 'severity', direction: 'asc' }, { key: 'createdAt', direction: 'desc' }]}
              exportFileName="novasteel-operations-alerts"
              onRefresh={alertsState.reload}
            />
          )}
        </StateBoundary>
      </PanelCard>
    </SectionStack>
  )
}
