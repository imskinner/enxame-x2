// Enxame ×2 service worker: after the first visit the game opens with no network.
// The page is fetched network first (a new version shows up on the next visit with a connection, the cached one when
// there is none). Models, sprites, the libraries and the fonts are answered from the cache at once and refreshed in the
// background. Supabase and everything else never pass through here.
const CACHE = 'enxame-v1';
const CDN = /^https:\/\/(cdn\.jsdelivr\.net|fonts\.googleapis\.com|fonts\.gstatic\.com)\//;
const PRECACHE = [
  './', 'manifest.webmanifest', 'assets/icon-192.png', 'assets/castle.glb', 'assets/characters.glb', 'assets/flora.glb',
  'assets/ogre.glb', 'assets/props.glb', 'assets/worlds.glb', 'assets/ui/bag.webp', 'assets/ui/chest_bronze.webp', 'assets/ui/chest_bronze_open.webp',
  'assets/ui/chest_gold.webp', 'assets/ui/chest_gold_open.webp', 'assets/ui/chest_silver.webp', 'assets/ui/chest_silver_open.webp', 'assets/ui/coin.webp', 'assets/ui/coins.webp',
  'assets/ui/crown.webp', 'assets/ui/gem.webp', 'assets/ui/gems.webp', 'assets/ui/hero_arqueira.webp', 'assets/ui/hero_ladrao.webp', 'assets/ui/hero_muralha.webp',
  'assets/ui/ticket.webp', 'assets/ui/trophy.webp',
];
const put = (req, res) => caches.open(CACHE).then((c) => c.put(req, res)).catch(() => {});

self.addEventListener('install', (e) => {
  self.skipWaiting();
  // everything the game draws with, so the first offline visit is not missing a sprite the online one never opened
  e.waitUntil(caches.open(CACHE).then((c) => Promise.allSettled(PRECACHE.map((u) => c.add(u)))));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const req = e.request, url = new URL(req.url), own = url.origin === location.origin;
  if (req.method !== 'GET' || (!own && !CDN.test(req.url))) return;
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req).then((res) => { if (res.ok) put(req, res.clone()); return res; })
        .catch(() => caches.match(req, { ignoreSearch: true }).then((hit) => hit || caches.match('./'))),
    );
    return;
  }
  e.respondWith(caches.match(req).then((hit) => {
    const net = fetch(req).then((res) => { if (res.ok || res.type === 'opaque') put(req, res.clone()); return res; });
    if (!hit) return net;
    e.waitUntil(net.catch(() => {})); // refresh behind the cached answer
    return hit;
  }));
});
