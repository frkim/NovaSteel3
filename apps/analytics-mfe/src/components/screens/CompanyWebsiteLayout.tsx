import { Box, Container, Divider, Link, Stack, Typography } from '@mui/material'
import type { ReactNode } from 'react'
import { useAnalytics } from '../../context/analytics'
import { DockedContext } from '../dock/dockContext'
import type { DockAwareComponent } from '../dock/dockTypes'
import { SectionStack } from './common'

/**
 * The body of a corporate website page, as seen by the dock collector.
 *
 * It claims the whole page as one panel so the collector stops here: a
 * marketing page contains ordinary cards that are part of the article, not
 * workspace panels an operator should be able to tear off. Resetting the docked
 * context keeps those cards rendering their normal chrome.
 */
function WebsiteBody({ children }: { id: string; title: string; dockBleed?: boolean; children: ReactNode }) {
  return <DockedContext.Provider value={false}>{children}</DockedContext.Provider>
}
;(WebsiteBody as DockAwareComponent).dockRole = 'panel'

/**
 * Docks a corporate website page as a single, full-bleed, non-closable panel.
 *
 * Operational screens split into several panels an operator can rearrange; a
 * marketing page has no such seams — separating the hero from the body would
 * read as a broken site rather than a flexible workspace. Wrapping it in the
 * same dock keeps the workspace consistent (every screen is a Dockview grid,
 * every tab is meaningful) while `dockBleed` removes the panel inset so the
 * hero still runs edge to edge.
 */
export function WebsitePage({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <SectionStack>
      <WebsiteBody id={id} title={title} dockBleed>
        {children}
      </WebsiteBody>
    </SectionStack>
  )
}

/**
 * Reusable footer strip for all AxelorMetal corporate website screens.
 * Uses the analytics context for translations; rendered inside the
 * AnalyticsContext.Provider so useAnalytics() is safe to call here.
 */
export function WebsiteFooter() {
  const { t } = useAnalytics()
  return (
    <Box
      component="footer"
      sx={{
        mt: 10,
        bgcolor: 'grey.900',
        color: 'grey.100',
        py: 5,
        px: 2,
      }}
    >
      <Container maxWidth="lg">
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ alignItems: { sm: 'center' }, mb: 3 }}>
          <Box
            component="img"
            src="/brand/axelormetal-logo-full.png"
            alt="AxelorMetal"
            height={40}
            sx={{ mr: 3, width: 'auto' }}
            onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
              e.currentTarget.style.display = 'none'
            }}
          />
          <Typography variant="body2" sx={{ color: 'grey.400' }}>
            {t('website.footer.copyright')}
          </Typography>
        </Stack>
        <Divider sx={{ borderColor: 'grey.700', mb: 3 }} />
        <Typography variant="caption" sx={{ color: 'grey.500', display: 'block', mb: 1 }}>
          {t('website.footer.disclaimer')}
        </Typography>
        <Stack direction="row" spacing={3} sx={{ flexWrap: 'wrap' }}>
          <Link href="#" underline="hover" sx={{ color: 'grey.500', fontSize: '0.75rem' }}>
            Privacy Policy
          </Link>
          <Link href="#" underline="hover" sx={{ color: 'grey.500', fontSize: '0.75rem' }}>
            Terms of Use
          </Link>
          <Link href="#" underline="hover" sx={{ color: 'grey.500', fontSize: '0.75rem' }}>
            Cookie Policy
          </Link>
        </Stack>
      </Container>
    </Box>
  )
}
