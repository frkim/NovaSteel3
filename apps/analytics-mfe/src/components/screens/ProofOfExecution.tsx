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
import GavelOutlinedIcon from '@mui/icons-material/GavelOutlined'
import ReportProblemOutlinedIcon from '@mui/icons-material/ReportProblemOutlined'
import FlagOutlinedIcon from '@mui/icons-material/FlagOutlined'
import EmojiEventsOutlinedIcon from '@mui/icons-material/EmojiEventsOutlined'
import PsychologyOutlinedIcon from '@mui/icons-material/PsychologyOutlined'
import { useAnalytics } from '../../context/analytics'
import { useTokens } from '../../hooks/useTokens'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { KpiBand, PanelCard, SectionStack, TwoColumn } from './common'
import {
  githubUrlFor,
  PROOF_CATEGORY_ORDER,
  PROOF_REQUIREMENTS,
  proofCoverage,
  type EvidenceKind,
  type ProofCategory,
  type ProofRequirement,
  type ProofStatus,
} from '../../proof/proofCatalog'

const CATEGORY_ICON: Record<ProofCategory, typeof GavelOutlinedIcon> = {
  regulatory: GavelOutlinedIcon,
  challenge: ReportProblemOutlinedIcon,
  objective: FlagOutlinedIcon,
  outcome: EmojiEventsOutlinedIcon,
  ai: PsychologyOutlinedIcon,
}

/**
 * Proof of execution (defense aid): every requirement of the use-case brief,
 * the evidence that satisfies it, and an honest caveat where the demo is a
 * surrogate for the production claim.
 *
 * The catalog in `src/proof/proofCatalog.ts` is the single source of truth and
 * is also what the in-situ `ProofBadge` chips resolve against, so a reference
 * ID seen on any screen leads back to exactly this register.
 */
