import type { ShellContext } from './types'

/**
 * Full demo reader role-set. The local BFF authenticates demo requests with
 * explicit `X-Demo-*` headers (see services/bff-api auth boundary). The MFE is
 * a demo client only: it never holds a workload credential and the shell owns
 * real identity. Sending the union of reader roles keeps every persona surface
 * usable against the synthetic fixture without escalating any real privilege.
 */
export const DEMO_ROLES = [
  'Operator.Read',
  'MaintenanceEngineer.Read',
  'EnergyPlanner.Approve',
  'ProcessEngineer.Contribute',
  'Knowledge.Publisher',
  'Compliance.Auditor',
  'Platform.Capacity.Manage',
] as const

export const DEMO_PLANT = 'NS-DEMO-LUX-01'

declare global {
  interface Window {
    NOVASTEEL_ANALYTICS_CONFIG?: {
      bffBaseUrl?: string
      fixturesOnly?: boolean
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

/**
 * Resolve the BFF base URL with a deterministic precedence so the same bundle
 * runs embedded in the shell, standalone in dev, and fully offline:
 * 1. shell-provided context value (typed interop),
 * 2. runtime global injected by the host page,
 * 3. Vite build/dev env var,
 * 4. same-origin ('').
 */
export function resolveBffBaseUrl(context: ShellContext): string {
  const fromContext = context.bffBaseUrl?.trim()
  if (fromContext) {
    return stripTrailingSlash(fromContext)
  }
  const fromWindow =
    typeof window !== 'undefined' ? window.NOVASTEEL_ANALYTICS_CONFIG?.bffBaseUrl?.trim() : undefined
  if (fromWindow) {
    return stripTrailingSlash(fromWindow)
  }
  const fromEnv = readEnv('VITE_BFF_BASE_URL')
  if (fromEnv) {
    return stripTrailingSlash(fromEnv)
  }
  return ''
}

export function fixturesOnly(): boolean {
  if (typeof window !== 'undefined' && window.NOVASTEEL_ANALYTICS_CONFIG?.fixturesOnly) {
    return true
  }
  return readEnv('VITE_FIXTURES_ONLY') === 'true'
}

export function demoHeaders(context: ShellContext): Record<string, string> {
  return {
    'X-Demo-User': 'demo-portal-analytics',
    'X-Demo-Roles': DEMO_ROLES.join(','),
    'X-Demo-Plants': DEMO_PLANT,
    'X-Demo-Display-Name': context.activePersona || 'NovaSteel Demo',
    'X-Demo-Locale': context.locale || 'en-LU',
  }
}
