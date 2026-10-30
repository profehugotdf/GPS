"""Semáforos: se traen de OpenStreetMap, se marcan a mano, suman espera por modo, la preferencia
"Menos semáforos" los esquiva, la ruta dice cuántos tiene y Guiarme los avisa.

Red de juguete: una calle recta de 600 m (Recta, con un semáforo a los 300 m) y un rodeo de 800 m (Rodeo, sin semáforos).
  auto  : recta = 90 s + espera;  rodeo = 120 s
  a pie : recta = 432 s + espera; rodeo = 576 s
"""
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


async def main():
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8795), functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    errs = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={'width': 412, 'height': 860})
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8795/index.html')
        await pg.wait_for_function('!!window.__ok')
        await pg.evaluate(SETUP)

        # ---------- 1. semáforo de OpenStreetMap (nodo 13, a 300 m) ----------
        print('1) Semáforo de OpenStreetMap suma espera por modo')
        await pg.evaluate("async()=>{await putNet([[13,...T.n13]]);}")
        car = await pg.evaluate("async()=>slim(await R('car','fast'))")
        print('  ', car)
        ok(car['sig'] == 1 and car['wait'] == 25 and car['k'] is True, 'en auto: 1 semáforo y 25 s de espera')
        ok(500 < car['dist'] < 700, 'en auto va por la recta (%d m)' % car['dist'])
        await pg.evaluate("S.sigCar=0;dropGraph()")
        car0 = await pg.evaluate("async()=>slim(await R('car','fast'))")
        ok(abs((car['time'] - car0['time']) - 25) < 0.01, 'la espera suma exactamente 25 s al tiempo (%.1f → %.1f)' % (car0['time'], car['time']))
        await pg.evaluate("S.sigCar=25;dropGraph()")
        foot = await pg.evaluate("async()=>slim(await R('foot','fast'))")
        bike = await pg.evaluate("async()=>slim(await R('bike','fast'))")
        print('   a pie', foot, '\n   bici', bike)
        ok(foot['sig'] == 1 and foot['wait'] == 15, 'a pie: espera de 15 s')
        ok(bike['sig'] == 1 and bike['wait'] == 20, 'en bici: espera de 20 s')

        # ---------- 2. la espera puede cambiar el camino; "Menos semáforos" lo esquiva ----------
        print('2) Preferencias')
        sh = await pg.evaluate("async()=>slim(await R('car','short'))")
        ok(sh['sig'] == 1 and sh['dist'] < 700, 'más corta: ignora los semáforos y va por la recta')
        ns = await pg.evaluate("async()=>slim(await R('car','nosig'))")
        print('   menos semáforos', ns)
        ok(ns['sig'] == 0 and 750 < ns['dist'] < 850, 'menos semáforos: rodea y no pasa por ninguno (%d m)' % ns['dist'])
        ok(ns['k'] is True and ns['wait'] == 0, 'sin semáforos en la ruta no suma espera')
        await pg.evaluate("S.sigCar=0;dropGraph()")
        ns0 = await pg.evaluate("async()=>slim(await R('car','nosig'))")
        ok(ns0['sig'] == 0 and ns0['dist'] > 750, 'con espera 0 igual esquiva los semáforos si se pide "Menos semáforos"')
        await pg.evaluate("S.sigCar=60;dropGraph()")
        big = await pg.evaluate("async()=>slim(await R('car','fast'))")
        ok(big['sig'] == 0 and big['dist'] > 750, 'con 60 s de espera más rápida conviene el rodeo (%d m)' % big['dist'])
        await pg.evaluate("S.sigCar=25;dropGraph()")
        for m in ('foot', 'bike'):
            r = await pg.evaluate("async(m)=>slim(await R(m,'nosig'))", m)
            ok(r['sig'] == 0 and r['dist'] > 750, 'menos semáforos también esquiva a pie y en bici (%s)' % m)
        names = await pg.evaluate("PREFS.map(p=>p[0])")
        ok('nosig' in names, 'la preferencia está en la lista: %s' % names)

        # ---------- 3. un mismo cruce marcado en cada acceso cuenta una sola vez ----------
        print('3) Un semáforo por acceso del mismo cruce')
        await pg.evaluate("async()=>{await putNet([[16,...T.n16],[41,...T.n41]]);}")
        two = await pg.evaluate("async()=>slim(await R('car','fast'))")
        print('  ', two)
        ok(two['sig'] == 1 and two['wait'] == 25, 'dos nodos del mismo cruce (a 10 m de la esquina) cuentan una sola espera')
        ok(two['dist'] < 700, 'y la ruta no da un rodeo por pagar la espera dos veces (%d m)' % two['dist'])
        lat = await pg.evaluate("async()=>slim(await R('car','fast',T.B,T.L))")
        ok(lat['sig'] == 1 and lat['wait'] == 25, 'entrando al cruce por un acceso y doblando por la calle lateral también cuenta una vez')
        sol = await pg.evaluate("async()=>{await putNet([[16,...T.n16]]);return slim(await R('car','fast',T.B,T.A));}")
        ok(sol['sig'] == 1, 'un semáforo suelto (sin otro cerca) queda donde está')
        await pg.evaluate("async()=>{await putNet([[13,...T.n13],[14,...T.P(450,0)]]);}")
        lejos = await pg.evaluate("async()=>slim(await R('car','short'))")
        ok(lejos['sig'] == 2, 'dos semáforos a 150 m son dos cruces distintos (%s)' % lejos['sig'])

        # ---------- 4. marcado a mano en Correcciones ----------
        print('4) Semáforo marcado a mano')
        await pg.evaluate("async()=>{await putNet(null);}")
        nodata = await pg.evaluate("async()=>slim(await R('car','fast'))")
        ok(nodata['sig'] == 0 and nodata['k'] is False, 'red bajada sin semáforos: no los cuenta ni muestra nada (sigK false)')
        await pg.evaluate("async()=>{await putNet([]);}")
        none = await pg.evaluate("async()=>slim(await R('car','fast'))")
        ok(none['sig'] == 0 and none['k'] is True, 'zona con semáforos conocidos y ninguno en la ruta: "sin semáforos" (sigK true)')
        await pg.evaluate("""async()=>{
          const q=T.P(225,0);NP.pt=[q[0],q[1]];NP.type='signal';NP.items=[];$('#npName').value='';await nodeSave();}""")
        eds = await pg.evaluate("DB.all('kv','edit:').then(l=>l.filter(e=>e.type==='signal').map(e=>({n:e.name})))")
        ok(len(eds) == 1 and eds[0]['n'] == 'Semáforo', 'se guardó la corrección tipo semáforo')
        man = await pg.evaluate("async()=>slim(await R('car','fast'))")
        print('  ', man)
        ok(man['sig'] == 1 and man['wait'] == 25 and man['k'] is True, 'el semáforo a mitad de cuadra se cuenta y suma 25 s')
        await pg.evaluate("showFix()");await pg.wait_for_timeout(300)
        txt = await pg.evaluate("document.querySelector('#sBody').innerText")
        ok('Semáforo' in txt, 'aparece en la lista de Correcciones')
        ok(await pg.evaluate("!!document.querySelector('#npType [data-t=signal]')"), 'la herramienta tiene el botón 🚦 Semáforo')
        await pg.evaluate("async()=>{for(const e of await DB.all('kv','edit:'))await DB.del('kv','edit:'+e.id);dropGraph();}")
        gone = await pg.evaluate("async()=>slim(await R('car','fast'))")
        ok(gone['sig'] == 0, 'al quitarla vuelve a no contarse')

        # ---------- 5. bajada de OpenStreetMap ----------
        print('5) Descarga de OpenStreetMap')
        await pg.evaluate("""()=>{
          window.__q=[];
          window.fetch=async(url,opt)=>{window.__q.push(opt.body.get('data'));return {ok:true,json:async()=>({elements:[
            {type:'way',id:7,nodes:[1,2],geometry:[{lat:-26.9,lon:-65.3},{lat:-26.9,lon:-65.301}],tags:{highway:'residential'}},
            {type:'node',id:1,lat:-26.9,lon:-65.3,tags:{highway:'traffic_signals'}},
            {type:'node',id:5,lat:-26.9001,lon:-65.3001,tags:{traffic_calming:'bump'}},
            {type:'node',id:6,lat:-26.9002,lon:-65.3002,tags:{highway:'crossing'}}]})};};}""")
        f = await pg.evaluate("fetchNet({s:-27,w:-65.4,n:-26.8,e:-65.2})")
        q0 = await pg.evaluate("window.__q[0]")
        ok('"highway"="traffic_signals"' in q0, 'la consulta pide los highway=traffic_signals')
        ok(f['sg'] == [[1, -26.9, -65.3]], 'guarda [id, lat, lon] solo de los semáforos: %s' % f['sg'])
        ok(len(f['hz']) == 1 and len(f['ways']) == 1, 'los lomos y las calles siguen como antes')
        await pg.evaluate("fetchNet({s:-27,w:-65.4,n:-26.8,e:-65.2},true).catch(()=>0)")
        q1 = await pg.evaluate("window.__q[1]")
        ok('traffic_signals' not in q1, 'la red regional (solo rutas) no pide semáforos')

        # ---------- 6. traer los semáforos de una red ya bajada ----------
        print('6) Traer los semáforos de lo ya bajado')
        await pg.evaluate("async()=>{await putNet(null);}")
        idx0 = await pg.evaluate("netIndex().then(l=>l.map(n=>n.sg))")
        ok(idx0 == [-1], 'una red vieja figura sin datos de semáforos (-1)')
        await pg.evaluate("showFix()");await pg.wait_for_timeout(300)
        ok(await pg.evaluate("!!document.querySelector('#sgdl')"), 'Correcciones ofrece "Traer los semáforos"')
        await pg.evaluate("window.__q=[]")
        r = await pg.evaluate("dlSignals()")
        print('  ', r)
        ok(r['ok'] == 1 and r['fail'] == 0 and r['tot'] == 3, 'bajó los semáforos de la zona (%s)' % r)
        qs = await pg.evaluate("window.__q[0]")
        ok('traffic_signals' in qs and 'way[' not in qs, 'pide solo nodos, no vuelve a bajar las calles')
        idx1 = await pg.evaluate("netIndex().then(l=>l.map(n=>n.sg))")
        ok(idx1 == [3], 'la red ahora figura con 3 semáforos')
        ok(not await pg.evaluate("(async()=>{await showFix();return !!document.querySelector('#sgdl');})()"), 'el botón desaparece cuando ya están')
        again = await pg.evaluate("dlSignals()")
        ok(again['zonas'] == 0, 'no repite las zonas que ya los tienen')

        # ---------- 7. lo que se ve en la ruta ----------
        print('7) Pantalla')
        await pg.evaluate("async()=>{await putNet([[13,...T.n13]]);}")
        await pg.evaluate("""async()=>{
          lastFix={lat:T.A[0],lon:T.A[1],t:Date.now()};
          RT.from={lat:T.A[0],lon:T.A[1],label:'A'};RT.to={lat:T.B[0],lon:T.B[1],label:'B'};S.routeMode='car';S.pref='fast';
          const g=await ensureGraph();await calcRoutes(g);RT.sel='car';computeAlt(g);}""")
        await pg.wait_for_timeout(300)
        html = await pg.evaluate("resultsHtml()")
        ok('🚦 1 semáforo' in html, 'la tarjeta de la ruta dice "🚦 1 semáforo"')
        ok('data-p="nosig"' in html, 'el comparador ofrece "Menos semáforos"')
        await pg.evaluate("rtPanel()");await pg.wait_for_timeout(200)
        pan = await pg.evaluate("document.querySelector('#rtp').innerText")
        ok('🚦 1 semáforo' in pan, 'el panel de la ruta también')
        await pg.evaluate("""async()=>{S.pref='nosig';const g=await ensureGraph();await calcRoutes(g,true);}""")
        html2 = await pg.evaluate("resultsHtml()")
        ok('🚦 sin semáforos' in html2, 'con "Menos semáforos" dice "🚦 sin semáforos"')
        await pg.evaluate("async()=>{await putNet(null);S.pref='fast';}")
        await pg.evaluate("showRoutes()");await pg.wait_for_timeout(500)
        t2 = await pg.evaluate("document.querySelector('#sBody').innerText")
        ok('Traer los semáforos' in t2, 'sin datos de semáforos, Rutas avisa cómo traerlos')
        await pg.evaluate("async()=>{await putNet([[13,...T.n13]]);}")
        await pg.evaluate("showRoutes()");await pg.wait_for_timeout(500)
        t3 = await pg.evaluate("document.querySelector('#sBody').innerText")
        ok('Traer los semáforos' not in t3, 'con datos, el aviso no aparece')

        # ---------- 8. Guiarme avisa ----------
        print('8) Guiarme')
        await pg.evaluate("S.pref='fast';S.sigVoice=true")
        res = await pg.evaluate("""async()=>{
          const r=(await R('car','fast')).route,N=navInit(r,'car',[]);
          const at=x=>{const q=T.P(x,0);return {lat:q[0],lon:q[1],speed:8};};
          const a=navTick(N,at(230)).say,b=navTick(N,at(232)).say;
          return {n:N.sgs.length,s:Math.round(N.sgs[0].s),a,b};}""")
        print('  ', res)
        ok(res['n'] == 1 and 280 < res['s'] < 320, 'la ruta tiene 1 semáforo a ~300 m del inicio')
        ok(any('Semáforo en' in x for x in res['a']), 'avisa por voz: %s' % res['a'])
        ok(not any('Semáforo' in x for x in res['b']), 'y no lo repite')
        foot = await pg.evaluate("""async()=>{
          const r=(await R('foot','fast')).route,N=navInit(r,'foot',[]);
          const at=x=>{const q=T.P(x,0);return {lat:q[0],lon:q[1],speed:1.4};};
          return {lejos:navTick(N,at(230)).say,cerca:navTick(N,at(275)).say};}""")
        ok(not any('Semáforo' in x for x in foot['lejos']) and any('Semáforo' in x for x in foot['cerca']), 'a pie avisa más cerca (a 25 m sí, a 70 m no)')
        mute = await pg.evaluate("""async()=>{S.sigVoice=false;const r=(await R('car','fast')).route;S.sigVoice=true;return navInit(Object.assign({},r),'car',[]).sgs.length+'/'+(()=>{S.sigVoice=false;const n=navInit(r,'car',[]).sgs.length;S.sigVoice=true;return n;})();}""")
        ok(mute == '1/0', 'se puede apagar el aviso en Ajustes (%s)' % mute)

        # ---------- 9. Ajustes ----------
        print('9) Ajustes')
        await pg.evaluate("showMore()");await pg.wait_for_timeout(300)
        vals = await pg.evaluate("['s20','s21','s22'].map(i=>document.getElementById(i)&&document.getElementById(i).value)")
        ok(vals == ['15', '20', '25'], 'tres campos de espera con los valores por defecto: %s' % vals)
        await pg.evaluate("""()=>{const e=document.getElementById('s21');e.value='33';e.dispatchEvent(new Event('change',{bubbles:true}));}""")
        ok(await pg.evaluate("S.sigBike") == 33, 'cambiar la espera en bici se guarda')
        await pg.evaluate("""()=>{const e=document.getElementById('s23');e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}""")
        ok(await pg.evaluate("S.sigVoice") is False, 'se puede apagar el aviso de voz')
        await pg.evaluate("""()=>{const e=document.getElementById('s22');e.value='999';e.dispatchEvent(new Event('change',{bubbles:true}));}""")
        ok(await pg.evaluate("S.sigCar") == 180, 'la espera tiene un tope razonable (180 s)')

        print('ERRORES JS:', errs[:3] or 'ninguno')
        assert not errs, errs[:3]
        await b.close()
    srv.shutdown()

asyncio.run(main())
