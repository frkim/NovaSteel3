import { useMemo, useState } from 'react'
import { ToggleButton, ToggleButtonGroup, Typography } from '@mui/material'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { useTokens } from '../../hooks/useTokens'
import { thermalMatrix } from '../../api/fixtures'
import { StateBoundary } from '../primitives/StateBoundary'
import { SeverityPill } from '../primitives/SeverityPill'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { Heatmap } from '../charts/Heatmap'
import { LineChart } from '../charts/LineChart'
import { ChartContainer } from '../charts/ChartContainer'
import { KpiBand, PanelCard, SectionStack, TwoColumn, revealPanel } from './common'
import { formatDateTime, formatNumber, formatTime, msOf } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'

const ANOMALY_THRESHOLD = 700

interface AnomalyRow {
  id: string
  zone: string
  time: string
  value: number
  status: string
}

export function FurnaceThermal() {
  const { client, locale } = useAnalytics()
  const tokens = useTokens()
  const [selectedZone, setSelectedZone] = useState('SECTOR-07')
  const telemetryState = useResource(() => client.getTelemetry(), [client])

  const matrix = useMemo(() => thermalMatrix(), [])
  const zoneIndex = Math.max(0, matrix.zones.indexOf(selectedZone))

  const anomalies = useMemo<AnomalyRow[]>(() => {
    const rows: AnomalyRow[] = []
    matrix.zones.forEach((zone, row) => {
      matrix.hours.forEach((hour, column) => {
        const value = matrix.values[row][column]
        if (value >= ANOMALY_THRESHOLD) {
          rows.push({ id: `${zone}-${column}`, zone, time: hour, value, status: value >= 720 ? 'CRITICAL' : 'WARNING' })
        }
      })
    })
    return rows
  }, [matrix])

  const selectedSeries = useMemo(
    () => matrix.values[zoneIndex].map((value, index) => ({ x: msOf(matrix.hours[index]), y: value })),
    [matrix, zoneIndex],
  )

  const metrics: KpiCardModel[] = [
    { id: 'peak', label: `${selectedZone} peak`, value: formatNumber(Math.max(...matrix.values[zoneIndex]), locale), unit: '°C', trend: 'up', goodDirection: 'down', deltaLabel: 'rising', target: `anomaly ≥ ${ANOMALY_THRESHOLD} °C`, tooltip: '24-hour peak temperature for the selected hearth sector from the thermocouple array; values at or above 700 °C are classified as anomalies and flagged on the heatmap.', onClick: () => revealPanel('thermal-sensor-trend'), actionHint: 'the selected sensor trend chart' },
    { id: 'slope', label: '6-hour slope', value: '3.4', unit: '°C/h', trend: 'up', goodDirection: 'down', deltaLabel: 'HEARTH-07', target: 'watch trend', tooltip: 'Rate of temperature change for HEARTH-07 over the last six hours, derived from adjacent thermocouple readings; a rising slope corroborated by heat-flux residuals indicates a developing hotspot.', onClick: () => revealPanel('thermal-sensor-trend'), actionHint: 'the selected sensor trend chart' },
    { id: 'anomalies', label: 'Anomaly cells', value: String(anomalies.length), trend: 'up', goodDirection: 'down', target: 'zones × hours', tooltip: 'Count of zone–hour cells in the 24-hour thermal matrix where temperature meets or exceeds the 700 °C anomaly threshold, aggregated across all hearth sectors.', onClick: () => revealPanel('thermal-anomalies'), actionHint: 'the thermal anomaly table' },
    { id: 'cooling', label: 'Cooling ΔT', value: '9.4', unit: '°C', trend: 'flat', target: 'inlet vs outlet', tooltip: 'Temperature differential between cooling-circuit inlet and outlet for the primary cooling loop; a rising ΔT indicates reduced heat-removal capacity and should be trended against lining wear.' },
  ]

  const anomalyColumns: DataTableColumn<AnomalyRow>[] = [
    { key: 'zone', label: 'Zone', type: 'text' },
    { key: 'time', label: 'Time', type: 'date', render: (row) => formatDateTime(row.time, locale) },
    { key: 'value', label: 'Temperature °C', type: 'number', align: 'right' },
    { key: 'status', label: 'Status', type: 'enum', render: (row) => <SeverityPill severity={row.status} /> },
  ]

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />
      <TwoColumn
        main={
          <ChartContainer
            title="Thermal signature (hearth sectors × time)"
            summary={`Synthetic thermal map; ${selectedZone} develops a localized warm zone. ▲ marks cells at or above ${ANOMALY_THRESHOLD} °C.`}
            height={280}
          >
            <Heatmap
              zones={matrix.zones}
              columns={matrix.hours}
              values={matrix.values}
              columnFormat={(value) => formatTime(value, locale)}
              anomalyThreshold={ANOMALY_THRESHOLD}
              height={280}
            />
          </ChartContainer>
        }
        side={
          <PanelCard
            id="thermal-sensor-trend"
            title="Selected sensor"
            action={
              <ToggleButtonGroup
                size="small"
                exclusive
                value={selectedZone}
                onChange={(_, value) => value && setSelectedZone(value)}
                aria-label="Select hearth sector"
              >
                {matrix.zones.map((zone) => (
                  <ToggleButton key={zone} value={zone} sx={{ px: 1 }}>
                    {zone.replace('SECTOR-', 'S')}
                  </ToggleButton>
                ))}
              </ToggleButtonGroup>
            }
          >
            <ChartContainer
              title={`${selectedZone} trend`}
              summary={`${selectedZone} temperature over the last 24 hours.`}
              height={200}
            >
              <LineChart
                series={[{ id: 'sensor', label: selectedZone, color: tokens.palette[zoneIndex % tokens.palette.length], points: selectedSeries }]}
                height={200}
                xFormat={(value) => formatTime(value, locale)}
                yFormat={(value) => formatNumber(value, locale)}
              />
            </ChartContainer>
            <Typography variant="caption" color="text.secondary">
              Neighboring thermocouples, cooling-water ΔT, and heat-flux residual agree — unlike a single bad sensor.
            </Typography>
          </PanelCard>
        }
      />
      <PanelCard id="thermal-anomalies" title="Thermal anomalies">
        <StateBoundary state={telemetryState} isEmpty={() => anomalies.length === 0} emptyMessage="No anomalies detected.">
          {() => (
            <DataTable
              caption="Thermal anomalies linked to the heatmap"
              rows={anomalies}
              columns={anomalyColumns}
              getRowId={(row) => row.id}
              defaultSort={[{ key: 'time', direction: 'desc' }]}
              exportFileName="novasteel-thermal-anomalies"
            />
          )}
        </StateBoundary>
      </PanelCard>
    </SectionStack>
  )
}
