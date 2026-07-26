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
import { KpiBand, PanelCard, SectionStack, revealPanel } from './common'
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
    { id: 'open', label: 'Open work orders', value: String((workOrdersState.data ?? []).filter((row) => row.status !== 'COMPLETED').length), target: 'planned + in progress', asOf: workOrdersState.asOf, source: workOrdersState.source, tooltip: 'Total count of work orders with status PLANNED or IN_PROGRESS for all furnace assets, sourced from the CMMS integration.', onClick: () => revealPanel('maintenance-work-orders'), actionHint: 'the work order table' },
    { id: 'urgent', label: 'Urgent', value: '1', trend: 'up', goodDirection: 'down', deltaLabel: 'BF-01', target: 'hearth inspection', tooltip: 'Work orders flagged as urgent due to immediate safety or availability risk; BF-01 hearth inspection (WO-1042) is currently overdue relative to the lining RUL model output.', onClick: () => revealPanel('maintenance-work-orders'), actionHint: 'the work order table' },
    { id: 'window', label: 'Relining window', value: '18–24', unit: 'd', target: 'aligned to RUL P50', tooltip: 'Planned refractory relining maintenance window in days from today, timed to align with the P50 RUL forecast so the furnace goes offline before the 80% risk threshold is breached.', onClick: () => revealPanel('maintenance-work-orders'), actionHint: 'the maintenance schedule work orders' },
    { id: 'completed', label: 'Completed (30d)', value: '7', trend: 'up', goodDirection: 'up', target: 'synthetic history', tooltip: 'Work orders closed with status COMPLETED in the rolling 30-day window, drawn from synthetic CMMS history for demo purposes.' },
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
      <PanelCard id="maintenance-work-orders" title="Work orders">
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
