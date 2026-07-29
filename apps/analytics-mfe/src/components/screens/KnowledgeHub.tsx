import { useCallback, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  InputAdornment,
  LinearProgress,
  MenuItem,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import NoteAddIcon from '@mui/icons-material/NoteAdd'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import CancelIcon from '@mui/icons-material/Cancel'
import SendIcon from '@mui/icons-material/SendOutlined'
import ScienceIcon from '@mui/icons-material/ScienceOutlined'
import RestartAltIcon from '@mui/icons-material/RestartAlt'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { useTokens } from '../../hooks/useTokens'
import type { ProcedureRow } from '../../api/domain'
import { knowledgeCoverage } from '../../api/fixtures'
import { KnowledgeClient } from '../../api/knowledgeClient'
import { StateBoundary } from '../primitives/StateBoundary'
import { SeverityPill } from '../primitives/SeverityPill'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { ProofBadges } from '../primitives/ProofBadge'
import { ProgressBullet } from '../charts/ProgressBullet'
import { KpiBand, PanelCard, SectionStack, TwoColumn, revealPanel } from './common'
import type { KpiCardModel } from '../primitives/KpiCard'

function statusSeverity(status: string): string {
  if (status === 'APPROVED') return 'INFO'
  if (status === 'IN_REVIEW') return 'WARNING'
  if (status === 'REJECTED') return 'CRITICAL'
  return 'CRITICAL'
}

const DOMAINS = [
  'Blast Furnace',
  'Electric Arc Furnace',
  'Ladle Metallurgy',
  'Continuous Casting',
  'Hot Rolling',
  'Cold Rolling',
  'Refractory',
  'Cooling Water',
  'Gas Cleaning',
  'Energy Management',
  'Safety & LOTO',
  'Environmental / EU ETS',
  'Quality & SPC',
  'Crane & Material Handling',
  'Coke Oven',
]

// ─── Create Entry Dialog ──────────────────────────────────────────────────────

interface CreateDialogProps {
  open: boolean
  onClose: () => void
  onCreated: () => void
  knowledgeClient: KnowledgeClient
  emit: (event: string, payload: unknown) => void
}

function CreateEntryDialog({ open, onClose, onCreated, knowledgeClient, emit }: CreateDialogProps) {
  const [title, setTitle] = useState('')
  const [domain, setDomain] = useState(DOMAINS[0])
  const [operatorRef, setOperatorRef] = useState('')
  const [consentGranted, setConsentGranted] = useState(false)
  const [retentionDays, setRetentionDays] = useState(365)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canSubmit = title.trim() && operatorRef.trim() && consentGranted && !submitting

  const handleSubmit = async () => {
    if (!canSubmit) return
    setSubmitting(true)
    setError(null)
    try {
      await knowledgeClient.createInterview({
        operatorRef: operatorRef.trim(),
        language: 'en',
        consent: { granted: true, scope: 'knowledge-capture', retentionDays },
      })
      emit('toast', { severity: 'success', message: `Knowledge capture started: "${title.trim()}" (domain: ${domain})` })
      onCreated()
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create entry')
    } finally {
      setSubmitting(false)
    }
  }

  const handleClose = () => {
    setTitle('')
    setDomain(DOMAINS[0])
    setOperatorRef('')
    setConsentGranted(false)
    setRetentionDays(365)
    setError(null)
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>New Knowledge Capture</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField
            label="Procedure title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            fullWidth
            required
            autoFocus
          />
          <TextField
            label="Domain"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            select
            fullWidth
          >
            {DOMAINS.map((d) => (
              <MenuItem key={d} value={d}>{d}</MenuItem>
            ))}
          </TextField>
          <TextField
            label="Expert / operator reference"
            value={operatorRef}
            onChange={(e) => setOperatorRef(e.target.value)}
            fullWidth
            required
            helperText="Name or ID of the domain expert being interviewed"
          />
          <TextField
            label="Retention period (days)"
            type="number"
            value={retentionDays}
            onChange={(e) => setRetentionDays(Number(e.target.value) || 365)}
            fullWidth
            helperText="How long recorded data will be retained under GDPR Art. 5(1)(e)"
          />
          <Alert severity="info" variant="outlined" data-help="knowledge:consent">
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
              Consent is required for knowledge capture
            </Typography>
            <Typography variant="caption" sx={{ display: 'block' }}>
              The expert's spoken expertise will be transcribed and stored. Under GDPR, explicit
              consent must be obtained before recording begins. The captured data will be retained for
              the specified period and used solely for operational knowledge extraction.
            </Typography>
          </Alert>
          <FormControlLabel
            control={
              <Checkbox
                checked={consentGranted}
                onChange={(e) => setConsentGranted(e.target.checked)}
                color="primary"
              />
            }
            label="I confirm that the expert has given explicit consent for this knowledge capture session (GDPR Art. 6(1)(a))"
          />
          {!consentGranted && (
            <Alert severity="warning" variant="outlined">
              Consent must be granted before submission. Without consent, the capture session cannot proceed.
            </Alert>
          )}
          {error && <Alert severity="error">{error}</Alert>}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={submitting}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!canSubmit}
          startIcon={<NoteAddIcon />}
        >
          Start capture
        </Button>
      </DialogActions>
      {submitting && <LinearProgress />}
    </Dialog>
  )
}

