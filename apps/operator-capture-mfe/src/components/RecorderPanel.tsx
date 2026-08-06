import { Alert, Box, Button, Chip, Stack, Typography } from '@mui/material'
import MicIcon from '@mui/icons-material/Mic'
import PauseIcon from '@mui/icons-material/Pause'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import StopIcon from '@mui/icons-material/Stop'
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord'
import { useApp } from './appContext'
import { LevelMeter } from './LevelMeter'
import type { RecorderController } from '../recorder/useRecorder'

interface RecorderPanelProps {
  controller: RecorderController
}

function formatElapsed(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

export function RecorderPanel({ controller }: RecorderPanelProps) {
  const { t } = useApp()
  const { state, elapsedMs, level, error } = controller

  if (state === 'unsupported') {
    return (
      <Alert severity="error" role="alert">
        {t('record.err.unsupported')}
      </Alert>
    )
  }

  if (state === 'error' && error) {
    const key = `record.err.${error.kind}` as const
    return (
      <Stack spacing={2}>
        <Alert severity="error" role="alert">
          {t(key)}
        </Alert>
        <Button variant="contained" size="large" onClick={() => void controller.start()} startIcon={<MicIcon />}>
          {t('record.retry')}
        </Button>
      </Stack>
    )
  }

  const isRecording = state === 'recording'
  const isPaused = state === 'paused'
  const isActive = isRecording || isPaused

  const statusLabel = isRecording ? t('record.recording') : isPaused ? t('record.paused') : ''

  return (
    <Stack spacing={2.5}>
      <Typography variant="h2">{t('record.title')}</Typography>
      <Typography variant="body2" color="text.secondary">
        {t('record.hint')}
      </Typography>

      {/* Screen readers get a live announcement of the recording state. */}
      <Box aria-live="assertive" sx={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)' }}>
        {statusLabel}
      </Box>

      <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', justifyContent: 'center' }}>
        {isActive && (
          <Chip
            icon={<FiberManualRecordIcon sx={{ color: isRecording ? 'error.main' : 'warning.main' }} />}
            label={statusLabel}
            variant="outlined"
            sx={{ fontWeight: 700 }}
          />
        )}
        <Typography
          variant="h1"
          component="p"
          aria-label={`${t('record.elapsed')} ${formatElapsed(elapsedMs)}`}
          sx={{ fontVariantNumeric: 'tabular-nums', letterSpacing: 1 }}
        >
          {formatElapsed(elapsedMs)}
        </Typography>
      </Stack>

      <LevelMeter level={level} active={isRecording} label={t('record.level')} />

      {isPaused && (
        <Alert severity="info" variant="outlined">
          {t('record.autopaused')}
        </Alert>
      )}

      {!isActive ? (
        <Button
          variant="contained"
          size="large"
          fullWidth
          onClick={() => void controller.start()}
          startIcon={<MicIcon />}
          sx={{ py: 2, fontSize: '1.1rem' }}
        >
          {t('record.start')}
        </Button>
      ) : (
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
          {isRecording ? (
            <Button
              variant="outlined"
              size="large"
              fullWidth
              onClick={controller.pause}
              startIcon={<PauseIcon />}
              aria-label={t('record.pause')}
            >
              {t('record.pause')}
            </Button>
          ) : (
            <Button
              variant="outlined"
              size="large"
              fullWidth
              onClick={controller.resume}
              startIcon={<PlayArrowIcon />}
              aria-label={t('record.resume')}
            >
              {t('record.resume')}
            </Button>
          )}
          <Button
            variant="contained"
            color="error"
            size="large"
            fullWidth
            onClick={controller.stop}
            startIcon={<StopIcon />}
            aria-label={t('record.stop')}
            sx={{ py: 2 }}
          >
            {t('record.stop')}
          </Button>
        </Stack>
      )}
    </Stack>
  )
}
