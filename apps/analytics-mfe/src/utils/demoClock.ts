/**
 * Demo clock.
 *
 * Every synthetic fixture in this app is authored on a single 24-hour day that
 * ends at an 18:45Z snapshot. Anchoring that day to a literal calendar date
 * makes the demo rot: a forecast scored on a fixed date eventually predicts a
 * failure in the past. These helpers rebase the authored day onto the present
 * instead, so a rehearsal on any date shows plausible current timestamps while
 * keeping the hour-of-day structure the narrative depends on (spot-price peak,
 * shift patterns, the 15-minute interval grid).
 *
 * The data itself is unchanged and remains SYNTHETIC — only the calendar day it
 * hangs off moves.
 */

const FIXTURE_SNAPSHOT_HOUR_UTC = 18
const FIXTURE_SNAPSHOT_MINUTE_UTC = 45
const DAY_MS = 86_400_000

/** Most recent 18:45Z fixture snapshot at or before `now`. */
export function fixtureClock(now: Date = new Date()): Date {
  const candidate = new Date(
    Date.UTC(
      now.getUTCFullYear(),
      now.getUTCMonth(),
      now.getUTCDate(),
      FIXTURE_SNAPSHOT_HOUR_UTC,
      FIXTURE_SNAPSHOT_MINUTE_UTC,
      0,
      0,
    ),
  )
  return candidate.getTime() > now.getTime() ? new Date(candidate.getTime() - DAY_MS) : candidate
}

/** Calendar day (`YYYY-MM-DD`) the fixture day is currently anchored to. */
export function fixtureDay(now: Date = new Date()): string {
  return utcDate(fixtureClock(now))
}

/** `asOf` stamp for fixture-sourced responses, matching the fixture day. */
export function fixtureAsOf(now: Date = new Date()): string {
  return `${fixtureDay(now)}T18:45:00Z`
}

/** Midnight UTC of the current day, as epoch milliseconds. */
export function startOfUtcDay(now: Date = new Date()): number {
  return Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate())
}

/** Calendar day (`YYYY-MM-DD`) `days` before today; negative values look ahead. */
export function utcDaysAgo(days: number, now: Date = new Date()): string {
  return utcDate(new Date(startOfUtcDay(now) - days * DAY_MS))
}

function utcDate(value: Date): string {
  return value.toISOString().slice(0, 10)
}
