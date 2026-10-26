# Lo usan otras personas: nada de valores de Hugo por defecto (destino de vuelo, peso para la potencia)
import asyncio,http.server,threading,functools,os
from playwright.async_api import async_playwright
SITE=os.environ.get('RUMBO_SITE','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8797),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8797/index.html');await pg.wait_for_function('!!window.__ok')
        d=await pg.evaluate("delete S.flDest;RT.to=null;flDest()");ok(d['def'] and 'elegí' in d['name'],'Modo vuelo: sin destino elegido no supone Ushuaia')
        await pg.evaluate("flStart()");await pg.evaluate("__ok({coords:{latitude:-34.6,longitude:-58.4,accuracy:5,altitude:20,speed:60,heading:0},timestamp:Date.now()});flDraw()")
        t=await pg.inner_text('#flt');ok('Destino' in t and 'Ushuaia' not in t,'el tablero pide elegir el destino')
        await pg.evaluate("S.flDest='EZE';flDraw()");t=await pg.inner_text('#flt');ok('Ezeiza' in t,'con destino elegido, lo muestra')
        await pg.evaluate("flStop()")
        w0=await pg.evaluate("localStorage.removeItem('bici_config');localStorage.removeItem('entrenamiento_perfil');bkCfg().w")
        w1=await pg.evaluate("localStorage.setItem('entrenamiento_perfil',JSON.stringify({pesoKg:61}));bkCfg().w")
        w2=await pg.evaluate("localStorage.setItem('bici_config',JSON.stringify({weight:80}));bkCfg().w")
        ok(w0==75 and w1==61 and w2==80,'peso para la potencia: neutro (%s), del perfil (%s), el de Bici si lo tiene (%s)'%(w0,w1,w2))
        ok(await pg.evaluate("!/Hugo/.test(document.body.innerHTML.replace(/<script[\\s\\S]*?<\\/script>/g,''))"),'no aparece "Hugo" en la página')
        print('ERRORES JS:',errs[:3] or 'ninguno');ok(not errs,'sin errores')
        await b.close()
    srv.shutdown()
asyncio.run(main())
