/**
 * Standalone-app configuration. Mirrors analytics-mfe `config.ts` conventions:
 * a runtime global injected by the host page takes precedence, then a Vite env
 * var, then same-origin. When no backend is reachable the app runs in demo
 * mode against synthetic data so it is demoable without a live BFF.
 */

const DEMO_ROLES = [
  'Operator.Read',
  'ProcessEngineer.Contribute',
  'Knowledge.Publisher',
] as const

declare global {
  interface Window {
    NOVASTEEL_CAPTURE_CONFIG?: {
      bffBaseUrl?: string
      /** Force synthetic offline behaviour with no network calls. */
      demoMode?: boolean
    }
  }
}

function stripTrailingSlash(value: string): string {
  return value.replace(/\/+$/, '')
}

function readEnv(name: string): string | undefined {
  const env = import.meta.env as unknown as Record<string, string | undefined>
  const value = env?.[name]
  return typeof value === 'string' && value.trim() ? value.trim() : undefined
}

export function resolveBffBaseUrl(): string {
  const fromWindow =
    typeof window !== 'undefined' ? window.NOVASTEEL_CAPTURE_CONFIG?.bffBaseUrl?.trim() : undefined
  if (fromWindow) {
    return stripTrailingSlash(fromWindow)
  }
  const fromEnv = readEnv('VITE_BFF_BASE_URL')
  if (fromEnv) {
    return stripTrailingSlash(fromEnv)
  }
  return ''
}

/**
 * Demo mode is on when the host explicitly asks for it, when the Vite flag is
 * set, or when no BFF base URL is configured at all (pure static hosting).
 */
export function demoMode(): boolean {
  if (typeof window !== 'undefined' && window.NOVASTEEL_CAPTURE_CONFIG?.demoMode) {
    return true
  }
  if (readEnv('VITE_DEMO_MODE') === 'true') {
    return true
  }
  const hasBackend = Boolean(resolveBffBaseUrl()) || readEnv('VITE_BFF_BASE_URL') !== undefined
  return !hasBackend
}

export function demoHeaders(locale: string): Record<string, string> {
  return {
    'X-Demo-User': 'demo-operator-capture',
    'X-Demo-Roles': DEMO_ROLES.join(','),
    'X-Demo-Display-Name': 'NovaSteel Operator',
    'X-Demo-Locale': locale || 'en-LU',
  }
}
