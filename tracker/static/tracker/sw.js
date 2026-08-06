const CACHE_NAME = 'finans-app-v1';
const urlsToCache = [
  '/',
  '/static/tracker/manifest.json'
];

// Yükleme aşaması (Install)
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

// İstekleri yakalama (Fetch)
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        return response || fetch(event.request);
      })
  );
});