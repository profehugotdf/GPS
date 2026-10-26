# 🧲 Pegar a la costa: el borde de un área de mar entre dos puntos elegidos pasa a seguir la costa
# (Hugo: "¿cómo hago coincidir la costa con el área de mar?" — un área grande de pocos puntos cortaba la costa en recta)
import asyncio,http.server,threading,functools,os
from playwright.async_api import async_playwright
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8803),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8803/index.html');await pg.wait_for_function('!!window.__ok')
        # mar: un cuadrado al sur de la costa; su borde norte es una recta entre (-17.00,-101.0) y (-17.00,-100.0)
        # la costa real ondula al norte entre -16.97 y -16.99, en dos pedazos de OSM que hay que unir
        r=await pg.evaluate("""async()=>{
          const ar={type:'area',id:'mar1',kind:'agua',name:'Mar de prueba',pts:[[-17.0,-101.0],[-17.0,-100.5],[-17.0,-100.0],[-17.5,-100.0],[-17.5,-101.0]],props:{},created:Date.now()};
          await DB.put('kv','edit:mar1',ar);
          const C=[];for(let k=0;k<=60;k++){const lo=-101.05+k*0.0183;C.push([-16.98+0.01*Math.sin(k/3),lo]);}
          window.__osm=[C.slice(0,31),C.slice(30)];
          osmCoastNear=async()=>__osm.map(l=>l.slice());netAllowed=async()=>true;
          map.setView([-17.0,-100.5],9);
          await openVEdit('mar1');await new Promise(r=>setTimeout(r,300));
          return {vis:!$('#evSnapC').hidden,n:EV.pts.length};}""")
        ok(r['vis'],'en un área aparece 🧲 Pegar a la costa')
        await pg.evaluate("$('#evSnapC').click()");await pg.wait_for_timeout(200)
        ok(await pg.evaluate("EV.pts.length")==5,'sin elegir 2 puntos no cambia nada (pide elegirlos)')
        r=await pg.evaluate("""async()=>{EV.sels=new Set([0,2]);evDraw();await evSnapCoast();
          const P=EV.pts,north=P.filter(p=>p[0]>-17.0001);
          return {n:P.length,north:north.length,maxLat:Math.max(...P.map(p=>p[0])),hasMid:P.some(p=>Math.abs(p[0]+17)<1e-9&&Math.abs(p[1]+100.5)<1e-9),south:P.filter(p=>p[0]<-17.4).length,area:polyArea(P)};}""")
        print('   ',r)
        ok(r['north']>20 and r['maxLat']>-16.975,'el borde norte ahora ondula siguiendo la costa (dos pedazos de OSM unidos)')
        ok(not r['hasMid'],'el punto que cortaba en recta se reemplazó')
        ok(r['south']==2,'el resto del área queda igual')
        await pg.evaluate("$('#evUndo').click()");ok(await pg.evaluate("EV.pts.length")==5,'deshacer vuelve al área de antes')
        # con un trazo propio de costa cerca, usa ese y no baja nada
        r=await pg.evaluate("""async()=>{let bajo=0;osmCoastNear=async()=>{bajo++;return [];};
          await DB.put('kv','edit:c1',{type:'path',id:'c1',kind:'costa',name:'',pts:[[-16.99,-101.1],[-16.995,-100.5],[-16.99,-99.9]],props:{},created:Date.now()});
          EV.sels=new Set([0,2]);await evSnapCoast();return {bajo,n:EV.pts.length,has:EV.pts.some(p=>Math.abs(p[0]+16.995)<1e-6)};}""")
        ok(r['bajo']==0 and r['has'],'con un trazo de 🏖️ costa propio cerca, usa ese')
        await pg.evaluate("evSave()");await pg.wait_for_timeout(300)
        r=await pg.evaluate("(async()=>{const e=await DB.get('kv','edit:mar1');return e.pts.some(p=>Math.abs(p[0]+16.995)<1e-6)})()");ok(r,'✓ Guardar lo guarda')
        print('ERRORES JS:',errs[:3] or 'ninguno');ok(not errs,'sin errores');await b.close()
    srv.shutdown()
asyncio.run(main())
