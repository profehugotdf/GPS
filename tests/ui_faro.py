"""Faros 🗼 y balizas 🔶 en Calcar (un toque), de OpenStreetMap (nodos) y en `elems` para Kayak."""
import asyncio, http.server, threading, functools, os
from playwright.async_api import async_playwright
SITE = os.environ.get('RUMBO_SITE', '.')
def ok(c, m):
    print(('  ✔ ' if c else '  ✘ ') + m); assert c, m
async def main():
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8798), functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    errs = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch(); pg = await b.new_page(viewport={'width': 412, 'height': 860})
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8798/index.html'); await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("async()=>{await openTrace();}")
        ok(await pg.evaluate("['faro','baliza'].every(k=>!!document.querySelector('#trKind button[data-k='+k+']')&&NOROUTE.has(k)&&ELEMK.includes(k)&&POINTK.includes(k)&&!BARCOK.includes(k))"), 'faro y baliza aparecen en Calcar, no se rutean y no son barcos')
        ok(await pg.evaluate("userTags({kind:'faro',props:{}}).man_made")=='lighthouse', 'etiqueta man_made=lighthouse')
        # un toque guarda
        r = await pg.evaluate("""async()=>{TR.kind='faro';TR.shape='line';TR.mode='taps';traceTap({latlng:{lat:-54.8700,lng:-68.1300}});
          await new Promise(r=>setTimeout(r,400));const all=(await DB.all('kv','edit:')).filter(e=>e.kind==='faro');
          return {n:all.length,pts:all[0]&&all[0].pts};}""")
        print('   ', r)
        ok(r['n'] == 1 and len(r['pts']) == 2 and r['pts'][0] == r['pts'][1], 'un toque guarda el faro (2 puntos iguales)')
        await pg.evaluate("async()=>{await DB.put('kv','edit:bz',{id:'bz',type:'path',kind:'baliza',name:'Baliza Este',pts:[[-54.8710,-68.1310],[-54.8710,-68.1310]],props:{alto:6},created:Date.now()});}")
        # OSM: nodos de faro y baliza
        r = await pg.evaluate("""()=>elFromOsm([{type:'node',id:1,lat:-54.88,lon:-68.14,tags:{man_made:'lighthouse',name:'Faro Prueba',height:'11'}},
          {type:'node',id:2,lat:-54.881,lon:-68.141,tags:{'seamark:type':'beacon_cardinal'}},{type:'node',id:3,lat:-54.882,lon:-68.142,tags:{'seamark:type':'buoy_lateral'}},
          {type:'way',id:4,geometry:[{lat:-54.9,lon:-68.2},{lat:-54.9001,lon:-68.2001}],tags:{man_made:'lighthouse'}}]).map(e=>[e.k,e.name,e.alto,e.pts.length])""")
        print('   ', r)
        ok(r == [['faro', 'Faro Prueba', 11, 2], ['baliza', '', None, 2], ['faro', '', None, 2]], 'nodos de OpenStreetMap: faro, baliza; la boya no entra; faro edificio = faro')
        ok('node["man_made"="lighthouse"]' in await pg.evaluate("elOsmQ([[-54.87,-68.13],[-54.87,-68.12]],900)"), 'la consulta de elementos pide faros y balizas')
        r = await pg.evaluate("""async()=>{const P=[[-54.872,-68.132],[-54.872,-68.125]];const o=await elCollect(P,{s:-54.9,n:-54.84,w:-68.2,e:-68.1},900);
          return {l:o.list.map(e=>[e.k,e.n,e.a,e.m,e.p.length>=1]),res:elResumen(o.list)};}""")
        print('   ', r)
        ok(any(x[0] == 'faro' and x[3] == 1 for x in r['l']) and any(x[0] == 'baliza' and x[2] == 6 and x[1] == 'Baliza Este' for x in r['l']), 'viajan en `elems` (faro a mano, baliza con altura 6 m)')
        ok('faro' in r['res'] and 'baliza' in r['res'], 'el resumen los nombra: %s' % r['res'])
    ok(not errs, 'sin errores de página %s' % errs)
asyncio.run(main())
