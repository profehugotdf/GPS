"""Giros, barreras y semáforos: los botones de tipo (Giro / Barrera / Semáforo) responden al toque de verdad."""
import asyncio, http.server, threading, functools, os
from playwright.async_api import async_playwright
SITE = os.environ.get('RUMBO_SITE', '.')
def ok(c, m):
    print(('  ✔ ' if c else '  ✘ ') + m); assert c, m
async def main():
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8799), functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    errs = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch(); pg = await b.new_page(viewport={'width': 412, 'height': 860})
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8799/index.html'); await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("async()=>{await openNodeTool();NP.pt=[-54.8,-68.3];NP.items=[];NP.type='barrier';drawNodeTool();}")
        r = await pg.evaluate("[...document.querySelectorAll('#npType button')].map(b=>[b.dataset.t,b.disabled])")
        print('   ', r)
        r = await pg.evaluate("""()=>{const out=[];for(const k of ['turn','barrier','signal']){const b=document.querySelector('#npType button[data-t='+k+']'),r=b.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2,el=document.elementFromPoint(x,y);out.push([k,Math.round(x),Math.round(y),el===b||b.contains(el)?'ok':(el&&(el.id||el.className||el.tagName))]);}return out;}""")
        print('   ', r)
        ok(all(x[3] == 'ok' for x in r), 'ningún elemento tapa los botones de tipo: %s' % r)
        await pg.locator('#npType button[data-t=signal]').click()
        r = await pg.evaluate("({t:NP.type,on:[...document.querySelectorAll('#npType button.on')].map(b=>b.dataset.t),info:document.querySelector('#npInfo').textContent.slice(0,30),bar:document.querySelector('#npBar').hidden})")
        print('   ', r)
        ok(r['t'] == 'signal' and r['on'] == ['signal'] and r['bar'] is True, 'tocar 🚦 Semáforo lo elige y esconde las casillas de la barrera: %s' % r)
        ok(await pg.evaluate("NP.pick") == 'signal', 'la elección queda recordada para el próximo punto')
        await pg.locator('#npType button[data-t=barrier]').click()
        ok(await pg.evaluate("NP.type") == 'barrier', 'y se puede volver a ⛔ Barrera')
        ok(not errs, 'sin errores: %s' % errs[:2])
        await b.close()
    srv.shutdown()
asyncio.run(main())
