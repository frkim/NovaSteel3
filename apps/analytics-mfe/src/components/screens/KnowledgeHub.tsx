import { useMemo, useState } from 'react'
import { Box, Button, Card, CardContent, Chip, InputAdornment, Stack, TextField, Typography } from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { useTokens } from '../../hooks/useTokens'
import type { ProcedureRow } from '../../api/domain'
import { knowledgeCoverage } from '../../api/fixtures'
import { StateBoundary } from '../primitives/StateBoundary'
import { SeverityPill } from '../primitives/SeverityPill'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { ProgressBullet } from '../charts/ProgressBullet'
import { KpiBand, PanelCard, SectionStack, TwoColumn } from './common'
import type { KpiCardModel } from '../primitives/KpiCard'

function statusSeverity(status: string): string {
  if (status === 'APPROVED') {
    return 'INFO'
  }
  if (status === 'IN_REVIEW') {
    return 'WARNING'
  }
  return 'CRITICAL'
}

export function KnowledgeHub() {
  const { client, emit, can } = useAnalytics()
  const tokens = useTokens()
  const [query, setQuery] = useState('')
  const debounced = useDebouncedValue(query, 250)

  const proceduresState = useResource(
    () => (debounced.trim() ? client.searchKnowledge(debounced) : client.getProcedures()),
    [client, debounced],
  )

  const procedures = proceduresState.data ?? []
  const coverage = useMemo(() => knowledgeCoverage(), [])

  const metrics: KpiCardModel[] = [
    { id: 'approved', label: 'Approved procedures', value: String(procedures.filter((row) => row.status === 'APPROVED').length), target: 'published only', asOf: proceduresState.asOf, source: proceduresState.source },
    { id: 'review', label: 'In review', value: String(procedures.filter((row) => row.status === 'IN_REVIEW').length), trend: 'up', goodDirection: 'up', target: 'publisher action' },
    { id: 'coverage', label: 'Coverage', value: String(Math.round(coverage.reduce((sum, item) => sum + item.coveragePct, 0) / coverage.length)), unit: '%', trend: 'up', goodDirection: 'up', target: 'target 80%' },
    { id: 'sessions', label: 'Capture sessions', value: '3', target: 'consent-bound', trend: 'flat' },
  ]

  const columns: DataTableColumn<ProcedureRow>[] = [
    { key: 'title', label: 'Title', type: 'text' },
    { key: 'sessionId', label: 'Session', type: 'text' },
    { key: 'observation', label: 'Observation', type: 'text' },
    { key: 'status', label: 'Review status', type: 'enum', render: (row) => <SeverityPill severity={statusSeverity(row.status)} label={row.status} /> },
    { key: 'version', label: 'Version', type: 'number', align: 'right' },
  ]

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />
      <TextField
        fullWidth
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
          <PanelCard title="Procedure cards">
            <StateBoundary state={proceduresState} isEmpty={(rows) => rows.length === 0} emptyMessage="No procedures match your search.">
              {(rows) => (
                <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))' }}>
                  {rows.map((procedure) => (
                    <Card key={procedure.procedureId} variant="outlined">
                      <CardContent>
                        <Stack direction="row" spacing={1} sx={{ mb: 1, flexWrap: 'wrap' }}>
                          <SeverityPill severity={statusSeverity(procedure.status)} label={procedure.status} />
                          <Chip size="small" variant="outlined" label="source: interview" />
                        </Stack>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                          {procedure.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                          {procedure.observation}
                        </Typography>
                        {procedure.status === 'IN_REVIEW' && (
                          <Button
                            size="small"
                            variant="contained"
                            sx={{ mt: 1 }}
                            disabled={!can('knowledge.publish')}
                            onClick={() =>
                              emit('toast', {
                                severity: 'success',
                                message: `Approval submitted for ${procedure.procedureId} (reviewer boundary enforced by the BFF).`,
                              })
                            }
                          >
                            Approve & publish
                          </Button>
                        )}
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
            <PanelCard title="Capture completeness">
              <ProgressBullet
                items={coverage.map((item, index) => ({
                  label: item.domain,
                  value: item.coveragePct,
                  target: 80,
                  color: tokens.palette[index % tokens.palette.length],
                }))}
              />
            </PanelCard>
            <PanelCard title="Interview capture status">
              <Stack spacing={1}>
                {[
                  { id: 'OP-DEMO-014', status: 'Transcript ready · DRAFT — expert review required', tone: 'WARNING' },
                  { id: 'OP-DEMO-015', status: 'Approved & published', tone: 'INFO' },
                  { id: 'OP-DEMO-016', status: 'Processing STT…', tone: 'INFO' },
                ].map((session) => (
                  <Stack key={session.id} direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                    <SeverityPill severity={session.tone} label={session.id} />
                    <Typography variant="caption" color="text.secondary">
                      {session.status}
                    </Typography>
                  </Stack>
                ))}
              </Stack>
            </PanelCard>
          </Stack>
        }
      />
      <PanelCard title="Procedures">
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
  )
}
