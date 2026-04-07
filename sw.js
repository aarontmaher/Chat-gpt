// Service Worker — cache-first for offline support
// v3: bumped to evict stale SW. Pre-cache list intentionally empty;
// same-origin resources are cached dynamically via the fetch handler.
const CACHE_VERSION = 'v3';
const CACHE_NAME = 'grappling-map-' + CACHE_VERSION;
const CACHE_URLS = [];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(CACHE_URLS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k.startsWith('grappling-map-') && k !== CACHE_NAME)
          .map(k => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  // On localhost/dev: pass everything through — never intercept or cache.
  // Guards against any old SW version being resident in the browser.
  if (self.location.hostname === 'localhost' || self.location.hostname === '127.0.0.1' || self.location.hostname === '') return;

  // Do not intercept cross-origin requests (API calls, Railway backend, etc.)
  // They must reach the network directly to avoid SW interference with CORS/timeout.
  if (!event.request.url.startsWith(self.location.origin)) return;

  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        // Only cache successful same-origin responses
        if (response.ok && response.type === 'basic') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      });
    })
  );
});
