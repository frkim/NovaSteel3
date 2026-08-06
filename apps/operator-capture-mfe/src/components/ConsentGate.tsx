import { useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  FormControlLabel,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import MicIcon from '@mui/icons-material/Mic'
import { useApp } from './appContext'
import { DOMAINS, type CaptureLanguage } from '../types'
import { LANGUAGE_LABELS, SUPPORTED_LANGUAGES } from '../i18n/messages'

export interface ConsentValues {
  operatorRef: string
  title: string
  domain: string
  language: CaptureLanguage
  retentionDays: number
}

interface ConsentGateProps {
  initial: ConsentValues
  onSubmit: (values: ConsentValues) => void
}

/**
 * GDPR consent gate. Mirrors the wording/semantics of the Knowledge Hub
 * `CreateEntryDialog`: explicit Art. 6(1)(a) consent + retention days under
 * Art. 5(1)(e). The "continue" action is hard-disabled until consent is
 * granted, so recording controls are unreachable without consent.
 */
export function ConsentGate({ initial, onSubmit }: ConsentGateProps) {
  const { t } = useApp()
  const [operatorRef, setOperatorRef] = useState(initial.operatorRef)
  const [title, setTitle] = useState(initial.title)
  const [domain, setDomain] = useState(initial.domain)
  const [language, setLanguage] = useState<CaptureLanguage>(initial.language)
  const [retentionDays, setRetentionDays] = useState(initial.retentionDays)
  const [consentGranted, setConsentGranted] = useState(false)

  const canContinue = Boolean(operatorRef.trim() && title.trim() && consentGranted)

  const handleSubmit = () => {
    if (!canContinue) {
      return
    }
    onSubmit({ operatorRef: operatorRef.trim(), title: title.trim(), domain, language, retentionDays })
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h2" gutterBottom>
          {t('consent.title')}
        </Typography>
        <Stack spacing={2.5} component="form" onSubmit={(e) => { e.preventDefault(); handleSubmit() }}>
          <TextField
            label={t('consent.procedureTitle')}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            fullWidth
            autoComplete="off"
          />
          <TextField
            label={t('consent.operator')}
            value={operatorRef}
            onChange={(e) => setOperatorRef(e.target.value)}
            required
            fullWidth
            autoComplete="off"
            helperText={t('consent.operator.help')}
          />
          <TextField
            label={t('consent.domain')}
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            select
            fullWidth
          >
            {DOMAINS.map((d) => (
              <MenuItem key={d} value={d}>
                {d}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label={t('consent.language')}
            value={language}
            onChange={(e) => setLanguage(e.target.value as CaptureLanguage)}
            select
            fullWidth
          >
            {SUPPORTED_LANGUAGES.map((code) => (
              <MenuItem key={code} value={code}>
                {LANGUAGE_LABELS[code]}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label={t('consent.retention')}
            type="number"
            value={retentionDays}
            onChange={(e) => setRetentionDays(Number(e.target.value) || 365)}
            fullWidth
            helperText={t('consent.retention.help')}
            slotProps={{ htmlInput: { min: 1, max: 3650 } }}
          />

          <Alert severity="info" variant="outlined">
            <Typography variant="body2" sx={{ fontWeight: 700, mb: 0.5 }}>
              {t('consent.notice.title')}
            </Typography>
            <Typography variant="caption" sx={{ display: 'block' }}>
              {t('consent.notice.body')}
            </Typography>
          </Alert>

          <FormControlLabel
            sx={{ alignItems: 'flex-start' }}
            control={
              <Checkbox
                checked={consentGranted}
                onChange={(e) => setConsentGranted(e.target.checked)}
                slotProps={{ input: { 'aria-label': t('consent.checkbox') } }}
              />
            }
            label={<Typography variant="body2">{t('consent.checkbox')}</Typography>}
          />
          {!consentGranted && (
            <Alert severity="warning" variant="outlined">
              {t('consent.required')}
            </Alert>
          )}

          <Box>
            <Button
              type="submit"
              variant="contained"
              size="large"
              fullWidth
              disabled={!canContinue}
              startIcon={<MicIcon />}
            >
              {t('consent.start')}
            </Button>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  )
}
