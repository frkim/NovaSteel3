import type { MouseEvent } from 'react'
import { Box, Card, CardActionArea, CardContent, Stack, Typography } from '@mui/material'
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'
import RemoveIcon from '@mui/icons-material/Remove'
import type { DataSource } from '../../api/domain'
import type { Driver } from '../../api/envelope'
import { useTokens } from '../../hooks/useTokens'
import { Sparkline } from '../charts/Sparkline'
import { FreshnessBadge } from './FreshnessBadge'
import { WhyPopover } from './WhyPopover'

export interface KpiWhy {
  modelVersion: string
  scoredAt: string | null
  drivers: Driver[]
  confidenceText?: string
}

export interface KpiCardModel {
  id: string
  label: string
  value: string
  unit?: string
  trend?: 'up' | 'down' | 'flat'
  deltaLabel?: string
  goodDirection?: 'up' | 'down'
  target?: string
  sparkline?: number[]
  asOf?: string | null
  source?: DataSource | null
  why?: KpiWhy
  onClick?: () => void
}

export interface KpiCardProps {
  metric: KpiCardModel
}

export function KpiCard({ metric }: KpiCardProps) {
  const tokens = useTokens()

  const trendColor =
    metric.trend && metric.trend !== 'flat' && metric.goodDirection
      ? metric.trend === metric.goodDirection
        ? tokens.status.success
        : tokens.status.critical
      : 'text.secondary'
  const TrendIcon =
    metric.trend === 'up' ? ArrowUpwardIcon : metric.trend === 'down' ? ArrowDownwardIcon : RemoveIcon

  const details = (
    <>
      <Stack direction="row" spacing={1} sx={{ alignItems: 'baseline', flexWrap: 'wrap' }}>
        <Typography component="p" variant="h4" sx={{ lineHeight: 1.1 }}>
          {metric.value}
        </Typography>
        {metric.unit && (
          <Typography component="span" variant="body1" color="text.secondary">
            {metric.unit}
          </Typography>
        )}
        {metric.deltaLabel && (
          <Stack direction="row" spacing={0.25} sx={{ alignItems: 'center', color: trendColor }}>
            <TrendIcon sx={{ fontSize: '1rem' }} aria-hidden />
            <Typography variant="caption" sx={{ fontWeight: 700 }}>
              {metric.deltaLabel}
            </Typography>
          </Stack>
        )}
      </Stack>

      {metric.sparkline && metric.sparkline.length > 1 && (
        <Box sx={{ my: 0.25 }}>
          <Sparkline
            values={metric.sparkline}
            color={tokens.palette[0]}
            ariaLabel={`${metric.label} micro-trend`}
          />
        </Box>
      )}

      <Box sx={{ flex: 1 }} />
      <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
        {metric.target ? (
          <Typography variant="caption" color="text.secondary">
            {metric.target}
          </Typography>
        ) : (
          <span />
        )}
        {metric.asOf !== undefined && <FreshnessBadge asOf={metric.asOf ?? null} source={metric.source} />}
      </Stack>
    </>
  )

  return (
    <Card component="article" aria-label={metric.label} sx={{ height: '100%' }}>
      <CardContent sx={{ height: '100%' }}>
        <Stack sx={{ height: '100%' }} spacing={0.5}>
          <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography color="text.secondary" variant="body2" sx={{ fontWeight: 600 }}>
              {metric.label}
            </Typography>
            {metric.why && (
              <WhyPopover
                modelVersion={metric.why.modelVersion}
                scoredAt={metric.why.scoredAt}
                drivers={metric.why.drivers}
                confidenceText={metric.why.confidenceText}
              />
            )}
          </Stack>

          {metric.onClick ? (
            <CardActionArea
              sx={{ alignItems: 'stretch', flex: 1, justifyContent: 'flex-start', textAlign: 'left' }}
              onClick={(event: MouseEvent) => {
                event.preventDefault()
                metric.onClick?.()
              }}
            >
              <Stack sx={{ height: '100%', width: '100%' }} spacing={0.5}>
                {details}
              </Stack>
            </CardActionArea>
          ) : (
            details
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}
