"""Guiando una ruta, tocar un punto del mapa deja pasar por ahí o cambiar el destino (Hugo, 13-nov:
"quisiera que si ya me está dirigiendo en una ruta pueda seleccionar un punto, para pasar por ahí o cambiar de destino")."""
import asyncio, http.server, threading, functools, os, importlib.util
from playwright.async_api import async_playwright
SITE = os.environ.get('RUMBO_SITE', '.')
spec = importlib.util.spec_from_file_location('ui_land', os.path.join(os.path.dirname(__file__), 'ui_land.py'))
SETUP = open(spec.origin, encoding='utf8').read().split('SETUP = """')[1].split('"""')[0]   # la misma red de prueba: Recta (600 m), Rodeo (800 m) y Lateral
def ok(c, m):
    print(('  ✔ ' if c else '  ✘ ') + m); assert c, m
async def main():
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8815), functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE)); threading.Thread(target=srv.serve_forever, daemon=True).start()
    errs = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch(); pg = await b.new_page(viewport={'width': 412, 'height': 860}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8815/index.html'); await pg.wait_for_function('!!window.__ok')
        await pg.evaluate(SETUP)
        await pg.evaluate("""async()=>{await putNet();startWatch=async()=>{};keepAwake=()=>{};navSay=t=>{(window.__dijo=window.__dijo||[]).push(t)};pinEle=async()=>({why:'x'});
          lastFix={lat:T.A[0],lon:T.A[1],t:Date.now(),acc:5};
          RT.from={lat:T.A[0],lon:T.A[1],label:'A'};RT.to={lat:T.B[0],lon:T.B[1],label:'B'};S.routeMode='car';S.pref='fast';
          const g=await ensureGraph();await calcRoutes(g);RT.sel='car';await startNav();}""")
        await pg.wait_for_timeout(300)
        d0 = await pg.evaluate("Math.round(NAV.N.route.dist)")
        ok(await pg.evaluate("NAV.on") and 590 <= d0 <= 610, 'guiando por la Recta (%d m)' % d0)
        # tocar el mapa sobre el Rodeo
        r = await pg.evaluate("""async()=>{const p=T.P(300,100);await onMapTap({latlng:{lat:p[0],lng:p[1]}});
          const v=id=>!$('#'+id).hidden;return {pin:!$('#pin').hidden,via:v('pinNavVia'),to:v('pinNavTo'),go:v('pinGo'),from:v('pinFrom'),tgt:v('pinTgt'),txt:$('#pinTxt').textContent};}""")
        print('   ', r)
        ok(r['pin'] and r['via'] and r['to'], 'guiando, tocar el mapa abre la tarjeta con "Pasar por acá" y "Cambiar el destino"')
        ok(not r['go'] and not r['from'] and not r['tgt'], 'y sin los botones que no van durante la guía')
        await pg.evaluate("$('#pinNavVia').click()"); await pg.wait_for_function("!NAV.busy&&$('#pin').hidden"); await pg.wait_for_timeout(200)
        r = await pg.evaluate("({d:Math.round(NAV.N.route.dist),via:!!NAV.via,dest:NAV.dest.label,on:NAV.on,dijo:(window.__dijo||[]).join(' | '),km:$('#nvKm').textContent})")
        print('   ', r)
        ok(r['on'] and r['via'] and 780 <= r['d'] <= 820 and r['dest'] == 'B', 'Pasar por acá: la guía sigue al mismo destino pero por el Rodeo (%d m)' % r['d'])
        ok('Pasando por' in r['dijo'], 'lo dice en voz alta y actualiza la tarjeta (%s)' % r['km'])
        # te salís de la ruta: el recálculo sigue pasando por el punto; al pasar por él, se olvida
        r = await pg.evaluate("""async()=>{NAV.lastRecalc=0;const p=T.P(0,40);await navRecalc({lat:p[0],lon:p[1]});const d1=Math.round(NAV.N.route.dist),v1=!!NAV.via;
          const q=T.P(300,100);navOnFix({lat:q[0],lon:q[1],acc:5,t:Date.now(),speed:5});return {d1,v1,v2:!!NAV.via};}""")
        ok(r['v1'] and r['d1'] > 700 and not r['v2'], 'un recálculo sigue pasando por el punto (%d m) y al pasar por ahí se olvida' % r['d1'])
        # cambiar el destino a la punta de la Lateral
        await pg.evaluate("""async()=>{lastFix={lat:T.A[0],lon:T.A[1],t:Date.now(),acc:5};await onMapTap({latlng:{lat:T.L[0],lng:T.L[1]}});}""")
        await pg.evaluate("$('#pinNavTo').click()"); await pg.wait_for_function("!NAV.busy&&$('#pin').hidden"); await pg.wait_for_timeout(200)
        r = await pg.evaluate("({d:Math.round(NAV.N.route.dist),dest:[NAV.dest.lat,NAV.dest.lon],L:T.L,to:[RT.to.lat,RT.to.lon],via:!!NAV.via,on:NAV.on,dijo:(window.__dijo||[]).join(' | ')})")
        print('   ', r)
        ok(r['on'] and r['dest'] == r['L'] and r['to'] == r['L'] and 390 <= r['d'] <= 410 and not r['via'], 'Cambiar el destino: la guía ahora va al punto tocado (%d m)' % r['d'])
        ok('Nuevo destino' in r['dijo'], 'y avisa "Nuevo destino"')
        # un punto sin camino: queda la ruta de antes
        r = await pg.evaluate("""async()=>{const f0=findRoute;findRoute=()=>({err:'nopath'});const ok=await navCambiar({dest:{lat:T.la+0.2,lon:T.lo0+0.2,label:'lejos'}});findRoute=f0;return {ok,dest:[NAV.dest.lat,NAV.dest.lon],L:T.L,on:NAV.on,d:Math.round(NAV.N.route.dist)};}""")
        ok(not r['ok'] and r['dest'] == r['L'] and r['on'] and 390 <= r['d'] <= 410, 'si no hay camino al punto nuevo, sigue con la ruta de antes')
        await pg.evaluate("endNav()")
        r = await pg.evaluate("""async()=>{const p=T.P(300,100);await onMapTap({latlng:{lat:p[0],lng:p[1]}});const v=id=>!$('#'+id).hidden;return {go:v('pinGo'),nv:v('pinNavVia'),nt:v('pinNavTo')};}""")
        ok(r['go'] and not r['nv'] and not r['nt'], 'sin guía, la tarjeta del punto vuelve a ser la de siempre')
        ok(not errs, 'sin errores JS: %s' % errs[:2])
        await b.close()
    srv.shutdown()
asyncio.run(main())
