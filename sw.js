const CACHE='ewaste-v1';
const SHELL=['/','/static/manifest.json','/static/icon-192.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==CACHE).map(x=>caches.delete(x)))));self.clients.claim();});
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;           // never cache /analyze POSTs
  e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));
});
