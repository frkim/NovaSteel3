import { useMemo, useState } from 'react'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { useTokens } from '../../hooks/useTokens'
import type { QualityBatchRow } from '../../api/domain'
import { StateBoundary } from '../primitives/StateBoundary'
import { SeverityPill } from '../primitives/SeverityPill'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { LineChart } from '../charts/LineChart'
import { ChartContainer } from '../charts/ChartContainer'
import { KpiBand, PanelCard, SectionStack } from './common'
import { formatDateTime, formatNumber } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'
import { QualityBatchDrawer } from './QualityBatchDrawer'

const RESULT_RANK: Record<string, number> = { FAIL: 0, REVIEW: 1, PASS: 2 }

export function QualityBatches() {
  const { client, locale } = useAnalytics()
  const tokens = useTokens()
  const batchesState = useResource(() => client.getQualityBatches(), [client])
  const [selected, setSelected] = useState<QualityBatchRow | null>(null)

  const yieldTrend = useMemo(() => {
    const rows = [...(batchesState.data ?? [])].sort((a, b) => a.eventTs.localeCompare(b.eventTs))
    return rows.map((row, index) => ({ x: index, y: Math.round((100 - row.riskScore * 20) * 10) / 10 }))
  }, [batchesState.data])

  const metrics: KpiCardModel[] = [
    { id: 'yield', label: 'High-grade yield', value: '94.8', unit: '%', trend: 'up', goodDirection: 'up', deltaLabel: '+1.2 pts', target: 'target 95%', asOf: batchesState.asOf, source: batchesState.source, sparkline: yieldTrend.map((point) => point.y) },
    { id: 'firstpass', label: 'First-pass yield', value: '97.1', unit: '%', trend: 'up', goodDirection: 'up', deltaLabel: '+0.6 pts', target: 'target 97%' },
    { id: 'ncr', label: 'Open NCRs', value: String((batchesState.data ?? []).filter((row) => row.resultStatus !== 'PASS').length), trend: 'down', goodDirection: 'down', target: 'under review' },
    { id: 'defect', label: 'Defect rate', value: '182', unit: 'ppm', trend: 'down', goodDirection: 'down', deltaLabel: '−12%', target: 'target 170' },
  ]

  const columns: DataTableColumn<QualityBatchRow>[] = [
    { key: 'batchId', label: 'Batch', type: 'text' },
    { key: 'grade', label: 'Grade', type: 'enum' },
    { key: 'heatId', label: 'Heat', type: 'text' },
    { key: 'value', label: 'Value', type: 'number', align: 'right', render: (row) => `${formatNumber(row.value, locale)} ${row.unit}` },
    { key: 'coilingTempBiasC', label: 'Coiling bias °C', type: 'number', align: 'right' },
    { key: 'riskScore', label: 'Risk', type: 'number', align: 'right', render: (row) => `${Math.round(row.riskScore * 100)}%` },
    { key: 'resultStatus', label: 'Result', type: 'enum', render: (row) => <SeverityPill severity={row.resultStatus === 'FAIL' ? 'CRITICAL' : row.resultStatus === 'REVIEW' ? 'WARNING' : 'INFO'} label={row.resultStatus} />, value: (row) => RESULT_RANK[row.resultStatus] ?? 3 },
    { key: 'eventTs', label: 'Updated', type: 'date', render: (row) => formatDateTime(row.eventTs, locale) },
  ]

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />
      <ChartContainer
        title="Yield trend"
        summary="Predicted first-pass yield per batch derived from process risk; a downward excursion flags the drifting DP780 coil."
        height={240}
        tableColumns={[
          { key: 'index', label: 'Batch #' },
          { key: 'yield', label: 'Yield %' },
        ]}
        tableRows={yieldTrend.map((point) => ({ index: point.x + 1, yield: point.y }))}
      >
        <LineChart
          series={[{ id: 'yield', label: 'Yield', color: tokens.palette[2], points: yieldTrend }]}
          height={240}
          xFormat={(value) => `#${Math.round(value) + 1}`}
          yFormat={(value) => formatNumber(value, locale)}
        />
      </ChartContainer>
      <PanelCard title="Batches">
        <StateBoundary state={batchesState} isEmpty={(rows) => rows.length === 0}>
          {(rows) => (
            <DataTable
              caption="Quality batches — click a row for genealogy and what-if"
              rows={rows}
              columns={columns}
              getRowId={(row) => row.batchId}
              defaultSort={[{ key: 'eventTs', direction: 'desc' }]}
              exportFileName="novasteel-quality-batches"
              onRowClick={(row) => setSelected(row)}
              onRefresh={batchesState.reload}
            />
          )}
        </StateBoundary>
      </PanelCard>
      {selected && <QualityBatchDrawer batch={selected} onClose={() => setSelected(null)} />}
    </SectionStack>
  )
}
