import { useMemo } from 'react'
import { Stack, Typography } from '@mui/material'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { useTokens } from '../../hooks/useTokens'
import { StateBoundary } from '../primitives/StateBoundary'
import { GaugeChart } from '../charts/GaugeChart'
import { LineChart } from '../charts/LineChart'
import { ChartContainer } from '../charts/ChartContainer'
import { KpiBand, PanelCard, SectionStack, TwoColumn, revealPanel } from './common'
import { formatCurrency, formatNumber } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'
import { ProofBadges } from '../primitives/ProofBadge'

const CAP_PCT = 100
const USED_PCT = 71
const OVERAGE_THRESHOLD = 85

export function SustainabilityEts() {
  const { client, locale } = useAnalytics()
  const tokens = useTokens()
  const summaryState = useResource(() => client.getSustainabilitySummary(), [client])

  const projection = useMemo(
    () =>
      Array.from({ length: 12 }, (_, month) => ({
        x: month,
        y: Math.round((USED_PCT + month * 3.1) * 10) / 10,
      })),
    [],
  )
  const cap = useMemo(() => projection.map((point) => ({ x: point.x, y: CAP_PCT })), [projection])

  const metrics = useMemo<KpiCardModel[]>(() => {
    const price = summaryState.data?.etsAllowancePriceEurTonne ?? 86
    return [
      { id: 'used', label: 'Allowances used', value: String(USED_PCT), unit: '%', trend: 'up', goodDirection: 'down', target: `cap ${CAP_PCT}%`, asOf: summaryState.asOf, source: summaryState.source, tooltip: `Percentage of the period's granted EU ETS allowances committed to date. At ${USED_PCT}%, cumulative use is on track to breach the 100% cap around month 5 at the current burn rate.`, actionHint: 'the allowance gauge', onClick: () => revealPanel('ets-gauge') },
      { id: 'price', label: 'ETS price', value: formatCurrency(price, locale), unit: '/t', target: 'market', trend: 'flat', tooltip: 'Current EU ETS market allowance price per tonne of CO₂, sourced from the day-ahead market via the BFF. This price drives the period monetary exposure calculation.' },
      { id: 'overage', label: 'Projected overage', value: 'Month 5', trend: 'up', goodDirection: 'down', target: `crosses cap ~${OVERAGE_THRESHOLD}%`, tooltip: `Forecast month in which cumulative allowance use will cross the 100% period cap at the current burn rate. The ${OVERAGE_THRESHOLD}% guidance threshold triggers early mitigation review.`, actionHint: 'the ETS projection chart', onClick: () => revealPanel('ets-projection') },
      { id: 'exposure', label: 'Exposure', value: formatCurrency(248000, locale, 'EUR', { notation: 'compact' }), trend: 'down', goodDirection: 'down', target: 'period forecast', tooltip: 'Estimated total period financial exposure from the projected allowance deficit—calculated as modeled overage tonnes × current ETS market price. A synthetic forward estimate, not a financial commitment.' },
    ]
  }, [summaryState.data, summaryState.asOf, summaryState.source, locale])

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />
      <TwoColumn
        main={
          <div id="ets-projection">
          <ChartContainer
            title="ETS allowance projection"
            summary={`Cumulative allowance use projected to breach the cap around month 5; threshold guidance at ${OVERAGE_THRESHOLD}%.`}
            height={280}
            tableColumns={[
              { key: 'month', label: 'Month' },
              { key: 'used', label: 'Used %' },
            ]}
            tableRows={projection.map((point) => ({ month: point.x + 1, used: point.y }))}
          >
            <LineChart
              series={[
                { id: 'used', label: 'Cumulative used', color: tokens.palette[0], points: projection },
                { id: 'cap', label: 'Cap', color: tokens.status.critical, points: cap, dashed: true },
              ]}
              threshold={{ value: OVERAGE_THRESHOLD, label: `Guidance ${OVERAGE_THRESHOLD}%`, color: tokens.status.warning }}
              height={280}
              xFormat={(value) => `M${Math.round(value) + 1}`}
              yFormat={(value) => `${formatNumber(value, locale)}%`}
            />
          </ChartContainer>
          </div>
        }
        side={
          <StateBoundary state={summaryState} dockId="ets-gauge" dockTitle="Allowances used vs cap">
            {() => (
              <PanelCard
                id="ets-gauge"
                title="Allowances used vs cap"
                action={<ProofBadges ids={['REG-03']} />}
              >
                <GaugeChart
                  value={USED_PCT}
                  min={0}
                  max={CAP_PCT}
                  threshold={OVERAGE_THRESHOLD}
                  color={tokens.status.success}
                  thresholdColor={tokens.status.critical}
                  trackColor={tokens.colors.surfaceAlt}
                  valueLabel={`${USED_PCT}%`}
                  height={180}
                />
                <Stack spacing={0.5} sx={{ mt: 1 }}>
                  <Typography variant="body2">
                    {USED_PCT}% of the period allowance is committed; the threshold marker shows the {OVERAGE_THRESHOLD}% guidance line.
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Targets are modeled synthetic figures, not financial commitments.
                  </Typography>
                </Stack>
              </PanelCard>
            )}
          </StateBoundary>
        }
      />
    </SectionStack>
  )
}
