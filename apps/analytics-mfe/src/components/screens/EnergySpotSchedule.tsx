import { useMemo } from 'react'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { useTokens } from '../../hooks/useTokens'
import type { EnergyIntervalRow, EnergyRecommendation, EnergyScheduleRow } from '../../api/domain'
import { StateBoundary } from '../primitives/StateBoundary'
import { SeverityPill } from '../primitives/SeverityPill'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { PriceLoadChart, type PriceLoadPoint } from '../charts/PriceLoadChart'
import { ChartContainer } from '../charts/ChartContainer'
import { KpiBand, PanelCard, SectionStack, revealPanel } from './common'
import { formatCurrency, formatNumber, formatTime, msOf } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'
import { ProofBadges } from '../primitives/ProofBadge'

export function EnergySpotSchedule() {
  const { client, emit, locale, site } = useAnalytics()
  const tokens = useTokens()
  const intervalsState = useResource(() => client.getEnergyIntervals(), [client])
  // 120 minutes: the documented demo window behind the 7.25% headline.
  const recommendationState = useResource(() => client.simulateEnergy({ maxShiftMinutes: 120, maxConcurrentBatches: 2 }), [client])

  const overlay = useMemo<PriceLoadPoint[]>(() => {
    const rows = intervalsState.data ?? []
    return [...rows]
      .sort((a: EnergyIntervalRow, b: EnergyIntervalRow) => msOf(a.intervalStart) - msOf(b.intervalStart))
      .map((row) => ({
        t: msOf(row.intervalStart),
        price: row.priceEurMwh,
        baseline: row.baselineDemandMw,
        optimized: row.demandMw,
      }))
  }, [intervalsState.data])

  const peakPrice = overlay.reduce((max, point) => Math.max(max, point.price), 0)
  const avgCarbon = useMemo(() => {
    const rows = intervalsState.data ?? []
    return rows.length
      ? Math.round(rows.reduce((sum, row) => sum + row.carbonIntensityKgCo2eMwh, 0) / rows.length)
      : 244
  }, [intervalsState.data])

  const metrics = useMemo<KpiCardModel[]>(() => {
    const rec = recommendationState.data
    return [
      { id: 'price', label: 'Peak price today', value: formatNumber(peakPrice, locale), unit: '€/MWh', trend: 'up', goodDirection: 'down', deltaLabel: 'evening scarcity', target: 'peak ~18:30', asOf: intervalsState.asOf, source: intervalsState.source, sparkline: overlay.map((point) => point.price), tooltip: "Highest day-ahead spot price observed in today's intervals, sourced from the energy market feed. The optimiser shifts flexible loads away from this peak window to lower cost.", actionHint: 'the spot price & load chart', onClick: () => revealPanel('spot-price-chart') },
      { id: 'savings', label: 'Projected savings', value: rec ? formatNumber(rec.savings.costPct, locale) : '—', unit: '%', trend: 'down', goodDirection: 'up', deltaLabel: rec ? formatCurrency(rec.savings.costEur, locale) : undefined, target: 'simulated / shadow', asOf: recommendationState.asOf, source: recommendationState.source, tooltip: 'Whole-dispatch energy cost saving projected by the BFF MILP optimiser (PuLP/CBC) relative to the unshifted baseline. Reported on a whole-dispatch basis; the demo scenario achieves 7.25% (€2,688.7) whole-dispatch and 21.74% on the flexible-only portion.', actionHint: 'the dispatch schedule', onClick: () => revealPanel('energy-schedule') },
      { id: 'co2', label: 'CO₂ intensity', value: formatNumber(avgCarbon, locale), unit: 'gCO₂/kWh', trend: 'down', goodDirection: 'down', deltaLabel: rec ? `−${rec.savings.co2Pct}%` : undefined, target: 'target 230', tooltip: "Average grid carbon intensity across today's dispatch intervals in grams of CO₂ per kWh. Shifting load to cleaner off-peak hours reduces this figure; the delta shows the CO₂ saving from optimisation.", actionHint: 'the emissions ledger', onClick: () => emit('nav.intent', { route: `/${site}/sustainability-compliance/emissions-ledger` }) },
      { id: 'shiftable', label: 'Shiftable load', value: '18', unit: 'MW', target: 'within constraints', trend: 'flat', tooltip: 'Estimated flexible electrical load the optimiser can time-shift—currently 18 MW of reheat and auxiliary processes—within the configured shift-window and concurrency constraints.' },
    ]
  }, [recommendationState.data, recommendationState.asOf, recommendationState.source, intervalsState.asOf, intervalsState.source, peakPrice, overlay, avgCarbon, locale, emit, site])

  const scheduleColumns: DataTableColumn<EnergyScheduleRow>[] = [
    { key: 'batchId', label: 'Process', type: 'text' },
    { key: 'processType', label: 'Type', type: 'enum' },
    { key: 'grade', label: 'Grade', type: 'enum' },
    { key: 'scheduledAt', label: 'Window', type: 'date', render: (row) => formatTime(row.scheduledAt, locale) },
    { key: 'tonnage', label: 'Tonnage', type: 'number', align: 'right' },
    { key: 'priceEurMwh', label: '€/MWh', type: 'number', align: 'right', render: (row) => formatNumber(row.priceEurMwh, locale) },
    { key: 'shiftMinutes', label: 'Shift (min)', type: 'number', align: 'right' },
    { key: 'urgent', label: 'Status', type: 'enum', render: (row) => <SeverityPill severity={row.urgent ? 'WARNING' : 'INFO'} label={row.urgent ? 'Fixed (urgent)' : 'Shiftable'} /> },
  ]

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />
      <div id="spot-price-chart">
      <ChartContainer
        title="Spot price & scheduled load"
        summary={`Day-ahead price peaks near €${peakPrice}/MWh in the evening; the optimized load (shaded) shifts flexible reheat away from the peak versus the dashed baseline.`}
        height={300}
        tableColumns={[
          { key: 'time', label: 'Time' },
          { key: 'price', label: '€/MWh' },
          { key: 'baseline', label: 'Baseline MW' },
          { key: 'optimized', label: 'Optimized MW' },
        ]}
        tableRows={overlay.filter((_, index) => index % 6 === 0).map((point) => ({
          time: formatTime(point.t, locale),
          price: point.price,
          baseline: point.baseline,
          optimized: point.optimized,
        }))}
      >
        <PriceLoadChart
          data={overlay}
          priceColor={tokens.status.warning}
          baselineColor={tokens.palette[4]}
          optimizedColor={tokens.palette[2]}
          height={300}
          xFormat={(value) => formatTime(value, locale)}
        />
      </ChartContainer>
      </div>
      <PanelCard
        id="energy-schedule"
        title="Schedule"
        action={<ProofBadges ids={['CHL-01', 'OBJ-01', 'AI-02']} />}
      >
        <StateBoundary state={recommendationState} isEmpty={(rec: EnergyRecommendation) => rec.optimized.schedule.length === 0}>
          {(rec) => (
            <DataTable
              caption="Optimized energy dispatch schedule"
              rows={rec.optimized.schedule}
              columns={scheduleColumns}
              getRowId={(row) => row.batchId}
              defaultSort={[{ key: 'scheduledAt', direction: 'asc' }]}
              exportFileName="novasteel-energy-schedule"
              onRefresh={recommendationState.reload}
            />
          )}
        </StateBoundary>
      </PanelCard>
    </SectionStack>
  )
}
