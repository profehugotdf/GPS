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
          const la0=-54.80,lo0=-68.30,K=111320,kc=Math.cos(la0*Math.PI/180);
          // ruta recta hacia el este, 600 m, un punto cada 25 m. Tierra firme al norte desde 300 m; un barco de 35 m de ancho y 25 m de alto a 60-95 m al norte
          const P=[];for(let i=0;i<=24;i++)P.push([la0,lo0+i*25/(K*kc)]);
          const N=(la)=>(la-la0)*K;               // metros al norte de la ruta
          const raw=(la,lo)=>{const n=N(la);return n>=300?30:(n>=60&&n<=95?25:0);};
          const wl=P.map(()=>0);
          const a=kyShores(P,wl,raw,null)[10].find(x=>x.side===1);
          // máscara: el barco definido como línea popa→proa paralela a la ruta, a 77 m al norte (30 m de radio)
          const barco={k:'carguero',p:[[la0+77/K,lo0+200/(K*kc)],[la0+77/K,lo0+400/(K*kc)]]};
          const muelle={k:'muelle',p:[[la0+60/K,lo0+100/(K*kc)],[la0+300/K,lo0+100/(K*kc)]]};   // un muelle perpendicular: 240 m de largo
          const m=elemMask([barco,muelle,{k:'puente',p:[[la0,lo0],[la0,lo0+1e-4]]}]);
          const g=demSinElems(raw,m);
          const sobre=[g(la0+77/K,lo0+300/(K*kc)),g(la0+150/K,lo0+100/(K*kc)),g(la0+400/K,lo0+300/(K*kc)),g(la0+200/K,lo0+500/(K*kc))];
          const c=kyShores(P,wl,g,null)[10].find(x=>x.side===1);
          // el muelle: alto de 4 m sobre el agua que llega hasta tierra firme (tierra al norte desde 300): sin máscara sería una "orilla" a 60 m
          const raw2=(la,lo)=>{const n=N(la),e=(lo-lo0)*kc*K;return n>=300?30:((Math.abs(e-100)<=6&&n>=60)?4:0);};
          const cx=kyShores(P,wl,raw2,null)[4].find(x=>x.side===1), cm=kyShores(P,wl,demSinElems(raw2,m),null)[4].find(x=>x.side===1);
          return {sinFiltro:a.d,conMascara:c.d,sobre,vacio:elemMask([{k:'puente',p:[[0,0],[0,1]]}])===null,muelleSin:cx.d,muelleCon:cm.d,
            fn:typeof coastSea.why};}""")
        print('   ',r)
        ok(r['sinFiltro'] is not None and 280<=r['sinFiltro']<=320,'un barco angosto sobre el agua ya no cuenta como orilla (a 300 m está la tierra): %s'%r['sinFiltro'])
        ok(r['sobre'][0]==0 and r['sobre'][1]==0 and r['sobre'][2]==30 and r['sobre'][3]==0,'la máscara aplana barco y muelle, y deja la tierra firme: %s'%r['sobre'])
        ok(r['conMascara'] is not None and 280<=r['conMascara']<=320,'con barco y muelle definidos, la orilla sigue a 300 m: %s'%r['conMascara'])
        ok(r['vacio'],'sin muelles ni barcos no hay máscara (los puentes no aplanan nada)')
        ok(r['muelleSin']<=70 and r['muelleCon']>=280,'un muelle definido deja de contar como tierra: sin máscara %s m, con máscara %s m'%(r['muelleSin'],r['muelleCon']))
        ok(r['fn']=='string','coastSea guarda por qué no pudo bajar la costa (why)')
        ok(not errs,'sin errores JS: %s'%errs[:2])
        await b.close()
    s1.shutdown()
asyncio.run(main())
