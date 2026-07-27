import { useCallback, useEffect, useRef, useState } from 'react'
import { Box, GlobalStyles, IconButton, Paper, Stack, Typography } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import HelpOutlineIcon from '@mui/icons-material/HelpOutlined'
import type { TranslateFn } from '../../i18n/messages'
import { resolveHelpCatalog, isFrenchFirst } from '../../i18n/helpCatalogs'
import { BilingualText } from './BilingualText'
import { pickHelpKey, resolveHelpTarget } from './resolveHelpTarget'
import type { HelpTarget, HelpTopic } from './helpTypes'

const POPUP_WIDTH = 420
/** Two languages sit side by side, so the popup needs room for both columns. */
const POPUP_WIDTH_BILINGUAL = 760
const CURSOR_GAP = 18
const VIEWPORT_MARGIN = 12
const HELP_BODY_CLASS = 'novasteel-help-mode'

interface Selection {
  target: HelpTarget
  topic: HelpTopic | null
  key?: string
  point: { x: number; y: number }
}

interface Rect {
  top: number
  left: number
  width: number
  height: number
}

function rectOf(element: HTMLElement): Rect {
  const box = element.getBoundingClientRect()
  return { top: box.top, left: box.left, width: box.width, height: box.height }
}

/** Keeps the popup inside the viewport, flipping to the other side when needed. */
function placePopup(point: { x: number; y: number }, height: number, width: number) {
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  let left = point.x + CURSOR_GAP
  if (left + width + VIEWPORT_MARGIN > viewportWidth) {
    left = Math.max(VIEWPORT_MARGIN, point.x - CURSOR_GAP - width)
  }
  let top = point.y + CURSOR_GAP
  if (top + height + VIEWPORT_MARGIN > viewportHeight) {
    top = Math.max(VIEWPORT_MARGIN, viewportHeight - height - VIEWPORT_MARGIN)
  }
  return { top, left }
}

export interface HelpAssistantProps {
  active: boolean
  onExit: () => void
  /** `section/subView`, used to disambiguate metric ids shared between screens. */
  scope: string
  locale: string
  /** Show English and French together, from the shell settings dialog. */
  bilingual?: boolean
  t: TranslateFn
}

/**
 * Explain mode. While active, a click anywhere selects the element under the
 * pointer and describes it instead of triggering whatever that element
 * normally does.
 */
