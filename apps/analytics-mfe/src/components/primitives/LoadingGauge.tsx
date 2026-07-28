import { useEffect, useState } from 'react'
import { Box, CircularProgress, Stack, Typography } from '@mui/material'
import CloudSyncIcon from '@mui/icons-material/CloudSync'
import { useAnalytics } from '../../context/analytics'

export interface LoadingGaugeProps {
  /** Headline; defaults to the shared "Loading in progress…" message. */
  label?: string
  /** Optional sentence explaining what is being fetched. */
  caption?: string
  size?: number
}

/**
 * Animated gauge for first loads that are slow enough to need reassurance —
 * chiefly cloud mode, where the Device Operations screens wait on the BFF.
 * The sweep is indeterminate on purpose: a fake percentage would be a claim we
 * cannot make. The elapsed counter is the only real progress signal there is.
 */
export function LoadingGauge({ label, caption, size = 104 }: LoadingGaugeProps) {
  const { t } = useAnalytics()
  const [elapsedSeconds, setElapsedSeconds] = useState(0)

  useEffect(() => {
    const timer = window.setInterval(() => setElapsedSeconds((value) => value + 1), 1000)
    return () => window.clearInterval(timer)
  }, [])

  return (
    <Stack
      role="status"
      aria-busy="true"
      aria-live="polite"
      spacing={1.25}
      sx={{ alignItems: 'center', justifyContent: 'center', py: 5, px: 2 }}
    >
      <Box sx={{ position: 'relative', display: 'inline-flex' }}>
        <CircularProgress
          variant="determinate"
          value={100}
          size={size}
          thickness={4}
          aria-hidden
          sx={{ color: (theme) => (theme.palette.mode === 'dark' ? theme.palette.grey[800] : theme.palette.grey[200]) }}
        />
        <CircularProgress
          variant="indeterminate"
          disableShrink
          size={size}
          thickness={4}
          aria-hidden
          sx={{
            position: 'absolute',
            left: 0,
            color: 'primary.main',
            animationDuration: '1100ms',
            '& .MuiCircularProgress-circle': { strokeLinecap: 'round' },
          }}
        />
        <Stack
          sx={{ position: 'absolute', inset: 0, alignItems: 'center', justifyContent: 'center' }}
          spacing={0.25}
        >
          <CloudSyncIcon fontSize="small" color="primary" aria-hidden />
          <Typography variant="caption" color="text.secondary" sx={{ fontVariantNumeric: 'tabular-nums' }}>
            {elapsedSeconds}s
          </Typography>
        </Stack>
      </Box>
      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
        {label ?? t('state.loading.progress')}
      </Typography>
      {caption && (
        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 420, textAlign: 'center' }}>
          {caption}
        </Typography>
      )}
    </Stack>
  )
}
