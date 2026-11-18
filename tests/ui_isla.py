"""🏝️ Una 🌊 costa cerrada alrededor de una isla no es agua (Hugo, 18-nov: cerró la costa de una isla como superficie, quedó como 💧 agua
y Kayak aplanaba la isla entera).
- islaPorRelieve compara el relieve de adentro con el de afuera: isla = adentro más alto; lago o mar = adentro igual o más bajo;
- hisWater toma como tierra un área de agua armada con una costa que encierra una isla (arregla las que ya quedaron mal guardadas),
  pero un lago dibujado a mano en altura sigue siendo agua;
- hay un tipo de área nuevo, 🏝️ Tierra o isla, que cuenta como tierra."""
import asyncio,http.server,threading,functools,os
from playwright.async_api import async_playwright
SITE=os.environ.get('RUMBO_SITE','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    s1=http.server.ThreadingHTTPServer(('127.0.0.1',8798),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=s1.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8798/index.html');await pg.wait_for_function('!!window.__ok')
        r=await pg.evaluate("""async()=>{
          // isla de ~1 km alrededor de (-54.85,-68.45): adentro 30 m, afuera mar (0 m); lago en altura: adentro 300 m, alrededor 340 m
          const ring=[];for(let i=0;i<24;i++){const a=i/24*6.2832;ring.push([-54.85+Math.sin(a)*.005,-68.45+Math.cos(a)*.008]);}
          const dIsla=(la,lo)=>pip(la,lo,ring)?30:0, dLago=(la,lo)=>pip(la,lo,ring)?300:340, dPlano=()=>5;
          const res={isla:islaPorRelieve(ring,dIsla),lago:islaPorRelieve(ring,dLago),plano:islaPorRelieve(ring,dPlano),sin:islaPorRelieve(ring,()=>NaN)};
          await DB.put('kv','edit:ic',{id:'ic',type:'path',kind:'costa',pts:ring.concat([ring[0]]),created:1});
          await DB.put('kv','edit:ia',{id:'ia',type:'area',kind:'agua',pts:ring,members:[{id:'ic',rev:false}],created:1});
          // lago a mano (sin costa), 20 km al norte, en altura
          const lago=ring.map(q=>[q[0]+.2,q[1]]);
          await DB.put('kv','edit:la',{id:'la',type:'area',kind:'agua',pts:lago,created:1});
          const dem=(la,lo)=>pip(la,lo,ring)?30:pip(la,lo,lago)?300:(la>-54.7?340:0);
          const f=await hisWater(dem);
          res.centroIsla=f(-54.85,-68.45); res.centroLago=f(-54.65,-68.45); res.islas=f.info.islas;
          res.tipo=!!AREA_UI.tierra&&!!AREA_COL.tierra&&!!AREA_COLN.tierra;
          await DB.put('kv','edit:ia',{id:'ia',type:'area',kind:'tierra',pts:ring,created:1});
          const g=await hisWater(dem); res.tierraNueva=g(-54.85,-68.45);
          return res;}""")
        print('   ',r)
        ok(r['isla'] is True and r['lago'] is False,'islaPorRelieve: la isla (adentro más alto) es isla; el lago en altura (adentro más bajo) es agua')
        ok(r['plano'] is False and r['sin'] is None,'relieve parejo: agua (como antes); sin relieve: no se sabe')
        ok(r['centroIsla'] is False and r['islas']==1,'hisWater: el área de agua hecha con la costa de la isla cuenta como tierra')
        ok(r['centroLago'] is True,'un lago dibujado a mano sigue siendo agua aunque esté en altura')
        ok(r['tipo'] and r['tierraNueva'] is False,'el tipo nuevo 🏝️ Tierra o isla existe y cuenta como tierra')
        ok(not errs,'sin errores en la página: %s'%errs)
        await b.close()
    s1.shutdown()
asyncio.run(main())
