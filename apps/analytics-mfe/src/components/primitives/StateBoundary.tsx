import type { ReactNode } from 'react'
import { Alert, AlertTitle, Box, Button, Skeleton, Stack, Typography } from '@mui/material'
import ReplayIcon from '@mui/icons-material/Replay'
import InboxIcon from '@mui/icons-material/Inbox'
import type { ResourceState } from '../../hooks/useResource'
import { useAnalytics } from '../../context/analytics'
import { LoadingGauge } from './LoadingGauge'

export interface StateBoundaryProps<T> {
  state: ResourceState<T>
  children: (data: T) => ReactNode
  isEmpty?: (data: T) => boolean
  emptyMessage?: string
  onReset?: () => void
  skeleton?: ReactNode
  skeletonRows?: number
  /**
   * `gauge` swaps the skeleton rows for an animated gauge with a progress
   * message — used where a first load can genuinely take seconds (cloud mode).
   */
  loadingVariant?: 'skeleton' | 'gauge'
  loadingCaption?: string
  /**
   * Tab label when this boundary becomes a dock panel. A render-function child
   * cannot be inspected statically, so a boundary that wraps its screen's
   * panels is opaque to the panel collector and needs to name itself.
   */
  dockTitle?: string
  /** Dock panel id, when the boundary itself is the panel. */
  dockId?: string
}

export function StateBoundary<T>({
  state,
  children,
  isEmpty,
  emptyMessage,
  onReset,
  skeleton,
  skeletonRows = 4,
  loadingVariant = 'skeleton',
  loadingCaption,
  dockTitle,
  dockId,
}: StateBoundaryProps<T>) {
  const { t } = useAnalytics()
  void dockTitle
  void dockId

  if (state.status === 'loading' && state.data === null) {
    return (
      <Box aria-busy="true" aria-live="polite">
        <span className="ns-visually-hidden">{t('state.loading')}</span>
        {skeleton ??
          (loadingVariant === 'gauge' ? (
            <LoadingGauge caption={loadingCaption} />
          ) : (
            <Stack spacing={1}>
              {Array.from({ length: skeletonRows }).map((_, index) => (
                <Skeleton key={index} variant="rounded" height={index === 0 ? 48 : 32} animation="wave" />
              ))}
            </Stack>
          ))}
      </Box>
    )
  }

  if (state.status === 'error' && state.data === null) {
    return (
      <Alert
        severity="error"
        role="alert"
        action={
          <Button color="inherit" size="small" startIcon={<ReplayIcon />} onClick={state.reload}>
            {t('state.error.retry')}
          </Button>
        }
      >
        <AlertTitle>{t('state.error.title')}</AlertTitle>
        {state.error?.message}
        {state.error?.correlationId && (
          <Typography variant="caption" sx={{ display: 'block', mt: 0.5, opacity: 0.8 }}>
            correlation: {state.error.correlationId}
          </Typography>
        )}
      </Alert>
    )
  }

  if (state.data !== null && isEmpty?.(state.data)) {
    return (
      <Stack spacing={1.5} sx={{ alignItems: 'center', py: 4, textAlign: 'center' }}>
        <InboxIcon fontSize="large" color="disabled" aria-hidden />
        <Typography variant="body2" color="text.secondary">
          {emptyMessage ?? t('state.empty.filters')}
        </Typography>
        {onReset && (
          <Button size="small" variant="outlined" onClick={onReset}>
            {t('state.empty.reset')}
          </Button>
        )}
      </Stack>
    )
  }

  if (state.data === null) {
    return null
  }

  return <>{children(state.data)}</>
}
