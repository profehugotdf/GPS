# Trazar ruta: un tramo que en bici da la vuelta por una mano única se marca "🚶 a pie" o "📏 en línea recta",
# y se respeta al pasar a Rutas y al volver a editar. (Hugo: "si elijo caminando hace el recorrido que quiero hacer en bicicleta")
import asyncio,http.server,threading,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8802),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8802/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("""async()=>{const la=-54.8,u=0.003;
          // avenida de oeste a este; la calle que sube al norte desde la rotonda es mano única BAJANDO (n4→n2);
          // para subir en bici hay que seguir hasta n3, subir y volver por arriba
          const ways=[{id:1,t:{highway:'primary',name:'Avenida'},n:[1,2,3],p:[la,-68.30,la,-68.29,la,-68.28]},
            {id:2,t:{highway:'residential',name:'Bajada',oneway:'yes'},n:[4,2],p:[la+u,-68.29,la,-68.29]},
            {id:3,t:{highway:'residential',name:'Este'},n:[3,5],p:[la,-68.28,la+u,-68.28]},
            {id:4,t:{highway:'residential',name:'Arriba'},n:[5,4],p:[la+u,-68.28,la+u,-68.29]}];
          await DB.put('kv','net:tst',{id:'tst',bb:{s:la-0.02,n:la+0.02,w:-68.32,e:-68.26},date:Date.now(),ways,hz:[]});
          lastFix={lat:la,lon:-68.30,t:Date.now()};netsChanged();dropGraph();}""")
        tap="(ll)=>plTap({latlng:{lat:ll[0],lng:ll[1]}})"
        W="async()=>{for(let i=0;i<100&&(PL.busy||PL.legs.length<plLegN());i++)await new Promise(r=>setTimeout(r,50));}"
        await pg.evaluate("RT.sel='bike';openPlanner(false)");await pg.wait_for_timeout(200)
        await pg.evaluate(tap,[-54.8,-68.30]);await pg.evaluate(tap,[-54.797,-68.29]);await pg.evaluate(W)
        await pg.evaluate("document.querySelector('#plMode [data-m=bike]').click()");await pg.evaluate(W)
        d0=await pg.evaluate("PL.legs[0].dist");o=await pg.inner_text('#plOut');print('   bici:',round(d0),'m ·',o.replace('\n',' | ')[:200])
        ok(d0>1800 and 'vuelta' in o and 'a pie' in o,'en bici da la vuelta por la mano única y sugiere el tramo a pie')
        await pg.evaluate("plLegTap(0)");h=await pg.inner_text('#plHint')
        ok('A pie (empujando' in h and 'En línea recta' in h,'tocando el tramo se puede elegir cómo va')
        await pg.evaluate("document.querySelector('#plLm [data-lm=foot]').click()");await pg.evaluate(W)
        r=await pg.evaluate("({d:PL.legs[0].dist,m:PL.legs[0].mode,lm:PL.lm[0],o:$('#plOut').innerText})");print('   a pie:',round(r['d']),r['m'],'·',r['o'].replace('\n',' | ')[:200])
        ok(r['d']<1100 and r['lm']=='foot','el tramo marcado a pie va directo (%d m)'%r['d'])
        ok('Tramos marcados' in r['o'] and '🚴' in r['o'],'la ruta sigue siendo en bici y muestra el tramo marcado')
        # un punto metido en el medio hereda la marca
        await pg.evaluate("plLegTap(0)");await pg.evaluate(tap,[-54.8,-68.29]);await pg.evaluate(W)
        ok(await pg.evaluate("PL.lm[0]==='foot'&&PL.lm[1]==='foot'"),'al meter un punto, las dos mitades quedan a pie')
        await pg.evaluate("$('#plUndo').click()");await pg.evaluate(W)
        ok(await pg.evaluate("PL.pts.length===2&&PL.lm[0]==='foot'"),'deshacer vuelve atrás también la marca')
        tot=await pg.evaluate("plSum().d")
        await pg.evaluate("plUse()");await pg.wait_for_timeout(800)
        r=await pg.evaluate("({sel:RT.sel,d:RT.res.bike&&RT.res.bike.dist,err:RT.res.bike&&RT.res.bike.err})");print('   Rutas:',r)
        ok(r['sel']=='bike' and not r['err'] and abs(r['d']-tot)<5,'en Rutas, la bici respeta el tramo a pie (%d m)'%(r['d'] or 0))
        await pg.evaluate("openPlanner(true)");await pg.evaluate(W)
        ok(await pg.evaluate("PL.lm[0]==='foot'&&PL.legs[0].dist<1100"),'✏️ desde la ruta trae la marca del tramo')
        # en línea recta
        await pg.evaluate("plLegTap(0)");await pg.evaluate("document.querySelector('#plLm [data-lm=line]').click()");await pg.evaluate(W)
        r=await pg.evaluate("({d:PL.legs[0].dist,s:hav(PL.pts[0],PL.pts[1]),n:PL.legs[0].coords.length})")
        ok(abs(r['d']-r['s'])<1 and r['n']==2,'en línea recta: derecho de un punto al otro')
        await pg.evaluate("plLegTap(0)");await pg.evaluate("document.querySelector('#plLm [data-lm=\"\"]').click()");await pg.evaluate(W)
        ok(await pg.evaluate("!PL.lm[0]&&PL.legs[0].dist>1800"),'"Como la ruta" lo vuelve a la normal')
        await pg.screenshot(path=BUILD+'/plft.png')
        # a pie: el botón Indoor deja elegir Correr o Bici Indoor
        await pg.evaluate("document.querySelector('#plMode [data-m=foot]').click()");await pg.evaluate(W)
        await pg.evaluate("window.__bk=[];bkSend=o=>{window.__bk.push(o)};$('#plBk').click()");await pg.wait_for_timeout(200)
        s=await pg.inner_text('#sheet');ok('Bici Indoor' in s and 'Correr' in s,'a pie: Indoor ofrece Correr o Bici Indoor')
        await pg.evaluate("document.querySelector('#sheet [data-act=bk]').click()");await pg.wait_for_timeout(200)
        r=await pg.evaluate("window.__bk.map(o=>({app:o.app||'bici',n:o.ll.length}))");ok(r and r[0]['app']=='bici' and r[0]['n']>=2,'manda el recorrido a pie a Bici Indoor')
        print('ERRORES JS:',errs[:3] or 'ninguno');ok(not errs,'sin errores');await b.close()
    srv.shutdown()
asyncio.run(main())
