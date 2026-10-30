"""Rotonda dibujada a mano (Calcar → 🔄 Rotonda): centro + borde, círculo cerrado, de un solo sentido y
en el sentido del tránsito; las calles que llegan se pegan al anillo y Guiarme cuenta bien las salidas.

Red de juguete: 4 calles que llegan a un círculo de 15 m de radio (Oeste, Este, Norte, Sur).
Tránsito por la derecha: la rotonda gira al revés de las agujas del reloj (O → S → E → N).
"""
import asyncio, http.server, threading, functools, os
from playwright.async_api import async_playwright

SITE = os.environ.get('RUMBO_SITE', '.')


def ok(c, m):
    print(('  ✔ ' if c else '  ✘ ') + m)
    assert c, m


SETUP = """async()=>{
  const la=-54.8,lo0=-68.3,kx=111320*Math.cos(la*Math.PI/180);
  const P=(x,y)=>[+(la+y/110540).toFixed(6),+(lo0+x/kx).toFixed(6)];
  const C=P(200,0);
  const ways=[
    {id:1,t:{highway:'secondary',name:'Oeste'},n:[11,12],p:[...P(0,0),...P(185,0)]},
    {id:2,t:{highway:'secondary',name:'Este'},n:[21,22],p:[...P(215,0),...P(400,0)]},
    {id:3,t:{highway:'residential',name:'Norte'},n:[31,32],p:[...P(200,15),...P(200,200)]},
    {id:4,t:{highway:'residential',name:'Sur'},n:[41,42],p:[...P(200,-15),...P(200,-200)]}];
  window.T={la,lo0,P,C,W:P(0,0),E:P(400,0),N:P(200,200),S:P(200,-200),edge:P(200+25,0)};
  await DB.put('kv','net:tst',{id:'tst',bb:{s:la-.01,n:la+.01,w:lo0-.01,e:lo0+.02},date:Date.now(),ways,hz:[],sg:[]});
  await DB.del('kv','netidx:tst');netsChanged();
  window.R=async(a,b)=>{
    const g=await ensureGraph(),r=findRoute(g,'car',{lat:a[0],lon:a[1]},{lat:b[0],lon:b[1]},'fast');
    return {err:r.err,dist:Math.round(r.dist||0),steps:(r.steps||[]).map(s=>s.text)};
  };
  Object.assign(S,{timeMode:'model',pref:'fast',dataMode:'allow'});
}"""


async def main():
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8796), functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    errs = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={'width': 412, 'height': 860})
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8796/index.html')
        await pg.wait_for_function('!!window.__ok')
        await pg.evaluate(SETUP)

        print('1) Sin rotonda las 4 calles no se conectan')
        r = await pg.evaluate("async()=>R(T.W,T.N)")
        ok(bool(r['err']) or r['dist'] == 0, 'no hay ruta de Oeste a Norte (%s)' % r)

        print('2) Dibujar: centro y un punto del borde')
        await pg.evaluate("async()=>{await openTrace();TR.kind='rotonda';renderTraceKinds();}")
        ok(await pg.evaluate("!!document.querySelector('#trKind button[data-k=rotonda]')"), 'el tipo 🔄 Rotonda aparece en Calcar')
        ok(await pg.evaluate("document.querySelector('#trOw').hidden"), 'no se elige sentido (lo pone la app)')
        await pg.evaluate("traceTap({latlng:{lat:T.C[0],lng:T.C[1]}})")
        ok('centro' in await pg.evaluate("document.querySelector('#trInfo').textContent") or 'borde' in await pg.evaluate("document.querySelector('#trInfo').textContent"), 'después del centro pide el borde')
        await pg.evaluate("traceTap({latlng:{lat:T.edge[0],lng:T.edge[1]}})")   # a 25 m del centro
        await pg.wait_for_timeout(600)
        eds = await pg.evaluate("async()=>(await DB.all('kv','edit:')).filter(e=>e.kind==='rotonda')")
        ok(len(eds) == 1, 'se guardó una rotonda')
        e = eds[0]
        print('   ', len(e['pts']), 'puntos, oneway', e['oneway'])
        ok(e['oneway'] == 1 and len(e['pts']) == 29 and e['pts'][0] == e['pts'][-1], 'círculo cerrado de 28 tramos, un solo sentido')
        ccw = await pg.evaluate("(p)=>ringArea(p)>0", e['pts'])
        ok(ccw, 'gira al revés de las agujas del reloj (tránsito por la derecha)')
        rad = await pg.evaluate("(e)=>Math.round(hav(T.C,e.pts[0]))", e)
        ok(24 <= rad <= 26, 'el radio sale del borde tocado (%d m)' % rad)
        await pg.evaluate("async()=>{await DB.del('kv','edit:'+(await DB.all('kv','edit:')).find(e=>e.kind==='rotonda').id);dropGraph();}")

        print('3) Radio chico (15 m) para que las calles lleguen al anillo; dibujada en sentido horario se da vuelta')
        await pg.evaluate("""async()=>{
          TR.pts=rbRing(T.C,15,28).reverse();TR.snapped=TR.pts.map(()=>false);TR.strokes=[TR.pts.length];
          await traceSave();
        }""")
        e = (await pg.evaluate("async()=>(await DB.all('kv','edit:')).filter(e=>e.kind==='rotonda')"))[0]
        ok(await pg.evaluate("(p)=>ringArea(p)>0", e['pts']), 'dibujada al revés, se guardó antihoraria')
        g = await pg.evaluate("""async()=>{const g=await ensureGraph(),w=g.W.find(x=>x.id==='u:'+(window.__id||''))||g.W.find(x=>x.user&&x.tags.junction==='roundabout');
          return {closed:w.nodes[0]===w.nodes[w.nodes.length-1],n:w.nodes.length,rb:w.tags.junction}}""")
        ok(g['closed'] and g['rb'] == 'roundabout', 'en el grafo el anillo está cerrado (mismo nudo al principio y al final)')

        print('4) Rutas por la rotonda y salidas')
        cases = [('W', 'S', 1, 'primera'), ('W', 'E', 2, 'segunda'), ('W', 'N', 3, 'tercera'), ('N', 'W', 1, 'primera'), ('N', 'S', 2, 'segunda')]
        base = {}
        for a, bb, n, ord_ in cases:
            r = await pg.evaluate("async([a,b])=>R(T[a],T[b])", [a, bb])
            txt = [t for t in r['steps'] if 'rotonda' in t]
            print('  ', a, '→', bb, r['dist'], 'm', txt)
            ok(not r['err'] and r['dist'] > 0, '%s → %s tiene ruta' % (a, bb))
            ok(len(txt) == 1 and ord_ in txt[0], '%s → %s: %s salida' % (a, bb, ord_))
            base[(a, bb)] = r['dist']
        ok(base[('W', 'N')] - base[('W', 'S')] > 40, 'es de un solo sentido: Oeste→Norte da la vuelta larga (%d vs %d m)' % (base[('W', 'N')], base[('W', 'S')]))


    ok(not errs, 'sin errores de página %s' % errs)
    print('OK')

asyncio.run(main())
