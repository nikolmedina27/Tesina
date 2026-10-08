/* SteelPlan · service worker.
   Guarda la "cáscara" (HTML, JS, CSS, librerías) para que la app abra rápido y sin internet en la tablet.
   La API (/api/...) siempre va a la red: los datos de planta nunca se sirven desde caché. */
const VERSION = 'steelplan-v3.1';
const CASCARA = ['/', '/static/app.js', '/static/mant.js', '/static/prog.js', '/static/styles.css', '/static/icono.svg', '/static/icono.png', '/static/img/logo-steelser.png', '/static/img/marca.png', '/static/gemelo3d.js', '/static/gemelo_modelos.js',
  '/static/vendor/frappe-gantt.css', '/static/vendor/frappe-gantt.min.js', '/static/vendor/echarts.min.js', '/manifest.webmanifest'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(CASCARA)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin || url.pathname.startsWith('/api/')) return;
  // red primero (para recibir siempre la última versión); si no hay red, la copia guardada
  e.respondWith(fetch(e.request, { cache: 'no-cache' }).then(r => {
    if (r.ok) { const copia = r.clone(); caches.open(VERSION).then(c => c.put(e.request, copia)); }
    return r;
  }).catch(() => caches.match(e.request).then(r => r || caches.match('/'))));
});
