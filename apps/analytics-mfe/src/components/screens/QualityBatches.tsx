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
import { KpiBand, PanelCard, SectionStack, revealPanel } from './common'
import { formatDateTime, formatNumber } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'
import { ProofBadges } from '../primitives/ProofBadge'
import { QualityBatchDrawer } from './QualityBatchDrawer'

const RESULT_RANK: Record<string, number> = { FAIL: 0, REVIEW: 1, PASS: 2 }

export function QualityBatches() {
  const { client, emit, locale, site } = useAnalytics()
  const tokens = useTokens()
  const batchesState = useResource(() => client.getQualityBatches(), [client])
  const [selected, setSelected] = useState<QualityBatchRow | null>(null)

  const yieldTrend = useMemo(() => {
    const rows = [...(batchesState.data ?? [])].sort((a, b) => a.eventTs.localeCompare(b.eventTs))
    return rows.map((row, index) => ({ x: index, y: Math.round((100 - row.riskScore * 20) * 10) / 10 }))
  }, [batchesState.data])

  const openNcrCount = (batchesState.data ?? []).filter((row) => row.resultStatus !== 'PASS').length
  const metrics: KpiCardModel[] = [
    { id: 'yield', label: 'High-grade yield', value: '94.8', unit: '%', trend: 'up', goodDirection: 'up', deltaLabel: '+1.2 pts', target: 'target 95%', asOf: batchesState.asOf, source: batchesState.source, sparkline: yieldTrend.map((point) => point.y), tooltip: 'Rolling percentage of production classified as high-grade, derived by inverting the per-batch process risk score; target is 95% per the annual quality agreement.', onClick: () => revealPanel('quality-batches-table'), actionHint: 'the batch table' },
    { id: 'firstpass', label: 'First-pass yield', value: '97.1', unit: '%', trend: 'up', goodDirection: 'up', deltaLabel: '+0.6 pts', target: 'target 97%', tooltip: 'Percentage of batches that pass the quality inspection on the first attempt without rework, calculated from LIMS records over the rolling production cycle.', onClick: () => revealPanel('quality-batches-table'), actionHint: 'the batch table' },
    { id: 'ncr', label: 'Open NCRs', value: String(openNcrCount), trend: 'down', goodDirection: 'down', status: openNcrCount > 0 ? 'warning' : 'ok', target: 'under review', tooltip: 'Count of open non-conformance records: batches with status REVIEW or FAIL that require corrective action before shipment release.', onClick: () => revealPanel('quality-batches-table'), actionHint: 'the batch table' },
    { id: 'defect', label: 'Defect rate', value: '182', unit: 'ppm', trend: 'down', goodDirection: 'down', deltaLabel: '−12%', target: 'target 170', tooltip: 'Rolling 30-day defect rate in parts per million across all inspected batches and grades; target is 170 ppm per the customer quality plan.', onClick: () => emit('nav.intent', { route: `/${site}/quality/spc` }), actionHint: 'the SPC control chart' },
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
      <PanelCard
        id="quality-batches-table"
        title="Batches"
        action={<ProofBadges ids={['CHL-04', 'OBJ-03', 'OUT-04']} />}
      >
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
