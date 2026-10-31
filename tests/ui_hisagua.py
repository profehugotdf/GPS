"""Lo que Hugo dibujó (🌊 Costa, 💧 agua, áreas de tierra) es la referencia de agua y tierra para Kayak:
- la costa sin sentido se orienta con el relieve (la tierra es el lado más alto) y baja a 0 m el agua del otro lado;
- un muelle dibujado pegado a la costa ya no aplana la playa de atrás (tierra segura = no se toca);
- las áreas de agua y de tierra mandan; lejos de lo dibujado no se sabe."""
import asyncio,http.server,threading,functools,os
from playwright.async_api import async_playwright
SITE=os.environ.get('RUMBO_SITE','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    s1=http.server.ThreadingHTTPServer(('127.0.0.1',8797),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=s1.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8797/index.html');await pg.wait_for_function('!!window.__ok')
        r=await pg.evaluate("""()=>{
          // costa recta oeste→este por lat -54.80; tierra al norte (40 m), mar al sur (0 m) con un cono falso de 60 m sobre el agua
          const dem=(la,lo)=>la>-54.80?40:(lo>-68.31&&lo<-68.29&&la>-54.8004?60:0);
          const dibujada=[[-54.80,-68.40],[-54.80,-68.30],[-54.80,-68.20]];
          const f=hisSeaFn([dibujada],[],[],dem),g=hisSeaFn([dibujada.slice().reverse()],[],[],dem);   // dibujada al revés: da igual
          const plano=hisSeaFn([dibujada],[],[],()=>10);
          const t=hisSeaFn([],[[[-54.9,-68.5],[-54.9,-68.4],[-54.8,-68.4],[-54.8,-68.5]]],[[[-54.87,-68.47],[-54.87,-68.43],[-54.83,-68.43],[-54.83,-68.47]]],dem);
          // muelle de 40 m que arranca 10 m adentro de la tierra (pegado a la costa): sin la referencia aplanaba la playa
          const muelle=elemMask([{k:'muelle',p:[[-54.79991,-68.30],[-54.8004,-68.30]]}]);
          const base=(la,lo)=>dem(la,lo),a=demSinElems(base,muelle),c=demSinElems(base,muelle,f);
          return {mar:f(-54.801,-68.35),tierra:f(-54.799,-68.35),rev:g(-54.801,-68.35)===true&&g(-54.799,-68.35)===false,lejos:f(-54.5,-68.35),plano:plano===null,
            agua:t(-54.85,-68.405),isla:t(-54.85,-68.45),fuera:t(-54.5,-68.45),
            playaSin:a(-54.79993,-68.30),playaCon:c(-54.79993,-68.30),
            piloteSin:a(-54.8002,-68.30),piloteCon:c(-54.8002,-68.30),   // sobre el agua el muelle sí aplana el pico
            nada:hisSeaFn([],[],[],dem)===null};}""")
        print('   ',r)
        ok(r['mar'] is True and r['tierra'] is False,'la costa dibujada se orienta con el relieve: el sur es agua y el norte tierra')
        ok(r['rev'],'da lo mismo en qué sentido la dibujaste')
        ok(r['lejos'] is None,'lejos de lo dibujado no se sabe')
        ok(r['plano'] is True,'con el relieve parejo no se puede orientar la costa: se ignora')
        ok(r['agua'] is True and r['isla'] is False and r['fuera'] is None,'área de agua = agua; el área de tierra adentro (isla) = tierra; afuera no se sabe')
        ok(r['playaSin']==0 and r['playaCon']==40,'el muelle pegado a la costa ya no aplana la playa: %s → %s'%(r['playaSin'],r['playaCon']))
        ok(r['piloteSin']==0 and r['piloteCon']==0,'sobre el agua el muelle sigue aplanando el pico')
        ok(r['nada'],'sin nada dibujado, null')
        # hisWater lee lo guardado (edit:)
        r=await pg.evaluate("""async()=>{
          await DB.put('kv','edit:h1',{id:'h1',type:'path',kind:'costa',pts:[[-54.80,-68.40],[-54.80,-68.30],[-54.80,-68.20]],created:1});
          await DB.put('kv','edit:h2',{id:'h2',type:'path',kind:'limite',pts:[[-54.70,-68.40],[-54.70,-68.20]],created:1});
          const f=await hisWater((la,lo)=>la>-54.80?40:0);return {mar:f(-54.801,-68.3),tierra:f(-54.799,-68.3),lim:f(-54.701,-68.3)};}""")
        print('   ',r)
        ok(r['mar'] is True and r['tierra'] is False and r['lim'] is None,'hisWater toma las costas guardadas (el 🚩 límite no cuenta)')
        ok(not errs,'sin errores JS: %s'%errs[:2])
        await b.close()
    s1.shutdown()
asyncio.run(main())
