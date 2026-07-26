import { Box, Chip } from '@mui/material'
import { useTokens } from '../../hooks/useTokens'

export interface SeverityPillProps {
  severity: string
  label?: string
  size?: 'small' | 'medium'
}

/** Status pill that always pairs color with an icon glyph + text (§7.1, §17 not-color-alone). */
export function SeverityPill({ severity, label, size = 'small' }: SeverityPillProps) {
  const tokens = useTokens()
  const meta = tokens.severity(severity)
  return (
    <Chip
      size={size}
      label={
        <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
          <Box component="span" aria-hidden sx={{ fontSize: '0.9em' }}>
            {meta.glyph}
          </Box>
          {label ?? meta.label}
        </Box>
      }
      sx={{
        bgcolor: 'transparent',
        border: `1px solid ${meta.color}`,
        color: meta.color,
        fontWeight: 700,
      }}
    />
  )
}
