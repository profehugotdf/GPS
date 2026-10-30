"""Buque naval (fuerzas navales de la base de Ushuaia) en Calcar: aparece entre los tipos, no entra al ruteo,
usa "Altura" como largo y viaja como elemento (`elems`, k:'naval') igual que los demás barcos."""
import asyncio, http.server, threading, functools, os
from playwright.async_api import async_playwright

SITE = os.environ.get('RUMBO_SITE', '.')


def ok(c, m):
    print(('  ✔ ' if c else '  ✘ ') + m)
    assert c, m


async def main():
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8797), functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    errs = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={'width': 412, 'height': 860})
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8797/index.html')
        await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("async()=>{await openTrace();}")
        ok(await pg.evaluate("!!document.querySelector('#trKind button[data-k=naval]')"), 'el tipo 🛡️ Buque naval aparece en Calcar')
        ok(await pg.evaluate("NOROUTE.has('naval')&&BARCOK.includes('naval')&&ELEMK.includes('naval')"), 'no se rutea y cuenta como barco (largo en "Altura")')
        ok(await pg.evaluate("userTags({kind:'naval',props:{}}).seamark")=='vessel', 'etiqueta seamark=vessel')
        await pg.evaluate("""async()=>{await DB.put('kv','edit:n1',{id:'n1',type:'path',kind:'naval',name:'ARA de prueba',pts:[[-54.8100,-68.3100],[-54.8100,-68.3090]],props:{alto:90},created:Date.now()});}""")
        r = await pg.evaluate("""async()=>{const P=[[-54.812,-68.312],[-54.812,-68.305]];const bb={s:-54.83,n:-54.79,w:-68.33,e:-68.29};const o=await elCollect(P,bb,900);
          return {list:o.list.map(e=>[e.k,e.n,e.a,e.m]),res:elResumen(o.list)}}""")
        print('   ', r)
        ok(any(x[0] == 'naval' and x[2] == 90 and x[3] == 1 for x in r['list']), 'viaja en `elems` con k:naval, largo 90 m y marca de "a mano"')
        ok('buque naval' in r['res'], 'el resumen lo nombra: %s' % r['res'])
    ok(not errs, 'sin errores de página %s' % errs)
    print('OK')

asyncio.run(main())
