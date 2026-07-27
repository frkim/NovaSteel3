import { Box, Chip, Divider, Link, Stack, Tooltip, Typography } from '@mui/material'
import FactoryOutlinedIcon from '@mui/icons-material/FactoryOutlined'
import ReportProblemOutlinedIcon from '@mui/icons-material/ReportProblemOutlined'
import FlagOutlinedIcon from '@mui/icons-material/FlagOutlined'
import EmojiEventsOutlinedIcon from '@mui/icons-material/EmojiEventsOutlined'
import PsychologyOutlinedIcon from '@mui/icons-material/PsychologyOutlined'
import GitHubIcon from '@mui/icons-material/GitHub'
import { useAnalytics } from '../../context/analytics'
import { useTokens } from '../../hooks/useTokens'
import { KpiBand, PanelCard, SectionStack } from './common'
import { ProofBadge } from '../primitives/ProofBadge'
import { GITHUB_REPO_URL, PROOF_BY_ID, proofCoverage, type ProofStatus } from '../../proof/proofCatalog'

const USECASE_SOURCE_URL = `${GITHUB_REPO_URL}/blob/main/docs/usecase/usecase.md`

/**
 * A statement lifted verbatim from `docs/usecase/usecase.md`, split so the
 * emphasised fragment renders bold exactly as the Markdown does, and bound to
 * the reference IDs in the proof catalog that evidence it.
 */
interface BriefLine {
  /** Bold fragment, i.e. the `**...**` run at the head of the bullet. */
  lead?: string
  /** Remainder of the bullet, plain text. */
  rest?: string
  /** Trailing bold fragment, where the brief bolds the measurable target. */
  tail?: string
  /** Proof reference IDs that evidence this line. */
  refs: string[]
}

const PROFILE: Array<{ key: string; value: string; refs: string[] }> = [
  { key: 'industry', value: 'Heavy Industry & Metals', refs: [] },
  { key: 'headquarters', value: 'Luxembourg', refs: [] },
  { key: 'region', value: 'Luxembourg, Germany, Belgium, Spain', refs: [] },
  {
    key: 'regulatory',
    value: 'GDPR \u2022 EU AI Act \u2022 Sector\u2011specific EU Directives',
    refs: ['REG-01', 'REG-02', 'REG-03'],
  },
]

const CHALLENGE_INTRO =
  'A Luxembourg-based integrated steel producer operating blast furnaces and rolling mills across four countries faces:'

const CHALLENGES: BriefLine[] = [
  { lead: 'Energy costs', rest: ' represent 35% of total production cost with no real\u2011time optimization', refs: ['CHL-01'] },
  {
    lead: 'CO\u2082 emissions',
    rest: ' under increasing pressure from EU Emissions Trading System (ETS) penalties',
    refs: ['CHL-02'],
  },
  {
    lead: 'Furnace lining wear',
    rest: ' impossible to predict, causing catastrophic failures costing ',
    tail: '\u20ac8M per event',
    refs: ['CHL-03'],
  },
  { lead: 'Quality consistency issues', rest: ' in high\u2011grade steel for automotive customers', refs: ['CHL-04'] },
  {
    lead: 'Skilled operators retiring',
    rest: ', with knowledge disappearing faster than it can be captured',
    refs: ['CHL-05'],
  },
]

const OBJECTIVE_INTRO = 'Implement an AI\u2011driven production optimization platform that:'

const OBJECTIVES: BriefLine[] = [
  { rest: 'Reduces energy consumption', refs: ['OBJ-01'] },
  { rest: 'Predicts equipment failures', refs: ['OBJ-02'] },
  { rest: 'Improves steel quality', refs: ['OBJ-03'] },
  { rest: 'Captures and structures operational expertise before it is lost', refs: ['OBJ-04'] },
]

