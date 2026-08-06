import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import ReplayIcon from '@mui/icons-material/Replay'
import { useApp } from './appContext'
import { DataClientError } from '../api/envelope'
import type { CaptureClient, TranscriptResponse } from '../api/captureClient'

interface TranscriptPanelProps {
  client: CaptureClient
  sessionId: string
  onContinue: (transcript: TranscriptResponse) => void
}

type Phase = 'processing' | 'ready' | 'error'

export function TranscriptPanel({ client, sessionId, onContinue }: TranscriptPanelProps) {
  const { t } = useApp()
  const [phase, setPhase] = useState<Phase>('processing')
  const [transcript, setTranscript] = useState<TranscriptResponse | null>(null)
  const [message, setMessage] = useState('')
  const abortRef = useRef<AbortController | null>(null)

  const run = useCallback(async () => {
    setPhase('processing')
    setMessage('')
    const controller = new AbortController()
    abortRef.current = controller
    try {
      const result = await client.pollTranscript(sessionId, { signal: controller.signal })
      setTranscript(result)
      setPhase('ready')
    } catch (err) {
      if (err instanceof DataClientError && err.code === 'CANCELLED') {
        return
      }
      setMessage(err instanceof Error ? err.message : t('upload.err.generic'))
      setPhase('error')
    } finally {
      abortRef.current = null
    }
  }, [client, sessionId, t])

  useEffect(() => {
    void run()
    return () => abortRef.current?.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <Card>
      <CardContent>
        <Stack spacing={2.5}>
          <Typography variant="h2">{t('transcript.title')}</Typography>

          {phase === 'processing' && (
            <Stack spacing={2} sx={{ py: 3, alignItems: 'center' }}>
              <CircularProgress aria-label={t('transcript.processing')} />
              <Typography variant="body2" color="text.secondary" align="center">
                {t('transcript.processing')}
              </Typography>
              <Box sx={{ width: '100%' }} aria-hidden>
                <LinearProgress />
              </Box>
            </Stack>
          )}

          {phase === 'error' && (
            <>
              <Alert severity="error" role="alert">
                {message}
              </Alert>
              <Button variant="contained" size="large" onClick={() => void run()} startIcon={<ReplayIcon />}>
                {t('transcript.retry')}
              </Button>
            </>
          )}

          {phase === 'ready' && transcript && (
            <>
              {transcript.classification && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    {t('transcript.classification')}
                  </Typography>
                  <Box>
                    <Chip label={transcript.classification} color="secondary" variant="outlined" sx={{ mt: 0.5 }} />
                  </Box>
                </Box>
              )}

              {transcript.segments && transcript.segments.length > 0 ? (
                <Stack spacing={1.5} divider={<Divider flexItem />}>
                  {transcript.segments.map((seg) => (
                    <Box key={seg.segmentId}>
                      <Stack direction="row" spacing={1} sx={{ mb: 0.5, alignItems: 'center', flexWrap: 'wrap' }}>
                        <Chip size="small" label={seg.speaker} variant="outlined" />
                        <Typography variant="caption" color="text.secondary">
                          {t('transcript.confidence')}: {Math.round(seg.confidence * 100)}%
                        </Typography>
                      </Stack>
                      <Typography variant="body2">{seg.text}</Typography>
                    </Box>
                  ))}
                </Stack>
              ) : (
                <Alert severity="info" variant="outlined">
                  {t('transcript.empty')}
                </Alert>
              )}

              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={() => onContinue(transcript)}
                endIcon={<ArrowForwardIcon />}
              >
                {t('transcript.continue')}
              </Button>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}
