export type UnitSystem = 'metric' | 'imperial'

function safeLocale(locale: string | undefined): string {
  return locale && locale.length >= 2 ? locale : 'en-LU'
}

export function formatNumber(
  value: number | null | undefined,
  locale: string,
  options: Intl.NumberFormatOptions = {},
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—'
  }
  return new Intl.NumberFormat(safeLocale(locale), {
    maximumFractionDigits: 1,
    ...options,
  }).format(value)
}

export function formatInteger(value: number | null | undefined, locale: string): string {
  return formatNumber(value, locale, { maximumFractionDigits: 0 })
}

export function formatCurrency(
  value: number | null | undefined,
  locale: string,
  currency = 'EUR',
  options: Intl.NumberFormatOptions = {},
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—'
  }
  return new Intl.NumberFormat(safeLocale(locale), {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
    ...options,
  }).format(value)
}

export function formatPercent(
  value: number | null | undefined,
  locale: string,
  fractionDigits = 1,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—'
  }
  return new Intl.NumberFormat(safeLocale(locale), {
    style: 'percent',
    maximumFractionDigits: fractionDigits,
  }).format(value / 100)
}

export function formatDateTime(
  value: string | number | Date | null | undefined,
  locale: string,
  options: Intl.DateTimeFormatOptions = { dateStyle: 'medium', timeStyle: 'short' },
): string {
  if (value === null || value === undefined || value === '') {
    return '—'
  }
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value)
  }
  return new Intl.DateTimeFormat(safeLocale(locale), options).format(date)
}

export function formatTime(value: string | number | Date | null | undefined, locale: string): string {
  return formatDateTime(value, locale, { timeStyle: 'short' })
}

/** Human-readable "x ago" using Intl.RelativeTimeFormat. */
export function formatRelativeTime(
  value: string | number | Date | null | undefined,
  locale: string,
  now: number = Date.now(),
): string {
  if (!value) {
    return '—'
  }
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value)
  }
  const diffSeconds = Math.round((date.getTime() - now) / 1000)
  const rtf = new Intl.RelativeTimeFormat(safeLocale(locale), { numeric: 'auto' })
  const divisions: Array<{ amount: number; unit: Intl.RelativeTimeFormatUnit }> = [
    { amount: 60, unit: 'second' },
    { amount: 60, unit: 'minute' },
    { amount: 24, unit: 'hour' },
    { amount: 7, unit: 'day' },
    { amount: 4.34524, unit: 'week' },
    { amount: 12, unit: 'month' },
    { amount: Number.POSITIVE_INFINITY, unit: 'year' },
  ]
  let duration = diffSeconds
  for (const division of divisions) {
    if (Math.abs(duration) < division.amount) {
      return rtf.format(Math.round(duration), division.unit)
    }
    duration /= division.amount
  }
  return rtf.format(Math.round(duration), 'year')
}

export function secondsSince(value: string | number | Date | null | undefined, now = Date.now()): number {
  if (!value) {
    return Number.POSITIVE_INFINITY
  }
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) {
    return Number.POSITIVE_INFINITY
  }
  return Math.max(0, Math.round((now - date.getTime()) / 1000))
}

const CELSIUS_TO_FAHRENHEIT = (c: number): number => c * 1.8 + 32

export function formatTemperature(
  celsius: number | null | undefined,
  locale: string,
  system: UnitSystem,
): string {
  if (celsius === null || celsius === undefined) {
    return '—'
  }
  if (system === 'imperial') {
    return `${formatNumber(CELSIUS_TO_FAHRENHEIT(celsius), locale)} °F`
  }
  return `${formatNumber(celsius, locale)} °C`
}

export function trendDirection(delta: number): 'up' | 'down' | 'flat' {
  if (delta > 0.0001) {
    return 'up'
  }
  if (delta < -0.0001) {
    return 'down'
  }
  return 'flat'
}

/** Parse an ISO timestamp (or epoch ms) to epoch ms for numeric chart axes. */
export function msOf(value: string | number | null | undefined): number {
  if (value === null || value === undefined) {
    return 0
  }
  const time = typeof value === 'number' ? value : new Date(value).getTime()
  return Number.isNaN(time) ? 0 : time
}