// ─── Reject Dialog ────────────────────────────────────────────────────────────

interface RejectDialogProps {
  open: boolean
  procedure: ProcedureRow | null
  onClose: () => void
  onRejected: () => void
  knowledgeClient: KnowledgeClient
  emit: (event: string, payload: unknown) => void
}

function RejectDialog({ open, procedure, onClose, onRejected, knowledgeClient, emit }: RejectDialogProps) {
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleReject = async () => {
    if (!procedure || !reason.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      await knowledgeClient.reject(procedure.procedureId, reason.trim())
      emit('toast', { severity: 'info', message: `Rejected: ${procedure.title}` })
      onRejected()
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rejection failed')
    } finally {
      setSubmitting(false)
    }
  }

  const handleClose = () => {
    setReason('')
    setError(null)
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Reject procedure</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {procedure && (
            <Alert severity="warning" variant="outlined">
              Rejecting: <strong>{procedure.title}</strong> ({procedure.procedureId})
            </Alert>
          )}
          <TextField
            label="Reason for rejection"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            multiline
            rows={3}
            fullWidth
            required
            helperText="Explain why this procedure does not meet quality standards"
          />
          {error && <Alert severity="error">{error}</Alert>}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={submitting}>Cancel</Button>
        <Button
          variant="contained"
          color="error"
          onClick={handleReject}
          disabled={!reason.trim() || submitting}
          startIcon={<CancelIcon />}
        >
          Reject
        </Button>
      </DialogActions>
      {submitting && <LinearProgress />}
    </Dialog>
  )
}

// ─── Pipeline View ────────────────────────────────────────────────────────────

