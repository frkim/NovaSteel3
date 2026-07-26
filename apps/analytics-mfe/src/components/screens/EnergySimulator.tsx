import { useMemo, useState } from 'react'
import { Box, Button, Slider, Stack, Typography } from '@mui/material'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { useTokens } from '../../hooks/useTokens'
import type { EnergyRecommendation } from '../../api/domain'
import { StateBoundary } from '../primitives/StateBoundary'
import { BarChart } from '../charts/BarChart'
import { ChartContainer } from '../charts/ChartContainer'
import { KpiBand, PanelCard, SectionStack, TwoColumn, revealPanel } from './common'
import { formatCurrency, formatNumber } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'

export function EnergySimulator() {
  const { client, emit, locale, can } = useAnalytics()
  const tokens = useTokens()
  const [maxShift, setMaxShift] = useState(180)
  const [maxConcurrent, setMaxConcurrent] = useState(2)
  const [committed, setCommitted] = useState({ maxShiftMinutes: 180, maxConcurrentBatches: 2 })

  const recState = useResource(() => client.simulateEnergy(committed), [client, committed])

  // Instant client-side estimate (<300ms, no round-trip) as controls move (AC-P3-2).
  const estimatedSavingsPct = useMemo(() => {
    const shiftFactor = Math.min(1, maxShift / 240)
    const concurrencyFactor = Math.min(1, maxConcurrent / 3)
    return Math.round((6 + shiftFactor * 6 + concurrencyFactor * 1.5) * 10) / 10
  }, [maxShift, maxConcurrent])

  const metrics: KpiCardModel[] = [
    { id: 'estimate', label: 'Estimated saving (live)', value: formatNumber(estimatedSavingsPct, locale), unit: '%', trend: 'down', goodDirection: 'up', deltaLabel: 'client estimate', target: 'press Simulate to confirm', tooltip: 'Instant client-side estimate updated as you move the sliders, using a linear heuristic (shift-window factor × concurrency factor). Press Simulate schedule to replace this with the BFF MILP-optimized result.', actionHint: 'the baseline vs optimized chart', onClick: () => revealPanel('simulator-chart') },
    { id: 'server', label: 'Confirmed saving', value: recState.data ? formatNumber(recState.data.savings.costPct, locale) : '—', unit: '%', deltaLabel: recState.data ? formatCurrency(recState.data.savings.costEur, locale) : undefined, target: 'BFF optimizer', asOf: recState.asOf, source: recState.source, tooltip: 'MILP-optimized (PuLP/CBC) cost saving confirmed by the BFF for the last submitted scenario, reported on a whole-dispatch basis. The demo scenario yields 7.25% (€2,688.7) whole-dispatch; the flexible-only portion is 21.74%.', actionHint: 'the baseline vs optimized chart', onClick: () => revealPanel('simulator-chart') },
    { id: 'peak', label: 'Peak reduction', value: recState.data ? formatNumber(recState.data.savings.peakPct, locale) : '—', unit: '%', trend: 'down', goodDirection: 'up', target: 'lower evening peak', tooltip: 'Reduction in peak electrical demand achieved by shifting flexible batches away from high-price hours. In the demo scenario, peak falls from 56.0 to 51.58 MW (−7.89%).', actionHint: 'the baseline vs optimized chart', onClick: () => revealPanel('simulator-chart') },
    { id: 'violations', label: 'Hard violations', value: recState.data ? String(recState.data.hardConstraintViolations) : '—', trend: 'flat', goodDirection: 'down', target: 'must be 0', tooltip: 'Count of MILP hard constraints violated in the last simulation—must be zero for a feasible schedule. Hard constraints include tonnage conservation (960.0 t) and batch-window feasibility.' },
  ]

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />
      <TwoColumn
        main={
          <div id="simulator-chart">
          <StateBoundary state={recState}>
            {(rec: EnergyRecommendation) => (
              <ChartContainer
                title="Baseline vs optimized"
                summary={`Optimized dispatch lowers modeled cost from ${formatCurrency(rec.baseline.costEur, locale)} to ${formatCurrency(rec.optimized.costEur, locale)} and peak demand from ${rec.baseline.peakDemandMw} to ${rec.optimized.peakDemandMw} MW, preserving ${rec.optimized.tonnage} t tonnage.`}
                height={280}
                tableColumns={[
                  { key: 'metric', label: 'Metric' },
                  { key: 'baseline', label: 'Baseline' },
                  { key: 'optimized', label: 'Optimized' },
                ]}
                tableRows={[
                  { metric: 'Cost €', baseline: rec.baseline.costEur, optimized: rec.optimized.costEur },
                  { metric: 'Peak MW', baseline: rec.baseline.peakDemandMw, optimized: rec.optimized.peakDemandMw },
                ]}
              >
                <BarChart
                  groups={[
                    { label: 'Cost (k€)', values: { baseline: Math.round(rec.baseline.costEur / 100) / 10, optimized: Math.round(rec.optimized.costEur / 100) / 10 } },
                    { label: 'Peak (MW)', values: { baseline: rec.baseline.peakDemandMw, optimized: rec.optimized.peakDemandMw } },
                  ]}
                  series={[
                    { id: 'baseline', label: 'Baseline', color: tokens.palette[4] },
                    { id: 'optimized', label: 'Optimized', color: tokens.palette[2] },
                  ]}
                  height={280}
                  yFormat={(value) => formatNumber(value, locale)}
                />
              </ChartContainer>
            )}
          </StateBoundary>
          </div>
        }
        side={
          <PanelCard title="Scenario controls">
            <Stack spacing={3}>
              <Box>
                <Typography id="max-shift-label" gutterBottom>
                  Max shift window: {maxShift} min
                </Typography>
                <Slider
                  aria-labelledby="max-shift-label"
                  value={maxShift}
                  min={0}
                  max={240}
                  step={15}
                  marks
                  onChange={(_, value) => setMaxShift(value as number)}
                  valueLabelDisplay="auto"
                />
              </Box>
              <Box>
                <Typography id="max-concurrent-label" gutterBottom>
                  Max concurrent batches: {maxConcurrent}
                </Typography>
                <Slider
                  aria-labelledby="max-concurrent-label"
                  value={maxConcurrent}
                  min={1}
                  max={4}
                  step={1}
                  marks
                  onChange={(_, value) => setMaxConcurrent(value as number)}
                  valueLabelDisplay="auto"
                />
              </Box>
              <Button
                variant="contained"
                onClick={() => setCommitted({ maxShiftMinutes: maxShift, maxConcurrentBatches: maxConcurrent })}
              >
                Simulate schedule
              </Button>
              <Button
                variant="outlined"
                disabled={!can('energy.approve')}
                onClick={() =>
                  emit('toast', {
                    severity: 'success',
                    message: 'Simulated/shadow approval recorded — no operational schedule was written.',
                  })
                }
              >
                Record simulated approval
              </Button>
              <Typography variant="caption" color="text.secondary">
                No UI action writes an operational schedule. Approval is simulated/shadow in Phase 0/1 and is fully audited by the BFF.
              </Typography>
            </Stack>
          </PanelCard>
        }
      />
    </SectionStack>
  )
}
