import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import type { AuditRow } from '../../api/domain'
import { StateBoundary } from '../primitives/StateBoundary'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { KpiBand, PanelCard, SectionStack, revealPanel } from './common'
import { formatDateTime } from '../../utils/format'
import type { KpiCardModel } from '../primitives/KpiCard'
import { ProofBadges } from '../primitives/ProofBadge'

export function SustainabilityAudit() {
  const { client, locale } = useAnalytics()
  const auditState = useResource(() => client.getAudit(), [client])

  const rows = auditState.data ?? []
  const metrics: KpiCardModel[] = [
    { id: 'records', label: 'Decision records', value: String(rows.length), target: 'append-only', asOf: auditState.asOf, source: auditState.source, tooltip: 'Total count of immutable AI decision records logged in the append-only audit store. Each record captures actor, action, domain, entity, and model version for full regulatory traceability.', actionHint: 'the audit evidence table', onClick: () => revealPanel('audit-evidence') },
    { id: 'domains', label: 'Domains covered', value: String(new Set(rows.map((row) => row.domain)).size), target: 'energy, furnace, quality…', tooltip: 'Number of distinct operational domains (e.g. energy, furnace, quality) that have at least one audited AI-assisted decision in the current log.', actionHint: 'the audit evidence table', onClick: () => revealPanel('audit-evidence') },
    { id: 'models', label: 'Model-linked', value: String(rows.filter((row) => row.modelVersion).length), target: 'input→model→decision', tooltip: 'Count of audit records that include a model version reference, enabling input → model → decision traceability. Records without a model version represent rule-based or human decisions.', actionHint: 'the audit evidence table', onClick: () => revealPanel('audit-evidence') },
    { id: 'immutable', label: 'Immutability', value: '100%', trend: 'flat', target: 'no inline edit', tooltip: 'Confirms that all audit records are append-only: the BFF API enforces no inline edit or delete. Records are written exactly once at the moment of decision and cannot be altered.' },
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
      <PanelCard
        id="audit-evidence"
        title="Audit & decision evidence (read-only)"
        action={<ProofBadges ids={['REG-01', 'REG-02']} />}
      >
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
