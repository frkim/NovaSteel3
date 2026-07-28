import { useEffect, useMemo, useState } from 'react'
import {
  Box,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
} from '@mui/material'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { useTokens } from '../../hooks/useTokens'
import type { SensorRow, SensorStatus } from '../../api/deviceDomain'
import { StateBoundary } from '../primitives/StateBoundary'
import { SeverityPill } from '../primitives/SeverityPill'
import { FreshnessBadge } from '../primitives/FreshnessBadge'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { PanelCard, SectionStack, revealPanel } from './common'
import { formatDateTime, formatNumber } from '../../utils/format'
import { SensorChartPanel } from '../devices/SensorChartPanel'
import { formatSensorValue, formatSamplePeriod, sensorStatusSeverity, trendGlyph } from '../devices/deviceFormat'

const SENSOR_STATUSES: SensorStatus[] = ['normal', 'warning', 'alarm', 'stale']

export function DeviceSensors() {
  const { deviceClient, locale, t } = useAnalytics()
  const tokens = useTokens()

  const sensorsState = useResource(() => deviceClient.getSensors(), [deviceClient])
  const sensors = sensorsState.data ?? []

  const [deviceFilter, setDeviceFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedSensorId, setSelectedSensorId] = useState<string | null>(null)

  // Unique devices for the device filter
  const devices = useMemo(() => {
    const map = new Map<string, string>()
    for (const s of sensors) {
      if (!map.has(s.deviceId)) map.set(s.deviceId, s.deviceId)
    }
    return [...map.entries()]
  }, [sensors])

  // Filtered sensors
  const filteredSensors = useMemo(() => {
    return sensors.filter((s) => {
      const deviceMatch = deviceFilter === 'all' || s.deviceId === deviceFilter
      const statusMatch = statusFilter === 'all' || s.status === statusFilter
      return deviceMatch && statusMatch
    })
  }, [sensors, deviceFilter, statusFilter])

  // Clear selected sensor if it's no longer in the filtered set
  useEffect(() => {
    if (selectedSensorId && !filteredSensors.find((s) => s.sensorId === selectedSensorId)) {
      setSelectedSensorId(null)
    }
  }, [filteredSensors, selectedSensorId])

  const columns: DataTableColumn<SensorRow>[] = [
    {
      key: 'displayName',
      label: 'Sensor',
      type: 'text',
    },
    {
      key: 'deviceId',
      label: 'Device',
      type: 'enum',
    },
    {
      key: 'area',
      label: 'Area',
      type: 'enum',
    },
    {
      key: 'signalCode',
      label: 'Signal code',
      type: 'text',
    },
    {
      key: 'value',
      label: 'Value',
      type: 'number',
      align: 'right',
      render: (row) => formatSensorValue(row.value, row.unit, locale),
      value: (row) => row.value ?? undefined,
    },
    {
      key: 'unit',
      label: 'Unit',
      type: 'enum',
    },
    {
      key: 'status',
      label: 'Status',
      type: 'enum',
      render: (row) => (
        <SeverityPill severity={sensorStatusSeverity(row.status)} label={row.status} />
      ),
      value: (row) => row.status,
    },
    {
      key: 'trend',
      label: 'Trend',
      type: 'enum',
      render: (row) => {
        const { glyph, label } = trendGlyph(row.trend)
        return (
          <Box
            component="span"
            aria-label={label}
            sx={{
              color:
                row.trend === 'rising'
                  ? tokens.status.warning
                  : row.trend === 'falling'
                    ? tokens.status.info
                    : 'text.secondary',
              fontWeight: 700,
            }}
          >
            {glyph}
          </Box>
        )
      },
      value: (row) => row.trend,
    },
    {
      key: 'deviationPct',
      label: 'Deviation %',
      type: 'number',
      align: 'right',
      render: (row) =>
        `${row.deviationPct > 0 ? '+' : ''}${formatNumber(row.deviationPct, locale, {
          maximumFractionDigits: 1,
        })}%`,
    },
    {
      key: 'low',
      label: 'Range',
      type: 'text',
      render: (row) => `${row.low}–${row.high} ${row.unit}`,
      value: (row) => row.low,
    },
    {
      key: 'samplePeriodMs',
      label: 'Sample period',
      type: 'text',
      render: (row) => formatSamplePeriod(row.samplePeriodMs),
      value: (row) => row.samplePeriodMs,
    },
    {
      key: 'lastSampleAt',
      label: 'Last sample',
      type: 'date',
      render: (row) => formatDateTime(row.lastSampleAt, locale),
    },
  ]

  return (
    <SectionStack>
      <PanelCard
        title="Sensor Explorer"
        action={
          <FreshnessBadge asOf={sensorsState.asOf ?? null} source={sensorsState.source} />
        }
      >
        {/* Filters */}
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={1.5}
          sx={{ mb: 2 }}
        >
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel id="device-filter-label">{t('device.sensors.deviceFilter')}</InputLabel>
            <Select
              labelId="device-filter-label"
              value={deviceFilter}
              label={t('device.sensors.deviceFilter')}
              onChange={(e) => setDeviceFilter(e.target.value)}
              aria-label={t('device.sensors.deviceFilter')}
            >
              <MenuItem value="all">{t('device.sensors.deviceAll')}</MenuItem>
              {devices.map(([id]) => (
                <MenuItem key={id} value={id}>
                  {id}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel id="status-filter-label">{t('device.sensors.statusFilter')}</InputLabel>
            <Select
              labelId="status-filter-label"
              value={statusFilter}
              label={t('device.sensors.statusFilter')}
              onChange={(e) => setStatusFilter(e.target.value)}
              aria-label={t('device.sensors.statusFilter')}
            >
              <MenuItem value="all">{t('device.sensors.statusAll')}</MenuItem>
              {SENSOR_STATUSES.map((s) => (
                <MenuItem key={s} value={s}>
                  {s}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>

        <StateBoundary
          state={sensorsState}
          isEmpty={(rows) => rows.length === 0}
          loadingVariant="gauge"
          loadingCaption={t('device.loading.caption')}
        >
          {() => (
            <DataTable
              caption="Sensor explorer — click a row to chart its time series"
              rows={filteredSensors}
              columns={columns}
              getRowId={(row) => row.sensorId}
              defaultSort={[{ key: 'status', direction: 'asc' }]}
              exportFileName="novasteel-sensors"
              pageSizeOptions={[10, 25, 100]}
              initialPageSize={10}
              onRowClick={(row) => {
                const nextId = selectedSensorId === row.sensorId ? null : row.sensorId
                setSelectedSensorId(nextId)
                if (nextId) {
                  revealPanel('sensor-chart-panel')
                }
              }}
              onRefresh={sensorsState.reload}
            />
          )}
        </StateBoundary>
      </PanelCard>

      {/* Linked chart panel */}
      {selectedSensorId && (
        <PanelCard
          id="sensor-chart-panel"
          title={t('device.sensors.chart')}
          onDockClose={() => setSelectedSensorId(null)}
          dockHeight={420}
        >
          <SensorChartPanel
            sensorId={selectedSensorId}
            onClose={() => setSelectedSensorId(null)}
          />
        </PanelCard>
      )}
    </SectionStack>
  )
}
