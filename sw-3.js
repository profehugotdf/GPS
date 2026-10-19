/* Rumbo: para que la versión web (por ejemplo en iPhone) abra sin internet.
   - La app (index.html) se baja de nuevo cada vez que hay internet y queda guardada para cuando no hay.
   - Leaflet (la librería del mapa) se guarda la primera vez.
   - Los mapas y la altura los guarda la propia app (no pasan por acá). */
const V='rumbo-v1';
const LEAF='https://unpkg.com/leaflet@1.9.4/dist/';
const CORE=['./','index.html','manifest.webmanifest','icon-192.png','icon-512.png','apple-touch-icon.png'];
const LIBS=[LEAF+'leaflet.js',LEAF+'leaflet.css'];

self.addEventListener('install',e=>{
  e.waitUntil((async()=>{
    const c=await caches.open(V);
    await Promise.all(CORE.map(u=>c.add(u).catch(()=>{})));
    await Promise.all(LIBS.map(u=>c.add(new Request(u,{mode:'cors'})).catch(()=>{})));
    self.skipWaiting();
  })());
});
self.addEventListener('activate',e=>{
  e.waitUntil((async()=>{
    for(const k of await caches.keys())if(k!==V)await caches.delete(k);
    await self.clients.claim();
  })());
});

const withTimeout=(p,ms)=>new Promise((ok,no)=>{const t=setTimeout(()=>no(new Error('timeout')),ms);p.then(r=>{clearTimeout(t);ok(r);},er=>{clearTimeout(t);no(er);});});

self.addEventListener('fetch',e=>{
  const req=e.request;
  if(req.method!=='GET')return;
  const url=new URL(req.url);
  const same=url.origin===self.location.origin;

  /* la app: primero internet (para tener siempre la última versión), si no hay, la guardada */
  if(req.mode==='navigate'||(same&&/\/(index\.html)?$/.test(url.pathname))){
    e.respondWith((async()=>{
      const c=await caches.open(V);
      try{
        const r=await withTimeout(fetch(req),6000);
        if(r&&r.ok){c.put('index.html',r.clone());return r;}
        throw new Error('http '+(r&&r.status));
      }catch(er){
        return (await c.match('index.html'))||(await c.match('./'))||Response.error();
      }
    })());
    return;
  }

  /* lib/leaflet.* no existe en la página web (es para la app de Android): se usa la copia de unpkg */
  if(same&&/\/lib\/leaflet\.(js|css)$/.test(url.pathname)){
    const ext=url.pathname.endsWith('.css')?'leaflet.css':'leaflet.js';
    e.respondWith((async()=>{
      const c=await caches.open(V);
      let r=await c.match(LEAF+ext);
      if(!r){try{r=await fetch(new Request(LEAF+ext,{mode:'cors'}));if(r.ok)c.put(LEAF+ext,r.clone());}catch(er){}}
      return r||new Response('',{status:404});
    })());
    return;
  }
  if(same&&/\/lib\//.test(url.pathname)){e.respondWith(fetch(req).catch(()=>new Response('',{status:404})));return;}

  /* leaflet de unpkg, íconos y manifiesto: lo guardado primero */
  if(url.href.startsWith(LEAF)||(same&&/\.(png|webmanifest)$/.test(url.pathname))){
    e.respondWith((async()=>{
      const c=await caches.open(V);
      const hit=await c.match(req.url);
      if(hit)return hit;
      try{const r=await fetch(req);if(r.ok)c.put(req.url,r.clone());return r;}catch(er){return Response.error();}
    })());
  }
  /* todo lo demás (mapas, clima, seguimiento en vivo…) va directo a internet, como siempre */
});