export function ProofOfExecution() {
  const { emit, site, t } = useAnalytics()
  const tokens = useTokens()
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<ProofCategory | null>(null)
  const [selectedId, setSelectedId] = useState<string>(PROOF_REQUIREMENTS[0].id)

  const statusColor = (status: ProofStatus): string =>
    status === 'met' ? tokens.status.success : status === 'partial' ? tokens.status.warning : tokens.status.info

  const statusLabel = (status: ProofStatus): string =>
    status === 'met' ? t('proof.status.met') : status === 'partial' ? t('proof.status.partial') : t('proof.status.demo')

  const categoryLabel = (value: ProofCategory): string => t(`proof.category.${value}`)

  const evidenceLabel = (kind: EvidenceKind): string => t(`proof.evidence.${kind}`)

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase()
    return PROOF_REQUIREMENTS.filter((requirement) => {
      if (category && requirement.category !== category) return false
      if (!needle) return true
      const haystack = [
        requirement.id,
        requirement.statement,
        requirement.howMet,
        requirement.target ?? '',
        requirement.caveat ?? '',
        ...requirement.evidence.map((entry) => `${entry.label} ${entry.detail ?? ''}`),
      ]
        .join(' ')
        .toLowerCase()
      return haystack.includes(needle)
    })
  }, [query, category])

  const selected: ProofRequirement =
    visible.find((requirement) => requirement.id === selectedId) ?? visible[0] ?? PROOF_REQUIREMENTS[0]

  const coverage = proofCoverage()

  const open = (route: string) => {
    emit('nav.intent', { route: `/${site}/${route}` })
  }

  const metrics = [
    {
      id: 'proof-total',
      label: t('proof.kpi.total'),
      value: String(coverage.total),
      status: 'neutral' as const,
      tooltip: t('proof.legend'),
    },
    {
      id: 'proof-met',
      label: t('proof.kpi.met'),
      value: String(coverage.met),
      status: 'ok' as const,
      target: `${coverage.coveragePct}%`,
    },
    {
      id: 'proof-partial',
      label: t('proof.kpi.partial'),
      value: String(coverage.partial + coverage.demo),
      status: 'warning' as const,
    },
    {
      id: 'proof-coverage',
      label: t('proof.kpi.coverage'),
      value: coverage.coveragePct.toFixed(1),
      unit: '%',
      status: coverage.coveragePct >= 75 ? ('ok' as const) : ('warning' as const),
    },
  ]

  const columns: DataTableColumn<ProofRequirement>[] = [
    {
      key: 'id',
      label: t('proof.col.id'),
      sortable: true,
      searchable: true,
      width: 88,
      render: (row) => (
        <Chip
          label={row.id}
          size="small"
          variant="outlined"
          sx={{ height: 20, fontSize: '0.65rem', fontWeight: 700, borderColor: statusColor(row.status), color: statusColor(row.status) }}
        />
      ),
    },
    {
      key: 'category',
      label: t('proof.col.category'),
      sortable: true,
      searchable: true,
      width: 170,
      value: (row) => categoryLabel(row.category),
    },
    {
      key: 'statement',
      label: t('proof.col.requirement'),
      sortable: true,
      searchable: true,
      value: (row) => row.statement,
    },
    {
      key: 'target',
      label: t('proof.col.target'),
      sortable: true,
      searchable: true,
      width: 150,
      value: (row) => row.target ?? '\u2014',
    },
    {
      key: 'status',
      label: t('proof.col.status'),
      sortable: true,
      searchable: true,
      width: 130,
      value: (row) => statusLabel(row.status),
      render: (row) => (
        <Chip
          label={statusLabel(row.status)}
          size="small"
          sx={{ height: 20, fontSize: '0.68rem', bgcolor: `${statusColor(row.status)}22`, color: statusColor(row.status) }}
        />
      ),
    },
  ]

  return (
    <SectionStack>
      <KpiBand id="proof-kpis" title={t('proof.title')} metrics={metrics} />

      <PanelCard
        id="proof-filters"
        title={t('proof.title')}
        action={
          <TextField
            size="small"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={t('proof.search')}
            sx={{ minWidth: 260 }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              },
              htmlInput: { 'aria-label': t('proof.search') },
            }}
          />
        }
      >
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          {t('proof.subtitle')}
        </Typography>
        <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
          <Chip
            size="small"
            label={t('proof.filter.all')}
            color={category === null ? 'primary' : 'default'}
            variant={category === null ? 'filled' : 'outlined'}
            onClick={() => setCategory(null)}
          />
          {PROOF_CATEGORY_ORDER.map((entry) => {
            const Icon = CATEGORY_ICON[entry]
            const count = PROOF_REQUIREMENTS.filter((requirement) => requirement.category === entry).length
            return (
              <Chip
                key={entry}
                size="small"
                icon={<Icon fontSize="small" />}
                label={`${categoryLabel(entry)} (${count})`}
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
            value={coverage.coveragePct}
            aria-label={t('proof.kpi.coverage')}
            sx={{ height: 8, borderRadius: 4 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            {t('proof.legend')}
          </Typography>
        </Box>
      </PanelCard>

      <TwoColumn
        sideWidth={380}
        main={
          <PanelCard id="proof-register" title={t('proof.section.requirements')}>
            <DataTable
              rows={visible}
              columns={columns}
              getRowId={(row) => row.id}
              caption={t('proof.section.requirements')}
              exportable
              exportFileName="novasteel-proof-of-execution"
              onRowClick={(row) => setSelectedId(row.id)}
              pageSizeOptions={[10, 25, 100]}
              initialPageSize={25}
              emptyMessage={t('proof.empty')}
            />
          </PanelCard>
        }
        side={
          <PanelCard
            id="proof-detail"
            title={`${selected.id} \u2014 ${t('proof.section.detail')}`}
            action={
              selected.primaryRoute ? (
                <Tooltip title={t('proof.detail.openScreen')}>
                  <Button
                    size="small"
                    variant="outlined"
                    endIcon={<LaunchIcon fontSize="small" />}
                    onClick={() => open(selected.primaryRoute as string)}
                  >
                    {t('proof.detail.openScreen')}
                  </Button>
                </Tooltip>
              ) : undefined
            }
          >
            <Stack spacing={1.5}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap', gap: 0.5 }}>
                <Chip
                  size="small"
                  label={statusLabel(selected.status)}
                  sx={{
                    height: 22,
                    bgcolor: `${statusColor(selected.status)}22`,
                    color: statusColor(selected.status),
                    fontWeight: 600,
                  }}
                />
                <Chip size="small" variant="outlined" label={categoryLabel(selected.category)} sx={{ height: 22 }} />
                {selected.target ? (
                  <Chip size="small" variant="outlined" label={selected.target} sx={{ height: 22 }} />
                ) : null}
              </Stack>

              <Box>
                <Typography variant="overline" color="text.secondary">
                  {t('proof.detail.requirement')}
                </Typography>
                <Typography variant="body2">{selected.statement}</Typography>
              </Box>

              <Divider />

              <Box>
                <Typography variant="overline" color="text.secondary">
                  {t('proof.detail.howMet')}
                </Typography>
                <Typography variant="body2">{selected.howMet}</Typography>
              </Box>

              <Divider />

              <Box>
                <Typography variant="overline" color="text.secondary">
                  {t('proof.detail.evidence')}
                </Typography>
                <Stack spacing={1} sx={{ mt: 0.5 }}>
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
                            <Tooltip title={t('proof.detail.openGithub')} describeChild>
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
              </Box>

              {selected.caveat ? (
                <>
                  <Divider />
                  <Box
                    sx={{
                      p: 1.25,
                      borderRadius: 1,
                      borderLeft: `3px solid ${tokens.status.warning}`,
                      bgcolor: `${tokens.status.warning}12`,
                    }}
                  >
                    <Typography variant="overline" sx={{ color: tokens.status.warning }}>
                      {t('proof.detail.caveat')}
                    </Typography>
                    <Typography variant="body2">{selected.caveat}</Typography>
                  </Box>
                </>
              ) : null}
            </Stack>
          </PanelCard>
        }
      />
    </SectionStack>
  )
}
