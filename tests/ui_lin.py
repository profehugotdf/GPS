import asyncio,http.server,threading,functools,os,sys
from playwright.async_api import async_playwright
SITE=os.environ.get('RUMBO_SITE','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    s1=http.server.ThreadingHTTPServer(('127.0.0.1',8799),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=s1.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8799/index.html');await pg.wait_for_function('!!window.__ok')
        r=await pg.evaluate("""()=>{
          const la=-54.80,lo=-68.30,K=111320,kc=Math.cos(la*Math.PI/180);
          const P=[];for(let i=0;i<=20;i++)P.push([la,lo+i*100/(K*kc),i*100]);      // 2 km hacia el este
          const at=(d,off)=>[la+off/K,lo+d/(K*kc)];                                   // off>0: norte = izquierda
          const W=[
            {k:0,w:2.5,agua:true,pts:[at(800,-120),at(800,120)]},                    // arroyo que cruza el camino en el km 0,8, de sur a norte
            {k:11,w:6,agua:false,pts:[at(200,25),at(900,25)]},                        // calle paralela 25 m a la izquierda
            {k:13,w:2.5,agua:false,pts:[at(300,2),at(600,2)]},                        // pegada al eje: es el propio camino, no va
            {k:11,w:6,agua:false,pts:[at(1500,300),at(1600,300)]}                     // lejos: no va
          ];
          return {out:linDeWays(P,W),vacio:linDeWays([],W).length,tipo:[linTipo({waterway:'stream'}),linTipo({highway:'primary'}),linTipo({highway:'cycleway'}),linTipo({building:'yes'}),linTipo({highway:'residential',tunnel:'yes'})]};}""")
        print('   ',r)
        o=r['out']
        ok(len(o)==2,'2 líneas (el propio camino y la lejana quedan afuera): %d'%len(o))
        a=[x for x in o if x[0]==0][0];c=[x for x in o if x[0]==11][0]
        pts=a[2];ds=pts[0::2];ls=pts[1::2]
        ok(min(ds)>=700 and max(ds)<=900 and all(abs(d-800)<=12 for d in ds),'arroyo cerca del km 0,8: %s'%ds[:3])
        ok(ls[0]<0 and ls[-1]>0,'cruza de la derecha (l<0) a la izquierda (l>0): %s → %s'%(ls[0],ls[-1]))
        ok(a[1]==2.5,'ancho de arroyo 2,5 m')
        ok(all(abs(l-25)<1 for l in c[2][1::2]) and c[2][0]<=260,'calle paralela a 25 m a la izquierda desde el km 0,2')
        t=r['tipo']
        ok(t[0]['k']==0 and t[1]['k']==10 and t[2]['k']==13 and t[3] is None and t[4] is None,'tipos: arroyo 0, ruta 10, bicisenda 13; edificio y túnel no')
        ok(r['vacio']==0,'sin camino, nada')
        ok(not errs,'sin errores de página: %s'%errs)
        await b.close()
asyncio.run(main())
