import asyncio,http.server,threading,functools
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
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8791/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("""async()=>{const la=-54.8,d=0.004;
          // calle norte y calle sur, paralelas a ~450 m, unidas solo en las puntas (2 km); y una avenida al norte
          const ways=[{id:1,t:{highway:'residential',name:'Norte'},n:[1,2,3],p:[la,-68.30,la,-68.286,la,-68.272]},
            {id:2,t:{highway:'residential',name:'Sur'},n:[4,5,6],p:[la-d,-68.30,la-d,-68.286,la-d,-68.272]},
            {id:3,t:{highway:'residential',name:'Oeste'},n:[1,4],p:[la,-68.30,la-d,-68.30]},
            {id:4,t:{highway:'residential',name:'Este'},n:[3,6],p:[la,-68.272,la-d,-68.272]}];
          await DB.put('kv','net:tst',{id:'tst',bb:{s:la-0.02,n:la+0.02,w:-68.32,e:-68.26},date:Date.now(),ways,hz:[]});
          lastFix={lat:la,lon:-68.29,t:Date.now()};netsChanged();dropGraph();}""")
        tap="(ll)=>plTap({latlng:{lat:ll[0],lng:ll[1]}})"
        W="async()=>{for(let i=0;i<100&&(PL.busy||PL.legs.length<plLegN());i++)await new Promise(r=>setTimeout(r,50));}"
        await pg.evaluate("RT.sel='bike';openPlanner(false)");await pg.wait_for_timeout(200)
        ok(await pg.is_visible('#rplan'),'se abre el panel')
        await pg.evaluate(tap,[-54.8,-68.288]);await pg.evaluate(tap,[-54.804,-68.288]);await pg.evaluate(W)
        o=await pg.inner_text('#plOut');print('   ',o.replace('\n',' | '))
        ok('vuelta' in o,'avisa que el tramo da una vuelta')
        d0=await pg.evaluate("PL.legs[0].dist");print('   tramo A→B',round(d0))
        # tocar la línea del tramo y después donde quiero pasar
        await pg.evaluate("plLegTap(0)");h=await pg.inner_text('#plHint');ok('por dónde querés pasar' in h,'tocando la línea pide por dónde pasar')
        await pg.evaluate(tap,[-54.802,-68.272]);await pg.evaluate(W)
        pts=await pg.evaluate("PL.pts");ok(len(pts)==3 and abs(pts[1][1]+68.272)<1e-6,'el punto se mete en el medio del tramo (A, 1, B)')
        await pg.screenshot(path='plan_1.png')
        # deshacer
        await pg.evaluate("$('#plUndo').click()");await pg.evaluate(W);ok(await pg.evaluate("PL.pts.length")==2,'deshacer saca el punto insertado')
        await pg.evaluate("$('#plUndo').click()");await pg.evaluate("$('#plUndo').click()");ok(await pg.evaluate("PL.pts.length")==0,'deshacer hasta vaciar')
        # circuito de 3 puntos
        for ll in [[-54.8,-68.296],[-54.8,-68.276],[-54.804,-68.286]]:await pg.evaluate(tap,ll)
        await pg.evaluate("$('#plLoop').click()");await pg.evaluate(W)
        n=await pg.evaluate("[plLegN(),PL.legs.every(r=>r&&!r.err)]");ok(n==[3,True],'circuito: 3 tramos, el último vuelve a A')
        # seleccionar punto y moverlo
        await pg.evaluate("plPtTap(2)");ok(await pg.is_visible('#plDel'),'tocando un punto aparece Quitar')
        await pg.evaluate(tap,[-54.804,-68.29]);await pg.evaluate(W);ok(abs(await pg.evaluate("PL.pts[2][1]")+68.29)<1e-6 and await pg.evaluate("PL.pts.length")==3,'tocar el mapa mueve el punto elegido')
        # modo a pie
        await pg.evaluate("document.querySelector('#plMode [data-m=foot]').click()");await pg.evaluate(W)
        o=await pg.inner_text('#plOut');print('   ',o.replace('\n',' | '));ok('🚶' in o,'cambia a pie y recalcula')
        await pg.evaluate("document.querySelector('#plMode [data-m=bike]').click()");await pg.evaluate(W)
        tot=await pg.evaluate("plSum().d")
        # usar la ruta
        await pg.evaluate("plUse()");await pg.wait_for_timeout(800)
        r=await pg.evaluate("({st:RT.stops.map(s=>[s.label,s.stay]),to:RT.to.label,sel:RT.sel,d:RT.res.bike.dist,err:RT.res.bike.err,pan:!$('#rplan').hidden})");print('   ',r)
        ok(r['to']=='Punto A (llegada)' and len(r['st'])==2 and all(s[1]==0 for s in r['st']),'pasa a Rutas como A → 1 → 2 → A, solo pasar')
        ok(r['sel']=='bike' and not r['err'] and abs(r['d']-tot)<5,'misma ruta en Rutas (%d m vs %d m)'%(r['d'],tot))
        ok(not r['pan'],'cierra el panel')
        # editar la ruta de nuevo
        await pg.evaluate("openPlanner(true)");await pg.evaluate(W)
        r=await pg.evaluate("({n:PL.pts.length,loop:PL.loop,m:PL.mode})");ok(r=={'n':3,'loop':True,'m':'bike'},'✏️ desde la ruta trae los puntos y el circuito')
        await pg.screenshot(path='plan_2.png')
        await pg.evaluate("closePlanner()")
        # kayak sin agua
        await pg.evaluate("openPlanner(false)");await pg.evaluate(tap,[-54.8,-68.296]);await pg.evaluate(tap,[-54.8,-68.276])
        await pg.evaluate("document.querySelector('#plMode [data-m=kayak]').click()");await pg.evaluate(W);await pg.wait_for_timeout(300)
        o=await pg.inner_text('#plOut');print('   ',o.replace('\n',' | '));ok('⛔' in o,'kayak sin agua: lo dice')
        await pg.evaluate("closePlanner()")
        # rutas: botón
        await pg.evaluate("showRoutes()");await pg.wait_for_timeout(400);t=await pg.inner_text('#sheet');ok('Trazar punto por punto' in t,'botón en Rutas')
        print('ERRORES JS:',errs[:3] or 'ninguno');ok(not errs,'sin errores');await b.close()
    srv.shutdown()
asyncio.run(main())
