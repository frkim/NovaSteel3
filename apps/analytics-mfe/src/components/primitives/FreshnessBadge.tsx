import { Box, Stack, Tooltip, Typography } from '@mui/material'
import type { DataSource } from '../../api/domain'
import { useAnalytics } from '../../context/analytics'
import { useTokens } from '../../hooks/useTokens'
import { useNow } from '../../hooks/usePolling'
import { formatRelativeTime, secondsSince } from '../../utils/format'

export interface FreshnessBadgeProps {
  asOf: string | null
  source?: DataSource | null
  staleThresholdSeconds?: number
}

/** Freshness + data-source indicator; turns amber when data is stale (STATE-STALE). */
export function FreshnessBadge({ asOf, source, staleThresholdSeconds = 60 }: FreshnessBadgeProps) {
  const { locale, t } = useAnalytics()
  const tokens = useTokens()
  const now = useNow(10000)
  const ageSeconds = secondsSince(asOf, now)
  const isFixture = source === 'fixture'
  const isStale = ageSeconds > staleThresholdSeconds
  const color = isFixture ? tokens.status.stale : isStale ? tokens.status.warning : tokens.status.success
  const glyph = isFixture ? '◍' : isStale ? '▲' : '●'
  const sourceLabel = isFixture ? t('source.fixture') : t('source.bff')

  return (
    <Tooltip title={sourceLabel}>
      <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center' }} aria-live="polite">
        <Box component="span" aria-hidden sx={{ color, fontSize: '0.7rem' }}>
          {glyph}
        </Box>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          {asOf ? formatRelativeTime(asOf, locale, now) : '—'}
        </Typography>
      </Stack>
    </Tooltip>
  )
}
