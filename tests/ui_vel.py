"""Velocidades aprendidas de las salidas en auto: se cruzan una sola vez con las calles guardadas, queda un resumen por
tipo de calle y franja horaria, se usa en el ruteo (según la hora de salida) y se pueden borrar los tracks ya procesados.

Red de juguete entre A y B:
  Principal (primary), recta de 1200 m:  modelo 13,3 m/s → 90 s
  Calle (residential), rodeo de 1800 m:  modelo 6,7 m/s  → 270 s
Salidas: Principal a 5 m/s por la mañana y a 10 m/s por la tarde; Calle a 12 m/s por la mañana.
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
  const nodes={101:P(0,0),102:P(200,0),103:P(400,0),104:P(600,0),105:P(800,0),106:P(1000,0),107:P(1200,0),201:P(0,300),202:P(1200,300)};
  const flat=ids=>ids.flatMap(i=>nodes[i]);
  const ways=[
    {id:1,t:{highway:'primary',name:'Principal'},n:[101,102,103,104,105,106,107],p:flat([101,102,103,104,105,106,107])},
    {id:2,t:{highway:'residential',name:'Calle'},n:[101,201,202,107],p:flat([101,201,202,107])}];
  await DB.put('kv','net:tst',{id:'tst',bb:{s:la-.02,n:la+.02,w:lo0-.02,e:lo0+.03},date:Date.now(),ways,hz:[],sg:[]});
  netsChanged();
  window.T={P,A:nodes[101],B:nodes[107]};
  window.drive=(poly,v,t0)=>{
    const cum=[0];for(let i=1;i<poly.length;i++)cum.push(cum[i-1]+Math.hypot(poly[i][0]-poly[i-1][0],poly[i][1]-poly[i-1][1]));
    const tot=cum[cum.length-1],pts=[];let seg=1;
    for(let k=0;k*v*2<=tot;k++){
      const s=k*v*2;while(seg<cum.length-1&&cum[seg]<s)seg++;
      const f=(s-cum[seg-1])/((cum[seg]-cum[seg-1])||1),x=poly[seg-1][0]+(poly[seg][0]-poly[seg-1][0])*f,y=poly[seg-1][1]+(poly[seg][1]-poly[seg-1][1])*f,q=P(x,y);
      pts.push([q[0],q[1],t0+k*2000,5,null,0]);
    }
    return pts;
  };
  window.putTrack=async(id,act,pts,name)=>{await DB.put('kv','track:'+id,{id,name:name||id,t0:pts[0][2],t1:pts[pts.length-1][2],pts,stats:calcStats(pts),act,circuitId:null,laps:[]});};
  const AM=new Date(2026,9,5,8,0,0).getTime(),PM=new Date(2026,9,5,15,0,0).getTime();
  const prim=[[0,0],[1200,0]],resi=[[0,0],[0,300],[1200,300],[1200,0]];
  await putTrack('t1','car',drive(prim,5,AM),'Mañana lenta');
  await putTrack('t2','car',drive(prim,10,PM),'Tarde fluida');
  await putTrack('t3','car',drive(resi,12,AM),'Por la calle');
  await putTrack('t4','bike',drive(prim,5,AM),'En bici');
  const far=drive(prim,10,AM).map(p=>[p[0]+1,p[1],p[2],p[3],p[4],p[5]]);
  await putTrack('t5','car',far,'Otra ciudad');
  Object.assign(S,{vlOn:false,sigCar:0,timeMode:'model',pref:'fast'});
  window.R=async()=>{const g=await ensureGraph(),r=findRoute(g,'car',{lat:T.A[0],lon:T.A[1]},{lat:T.B[0],lon:T.B[1]},'fast');return {dist:Math.round(r.dist),time:Math.round(r.time)};};
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

        # ---------- 1. sin lo aprendido, el modelo manda ----------
        print('1) Modelo')
        base = await pg.evaluate("R()")
        print('  ', base)
        ok(1100 < base['dist'] < 1300, 'por tipo de calle, la más rápida es la Principal (%d m)' % base['dist'])

        # ---------- 2. aprender desde Ajustes ----------
        print('2) Aprender de las salidas en auto')
        await pg.evaluate("showMore()");await pg.wait_for_timeout(400)
        ok(await pg.evaluate("!!document.getElementById('vlgo')&&!!document.getElementById('s24')"), 'Ajustes tiene el botón de aprender y el interruptor para usarlo')
        await pg.evaluate("document.getElementById('vlgo').click()")
        await pg.wait_for_function("document.getElementById('vlmsg')&&/Listo/.test(document.getElementById('vlmsg').textContent)", timeout=20000)
        msg = await pg.evaluate("document.getElementById('vlmsg').textContent")
        print('  ', msg)
        ok('3 salidas nuevas' in msg, 'procesó las 3 salidas en auto que cruzan con las calles')
        ok('1 no se pudo' in msg, 'avisa la que no pudo cruzar (otra ciudad, sin calles guardadas)')
        vl = await pg.evaluate("DB.get('kv','vel:car')")
        ok(sorted(vl['done'].keys()) == ['t1', 't2', 't3'], 'quedaron registradas solo las procesadas: %s' % sorted(vl['done'].keys()))
        bins = vl['bins']
        print('   bins:', {k: [round(x) for x in v] for k, v in bins.items()})
        ok('primary|x|1' in bins and 'primary|x|2' in bins and 'residential|x|1' in bins, 'resumen por tipo de calle, pendiente (x = sin altura) y franja')
        sp = lambda k: bins[k][0] / bins[k][1]
        ok(abs(sp('primary|x|1') - 5) < 0.4, 'Principal por la mañana: %.1f m/s' % sp('primary|x|1'))
        ok(abs(sp('primary|x|2') - 10) < 0.8, 'Principal por la tarde: %.1f m/s' % sp('primary|x|2'))
        ok(abs(sp('residential|x|1') - 12) < 1.0, 'Calle por la mañana: %.1f m/s' % sp('residential|x|1'))
        ok(not any(k.startswith('motorway') for k in bins), 'la salida en bici no entró')
        txt = await pg.evaluate("document.getElementById('vltab').innerText")
        print('  ', txt.replace('\n', ' | ')[:300])
        ok('Ruta o avenida principal' in txt and 'km/h' in txt and 'mañana' in txt and 'tarde' in txt, 'Ajustes muestra lo aprendido por tipo de calle y franja')

        # ---------- 3. no cuenta dos veces ----------
        print('3) Segunda pasada')
        before = await pg.evaluate("DB.get('kv','vel:car').then(v=>JSON.stringify(v.bins))")
        r2 = await pg.evaluate("vlLearn().then(x=>x.r)")
        after = await pg.evaluate("DB.get('kv','vel:car').then(v=>JSON.stringify(v.bins))")
        ok(r2['nuevas'] == 0 and before == after, 'volver a aprender no suma de nuevo las salidas ya procesadas')

        # ---------- 4. franjas ----------
        print('4) Velocidad por franja')
        s1 = await pg.evaluate("vlSpeeds(null,1)")
        ok(s1 == {}, 'sin datos no inventa velocidades')
        sm = await pg.evaluate("DB.get('kv','vel:car').then(v=>[vlSpeeds(v,1),vlSpeeds(v,2),vlSpeeds(v,0)])")
        print('  ', sm)
        ok(abs(sm[0]['primary'] - 5) < 0.4 and abs(sm[1]['primary'] - 10) < 0.8, 'la Principal es 5 m/s de mañana y 10 m/s de tarde')
        ok(abs(sm[2]['primary'] - 20 / 3) < 0.7, 'de madrugada no hay datos propios: usa el promedio de todo el día (%.1f m/s)' % sm[2]['primary'])
        ok(abs(sm[1]['residential'] - 12) < 1.0, 'si en una franja no hay datos suficientes de un tipo de calle, usa el de todo el día')

        # ---------- 5. se usan al rutear, según la hora de salida ----------
        print('5) Ruteo')
        await pg.evaluate("""()=>{const e=document.getElementById('s24');e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}));}""")
        ok(await pg.evaluate("S.vlOn") is True, 'el interruptor activa las velocidades aprendidas')
        await pg.evaluate("RT.dep='08:00'")
        am = await pg.evaluate("R()")
        await pg.evaluate("RT.dep='15:00'")
        pm = await pg.evaluate("R()")
        print('   08:00', am, ' 15:00', pm)
        ok(am['dist'] > 1700, 'a las 08:00 la Principal está lenta (5 m/s): conviene la Calle (%d m, %d s)' % (am['dist'], am['time']))
        ok(1100 < pm['dist'] < 1300, 'a las 15:00 la Principal anda a 10 m/s: conviene la Principal (%d m, %d s)' % (pm['dist'], pm['time']))
        ok(abs(am['time'] - 1800 / 12) < 25, 'el tiempo sale de la velocidad aprendida (%d s ≈ 150 s)' % am['time'])
        await pg.evaluate("""()=>{const e=document.getElementById('s24');e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}""")
        off = await pg.evaluate("RT.dep='08:00';R()")
        ok(1100 < off['dist'] < 1300, 'apagado, vuelve al modelo por tipo de calle')

        # ---------- 6. borrar solo lo procesado ----------
        print('6) Borrar los tracks ya procesados')
        ok(await pg.evaluate("[...document.querySelectorAll('#vltab button')].some(b=>/Borrar los 3 tracks/.test(b.textContent))"), 'ofrece borrar los 3 tracks de auto ya procesados')
        await pg.evaluate("document.querySelector('#vltab [data-act=vldel]').click()")
        ok(await pg.evaluate("DB.has('kv','track:t1')"), 'el primer toque solo pide confirmación: no borra')
        await pg.evaluate("document.querySelector('#vltab [data-act=vldel]').click()")
        await pg.wait_for_function("!document.querySelector('#vltab [data-act=vldel]')", timeout=10000)
        left = await pg.evaluate("DB.keys('kv','track:')")
        print('   quedan:', left)
        ok(sorted(left) == ['track:t4', 'track:t5'], 'se borraron solo los 3 de auto procesados; la salida en bici y la de otra ciudad siguen')
        ok(await pg.evaluate("DB.has('kv','vel:car')"), 'el resumen queda guardado')
        txt2 = await pg.evaluate("document.getElementById('vltab').innerText")
        ok('Ruta o avenida principal' in txt2, 'y se sigue viendo lo aprendido')
        again = await pg.evaluate("vlDeleteDone()")
        ok(again == 0, 'borrar de nuevo no hace nada')

        # ---------- 7. olvidar ----------
        print('7) Olvidar')
        await pg.evaluate("document.querySelector('#vltab [data-act=vlclr]').click()")
        await pg.evaluate("document.querySelector('#vltab [data-act=vlclr]').click()")
        await pg.wait_for_function("!document.querySelector('#vltab [data-act=vlclr]')", timeout=10000)
        ok(not await pg.evaluate("DB.has('kv','vel:car')"), 'se puede olvidar todo lo aprendido')

        print('ERRORES JS:', errs[:3] or 'ninguno')
        assert not errs, errs[:3]
        await b.close()
    srv.shutdown()

asyncio.run(main())
