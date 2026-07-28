import { useContext, useMemo, type ReactNode } from 'react'
import { Box, Card, CardContent, Stack, Typography } from '@mui/material'
import { KpiCard, type KpiCardModel } from '../primitives/KpiCard'
import { AnalyticsContext } from '../../context/analytics'
import { resolveThemeMode } from '../../designTokens'
import { WorkspaceDock } from '../dock/WorkspaceDock'
import { collectDockPanels } from '../dock/dockPanels'
import { revealDockPanel } from '../dock/dockCommands'
import { DockedContext, useDocked } from '../dock/dockContext'

const KPI_PENDING_VALUE = '—'

/**
 * Strips every derived signal from a KPI tile so an in-flight fetch never renders a
 * computed zero (which would read as a real, healthy measurement).
 */
export function toPendingMetrics(metrics: KpiCardModel[]): KpiCardModel[] {
  return metrics.map((metric) => ({
    id: metric.id,
    label: metric.label,
    value: KPI_PENDING_VALUE,
    tooltip: metric.tooltip,
    status: 'neutral',
  }))
}

export function KpiBand({
  metrics,
  minWidth = 190,
  id,
  title,
  pending = false,
}: {
  metrics: KpiCardModel[]
  minWidth?: number
  /** Dock panel id; read by the panel collector, not by this component. */
  id?: string
  /** Dock tab label; read by the panel collector, not by this component. */
  title?: string
  /** True while the first fetch is in flight: tiles show a placeholder instead of derived zeros. */
  pending?: boolean
}) {
  void id
  void title
  const shown = pending ? toPendingMetrics(metrics) : metrics
  return (
    <Box
      component="section"
      aria-label="Key performance indicators"
      aria-busy={pending || undefined}
      sx={{
        display: 'grid',
        gap: 2,
        gridTemplateColumns: `repeat(auto-fit, minmax(${minWidth}px, 1fr))`,
      }}
    >
      {shown.map((metric) => (
        <KpiCard key={metric.id} metric={metric} />
      ))}
    </Box>
  )
}
KpiBand.dockRole = 'kpi' as const

export function TwoColumn({
  main,
  side,
  sideWidth = 320,
}: {
  main: ReactNode
  side: ReactNode
  sideWidth?: number
}) {
  return (
    <Box
      sx={{
        display: 'grid',
        gap: 2,
        gridTemplateColumns: { xs: '1fr', lg: `minmax(0, 2fr) minmax(${sideWidth}px, 1fr)` },
        alignItems: 'start',
      }}
    >
      <Box sx={{ minWidth: 0 }}>{main}</Box>
      <Box sx={{ minWidth: 0 }}>{side}</Box>
    </Box>
  )
}
TwoColumn.dockRole = 'split' as const

export function PanelCard({
  id,
  title,
  action,
  children,
  onDockClose,
  dockWidth,
  dockHeight,
}: {
  id?: string
  title: string
  action?: ReactNode
  children: ReactNode
  /**
   * Supplying this makes the panel dismissible: its dock tab gains a close
   * button which invokes the callback instead of removing the panel behind
   * React's back, so the owning screen's state stays authoritative.
   */
  onDockClose?: () => void
  dockWidth?: number
  dockHeight?: number
}) {
  const docked = useDocked()
  void onDockClose
  void dockWidth
  void dockHeight

  // Inside a dock the tab already supplies the frame and the title, so the card
  // chrome would only add a second border and a duplicate heading.
  if (docked) {
    return (
      <Box
        id={id}
        component="section"
        aria-label={title || undefined}
        sx={{ minWidth: 0, scrollMarginTop: 16 }}
      >
        {action ? (
          <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'flex-end', mb: 1 }}>
            {action}
          </Stack>
        ) : null}
        {children}
      </Box>
    )
  }

  return (
    <Card id={id} component="section" aria-label={title || undefined} sx={{ scrollMarginTop: 16 }}>
      <CardContent>
        <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="h3">{title}</Typography>
          {action}
        </Stack>
        {children}
      </CardContent>
    </Card>
  )
}
PanelCard.dockRole = 'panel' as const

/**
 * Bring a same-screen detail panel to the operator's attention for a KPI tile
 * drill-down.
 *
 * In a dock the target is frequently on a background tab, where scrolling is a
 * no-op, so activating the tab is the correct reveal. The scroll fallback still
 * covers undocked screens and content nested inside a panel.
 */
export function revealPanel(id: string) {
  if (revealDockPanel(id)) {
    return
  }
  if (typeof document === 'undefined') {
    return
  }
  const panel = document.getElementById(id)
  if (!panel) {
    return
  }
  panel.scrollIntoView({ behavior: 'smooth', block: 'start' })
  panel.setAttribute('tabindex', '-1')
  panel.focus({ preventScroll: true })
}

function dockDisabled(): boolean {
  return typeof window !== 'undefined' && window.NOVASTEEL_ANALYTICS_CONFIG?.disableDock === true
}

/**
 * The layout root of every screen.
 *
 * The panels a screen already declares become a Dockview grid, so an operator
 * can rearrange, resize, tab-group and maximise any part of any screen instead
 * of scrolling one fixed column. Screens keep declaring plain JSX — the panel
 * set is derived from it, so the two descriptions cannot drift apart.
 */
export function SectionStack({ children }: { children: ReactNode }) {
  const analytics = useContext(AnalyticsContext)
  const specs = useMemo(() => collectDockPanels(children), [children])

  const layoutKey = analytics
    ? `${analytics.context.navigation.section}/${analytics.context.navigation.subView ?? 'default'}`
    : 'standalone'
  const themeMode = resolveThemeMode(analytics?.context.themeMode ?? 'light')

  // Flipping between a plain stack and a grid as detail panels appear would
  // remount the whole screen, so the dock is used whenever there is anything to
  // dock at all. The escape hatch stays for hosts that cannot bound its height.
  if (dockDisabled() || specs.length === 0) {
    return <Stack spacing={2}>{children}</Stack>
  }

  return (
    <DockedContext.Provider value>
      <WorkspaceDock layoutKey={layoutKey} specs={specs} themeMode={themeMode} />
    </DockedContext.Provider>
  )
}
