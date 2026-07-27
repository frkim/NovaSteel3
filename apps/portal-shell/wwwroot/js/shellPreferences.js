/**
 * Cookie-backed shell preferences.
 *
 * The three settings persisted here are the ones a visitor is expected to set
 * once and keep: the theme, the display language, and whether the Help
 * Assistant explains everything in both English and French. They are stored in
 * first-party cookies rather than `localStorage` so the same preference is
 * carried on any request the shell makes and can be read by the boot script in
 * `index.html` before the WebAssembly runtime starts.
 *
 * No personal data is stored: the values are a theme name, a locale tag and a
 * boolean. Cookies are `SameSite=Lax`, and `Secure` whenever the page is
 * served over HTTPS.
 */

const PREFIX = 'ns.'
const MAX_AGE_SECONDS = 60 * 60 * 24 * 365

function allCookies() {
  const jar = {}
  for (const part of document.cookie ? document.cookie.split(';') : []) {
    const index = part.indexOf('=')
    if (index < 1) {
      continue
    }
    const name = part.slice(0, index).trim()
    if (!name.startsWith(PREFIX)) {
      continue
    }
    jar[name.slice(PREFIX.length)] = decodeURIComponent(part.slice(index + 1).trim())
  }
  return jar
}

export function read() {
  return allCookies()
}

export function write(key, value) {
  const secure = window.location.protocol === 'https:' ? '; Secure' : ''
  document.cookie = `${PREFIX}${key}=${encodeURIComponent(value)}; path=/; max-age=${MAX_AGE_SECONDS}; SameSite=Lax${secure}`
}

export function clearAll() {
  for (const key of Object.keys(allCookies())) {
    document.cookie = `${PREFIX}${key}=; path=/; max-age=0; SameSite=Lax`
  }
}
