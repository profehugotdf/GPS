import asyncio,http.server,threading,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8784),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8784/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("""async()=>{
          window.mk=(id,secPerKm,km,day,act)=>{const P=[];let la=-54.8,t=Date.parse('2026-10-'+day+'T10:00:00-03:00');for(let i=0;i<=km*1000;i+=10){la+=10/111320;t+=secPerKm*10;P.push([la,-68.3,t,5,20,0]);}
            return {id,name:'Prueba '+id,act:act||'run',t0:P[0][2],pts:P,stats:calcStats(P),src:'rec'};};
          window.TOASTS=[];const ot=toast;toast=(m,d)=>{TOASTS.push(m);ot(m,d)};
          await DB.put('kv','track:a',mk('a',330,6,'10'));await DB.put('kv','track:b',mk('b',310,11,'15'));await DB.put('kv','track:c',mk('c',120,22,'01','bike'));}""")
        await pg.evaluate("showRecords('run')");await pg.wait_for_timeout(1500)
        t=await pg.evaluate("document.querySelector('#sheet').innerText");print('  ',t.replace('\n',' | ')[:500])
        ok('5 km · 25:5' in t and '10 km · 51:4' in t,'tabla de corredor: mejores tiempos (5:10/km de la salida b)')
        ok('2° 27:3' in t,'muestra 2° y 3° mejor')
        ok('Salida más larga' in t and '10,99 km' in t,'salida más larga')
        # en vivo: ritmo 4:50 → récord de 1 km y 5 km
        r=await pg.evaluate("""async()=>{REC.state='rec';REC.act='run';await prLiveLoad();const tr=mk('live',290,5.2,'20');REC.pts=[];const out=[];
          for(const p of tr.pts){REC.pts.push(p);REC.prT=0;prLive();}REC.state='idle';return {best:REC.prBest,said:REC.prSaid,toasts:TOASTS.slice()};}""")
        print('   en vivo:',r['said'],r['toasts'][-2:])
        ok(r['said'].get('d1000') and r['said'].get('d5000'),'en vivo: avisa récord de 1 km y de 5 km al completarlos')
        # al guardar
        n=await pg.evaluate("""async()=>{REC.prSaid={};const tr=mk('d',300,10.5,'21');await DB.put('kv','track:d',tr);return await prCheck(tr);}""")
        print('   al guardar:',[(x['k'],x['pos']) for x in n])
        ok(any(x['k']=='d10000' and x['pos']==0 for x in n),'al guardar: récord de 10 km detectado')
        await pg.evaluate("showRecords('bike')");await pg.wait_for_timeout(800)
        t=await pg.evaluate("document.querySelector('#sheet').innerText");print('  ',t.replace('\n',' | ')[:300]);ok('20 km' in t and 'km/h' in t,'bici: tiempos y velocidad media')
        print('ERRORES JS:',errs[:3] or 'ninguno');await b.close()
    srv.shutdown()
asyncio.run(main())
