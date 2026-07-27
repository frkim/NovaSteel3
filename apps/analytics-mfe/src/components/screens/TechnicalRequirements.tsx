import { useMemo, useState } from 'react'
import {
  Box,
  Button,
  Chip,
  Divider,
  InputAdornment,
  LinearProgress,
  Link,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import LaunchIcon from '@mui/icons-material/Launch'
import GitHubIcon from '@mui/icons-material/GitHub'
import ArchitectureOutlinedIcon from '@mui/icons-material/ArchitectureOutlined'
import TerminalOutlinedIcon from '@mui/icons-material/TerminalOutlined'
import MonitorHeartOutlinedIcon from '@mui/icons-material/MonitorHeartOutlined'
import PsychologyOutlinedIcon from '@mui/icons-material/PsychologyOutlined'
import HubOutlinedIcon from '@mui/icons-material/HubOutlined'
import SpeedOutlinedIcon from '@mui/icons-material/SpeedOutlined'
import SlideshowOutlinedIcon from '@mui/icons-material/SlideshowOutlined'
import { useAnalytics } from '../../context/analytics'
import { useTokens } from '../../hooks/useTokens'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { KpiBand, PanelCard, SectionStack, TwoColumn } from './common'
import { GITHUB_REPO_URL, githubUrlFor, type EvidenceKind } from '../../proof/proofCatalog'
import {
  TECH_CATEGORY_ORDER,
  TECH_REQUIREMENTS,
  techScorecard,
  type TechCategory,
  type TechRequirement,
  type TechScore,
} from '../../proof/technicalCatalog'

const ANALYSIS_URL = `${GITHUB_REPO_URL}/blob/main/docs/tech/technical-analysis.md`
const RUBRIC_URL = `${GITHUB_REPO_URL}/blob/main/docs/tech/rating_grid.md`

const CATEGORY_ICON: Record<TechCategory, typeof ArchitectureOutlinedIcon> = {
  design: ArchitectureOutlinedIcon,
  development: TerminalOutlinedIcon,
  monitoring: MonitorHeartOutlinedIcon,
  ai: PsychologyOutlinedIcon,
  agentic: HubOutlinedIcon,
  architecture: SpeedOutlinedIcon,
  presentation: SlideshowOutlinedIcon,
}

/**
 * Technical requirements (defense aid): the grading rubric answered criterion
 * by criterion, with the evidence behind each score and — where the score is
 * below 5 — the gap and the work that would close it.
 *
 * Deliberately mirrors the Proof of Execution screen so a jury moving between
 * the two only has to learn one layout. `src/proof/technicalCatalog.ts` is the
 * source of truth and must stay in step with `docs/tech/technical-analysis.md`.
 */
export function TechnicalRequirements() {
  const { emit, site, t } = useAnalytics()
  const tokens = useTokens()
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<TechCategory | null>(null)
  const [selectedId, setSelectedId] = useState<string>(TECH_REQUIREMENTS[0].id)

  const scoreColor = (score: TechScore): string =>
    score === 5 ? tokens.status.success : score === 4 ? tokens.status.warning : tokens.status.critical

  const categoryLabel = (value: TechCategory): string => t(`tech.category.${value}`)

  const evidenceLabel = (kind: EvidenceKind): string => t(`tech.evidence.${kind}`)

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase()
    return TECH_REQUIREMENTS.filter((requirement) => {
      if (category && requirement.category !== category) return false
      if (!needle) return true
      const haystack = [
        requirement.id,
        requirement.criterion,
        requirement.excellentBar,
        requirement.verdict,
        requirement.howMet,
        requirement.gap ?? '',
        requirement.uplift ?? '',
        ...requirement.evidence.map((entry) => `${entry.label} ${entry.detail ?? ''}`),
      ]
        .join(' ')
        .toLowerCase()
      return haystack.includes(needle)
    })
  }, [query, category])

  const selected: TechRequirement =
    visible.find((requirement) => requirement.id === selectedId) ?? visible[0] ?? TECH_REQUIREMENTS[0]

  const scorecard = techScorecard()

  const open = (route: string) => {
    emit('nav.intent', { route: `/${site}/${route}` })
  }

  const metrics = [
    {
      id: 'tech-total',
      label: t('tech.kpi.total'),
      value: `${scorecard.total}`,
      unit: `/ ${scorecard.max}`,
      status: 'ok' as const,
      tooltip: t('tech.legend'),
    },
    {
      id: 'tech-grade',
      label: t('tech.kpi.grade'),
      value: scorecard.grade,
      status: scorecard.grade === 'A' ? ('ok' as const) : ('warning' as const),
      target: scorecard.gradeLabel,
    },
    {
      id: 'tech-perfect',
      label: t('tech.kpi.perfect'),
      value: `${scorecard.perfect}`,
      unit: `/ ${scorecard.criteria}`,
      status: 'ok' as const,
    },
    {
      id: 'tech-criteria',
      label: t('tech.kpi.criteria'),
      value: String(scorecard.criteria),
      status: 'neutral' as const,
    },
  ]

  const columns: DataTableColumn<TechRequirement>[] = [
    {
      key: 'id',
      label: t('tech.col.id'),
      sortable: true,
      searchable: true,
      width: 104,
      render: (row) => (
        <Chip
          label={row.id}
          size="small"
          variant="outlined"
          sx={{
            height: 20,
            fontSize: '0.65rem',
            fontWeight: 700,
            borderColor: scoreColor(row.score),
            color: scoreColor(row.score),
          }}
        />
      ),
    },
    {
      key: 'category',
      label: t('tech.col.category'),
      sortable: true,
      searchable: true,
      width: 180,
      value: (row) => categoryLabel(row.category),
    },
    {
      key: 'criterion',
      label: t('tech.col.criterion'),
      sortable: true,
      searchable: true,
      value: (row) => row.criterion,
    },
    {
      key: 'verdict',
      label: t('tech.col.verdict'),
      sortable: true,
      searchable: true,
      value: (row) => row.verdict,
    },
    {
      key: 'score',
      label: t('tech.col.score'),
      sortable: true,
      searchable: true,
      width: 100,
      value: (row) => `${row.score} / 5`,
      render: (row) => (
        <Chip
          label={`${row.score} / 5`}
          size="small"
          sx={{ height: 20, fontSize: '0.68rem', bgcolor: `${scoreColor(row.score)}22`, color: scoreColor(row.score), fontWeight: 700 }}
        />
      ),
    },
  ]

  return (
    <SectionStack>
      <KpiBand id="tech-kpis" title={t('tech.title')} metrics={metrics} />

      <PanelCard
        id="tech-filters"
        title={t('tech.title')}
        action={
          <TextField
            size="small"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={t('tech.search')}
            sx={{ minWidth: 260 }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              },
              htmlInput: { 'aria-label': t('tech.search') },
            }}
          />
        }
      >
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          {t('tech.subtitle')}
        </Typography>
        <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
          <Chip
            size="small"
            label={t('tech.filter.all')}
            color={category === null ? 'primary' : 'default'}
            variant={category === null ? 'filled' : 'outlined'}
            onClick={() => setCategory(null)}
          />
          {TECH_CATEGORY_ORDER.map((entry) => {
            const Icon = CATEGORY_ICON[entry]
            const rows = TECH_REQUIREMENTS.filter((requirement) => requirement.category === entry)
            const earned = rows.reduce((sum, requirement) => sum + requirement.score, 0)
            return (
              <Chip
                key={entry}
                size="small"
                icon={<Icon fontSize="small" />}
                label={`${categoryLabel(entry)} (${earned}/${rows.length * 5})`}
                color={category === entry ? 'primary' : 'default'}
                variant={category === entry ? 'filled' : 'outlined'}
                onClick={() => setCategory(category === entry ? null : entry)}
              />
            )
          })}
        </Stack>
        <Box sx={{ mt: 2 }}>
          <LinearProgress
            variant="determinate"
            value={scorecard.pct}
            aria-label={t('tech.kpi.total')}
            sx={{ height: 8, borderRadius: 4 }}
          />
          <Stack direction="row" spacing={1.5} sx={{ mt: 0.75, alignItems: 'center', flexWrap: 'wrap' }}>
            <Typography variant="caption" color="text.secondary">
              {t('tech.legend')}
            </Typography>
            <Link
              href={RUBRIC_URL}
              target="_blank"
              rel="noopener noreferrer"
              underline="hover"
              sx={{ fontSize: '0.72rem', display: 'inline-flex', alignItems: 'center', gap: 0.4 }}
            >
              rating_grid.md
              <GitHubIcon sx={{ fontSize: '0.8rem' }} />
            </Link>
            <Link
              href={ANALYSIS_URL}
              target="_blank"
              rel="noopener noreferrer"
              underline="hover"
              sx={{ fontSize: '0.72rem', display: 'inline-flex', alignItems: 'center', gap: 0.4 }}
            >
              {t('tech.source')}
              <GitHubIcon sx={{ fontSize: '0.8rem' }} />
            </Link>
          </Stack>
        </Box>
      </PanelCard>

      <TwoColumn
        sideWidth={400}
        main={
          <PanelCard id="tech-register" title={t('tech.section.register')}>
            <DataTable
              rows={visible}
              columns={columns}
              getRowId={(row) => row.id}
              caption={t('tech.section.register')}
              exportable
              exportFileName="novasteel-technical-requirements"
              onRowClick={(row) => setSelectedId(row.id)}
              pageSizeOptions={[10, 25, 100]}
              initialPageSize={25}
              emptyMessage={t('tech.empty')}
            />
          </PanelCard>
        }
        side={
          <PanelCard
            id="tech-detail"
            title={`${selected.id} \u2014 ${t('tech.section.detail')}`}
            action={
              selected.primaryRoute ? (
                <Tooltip title={t('tech.detail.openScreen')} describeChild>
                  <Button
                    size="small"
                    variant="outlined"
                    endIcon={<LaunchIcon fontSize="small" />}
                    onClick={() => open(selected.primaryRoute as string)}
                  >
                    {t('tech.detail.openScreen')}
                  </Button>
                </Tooltip>
              ) : undefined
            }
          >
            <Stack spacing={1.5}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap', gap: 0.5 }}>
                <Chip
                  size="small"
                  label={t('tech.detail.score').replace('{score}', String(selected.score))}
                  sx={{
                    height: 22,
                    bgcolor: `${scoreColor(selected.score)}22`,
                    color: scoreColor(selected.score),
                    fontWeight: 700,
                  }}
                />
                <Chip size="small" variant="outlined" label={categoryLabel(selected.category)} sx={{ height: 22 }} />
              </Stack>

              <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                {selected.criterion}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {selected.verdict}
              </Typography>

              <Divider />
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  {t('tech.detail.bar')}
                </Typography>
                <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                  {selected.excellentBar}
                </Typography>
              </Box>

              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  {t('tech.detail.howMet')}
                </Typography>
                <Typography variant="body2">{selected.howMet}</Typography>
              </Box>

              {selected.gap ? (
                <Box
                  sx={{
                    p: 1,
                    borderLeft: '3px solid',
                    borderColor: tokens.status.warning,
                    bgcolor: `${tokens.status.warning}12`,
                    borderRadius: 0.5,
                  }}
                >
                  <Typography variant="caption" sx={{ color: tokens.status.warning, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    {t('tech.detail.gap')}
                  </Typography>
                  <Typography variant="body2">{selected.gap}</Typography>
                </Box>
              ) : null}

              {selected.uplift ? (
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    {t('tech.detail.uplift')}
                  </Typography>
                  <Typography variant="body2">{selected.uplift}</Typography>
                </Box>
              ) : null}

              <Divider />
              <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                {t('tech.detail.evidence')}
              </Typography>
              <Stack spacing={1}>
                {selected.evidence.map((entry) => {
                  const href = githubUrlFor(entry)
                  return (
                    <Box key={`${entry.kind}-${entry.label}`}>
                      <Stack direction="row" spacing={0.75} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
                        <Chip
                          size="small"
                          label={evidenceLabel(entry.kind)}
                          sx={{ height: 18, fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}
                        />
                        {href ? (
                          <Tooltip title={t('tech.detail.openGithub')} describeChild>
                            <Link
                              href={href}
                              target="_blank"
                              rel="noopener noreferrer"
                              underline="hover"
                              sx={{
                                fontFamily: 'ui-monospace, SFMono-Regular, monospace',
                                fontSize: '0.78rem',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 0.4,
                              }}
                            >
                              {entry.label}
                              <GitHubIcon sx={{ fontSize: '0.85rem' }} />
                            </Link>
                          </Tooltip>
                        ) : (
                          <Typography
                            variant="body2"
                            sx={{ fontFamily: 'ui-monospace, SFMono-Regular, monospace', fontSize: '0.78rem' }}
                          >
                            {entry.label}
                          </Typography>
                        )}
                        {entry.route ? (
                          <Button size="small" sx={{ minWidth: 0, px: 0.5 }} onClick={() => open(entry.route as string)}>
                            <LaunchIcon fontSize="inherit" />
                          </Button>
                        ) : null}
                      </Stack>
                      {entry.detail ? (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', pl: 0.5 }}>
                          {entry.detail}
                        </Typography>
                      ) : null}
                    </Box>
                  )
                })}
              </Stack>
            </Stack>
          </PanelCard>
        }
      />

      <PanelCard id="tech-breakdown" title={t('tech.section.breakdown')}>
        <Stack spacing={1.25}>
          {scorecard.byCategory.map((row) => {
            const pct = (row.score / row.max) * 100
            return (
              <Box key={row.category}>
                <Stack direction="row" sx={{ justifyContent: 'space-between', mb: 0.25 }}>
                  <Typography variant="body2">{categoryLabel(row.category)}</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 700 }}>
                    {row.score} / {row.max}
                  </Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={pct}
                  aria-label={categoryLabel(row.category)}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    '& .MuiLinearProgress-bar': {
                      bgcolor: pct === 100 ? tokens.status.success : tokens.status.warning,
                    },
                  }}
                />
              </Box>
            )
          })}
        </Stack>
      </PanelCard>
    </SectionStack>
  )
}
