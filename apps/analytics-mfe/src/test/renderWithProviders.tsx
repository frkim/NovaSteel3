import type { ReactElement, ReactNode } from 'react'
import { render, type RenderOptions, type RenderResult } from '@testing-library/react'
import { ThemeProvider } from '@mui/material/styles'
import { DataClient } from '../api/dataClient'
import { AnalyticsContext, type AnalyticsContextValue } from '../context/analytics'
import { createNovaSteelTheme } from '../designTokens'
import { createTranslator } from '../i18n/messages'
import type { ShellContext } from '../types'

export function testShellContext(overrides: Partial<ShellContext> = {}): ShellContext {
  return {
    themeMode: 'light',
    locale: 'en-LU',
    activePersona: 'PlantManager',
    primaryPersona: 'PlantManager',
    site: 'de',
    tokenRef: 'test-reference',
    bridgeVersion: '1.0',
    navigation: { section: 'command-center', subView: null, site: 'de' },
    bffBaseUrl: null,
    ...overrides,
  }
}

export function testAnalyticsValue(
  overrides: Partial<AnalyticsContextValue> = {},
): AnalyticsContextValue {
  const context = overrides.context ?? testShellContext()
  return {
    context,
    emit: () => undefined,
    client: overrides.client ?? new DataClient(context),
    locale: context.locale,
    site: context.site,
    unitSystem: 'metric',
    t: createTranslator(context.locale),
    can: () => true,
    ...overrides,
  }
}

function Providers({ value, children }: { value: AnalyticsContextValue; children: ReactNode }) {
  const theme = createNovaSteelTheme(value.context.themeMode)
  return (
    <ThemeProvider theme={theme}>
      <AnalyticsContext.Provider value={value}>{children}</AnalyticsContext.Provider>
    </ThemeProvider>
  )
}

export function renderWithProviders(
  ui: ReactElement,
  value: AnalyticsContextValue = testAnalyticsValue(),
  options?: RenderOptions,
): RenderResult {
  return render(<Providers value={value}>{ui}</Providers>, options)
}
