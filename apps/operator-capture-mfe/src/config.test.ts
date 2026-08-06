import { afterEach, describe, expect, it } from 'vitest'
import { demoHeaders, demoPlant } from './config'

afterEach(() => {
  delete window.NOVASTEEL_CAPTURE_CONFIG
})

describe('demoHeaders', () => {
  it('sends a plant scope, which the BFF requires on every demo identity', () => {
    // Regression guard: without X-Demo-Plants the BFF answers 401 on every call.
    // Unit tests that stub fetch cannot see this, but the deployed app breaks.
    const headers = demoHeaders('en-LU')
    expect(headers['X-Demo-Plants']).toBe('NS-DEMO-LUX-01')
    expect(headers['X-Demo-Plants']).toMatch(/^NS-DEMO-/)
  })

  it('only claims roles the operator persona is entitled to', () => {
    const roles = demoHeaders('en-LU')['X-Demo-Roles'].split(',')
    expect(roles).toContain('Knowledge.Contributor')
    // Operators capture and submit; approving their own procedure stays out.
    expect(roles).not.toContain('Knowledge.Publisher')
  })

  it('falls back to the default locale when none is supplied', () => {
    expect(demoHeaders('')['X-Demo-Locale']).toBe('en-LU')
    expect(demoHeaders('fr-LU')['X-Demo-Locale']).toBe('fr-LU')
  })

  it('lets the host page override the plant at runtime', () => {
    window.NOVASTEEL_CAPTURE_CONFIG = { plant: 'NS-DEMO-BEL-02' }
    expect(demoPlant()).toBe('NS-DEMO-BEL-02')
    expect(demoHeaders('en-LU')['X-Demo-Plants']).toBe('NS-DEMO-BEL-02')
  })
})
