import { useId, useState, type MouseEvent } from 'react'
import { Box, IconButton, Popover, Stack, Typography } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import type { TranslateFn } from '../../i18n/messages'
import { isFrenchFirst, resolveHelpCatalog } from '../../i18n/helpCatalogs'
import { BilingualText } from './BilingualText'

const POPUP_WIDTH = 420
/** Two languages sit side by side, so the popup needs room for both columns. */
const POPUP_WIDTH_BILINGUAL = 760

export interface SectionInsightProps {
  /** Section id from `personaRoutes`; the topic is `section:<id>`. */
  section: string
  locale: string
  /** Show English and French together, from the shell settings dialog. */
  bilingual?: boolean
  t: TranslateFn
}

/**
 * Info affordance next to a screen title. It opens the same explanation popup
 * the Help Assistant uses — bilingual when the shell asks for it, dismissed
 * with Esc — but scoped to the screen as a whole rather than to one control,
 * so it answers "what is this screen for?" instead of "what is this number?".
 *
 * Renders nothing for a section with no `section:` topic, which keeps the
 * affordance off screens that have no business narrative to tell.
 */
export function SectionInsight({ section, locale, bilingual = false, t }: SectionInsightProps) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null)
  const id = useId()

  const topic = resolveHelpCatalog(locale, bilingual)[`section:${section}`]
  if (!topic) return null

  const open = Boolean(anchor)
  const frenchFirst = isFrenchFirst(locale)
  const width = bilingual ? POPUP_WIDTH_BILINGUAL : POPUP_WIDTH

  return (
    <>
      <IconButton
        size="small"
        aria-label={t('help.insight.open')}
        aria-describedby={open ? id : undefined}
        aria-expanded={open}
        title={t('help.insight.open')}
        data-testid="section-insight-toggle"
        data-help-surface=""
        onClick={(event: MouseEvent<HTMLButtonElement>) => setAnchor(event.currentTarget)}
      >
        <InfoOutlinedIcon fontSize="small" />
      </IconButton>

      <Popover
        id={id}
        open={open}
        anchorEl={anchor}
        onClose={() => setAnchor(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        slotProps={{
          paper: {
            elevation: 12,
            sx: {
              width,
              maxWidth: 'calc(100vw - 24px)',
              maxHeight: '70vh',
              overflowY: 'auto',
            },
          },
        }}
      >
        <Box
          role="dialog"
          aria-label={t('help.popup.label')}
          // Explain mode must not swallow clicks inside an open explanation.
          data-help-surface=""
          data-testid="section-insight-popup"
          data-help-topic={`section:${section}`}
          sx={{ p: 2 }}
        >
          <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start', mb: 1 }}>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <BilingualText
                text={topic.title}
                bilingual={bilingual}
                frenchFirst={frenchFirst}
                variant="subtitle1"
                component="h2"
                sx={{ fontWeight: 700, m: 0 }}
              />
            </Box>
            <IconButton
              size="small"
              aria-label={t('help.popup.close')}
              data-testid="section-insight-close"
              onClick={() => setAnchor(null)}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </Stack>

          <Box sx={{ mb: topic.steel || topic.useIt ? 1.5 : 0 }}>
            <BilingualText text={topic.what} bilingual={bilingual} frenchFirst={frenchFirst} />
          </Box>

          {topic.steel && (
            <>
              <Typography variant="overline" sx={{ display: 'block', lineHeight: 1.6, color: 'primary.main' }}>
                {t('help.section.steel')}
              </Typography>
              <Box sx={{ mb: 1.5 }}>
                <BilingualText text={topic.steel} bilingual={bilingual} frenchFirst={frenchFirst} />
              </Box>
            </>
          )}

          {topic.useIt && (
            <>
              <Typography variant="overline" sx={{ display: 'block', lineHeight: 1.6, color: 'primary.main' }}>
                {t('help.section.useIt')}
              </Typography>
              <BilingualText text={topic.useIt} bilingual={bilingual} frenchFirst={frenchFirst} />
            </>
          )}

          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            {t('help.insight.hint')}
          </Typography>
        </Box>
      </Popover>
    </>
  )
}
