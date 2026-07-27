import { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  InputAdornment,
  Link,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import MenuBookIcon from '@mui/icons-material/MenuBook'
import TravelExploreIcon from '@mui/icons-material/TravelExplore'
import type { CopilotClient, GlossaryEntry, GlossaryOnlineResultItem } from '../../api/copilotClient'
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
 *
 * When no local match is found, the user can trigger an online lookup that
 * searches the same corpus the chat uses for online search.
 */
export function GlossaryBox({ client, language, section, t }: GlossaryBoxProps) {
  const [query, setQuery] = useState('')
  const [entries, setEntries] = useState<GlossaryEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [onlineResults, setOnlineResults] = useState<GlossaryOnlineResultItem[]>([])
  const [onlineLoading, setOnlineLoading] = useState(false)
  const [onlineCorpusLabel, setOnlineCorpusLabel] = useState('')
  const debounced = useDebouncedValue(query, 250)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setOnlineResults([])
    setOnlineCorpusLabel('')
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

  const searchOnline = () => {
    if (!debounced.trim()) {
      return
    }
    setOnlineLoading(true)
    client
      .glossaryOnline(debounced, language)
      .then((result) => {
        setOnlineResults(result.results)
        setOnlineCorpusLabel(result.corpusLabel)
      })
      .catch(() => {
        setOnlineResults([])
      })
      .finally(() => {
        setOnlineLoading(false)
      })
  }

  const showNoMatch = entries.length === 0 && !loading && debounced.trim().length > 0

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
        {entries.length === 0 && !loading && !debounced.trim() && (
          <Typography variant="caption" color="text.secondary">
            {t('copilot.glossary.empty')}
          </Typography>
        )}
        {showNoMatch && (
          <Stack spacing={0.5}>
            <Typography variant="caption" color="text.secondary">
              {t('copilot.glossary.noLocalMatch')}
            </Typography>
            <Button
              size="small"
              variant="text"
              startIcon={onlineLoading ? <CircularProgress size={12} /> : <TravelExploreIcon />}
              disabled={onlineLoading}
              onClick={searchOnline}
              data-testid="copilot-glossary-search-online"
            >
              {t('copilot.glossary.searchOnline')}
            </Button>
          </Stack>
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
        {onlineResults.length > 0 && (
          <Box sx={{ mt: 1.5 }} data-testid="copilot-glossary-online">
            <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center', mb: 0.5 }}>
              <TravelExploreIcon fontSize="small" color="action" />
              <Typography variant="caption" sx={{ fontWeight: 600 }}>
                {t('copilot.glossary.onlineResults')}
              </Typography>
              {onlineCorpusLabel && (
                <Chip size="small" variant="outlined" label={onlineCorpusLabel} sx={{ height: 18 }} />
              )}
            </Stack>
            <Stack spacing={1}>
              {onlineResults.map((result) => (
                <Box key={result.sourceId}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {result.url ? (
                      <Link href={result.url} target="_blank" rel="noopener noreferrer">
                        {result.title}
                      </Link>
                    ) : (
                      result.title
                    )}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {result.snippet}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Box>
        )}
      </Box>
    </Box>
  )
}
