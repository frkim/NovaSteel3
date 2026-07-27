import { Chip, Stack, Tooltip } from '@mui/material'
import { useAnalytics } from '../../context/analytics'
import { useTokens } from '../../hooks/useTokens'
import { PROOF_BY_ID, type ProofStatus } from '../../proof/proofCatalog'

export interface ProofBadgeProps {
  /** Reference ID from the use-case catalog, e.g. `OUT-03`. */
  id: string
  /** Render without the click-through (useful inside already-clickable rows). */
  static?: boolean
}

/**
 * Stamps a use-case reference ID onto the component that proves it.
 *
 * Clicking navigates to the Proof of execution screen, so any panel in the
 * application can be traced back to the line of the brief it answers.
 */
export function ProofBadge({ id, static: isStatic = false }: ProofBadgeProps) {
  const { emit, site, t } = useAnalytics()
  const tokens = useTokens()
  const requirement = PROOF_BY_ID[id]
  if (!requirement) return null

  const color = statusColor(requirement.status, tokens.status)
  const title = `${id} \u2014 ${requirement.statement}`

  return (
    <Tooltip title={title}>
      <Chip
        label={id}
        size="small"
        variant="outlined"
        aria-label={t('proof.badge.tooltip').replace('{id}', id)}
        onClick={
          isStatic
            ? undefined
            : () => emit('nav.intent', { route: `/${site}/proof-of-execution/requirements` })
        }
        sx={{
          height: 20,
          borderColor: color,
          color,
          fontSize: '0.65rem',
          fontWeight: 700,
          letterSpacing: '0.04em',
          cursor: isStatic ? 'default' : 'pointer',
          '& .MuiChip-label': { px: 0.75 },
        }}
      />
    </Tooltip>
  )
}

function statusColor(status: ProofStatus, palette: { success: string; warning: string; info: string }): string {
  if (status === 'met') return palette.success
  if (status === 'partial') return palette.warning
  return palette.info
}

/** Convenience wrapper for the common case of several reference IDs on one panel. */
export function ProofBadges({ ids }: { ids: string[] }) {
  return (
    <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center', flexWrap: 'wrap', gap: 0.5 }}>
      {ids.map((id) => (
        <ProofBadge key={id} id={id} />
      ))}
    </Stack>
  )
}
