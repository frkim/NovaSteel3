import { useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Divider,
  MenuItem,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import { useAnalytics } from '../../context/analytics'
import { SeverityPill } from '../primitives/SeverityPill'
import type { SimulatorCommandRequest, SimulatorStatus } from '../../api/deviceDomain'
import { SIMULATOR_SPEEDS } from '../../api/deviceDomain'
import { formatDateTime, formatNumber } from '../../utils/format'

function stateSeverity(state: string): string {
  if (state === 'running') return 'INFO'
  if (state === 'paused') return 'WARNING'
  return 'MEDIUM'
}

export interface SimulatorControlsProps {
  status: SimulatorStatus
  onReload: () => void
}

export function SimulatorControls({ status, onReload }: SimulatorControlsProps) {
  const { deviceClient, locale, t, can } = useAnalytics()

  const [pending, setPending] = useState(false)
  const [writeError, setWriteError] = useState<string | null>(null)
  const [seed, setSeed] = useState(String(status.seed))

  const canManage = can('platform.capacity.manage')
  const { state, scenario, speedFactor, availableScenarios } = status

  const canStart = state === 'stopped'
  const canPause = state === 'running'
  const canResume = state === 'paused'
  const canStop = state === 'running' || state === 'paused'
  const canReset = state === 'stopped'

  async function sendCmd(req: SimulatorCommandRequest) {
    setWriteError(null)
    setPending(true)
    try {
      await deviceClient.sendCommand(req)
      onReload()
    } catch (err) {
      setWriteError(err instanceof Error ? err.message : String(err))
    } finally {
      setPending(false)
    }
  }

  const btnProps = (enabled: boolean) => ({
    disabled: !canManage || pending || !enabled,
    variant: 'outlined' as const,
    size: 'small' as const,
  })

  return (
    <Box component="section" aria-label={t('device.simulator.controls')}>
      <Stack spacing={2}>
        {/* State chip */}
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            {t('device.simulator.state')}
          </Typography>
          <SeverityPill severity={stateSeverity(state)} label={state} />
          {status.startedAt && (
            <Typography variant="caption" color="text.secondary">
              started {formatDateTime(status.startedAt, locale)}
            </Typography>
          )}
        </Stack>

        {/* Telemetry grid */}
        <Box
          sx={{
            display: 'grid',
            gap: 1,
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          }}
        >
          {(
            [
              { label: t('device.simulator.clock'), value: formatDateTime(status.simulatedClock, locale) },
              { label: t('device.simulator.elapsed'), value: `${formatNumber(status.elapsedHours, locale)} h` },
              { label: t('device.simulator.ticks'), value: formatNumber(status.tickCount, locale, { maximumFractionDigits: 0 }) },
              { label: t('device.simulator.devices'), value: String(status.deviceCount) },
              { label: t('device.simulator.sensors'), value: String(status.sensorCount) },
            ] as const
          ).map(({ label, value }) => (
            <Box key={label}>
              <Typography variant="caption" color="text.secondary">
                {label}
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {value}
              </Typography>
            </Box>
          ))}
        </Box>

        <Divider />

        {/* Configuration selects */}
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={2}
          sx={{ alignItems: { sm: 'flex-end' } }}
        >
          <Box sx={{ minWidth: 180 }}>
            <Typography variant="caption" color="text.secondary" component="label" htmlFor="sim-scenario">
              {t('device.simulator.scenario')}
            </Typography>
            <Select
              id="sim-scenario"
              value={scenario}
              size="small"
              fullWidth
              disabled={!canManage || pending}
              onChange={(e) => sendCmd({ command: 'set-scenario', scenario: e.target.value })}
              aria-label={t('device.simulator.scenario')}
            >
              {availableScenarios.map((s) => (
                <MenuItem key={s} value={s}>
                  {s}
                </MenuItem>
              ))}
            </Select>
          </Box>

          <Box sx={{ minWidth: 120 }}>
            <Typography variant="caption" color="text.secondary" component="label" htmlFor="sim-speed">
              {t('device.simulator.speed')}
            </Typography>
            <Select
              id="sim-speed"
              value={speedFactor}
              size="small"
              fullWidth
              disabled={!canManage || pending}
              onChange={(e) => sendCmd({ command: 'set-speed', speedFactor: Number(e.target.value) })}
              aria-label={t('device.simulator.speed')}
            >
              {SIMULATOR_SPEEDS.map((s) => (
                <MenuItem key={s} value={s}>
                  {s}×
                </MenuItem>
              ))}
            </Select>
          </Box>

          <TextField
            label={t('device.simulator.seed')}
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            size="small"
            type="number"
            sx={{ minWidth: 100 }}
            disabled={!canManage || pending || state !== 'stopped'}
            slotProps={{ htmlInput: { 'aria-label': t('device.simulator.seed') } }}
          />
        </Stack>

        {/* Command buttons */}
        <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
          <Tooltip
            title={
              !canManage
                ? t('device.simulator.permissionHint')
                : !canStart
                  ? `Cannot start while ${state}`
                  : ''
            }
            disableHoverListener={canManage && canStart}
          >
            <span>
              <Button
                {...btnProps(canStart)}
                variant="contained"
                color="primary"
                onClick={() =>
                  sendCmd({
                    command: 'start',
                    scenario,
                    speedFactor,
                    seed: Number(seed) || undefined,
                  })
                }
                aria-label={t('device.simulator.start')}
              >
                {t('device.simulator.start')}
              </Button>
            </span>
          </Tooltip>

          <Tooltip
            title={!canManage ? t('device.simulator.permissionHint') : ''}
            disableHoverListener={canManage}
          >
            <span>
              <Button
                {...btnProps(canPause)}
                onClick={() => sendCmd({ command: 'pause' })}
                aria-label={t('device.simulator.pause')}
              >
                {t('device.simulator.pause')}
              </Button>
            </span>
          </Tooltip>

          <Tooltip
            title={!canManage ? t('device.simulator.permissionHint') : ''}
            disableHoverListener={canManage}
          >
            <span>
              <Button
                {...btnProps(canResume)}
                onClick={() => sendCmd({ command: 'resume' })}
                aria-label={t('device.simulator.resume')}
              >
                {t('device.simulator.resume')}
              </Button>
            </span>
          </Tooltip>

          <Tooltip
            title={!canManage ? t('device.simulator.permissionHint') : ''}
            disableHoverListener={canManage}
          >
            <span>
              <Button
                {...btnProps(canStop)}
                color="warning"
                onClick={() => sendCmd({ command: 'stop' })}
                aria-label={t('device.simulator.stop')}
              >
                {t('device.simulator.stop')}
              </Button>
            </span>
          </Tooltip>

          <Tooltip
            title={!canManage ? t('device.simulator.permissionHint') : ''}
            disableHoverListener={canManage}
          >
            <span>
              <Button
                {...btnProps(canReset)}
                color="error"
                onClick={() => sendCmd({ command: 'reset' })}
                aria-label={t('device.simulator.reset')}
              >
                {t('device.simulator.reset')}
              </Button>
            </span>
          </Tooltip>
        </Stack>

        {!canManage && (
          <Typography variant="caption" color="text.secondary">
            {t('device.simulator.permissionHint')}
          </Typography>
        )}

        {writeError && (
          <Alert severity="error" onClose={() => setWriteError(null)}>
            {writeError}
          </Alert>
        )}
      </Stack>
    </Box>
  )
}
