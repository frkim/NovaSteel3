import { useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  LinearProgress,
  MenuItem,
  Select,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material'
import { useAnalytics } from '../../context/analytics'
import { SeverityPill } from '../primitives/SeverityPill'
import type {
  IncidentCatalogEntry,
  SensorRow,
  SimulatorStatus,
  TriggerIncidentRequest,
} from '../../api/deviceDomain'
import { DEVICE_MESSAGE_KEYS } from './deviceFormat'

export interface IncidentPanelProps {
  status: SimulatorStatus
  onReload: () => void
}

function isGenericIncident(entry: IncidentCatalogEntry): boolean {
  return entry.targetDeviceIds.length === 0 && entry.affectedSignalCodes.length === 0
}

function incidentSeverity(severity: string): string {
  switch (severity) {
    case 'critical':
      return 'CRITICAL'
    case 'high':
      return 'HIGH'
    case 'medium':
      return 'WARNING'
    default:
      return 'INFO'
  }
}

interface TargetDialogProps {
  entry: IncidentCatalogEntry
  sensors: SensorRow[]
  open: boolean
  onClose: () => void
  onConfirm: (req: TriggerIncidentRequest) => Promise<void>
}

function TargetDialog({ entry, sensors, open, onClose, onConfirm }: TargetDialogProps) {
  const { t } = useAnalytics()
  const [deviceId, setDeviceId] = useState('')
  const [sensorId, setSensorId] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Unique device IDs from the sensor list
  const deviceIds = [...new Set(sensors.map((s) => s.deviceId))]
  const filteredSensors = deviceId ? sensors.filter((s) => s.deviceId === deviceId) : sensors

  async function handleConfirm() {
    if (!deviceId) return
    setPending(true)
    setError(null)
    try {
      await onConfirm({
        incidentId: entry.incidentId,
        deviceId,
        sensorId: sensorId || undefined,
      })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setPending(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth aria-labelledby="target-dialog-title">
      <DialogTitle id="target-dialog-title">
        {t('device.incident.selectTarget')} — {entry.label}
      </DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <Box>
            <Typography variant="caption" color="text.secondary" component="label" htmlFor="target-device">
              {t('device.incident.targetDevice')} *
            </Typography>
            <Select
              id="target-device"
              value={deviceId}
              displayEmpty
              fullWidth
              size="small"
              onChange={(e) => {
                setDeviceId(e.target.value)
                setSensorId('')
              }}
              aria-label={t('device.incident.targetDevice')}
            >
              <MenuItem value="">
                <em>— select device —</em>
              </MenuItem>
              {deviceIds.map((id) => (
                <MenuItem key={id} value={id}>
                  {id}
                </MenuItem>
              ))}
            </Select>
          </Box>

          <Box>
            <Typography variant="caption" color="text.secondary" component="label" htmlFor="target-sensor">
              {t('device.incident.targetSensor')}
            </Typography>
            <Select
              id="target-sensor"
              value={sensorId}
              displayEmpty
              fullWidth
              size="small"
              disabled={!deviceId}
              onChange={(e) => setSensorId(e.target.value)}
              aria-label={t('device.incident.targetSensor')}
            >
              <MenuItem value="">
                <em>— any sensor —</em>
              </MenuItem>
              {filteredSensors.map((s) => (
                <MenuItem key={s.sensorId} value={s.sensorId}>
                  {s.displayName}
                </MenuItem>
              ))}
            </Select>
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={pending}>
          {t('device.incident.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={handleConfirm}
          disabled={!deviceId || pending}
          aria-label={t('device.incident.confirm')}
        >
          {t('device.incident.confirm')}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export function IncidentPanel({ status, onReload }: IncidentPanelProps) {
  const { deviceClient, t, can } = useAnalytics()

  const [writeError, setWriteError] = useState<string | null>(null)
  const [pendingTrigger, setPendingTrigger] = useState<string | null>(null)
  const [dialogEntry, setDialogEntry] = useState<IncidentCatalogEntry | null>(null)
  const [pendingClear, setPendingClear] = useState<string | null>(null)
  const [allSensors, setAllSensors] = useState<SensorRow[]>([])

  const canManage = can('platform.capacity.manage')
  const { activeIncidents, availableIncidents } = status

  async function triggerIncident(req: TriggerIncidentRequest) {
    setWriteError(null)
    setPendingTrigger(req.incidentId)
    try {
      await deviceClient.triggerIncident(req)
      onReload()
    } catch (err) {
      setWriteError(err instanceof Error ? err.message : String(err))
    } finally {
      setPendingTrigger(null)
    }
  }

  async function handleTriggerClick(entry: IncidentCatalogEntry) {
    if (isGenericIncident(entry)) {
      // Load sensors for target selection dialog
      const loaded = await deviceClient.getSensors()
      setAllSensors(loaded.value)
      setDialogEntry(entry)
    } else {
      await triggerIncident({
        incidentId: entry.incidentId,
        deviceId: entry.targetDeviceIds[0],
      })
    }
  }

  async function clearIncident(activeIncidentId: string) {
    setWriteError(null)
    setPendingClear(activeIncidentId)
    try {
      await deviceClient.clearIncident(activeIncidentId)
      onReload()
    } catch (err) {
      setWriteError(err instanceof Error ? err.message : String(err))
    } finally {
      setPendingClear(null)
    }
  }

  return (
    <Stack spacing={2}>
      {writeError && (
        <Alert severity="error" onClose={() => setWriteError(null)}>
          {writeError}
        </Alert>
      )}

      {/* Active incidents */}
      <Box component="section" aria-label={t('device.incident.active')}>
        <Typography variant="h3" sx={{ mb: 1 }}>
          {t('device.incident.active')}
        </Typography>
        {activeIncidents.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            {t('device.incident.none')}
          </Typography>
        ) : (
          <Stack spacing={1}>
            {activeIncidents.map((incident) => (
              <Card key={incident.activeIncidentId} variant="outlined">
                <CardContent sx={{ pb: 1 }}>
                  <Stack
                    direction="row"
                    spacing={1}
                    sx={{ alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}
                  >
                    <Typography variant="body2" sx={{ fontWeight: 700 }}>
                      {incident.label}
                    </Typography>
                    <SeverityPill severity={incidentSeverity(incident.severity)} label={incident.severity} />
                  </Stack>
                  <Typography variant="caption" color="text.secondary">
                    {incident.deviceId}
                    {incident.sensorId ? ` · ${incident.sensorId}` : ''}
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    <Stack
                      direction="row"
                      sx={{ justifyContent: 'space-between', mb: 0.25 }}
                    >
                      <Typography variant="caption" color="text.secondary">
                        {t('device.incident.progress')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {t('device.incident.remaining', {
                          minutes: Math.round(incident.remainingMinutes),
                        })}
                      </Typography>
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(100, Math.round(incident.progress * 100))}
                      aria-label={`${incident.label} progress`}
                      sx={{ borderRadius: 1 }}
                    />
                  </Box>
                </CardContent>
                <CardActions sx={{ pt: 0 }}>
                  <Button
                    size="small"
                    color="error"
                    disabled={!canManage || pendingClear === incident.activeIncidentId}
                    onClick={() => clearIncident(incident.activeIncidentId)}
                    aria-label={`${t('device.incident.clear')} ${incident.label}`}
                  >
                    {t('device.incident.clear')}
                  </Button>
                </CardActions>
              </Card>
            ))}
          </Stack>
        )}
      </Box>

      <Divider />

      {/* Incident catalog */}
      <Box component="section" aria-label={t('device.incident.catalog')}>
        <Typography variant="h3" sx={{ mb: 1 }}>
          {t('device.incident.catalog')}
        </Typography>
        <Box
          sx={{
            display: 'grid',
            gap: 1.5,
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          }}
        >
          {availableIncidents.map((entry) => {
            const generic = isGenericIncident(entry)
            const signalText = generic
              ? t('device.incident.affectedAny')
              : entry.affectedSignalCodes.join(', ')
            const isTriggering = pendingTrigger === entry.incidentId

            return (
              <Card key={entry.incidentId} variant="outlined">
                <CardContent sx={{ pb: 1 }}>
                  <Stack
                    direction="row"
                    sx={{ alignItems: 'flex-start', justifyContent: 'space-between', mb: 0.5 }}
                  >
                    <Typography variant="body2" sx={{ fontWeight: 700 }}>
                      {entry.label}
                    </Typography>
                    <SeverityPill
                      severity={incidentSeverity(entry.severity)}
                      label={entry.severity}
                    />
                  </Stack>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 0.75 }}>
                    {entry.description}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {t('device.incident.defaultDuration', {
                      minutes: entry.defaultDurationMinutes,
                    })}
                  </Typography>
                  {signalText && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                      {t('device.incident.affectedSignals', { signals: signalText })}
                    </Typography>
                  )}
                </CardContent>
                <CardActions sx={{ pt: 0 }}>
                  <Tooltip
                    title={
                      !canManage
                        ? DEVICE_MESSAGE_KEYS['device.simulator.permissionHint']
                        : generic
                          ? 'Opens a dialog to select target device/sensor'
                          : ''
                    }
                    disableHoverListener={canManage && !generic}
                  >
                    <span>
                      <Button
                        size="small"
                        variant="contained"
                        disabled={!canManage || isTriggering}
                        onClick={() => handleTriggerClick(entry)}
                        aria-label={`${t('device.incident.trigger')} ${entry.label}`}
                      >
                        {t('device.incident.trigger')}
                      </Button>
                    </span>
                  </Tooltip>
                </CardActions>
              </Card>
            )
          })}
        </Box>
      </Box>

      {/* Target selection dialog for generic incidents */}
      {dialogEntry && (
        <TargetDialog
          entry={dialogEntry}
          sensors={allSensors}
          open={dialogEntry !== null}
          onClose={() => setDialogEntry(null)}
          onConfirm={triggerIncident}
        />
      )}
    </Stack>
  )
}
