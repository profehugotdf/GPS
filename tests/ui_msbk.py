import asyncio,http.server,threading,functools,json
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8791),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8791/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("""()=>{window.SENT=null;bkSend=async o=>{window.SENT={name:o.name,n:o.ll.length,first:o.ll[0],last:o.ll[o.ll.length-1],L:o.ll.reduce((s,p,i,a)=>i?s+hav(a[i-1],p):0,0)};};
          const la=-54.8;RT.from={lat:la,lon:-68.32};RT.to={lat:la,lon:-68.30};RT.calcFrom=RT.from;RT.sel='bike';S.roundTrip=true;
          RT.res={bike:{coords:[[la,-68.32],[la,-68.31],[la,-68.30]],dist:1280,time:300}};RT.back=null;
          openMeasure();MS.mode='dist';MS.pts=[[la,-68.2998],[la+0.0005,-68.299],[la+0.0007,-68.2995],[la+0.0004,-68.3002]];drawMeasure();}""")
        await pg.evaluate("document.querySelector('#msBk').click()");await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.querySelector('#sheet').innerText");print('  ',t.replace('\n',' | ')[:200])
        ok('La ruta con este pedazo' in t and 'vuelta' in t,'ofrece ruta + lo dibujado + vuelta')
        await pg.evaluate("document.querySelector('#sheet [data-act=all]').click()");await pg.wait_for_timeout(300)
        s=await pg.evaluate("SENT");print('  ',s)
        ok(s and abs(s['first'][1]+68.32)<1e-6 and abs(s['last'][1]+68.32)<1e-6 and s['L']>2600,'manda ida + retome + vuelta, empezando y terminando en A')
        print('ERRORES JS:',errs[:3] or 'ninguno');await b.close()
    srv.shutdown()
asyncio.run(main())