const OUTCOMES: BriefLine[] = [
  { lead: 'Energy consumption per ton', rest: ' reduced by ', tail: '14%', refs: ['OUT-01'] },
  { lead: 'CO\u2082 emissions', rest: ' reduced by ', tail: '22%', refs: ['OUT-02'] },
  { lead: 'Furnace lining failure prediction', rest: ' with ', tail: '21\u2011day advance warning', refs: ['OUT-03'] },
  { lead: 'High\u2011grade steel yield', rest: ' improved by ', tail: '8%', refs: ['OUT-04'] },
]

const AI_POINTS: BriefLine[] = [
  {
    rest: 'A physics\u2011informed ML model predicts furnace lining degradation from thermal signatures',
    refs: ['AI-01'],
  },
  {
    rest: 'An energy dispatch optimization agent schedules energy\u2011intensive processes around electricity spot prices',
    refs: ['AI-02'],
  },
  {
    rest: 'A GenAI knowledge\u2011capture system interviews operators and structures expertise into searchable procedure libraries',
    refs: ['AI-03'],
  },
]

/**
 * Use case (defense aid): the brief itself, reproduced verbatim next to the
 * reference IDs that carry it into the running solution.
 *
 * This is deliberately not a Markdown renderer. The point of the screen is that
 * every sentence of `docs/usecase/usecase.md` is bound to a proof reference, so
 * a jury can walk the brief top to bottom and click straight through to the
 * evidence — which a rendered blob of Markdown could not offer.
 *
 * The whole brief lives in a single dock panel, so the page presents one tab
 * holding one continuous document that reads in the same order as the source
 * Markdown, rather than a grid of separately dockable fragments.
 */