function PipelineView({ procedures }: { procedures: ProcedureRow[] }) {
  const counts = useMemo(() => {
    const draft = procedures.filter((p) => p.status === 'DRAFT')
    const review = procedures.filter((p) => p.status === 'IN_REVIEW')
    const approved = procedures.filter((p) => p.status === 'APPROVED')
    const rejected = procedures.filter((p) => p.status === 'REJECTED')
    return { draft, review, approved, rejected }
  }, [procedures])

  const total = procedures.length || 1

  return (
    <Stack spacing={2} data-help="knowledge:pipeline">
      <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
        Workflow pipeline — {procedures.length} procedures
      </Typography>
      <Stack direction="row" spacing={0} sx={{ height: 32, borderRadius: 1, overflow: 'hidden' }}>
        {counts.draft.length > 0 && (
          <Tooltip title={`DRAFT: ${counts.draft.length}`}>
            <Box sx={{ flex: counts.draft.length / total, bgcolor: 'error.light', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="caption" sx={{ color: 'error.contrastText', fontWeight: 600 }}>
                {counts.draft.length}
              </Typography>
            </Box>
          </Tooltip>
        )}
        {counts.review.length > 0 && (
          <Tooltip title={`IN REVIEW: ${counts.review.length}`}>
            <Box sx={{ flex: counts.review.length / total, bgcolor: 'warning.light', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="caption" sx={{ color: 'warning.contrastText', fontWeight: 600 }}>
                {counts.review.length}
              </Typography>
            </Box>
          </Tooltip>
        )}
        {counts.approved.length > 0 && (
          <Tooltip title={`APPROVED: ${counts.approved.length}`}>
            <Box sx={{ flex: counts.approved.length / total, bgcolor: 'success.light', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="caption" sx={{ color: 'success.contrastText', fontWeight: 600 }}>
                {counts.approved.length}
              </Typography>
            </Box>
          </Tooltip>
        )}
        {counts.rejected.length > 0 && (
          <Tooltip title={`REJECTED: ${counts.rejected.length}`}>
            <Box sx={{ flex: counts.rejected.length / total, bgcolor: 'grey.400', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="caption" sx={{ fontWeight: 600 }}>
                {counts.rejected.length}
              </Typography>
            </Box>
          </Tooltip>
        )}
      </Stack>
      <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap' }}>
        <Chip label={`Draft: ${counts.draft.length}`} color="error" size="small" variant="outlined" />
        <Chip label={`In review: ${counts.review.length}`} color="warning" size="small" variant="outlined" />
        <Chip label={`Approved: ${counts.approved.length}`} color="success" size="small" variant="outlined" />
        <Chip label={`Rejected: ${counts.rejected.length}`} size="small" variant="outlined" />
      </Stack>
      {counts.review.length > 0 && (
        <Box>
          <Typography variant="caption" sx={{ fontWeight: 600, display: 'block', mb: 0.5 }}>
            Awaiting reviewer action ({counts.review.length}):
          </Typography>
          {counts.review.slice(0, 5).map((p) => (
            <Typography key={p.procedureId} variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              • {p.title} ({p.procedureId})
            </Typography>
          ))}
          {counts.review.length > 5 && (
            <Typography variant="caption" color="text.secondary">
              … and {counts.review.length - 5} more
            </Typography>
          )}
        </Box>
      )}
      <Alert severity="info" variant="outlined" icon={false}>
        <Typography variant="caption" sx={{ display: 'block' }}>
          <strong>Human-in-the-loop gate:</strong> No procedure is published to operators until a domain
          expert with <code>Knowledge.Publisher</code> role explicitly approves it. This ensures AI-extracted
          content is always validated before operational use.
        </Typography>
      </Alert>
    </Stack>
  )
}

// ─── Main Screen ──────────────────────────────────────────────────────────────

export function KnowledgeHub() {
  const { client, context, emit, can } = useAnalytics()
  const tokens = useTokens()
  const [query, setQuery] = useState('')
  const debounced = useDebouncedValue(query, 250)
  const [createOpen, setCreateOpen] = useState(false)
  const [rejectTarget, setRejectTarget] = useState<ProcedureRow | null>(null)
  const [actionInProgress, setActionInProgress] = useState<string | null>(null)

  const knowledgeClient = useMemo(() => new KnowledgeClient(context), [context])

  const proceduresState = useResource(
    () => (debounced.trim() ? client.searchKnowledge(debounced) : client.getProcedures()),
    [client, debounced],
  )

  const procedures = proceduresState.data ?? []
  const coverage = useMemo(() => knowledgeCoverage(), [])

  const handleApprove = useCallback(async (procedure: ProcedureRow) => {
    if (!can('knowledge.publish')) return
    setActionInProgress(procedure.procedureId)
    try {
      await knowledgeClient.approve(procedure.procedureId, procedure.version)
      emit('toast', { severity: 'success', message: `Approved: ${procedure.title}` })
      proceduresState.reload()
    } catch (err) {
      emit('toast', { severity: 'error', message: err instanceof Error ? err.message : 'Approval failed' })
    } finally {
      setActionInProgress(null)
    }
  }, [knowledgeClient, can, emit, proceduresState])

  const handleSubmitForReview = useCallback(async (procedure: ProcedureRow) => {
    setActionInProgress(procedure.procedureId)
    try {
      await knowledgeClient.submitForReview(procedure.procedureId)
      emit('toast', { severity: 'success', message: `Submitted for review: ${procedure.title}` })
      proceduresState.reload()
    } catch (err) {
      emit('toast', { severity: 'error', message: err instanceof Error ? err.message : 'Submit failed' })
    } finally {
      setActionInProgress(null)
    }
  }, [knowledgeClient, emit, proceduresState])

  const handleSeedDemo = useCallback(async () => {
    try {
      const result = await knowledgeClient.seedDemo()
      emit('toast', { severity: 'success', message: `Seeded ${result.seeded} sample procedures across multiple domains` })
      proceduresState.reload()
    } catch (err) {
      emit('toast', { severity: 'error', message: err instanceof Error ? err.message : 'Seed failed' })
    }
  }, [knowledgeClient, emit, proceduresState])

  const handleResetDemo = useCallback(async () => {
    try {
      const result = await knowledgeClient.resetDemo()
      emit('toast', { severity: 'info', message: `Demo reset — ${result.procedureCount} baseline procedures remain` })
      proceduresState.reload()
    } catch (err) {
      emit('toast', { severity: 'error', message: err instanceof Error ? err.message : 'Reset failed' })
    }
  }, [knowledgeClient, emit, proceduresState])

  const metrics: KpiCardModel[] = [
    { id: 'approved', label: 'Approved procedures', value: String(procedures.filter((row) => row.status === 'APPROVED').length), target: 'published only', asOf: proceduresState.asOf, source: proceduresState.source, tooltip: 'Count of procedures in APPROVED status—reviewed by a domain expert and published to the knowledge library. Only approved procedures are surfaced to operators during production.', actionHint: 'the procedure cards', onClick: () => revealPanel('knowledge-procedures') },
    { id: 'review', label: 'In review', value: String(procedures.filter((row) => row.status === 'IN_REVIEW').length), trend: 'up', goodDirection: 'up', target: 'publisher action', tooltip: 'Count of procedures currently in IN_REVIEW status, awaiting expert sign-off before publication. Users with the knowledge.publish capability can approve directly from the procedure card.', actionHint: 'the procedure cards', onClick: () => revealPanel('knowledge-procedures') },
    { id: 'coverage', label: 'Coverage', value: String(Math.round(coverage.reduce((sum, item) => sum + item.coveragePct, 0) / coverage.length)), unit: '%', trend: 'up', goodDirection: 'up', target: 'target 80%', tooltip: 'Average knowledge-capture completeness across all operational domains, each targeting 80%. Computed from the fixture-derived domain coverage matrix.', actionHint: 'the capture completeness chart', onClick: () => revealPanel('capture-completeness') },
    { id: 'sessions', label: 'Capture sessions', value: String(procedures.filter((row) => row.status === 'DRAFT').length), target: 'consent-bound', trend: 'flat', tooltip: 'Number of entries in DRAFT status awaiting review submission. Sessions are consent-bound and progress through speech-to-text, DRAFT review, and expert approval before publication.', actionHint: 'the workflow pipeline', onClick: () => revealPanel('capture-pipeline') },
  ]

  const columns: DataTableColumn<ProcedureRow>[] = [
    { key: 'title', label: 'Title', type: 'text' },
    { key: 'sessionId', label: 'Session', type: 'text' },
    { key: 'observation', label: 'Observation', type: 'text' },
    { key: 'status', label: 'Review status', type: 'enum', render: (row) => <SeverityPill severity={statusSeverity(row.status)} label={row.status} /> },
    { key: 'version', label: 'Version', type: 'number', align: 'right' },
  ]

  return (
    <>
    <SectionStack>
      <KpiBand metrics={metrics} />
      <TextField
        fullWidth
        data-dock-id="knowledge-search"
        data-dock-title="Search"
        data-dock-height={110}
        data-help="knowledge:search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search procedures & captured expertise…"
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          },
          htmlInput: { 'aria-label': 'Search procedures and captured expertise' },
        }}
      />
      <TwoColumn
        main={
          <PanelCard
            id="knowledge-procedures"
            title="Procedure cards"
            action={
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <ProofBadges ids={['CHL-05', 'OBJ-04', 'AI-03']} />
                <Button size="small" variant="contained" startIcon={<NoteAddIcon />} onClick={() => setCreateOpen(true)} data-help="knowledge:createEntry">
                  New entry
                </Button>
                <Button size="small" variant="outlined" startIcon={<ScienceIcon />} onClick={handleSeedDemo} data-help="knowledge:demoSeed">
                  Seed samples
                </Button>
                <Button size="small" variant="outlined" color="warning" startIcon={<RestartAltIcon />} onClick={handleResetDemo} data-help="knowledge:demoReset">
                  Reset demo
                </Button>
              </Stack>
            }
          >
            <StateBoundary state={proceduresState} isEmpty={(rows) => rows.length === 0} emptyMessage="No procedures match your search.">
              {(rows) => (
                <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))' }}>
                  {rows.map((procedure) => (
                    <Card key={procedure.procedureId} variant="outlined" sx={{ opacity: actionInProgress === procedure.procedureId ? 0.6 : 1 }}>
                      <CardContent>
                        <Stack direction="row" spacing={1} sx={{ mb: 1, flexWrap: 'wrap' }}>
                          <SeverityPill severity={statusSeverity(procedure.status)} label={procedure.status} />
                          <Chip size="small" variant="outlined" label={`v${procedure.version}`} />
                          <Chip size="small" variant="outlined" label="source: interview" />
                        </Stack>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                          {procedure.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, mb: 1 }}>
                          {procedure.observation}
                        </Typography>
                        <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
                          {procedure.status === 'DRAFT' && (
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<SendIcon />}
                              disabled={actionInProgress === procedure.procedureId}
                              onClick={() => handleSubmitForReview(procedure)}
                            >
                              Submit for review
                            </Button>
                          )}
                          {procedure.status === 'IN_REVIEW' && (
                            <Stack direction="row" spacing={1} data-help="knowledge:reviewAction">
                              <Tooltip title={can('knowledge.publish') ? 'Approve and publish this procedure' : 'Requires Knowledge.Publisher role'}>
                                <span>
                                  <Button
                                    size="small"
                                    variant="contained"
                                    color="success"
                                    startIcon={<CheckCircleIcon />}
                                    disabled={!can('knowledge.publish') || actionInProgress === procedure.procedureId}
                                    onClick={() => handleApprove(procedure)}
                                  >
                                    Approve
                                  </Button>
                                </span>
                              </Tooltip>
                              <Tooltip title={can('knowledge.publish') ? 'Reject with a reason' : 'Requires Knowledge.Publisher role'}>
                                <span>
                                  <Button
                                    size="small"
                                    variant="outlined"
                                    color="error"
                                    startIcon={<CancelIcon />}
                                    disabled={!can('knowledge.publish') || actionInProgress === procedure.procedureId}
                                    onClick={() => setRejectTarget(procedure)}
                                  >
                                    Reject
                                  </Button>
                                </span>
                              </Tooltip>
                            </Stack>
                          )}
                        </Stack>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
            </StateBoundary>
          </PanelCard>
        }
        side={
          <Stack spacing={2}>
            <PanelCard id="capture-completeness" title="Capture completeness">
              <ProgressBullet
                items={coverage.map((item, index) => ({
                  label: item.domain,
                  value: item.coveragePct,
                  target: 80,
                  color: tokens.palette[index % tokens.palette.length],
                }))}
              />
            </PanelCard>
            <PanelCard id="capture-pipeline" title="Workflow pipeline">
              <PipelineView procedures={procedures} />
            </PanelCard>
          </Stack>
        }
      />
      <PanelCard title="Procedures table">
        <StateBoundary state={proceduresState} isEmpty={(rows) => rows.length === 0}>
          {(rows) => (
            <DataTable
              caption="Knowledge procedures library"
              rows={rows}
              columns={columns}
              getRowId={(row) => row.procedureId}
              defaultSort={[{ key: 'title', direction: 'asc' }]}
              exportFileName="novasteel-procedures"
              onRefresh={proceduresState.reload}
            />
          )}
        </StateBoundary>
      </PanelCard>
    </SectionStack>
      <CreateEntryDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => proceduresState.reload()}
        knowledgeClient={knowledgeClient}
        emit={emit}
      />
      <RejectDialog
        open={rejectTarget !== null}
        procedure={rejectTarget}
        onClose={() => setRejectTarget(null)}
        onRejected={() => proceduresState.reload()}
        knowledgeClient={knowledgeClient}
        emit={emit}
      />
    </>
  )
}
