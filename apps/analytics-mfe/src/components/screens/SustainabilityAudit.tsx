import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import type { AuditRow } from '../../api/domain'
import { StateBoundary } from '../primitives/StateBoundary'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { KpiBand, PanelCard, SectionStack } from './common'
import { formatDateTime } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'

export function SustainabilityAudit() {
  const { client, locale } = useAnalytics()
  const auditState = useResource(() => client.getAudit(), [client])

  const rows = auditState.data ?? []
  const metrics: KpiCardModel[] = [
    { id: 'records', label: 'Decision records', value: String(rows.length), target: 'append-only', asOf: auditState.asOf, source: auditState.source },
    { id: 'domains', label: 'Domains covered', value: String(new Set(rows.map((row) => row.domain)).size), target: 'energy, furnace, quality…' },
    { id: 'models', label: 'Model-linked', value: String(rows.filter((row) => row.modelVersion).length), target: 'input→model→decision' },
    { id: 'immutable', label: 'Immutability', value: '100%', trend: 'flat', target: 'no inline edit' },
  ]

  const columns: DataTableColumn<AuditRow>[] = [
    { key: 'recordedAt', label: 'Time', type: 'date', render: (row) => formatDateTime(row.recordedAt, locale) },
    { key: 'actor', label: 'Actor', type: 'text' },
    { key: 'action', label: 'Action', type: 'text' },
    { key: 'domain', label: 'Domain', type: 'enum' },
    { key: 'entityId', label: 'Entity', type: 'text' },
    { key: 'modelVersion', label: 'Model version', type: 'text' },
    { key: 'correlationId', label: 'Correlation', type: 'text' },
    { key: 'auditId', label: 'Audit ref', type: 'text' },
  ]

  return (
    <SectionStack>
      <KpiBand metrics={metrics} />
      <PanelCard title="Audit & decision evidence (read-only)">
        <StateBoundary state={auditState} isEmpty={(data) => data.length === 0}>
          {(data) => (
            <DataTable
              caption="Append-only audit decision records — read-only with per-column search and export"
              rows={data}
              columns={columns}
              getRowId={(row) => row.auditId}
              defaultSort={[{ key: 'recordedAt', direction: 'desc' }]}
              exportFileName="novasteel-audit-decisions"
              onRefresh={auditState.reload}
            />
          )}
        </StateBoundary>
      </PanelCard>
    </SectionStack>
  )
}
