import { useMemo } from 'react'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { usePolling } from '../../hooks/usePolling'
import { jobs as jobFixture } from '../../api/fixtures'
import type { Loaded } from '../../api/dataClient'
import { SeverityPill } from '../primitives/SeverityPill'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { FreshnessBadge } from '../primitives/FreshnessBadge'
import { PanelCard, SectionStack } from './common'
import { formatDateTime } from '../../utils/format'

interface JobRow {
  runId: string
  pipeline: string
  status: string
  startedAt: string
  durationSec: number
  actor: string
}

export function PlatformJobs() {
  const { locale } = useAnalytics()
  // Jobs are synthetic platform telemetry; refresh re-reads the deterministic set.
  const jobsState = useResource(
    () => Promise.resolve<Loaded<JobRow[]>>({ value: jobFixture(), source: 'fixture', asOf: new Date().toISOString() }),
    [],
  )
  usePolling(jobsState.reload, 12000)

  const columns: DataTableColumn<JobRow>[] = useMemo(
    () => [
      { key: 'runId', label: 'Run id', type: 'text' },
      { key: 'pipeline', label: 'Pipeline', type: 'text' },
      { key: 'status', label: 'Status', type: 'enum', render: (row) => <SeverityPill severity={row.status === 'RUNNING' ? 'WARNING' : row.status === 'FAILED' ? 'CRITICAL' : 'INFO'} label={row.status} /> },
      { key: 'startedAt', label: 'Started', type: 'date', render: (row) => formatDateTime(row.startedAt, locale) },
      { key: 'durationSec', label: 'Duration (s)', type: 'number', align: 'right' },
      { key: 'actor', label: 'Actor', type: 'text' },
    ],
    [locale],
  )

  return (
    <SectionStack>
      <PanelCard
        title="Jobs & pipelines"
        action={<FreshnessBadge asOf={jobsState.asOf} source={jobsState.source} />}
      >
        <DataTable
          caption="Platform jobs and pipeline runs"
          rows={jobsState.data ?? []}
          columns={columns}
          getRowId={(row) => row.runId}
          defaultSort={[{ key: 'startedAt', direction: 'desc' }]}
          exportFileName="novasteel-jobs"
          onRefresh={jobsState.reload}
        />
      </PanelCard>
    </SectionStack>
  )
}
