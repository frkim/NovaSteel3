import { useMemo } from 'react'
import { useAnalytics } from '../../context/analytics'
import { useTokens } from '../../hooks/useTokens'
import { costTrend } from '../../api/fixtures'
import { LineChart } from '../charts/LineChart'
import { AreaChart } from '../charts/AreaChart'
import { ChartContainer } from '../charts/ChartContainer'
import { KpiBand, SectionStack, TwoColumn } from './common'
import { formatCurrency, formatNumber, formatTime, msOf } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'

export function PlatformCost() {
  const { locale } = useAnalytics()
  const tokens = useTokens()
  const trend = useMemo(() => costTrend(), [])

  const spendToDate = trend.reduce((sum, point) => sum + point.costEur, 0)
  const avgUtil = Math.round(trend.reduce((sum, point) => sum + point.utilizationPct, 0) / trend.length)

  const metrics: KpiCardModel[] = [
    { id: 'spend', label: 'Spend to date', value: formatCurrency(spendToDate, locale), target: 'within budget cap', trend: 'flat' },
    { id: 'rate', label: 'Cost / hour', value: formatCurrency(2.8, locale), target: 'F2 measured', trend: 'flat' },
    { id: 'util', label: 'Utilization', value: String(avgUtil), unit: '%', trend: 'up', goodDirection: 'up', target: 'measurement only' },
    { id: 'fresh', label: 'Freshness', value: '12', unit: 's', target: 'last telemetry', trend: 'flat' },
  ]

  const costSeries = trend.map((point) => ({ x: msOf(point.ts), y: point.costEur }))
  const utilData = trend.map((point) => ({ x: msOf(point.ts), values: { utilization: point.utilizationPct } }))

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />
      <TwoColumn
        main={
          <ChartContainer
            title="Cost trend"
            summary="Hourly non-production capacity cost stays within the budget cap across the demo window."
            height={260}
            tableColumns={[
              { key: 'time', label: 'Time' },
              { key: 'cost', label: '€/h' },
            ]}
            tableRows={trend.map((point) => ({ time: formatTime(point.ts, locale), cost: point.costEur }))}
          >
            <LineChart
              series={[{ id: 'cost', label: 'Cost', color: tokens.palette[0], points: costSeries }]}
              height={260}
              xFormat={(value) => formatTime(value, locale)}
              yFormat={(value) => formatCurrency(value, locale)}
            />
          </ChartContainer>
        }
        side={
          <ChartContainer
            title="Capacity utilization"
            summary="Capacity utilization oscillates around the measured average across the window."
            height={260}
          >
            <AreaChart
              data={utilData}
              keys={[{ id: 'utilization', label: 'Utilization %', color: tokens.palette[2] }]}
              height={260}
              xFormat={(value) => formatTime(value, locale)}
              yFormat={(value) => `${formatNumber(value, locale)}%`}
            />
          </ChartContainer>
        }
      />
    </SectionStack>
  )
}
