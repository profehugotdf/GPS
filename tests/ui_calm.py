import asyncio,http.server,threading,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8790),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8790/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("""async()=>{const la=-54.8,d=0.0004;
          // avenida recta de 2 km y, al costado (40 m), una bicisenda un poco más larga que se une en las puntas
          const ways=[{id:1,t:{highway:'secondary',name:'Avenida'},n:[1,2,3],p:[la,-68.30,la,-68.29,la,-68.272]},
            {id:2,t:{highway:'cycleway',name:'Bicisenda'},n:[1,20,21,22,3],p:[la,-68.30,la-d*6,-68.296,la-d*7,-68.285,la-d*6,-68.276,la,-68.272]}];
          await DB.put('kv','net:tst',{id:'tst',bb:{s:la-0.02,n:la+0.02,w:-68.32,e:-68.26},date:Date.now(),ways,hz:[]});
          lastFix={lat:la,lon:-68.29,t:Date.now()};netsChanged();dropGraph();}""")
        q="""async(p)=>{const g=await ensureGraph();const r={};for(const m of ['bike','foot','car']){const x=findRoute(g,m,{lat:-54.8,lon:-68.30},{lat:-54.8,lon:-68.272},p);r[m]=x.err||((x.eids||[]).some(ei=>g.W[g.E[ei].w].hw==='cycleway')?'bicisenda':'avenida');}return r;}"""
        r0=await pg.evaluate(q,'fast');print('   más rápida:',r0)
        r1=await pg.evaluate(q,'calm');print('   por bicisendas:',r1)
        ok(r0['bike']=='avenida' and r1['bike']=='bicisenda','en bici: "Por bicisendas" va por la bicisenda')
        ok(r1['foot']=='bicisenda','a pie también')
        ok(r1['car']=='avenida','el auto sigue por la avenida')
        print('ERRORES JS:',errs[:3] or 'ninguno');await b.close()
    srv.shutdown()
asyncio.run(main())
