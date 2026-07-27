export type ThemeMode = 'light' | 'dark' | 'system'

export interface AnalyticsNavigation {
  section: string
  subView: string | null
  site: string
}

export interface ShellContext {
  themeMode: ThemeMode
  locale: string
  activePersona: string
  site: string
  demoMode: boolean
  tokenRef: string
  bridgeVersion: '1.0'
  navigation: AnalyticsNavigation
  /**
   * Optional shell-provided Backend-for-Frontend base URL. When absent the
   * microfrontend resolves the base URL from a runtime global, a Vite env var,
   * or falls back to same-origin and then to local synthetic fixtures.
   */
  bffBaseUrl?: string | null
  /**
   * Optional demo permission set forwarded by the shell so persona surfaces can
   * hide or disable role-gated actions. When absent the MFE assumes the full
   * demo reader set.
   */
  permittedActions?: string[]
  /**
   * When true the Help Assistant renders every explanation in English and
   * French together. Set from Settings in the shell; off by default.
   */
  helpBilingual?: boolean
}

export type MicrofrontendEmitter = (eventType: string, payload: unknown) => void

export interface MicrofrontendInstance {
  update: (context: ShellContext) => void
  unmount: () => void
}
