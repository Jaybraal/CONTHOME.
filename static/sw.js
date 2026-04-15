const STATIC_CACHE = 'conthome-static-v3';
const ALL_CACHES   = [STATIC_CACHE];

// Assets locales que se cachean al instalar el SW
const PRECACHE = [
  '/static/css/styles.css',
  '/static/favicon.png',
  '/static/manifest.json',
  '/offline',
];

// ─── Install ──────────────────────────────────────────────
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(STATIC_CACHE)
      .then(c => c.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

// ─── Activate ─────────────────────────────────────────────
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => !ALL_CACHES.includes(k)).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// ─── Fetch ────────────────────────────────────────────────
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;

  const url = new URL(e.request.url);

  // API JSON → solo red, sin cachear
  if (url.pathname.startsWith('/api/')) return;

  // CDN (Bootstrap, Icons, Chart.js) → stale-while-revalidate
  if (url.hostname === 'cdn.jsdelivr.net') {
    e.respondWith(staleWhileRevalidate(e.request, STATIC_CACHE));
    return;
  }

  // Assets locales → cache-first
  if (url.pathname.startsWith('/static/')) {
    e.respondWith(cacheFirst(e.request, STATIC_CACHE));
    return;
  }

  // Navegación HTML → siempre desde red, NUNCA cachear
  // Las páginas contienen datos del usuario y NO deben servirse a otro usuario
  if (e.request.mode === 'navigate') {
    e.respondWith(networkFirstNav(e.request));
    return;
  }
});

// ─── Estrategias ─────────────────────────────────────────

async function cacheFirst(req, cacheName) {
  const cached = await caches.match(req);
  if (cached) return cached;
  try {
    const res = await fetch(req);
    if (res.ok) (await caches.open(cacheName)).put(req, res.clone());
    return res;
  } catch {
    return new Response('Sin conexión', { status: 503 });
  }
}

async function staleWhileRevalidate(req, cacheName) {
  const cache  = await caches.open(cacheName);
  const cached = await cache.match(req);
  const fresh  = fetch(req).then(res => {
    if (res.ok) cache.put(req, res.clone());
    return res;
  }).catch(() => null);
  return cached ?? (await fresh);
}

async function networkFirstNav(req) {
  // NUNCA guardar páginas autenticadas en caché:
  // podrían ser servidas a un usuario distinto al que las generó.
  try {
    return await fetch(req);
  } catch {
    // Sin conexión: página offline genérica (sin datos de ningún usuario)
    return caches.match('/offline');
  }
}
