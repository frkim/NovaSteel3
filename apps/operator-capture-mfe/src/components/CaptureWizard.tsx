import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Alert, Box, LinearProgress, Stack, Typography } from '@mui/material'
import { useApp } from './appContext'
import { ConsentGate, type ConsentValues } from './ConsentGate'
import { RecorderPanel } from './RecorderPanel'
import { ReviewPanel } from './ReviewPanel'
import { UploadPanel, type UploadMeta } from './UploadPanel'
import { TranscriptPanel } from './TranscriptPanel'
import { StorePanel } from './StorePanel'
import { useRecorder } from '../recorder/useRecorder'
import { CaptureClient } from '../api/captureClient'
import { DOMAINS } from '../types'

type Step = 'consent' | 'record' | 'review' | 'upload' | 'transcript' | 'store'

const STEP_ORDER: Step[] = ['consent', 'record', 'review', 'upload', 'transcript', 'store']

const STEP_LABEL_KEY: Record<Step, string> = {
  consent: 'step.consent',
  record: 'step.record',
  review: 'step.review',
  upload: 'step.upload',
  transcript: 'step.transcript',
  store: 'step.store',
}

interface CaptureWizardProps {
  /** Injectable for tests; defaults to a client resolved from runtime config. */
  client?: CaptureClient
}

function newId(prefix: string): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return `${prefix}-${crypto.randomUUID()}`
  }
  return `${prefix}-${Date.now().toString(36)}`
}

export function CaptureWizard({ client: injected }: CaptureWizardProps) {
  const { t, language } = useApp()
  const client = useMemo(() => injected ?? new CaptureClient({ locale: language }), [injected, language])
  const recorder = useRecorder()

  const [step, setStep] = useState<Step>('consent')
  const [consent, setConsent] = useState<ConsentValues>({
    operatorRef: '',
    title: '',
    domain: DOMAINS[0],
    language,
    retentionDays: 365,
  })
  const [sessionId, setSessionId] = useState('')
  const [pendingId, setPendingId] = useState('')
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')
  const stepRef = useRef(step)
  stepRef.current = step

  // Advance to review once the recorder produces a finished blob.
  useEffect(() => {
    if (recorder.state === 'stopped' && recorder.result && stepRef.current === 'record') {
      setStep('review')
    }
  }, [recorder.state, recorder.result])

  const handleConsent = useCallback(
    async (values: ConsentValues) => {
      setConsent(values)
      setStarting(true)
      setError('')
      try {
        const response = await client.createInterview({
          operatorRef: values.operatorRef,
          language: values.language,
          consent: { granted: true, scope: 'knowledge-capture', retentionDays: values.retentionDays },
        })
        setSessionId(response.sessionId)
        recorder.reset()
        setStep('record')
      } catch (err) {
        setError(err instanceof Error ? err.message : t('upload.err.generic'))
      } finally {
        setStarting(false)
      }
    },
    [client, recorder, t],
  )

  const handleDiscard = useCallback(() => {
    recorder.reset()
    setStep('record')
  }, [recorder])

  const handleConfirmUpload = useCallback(() => {
    setPendingId(newId('rec'))
    setStep('upload')
  }, [])

  const handleReset = useCallback(() => {
    recorder.reset()
    setSessionId('')
    setPendingId('')
    setError('')
    setConsent((prev) => ({ ...prev, operatorRef: '', title: '' }))
    setStep('consent')
  }, [recorder])

  const activeIndex = STEP_ORDER.indexOf(step)

  const uploadMeta: UploadMeta = {
    pendingId,
    operatorRef: consent.operatorRef,
    title: consent.title,
    domain: consent.domain,
    language: consent.language,
    durationSeconds: recorder.result?.durationSeconds ?? 0,
  }

  return (
    <Stack spacing={2}>
      <Box>
        <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'baseline' }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
            {t(STEP_LABEL_KEY[step])}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {activeIndex + 1} / {STEP_ORDER.length}
          </Typography>
        </Stack>
        <LinearProgress
          variant="determinate"
          value={((activeIndex + 1) / STEP_ORDER.length) * 100}
          sx={{ mt: 0.5, borderRadius: 1 }}
          aria-label={t(STEP_LABEL_KEY[step])}
        />
      </Box>

      {error && step === 'consent' && (
        <Alert severity="error" role="alert" onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {step === 'consent' && (
        <>
          <ConsentGate initial={consent} onSubmit={handleConsent} />
          {starting && <LinearProgress aria-label={t('consent.start')} />}
        </>
      )}

      {step === 'record' && <RecorderPanel controller={recorder} />}

      {step === 'review' && recorder.result && (
        <ReviewPanel result={recorder.result} onDiscard={handleDiscard} onConfirm={handleConfirmUpload} />
      )}

      {step === 'upload' && recorder.result && (
        <UploadPanel
          client={client}
          sessionId={sessionId}
          blob={recorder.result.blob}
          meta={uploadMeta}
          onUploaded={() => setStep('transcript')}
          onCancel={() => setStep('review')}
        />
      )}

      {step === 'transcript' && (
        <TranscriptPanel client={client} sessionId={sessionId} onContinue={() => setStep('store')} />
      )}

      {step === 'store' && (
        <StorePanel
          client={client}
          sessionId={sessionId}
          title={consent.title}
          domain={consent.domain}
          onDone={handleReset}
        />
      )}
    </Stack>
  )
}
