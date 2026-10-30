import asyncio,http.server,threading,functools,os,sys
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
          const la=-54.80,lo=-68.30,K=111320,kc=Math.cos(la*Math.PI/180);
          // camino recto hacia el este, 2 km, un punto cada 100 m: [lat,lon,d]
          const P=[];for(let i=0;i<=20;i++)P.push([la,lo+i*100/(K*kc),i*100]);
          const at=(d,off)=>[la+off/K,lo+d/(K*kc)];       // off>0: al norte = a la izquierda de la marcha hacia el este
          const L=[
            {k:'puente',a:6,p:[at(500,0),at(700,0)]},          // sobre el camino
            {k:'tunel',p:[at(1000,0),at(1200,0)]},
            {k:'terraplen',p:[at(1400,30),at(1700,30)]},      // 30 m al norte = izquierda
            {k:'desmonte',p:[at(1400,-30),at(1700,-30)]},     // al sur = derecha
            {k:'muelle',p:[at(300,0),at(400,0)]},             // no es de camino
            {k:'puente',p:[at(1900,300),at(1950,300)]}        // lejos: no va
          ];
          const out=infraDeElems(P,L);
          let q=null;elCollect=async()=>({list:L,err:''});
          const c=await infraCollect(P);
          return {out,n:c.list.length,vacio:infraDeElems([],L).length};}""")
        print('   ',r)
        o=r['out']
        ok(len(o)==4,'4 tramos (muelle y lejano afuera): %d'%len(o))
        ok(o[0][0]=='puente' and abs(o[0][1]-500)<=12 and abs(o[0][2]-700)<=12 and o[0][3]==0 and o[0][4]==6,'puente 500–700 m sobre el camino, 6 m: %s'%o[0])
        ok(o[1][0]=='tunel' and o[1][3]==0 and o[1][4] is None,'túnel 1000–1200 m')
        t=[x for x in o if x[0]=='terraplen'][0];d=[x for x in o if x[0]=='desmonte'][0]
        ok(t[3]==1 and d[3]==-1,'terraplén a la izquierda (1), desmonte a la derecha (−1)')
        ok(r['n']==4 and r['vacio']==0,'infraCollect devuelve lo mismo; sin camino, nada')
        ok(not errs,'sin errores de página: %s'%errs)
        await b.close()
asyncio.run(main())
