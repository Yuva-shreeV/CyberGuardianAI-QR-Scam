// CyberGuardian AI - Service Worker
// Enables offline support and PWA installability

const CACHE_NAME = 'cyberguardian-v1';
const STATIC_ASSETS = [
  '/app/',
  '/app/index.html',
  '/app/style.css',
  '/app/script.js',
  '/app/manifest.json',
  '/app/icons/icon-192.png',
  '/app/icons/icon-512.png'
];

// Install: cache all static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activate: clear old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch: network-first for API calls, cache-first for static assets
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Always go network-first for API/backend calls
  if (url.pathname.startsWith('/predict') ||
      url.pathname.startsWith('/history') ||
      url.pathname.startsWith('/login') ||
      url.pathname.startsWith('/chat') ||
      url.pathname.startsWith('/health')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(JSON.stringify({
          error: 'You are offline. Please connect to the internet to scan QR codes.'
        }), { headers: { 'Content-Type': 'application/json' } });
      })
    );
    return;
  }

  // Cache-first for static assets (HTML, CSS, JS, images)
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request).then((response) => {
        // Cache new static assets on the fly
        if (response.ok && event.request.method === 'GET') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      });
    }).catch(() => {
      // Fallback for offline static page
      if (event.request.destination === 'document') {
        return caches.match('/app/index.html');
      }
    })
  );
});
