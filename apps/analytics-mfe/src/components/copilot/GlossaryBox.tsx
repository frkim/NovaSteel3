import { useEffect, useState } from 'react'
import {
  Box,
  CircularProgress,
  InputAdornment,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import MenuBookIcon from '@mui/icons-material/MenuBook'
import type { CopilotClient, GlossaryEntry } from '../../api/copilotClient'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import type { TranslateFn } from '../../i18n/messages'

interface GlossaryBoxProps {
  client: CopilotClient
  language: string
  section: string
  t: TranslateFn
}

/**
 * Instant-definition box. Typing a term *or* a phrase from inside a definition
 * resolves to the same ranked list the chat uses for grounding, so the
 * vocabulary a viewer sees here is exactly the vocabulary the assistant cites.
 * With no query it previews the terms that matter on the current screen.
 */
export function GlossaryBox({ client, language, section, t }: GlossaryBoxProps) {
  const [query, setQuery] = useState('')
  const [entries, setEntries] = useState<GlossaryEntry[]>([])
  const [loading, setLoading] = useState(false)
  const debounced = useDebouncedValue(query, 250)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    client
      .glossary(debounced, language, debounced.trim() ? undefined : section, 4)
      .then((results) => {
        if (!cancelled) {
          setEntries(results)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setEntries([])
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [client, debounced, language, section])

  return (
    <Box data-testid="copilot-glossary">
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1 }}>
        <MenuBookIcon fontSize="small" color="action" />
        <Typography variant="subtitle2">{t('copilot.glossary')}</Typography>
      </Stack>
      <TextField
        fullWidth
        size="small"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder={t('copilot.glossary.placeholder')}
        helperText={t('copilot.glossary.hint')}
        data-testid="copilot-glossary-input"
        slotProps={{
          htmlInput: { 'aria-label': t('copilot.glossary.placeholder') },
          input: {
            endAdornment: loading ? (
              <InputAdornment position="end">
                <CircularProgress size={14} />
              </InputAdornment>
            ) : undefined,
          },
        }}
      />
      <Box role="status" aria-live="polite" sx={{ mt: 1 }}>
        {entries.length === 0 && !loading && (
          <Typography variant="caption" color="text.secondary">
            {t('copilot.glossary.empty')}
          </Typography>
        )}
        <Stack spacing={1}>
          {entries.map((entry) => (
            <Box key={entry.termId} data-testid="copilot-glossary-entry">
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {entry.term}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {entry.definition}
              </Typography>
            </Box>
          ))}
        </Stack>
      </Box>
    </Box>
  )
}
