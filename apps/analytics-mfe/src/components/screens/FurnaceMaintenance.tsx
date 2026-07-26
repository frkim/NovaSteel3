import { useMemo } from 'react'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { useTokens } from '../../hooks/useTokens'
import type { WorkOrderRow } from '../../api/domain'
import { StateBoundary } from '../primitives/StateBoundary'
import { SeverityPill } from '../primitives/SeverityPill'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { GanttChart, type GanttTask } from '../charts/GanttChart'
import { ChartContainer } from '../charts/ChartContainer'
import { KpiBand, PanelCard, SectionStack } from './common'
import { formatDateTime } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'

const DAY_MS = 86400000

export function FurnaceMaintenance() {
  const { client, locale } = useAnalytics()
  const tokens = useTokens()
  const workOrdersState = useResource(() => client.getWorkOrders(), [client])

  const tasks = useMemo<GanttTask[]>(() => {
    const base = Date.parse('2026-07-25T00:00:00Z')
    return [
      { id: 'WO-1042', label: 'BF-01 hearth inspection', start: base + 1 * DAY_MS, end: base + 4 * DAY_MS, color: tokens.status.critical, urgent: true },
      { id: 'WO-1043', label: 'RHF-01 zone 03 watch', start: base + 2 * DAY_MS, end: base + 3 * DAY_MS, color: tokens.status.warning },
      { id: 'WO-1044', label: 'Cooling circuit ultrasound', start: base + 5 * DAY_MS, end: base + 8 * DAY_MS, color: tokens.palette[0] },
      { id: 'WO-1045', label: 'Refractory relining window', start: base + 18 * DAY_MS, end: base + 24 * DAY_MS, color: tokens.palette[2] },
    ]
  }, [tokens])

  const metrics: KpiCardModel[] = [
    { id: 'open', label: 'Open work orders', value: String((workOrdersState.data ?? []).filter((row) => row.status !== 'COMPLETED').length), target: 'planned + in progress', asOf: workOrdersState.asOf, source: workOrdersState.source },
    { id: 'urgent', label: 'Urgent', value: '1', trend: 'up', goodDirection: 'down', deltaLabel: 'BF-01', target: 'hearth inspection' },
    { id: 'window', label: 'Relining window', value: '18–24', unit: 'd', target: 'aligned to RUL P50' },
    { id: 'completed', label: 'Completed (30d)', value: '7', trend: 'up', goodDirection: 'up', target: 'synthetic history' },
  ]

  const columns: DataTableColumn<WorkOrderRow>[] = [
    { key: 'workOrderId', label: 'Work order', type: 'text' },
    { key: 'assetId', label: 'Unit', type: 'text' },
    { key: 'title', label: 'Title', type: 'text' },
    { key: 'reason', label: 'Reason', type: 'text' },
    { key: 'status', label: 'Status', type: 'enum', render: (row) => <SeverityPill severity={row.status === 'COMPLETED' ? 'INFO' : 'WARNING'} label={row.status} /> },
    { key: 'detectedAt', label: 'Detected', type: 'date', render: (row) => formatDateTime(row.detectedAt, locale) },
  ]

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />
      <ChartContainer
        title="Maintenance schedule"
        summary="Work orders across the next 24 days; the BF-01 hearth inspection is urgent (dashed outline) and the relining window aligns with the 21-day RUL forecast."
        height={240}
      >
        <GanttChart tasks={tasks} height={240} xFormat={(value) => formatDateTime(value, locale, { month: 'short', day: 'numeric' })} />
      </ChartContainer>
      <PanelCard title="Work orders">
        <StateBoundary state={workOrdersState} isEmpty={(rows) => rows.length === 0}>
          {(rows) => (
            <DataTable
              caption="Furnace maintenance work orders"
              rows={rows}
              columns={columns}
              getRowId={(row) => row.workOrderId}
              defaultSort={[{ key: 'detectedAt', direction: 'desc' }]}
              exportFileName="novasteel-work-orders"
              onRefresh={workOrdersState.reload}
            />
          )}
        </StateBoundary>
      </PanelCard>
    </SectionStack>
  )
}
