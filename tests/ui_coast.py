import asyncio,http.server,threading,functools,os,sys
from playwright.async_api import async_playwright
SITE=os.environ.get('RUMBO_SITE','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    s1=http.server.ThreadingHTTPServer(('127.0.0.1',8796),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=s1.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8796/index.html');await pg.wait_for_function('!!window.__ok')
        # costa recta de oeste a este por lat -54.80: en OSM la tierra queda a la izquierda (norte), el mar a la derecha (sur)
        r=await pg.evaluate("""()=>{
          const ways=[[[-54.80,-68.40],[-54.80,-68.30],[-54.80,-68.20]]],f=coastSeaFn(ways);
          const fh=coastSeaFn([[[-54.80,-68.20],[-54.80,-68.30]]]);   // al revés: la tierra queda al sur
          const base=(la,lo)=>la>-54.80?40:(lo>-68.31&&lo<-68.29&&la>-54.81?60:0);       // tierra al norte + un cono falso de 60 m sobre el agua
          const g=demSinMar(base,f);
          return {mar:f(-54.81,-68.30),tierra:f(-54.79,-68.30),punta:f(-54.80,-68.4001),lejos:f(-54.5,-68.3),
            conv:(()=>{const c=coastSeaFn([[[-54.80,-68.30],[-54.80,-68.29],[-54.79,-68.29]]]);return [c(-54.8001,-68.2899+.0003),c(-54.7950,-68.2950)];})(),   // costa al este y después al norte: la tierra queda adentro del giro, el afuera (sudeste) es mar
inv:fh(-54.81,-68.30),vacio:coastSeaFn([])===null,
            cono:g(-54.805,-68.30),tierraAlt:g(-54.79,-68.30),sinCosta:demSinMar(base,null)(-54.805,-68.30),nan:isNaN(demSinMar(()=>NaN,f)(-54.81,-68.3)),fondo:demSinMar(()=>-30,f)(-54.81,-68.3)};}""")
        print('   ',r)
        ok(r['mar'] is True and r['tierra'] is False,'costa de OSM: el sur es mar y el norte tierra')
        ok(r['conv'][0] is True and r['conv'][1] is False,'esquina de la costa: afuera del giro es mar, adentro es tierra: %s'%r['conv'])
        ok(r['inv'] is False,'el sentido del tramo manda: al revés, el sur es tierra')
        ok(r['lejos'] is None and r['vacio'],'lejos de la costa (>4 km) o sin costa: no se sabe')
        ok(r['cono']==0 and r['tierraAlt']==40,'el cono falso sobre el agua se aplana y la tierra queda igual')
        ok(r['sinCosta']==60,'sin costa, el relieve queda como estaba')
        ok(r['nan'] and r['fondo']==-30,'sin dato sigue sin dato y el fondo del mar no se toca')
        # coastSea: baja la costa con bkOver (falso), la guarda, y la segunda vez sale del caché
        r=await pg.evaluate("""async()=>{let n=0;bkOver=async(q)=>{n++;return [{type:'way',id:1,tags:{natural:'coastline'},geometry:[{lat:-54.80,lon:-68.40},{lat:-54.80,lon:-68.20}]}];};
          const bb={n:-54.78,s:-54.83,w:-68.35,e:-68.25},a=await coastSea(bb),b=await coastSea(bb);return {n,mar:a(-54.81,-68.3),mar2:b(-54.81,-68.3)};}""")
        print('   ',r)
        ok(r['n']==1 and r['mar'] is True and r['mar2'] is True,'coastSea pide la costa una sola vez y la guarda')
        # 3D: la malla aplana el pico falso sobre el agua
        r=await pg.evaluate("""()=>{const calls=[];const t=new Float32Array(65536).fill(0);t[100*256+100]=80;   // un pico de 80 m en un píxel
          Object.assign(T3,{N:1,step:2,x0:0,y0:0,zd:0,half:128,mpp:1,gl:null});
          let H=null;t3MeshBuf=()=>{H=T3.H;};t3TexInit=()=>{};T3.gl={};
          t3Mesh(new Map([['0/0',t]]),()=>true);const a=Math.max(...H);
          t3Mesh(new Map([['0/0',t]]),null);const b=Math.max(...H);t3Flat(()=>true);const c=Math.max(...H);return {a,b,c};}""")
        print('   ',r)
        ok(r['a']==0 and r['b']==80 and r['c']==0,'3D: el pico sobre el agua se aplana (y sin costa queda igual)')
        ok(not errs,'sin errores JS: %s'%errs[:2])
        await b.close()
    s1.shutdown()
asyncio.run(main())
