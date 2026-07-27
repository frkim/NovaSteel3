import { useState } from 'react'
import Box from '@mui/material/Box'
import ButtonBase from '@mui/material/ButtonBase'
import Dialog from '@mui/material/Dialog'
import IconButton from '@mui/material/IconButton'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import CloseIcon from '@mui/icons-material/Close'
import ZoomInIcon from '@mui/icons-material/ZoomIn'
import ZoomOutIcon from '@mui/icons-material/ZoomOut'
import ZoomOutMapIcon from '@mui/icons-material/ZoomOutMap'
import RestartAltIcon from '@mui/icons-material/RestartAlt'
import { useAnalytics } from '../../context/analytics'

const MIN_ZOOM = 100
const MAX_ZOOM = 400
const ZOOM_STEP = 50

export interface ProcessDiagramProps {
  /**
   * Asset stem below `/media`, without extension. A `-sm` rendition at 900 px
   * and a full rendition at 1800 px are both expected to exist.
   */
  stem: string
  /** Aspect ratio of the source artwork, used to reserve space before load. */
  ratio?: number
  alt: string
  title: string
  caption: string
}

/**
 * A full-width illustrated process diagram with a zoomable lightbox.
 *
 * The artwork carries a lot of small labels, so a static in-page image is not
 * enough — a reader needs to enlarge it. Clicking the figure opens a dialog
 * where the picture can be magnified up to 400 % and panned.
 */
export function ProcessDiagram({ stem, ratio = 2816 / 1536, alt, title, caption }: ProcessDiagramProps) {
  const { t } = useAnalytics()
  const [open, setOpen] = useState(false)
  const [zoom, setZoom] = useState(MIN_ZOOM)
  const [failed, setFailed] = useState(false)

  function close() {
    setOpen(false)
    setZoom(MIN_ZOOM)
  }

  if (failed) return null

  return (
    <>
      <Box
        component="figure"
        data-help="website.processDiagram"
        data-help-label={title}
        sx={{ m: 0, my: 3 }}
      >
        <ButtonBase
          onClick={() => setOpen(true)}
          aria-label={`${title} — ${t('website.diagram.enlarge')}`}
          sx={{
            display: 'block',
            width: '100%',
            borderRadius: 1,
            overflow: 'hidden',
            border: 1,
            borderColor: 'divider',
            cursor: 'zoom-in',
            transition: 'box-shadow 120ms ease',
            '&:hover': { boxShadow: 4 },
            '&:focus-visible': { outline: '2px solid', outlineColor: 'primary.main', outlineOffset: 2 },
          }}
        >
          <Box
            component="img"
            src={`/media/${stem}.webp`}
            srcSet={`/media/${stem}-sm.webp 900w, /media/${stem}.webp 1800w`}
            sizes="(max-width: 900px) 100vw, 1200px"
            alt={alt}
            loading="lazy"
            decoding="async"
            onError={() => setFailed(true)}
            sx={{ display: 'block', width: '100%', height: 'auto', aspectRatio: String(ratio) }}
          />
        </ButtonBase>
        <Stack
          component="figcaption"
          direction="row"
          spacing={1}
          sx={{ mt: 1, alignItems: 'flex-start', color: 'text.secondary' }}
        >
          <ZoomOutMapIcon fontSize="small" sx={{ mt: '2px', flexShrink: 0 }} />
          <Typography variant="caption" sx={{ lineHeight: 1.5 }}>
            <Box component="strong" sx={{ color: 'text.primary' }}>
              {title}.
            </Box>{' '}
            {caption} <em>{t('website.diagram.enlarge')}</em>
          </Typography>
        </Stack>
      </Box>

      <Dialog open={open} onClose={close} maxWidth="xl" fullWidth data-help-surface="">
        <Stack
          direction="row"
          spacing={1}
          sx={{ alignItems: 'center', px: 2, py: 1, borderBottom: 1, borderColor: 'divider' }}
        >
          <Typography variant="subtitle1" sx={{ fontWeight: 700, flex: 1 }}>
            {title}
          </Typography>
          <Tooltip title={t('chart.zoomOut')}>
            <span>
              <IconButton
                size="small"
                disabled={zoom <= MIN_ZOOM}
                onClick={() => setZoom((z) => Math.max(MIN_ZOOM, z - ZOOM_STEP))}
                aria-label={t('chart.zoomOut')}
              >
                <ZoomOutIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
          <Typography variant="caption" sx={{ minWidth: 44, textAlign: 'center', fontVariantNumeric: 'tabular-nums' }}>
            {zoom}%
          </Typography>
          <Tooltip title={t('chart.zoomIn')}>
            <span>
              <IconButton
                size="small"
                disabled={zoom >= MAX_ZOOM}
                onClick={() => setZoom((z) => Math.min(MAX_ZOOM, z + ZOOM_STEP))}
                aria-label={t('chart.zoomIn')}
              >
                <ZoomInIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title={t('chart.zoomReset')}>
            <span>
              <IconButton
                size="small"
                disabled={zoom === MIN_ZOOM}
                onClick={() => setZoom(MIN_ZOOM)}
                aria-label={t('chart.zoomReset')}
              >
                <RestartAltIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
          <IconButton size="small" onClick={close} aria-label={t('website.diagram.close')}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Stack>
        <Box sx={{ overflow: 'auto', bgcolor: 'background.default', maxHeight: '80vh' }}>
          <Box
            component="img"
            src={`/media/${stem}.webp`}
            alt={alt}
            sx={{ display: 'block', width: `${zoom}%`, maxWidth: 'none', height: 'auto' }}
          />
        </Box>
      </Dialog>
    </>
  )
}
