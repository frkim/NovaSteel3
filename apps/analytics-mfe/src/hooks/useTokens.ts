import { useMemo } from 'react'
import { useAnalytics } from '../context/analytics'
import {
  chartPalette,
  colorTokens,
  resolveThemeMode,
  statusPalette,
  type ColorTokens,
  type ResolvedMode,
  type StatusPalette,
} from '../designTokens'

export interface ThemeTokens {
  mode: ResolvedMode
  colors: ColorTokens
  palette: string[]
  status: StatusPalette
  /** Maps a semantic severity to its token color + accessible glyph. */
  severity: (severity: string | null | undefined) => { color: string; glyph: string; label: string }
}

const SEVERITY_GLYPH: Record<string, string> = {
  CRITICAL: '⛔',
  HIGH: '⛔',
  WARNING: '▲',
  MEDIUM: '▲',
  INFO: 'ℹ',
  LOW: '✓',
  SUCCESS: '✓',
}

export function useTokens(): ThemeTokens {
  const { context } = useAnalytics()
  return useMemo(() => {
    const mode = resolveThemeMode(context.themeMode)
    const colors = colorTokens(mode)
    const status = statusPalette(mode)
    const severity = (raw: string | null | undefined) => {
      const label = raw?.trim() || 'UNKNOWN'
      const key = label.toUpperCase()
      if (key === 'CRITICAL' || key === 'HIGH') {
        return { color: status.critical, glyph: SEVERITY_GLYPH[key], label }
      }
      if (key === 'WARNING' || key === 'MEDIUM' || key === 'WATCH') {
        return { color: status.warning, glyph: '▲', label }
      }
      if (key === 'INFO') {
        return { color: status.info, glyph: 'ℹ', label }
      }
      return { color: status.info, glyph: 'ℹ', label }
    }
    return { mode, colors, palette: chartPalette(mode), status, severity }
  }, [context.themeMode])
}
