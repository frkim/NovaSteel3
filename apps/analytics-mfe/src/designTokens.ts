import { createTheme, type Theme } from '@mui/material/styles'
import sharedTokens from '../../../contracts/ui/design-tokens.v1.json'
import type { ThemeMode } from './types'

export type ResolvedMode = 'light' | 'dark'
export type ColorTokens = typeof sharedTokens.light

export function resolveThemeMode(themeMode: ThemeMode): ResolvedMode {
  if (themeMode !== 'system') {
    return themeMode
  }
  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return 'light'
}

export function colorTokens(mode: ResolvedMode): ColorTokens {
  return mode === 'dark' ? sharedTokens.dark : sharedTokens.light
}

export function chartPalette(mode: ResolvedMode): string[] {
  return sharedTokens.chart[mode]
}

export function chartColor(themeMode: ThemeMode, index = 0): string {
  const palette = chartPalette(resolveThemeMode(themeMode))
  return palette[index % palette.length]
}

export interface StatusPalette {
  critical: string
  warning: string
  success: string
  info: string
  stale: string
}

export function statusPalette(mode: ResolvedMode): StatusPalette {
  const colors = colorTokens(mode)
  return {
    critical: colors.critical,
    warning: colors.warning,
    success: colors.success,
    info: colors.brandPrimary,
    stale: colors.stale,
  }
}

export interface DemoPalette {
  accent: string
  surface: string
}

export function demoPalette(mode: ResolvedMode): DemoPalette {
  const colors = colorTokens(mode)
  return { accent: colors.demo, surface: colors.demoSurface }
}

export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return false
  }
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export const KPI_PASTEL_LIGHT: string[] = [
  '#E3F2FD',
  '#E8F5E9',
  '#FFF3E0',
  '#F3E5F5',
  '#E0F7FA',
  '#FBE9E7',
  '#F1F8E9',
  '#EDE7F6',
]

export const KPI_PASTEL_DARK: string[] = [
  '#1A2733',
  '#1A2B1E',
  '#2B2317',
  '#261A2B',
  '#17292B',
  '#2B1D1A',
  '#222B1A',
  '#201A2B',
]

export function kpiPastelPalette(mode: ResolvedMode): string[] {
  return mode === 'dark' ? KPI_PASTEL_DARK : KPI_PASTEL_LIGHT
}

export function stableStringHash(str: string): number {
  let hash = 5381
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash + str.charCodeAt(i)) | 0
  }
  return Math.abs(hash)
}

export function createNovaSteelTheme(themeMode: ThemeMode): Theme {
  const mode = resolveThemeMode(themeMode)
  const colors = colorTokens(mode)

  return createTheme({
    palette: {
      mode,
      background: { default: colors.canvas, paper: colors.surface },
      text: { primary: colors.textPrimary, secondary: colors.textSecondary },
      primary: { main: colors.brandPrimary },
      secondary: { main: colors.brandAccent },
      error: { main: colors.critical },
      warning: { main: colors.warning },
      success: { main: colors.success },
      info: { main: colors.brandPrimary },
      divider: colors.surfaceAlt,
    },
    shape: { borderRadius: sharedTokens.radius.m },
    spacing: sharedTokens.spacing.s,
    typography: {
      fontFamily: sharedTokens.font.familyBase,
      htmlFontSize: 16,
      fontSize: 14,
      h1: { fontSize: '1.5rem', fontWeight: 700, lineHeight: 1.3 },
      h2: { fontSize: '1.25rem', fontWeight: 700, lineHeight: 1.3 },
      h3: { fontSize: '1.125rem', fontWeight: 600, lineHeight: 1.4 },
      h4: { fontSize: '1.5rem', fontWeight: 700 },
      h5: { fontSize: '1.125rem', fontWeight: 600 },
      h6: { fontSize: '1rem', fontWeight: 700 },
      body2: { fontSize: '0.875rem', lineHeight: 1.5 },
      caption: { fontSize: '0.75rem', lineHeight: 1.4 },
      button: { textTransform: 'none', fontWeight: 600 },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          ':root': {
            colorScheme: mode,
          },
          '*:focus-visible': {
            outline: `2px solid ${colors.focusRing}`,
            outlineOffset: '2px',
          },
          '@media (prefers-reduced-motion: reduce)': {
            '*, *::before, *::after': {
              animationDuration: '0.001ms !important',
              animationIterationCount: '1 !important',
              transitionDuration: '0.001ms !important',
              scrollBehavior: 'auto !important',
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            border: `1px solid ${colors.surfaceAlt}`,
            boxShadow: 'none',
            backgroundImage: 'none',
          },
        },
      },
      MuiPaper: {
        styleOverrides: { root: { backgroundImage: 'none' } },
      },
      MuiTab: {
        styleOverrides: { root: { textTransform: 'none', minHeight: 44 } },
      },
      MuiButtonBase: {
        styleOverrides: { root: { minHeight: 24 } },
      },
      MuiTableCell: {
        styleOverrides: {
          head: { backgroundColor: colors.surfaceAlt, fontWeight: 700 },
        },
      },
      MuiChip: {
        styleOverrides: { root: { fontWeight: 600 } },
      },
      MuiTooltip: {
        styleOverrides: { tooltip: { fontSize: '0.75rem' } },
      },
    },
  })
}
