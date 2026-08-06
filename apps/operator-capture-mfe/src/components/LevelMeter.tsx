import { Box } from '@mui/material'

interface LevelMeterProps {
  /** Live level 0..1. */
  level: number
  active: boolean
  label: string
}

const BAR_COUNT = 28

/**
 * Lightweight animated bar meter that reflects the live microphone input so an
 * operator can see the mic is picking up their voice. Decorative only —
 * announced state lives on the recorder controls, so this is aria-hidden.
 */
export function LevelMeter({ level, active, label }: LevelMeterProps) {
  const bars = Array.from({ length: BAR_COUNT }, (_, i) => {
    const threshold = i / BAR_COUNT
    const lit = active && level >= threshold
    const heat = i / BAR_COUNT
    const color = heat > 0.85 ? 'error.main' : heat > 0.6 ? 'warning.main' : 'success.main'
    return (
      <Box
        key={i}
        sx={{
          flex: 1,
          height: `${20 + threshold * 80}%`,
          borderRadius: 0.5,
          bgcolor: lit ? color : 'divider',
          opacity: lit ? 1 : 0.35,
          transition: 'opacity 80ms linear, background-color 80ms linear',
        }}
      />
    )
  })

  return (
    <Box
      role="img"
      aria-label={label}
      sx={{
        display: 'flex',
        alignItems: 'flex-end',
        gap: 0.5,
        height: 72,
        px: 1,
        py: 1,
        bgcolor: 'background.default',
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
      }}
    >
      {bars}
    </Box>
  )
}
