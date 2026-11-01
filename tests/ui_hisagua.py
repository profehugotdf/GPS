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
        # playa de arena (relieve plano): la costa se orienta con la ruta del kayak y la tierra de su lado vale al menos 3,5 m (Hugo, Muelle Afasyn)
        r2=await pg.evaluate("""()=>{
          const costa=[[[-54.80,-68.30],[-54.80,-68.29],[-54.80,-68.28]]],costaRev=[[[-54.80,-68.28],[-54.80,-68.29],[-54.80,-68.30]]];
          const plano=()=>0.3,ref=[[-54.8004,-68.29]];                       // el kayak, en el agua: al sur
          const f=hisSeaFn(costa,[],[],plano,ref),g=hisSeaFn(costaRev,[],[],plano,ref),sinRef=hisSeaFn(costa,[],[],plano);
          const h=demPisoTierra(plano,f,3.5);
          return {mar:f(-54.8002,-68.29),tierra:f(-54.7998,-68.29),rev:g(-54.8002,-68.29)===true&&g(-54.7998,-68.29)===false,sinRef:sinRef===null,
            arena:h(-54.7998,-68.29),agua:h(-54.8002,-68.29),lejos:h(-54.70,-68.29),sin:demPisoTierra(plano,null,3.5)(-54.7998,-68.29)};}""")
        print('   ',r2)
        ok(r2['mar'] is True and r2['tierra'] is False and r2['rev'],'con la ruta en el agua la costa se orienta aunque el relieve sea plano (en cualquier sentido trazada)')
        ok(r2['sinRef'],'sin ruta y con relieve plano se ignora, como antes')
        ok(r2['arena']==3.5 and r2['agua']==0.3 and r2['lejos']==0.3 and r2['sin']==0.3,'la arena del lado de tierra sube a 3,5 m; el agua y lo lejano no se tocan')
        ok(r['nada'],'sin nada dibujado, null')
        # hisWater lee lo guardado (edit:)
        r=await pg.evaluate("""async()=>{
          await DB.put('kv','edit:h1',{id:'h1',type:'path',kind:'costa',pts:[[-54.80,-68.40],[-54.80,-68.30],[-54.80,-68.20]],created:1});
          await DB.put('kv','edit:h2',{id:'h2',type:'path',kind:'limite',pts:[[-54.70,-68.40],[-54.70,-68.20]],created:1});
          const f=await hisWater((la,lo)=>la>-54.80?40:0);return {mar:f(-54.801,-68.3),tierra:f(-54.799,-68.3),lim:f(-54.701,-68.3)};}""")
        print('   ',r)
        ok(r['mar'] is True and r['tierra'] is False and r['lim'] is None,'hisWater toma las costas guardadas (el 🚩 límite no cuenta)')
        # hisResumen: dice qué dibujó Hugo cerca de la ruta (para diagnosticar "marqué la costa y no aparece")
        r3=await pg.evaluate("""async()=>{
          await DB.put('kv','edit:h3',{id:'h3',type:'area',kind:'playa',pts:[[-54.801,-68.31],[-54.801,-68.30],[-54.8015,-68.305]],created:1});
          await DB.put('kv','edit:h4',{id:'h4',type:'path',kind:'costa',pts:[[-10,-10],[-10,-9]],created:1});   // lejos
          const f=await hisWater((la,lo)=>0.3,[[-54.8004,-68.30]]);
          const P=[[-54.8004,-68.31,0],[-54.8004,-68.30,60]];
          return {t:await hisResumen(P,f),vacio:await hisResumen([[-30,-30,0],[-30,-29.99,10]],null),info:f&&f.info};}""")
        print('   ',r3)
        ok('costa 1 (1 orientada)' in r3['t'] and 'área playa 1' in r3['t'] and 'costa 2' not in r3['t'],'hisResumen cuenta lo dibujado a ≤ 800 m de la ruta y las costas orientadas: %s'%r3['t'])
        ok(r3['vacio']=='nada dibujado cerca','sin nada cerca lo dice')
        ok(not errs,'sin errores JS: %s'%errs[:2])
        await b.close()
    s1.shutdown()
asyncio.run(main())
