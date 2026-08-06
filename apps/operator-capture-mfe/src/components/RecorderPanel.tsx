import { useCallback, useRef, useState } from 'react'
import { Alert, Box, Button, Chip, Divider, LinearProgress, Stack, Typography } from '@mui/material'
import MicIcon from '@mui/icons-material/Mic'
import PauseIcon from '@mui/icons-material/Pause'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import StopIcon from '@mui/icons-material/Stop'
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord'
import AudioFileIcon from '@mui/icons-material/AudioFile'
import ScienceIcon from '@mui/icons-material/Science'
import { useApp } from './appContext'
import { LevelMeter } from './LevelMeter'
import { AUDIO_FILE_ACCEPT } from '../audio/audioFile'
import { loadSampleAudioFile } from '../audio/sampleAudio'
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
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [sampleError, setSampleError] = useState('')
  const [loadingSample, setLoadingSample] = useState(false)

  const handleFileChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      // Clear the input so picking the same file again still fires a change event.
      event.target.value = ''
      if (file) {
        setSampleError('')
        void controller.importFile(file)
      }
    },
    [controller],
  )

  const handleSample = useCallback(async () => {
    setSampleError('')
    setLoadingSample(true)
    try {
      const file = await loadSampleAudioFile()
      await controller.importFile(file)
    } catch {
      setSampleError(t('record.err.sample'))
    } finally {
      setLoadingSample(false)
    }
  }, [controller, t])

  const isRecording = state === 'recording'
  const isPaused = state === 'paused'
  const isActive = isRecording || isPaused || state === 'requesting'
  const isImporting = state === 'importing' || loadingSample

  const statusLabel = isRecording ? t('record.recording') : isPaused ? t('record.paused') : ''

  /**
   * Importing is offered in every non-recording state, including `unsupported`
   * and `error`: a denied microphone or an old browser is exactly when an
   * operator needs the fallback most.
   */
  const importSection = (
    <Stack spacing={1.5}>
      <Divider>
        <Typography variant="caption" color="text.secondary">
          {t('record.import.or')}
        </Typography>
      </Divider>

      <Typography variant="body2" color="text.secondary">
        {t('record.import.hint')}
      </Typography>

      <Box
        component="input"
        type="file"
        accept={AUDIO_FILE_ACCEPT}
        ref={fileInputRef}
        onChange={handleFileChange}
        aria-label={t('record.import')}
        sx={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)' }}
      />

      <Button
        variant="outlined"
        size="large"
        fullWidth
        disabled={isImporting}
        onClick={() => fileInputRef.current?.click()}
        startIcon={<AudioFileIcon />}
        sx={{ py: 1.5 }}
      >
        {t('record.import')}
      </Button>

      <Button
        variant="text"
        size="small"
        disabled={isImporting}
        onClick={() => void handleSample()}
        startIcon={<ScienceIcon />}
      >
        {t('record.sample')}
      </Button>

      {sampleError && (
        <Alert severity="warning" role="alert" onClose={() => setSampleError('')}>
          {sampleError}
        </Alert>
      )}

      {isImporting && <LinearProgress aria-label={t('record.import.busy')} />}
    </Stack>
  )

  if (state === 'unsupported') {
    return (
      <Stack spacing={2.5}>
        <Typography variant="h2">{t('record.title')}</Typography>
        <Alert severity="error" role="alert">
          {t('record.err.unsupported')}
        </Alert>
        {importSection}
      </Stack>
    )
  }

  if (state === 'error' && error) {
    const key = `record.err.${error.kind}` as const
    return (
      <Stack spacing={2.5}>
        <Typography variant="h2">{t('record.title')}</Typography>
        <Alert severity="error" role="alert">
          {t(key)}
        </Alert>
        {controller.isSupported && (
          <Button variant="contained" size="large" onClick={() => void controller.start()} startIcon={<MicIcon />}>
            {t('record.retry')}
          </Button>
        )}
        {importSection}
      </Stack>
    )
  }

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
        {(isRecording || isPaused) && (
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
        <>
          <Button
            variant="contained"
            size="large"
            fullWidth
            disabled={isImporting}
            onClick={() => void controller.start()}
            startIcon={<MicIcon />}
            sx={{ py: 2, fontSize: '1.1rem' }}
          >
            {t('record.start')}
          </Button>
          {importSection}
        </>
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
              disabled={state === 'requesting'}
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
