import asyncio,http.server,threading,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8781),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8781/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("""async()=>{
          const la=-26.9,P=(i)=>[la,-65.30+i*0.005];
          const ways=[{id:1,t:{highway:'trunk',motorroad:'yes',ref:'RN38',name:'Autopista'},n:[1,2,3,4,5],p:[].concat(...[0,1,2,3,4].map(i=>P(i)))},
            {id:2,t:{highway:'residential',name:'Desvío'},n:[1,10,11,12,13,5],p:[la,-65.30, la+0.01,-65.30, la+0.01,-65.29, la+0.012,-65.285, la+0.01,-65.28, la,-65.28]}];
          await DB.put('kv','net:tst',{id:'tst',bb:{s:la-0.02,n:la+0.03,w:-65.32,e:-65.26},date:Date.now(),ways,hz:[]});
          lastFix={lat:la,lon:-65.29,t:Date.now()};netsChanged();dropGraph();}""")
        q="""async()=>{const g=await ensureGraph();const a=g.idx.get(1),z=g.idx.get(5),r={};for(const m of ['foot','bike','car']){const p=astar(g,m,a,z);r[m]=p?Math.round(p.edges.reduce((s,x)=>s+g.E[x.ei].len,0)):null;}return r;}"""
        r0=await pg.evaluate(q);print('   antes (m):',r0)
        ok(r0['car']<2100 and r0['foot']>2500 and r0['bike']>2500,'según OpenStreetMap: a pie y en bici dan la vuelta')
        await pg.evaluate("pickWayAt({lat:-26.9,lon:-65.2875})");await pg.wait_for_timeout(600)
        t=await pg.evaluate("document.querySelector('#sheet').innerText");print('  ',t.replace('\n',' | ')[:260])
        ok('Toda la ruta RN38' in t,'la hoja de la calle ofrece habilitar toda la RN38')
        await pg.evaluate("document.querySelector('[data-act=fbroad]').click()");await pg.wait_for_timeout(800)
        r1=await pg.evaluate(q);print('   después (m):',r1)
        ok(r1['foot']<2100 and r1['bike']<2100 and r1['car']==r0['car'],'a pie y en bici ahora van por la ruta; el auto igual')
        t=await pg.evaluate("document.querySelector('#sheet').innerText")
        ok('a pie y en bici por la banquina (toda la ruta)' in t,'aparece en Tus correcciones')
        # volver a lo que dice el mapa
        await pg.evaluate("pickWayAt({lat:-26.9,lon:-65.2875})");await pg.wait_for_timeout(600)
        ok('ya lo corregiste' in await pg.evaluate("document.querySelector('#sheet').innerText"),'la hoja avisa que ya está corregida')
        await pg.evaluate("document.querySelector('[data-act=reset]').click()");await pg.wait_for_timeout(800)
        r2=await pg.evaluate(q);ok(r2['foot']>2500,'"Volver a lo que dice el mapa" lo deshace')
        # un solo tramo
        await pg.evaluate("pickWayAt({lat:-26.9,lon:-65.2875})");await pg.wait_for_timeout(600)
        await pg.evaluate("document.querySelector('[data-act=fbseg]').click()");await pg.wait_for_timeout(800)
        r3=await pg.evaluate(q);print('   solo un tramo (m):',r3);ok(r3['foot']<2100,'habilitar solo este tramo (de cruce a cruce) también funciona')
        print('ERRORES JS:',errs[:3] or 'ninguno');await b.close()
    srv.shutdown()
asyncio.run(main())
