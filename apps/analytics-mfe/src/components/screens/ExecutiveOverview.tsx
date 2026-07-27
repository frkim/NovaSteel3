import { useMemo } from 'react'
import { useAnalytics } from '../../context/analytics'
import { useTokens } from '../../hooks/useTokens'
import { executiveSites } from '../../api/fixtures'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { BarChart } from '../charts/BarChart'
import { ProgressBullet } from '../charts/ProgressBullet'
import { ChartContainer } from '../charts/ChartContainer'
import { KpiBand, PanelCard, SectionStack, TwoColumn } from './common'
import { formatNumber } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'
import { ProofBadges } from '../primitives/ProofBadge'

interface SiteRow {
  site: string
  energyDeltaPct: number
  co2DeltaPct: number
  yieldDeltaPct: number
  alerts: number
}

export function ExecutiveOverview() {
  const { emit, locale, site } = useAnalytics()
  const tokens = useTokens()
  const sites = useMemo<SiteRow[]>(() => executiveSites(), [])

  const metrics: KpiCardModel[] = [
    { id: 'energy', label: 'Energy / t', value: '−14', unit: '%', trend: 'down', goodDirection: 'down', deltaLabel: 'on track', target: 'use-case target −14%', tooltip: 'Fleet-wide use-case TARGET: 14% less electrical energy per tonne of crude steel versus the pre-AI baseline year, across all four sites. This is a pilot target, not a measurement; the demo scenario evidences the dispatch mechanics that would contribute to it.', actionHint: 'the spot-price schedule', onClick: () => emit('nav.intent', { route: `/${site}/energy-optimization/spot-price-schedule` }) },
    { id: 'co2', label: 'CO₂', value: '−22', unit: '%', trend: 'down', goodDirection: 'down', deltaLabel: 'on track', target: 'use-case target −22%', tooltip: 'Fleet-wide use-case TARGET: 22% lower Scope 2 market-based CO₂-equivalent emissions versus the pre-AI baseline. This is a pilot target, not a measurement; the single-site 24-hour demo scenario measures a 3.29% whole-dispatch reduction.', actionHint: 'the emissions ledger', onClick: () => emit('nav.intent', { route: `/${site}/sustainability-compliance/emissions-ledger` }) },
    { id: 'yield', label: 'High-grade yield', value: '+8', unit: '%', trend: 'up', goodDirection: 'up', deltaLabel: 'on track', target: 'use-case target +8%', tooltip: 'Fleet-wide use-case TARGET: 8 percentage points more first-pass high-grade yield versus the pre-AI baseline year. This is a pilot target requiring validation across many heats, not a demo measurement.', actionHint: 'quality batches', onClick: () => emit('nav.intent', { route: `/${site}/quality/batches` }) },
    { id: 'warning', label: 'Advance warning', value: '21', unit: 'd', target: 'use-case target ≥21 d', trend: 'flat', tooltip: 'Fleet-wide use-case TARGET (KPI-FUR-01): at least 21 days of advance warning before hearth lining end-of-life, so a reline can be scheduled rather than forced. This is a pilot target, not a measurement — the demo scenario measures a P50 of 19.65 days from lining-rul-piml:1.3.0-demo.', actionHint: 'the lining forecast', onClick: () => emit('nav.intent', { route: `/${site}/furnace-health/lining-forecast` }) },
    { id: 'failures', label: 'Failures prevented', value: '1', target: '€8M avoided (modeled)', trend: 'up', goodDirection: 'up', tooltip: 'Number of major equipment failures avoided since programme start, based on work orders raised from model alerts before the failure event. Avoided cost is a modeled estimate.' },
  ]

  const columns: DataTableColumn<SiteRow>[] = [
    { key: 'site', label: 'Site', type: 'text' },
    { key: 'energyDeltaPct', label: 'Energy Δ%', type: 'number', align: 'right', render: (row) => `${row.energyDeltaPct}%` },
    { key: 'co2DeltaPct', label: 'CO₂ Δ%', type: 'number', align: 'right', render: (row) => `${row.co2DeltaPct}%` },
    { key: 'yieldDeltaPct', label: 'Yield Δ%', type: 'number', align: 'right', render: (row) => `+${row.yieldDeltaPct}%` },
    { key: 'alerts', label: 'Open alerts', type: 'number', align: 'right' },
  ]

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />
      <TwoColumn
        main={
          <ChartContainer
            title="Site comparison"
            summary="Energy, CO₂, and yield improvements across the four-country fleet; Moselle (LU) leads on energy and CO₂ reductions."
            height={300}
            tableColumns={[
              { key: 'site', label: 'Site' },
              { key: 'energy', label: 'Energy Δ%' },
              { key: 'co2', label: 'CO₂ Δ%' },
              { key: 'yield', label: 'Yield Δ%' },
            ]}
            tableRows={sites.map((site) => ({ site: site.site, energy: site.energyDeltaPct, co2: site.co2DeltaPct, yield: site.yieldDeltaPct }))}
          >
            <BarChart
              groups={sites.map((site) => ({
                label: site.site.split(' ')[0],
                values: { energy: Math.abs(site.energyDeltaPct), co2: Math.abs(site.co2DeltaPct), yield: site.yieldDeltaPct },
              }))}
              series={[
                { id: 'energy', label: 'Energy −%', color: tokens.palette[0] },
                { id: 'co2', label: 'CO₂ −%', color: tokens.palette[2] },
                { id: 'yield', label: 'Yield +%', color: tokens.palette[1] },
              ]}
              height={300}
              yFormat={(value) => `${formatNumber(value, locale)}%`}
            />
          </ChartContainer>
        }
        side={
          <PanelCard
            title="Target vs actual"
            action={<ProofBadges ids={['OUT-01', 'OUT-02', 'OUT-03', 'OUT-04']} />}
          >
            <ProgressBullet
              items={[
                { label: 'Energy −14% target', value: 92, target: 100, color: tokens.palette[0] },
                { label: 'CO₂ −22% target', value: 88, target: 100, color: tokens.palette[2] },
                { label: 'Yield +8% target', value: 96, target: 100, color: tokens.palette[1] },
                { label: '≥21-day warning target', value: 100, target: 100, color: tokens.palette[4] },
              ]}
            />
          </PanelCard>
        }
      />
      <PanelCard title="Site scorecard">
        <DataTable
          caption="Executive site scorecard"
          rows={sites}
          columns={columns}
          getRowId={(row) => row.site}
          defaultSort={[{ key: 'site', direction: 'asc' }]}
          exportFileName="novasteel-executive-scorecard"
        />
      </PanelCard>
    </SectionStack>
  )
}
