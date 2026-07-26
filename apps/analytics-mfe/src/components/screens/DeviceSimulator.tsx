import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { usePolling } from '../../hooks/usePolling'
import { formatNumber } from '../../utils/format'
import { StateBoundary } from '../primitives/StateBoundary'
import { FreshnessBadge } from '../primitives/FreshnessBadge'
import { KpiBand, PanelCard, SectionStack } from './common'
import type { KpiCardModel } from '../primitives/KpiCard'
import { SimulatorControls } from '../devices/SimulatorControls'
import { IncidentPanel } from '../devices/IncidentPanel'

export function DeviceSimulator() {
  const { deviceClient, locale, t } = useAnalytics()

  const simulatorState = useResource(() => deviceClient.getSimulator(), [deviceClient])

  // Poll every 5 s while running
  usePolling(simulatorState.reload, 5000, simulatorState.data?.state === 'running')

  const status = simulatorState.data

  const metrics: KpiCardModel[] = status
    ? [
        {
          id: 'state',
          label: t('device.simulator.kpi.state'),
          value: status.state,
          asOf: simulatorState.asOf,
          source: simulatorState.source,
          tooltip: t('device.simulator.kpi.state.tooltip'),
        },
        {
          id: 'scenario',
          label: t('device.simulator.kpi.scenario'),
          value: status.scenario,
          tooltip: t('device.simulator.kpi.scenario.tooltip'),
        },
        {
          id: 'speed',
          label: t('device.simulator.kpi.speed'),
          value: `${status.speedFactor}×`,
          tooltip: t('device.simulator.kpi.speed.tooltip'),
        },
        {
          id: 'elapsed',
          label: t('device.simulator.kpi.elapsed'),
          value: formatNumber(status.elapsedHours, locale, { maximumFractionDigits: 1 }),
          unit: 'h',
          tooltip: t('device.simulator.kpi.elapsed.tooltip'),
          asOf: simulatorState.asOf,
          source: simulatorState.source,
        },
        {
          id: 'ticks',
          label: t('device.simulator.kpi.ticks'),
          value: String(status.tickCount),
          tooltip: t('device.simulator.kpi.ticks.tooltip'),
        },
        {
          id: 'incidents',
          label: t('device.simulator.kpi.incidents'),
          value: String(status.activeIncidents.length),
          trend: status.activeIncidents.length > 0 ? 'up' : 'flat',
          goodDirection: 'down',
          tooltip: t('device.simulator.kpi.incidents.tooltip'),
        },
      ]
    : []

  return (
    <SectionStack>
      {metrics.length > 0 && <KpiBand metrics={metrics} />}

      <StateBoundary state={simulatorState}>
        {(sim) => (
          <>
            <PanelCard
              title="Simulator controls"
              action={
                <FreshnessBadge
                  asOf={simulatorState.asOf ?? null}
                  source={simulatorState.source}
                />
              }
            >
              <SimulatorControls status={sim} onReload={simulatorState.reload} />
            </PanelCard>

            <PanelCard title="Incidents">
              <IncidentPanel status={sim} onReload={simulatorState.reload} />
            </PanelCard>
          </>
        )}
      </StateBoundary>
    </SectionStack>
  )
}
