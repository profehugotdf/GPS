"""Horizontal (teléfono acostado, 780×360): la tarjeta de la ruta, la de Guiarme y los botones del mapa no tapan el mapa
ni se salen de la pantalla. En vertical queda todo como estaba."""
import asyncio, http.server, threading, functools, os
from playwright.async_api import async_playwright

SITE = os.environ.get('RUMBO_SITE', '.')


def ok(c, m):
    print(('  ✔ ' if c else '  ✘ ') + m)
    assert c, m


SETUP = """async()=>{
  const la=-26.9,lo0=-65.3,kx=111320*Math.cos(la*Math.PI/180);
  const P=(x,y)=>[+(la+y/110540).toFixed(6),+(lo0+x/kx).toFixed(6)];
  const n11=P(0,0),n12=P(150,0),n16=P(290,0),n13=P(300,0),n41=P(310,0),n14=P(450,0),n15=P(600,0),n21=P(0,100),n22=P(600,100),n31=P(300,-100);
  const ways=[
    {id:1,t:{highway:'residential',name:'Recta'},n:[11,12,16,13,41,14,15],p:[...n11,...n12,...n16,...n13,...n41,...n14,...n15]},
    {id:2,t:{highway:'residential',name:'Rodeo'},n:[11,21,22,15],p:[...n11,...n21,...n22,...n15]},
    {id:3,t:{highway:'residential',name:'Lateral'},n:[13,31],p:[...n13,...n31]}];
  window.T={la,lo0,P,ways,n13,n16,n41,A:P(0,0),B:P(600,0),L:n31};
  window.putNet=async(sg)=>{
    const n={id:'tst',bb:{s:la-.01,n:la+.01,w:lo0-.01,e:lo0+.02},date:Date.now(),ways,hz:[]};
    if(sg)n.sg=sg;
    await DB.put('kv','net:tst',n);await DB.del('kv','netidx:tst');netsChanged();
  };
  window.R=async(m,p,a,b)=>{
    a=a||T.A;b=b||T.B;
    const g=await ensureGraph(),r=findRoute(g,m,{lat:a[0],lon:a[1]},{lat:b[0],lon:b[1]},p);
    return {err:r.err,sig:r.sig,wait:r.sigWait,time:r.time,dist:Math.round(r.dist),k:r.sigK,pts:(r.sigPts||[]).length,route:r};
  };
  window.slim=o=>{const x=Object.assign({},o);delete x.route;return x;};
  Object.assign(S,{sigFoot:15,sigBike:20,sigCar:25,timeMode:'model',pref:'fast',sigVoice:true,dataMode:'allow'});
}"""

BOX = "(s)=>{const e=document.querySelector(s);if(!e||e.hidden)return null;const r=e.getBoundingClientRect();return {l:r.left,t:r.top,r:r.right,b:r.bottom,w:r.width,h:r.height}}"


async def prep(pg):
    await pg.evaluate(SETUP)
    await pg.evaluate("async()=>{await putNet([[13,...T.n13]]);}")
    await pg.evaluate("""async()=>{lastFix={lat:T.A[0],lon:T.A[1],t:Date.now()};
      RT.from={lat:T.A[0],lon:T.A[1],label:'A'};RT.to={lat:T.B[0],lon:T.B[1],label:'B'};S.routeMode='car';S.pref='fast';
      const g=await ensureGraph();await calcRoutes(g);RT.sel='car';computeAlt(g);rtPanel();}""")
    await pg.wait_for_timeout(400)


async def main():
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8798), functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    errs = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        for nombre, W, H in (('horizontal', 780, 360), ('vertical', 412, 860)):
            print(nombre)
            pg = await b.new_page(viewport={'width': W, 'height': H})
            pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
            await pg.goto('http://127.0.0.1:8798/index.html')
            await pg.wait_for_function('!!window.__ok')
            await prep(pg)
            rtp = await pg.evaluate(BOX, '#rtp')
            fabs = await pg.evaluate(BOX, '#fabs')
            dock = await pg.evaluate(BOX, '#dock')
            print('   rtp', rtp, '\n   fabs', fabs, '\n   dock', dock)
            ok(fabs['t'] >= 0 and fabs['b'] <= dock['t'] + 40, 'los botones del mapa entran en la pantalla')
            ok(rtp['r'] <= fabs['l'] + 1, 'la tarjeta de la ruta no pisa los botones del mapa')
            if nombre == 'horizontal':
                ok(rtp['h'] < H * 0.4, 'la tarjeta de la ruta ocupa menos del 40 por ciento de la altura (%d de %d px)' % (rtp['h'], H))
                ok(dock['h'] < 60, 'el dock es finito (%d px)' % dock['h'])
            await pg.evaluate("startNav()")
            await pg.wait_for_timeout(800)
            nav = await pg.evaluate(BOX, '#nav')
            fabs = await pg.evaluate(BOX, '#fabs')
            print('   nav', nav)
            if nombre == 'horizontal':
                ok(nav and nav['r'] <= fabs['l'] + 1, 'la tarjeta de Guiarme no tapa los botones del mapa')
                ok(nav['w'] < W * 0.6 and nav['h'] < H * 0.45, 'Guiarme en horizontal es una columna angosta (%d×%d)' % (nav['w'], nav['h']))
            await pg.close()
    ok(not errs, 'sin errores de página %s' % errs)
    print('OK')

asyncio.run(main())
