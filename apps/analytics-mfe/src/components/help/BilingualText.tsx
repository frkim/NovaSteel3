import { Fragment } from 'react'
import { Typography } from '@mui/material'
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
 * Renders a help string that may carry two languages at once.
 *
 * The bilingual catalog joins the two languages with a blank line, but MUI
 * Typography collapses whitespace, so both languages used to run together on
 * one line. Splitting them into separate paragraphs restores the break, and
 * colouring the French half makes it obvious which language you are reading.
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

  return (
    <Fragment>
      {segments.map((segment, index) => {
        const isFrench = index === frenchIndex
        const isLast = index === segments.length - 1
        return (
          <Typography
            key={index}
            variant={variant}
            component={component ?? 'p'}
            lang={frenchIndex === -1 ? undefined : isFrench ? 'fr' : 'en'}
            color={isFrench ? 'info.main' : color}
            data-bilingual-segment={frenchIndex === -1 ? undefined : isFrench ? 'fr' : 'en'}
            sx={[
              { display: 'block' },
              ...(Array.isArray(sx) ? sx : [sx]),
              index > 0 ? { mt: 1 } : {},
              ...(isLast && trailingSx ? (Array.isArray(trailingSx) ? trailingSx : [trailingSx]) : []),
            ]}
          >
            {segment}
          </Typography>
        )
      })}
    </Fragment>
  )
}
