import { Alert, Box, Button, Stack, TextField, Typography } from '@mui/material'
import { useState } from 'react'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { usePolling } from '../../hooks/usePolling'
import { useTokens } from '../../hooks/useTokens'
import type { CapacityStatus, CapacityTransition } from '../../api/domain'
import { StateBoundary } from '../primitives/StateBoundary'
import { SeverityPill } from '../primitives/SeverityPill'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { KpiBand, PanelCard, SectionStack } from './common'
import { formatDateTime } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'

function stateSeverity(state: string): string {
  if (state === 'Running') {
    return 'INFO'
  }
  if (state === 'Failed') {
    return 'CRITICAL'
  }
  if (state === 'Paused') {
    return 'WARNING'
  }
  return 'WARNING'
}

const MUTATION_LOCK_STATES = new Set([
  'ResumeRequested',
  'Resuming',
  'ReadinessCheck',
  'DrainRequested',
  'Draining',
  'SuspendRequested',
])

export function PlatformCapacity() {
  const { client, emit, locale, can } = useAnalytics()
  const tokens = useTokens()
  const [reason, setReason] = useState('rehearsal readiness')
  const capacityState = useResource(() => client.getCapacity(), [client])
  usePolling(capacityState.reload, 10000)

  const transitions = client.capacityTransitions()
  const status = capacityState.data
  const locked = status ? MUTATION_LOCK_STATES.has(status.state) : true
  const canManage = can('platform.capacity.manage')

  const metrics: KpiCardModel[] = [
    { id: 'state', label: 'Capacity state', value: status?.state ?? '—', deltaLabel: status?.demoModeSimulated ? 'Simulated' : undefined, target: `SKU ${status?.sku ?? '—'}`, asOf: capacityState.asOf, source: capacityState.source },
    { id: 'sku', label: 'SKU', value: status?.sku ?? '—', target: 'non-production', trend: 'flat' },
    { id: 'env', label: 'Environment', value: status?.environment ?? '—', target: 'demo namespace', trend: 'flat' },
    { id: 'policy', label: 'Lifecycle policy', value: '01:00', unit: 'Europe/Luxembourg', target: 'non-production check', trend: 'flat' },
  ]

  const requestCapacity = (action: 'start' | 'pause') => {
    emit('capacity.request', { action, reason })
    emit('toast', { severity: 'info', message: `${action} request routed to the shell (BFF-mediated).` })
  }

  const columns: DataTableColumn<CapacityTransition>[] = [
    { key: 'recordedAt', label: 'Time', type: 'date', render: (row) => formatDateTime(row.recordedAt, locale) },
    { key: 'actor', label: 'Actor', type: 'text' },
    { key: 'fromState', label: 'From', type: 'text' },
    { key: 'toState', label: 'To', type: 'text' },
    { key: 'reason', label: 'Reason', type: 'text' },
    { key: 'correlationId', label: 'Correlation', type: 'text' },
  ]

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />

      {status?.demoModeSimulated && (
        <Alert severity="info" icon={false}>
          <strong>Simulated</strong> — capacity transitions are timed to look realistic; no real ARM operation fires in Demo Mode.
        </Alert>
      )}

      <StateBoundary state={capacityState}>
        {(capacity: CapacityStatus) => (
          <PanelCard
            title="Fabric capacity (read-only mirror)"
            action={<SeverityPill severity={stateSeverity(capacity.state)} label={capacity.state} />}
          >
            <Stack spacing={2}>
              <Typography variant="body2" color="text.secondary">
                The authoritative control lives in the shell top-bar capacity panel; this mirror requests
                non-production start/pause through the BFF only. No browser-to-ARM call or SKU scaling is possible.
              </Typography>
              <Box sx={{ display: 'grid', gap: 1, gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))' }}>
                <Typography variant="body2"><strong>Capacity:</strong> {capacity.capacityId}</Typography>
                <Typography variant="body2"><strong>Region:</strong> Sweden Central</Typography>
                <Typography variant="body2"><strong>Budget:</strong> within cap</Typography>
              </Box>
              <TextField
                label="Reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                size="small"
                fullWidth
                disabled={!canManage}
              />
              <Stack direction="row" spacing={1}>
                <Button
                  variant="contained"
                  disabled={!canManage || locked || capacity.state !== 'Paused'}
                  onClick={() => requestCapacity('start')}
                >
                  Request start
                </Button>
                <Button
                  variant="outlined"
                  color="warning"
                  disabled={!canManage || locked || capacity.state !== 'Running'}
                  onClick={() => requestCapacity('pause')}
                >
                  Request pause
                </Button>
              </Stack>
              {!canManage && (
                <Typography variant="caption" color="text.secondary">
                  Read-only: only Platform.Capacity.Manage may request start/pause. Request access in Settings.
                </Typography>
              )}
              {locked && (
                <Typography variant="caption" sx={{ color: tokens.status.warning }}>
                  A lifecycle operation is in progress ({capacity.state}); mutations are disabled until it settles.
                </Typography>
              )}
            </Stack>
          </PanelCard>
        )}
      </StateBoundary>

      <PanelCard title="Recent transitions">
        <DataTable
          caption="Capacity lifecycle transitions audit trail"
          rows={transitions}
          columns={columns}
          getRowId={(row) => `${row.recordedAt}-${row.toState}`}
          defaultSort={[{ key: 'recordedAt', direction: 'desc' }]}
          exportFileName="novasteel-capacity-transitions"
        />
      </PanelCard>
    </SectionStack>
  )
}
