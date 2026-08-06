import { useCallback, useEffect, useRef, useState } from 'react'
import { Alert, Box, Button, Card, CardContent, LinearProgress, Stack, Typography } from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import CloseIcon from '@mui/icons-material/Close'
import ReplayIcon from '@mui/icons-material/Replay'
import { useApp } from './appContext'
import { DataClientError } from '../api/envelope'
import type { CaptureClient, UploadAudioResponse } from '../api/captureClient'
import { deletePending, savePending } from '../offline/recordingStore'
import type { CaptureLanguage } from '../types'

export interface UploadMeta {
  pendingId: string
  operatorRef: string
  title: string
  domain: string
  language: CaptureLanguage
  durationSeconds: number
}

interface UploadPanelProps {
  client: CaptureClient
  sessionId: string
  blob: Blob
  meta: UploadMeta
  onUploaded: (response: UploadAudioResponse) => void
  onCancel: () => void
}

type Phase = 'uploading' | 'error' | 'saved-offline'

function mapError(t: (k: string) => string, err: unknown): { message: string; offline: boolean } {
  if (err instanceof DataClientError) {
    if (err.status === 413) return { message: t('upload.err.tooLarge'), offline: false }
    if (err.status === 403) return { message: t('upload.err.consent'), offline: false }
    if (err.status === 404) return { message: t('upload.err.notFound'), offline: false }
    if (err.code === 'NETWORK_ERROR' || err.code === 'TIMEOUT') {
      return { message: t('upload.err.generic'), offline: true }
    }
    return { message: err.message || t('upload.err.generic'), offline: err.retryable }
  }
  return { message: t('upload.err.generic'), offline: true }
}

export function UploadPanel({ client, sessionId, blob, meta, onUploaded, onCancel }: UploadPanelProps) {
  const { t } = useApp()
  const [phase, setPhase] = useState<Phase>('uploading')
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState('')
  const abortRef = useRef<AbortController | null>(null)

  const runUpload = useCallback(async () => {
    setPhase('uploading')
    setProgress(0)
    setMessage('')
    const controller = new AbortController()
    abortRef.current = controller
    try {
      const response = await client.uploadAudio(
        sessionId,
        { blob, durationSeconds: meta.durationSeconds, language: meta.language },
        { signal: controller.signal, onProgress: setProgress },
      )
      // Success: the recording is safely on the backend, drop the local copy.
      await deletePending(meta.pendingId).catch(() => undefined)
      onUploaded(response)
    } catch (err) {
      if (err instanceof DataClientError && err.code === 'CANCELLED') {
        return
      }
      const mapped = mapError(t, err)
      setMessage(mapped.message)
      if (mapped.offline) {
        // Never lose a recording: persist it for a later retry.
        await savePending({
          id: meta.pendingId,
          createdAt: Date.now(),
          operatorRef: meta.operatorRef,
          title: meta.title,
          domain: meta.domain,
          language: meta.language,
          durationSeconds: meta.durationSeconds,
          sessionId,
          blob,
        }).catch(() => undefined)
        setPhase('saved-offline')
      } else {
        setPhase('error')
      }
    } finally {
      abortRef.current = null
    }
  }, [client, sessionId, blob, meta, onUploaded, t])

  useEffect(() => {
    void runUpload()
    return () => abortRef.current?.abort()
    // Run once for this recording; retry is explicit via button.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const percent = Math.round(progress * 100)

  return (
    <Card>
      <CardContent>
        <Stack spacing={2.5}>
          <Typography variant="h2">{t('upload.title')}</Typography>

          {phase === 'uploading' && (
            <>
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {t('upload.progress', { percent })}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={percent}
                  aria-label={t('upload.title')}
                  aria-valuenow={percent}
                />
              </Box>
              <Button variant="outlined" size="large" onClick={onCancel} startIcon={<CloseIcon />}>
                {t('upload.cancel')}
              </Button>
            </>
          )}

          {phase === 'error' && (
            <>
              <Alert severity="error" role="alert">
                {message}
              </Alert>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                <Button variant="outlined" size="large" fullWidth onClick={onCancel}>
                  {t('review.discard')}
                </Button>
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  onClick={() => void runUpload()}
                  startIcon={<ReplayIcon />}
                >
                  {t('upload.retry')}
                </Button>
              </Stack>
            </>
          )}

          {phase === 'saved-offline' && (
            <>
              <Alert severity="warning" role="alert">
                {t('upload.saved')}
              </Alert>
              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={() => void runUpload()}
                startIcon={<CloudUploadIcon />}
              >
                {t('upload.retry')}
              </Button>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}
