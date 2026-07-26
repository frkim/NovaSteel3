import { Box, Stack, Typography } from '@mui/material'
import type { ConfidenceBand } from '../../api/envelope'
import { useAnalytics } from '../../context/analytics'
import { useTokens } from '../../hooks/useTokens'
import { formatNumber } from '../../utils/format'

export interface ConfidenceMeterProps {
  band: ConfidenceBand
  unit?: string
  label?: string
}

/** Renders a p10–p50–p90 uncertainty band as a horizontal meter (§12.2, AC-G11). */
export function ConfidenceMeter({ band, unit = '', label }: ConfidenceMeterProps) {
  const { locale, t } = useAnalytics()
  const tokens = useTokens()
  const span = Math.max(1e-6, band.p90 - band.p10)
  const p50Pct = ((band.p50 - band.p10) / span) * 100

  return (
    <Box>
      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
        {label ?? t('kpi.confidence')}
      </Typography>
      <Box
        role="img"
        aria-label={`P10 ${band.p10}, P50 ${band.p50}, P90 ${band.p90} ${unit}`}
        sx={{ position: 'relative', height: 10, borderRadius: 999, bgcolor: 'action.hover', mt: 0.5 }}
      >
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            borderRadius: 999,
            background: `linear-gradient(90deg, ${tokens.status.warning}55, ${tokens.status.info}55)`,
          }}
        />
        <Box
          aria-hidden
          sx={{
            position: 'absolute',
            top: -2,
            bottom: -2,
            left: `${Math.max(0, Math.min(100, p50Pct))}%`,
            width: '3px',
            bgcolor: tokens.status.info,
            borderRadius: 2,
          }}
        />
      </Box>
      <Stack direction="row" sx={{ justifyContent: 'space-between', mt: 0.25 }}>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          P10 {formatNumber(band.p10, locale)}
        </Typography>
        <Typography variant="caption" sx={{ fontWeight: 700 }}>
          P50 {formatNumber(band.p50, locale)} {unit}
        </Typography>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          P90 {formatNumber(band.p90, locale)}
        </Typography>
      </Stack>
    </Box>
  )
}
