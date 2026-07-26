import { useMemo } from 'react'
import { useAnalytics } from '../../context/analytics'
import { useTokens } from '../../hooks/useTokens'
import { defectPareto, spcSeries } from '../../api/fixtures'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { ControlChart } from '../charts/ControlChart'
import { ParetoChart } from '../charts/ParetoChart'
import { ChartContainer } from '../charts/ChartContainer'
import { KpiBand, PanelCard, SectionStack, TwoColumn, revealPanel } from './common'
import { formatNumber } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'

interface DefectRow {
  defect: string
  count: number
  cause: string
  cumulativePct: number
}

export function QualitySpc() {
  const { locale } = useAnalytics()
  const tokens = useTokens()
  const spc = useMemo(() => spcSeries(), [])
  const pareto = useMemo(() => defectPareto(), [])

  const outOfControl = spc.points.filter((point) => point.value > spc.ucl || point.value < spc.lcl).length

  const defectRows = useMemo<DefectRow[]>(() => {
    const ordered = [...pareto].sort((a, b) => b.count - a.count)
    const total = ordered.reduce((sum, item) => sum + item.count, 0) || 1
    let cumulative = 0
    return ordered.map((item) => {
      cumulative += item.count
      return { ...item, cumulativePct: Math.round((cumulative / total) * 1000) / 10 }
    })
  }, [pareto])

  const metrics: KpiCardModel[] = [
    { id: 'ooc', label: 'Out-of-control points', value: String(outOfControl), trend: outOfControl > 0 ? 'up' : 'flat', goodDirection: 'down', target: 'I-MR, 3σ limits', tooltip: 'Count of sample points that breach the ±3σ control limits on the I-MR chart for coiling temperature bias; each violation requires a root-cause investigation per the control plan.', onClick: () => revealPanel('spc-defects-table'), actionHint: 'the defect breakdown table' },
    { id: 'cpk', label: 'Process Cpk', value: '1.18', trend: 'up', goodDirection: 'up', target: 'target ≥ 1.33', tooltip: 'Process capability index (Cpk) for coiling temperature bias: measures how well the process distribution fits within the specification limits; Cpk ≥ 1.33 is the minimum acceptable standard for high-grade output.' },
    { id: 'top', label: 'Top defect share', value: formatNumber(defectRows[0]?.cumulativePct ?? 0, locale), unit: '%', target: 'Pareto 80/20', tooltip: 'Share of total 30-day defects attributed to the single highest-frequency defect type; a concentration above 50% indicates a single dominant root cause suitable for targeted corrective action.', onClick: () => revealPanel('spc-defects-table'), actionHint: 'the defect breakdown table' },
    { id: 'total', label: 'Defects (30d)', value: String(defectRows.reduce((sum, row) => sum + row.count, 0)), trend: 'down', goodDirection: 'down', target: 'synthetic', tooltip: 'Total defect events logged in the quality inspection system over the rolling 30-day window across all product types and production lines.', onClick: () => revealPanel('spc-defects-table'), actionHint: 'the defect table' },
  ]

  const columns: DataTableColumn<DefectRow>[] = [
    { key: 'defect', label: 'Defect', type: 'text' },
    { key: 'cause', label: 'Cause', type: 'enum' },
    { key: 'count', label: 'Count', type: 'number', align: 'right' },
    { key: 'cumulativePct', label: 'Cumulative %', type: 'number', align: 'right', render: (row) => `${row.cumulativePct}%` },
  ]

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />
      <TwoColumn
        main={
          <ChartContainer
            title="SPC control chart (coiling temperature bias)"
            summary={`Individuals chart with x̄ ${spc.mean}, UCL ${spc.ucl}, LCL ${spc.lcl}; ${outOfControl} point(s) breach the limits and are marked ⛔.`}
            height={280}
            tableColumns={[
              { key: 'label', label: 'Sample' },
              { key: 'value', label: 'Bias °C' },
            ]}
            tableRows={spc.points.map((point) => ({ label: point.label, value: point.value }))}
          >
            <ControlChart
              points={spc.points}
              mean={spc.mean}
              ucl={spc.ucl}
              lcl={spc.lcl}
              color={tokens.palette[0]}
              violationColor={tokens.status.critical}
              height={280}
              yFormat={(value) => formatNumber(value, locale)}
            />
          </ChartContainer>
        }
        side={
          <ChartContainer
            title="Defect Pareto"
            summary={`Defects ordered by frequency with a cumulative percentage line; ${defectRows[0]?.defect} dominates.`}
            height={280}
          >
            <ParetoChart items={pareto.map((item) => ({ label: item.defect, count: item.count }))} barColor={tokens.palette[1]} lineColor={tokens.status.critical} height={280} />
          </ChartContainer>
        }
      />
      <PanelCard id="spc-defects-table" title="Defects">
        <DataTable
          caption="Defect analytics linked to the Pareto"
          rows={defectRows}
          columns={columns}
          getRowId={(row) => row.defect}
          defaultSort={[{ key: 'count', direction: 'desc' }]}
          exportFileName="novasteel-defects"
        />
      </PanelCard>
    </SectionStack>
  )
}
