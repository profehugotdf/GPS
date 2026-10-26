import asyncio,http.server,threading,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8786),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("""window.__n=0;navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;window.__n++;return window.__n};navigator.geolocation.clearWatch=()=>{};
          navigator.geolocation.getCurrentPosition=(ok,err,o)=>{window.__opt=o;setTimeout(()=>ok({coords:{latitude:-34.5592,longitude:-58.4156,accuracy:900}}),50);};""")
        await pg.goto('http://127.0.0.1:8786/index.html');await pg.wait_for_function('!!window.__ok')
        # última lectura de GPS: en vuelo sobre Santa Fe, hace 3 minutos
        await pg.evaluate("__ok({coords:{latitude:-31.6,longitude:-60.7,accuracy:10,altitude:9000,speed:220,heading:150},timestamp:Date.now()});lastFixWall=Date.now()-180000;watch.t0=Date.now()-200000;APX.t=0;APX.restart=0;")
        n0=await pg.evaluate("__n")
        await pg.evaluate("apxTick()");await pg.wait_for_timeout(400)
        r=await pg.evaluate("({apx:APX.last,pill:$('#pill').innerText,opt:window.__opt,pos:{lat:posMk.getLatLng().lat},n:__n})");print('  ',r)
        ok(r['apx'] and abs(r['apx']['lat']+34.5592)<1e-3,'sin GPS: el punto pasa a Aeroparque (posición por antenas)')
        ok('antenas' in r['pill'] and '900' in r['pill'],'el cartel dice "≈ ±900 m (antenas)"')
        ok(r['opt']['enableHighAccuracy'] is False,'pide la posición de red (no GPS)')
        ok(r['n']>n0,'reinicia el GPS trabado')
        ok(await pg.evaluate("REC.pts.length")==0,'no se graba en el track')
        # vuelve el GPS
        await pg.evaluate("__ok({coords:{latitude:-34.559,longitude:-58.416,accuracy:6},timestamp:Date.now()})")
        r=await pg.evaluate("({apx:APX.last,pill:$('#pill').innerText})");ok(r['apx'] is None and 'GPS ±6' in r['pill'],'cuando vuelve el GPS, manda él')
        print('ERRORES JS:',errs[:3] or 'ninguno');await b.close()
    srv.shutdown()
asyncio.run(main())
