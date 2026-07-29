import { useCallback, useEffect, useState } from 'react'
import {
  Box,
  Button,
  Chip,
  FormControlLabel,
  IconButton,
  LinearProgress,
  Paper,
  Stack,
  Switch,
  Typography,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import NavigateNextIcon from '@mui/icons-material/NavigateNext'
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore'
import type { MicrofrontendEmitter } from '../types'
import { useAnalytics } from '../context/analytics'

interface TourStep {
  title: string
  route: string
  narrative: string
  headline: string
}

/** Steps follow the 10-minute demo runbook moments (DM-1..DM-6). */
const STEPS: TourStep[] = [
  {
    title: 'Plant Manager — fleet & targets',
    route: 'command-center/overview',
    narrative: 'NovaSteel unifies production, energy, emissions, quality, maintenance, and operator knowledge. Everything shown is deterministic synthetic data.',
    headline: 'Four target outcomes: −14% energy, −22% CO₂, +8% yield, 21-day warning.',
  },
  {
    title: 'Energy Manager — optimized dispatch',
    route: 'energy-optimization/spot-price-schedule',
    narrative: 'Accelerated time, not fabricated UI. The optimizer preserves soak times, deliveries, capacity, and tonnage.',
    headline: '8–13% modeled cost reduction · zero hard-constraint violations.',
  },
  {
    title: 'Reliability Engineer — advance warning on the lining',
    route: 'furnace-health/lining-forecast',
    narrative: 'Neighboring thermocouples, cooling ΔT, and heat-flux residual agree — this is unlike a single bad sensor.',
    headline: 'P50 19.65 days · P10 18.69 · P90 20.61 · risk 0.90 (HIGH) — close to the ≥21-day target, not yet at it.',
  },
  {
    title: 'Quality Engineer — genealogy & what-if',
    route: 'quality/batches',
    narrative: 'The model warns before the first off-spec lab result and traces heat, slab, coil, and process settings.',
    headline: 'Bounded what-if: first-pass yield ≈ 88% → 95%, no recipe change.',
  },
  {
    title: 'Knowledge — capture & review boundary',
    route: 'knowledge-hub/procedures',
    narrative: 'A Foundry draft cannot publish. A Knowledge Engineer reviews, edits, and approves a version before retrieval.',
    headline: 'Draft cited to transcript · expert review required.',
  },
  {
    title: 'Sustainability — CO₂ & ETS',
    route: 'sustainability-compliance/emissions-ledger',
    narrative: 'The semantic model rolls up synthetic emissions and connects a recommendation to its evidence.',
    headline: 'Carbon and financial figures remain modeled targets.',
  },
  {
    title: 'Executive — portfolio & audit',
    route: 'executive-overview/overview',
    narrative: 'Every recommendation links inputs, model/version, confidence, human decision, and outcome.',
    headline: 'The 14/22/21/8 figures are targets; the screen is synthetic evidence of traceability.',
  },
]

const AUTO_ADVANCE_MS = 14000

export interface DemoTourProps {
  open: boolean
  onClose: () => void
  emit: MicrofrontendEmitter
  site: string
}

export function DemoTour({ open, onClose, emit, site }: DemoTourProps) {
  const { t } = useAnalytics()
  const [index, setIndex] = useState(0)
  const [auto, setAuto] = useState(false)

  const goTo = useCallback(
    (nextIndex: number) => {
      const clamped = Math.max(0, Math.min(STEPS.length - 1, nextIndex))
      setIndex(clamped)
      emit('nav.intent', { route: `/${site}/${STEPS[clamped].route}` })
    },
    [emit, site],
  )

  useEffect(() => {
    if (!open || !auto) {
      return
    }
    const timer = setTimeout(() => {
      setIndex((current) => {
        const next = current + 1 >= STEPS.length ? 0 : current + 1
        emit('nav.intent', { route: `/${site}/${STEPS[next].route}` })
        return next
      })
    }, AUTO_ADVANCE_MS)
    return () => clearTimeout(timer)
  }, [open, auto, index, emit, site])

  if (!open) {
    return null
  }

  const step = STEPS[index]

  return (
    <Paper
      elevation={8}
      role="region"
      aria-label="Guided demo tour"
      sx={{
        position: 'fixed',
        left: { xs: 8, md: 24 },
        right: { xs: 8, md: 24 },
        bottom: 16,
        zIndex: 1100,
        p: 2,
        borderTop: 3,
        borderColor: 'primary.main',
      }}
    >
      <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          <Chip color="primary" size="small" label={`${index + 1} / ${STEPS.length}`} />
          <Typography variant="h6">{step.title}</Typography>
        </Stack>
        <IconButton aria-label="Close guided demo" onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </Stack>
      <LinearProgress variant="determinate" value={((index + 1) / STEPS.length) * 100} sx={{ mb: 1 }} />
      <Typography variant="body2" sx={{ mb: 0.5 }}>
        {step.narrative}
      </Typography>
      <Typography variant="caption" sx={{ fontWeight: 700 }}>
        {step.headline}
      </Typography>
      <Stack direction="row" spacing={1} sx={{ mt: 1.5, alignItems: 'center', flexWrap: 'wrap' }}>
        <Button startIcon={<NavigateBeforeIcon />} onClick={() => goTo(index - 1)} disabled={index === 0}>
          {t('demo.tour.prev')}
        </Button>
        <Button
          variant="contained"
          endIcon={<NavigateNextIcon />}
          onClick={() => goTo(index + 1)}
          disabled={index === STEPS.length - 1}
        >
          {t('demo.tour.next')}
        </Button>
        <Box sx={{ flex: 1 }} />
        <FormControlLabel
          control={<Switch checked={auto} onChange={(event) => setAuto(event.target.checked)} />}
          label={t('demo.tour.auto')}
        />
      </Stack>
    </Paper>
  )
}
