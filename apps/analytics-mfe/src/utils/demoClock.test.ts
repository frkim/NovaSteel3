import { describe, expect, it } from 'vitest'
import { fixtureAsOf, fixtureClock, fixtureDay, startOfUtcDay, utcDaysAgo } from './demoClock'
import { FIXTURE_AS_OF } from '../api/fixtures'

const DAY_MS = 86_400_000

describe('demoClock', () => {
  it('anchors to the 18:45Z snapshot of the same day once it has passed', () => {
    const now = new Date('2026-07-28T20:10:00Z')
    expect(fixtureClock(now).toISOString()).toBe('2026-07-28T18:45:00.000Z')
    expect(fixtureDay(now)).toBe('2026-07-28')
    expect(fixtureAsOf(now)).toBe('2026-07-28T18:45:00Z')
  })

  it('falls back to the previous day before the snapshot hour', () => {
    const now = new Date('2026-07-28T06:30:00Z')
    expect(fixtureClock(now).toISOString()).toBe('2026-07-27T18:45:00.000Z')
    expect(fixtureDay(now)).toBe('2026-07-27')
  })

  it('never anchors in the future and stays within 24 hours of now', () => {
    for (const iso of ['2026-01-01T00:00:00Z', '2026-02-28T18:44:59Z', '2026-12-31T23:59:59Z']) {
      const now = new Date(iso)
      const clock = fixtureClock(now)
      expect(clock.getTime()).toBeLessThanOrEqual(now.getTime())
      expect(now.getTime() - clock.getTime()).toBeLessThan(DAY_MS)
    }
  })

  it('resolves midnight UTC and past calendar days', () => {
    const now = new Date('2026-07-28T20:10:00Z')
    expect(startOfUtcDay(now)).toBe(Date.parse('2026-07-28T00:00:00Z'))
    expect(utcDaysAgo(0, now)).toBe('2026-07-28')
    expect(utcDaysAgo(53, now)).toBe('2026-06-05')
    expect(utcDaysAgo(-3, now)).toBe('2026-07-31')
  })

  it('keeps the offline fixture pack anchored to the present', () => {
    // Regression guard: a literal fixture day makes the lining forecast predict
    // a failure date in the past once the demo is a few weeks old.
    const asOf = Date.parse(FIXTURE_AS_OF)
    const now = Date.now()
    expect(asOf).toBeLessThanOrEqual(now)
    expect(now - asOf).toBeLessThan(DAY_MS)
  })
})
