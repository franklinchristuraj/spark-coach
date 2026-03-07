// Minimal service worker to satisfy PWA install criteria.
// Same-origin GET requests pass through; cross-origin requests are not intercepted.

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  // Only intercept same-origin GET requests to avoid breaking cross-origin fetches
  // (e.g. Vercel Analytics, Google Fonts) which can't be re-fetched via fetch(request).
  if (
    event.request.method !== "GET" ||
    !event.request.url.startsWith(self.location.origin)
  ) {
    return;
  }
  event.respondWith(fetch(event.request));
});