export function UseCaseBrief() {
  const { t } = useAnalytics()
  const tokens = useTokens()
  const coverage = proofCoverage()

  const statusOf = (refs: string[]): ProofStatus | null => {
    const statuses = refs.map((id) => PROOF_BY_ID[id]?.status).filter(Boolean) as ProofStatus[]
    if (statuses.length === 0) return null
    if (statuses.every((status) => status === 'met')) return 'met'
    if (statuses.some((status) => status === 'partial')) return 'partial'
    return 'demo'
  }

  const accentOf = (refs: string[]): string => {
    const status = statusOf(refs)
    if (status === 'met') return tokens.status.success
    if (status === 'partial') return tokens.status.warning
    if (status === 'demo') return tokens.status.info
    return tokens.status.stale
  }

  const metrics = [
    {
      id: 'usecase-statements',
      label: t('proof.kpi.total'),
      value: String(coverage.total),
      status: 'neutral' as const,
      tooltip: t('usecase.legend'),
    },
    { id: 'usecase-met', label: t('proof.kpi.met'), value: String(coverage.met), status: 'ok' as const },
    {
      id: 'usecase-partial',
      label: t('proof.kpi.partial'),
      value: String(coverage.partial + coverage.demo),
      status: 'warning' as const,
    },
    {
      id: 'usecase-coverage',
      label: t('proof.kpi.coverage'),
      value: coverage.coveragePct.toFixed(1),
      unit: '%',
      status: coverage.coveragePct >= 75 ? ('ok' as const) : ('warning' as const),
    },
  ]

  const renderLine = (line: BriefLine, index: number) => (
    <Box
      key={`${line.lead ?? ''}${line.rest ?? ''}${index}`}
      sx={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 1,
        py: 0.75,
        pl: 1.25,
        borderLeft: '3px solid',
        borderColor: accentOf(line.refs),
      }}
    >
      <Typography variant="body2" sx={{ flex: 1, lineHeight: 1.55 }}>
        {line.lead ? <Box component="strong">{line.lead}</Box> : null}
        {line.rest}
        {line.tail ? <Box component="strong">{line.tail}</Box> : null}
      </Typography>
      <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5, pt: 0.1 }}>
        {line.refs.map((id) => (
          <ProofBadge key={id} id={id} />
        ))}
      </Stack>
    </Box>
  )

  /**
   * One heading + body block of the brief, rendered inline so the whole
   * document reads top to bottom in a single tab, the way the Markdown does.
   */
  const section = (
    id: string,
    icon: typeof FactoryOutlinedIcon,
    titleKey: string,
    intro: string | null,
    lines: BriefLine[],
  ) => {
    const Icon = icon
    return (
      <Box key={id} id={id} component="section" aria-label={t(titleKey)} sx={{ scrollMarginTop: 16 }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1 }}>
          <Icon fontSize="small" sx={{ color: 'text.secondary' }} />
          <Typography variant="h3">{t(titleKey)}</Typography>
        </Stack>
        {intro ? (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {intro}
          </Typography>
        ) : null}
        <Stack divider={<Divider flexItem sx={{ opacity: 0.4 }} />}>{lines.map(renderLine)}</Stack>
      </Box>
    )
  }

  return (
    <SectionStack>
      <PanelCard
        id="usecase-document"
        title={t('usecase.title')}
        action={
          <Tooltip title={t('usecase.openSource')} describeChild>
            <Link
              href={USECASE_SOURCE_URL}
              target="_blank"
              rel="noopener noreferrer"
              underline="hover"
              sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, fontSize: '0.8rem' }}
            >
              docs/usecase/usecase.md
              <GitHubIcon sx={{ fontSize: '0.95rem' }} />
            </Link>
          </Tooltip>
        }
      >
        <Stack spacing={2.5} sx={{ maxWidth: 1080 }}>
          <Box id="usecase-source" component="section" aria-label={t('usecase.source')}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5 }}>
              {'NovaSteel \u2014 AI\u2011Powered Steel Production Optimization Platform'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('usecase.subtitle')}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              {t('usecase.sourceNote')}
            </Typography>
            <Chip
              size="small"
              label={t('usecase.covered')
                .replace('{met}', String(coverage.met))
                .replace('{total}', String(coverage.total))}
              sx={{
                mt: 1.25,
                height: 22,
                bgcolor: `${tokens.status.success}22`,
                color: tokens.status.success,
                fontWeight: 600,
              }}
            />
          </Box>

          <KpiBand id="usecase-kpis" title={t('usecase.title')} metrics={metrics} minWidth={170} />

          <Box id="usecase-profile" component="section" aria-label={t('usecase.section.profile')}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1 }}>
              <FactoryOutlinedIcon fontSize="small" sx={{ color: 'text.secondary' }} />
              <Typography variant="h3">{t('usecase.section.profile')}</Typography>
            </Stack>
            <Stack spacing={0.75}>
              {PROFILE.map((row) => (
                <Stack
                  key={row.key}
                  direction="row"
                  spacing={1}
                  sx={{ alignItems: 'center', flexWrap: 'wrap', gap: 0.5 }}
                >
                  <Typography variant="body2" sx={{ fontWeight: 700, minWidth: 160 }}>
                    {t(`usecase.profile.${row.key}`)}
                  </Typography>
                  <Typography variant="body2" sx={{ flex: 1 }}>
                    {row.value}
                  </Typography>
                  {row.refs.map((id) => (
                    <ProofBadge key={id} id={id} />
                  ))}
                </Stack>
              ))}
            </Stack>
          </Box>

          {section(
            'usecase-challenge',
            ReportProblemOutlinedIcon,
            'usecase.section.challenge',
            CHALLENGE_INTRO,
            CHALLENGES,
          )}
          {section(
            'usecase-objective',
            FlagOutlinedIcon,
            'usecase.section.objective',
            OBJECTIVE_INTRO,
            OBJECTIVES,
          )}
          {section('usecase-outcome', EmojiEventsOutlinedIcon, 'usecase.section.outcome', null, OUTCOMES)}
          {section('usecase-ai', PsychologyOutlinedIcon, 'usecase.section.ai', null, AI_POINTS)}
        </Stack>
      </PanelCard>
    </SectionStack>
  )
}
