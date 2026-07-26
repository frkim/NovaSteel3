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
  title,
  action,
  children,
}: {
  title: string
  action?: ReactNode
  children: ReactNode
}) {
  return (
    <Card component="section" aria-label={title}>
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

export function SectionStack({ children }: { children: ReactNode }) {
  return <Stack spacing={2}>{children}</Stack>
}
