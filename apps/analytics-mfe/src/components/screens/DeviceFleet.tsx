import { useMemo, useState } from 'react'
import {
  Box,
  Button,
  Chip,
  FormControl,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  Stack,
  Typography,
} from '@mui/material'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { useTokens } from '../../hooks/useTokens'
import type { DeviceRow } from '../../api/deviceDomain'
import { StateBoundary } from '../primitives/StateBoundary'
import { SeverityPill } from '../primitives/SeverityPill'
import { FreshnessBadge } from '../primitives/FreshnessBadge'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { KpiBand, PanelCard, SectionStack, revealPanel } from './common'
import { formatDateTime, formatNumber } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'
import { deviceStatusSeverity } from '../devices/deviceFormat'

const FLEET_TABLE_ID = 'fleet-device-table'
const DEVICE_DETAIL_ID = 'fleet-device-detail'

export function DeviceFleet() {
  const { deviceClient, emit, locale, site, t } = useAnalytics()
  const tokens = useTokens()

  const devicesState = useResource(() => deviceClient.getDevices(), [deviceClient])
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [siteFilter, setSiteFilter] = useState<string | null>(null)
  const [typeFilter, setTypeFilter] = useState<string | null>(null)
  const [areaFilter, setAreaFilter] = useState<string | null>(null)

  const devices = devicesState.data ?? []

  const totalDevices = devices.length
  const healthyCount = devices.filter((d) => d.status === 'healthy').length
  const degradedCount = devices.filter((d) => d.status === 'degraded').length
  const faultCount = devices.filter(
    (d) => d.status === 'fault' || d.status === 'offline',
  ).length
  const meanHealthScore =
    totalDevices > 0 ? devices.reduce((sum, d) => sum + d.healthScore, 0) / totalDevices : 0
  const totalActiveIncidents = devices.reduce((sum, d) => sum + d.activeIncidents.length, 0)
  const sensorsOnline = devices.reduce((sum, d) => sum + d.sensorCount, 0)

  const metrics: KpiCardModel[] = [
    {
      id: 'total',
      label: t('device.kpi.totalDevices'),
      value: String(totalDevices),
      asOf: devicesState.asOf,
      source: devicesState.source,
      tooltip: t('device.kpi.totalDevices.tooltip'),
      onClick: () => revealPanel(FLEET_TABLE_ID),
      actionHint: 'the device table',
    },
    {
      id: 'healthy',
      label: t('device.kpi.healthyCount'),
      value: String(healthyCount),
      trend: 'up',
      goodDirection: 'up',
      status: totalDevices > 0 && healthyCount === totalDevices ? 'ok' : 'neutral',
      tooltip: t('device.kpi.healthyCount.tooltip'),
      onClick: () => {
        setStatusFilter(statusFilter === 'healthy' ? null : 'healthy')
        revealPanel(FLEET_TABLE_ID)
      },
      actionHint: 'the device table filtered to healthy',
    },
    {
      id: 'degraded',
      label: t('device.kpi.degradedCount'),
      value: String(degradedCount),
      trend: degradedCount > 0 ? 'up' : 'flat',
      goodDirection: 'down',
      status: degradedCount > 0 ? 'warning' : 'ok',
      tooltip: t('device.kpi.degradedCount.tooltip'),
      onClick: () => {
        setStatusFilter(statusFilter === 'degraded' ? null : 'degraded')
        revealPanel(FLEET_TABLE_ID)
      },
      actionHint: 'the device table filtered to degraded',
    },
    {
      id: 'fault',
      label: t('device.kpi.faultCount'),
      value: String(faultCount),
      trend: faultCount > 0 ? 'up' : 'flat',
      goodDirection: 'down',
      status: faultCount > 0 ? 'critical' : 'ok',
      tooltip: t('device.kpi.faultCount.tooltip'),
      onClick: () => {
        setStatusFilter(statusFilter === 'fault' ? null : 'fault')
        revealPanel(FLEET_TABLE_ID)
      },
      actionHint: 'the device table filtered to fault/offline',
    },
    {
      id: 'health',
      label: t('device.kpi.meanHealthScore'),
      value: formatNumber(meanHealthScore * 100, locale, { maximumFractionDigits: 1 }),
      unit: '%',
      trend: meanHealthScore > 0.9 ? 'up' : 'down',
      goodDirection: 'up',
      tooltip: t('device.kpi.meanHealthScore.tooltip'),
      asOf: devicesState.asOf,
      source: devicesState.source,
      onClick: () => revealPanel(FLEET_TABLE_ID),
      actionHint: 'the device table',
    },
    {
      id: 'incidents',
      label: t('device.kpi.activeIncidents'),
      value: String(totalActiveIncidents),
      trend: totalActiveIncidents > 0 ? 'up' : 'flat',
      goodDirection: 'down',
      status: totalActiveIncidents > 0 ? 'warning' : 'ok',
      tooltip: t('device.kpi.activeIncidents.tooltip'),
      onClick: () => revealPanel(FLEET_TABLE_ID),
      actionHint: 'the device table',
    },
    {
      id: 'sensors',
      label: t('device.kpi.sensorsOnline'),
      value: String(sensorsOnline),
      tooltip: t('device.kpi.sensorsOnline.tooltip'),
      onClick: () => revealPanel(FLEET_TABLE_ID),
      actionHint: 'the device table',
    },
  ]

  const displayedDevices = useMemo(() => {
    let result = devices
    if (statusFilter) {
      result = statusFilter === 'fault'
        ? result.filter((d) => d.status === 'fault' || d.status === 'offline')
        : result.filter((d) => d.status === statusFilter)
    }
    if (siteFilter) {
      result = result.filter((d) => d.site === siteFilter)
    }
    if (typeFilter) {
      result = result.filter((d) => d.description === typeFilter)
    }
    if (areaFilter) {
      result = result.filter((d) => d.area === areaFilter)
    }
    return result
  }, [devices, statusFilter, siteFilter, typeFilter, areaFilter])

  const filterOptions = useMemo(() => ({
    sites: [...new Set(devices.map((d) => d.site))].sort(),
    types: [...new Set(devices.map((d) => d.description))].sort(),
    areas: [...new Set(devices.map((d) => d.area))].sort(),
    statuses: [...new Set(devices.map((d) => d.status))].sort(),
  }), [devices])

  const hasActiveFilters = !!(statusFilter || siteFilter || typeFilter || areaFilter)
  const clearAllFilters = () => {
    setStatusFilter(null)
    setSiteFilter(null)
    setTypeFilter(null)
    setAreaFilter(null)
  }

  const selectedDevice = useMemo(
    () => devices.find((d) => d.deviceId === selectedDeviceId) ?? null,
    [devices, selectedDeviceId],
  )

  const detailState = useResource(
    () =>
      selectedDeviceId
        ? deviceClient.getDevice(selectedDeviceId)
        : Promise.resolve({ value: null, source: 'fixture' as const, asOf: '' }),
    [deviceClient, selectedDeviceId],
  )

  const columns: DataTableColumn<DeviceRow>[] = [
    { key: 'deviceId', label: 'Device', type: 'text' },
    { key: 'area', label: 'Area', type: 'enum' },
    { key: 'description', label: 'Description', type: 'text' },
    {
      key: 'status',
      label: 'Status',
      type: 'enum',
      render: (row) => (
        <SeverityPill severity={deviceStatusSeverity(row.status)} label={row.status} />
      ),
      value: (row) => row.status,
    },
    {
      key: 'sensorCount',
      label: 'Sensors',
      type: 'number',
      align: 'right',
    },
    {
      key: 'healthScore',
      label: 'Health',
      type: 'number',
      align: 'right',
      render: (row) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 80 }}>
          <LinearProgress
            variant="determinate"
            value={Math.round(row.healthScore * 100)}
            sx={{ flex: 1, borderRadius: 1 }}
            color={row.healthScore > 0.9 ? 'success' : row.healthScore > 0.7 ? 'warning' : 'error'}
            aria-label={`Health ${Math.round(row.healthScore * 100)}%`}
          />
          <Typography variant="caption">{Math.round(row.healthScore * 100)}%</Typography>
        </Box>
      ),
    },
    {
      key: 'uptimePct',
      label: 'Uptime %',
      type: 'number',
      align: 'right',
      render: (row) => `${formatNumber(row.uptimePct * 100, locale, { maximumFractionDigits: 1 })}%`,
    },
    {
      key: 'activeIncidents',
      label: 'Incidents',
      type: 'number',
      align: 'right',
      value: (row) => row.activeIncidents.length,
      render: (row) => String(row.activeIncidents.length),
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
      <KpiBand metrics={metrics} />

      {/* Filter toolbar */}
      <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>{t('device.fleet.filter.site')}</InputLabel>
          <Select
            label={t('device.fleet.filter.site')}
            value={siteFilter ?? ''}
            onChange={(e) => setSiteFilter(e.target.value || null)}
          >
            <MenuItem value="">{t('device.fleet.filter.all')}</MenuItem>
            {filterOptions.sites.map((v) => (
              <MenuItem key={v} value={v}>{v}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>{t('device.fleet.filter.type')}</InputLabel>
          <Select
            label={t('device.fleet.filter.type')}
            value={typeFilter ?? ''}
            onChange={(e) => setTypeFilter(e.target.value || null)}
          >
            <MenuItem value="">{t('device.fleet.filter.all')}</MenuItem>
            {filterOptions.types.map((v) => (
              <MenuItem key={v} value={v}>{v}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>{t('device.fleet.filter.status')}</InputLabel>
          <Select
            label={t('device.fleet.filter.status')}
            value={statusFilter ?? ''}
            onChange={(e) => setStatusFilter(e.target.value || null)}
          >
            <MenuItem value="">{t('device.fleet.filter.all')}</MenuItem>
            {filterOptions.statuses.map((v) => (
              <MenuItem key={v} value={v}>{v}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>{t('device.fleet.filter.area')}</InputLabel>
          <Select
            label={t('device.fleet.filter.area')}
            value={areaFilter ?? ''}
            onChange={(e) => setAreaFilter(e.target.value || null)}
          >
            <MenuItem value="">{t('device.fleet.filter.all')}</MenuItem>
            {filterOptions.areas.map((v) => (
              <MenuItem key={v} value={v}>{v}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Stack>

      {hasActiveFilters && (
        <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
          {siteFilter && (
            <Chip size="small" label={`${t('device.fleet.filter.site')}: ${siteFilter}`} onDelete={() => setSiteFilter(null)} />
          )}
          {typeFilter && (
            <Chip size="small" label={`${t('device.fleet.filter.type')}: ${typeFilter}`} onDelete={() => setTypeFilter(null)} />
          )}
          {statusFilter && (
            <Chip size="small" label={`${t('device.fleet.filter.status')}: ${statusFilter}`} onDelete={() => setStatusFilter(null)} />
          )}
          {areaFilter && (
            <Chip size="small" label={`${t('device.fleet.filter.area')}: ${areaFilter}`} onDelete={() => setAreaFilter(null)} />
          )}
          <Button size="small" onClick={clearAllFilters}>
            {t('device.fleet.filter.clearAll')}
          </Button>
          <Typography variant="caption" color="text.secondary">
            {t('device.fleet.filter.showing')
              .replace('{filtered}', String(displayedDevices.length))
              .replace('{total}', String(devices.length))}
          </Typography>
        </Stack>
      )}

      <PanelCard
        id={FLEET_TABLE_ID}
        title="Device fleet"
        action={
          <FreshnessBadge asOf={devicesState.asOf ?? null} source={devicesState.source} />
        }
      >
        <StateBoundary
          state={devicesState}
          isEmpty={(rows) => rows.length === 0}
          loadingVariant="gauge"
          loadingCaption={t('device.loading.caption')}
        >
          {() => (
            <DataTable
              caption="Device fleet — click a row to inspect sensors"
              rows={displayedDevices}
              columns={columns}
              getRowId={(row) => row.deviceId}
              defaultSort={[{ key: 'healthScore', direction: 'asc' }]}
              exportFileName="novasteel-device-fleet"
              pageSizeOptions={[10, 25, 100]}
              initialPageSize={10}
              onRowClick={(row) => {
                setSelectedDeviceId(
                  selectedDeviceId === row.deviceId ? null : row.deviceId,
                )
                revealPanel(DEVICE_DETAIL_ID)
              }}
              onRefresh={devicesState.reload}
            />
          )}
        </StateBoundary>
      </PanelCard>

      {/* Device detail panel */}
      {selectedDevice && (
        <PanelCard
          id={DEVICE_DETAIL_ID}
          title={`${selectedDevice.deviceId} — ${selectedDevice.description}`}
          onDockClose={() => setSelectedDeviceId(null)}
          dockHeight={380}
          action={
            <Button
              size="small"
              variant="outlined"
              onClick={() =>
                emit('nav.intent', { route: `/${site}/device-operations/sensors` })
              }
              aria-label={t('device.fleet.navigateToSensors')}
            >
              {t('device.fleet.navigateToSensors')}
            </Button>
          }
        >
          <StateBoundary state={detailState}>
            {(detail) => {
              if (!detail) {
                return (
                  <Typography variant="body2" color="text.secondary">
                    Device not found.
                  </Typography>
                )
              }
              return (
                <Stack spacing={0.5}>
                  {detail.sensors.map((sensor) => (
                    <Box
                      key={sensor.sensorId}
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: 'minmax(160px,2fr) 80px 80px 60px 1fr',
                        gap: 1,
                        alignItems: 'center',
                        py: 0.5,
                        borderBottom: 1,
                        borderColor: 'divider',
                      }}
                    >
                      <Typography variant="body2" noWrap title={sensor.displayName}>
                        {sensor.displayName}
                      </Typography>
                      <Typography variant="body2" align="right" noWrap>
                        {sensor.value !== null
                          ? `${formatNumber(sensor.value, locale, { maximumFractionDigits: 2 })} ${sensor.unit}`
                          : '—'}
                      </Typography>
                      <Box>
                        <SeverityPill
                          severity={
                            sensor.status === 'normal'
                              ? 'INFO'
                              : sensor.status === 'warning'
                                ? 'WARNING'
                                : sensor.status === 'alarm'
                                  ? 'CRITICAL'
                                  : 'MEDIUM'
                          }
                          label={sensor.status}
                        />
                      </Box>
                      <Typography
                        variant="caption"
                        aria-label={`trend: ${sensor.trend}`}
                        sx={{
                          color:
                            sensor.trend === 'rising'
                              ? tokens.status.warning
                              : sensor.trend === 'falling'
                                ? tokens.status.info
                                : 'text.secondary',
                        }}
                      >
                        {sensor.trend === 'rising'
                          ? '▲'
                          : sensor.trend === 'falling'
                            ? '▼'
                            : '■'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" noWrap>
                        {sensor.signalCode}
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              )
            }}
          </StateBoundary>
        </PanelCard>
      )}
    </SectionStack>
  )
}
