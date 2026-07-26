import { Box, Button, Card, CardContent, Stack, Typography } from '@mui/material'
import AssessmentIcon from '@mui/icons-material/Assessment'
import { useAnalytics } from '../../context/analytics'
import { useResource } from '../../hooks/useResource'
import { SeverityPill } from '../primitives/SeverityPill'
import { PanelCard, SectionStack } from './common'

/**
 * Optional Power BI "Board Report" placeholder (§14.4). Embedding requires a
 * running Fabric capacity and a BFF-mediated user-owned-data token; until that
 * is provisioned the tab shows a capacity-aware placeholder with a shortcut to
 * the capacity control, and never leaks a service credential to the browser.
 */
export function ExecutivePowerBi() {
  const { client, emit, site } = useAnalytics()
  const capacityState = useResource(() => client.getCapacity(), [client])
  const running = capacityState.data?.state === 'Running'

  return (
    <SectionStack>
      <PanelCard title="Board report (Power BI Embedded)">
        <Card
          variant="outlined"
          sx={{
            minHeight: 360,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundImage:
              'repeating-linear-gradient(45deg, transparent, transparent 12px, rgba(128,128,128,0.06) 12px, rgba(128,128,128,0.06) 24px)',
          }}
        >
          <CardContent>
            <Stack spacing={2} sx={{ alignItems: 'center', textAlign: 'center', maxWidth: 460 }}>
              <AssessmentIcon sx={{ fontSize: 48 }} color="disabled" aria-hidden />
              <Typography variant="h3">Paginated board report</Typography>
              <Box>
                <SeverityPill
                  severity={running ? 'INFO' : 'WARNING'}
                  label={running ? 'Capacity Running — ready to embed' : `Capacity ${capacityState.data?.state ?? 'unknown'} — start required`}
                />
              </Box>
              <Typography variant="body2" color="text.secondary">
                Finance-grade paginated reporting embeds here for internal Entra users. The BFF mediates the
                user-owned-data token flow and syncs a Power BI theme from the design tokens; no service
                credential reaches the browser.
              </Typography>
              {!running && (
                <Button variant="contained" onClick={() => emit('nav.intent', { route: `/${site}/platform-ops/capacity` })}>
                  Open capacity control
                </Button>
              )}
            </Stack>
          </CardContent>
        </Card>
      </PanelCard>
    </SectionStack>
  )
}
