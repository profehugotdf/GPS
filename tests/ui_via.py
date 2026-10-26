import asyncio,http.server,threading,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8782),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8782/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("""async()=>{
          const la=-26.9;
          // casa (1) – vecino (2) a 45 m, y la ruta que sale 6 km al oeste (3..6), solo autos según OSM, que habilitaste a pie y en bici
          const ways=[{id:1,t:{highway:'residential',name:'9 de Julio'},n:[1,2],p:[la,-65.300,la,-65.3005]},
            {id:2,t:{highway:'trunk',motorroad:'yes',ref:'RP301'},n:[2,3,4,5,6],p:[la,-65.3005,la,-65.315,la,-65.33,la,-65.345,la,-65.36]}];
          await DB.put('kv','net:tst',{id:'tst',bb:{s:la-0.02,n:la+0.02,w:-65.37,e:-65.29},date:Date.now(),ways,hz:[]});
          await DB.put('kv','edit:acc_r_RP301',{type:'acc',id:'acc_r_RP301',scope:'road',ref:'RP301',created:Date.now()});
          lastFix={lat:la,lon:-65.30,t:Date.now()};netsChanged();dropGraph();
          RT.from={lat:la,lon:-65.3000,label:'Casa'};RT.to={lat:la,lon:-65.3005,label:'Casa (vuelta)'};S.routeMode='car';
          const g=await ensureGraph();await calcRoutes(g);RT.sel='car';resetCands();
          await addViaAt({lat:la,lon:-65.36});}""")
        await pg.wait_for_timeout(500)
        r=await pg.evaluate("({sel:RT.sel,car:Math.round(RT.res.car.dist),via:Object.fromEntries(Object.entries(RT.via.res).map(([k,v])=>[k,v.err||Math.round(v.dist)]))})")
        print('  ',r)
        ok(r['car']>11000,'en auto: ida y vuelta pasando por el punto (%d m)'%r['car'])
        ok(isinstance(r['via']['bike'],int) and r['via']['bike']>11000,'en bici también se calcula pasando por el punto')
        await pg.evaluate("rtPanel()");await pg.wait_for_timeout(300)
        chips=await pg.evaluate("[...document.querySelectorAll('#rtp [data-r^=\"m:\"]')].map(b=>b.textContent)");print('   botones:',chips)
        ok(any('🚴' in c and 'min' in c for c in chips),'el botón de bici muestra el tiempo con el desvío (no "21 s")')
        await pg.evaluate("document.querySelector('#rtp [data-r=\"m:bike\"]').click()");await pg.wait_for_timeout(500)
        r2=await pg.evaluate("({sel:RT.sel,d:Math.round(RT.res.bike.dist),txt:document.querySelector('#rtp').innerText.slice(0,120)})");print('  ',r2)
        ok(r2['sel']=='bike' and r2['d']>11000,'al tocar 🚴, la ruta en bici sigue pasando por el punto')
        print('ERRORES JS:',errs[:3] or 'ninguno');await b.close()
    srv.shutdown()
asyncio.run(main())
