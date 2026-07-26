/**
 * Device-domain format helpers.
 *
 * `DEVICE_MESSAGE_KEYS` is re-exported from the i18n layer, which owns the
 * English source of truth plus the fr / de / nl / es translations for every
 * `t('device.*')` call across the Device Operations screens.
 */
import type { DeviceStatus, SensorStatus, SensorTrend } from '../../api/deviceDomain'
import { DEVICE_MESSAGE_KEYS } from '../../i18n/deviceMessages'
import { formatNumber } from '../../utils/format'

/**
 * English text for all `device.*` translation keys.
 * Source of truth lives in the i18n layer so the five locale catalogs and
 * the component tree can never drift apart.
 */
export { DEVICE_MESSAGE_KEYS } from '../../i18n/deviceMessages'

/** Map DeviceStatus to SeverityPill severity string. */
export function deviceStatusSeverity(status: DeviceStatus): string {
  switch (status) {
    case 'healthy':
      return 'INFO'
    case 'degraded':
      return 'WARNING'
    case 'fault':
      return 'CRITICAL'
    case 'offline':
      return 'HIGH'
  }
}

/** Map SensorStatus to SeverityPill severity string. */
export function sensorStatusSeverity(status: SensorStatus): string {
  switch (status) {
    case 'normal':
      return 'INFO'
    case 'warning':
      return 'WARNING'
    case 'alarm':
      return 'CRITICAL'
    case 'stale':
      return 'MEDIUM'
  }
}

/** Trend glyph and aria-label for SensorTrend. */
export function trendGlyph(trend: SensorTrend): { glyph: string; label: string } {
  switch (trend) {
    case 'rising':
      return { glyph: '▲', label: DEVICE_MESSAGE_KEYS['device.trend.rising'] ?? 'Rising' }
    case 'falling':
      return { glyph: '▼', label: DEVICE_MESSAGE_KEYS['device.trend.falling'] ?? 'Falling' }
    case 'flat':
      return { glyph: '■', label: DEVICE_MESSAGE_KEYS['device.trend.flat'] ?? 'Flat' }
  }
}

/**
 * Format a sensor value to a sensible precision with its unit.
 * Integers or values > 100 show 0–1 decimal; smaller values show 1–3 decimals.
 */
export function formatSensorValue(
  value: number | null,
  unit: string,
  locale: string,
): string {
  if (value === null) {
    return '—'
  }
  const abs = Math.abs(value)
  const fractionDigits = abs >= 100 ? 1 : abs >= 10 ? 2 : 3
  const formatted = formatNumber(value, locale, { maximumFractionDigits: fractionDigits })
  return unit ? `${formatted} ${unit}` : formatted
}

/** Format sample period in ms to a human-readable string. */
export function formatSamplePeriod(ms: number): string {
  if (ms === 0) {
    return 'event'
  }
  if (ms < 1000) {
    return `${ms} ms`
  }
  if (ms < 60_000) {
    return `${ms / 1000} s`
  }
  if (ms < 3_600_000) {
    return `${ms / 60_000} min`
  }
  return `${ms / 3_600_000} h`
}
