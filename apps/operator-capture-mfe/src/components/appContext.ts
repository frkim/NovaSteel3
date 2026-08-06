import { createContext, useContext } from 'react'
import type { TranslateFn } from '../i18n/messages'
import type { CaptureLanguage } from '../types'

export interface AppContextValue {
  t: TranslateFn
  language: CaptureLanguage
  setLanguage: (language: CaptureLanguage) => void
  online: boolean
}

export const AppContext = createContext<AppContextValue | null>(null)

export function useApp(): AppContextValue {
  const value = useContext(AppContext)
  if (!value) {
    throw new Error('useApp must be used within AppContext')
  }
  return value
}
