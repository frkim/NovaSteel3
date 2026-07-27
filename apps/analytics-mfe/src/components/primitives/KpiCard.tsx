import type { MouseEvent } from 'react'
import { Box, Card, CardActionArea, CardContent, Stack, Tooltip, Typography } from '@mui/material'
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutlineOutlined'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import RemoveIcon from '@mui/icons-material/Remove'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import type { DataSource } from '../../api/domain'
import type { Driver } from '../../api/envelope'
import { useAnalytics } from '../../context/analytics'
import { useTokens } from '../../hooks/useTokens'
import { kpiSemanticPalette, type KpiSemanticStatus } from '../../designTokens'
import { Sparkline } from '../charts/Sparkline'
import { FreshnessBadge } from './FreshnessBadge'
import { WhyPopover } from './WhyPopover'

export type KpiCardStatus = KpiSemanticStatus

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
  /** Semantic tile status: ok = healthy/on target, warning = at risk, critical = alert, neutral = N/A or informational. */
  status?: KpiCardStatus
  /** Plain-language explanation of what the metric means and how it is derived. */
  tooltip?: string
  /** What clicking the tile opens, e.g. "the spot-price schedule". */
  actionHint?: string
  onClick?: () => void
}

export interface KpiCardProps {
  metric: KpiCardModel
}

const KPI_STATUS_LABEL_KEYS: Record<KpiCardStatus, string> = {
  ok: 'kpi.status.ok',
  warning: 'kpi.status.warning',
  critical: 'kpi.status.critical',
  neutral: 'kpi.status.neutral',
}

const KPI_STATUS_ICONS = {
  ok: CheckCircleOutlineIcon,
  warning: WarningAmberIcon,
  critical: ErrorOutlineIcon,
  neutral: InfoOutlinedIcon,
} as const

export function deriveKpiStatus(metric: Pick<KpiCardModel, 'status' | 'trend' | 'goodDirection'>): KpiCardStatus {
  if (metric.status) {
    return metric.status
  }
  if (!metric.trend || metric.trend === 'flat' || !metric.goodDirection) {
    return 'neutral'
  }
  return metric.trend === metric.goodDirection ? 'ok' : 'warning'
}

export function KpiCard({ metric }: KpiCardProps) {
  const { t } = useAnalytics()
  const tokens = useTokens()
  const status = deriveKpiStatus(metric)
  const statusColors = kpiSemanticPalette(tokens.mode)[status]
  const StatusIcon = KPI_STATUS_ICONS[status]
  const statusLabel = t(KPI_STATUS_LABEL_KEYS[status])
  const statusAria = t('kpi.status.aria', { status: statusLabel })

  const trendColor =
    metric.trend && metric.trend !== 'flat' && metric.goodDirection
      ? metric.trend === metric.goodDirection
        ? tokens.status.success
        : tokens.status.warning
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
        {metric.onClick && (
          <ChevronRightIcon
            aria-hidden
            sx={{ color: statusColors.accent, fontSize: '1.1rem', ml: 'auto', opacity: 0.85 }}
          />
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

  const labelText = (
    <Typography color="text.secondary" variant="body2" sx={{ fontWeight: 600 }}>
      {metric.label}
    </Typography>
  )

  const label = metric.tooltip ? (
    <Tooltip title={metric.tooltip} placement="top-start" arrow enterDelay={200} describeChild>
      <Stack
        component="span"
        direction="row"
        spacing={0.5}
        tabIndex={0}
        aria-label={`${metric.label}. ${metric.tooltip}`}
        sx={{ alignItems: 'center', cursor: 'help', minWidth: 0 }}
      >
        {labelText}
        <InfoOutlinedIcon aria-hidden sx={{ fontSize: '0.95rem', flexShrink: 0, opacity: 0.6 }} />
      </Stack>
    </Tooltip>
  ) : (
    labelText
  )

  const actionArea = (
    <CardActionArea
      aria-label={`${metric.label}: open ${metric.actionHint ?? 'details'}`}
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
  )

  return (
    <Card
      component="article"
      aria-label={`${metric.label}; ${statusAria}`}
      data-help={`kpi:${metric.id}`}
      data-help-detail={metric.tooltip}
      sx={{
        height: '100%',
        backgroundColor: statusColors.background,
        borderLeft: `4px solid ${statusColors.accent}`,
      }}
    >
      <CardContent sx={{ height: '100%' }}>
        <span className="ns-visually-hidden">{statusAria}</span>
        <Stack sx={{ height: '100%' }} spacing={0.5}>
          <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
            <Stack component="span" direction="row" spacing={0.5} sx={{ alignItems: 'center', minWidth: 0 }}>
              <Tooltip title={statusLabel} placement="top" enterDelay={200}>
                <Box component="span" aria-hidden sx={{ display: 'inline-flex', flexShrink: 0 }}>
                  <StatusIcon sx={{ color: statusColors.accent, fontSize: '1rem' }} />
                </Box>
              </Tooltip>
              {label}
            </Stack>
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
            metric.actionHint ? (
              <Tooltip title={`Open ${metric.actionHint}`} placement="bottom" enterDelay={400}>
                {actionArea}
              </Tooltip>
            ) : (
              actionArea
            )
          ) : (
            details
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}
