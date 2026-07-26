import { describe, expect, it } from 'vitest'
import { formatInteger, formatNumber, formatPercent, msOf, secondsSince, trendDirection } from './format'

describe('format helpers', () => {
  it('formats numbers with locale grouping', () => {
    expect(formatNumber(1842.4, 'en-LU')).toContain('1')
    expect(formatNumber(null, 'en-LU')).toBe('—')
  })

  it('formats integers without fraction digits', () => {
    expect(formatInteger(1842.6, 'en-LU')).not.toContain('.')
  })

  it('formats a percentage from a 0-100 value', () => {
    expect(formatPercent(94.8, 'en-LU')).toContain('%')
  })

  it('classifies trend direction', () => {
    expect(trendDirection(3)).toBe('up')
    expect(trendDirection(-3)).toBe('down')
    expect(trendDirection(0)).toBe('flat')
  })

  it('parses timestamps to epoch ms', () => {
    expect(msOf('2026-07-25T00:00:00Z')).toBe(Date.parse('2026-07-25T00:00:00Z'))
    expect(msOf(null)).toBe(0)
    expect(msOf('not-a-date')).toBe(0)
  })

  it('computes seconds since a timestamp', () => {
    const now = Date.parse('2026-07-25T00:01:00Z')
    expect(secondsSince('2026-07-25T00:00:00Z', now)).toBe(60)
    expect(secondsSince(null, now)).toBe(Number.POSITIVE_INFINITY)
  })
})
