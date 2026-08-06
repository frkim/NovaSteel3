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
  return 'dark'
}

export function colorTokens(mode: ResolvedMode): ColorTokens {
  return mode === 'dark' ? sharedTokens.dark : sharedTokens.light
}

/**
 * Operator-facing theme. Reuses the shared design tokens (same as analytics-mfe)
 * but enlarges touch targets and typography for one-handed, gloved-hand use on
 * the shop floor.
 */
export function createCaptureTheme(themeMode: ThemeMode): Theme {
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
      fontSize: 15,
      h1: { fontSize: '1.6rem', fontWeight: 700, lineHeight: 1.25 },
      h2: { fontSize: '1.3rem', fontWeight: 700, lineHeight: 1.3 },
      h3: { fontSize: '1.15rem', fontWeight: 600, lineHeight: 1.4 },
      body2: { fontSize: '0.95rem', lineHeight: 1.55 },
      caption: { fontSize: '0.8rem', lineHeight: 1.45 },
      button: { textTransform: 'none', fontWeight: 700 },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          ':root': { colorScheme: mode },
          '*:focus-visible': {
            outline: `3px solid ${colors.focusRing}`,
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
      MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
      // Large, thumb-reachable buttons for gloved operation.
      MuiButton: {
        styleOverrides: { root: { minHeight: 52, fontSize: '1rem', paddingInline: 20 } },
      },
      MuiButtonBase: { styleOverrides: { root: { minHeight: 44 } } },
    },
  })
}
