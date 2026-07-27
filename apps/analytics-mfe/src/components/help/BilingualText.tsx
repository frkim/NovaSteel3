import { Box, Typography } from '@mui/material'
import type { SxProps, Theme } from '@mui/material'
import type { TypographyProps } from '@mui/material'
import { BILINGUAL_SEPARATOR } from '../../i18n/helpCatalogs'

export interface BilingualTextProps {
  /** Either a single-language string, or two joined by {@link BILINGUAL_SEPARATOR}. */
  text: string
  /** True when the popup is showing English and French together. */
  bilingual?: boolean
  /** True when the French half comes first, which happens on a French portal. */
  frenchFirst?: boolean
  variant?: TypographyProps['variant']
  color?: TypographyProps['color']
  sx?: SxProps<Theme>
  /** Applied to the last rendered paragraph only, so callers keep their spacing. */
  trailingSx?: SxProps<Theme>
  component?: TypographyProps['component']
}

/**
 * Dark blue for the translated half.
 *
 * A single dark blue would be unreadable on the dark theme, so the light theme
 * gets the requested navy and the dark theme gets a lighter blue that still
 * reads as "the other language" without failing contrast.
 */
const FRENCH_COLOR = (theme: Theme) =>
  theme.palette.mode === 'dark' ? '#8FB6FF' : '#0A2F86'

/**
 * Renders a help string that may carry two languages at once.
 *
 * The bilingual catalog joins the two languages with a blank line. When both
 * are present they are laid out as two columns — the portal's own language on
 * the left, the translation on the right — so the reader can compare them line
 * for line instead of scrolling past a duplicated block. A single-language
 * string still renders as one plain paragraph.
 *
 * The French colour goes through `sx` rather than the `color` prop: MUI v9's
 * Typography `color` prop does not resolve palette paths or raw values on this
 * component (it silently falls back to the inherited text colour).
 */
export function BilingualText({
  text,
  bilingual = false,
  frenchFirst = false,
  variant = 'body2',
  color,
  sx,
  trailingSx,
  component,
}: BilingualTextProps) {
  const segments = bilingual ? text.split(BILINGUAL_SEPARATOR) : [text]
  const frenchIndex = segments.length > 1 ? (frenchFirst ? 0 : 1) : -1
  const sideBySide = segments.length > 1

  const paragraphs = segments.map((segment, index) => {
    const isFrench = index === frenchIndex
    const isLast = index === segments.length - 1
    return (
      <Typography
        key={index}
        variant={variant}
        component={component ?? 'p'}
        lang={frenchIndex === -1 ? undefined : isFrench ? 'fr' : 'en'}
        color={isFrench ? undefined : color}
        data-bilingual-segment={frenchIndex === -1 ? undefined : isFrench ? 'fr' : 'en'}
        sx={[
          { display: 'block', m: 0 },
          ...(Array.isArray(sx) ? sx : [sx]),
          isFrench ? { color: FRENCH_COLOR } : {},
          ...(isLast && trailingSx ? (Array.isArray(trailingSx) ? trailingSx : [trailingSx]) : []),
        ]}
      >
        {segment}
      </Typography>
    )
  })

  if (!sideBySide) return <>{paragraphs}</>

  return (
    <Box
      data-bilingual-columns="true"
      sx={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        columnGap: 2,
        alignItems: 'start',
        // The rule separates the two languages without adding vertical height.
        '& > :nth-of-type(2)': {
          pl: 2,
          borderLeft: (theme) => `1px solid ${theme.palette.divider}`,
        },
      }}
    >
      {paragraphs}
    </Box>
  )
}
