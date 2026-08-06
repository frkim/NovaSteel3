/**
 * Registers the hand-written service worker (public/service-worker.js) so the
 * app shell is cached and the UI loads on a flaky shop-floor network. Disabled
 * during dev/test to avoid caching a moving target.
 */
export function registerServiceWorker(): void {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return
  }
  if (import.meta.env.DEV) {
    return
  }
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js').catch(() => {
      // Registration failures are non-fatal; the app still works online.
    })
  })
}
