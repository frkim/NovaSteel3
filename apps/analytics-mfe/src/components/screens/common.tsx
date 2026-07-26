import type { ReactNode } from 'react'
import { Box, Card, CardContent, Stack, Typography } from '@mui/material'
import { KpiCard, type KpiCardModel } from '../primitives/KpiCard'

export function KpiBand({ metrics, minWidth = 190 }: { metrics: KpiCardModel[]; minWidth?: number }) {
  return (
    <Box
      component="section"
      aria-label="Key performance indicators"
      sx={{
        display: 'grid',
        gap: 2,
        gridTemplateColumns: `repeat(auto-fit, minmax(${minWidth}px, 1fr))`,
      }}
    >
      {metrics.map((metric) => (
        <KpiCard key={metric.id} metric={metric} />
      ))}
    </Box>
  )
}

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

export function PanelCard({
  id,
  title,
  action,
  children,
}: {
  id?: string
  title: string
  action?: ReactNode
  children: ReactNode
}) {
  return (
    <Card id={id} component="section" aria-label={title} sx={{ scrollMarginTop: 16 }}>
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

/**
 * Scroll a same-screen detail panel into view for a KPI tile drill-down.
 * Used when the detail for a metric already lives on the current screen, so
 * navigating to another tab would lose context.
 */
export function revealPanel(id: string) {
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

export function SectionStack({ children }: { children: ReactNode }) {
  return <Stack spacing={2}>{children}</Stack>
}
