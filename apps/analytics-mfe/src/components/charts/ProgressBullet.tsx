import { Box, Stack, Typography } from '@mui/material'

export interface ProgressItem {
  label: string
  value: number
  target?: number
  color: string
}

export interface ProgressBulletProps {
  items: ProgressItem[]
  max?: number
  valueSuffix?: string
}

/** Accessible progress/bullet bars for completion tracking (C-PROGRESS, §14.1). */
export function ProgressBullet({ items, max = 100, valueSuffix = '%' }: ProgressBulletProps) {
  return (
    <Stack spacing={1.5} component="ul" sx={{ listStyle: 'none', p: 0, m: 0 }}>
      {items.map((item) => {
        const pct = Math.max(0, Math.min(100, (item.value / max) * 100))
        const targetPct = item.target !== undefined ? Math.max(0, Math.min(100, (item.target / max) * 100)) : null
        return (
          <Box component="li" key={item.label}>
            <Stack direction="row" sx={{ justifyContent: 'space-between', mb: 0.25 }}>
              <Typography variant="body2">{item.label}</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700 }}>
                {item.value}
                {valueSuffix}
              </Typography>
            </Stack>
            <Box
              role="meter"
              aria-valuenow={item.value}
              aria-valuemin={0}
              aria-valuemax={max}
              aria-label={`${item.label} ${item.value}${valueSuffix}`}
              sx={{
                position: 'relative',
                height: 12,
                borderRadius: 999,
                bgcolor: 'action.hover',
                overflow: 'hidden',
              }}
            >
              <Box sx={{ position: 'absolute', inset: 0, width: `${pct}%`, bgcolor: item.color, borderRadius: 999 }} />
              {targetPct !== null && (
                <Box
                  aria-hidden
                  sx={{
                    position: 'absolute',
                    top: -2,
                    bottom: -2,
                    left: `${targetPct}%`,
                    width: '2px',
                    bgcolor: 'text.primary',
                  }}
                />
              )}
            </Box>
          </Box>
        )
      })}
    </Stack>
  )
}
