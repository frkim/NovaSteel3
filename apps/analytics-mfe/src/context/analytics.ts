import { createContext, useContext } from 'react'
import type { DataClient } from '../api/dataClient'
import type { DeviceClient } from '../api/deviceClient'
import type { MicrofrontendEmitter, ShellContext } from '../types'
import type { UnitSystem } from '../utils/format'
import type { TranslateFn } from '../i18n/messages'

export interface AnalyticsContextValue {
  context: ShellContext
  emit: MicrofrontendEmitter
  client: DataClient
  deviceClient: DeviceClient
  locale: string
  site: string
  unitSystem: UnitSystem
  t: TranslateFn
  demoMode: boolean
  can: (action: string) => boolean
}

export const AnalyticsContext = createContext<AnalyticsContextValue | null>(null)

export function useAnalytics(): AnalyticsContextValue {
  const value = useContext(AnalyticsContext)
  if (!value) {
    throw new Error('useAnalytics must be used within an AnalyticsContext provider.')
  }
  return value
}
