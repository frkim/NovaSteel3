import { useMemo, useState } from 'react'
import {
  Box,
  Button,
  Chip,
  Divider,
  Drawer,
  IconButton,
  Slider,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { useTokens } from '../../hooks/useTokens'
import type { QualityBatchRow } from '../../api/domain'
import { StateBoundary } from '../primitives/StateBoundary'
import { ConfidenceMeter } from '../primitives/ConfidenceMeter'
import { SeverityPill } from '../primitives/SeverityPill'
import { formatNumber } from '../../utils/format'

export interface QualityBatchDrawerProps {
  batch: QualityBatchRow | null
  onClose: () => void
}

const CHAIN_ORDER: Array<{ key: string; label: string }> = [
  { key: 'rawMaterialLots', label: 'Raw material lots' },
  { key: 'heat', label: 'Heat' },
  { key: 'ladleTreatment', label: 'Ladle treatment' },
  { key: 'slab', label: 'Slab' },
  { key: 'reheating', label: 'Reheating' },
  { key: 'coil', label: 'Coil' },
  { key: 'sample', label: 'Sample' },
  { key: 'shipment', label: 'Shipment' },
]

export function QualityBatchDrawer({ batch, onClose }: QualityBatchDrawerProps) {
  const { client, emit, locale, can } = useAnalytics()
  const tokens = useTokens()
  const [coilingDelta, setCoilingDelta] = useState(-8)
  const [forceDelta, setForceDelta] = useState(-3)
  const [labelMode, setLabelMode] = useState<'predicted' | 'measured'>('predicted')

  const batchId = batch?.batchId ?? ''
  const genealogyState = useResource(() => client.getGenealogy(batchId), [client, batchId])

  const pendingAdjustments = useMemo(
    () => ({ coilingTempDeltaC: coilingDelta, forceBalanceDeltaPct: forceDelta }),
    [coilingDelta, forceDelta],
  )
  const adjustments = useDebouncedValue(pendingAdjustments, 250)
  const whatIfState = useResource(() => client.qualityWhatIf(batchId, adjustments), [client, batchId, adjustments])

  const chainRows = useMemo(() => {
    const chain = genealogyState.data?.chain
    if (!chain) {
      return []
    }
    const record = chain as unknown as Record<string, unknown>
    return CHAIN_ORDER.map((step) => {
      const value = record[step.key]
      let display: string
      if (Array.isArray(value)) {
        display = value.join(', ')
      } else if (value && typeof value === 'object' && 'operation' in (value as Record<string, unknown>)) {
        display = String((value as Record<string, unknown>).operation)
      } else {
        display = String(value ?? '—')
      }
      return { label: step.label, value: display }
    })
  }, [genealogyState.data])

  return (
    <Drawer anchor="right" open={Boolean(batch)} onClose={onClose} slotProps={{ paper: { sx: { width: { xs: '100%', sm: 460 } } } }}>
      {batch && (
        <Box sx={{ p: 2 }} role="region" aria-label={`Batch ${batch.batchId} detail`}>
          <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h3">{batch.batchId}</Typography>
            <IconButton aria-label="Close batch detail" onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Stack>
          <Stack direction="row" spacing={1} sx={{ my: 1, flexWrap: 'wrap' }}>
            <Chip size="small" label={batch.grade} />
            <SeverityPill severity={batch.resultStatus === 'FAIL' ? 'CRITICAL' : batch.resultStatus === 'REVIEW' ? 'WARNING' : 'INFO'} label={batch.resultStatus} />
            <Chip size="small" variant="outlined" label={`Bias ${batch.coilingTempBiasC} °C`} />
          </Stack>

          <Typography variant="h6" sx={{ mt: 2 }}>
            Genealogy
          </Typography>
          <StateBoundary state={genealogyState}>
            {() => (
              <Stack spacing={0.5} sx={{ mt: 1 }}>
                {chainRows.map((row) => (
                  <Stack key={row.label} direction="row" sx={{ justifyContent: 'space-between', gap: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      {row.label}
                    </Typography>
                    <Typography variant="caption" sx={{ fontWeight: 600, textAlign: 'right' }}>
                      {row.value}
                    </Typography>
                  </Stack>
                ))}
              </Stack>
            )}
          </StateBoundary>

          <Divider sx={{ my: 2 }} />

          <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Bounded what-if</Typography>
            <ToggleButtonGroup
              size="small"
              exclusive
              value={labelMode}
              onChange={(_, value) => value && setLabelMode(value)}
              aria-label="Predicted or measured labels"
            >
              <ToggleButton value="predicted">Predicted</ToggleButton>
              <ToggleButton value="measured">Measured</ToggleButton>
            </ToggleButtonGroup>
          </Stack>

          <Box sx={{ mt: 1 }}>
            <Typography id="coiling-delta" gutterBottom variant="body2">
              Coiling temperature Δ: {coilingDelta} °C
            </Typography>
            <Slider aria-labelledby="coiling-delta" value={coilingDelta} min={-20} max={20} step={1} onChange={(_, value) => setCoilingDelta(value as number)} valueLabelDisplay="auto" />
            <Typography id="force-delta" gutterBottom variant="body2">
              Force balance Δ: {forceDelta}%
            </Typography>
            <Slider aria-labelledby="force-delta" value={forceDelta} min={-10} max={10} step={1} onChange={(_, value) => setForceDelta(value as number)} valueLabelDisplay="auto" />
          </Box>

          <StateBoundary state={whatIfState}>
            {(whatIf) => (
              <Box sx={{ mt: 1 }}>
                {labelMode === 'predicted' ? (
                  <>
                    <Stack direction="row" spacing={2} sx={{ alignItems: 'baseline' }}>
                      <Typography variant="body2" color="text.secondary">
                        {formatNumber(whatIf.current.predictedFirstPassYieldPct, locale)}%
                      </Typography>
                      <Typography aria-hidden>→</Typography>
                      <Typography variant="h4" sx={{ color: tokens.status.success }}>
                        {formatNumber(whatIf.proposed.predictedFirstPassYieldPct, locale)}%
                      </Typography>
                    </Stack>
                    <Typography variant="caption" color="text.secondary">
                      Predicted first-pass yield · {whatIf.modelVersion}
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      <ConfidenceMeter band={whatIf.confidence} unit="%" label="Predicted yield (P10–P90)" />
                    </Box>
                  </>
                ) : (
                  <Typography variant="body2">
                    Measured lab result: <strong>{batch.value} {batch.unit}</strong> · status {batch.resultStatus}. No setpoint or recipe is written.
                  </Typography>
                )}
              </Box>
            )}
          </StateBoundary>

          <Button
            sx={{ mt: 2 }}
            variant="outlined"
            fullWidth
            disabled={!can('quality.whatIf')}
            onClick={() => emit('toast', { severity: 'info', message: `Recorded synthetic what-if for ${batch.batchId}. No recipe changed.` })}
          >
            Record synthetic what-if
          </Button>
        </Box>
      )}
    </Drawer>
  )
}
