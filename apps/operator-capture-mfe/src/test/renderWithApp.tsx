import type { ReactElement, ReactNode } from 'react'
import { render, type RenderResult } from '@testing-library/react'
import { ThemeProvider } from '@mui/material/styles'
import { AppContext, type AppContextValue } from '../components/appContext'
import { createCaptureTheme } from '../designTokens'
import { createTranslator } from '../i18n/messages'
import type { CaptureLanguage } from '../types'

export function testAppValue(overrides: Partial<AppContextValue> = {}): AppContextValue {
  const language = (overrides.language ?? 'en') as CaptureLanguage
  return {
    t: createTranslator(language),
    language,
    setLanguage: () => undefined,
    online: true,
    ...overrides,
  }
}

function Providers({ value, children }: { value: AppContextValue; children: ReactNode }) {
  const theme = createCaptureTheme('dark')
  return (
    <ThemeProvider theme={theme}>
      <AppContext.Provider value={value}>{children}</AppContext.Provider>
    </ThemeProvider>
  )
}

export function renderWithApp(ui: ReactElement, value: AppContextValue = testAppValue()): RenderResult {
  return render(<Providers value={value}>{ui}</Providers>)
}
