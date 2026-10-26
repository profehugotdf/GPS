import asyncio,http.server,threading,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8783),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8783/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("""async()=>{
          const la=-26.9,dn=0.0004;
          // autovía de dos calzadas de una mano: la de ida (sur, hacia el oeste) y la de vuelta (norte, hacia el este), unidas en las puntas
          const ways=[{id:1,t:{highway:'trunk',oneway:'yes',ref:'RP301'},n:[1,2,3,4],p:[la,-65.300,la,-65.32,la,-65.34,la,-65.36]},
            {id:2,t:{highway:'trunk',oneway:'yes',ref:'RP301'},n:[14,13,12,11],p:[la+dn,-65.36,la+dn,-65.34,la+dn,-65.32,la+dn,-65.300]},
            {id:3,t:{highway:'residential'},n:[4,14],p:[la,-65.36,la+dn,-65.36]},{id:4,t:{highway:'residential'},n:[11,1],p:[la+dn,-65.300,la,-65.300]}];
          await DB.put('kv','net:tst',{id:'tst',bb:{s:la-0.02,n:la+0.02,w:-65.37,e:-65.29},date:Date.now(),ways,hz:[]});
          await DB.put('kv','edit:acc_r_RP301',{type:'acc',id:'acc_r_RP301',scope:'road',ref:'RP301',created:Date.now()});
          lastFix={lat:la,lon:-65.30,t:Date.now()};netsChanged();dropGraph();
          RT.from={lat:la,lon:-65.3001,label:'Casa'};RT.to={lat:la,lon:-65.3599,label:'RP301'};S.routeMode='bike';S.roundTrip=true;RT.pExp=true;
          const g=await ensureGraph();await calcRoutes(g);}""")
        await pg.wait_for_timeout(500)
        r=await pg.evaluate("""(()=>{const f=RT.res.bike,b=backNow('bike'),c=backNow('car');return {ida:Math.round(f.dist),idaLat:+f.coords[Math.floor(f.coords.length/2)][0].toFixed(5),vuelta:b&&Math.round(b.dist),vueltaLat:b&&+b.coords[Math.floor(b.coords.length/2)][0].toFixed(5),car:!!c,txt:document.querySelector('#rtp').innerText.replace(/\\n/g,' | ').slice(0,300)}})()""")
        print('  ',r)
        ok(r['vuelta'] and r['idaLat']!=r['vueltaLat'],'la vuelta va por la otra calzada')
        ok('por otro camino' in r['txt'] or 'vuelta' in r['txt'],'el panel muestra el tiempo de la vuelta real')
        print('   src',await pg.evaluate("drawRoute.toString().slice(0,260)"));print('   S',await pg.evaluate("(()=>{const bq=S.roundTrip&&backNow(RT.sel);const src=drawRoute.toString();return [bq?bq.coords.length:null, src.includes('backNow'), src.length]})()"))
        await pg.evaluate("drawRoute(true)");await pg.wait_for_timeout(800);await pg.screenshot(path=BUILD+'/back_map.png')
        ok(await pg.evaluate("routesDiffer(RT.res.bike,backNow('bike'))"),'detecta que la vuelta va por la otra calzada (se dibuja en puntos)')
        await pg.evaluate("RT.pExp=true;rtPanel()");t=await pg.evaluate("document.querySelector('#rtp').innerText.replace(/\\n/g,' | ')");print('  ',t[:400])
        ok('por otro camino' in t,'detalle: "vuelta … por otro camino"')
        print('ERRORES JS:',errs[:3] or 'ninguno');await b.close()
    srv.shutdown()
asyncio.run(main())