export function HelpAssistant({ active, onExit, scope, locale, bilingual = false, t }: HelpAssistantProps) {
  const [selection, setSelection] = useState<Selection | null>(null)
  const [frame, setFrame] = useState<Rect | null>(null)
  const popupRef = useRef<HTMLDivElement | null>(null)
  const [popupHeight, setPopupHeight] = useState(220)

  const clear = useCallback(() => {
    setSelection(null)
    setFrame(null)
  }, [])

  useEffect(() => {
    if (!active) clear()
  }, [active, clear])

  // Selecting a new screen must not leave a frame drawn over the old layout.
  useEffect(() => {
    clear()
  }, [scope, clear])

  useEffect(() => {
    if (!active) return undefined
    document.body.classList.add(HELP_BODY_CLASS)
    return () => document.body.classList.remove(HELP_BODY_CLASS)
  }, [active])

  useEffect(() => {
    if (!active) return undefined
    const catalog = resolveHelpCatalog(locale, bilingual)

    const onClick = (event: MouseEvent) => {
      const origin = event.target as HTMLElement | null
      if (origin?.closest('[data-help-surface]')) return
      // Swallow the click so a KPI tile explains itself instead of navigating.
      event.preventDefault()
      event.stopPropagation()

      const target = resolveHelpTarget(origin, scope)
      if (!target) {
        clear()
        return
      }
      const key = pickHelpKey(target.keys, catalog)
      setSelection({
        target,
        key,
        topic: key ? catalog[key] : null,
        point: { x: event.clientX, y: event.clientY },
      })
      setFrame(rectOf(target.element))
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        event.stopPropagation()
        onExit()
      }
    }

    window.addEventListener('click', onClick, true)
    window.addEventListener('keydown', onKeyDown, true)
    return () => {
      window.removeEventListener('click', onClick, true)
      window.removeEventListener('keydown', onKeyDown, true)
    }
  }, [active, scope, locale, bilingual, onExit, clear])

  // The frame is drawn in viewport coordinates, so it has to follow scrolling.
  useEffect(() => {
    if (!active || !selection) return undefined
    const reposition = () => {
      if (!selection.target.element.isConnected) {
        clear()
        return
      }
      setFrame(rectOf(selection.target.element))
    }
    window.addEventListener('scroll', reposition, true)
    window.addEventListener('resize', reposition)
    return () => {
      window.removeEventListener('scroll', reposition, true)
      window.removeEventListener('resize', reposition)
    }
  }, [active, selection, clear])

  useEffect(() => {
    if (popupRef.current) setPopupHeight(popupRef.current.offsetHeight)
  }, [selection])

  if (!active) return null

  const topic = selection?.topic
  const heading = selection?.target.label ?? topic?.title ?? t('help.fallback.title')
  // The label is read straight off the page, so it is only ever one language.
  const headingIsBilingual = bilingual && !selection?.target.label
  const frenchFirst = isFrenchFirst(locale)
  const popupWidth = bilingual ? POPUP_WIDTH_BILINGUAL : POPUP_WIDTH
  const position = selection ? placePopup(selection.point, popupHeight, popupWidth) : null

  return (
    <>
      <GlobalStyles
        styles={{
          [`body.${HELP_BODY_CLASS}, body.${HELP_BODY_CLASS} *`]: { cursor: 'help !important' },
          [`body.${HELP_BODY_CLASS} [data-help-surface], body.${HELP_BODY_CLASS} [data-help-surface] *`]: {
            cursor: 'auto !important',
          },
          [`body.${HELP_BODY_CLASS} [data-help-surface] button`]: { cursor: 'pointer !important' },
        }}
      />

      <Box
        data-testid="help-mode-banner"
        data-help-surface=""
        sx={{
          position: 'fixed',
          top: 12,
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: (theme) => theme.zIndex.tooltip + 20,
          px: 2,
          py: 0.75,
          borderRadius: 999,
          bgcolor: 'primary.main',
          color: 'primary.contrastText',
          boxShadow: 6,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <HelpOutlineIcon fontSize="small" />
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {t('help.mode.banner')}
        </Typography>
        <IconButton
          size="small"
          aria-label={t('help.mode.exit')}
          data-testid="help-mode-exit"
          onClick={onExit}
          sx={{ color: 'inherit' }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>

      {frame && (
        <Box
          data-testid="help-selection-frame"
          sx={{
            position: 'fixed',
            top: frame.top - 3,
            left: frame.left - 3,
            width: frame.width + 6,
            height: frame.height + 6,
            border: 2,
            borderColor: 'primary.main',
            borderRadius: 1.5,
            boxShadow: '0 0 0 9999px rgba(15, 23, 42, 0.28)',
            pointerEvents: 'none',
            zIndex: (theme) => theme.zIndex.tooltip + 10,
          }}
        />
      )}

      {selection && position && (
        <Paper
          ref={popupRef}
          elevation={12}
          data-help-surface=""
          data-testid="help-popup"
          data-help-topic={selection.key ?? 'none'}
          role="dialog"
          aria-label={t('help.popup.label')}
          sx={{
            position: 'fixed',
            top: position.top,
            left: position.left,
            width: popupWidth,
            maxWidth: `calc(100vw - ${VIEWPORT_MARGIN * 2}px)`,
            maxHeight: '70vh',
            overflowY: 'auto',
            p: 2,
            zIndex: (theme) => theme.zIndex.tooltip + 30,
          }}
        >
          <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start', mb: 1 }}>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <BilingualText
                text={heading}
                bilingual={headingIsBilingual}
                frenchFirst={frenchFirst}
                variant="subtitle1"
                component="h2"
                sx={{ fontWeight: 700, m: 0 }}
              />
            </Box>
            <IconButton size="small" aria-label={t('help.popup.close')} data-testid="help-popup-close" onClick={clear}>
              <CloseIcon fontSize="small" />
            </IconButton>
          </Stack>

          {topic && selection.target.label && topic.title !== selection.target.label && (
            <Box sx={{ mb: 1 }}>
              <BilingualText
                text={topic.title}
                bilingual={bilingual}
                frenchFirst={frenchFirst}
                variant="caption"
                color="text.secondary"
              />
            </Box>
          )}

          <Box sx={{ mb: topic?.steel || topic?.useIt ? 1.5 : 0 }}>
            <BilingualText
              text={topic?.what ?? t('help.fallback.what')}
              bilingual={bilingual && Boolean(topic?.what)}
              frenchFirst={frenchFirst}
            />
          </Box>

          {selection.target.detail && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5, fontStyle: 'italic' }}>
              {selection.target.detail}
            </Typography>
          )}

          {topic?.steel && (
            <>
              <Typography variant="overline" sx={{ display: 'block', lineHeight: 1.6, color: 'primary.main' }}>
                {t('help.section.steel')}
              </Typography>
              <Box sx={{ mb: 1.5 }}>
                <BilingualText text={topic.steel} bilingual={bilingual} frenchFirst={frenchFirst} />
              </Box>
            </>
          )}

          {topic?.useIt && (
            <>
              <Typography variant="overline" sx={{ display: 'block', lineHeight: 1.6, color: 'primary.main' }}>
                {t('help.section.useIt')}
              </Typography>
              <BilingualText text={topic.useIt} bilingual={bilingual} frenchFirst={frenchFirst} />
            </>
          )}

          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            {t('help.popup.hint')}
          </Typography>
        </Paper>
      )}
    </>
  )
}
