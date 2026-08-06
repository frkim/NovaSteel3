/*
 * NovaSteel Operator Capture — hand-written service worker (no build plugin).
 *
 * Goal: make the app shell load on a flaky shop-floor network. We cache the
 * shell (HTML/JS/CSS/manifest/icons) with a stale-while-revalidate strategy so
 * the UI opens instantly even offline. We DELIBERATELY never cache the capture
 * API (interviews / audio / transcript / draft): those carry consent-bound
 * personal data and large audio blobs, and stale responses would be dangerous.
 */

const CACHE_VERSION = 'ns-capture-shell-v1'
const APP_SHELL = ['/', '/index.html', '/manifest.webmanifest', '/icons/icon.svg', '/icons/icon-192.svg']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE_VERSION)
      .then((cache) => cache.addAll(APP_SHELL))
      .catch(() => undefined)
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  )
})

// Any request whose path targets the knowledge API must bypass the cache so we
// never serve stale audio/transcript/consent data from disk.
function isApiRequest(url) {
  return url.pathname.includes('/v1/knowledge/')
}

// The container rewrites /config.js on every start with the environment's BFF
// origin. Caching it would pin the app to a previous deployment's backend.
function isRuntimeConfig(url) {
  return url.pathname === '/config.js'
}

self.addEventListener('fetch', (event) => {
  const request = event.request
  if (request.method !== 'GET') {
    return
  }

  const url = new URL(request.url)

  if (isApiRequest(url) || isRuntimeConfig(url)) {
    // Network-only: consent-bound API data, and runtime config that must track
    // the deployed environment rather than whatever was cached last time.
    return
  }

  // Only handle same-origin navigations and shell assets.
  if (url.origin !== self.location.origin) {
    return
  }

  if (request.mode === 'navigate') {
    // App-shell navigation fallback: serve cached index.html when offline.
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone()
          caches.open(CACHE_VERSION).then((cache) => cache.put('/index.html', copy)).catch(() => undefined)
          return response
        })
        .catch(() => caches.match('/index.html').then((cached) => cached || Response.error())),
    )
    return
  }

  // Stale-while-revalidate for static shell assets.
  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request)
        .then((response) => {
          if (response && response.status === 200 && response.type === 'basic') {
            const copy = response.clone()
            caches.open(CACHE_VERSION).then((cache) => cache.put(request, copy)).catch(() => undefined)
          }
          return response
        })
        .catch(() => cached)
      return cached || network
    }),
  )
})
