import { useId, useState, type MouseEvent } from 'react'
import { Box, Divider, IconButton, Popover, Stack, Typography } from '@mui/material'
import HelpOutlineIcon from '@mui/icons-material/HelpOutlineOutlined'
import type { Driver } from '../../api/envelope'
import { useAnalytics } from '../../context/analytics'
import { formatDateTime } from '../../utils/format'

export interface WhyPopoverProps {
  modelVersion: string
  scoredAt: string | null
  drivers: Driver[]
  confidenceText?: string
}

/** EU AI Act "Why?" affordance exposing model version, freshness, and drivers (AC-G11). */
export function WhyPopover({ modelVersion, scoredAt, drivers, confidenceText }: WhyPopoverProps) {
  const { locale, t } = useAnalytics()
  const [anchor, setAnchor] = useState<HTMLElement | null>(null)
  const id = useId()
  const open = Boolean(anchor)

  return (
    <>
      <IconButton
        aria-label={t('kpi.why')}
        aria-describedby={open ? id : undefined}
        size="small"
        onClick={(event: MouseEvent<HTMLButtonElement>) => setAnchor(event.currentTarget)}
      >
        <HelpOutlineIcon fontSize="small" />
      </IconButton>
      <Popover
        id={id}
        open={open}
        anchorEl={anchor}
        onClose={() => setAnchor(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Box sx={{ p: 2, maxWidth: 320 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
            {t('kpi.why')}
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
            {modelVersion} · {t('kpi.asOf', { time: formatDateTime(scoredAt, locale) })}
          </Typography>
          {confidenceText && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              {confidenceText}
            </Typography>
          )}
          <Divider sx={{ my: 1 }} />
          <Typography variant="caption" sx={{ fontWeight: 700 }}>
            Top drivers
          </Typography>
          <Stack spacing={0.75} sx={{ mt: 0.5 }}>
            {drivers.map((driver) => (
              <Box key={driver.name}>
                <Stack direction="row" sx={{ justifyContent: 'space-between' }}>
                  <Typography variant="caption">{driver.name}</Typography>
                  <Typography variant="caption" sx={{ fontWeight: 700 }}>
                    {(driver.contribution * 100).toFixed(0)}%
                  </Typography>
                </Stack>
                <Box sx={{ height: 6, borderRadius: 999, bgcolor: 'action.hover', mt: 0.25 }}>
                  <Box
                    sx={{
                      height: '100%',
                      width: `${Math.min(100, Math.abs(driver.contribution) * 100)}%`,
                      borderRadius: 999,
                      bgcolor: 'primary.main',
                    }}
                  />
                </Box>
              </Box>
            ))}
          </Stack>
        </Box>
      </Popover>
    </>
  )
}
