import { useMemo } from 'react'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { useTokens } from '../../hooks/useTokens'
import type { EmissionRow, SustainabilitySummary } from '../../api/domain'
import { StateBoundary } from '../primitives/StateBoundary'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { LineChart } from '../charts/LineChart'
import { BarChart } from '../charts/BarChart'
import { ChartContainer } from '../charts/ChartContainer'
import { KpiBand, PanelCard, SectionStack, TwoColumn, revealPanel } from './common'
import { formatCurrency, formatDateTime, formatNumber, msOf } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'

export function SustainabilityEmissions() {
  const { client, emit, locale, site } = useAnalytics()
  const tokens = useTokens()
  const emissionsState = useResource(() => client.getEmissions(), [client])
  const summaryState = useResource(() => client.getSustainabilitySummary(), [client])

  const trend = useMemo(() => {
    const rows = [...(emissionsState.data ?? [])].sort((a, b) => msOf(a.eventTs) - msOf(b.eventTs))
    return rows.map((row) => ({ x: msOf(row.eventTs), y: Math.round(row.scope2KgCo2e / 100) / 10 }))
  }, [emissionsState.data])

  const target = useMemo(() => trend.map((point) => ({ x: point.x, y: 3.0 })), [trend])

  const metrics = useMemo<KpiCardModel[]>(() => {
    const summary = summaryState.data
    const totalScope2T = summary ? summary.scope2KgCo2e / 1000 : 0
    return [
      { id: 'co2', label: 'CO₂ (Scope 2)', value: formatNumber(totalScope2T, locale), unit: 't/day', trend: 'down', goodDirection: 'down', deltaLabel: '−2.8%', target: 'target −22%', asOf: summaryState.asOf, source: summaryState.source, tooltip: 'Total Scope 2 (purchased-electricity) CO₂-equivalent emissions for the day, derived from grid carbon intensity × energy consumption across all intervals. Target is −22% vs the prior-year baseline.', actionHint: 'the CO₂ trend chart', onClick: () => revealPanel('co2-trend-chart') },
      { id: 'intensity', label: 'CO₂ / t steel', value: '1.42', unit: 't/t', trend: 'down', goodDirection: 'down', deltaLabel: '−3%', target: 'target 1.35', tooltip: 'Carbon intensity of production: total Scope 2 CO₂-equivalent tonnes divided by finished steel tonnage. The target of 1.35 t/t tracks operational efficiency improvements across the fleet.', actionHint: 'the emissions ledger', onClick: () => revealPanel('emissions-ledger') },
      { id: 'allowance', label: 'ETS allowances left', value: '71', unit: '%', target: 'period cap', trend: 'flat', tooltip: 'Remaining EU ETS allowance budget as a percentage of the period cap, based on committed allocations vs granted allowances. Navigate to the ETS exposure tab for the full period projection.', actionHint: 'the ETS exposure tab', onClick: () => emit('nav.intent', { route: `/${site}/sustainability-compliance/ets-exposure` }) },
      { id: 'exposure', label: 'ETS € exposure', value: summary ? formatCurrency((summary.scope1KgCo2e + summary.scope2KgCo2e) / 1000 * summary.etsAllowancePriceEurTonne, locale, 'EUR', { notation: 'compact' }) : '—', trend: 'down', goodDirection: 'down', target: `€${summary?.etsAllowancePriceEurTonne ?? 86}/t`, asOf: summaryState.asOf, source: summaryState.source, tooltip: "Estimated monetary exposure if today's combined Scope 1 and Scope 2 CO₂ required spot-market ETS allowance purchases at the current market price per tonne.", actionHint: 'the ETS exposure tab', onClick: () => emit('nav.intent', { route: `/${site}/sustainability-compliance/ets-exposure` }) },
    ]
  }, [summaryState.data, summaryState.asOf, summaryState.source, locale, emit, site])

  const ledgerColumns: DataTableColumn<EmissionRow>[] = [
    { key: 'eventTs', label: 'Date', type: 'date', render: (row) => formatDateTime(row.eventTs, locale) },
    { key: 'site', label: 'Site', type: 'enum' },
    { key: 'scope2KgCo2e', label: 'Scope 2 kgCO₂e', type: 'number', align: 'right', render: (row) => formatNumber(row.scope2KgCo2e, locale) },
    { key: 'consumptionMwh', label: 'MWh', type: 'number', align: 'right', render: (row) => formatNumber(row.consumptionMwh, locale) },
    { key: 'carbonIntensityKgCo2eMwh', label: 'Intensity kg/MWh', type: 'number', align: 'right' },
  ]

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />
      <TwoColumn
        main={
          <div id="co2-trend-chart">
          <ChartContainer
            title="CO₂ trend vs target"
            summary="Scope 2 emissions per interval trend below the daily target line after optimized dispatch."
            height={260}
            tableColumns={[
              { key: 'time', label: 'Time' },
              { key: 'co2', label: 't CO₂' },
            ]}
            tableRows={trend.filter((_, index) => index % 6 === 0).map((point) => ({ time: formatDateTime(point.x, locale, { timeStyle: 'short' }), co2: point.y }))}
          >
            <LineChart
              series={[
                { id: 'co2', label: 'Scope 2', color: tokens.palette[0], points: trend },
                { id: 'target', label: 'Target', color: tokens.palette[3], points: target, dashed: true },
              ]}
              height={260}
              xFormat={(value) => formatDateTime(value, locale, { timeStyle: 'short' })}
              yFormat={(value) => formatNumber(value, locale)}
            />
          </ChartContainer>
          </div>
        }
        side={
          <StateBoundary state={summaryState} dockId="emissions-by-scope" dockTitle="Emissions by scope">
            {(summary: SustainabilitySummary) => (
              <ChartContainer
                title="Emissions by scope"
                summary={`Scope 1 (process) ${formatNumber(summary.scope1KgCo2e / 1000, locale)} t vs Scope 2 (electricity) ${formatNumber(summary.scope2KgCo2e / 1000, locale)} t.`}
                height={260}
              >
                <BarChart
                  groups={[
                    { label: 'Scope 1', values: { value: Math.round(summary.scope1KgCo2e / 1000) } },
                    { label: 'Scope 2', values: { value: Math.round(summary.scope2KgCo2e / 1000) } },
                  ]}
                  series={[{ id: 'value', label: 'tCO₂e', color: tokens.palette[1] }]}
                  height={260}
                  yFormat={(value) => formatNumber(value, locale)}
                />
              </ChartContainer>
            )}
          </StateBoundary>
        }
      />
      <PanelCard id="emissions-ledger" title="Emissions ledger (immutable)">
        <StateBoundary state={emissionsState} isEmpty={(rows) => rows.length === 0}>
          {(rows) => (
            <DataTable
              caption="Immutable emissions ledger — export honors current filters"
              rows={rows}
              columns={ledgerColumns}
              getRowId={(row) => row.sourceRef ?? row.eventTs}
              defaultSort={[{ key: 'eventTs', direction: 'desc' }]}
              exportFileName="novasteel-emissions-ledger"
              onRefresh={emissionsState.reload}
            />
          )}
        </StateBoundary>
      </PanelCard>
    </SectionStack>
  )
}
