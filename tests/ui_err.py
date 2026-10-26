# 🐞 Registro de errores: lo que antes fallaba en silencio queda anotado y se ve en Diagnóstico
import asyncio,http.server,threading,functools,os
from playwright.async_api import async_playwright
SITE=os.environ.get('RUMBO_SITE','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8796),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8796/index.html');await pg.wait_for_function('!!window.__ok');await pg.wait_for_timeout(500)
        n0=await pg.evaluate("ERRS.list.length")
        # un catch que antes era mudo: el guardián con un dato roto
        print('   al arrancar:',await pg.evaluate("ERRS.list.map(x=>x.msg+' @ '+x.donde)"))
        await pg.evaluate("window.__f=()=>{try{null.x}catch(e){errLog(e)}};__f();__f()")
        r=await pg.evaluate("ERRS.list.slice(-1)[0]");ok(r['n']==2 and 'null' in r['msg'],'anota y cuenta los repetidos (×%d)'%r['n'])
        # promesa sin atrapar
        await pg.evaluate("setTimeout(()=>Promise.reject(new Error('falla de prueba en una promesa')),0)");await pg.wait_for_timeout(300)
        ok(await pg.evaluate("ERRS.list.some(x=>/falla de prueba en una promesa/.test(x.msg))"),'atrapa las promesas sin catch')
        # grave: avisa en pantalla
        await pg.evaluate("errLog(new Error('disco lleno'),'Guardado automático de la grabación',true)")
        t=await pg.inner_text('#toast');ok('disco lleno' in t and 'Diagnóstico' in t,'lo grave avisa en pantalla')
        # guardar una grabación que falla: no se pierde, avisa
        await pg.evaluate("""()=>{const t0=Date.now()-60000;REC.state='pause';REC.pts=[[-54.8,-68.3,t0],[-54.801,-68.3,t0+30000],[-54.802,-68.3,t0+60000]];REC.id='rtest';REC.t0=t0;
          window.__put=DB.put;DB.put=async(st,k,v)=>{if(String(k).startsWith('track:'))throw new Error('QuotaExceededError');return window.__put(st,k,v);};}""")
        await pg.evaluate("stopFlow()");await pg.wait_for_timeout(300)
        await pg.click('#sBody [data-act=save]');await pg.wait_for_timeout(600)
        t=await pg.inner_text('#toast');ok('No se pudo guardar' in t,'si guardar falla, avisa')
        ok(await pg.evaluate("REC.pts.length")==3,'la grabación sigue en memoria')
        await pg.evaluate("DB.put=window.__put;closeSheet()")
        # Diagnóstico
        await pg.evaluate("showDiag()");await pg.wait_for_timeout(200)
        t=await pg.inner_text('#dgErr');ok('disco lleno' in t and '×2' in t,'se ve en Diagnóstico')
        # se guarda y vuelve al recargar
        await pg.evaluate("errSave()");await pg.wait_for_timeout(400)
        await pg.reload();await pg.wait_for_function('!!window.__ok');await pg.wait_for_timeout(800)
        ok(await pg.evaluate("ERRS.list.some(x=>x.msg==='disco lleno')"),'queda guardado al recargar')
        d=await pg.evaluate("errDump()");ok('GRAVE disco lleno' in d,'texto para copiar')
        print('ERRORES JS:',errs[:3] or 'ninguno')   # acá se generan errores a propósito: no se exige que no haya
        await b.close()
    srv.shutdown()
asyncio.run(main())
