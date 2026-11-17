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
        r=await pg.evaluate("""async()=>{
          const la=-54.80,lo=-68.30,K=111320,kc=Math.cos(la*Math.PI/180);
          const P=[];for(let i=0;i<=60;i++)P.push([la,lo+i*10/(K*kc),i*10]);           // 600 m hacia el este: izquierda = norte
          const prof=P.map(()=>50);
          const demS=(a,b)=>50+(a-la)*K*0.5;                                              // sube hacia el norte (izquierda) 0,5 m por m
          netBlocked=()=>true;                                                            // sin internet: sin colores
          const C=await bkCostados(P,prof,demS,16);
          const U=Uint8Array.from(atob(C.d.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
          return {n:C.n,off:C.off,col:C.col,len:U.length,izq:Array.from(U.slice(0,7)).map(v=>v-128),der:Array.from(U.slice(13,20)).map(v=>v-128)}; }""")
        print('   ',r)
        ok(r['n']==25 and r['len']==25*26,'25 muestras cada 25 m, 26 bytes cada una')
        ok(r['izq']==[3,6,10,18,30,50,90] or all(abs(a-b)<=1 for a,b in zip(r['izq'],[3,6,10,18,30,50,90])),'izquierda sube (ladera): %s'%r['izq'])
        ok(all(abs(a+b)<=1 for a,b in zip(r['der'],[3,6,10,18,30,50,90])),'derecha baja (barranca): %s'%r['der'])
        ok(r['col']==0,'sin foto satelital, colores en 0')
        ok(not errs,'sin errores de página: %s'%errs)
        await b.close()
asyncio.run(main())
