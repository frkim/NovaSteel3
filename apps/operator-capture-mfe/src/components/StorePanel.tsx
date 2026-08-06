import { useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
} from '@mui/material'
import NoteAddIcon from '@mui/icons-material/NoteAdd'
import SendIcon from '@mui/icons-material/SendOutlined'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import RestartAltIcon from '@mui/icons-material/RestartAlt'
import { useApp } from './appContext'
import type { CaptureClient } from '../api/captureClient'

interface StorePanelProps {
  client: CaptureClient
  sessionId: string
  title: string
  domain: string
  onDone: () => void
}

type Phase = 'idle' | 'creating' | 'draft' | 'submitting' | 'submitted' | 'error'

export function StorePanel({ client, sessionId, title, domain, onDone }: StorePanelProps) {
  const { t } = useApp()
  const [phase, setPhase] = useState<Phase>('idle')
  const [procedureId, setProcedureId] = useState('')
  const [status, setStatus] = useState('')
  const [message, setMessage] = useState('')

  const createDraft = async () => {
    setPhase('creating')
    setMessage('')
    try {
      const response = await client.createDraft(sessionId, { title, domain })
      setProcedureId(response.procedureId)
      setStatus(response.status)
      setPhase('draft')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : t('upload.err.generic'))
      setPhase('error')
    }
  }

  const submit = async () => {
    setPhase('submitting')
    setMessage('')
    try {
      const response = await client.submitForReview(procedureId)
      setStatus(response.status)
      setPhase('submitted')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : t('upload.err.generic'))
      setPhase('error')
    }
  }

  return (
    <Card>
      <CardContent>
        <Stack spacing={2.5}>
          <Typography variant="h2">{t('store.title')}</Typography>
          <Typography variant="body2" color="text.secondary">
            {t('store.hint')}
          </Typography>

          <Alert severity="info" variant="outlined" icon={false}>
            {t('store.humanGate')}
          </Alert>

          {procedureId && (
            <Box>
              <Typography variant="caption" color="text.secondary">
                {t('store.created', { id: '' })}
              </Typography>
              <Box sx={{ mt: 0.5 }}>
                <Chip label={procedureId} color="primary" variant="outlined" />
                {status && <Chip label={status} sx={{ ml: 1 }} variant="outlined" />}
              </Box>
            </Box>
          )}

          {message && (
            <Alert severity="error" role="alert">
              {message}
            </Alert>
          )}

          {phase === 'submitted' ? (
            <>
              <Alert severity="success" icon={<CheckCircleIcon />}>
                {t('store.submitted', { status })}
              </Alert>
              <Button variant="contained" size="large" fullWidth onClick={onDone} startIcon={<RestartAltIcon />}>
                {t('store.done')}
              </Button>
            </>
          ) : phase === 'draft' || phase === 'submitting' ? (
            <Button
              variant="contained"
              size="large"
              fullWidth
              onClick={() => void submit()}
              disabled={phase === 'submitting'}
              startIcon={<SendIcon />}
            >
              {phase === 'submitting' ? t('store.submitting') : t('store.submit')}
            </Button>
          ) : (
            <Button
              variant="contained"
              size="large"
              fullWidth
              onClick={() => void createDraft()}
              disabled={phase === 'creating'}
              startIcon={<NoteAddIcon />}
            >
              {phase === 'creating' ? t('store.creating') : t('store.create')}
            </Button>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}
