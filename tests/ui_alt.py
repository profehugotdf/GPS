import asyncio,http.server,threading,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8788),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8788/index.html');await pg.wait_for_function('!!window.__ok')
        # 1) grabar un vuelo a 830 km/h
        await pg.evaluate("flStart()");await pg.wait_for_timeout(300)
        await pg.evaluate("document.querySelector('#flt [data-fl=rec]').click()");await pg.wait_for_timeout(600)
        await pg.evaluate("(()=>{let la=-34.5,t=Date.now()-60000;for(let i=0;i<60;i++){__ok({coords:{latitude:la,longitude:-58.5,accuracy:8,altitude:11000,speed:230,heading:180},timestamp:t});la-=230/111320;t+=1000;}})()")
        r=await pg.evaluate("({act:REC.act,n:REC.pts.length,d:Math.round(REC.dist),btn:document.querySelector('#flt [data-fl=rec]').textContent})");print('  ',r)
        ok(r['act']=='plane' and r['n']>=55 and r['d']>12000,'grabando en avión a 830 km/h se guardan los puntos (antes se descartaban todos)')
        # 2) en la pista de El Calafate con el teléfono marcando 2.721 m
        await pg.evaluate("S.flDest='FTE';FL.hist=[];FL.cab=0;(()=>{const t0=Date.now()-20000;for(let i=0;i<=20;i++)__ok({coords:{latitude:-50.2803+i*0.00005,longitude:-72.0531,accuracy:8,altitude:2721,speed:6,heading:0},timestamp:t0+i*1000});})();lastFixWall=Date.now();flDraw()")
        t=await pg.evaluate("document.querySelector('#flt .fg').innerText.replace(/\\n/g,' | ')");print('  ',t[:160])
        ok('204' in t and 'el teléfono marca 2.721' in t,'en la pista muestra la altura del aeropuerto (204 m) y avisa el error del teléfono')
        x=await pg.evaluate("document.querySelector('#flt .fx').innerText");ok('Rampa' not in x,'sin rampa de 3° con la altura equivocada')
        # 3) aproximación a 10 km marcando 2.765 m a 268 km/h
        await pg.evaluate("FL.hist=[];(()=>{const t0=Date.now()-20000;for(let i=0;i<=20;i++)__ok({coords:{latitude:-50.2803+0.0899+(20-i)*0.0007,longitude:-72.0531,accuracy:8,altitude:2765+(20-i)*9,speed:74,heading:180},timestamp:t0+i*1000});})();flDraw()")
        t=await pg.evaluate("document.querySelector('#flt .fg').innerText.replace(/\\n/g,' | ')");print('  ',t[:160])
        ok('rampa de 3°' in t and '728' in t,'en la aproximación usa la rampa de 3° (≈ 728 m) y avisa')
        # 4) Revivir: la altura de llegada se corrige
        r=await pg.evaluate("""(()=>{const P=[];let t=1e12;for(let i=0;i<300;i++){const u=i/299;P.push([-34.56+(-50.28+34.56)*u,-58.41+(-72.05+58.41)*u,t+=20000,8,Math.round(i<20?10:i>280?2700:Math.min(11000,10+i*200,2700+(299-i)*700)),0]);}
          const A=airAlts({pts:P,act:'plane'});return {est:A.est,start:Math.round(A.a[0]),end:Math.round(A.a[A.a.length-1]),mid:Math.round(A.a[150])};})()""")
        print('  ',r);ok(abs(r['end']-204)<60 and r['mid']>8000,'Revivir: la llegada queda a la altura de El Calafate y el crucero a 10.000 m')
        # altura por el vuelo en crucero a 300 km del destino (el teléfono marca 2.300 de cabina)
        await pg.evaluate("S.flDest='SAWH';FL.hist=[];FL.toff=Date.now()-1800000;FL.dep={name:'El Calafate',elev:204};FL.cru=0;(()=>{const t0=Date.now()-20000;for(let i=0;i<=20;i++)__ok({coords:{latitude:-52.1-i*0.002,longitude:-70,accuracy:8,altitude:2300,speed:230,heading:150},timestamp:t0+i*1000});})();flDraw()")
        t=await pg.evaluate("document.querySelector('#flt .fg').innerText.replace(/\\n/g,' | ')");print('  ',t[:170])
        ok('10.700' in t and 'por el vuelo' in t,'en crucero: 10.700 m "por el vuelo", sin creerle al teléfono')
        # partida y llegada
        await pg.evaluate("flDraw();document.querySelector('#flt [data-fl=appr]').click()");await pg.wait_for_timeout(300)
        ok(await pg.evaluate("!!document.querySelector('#sheet [data-act=both]')"),'opción 🛫🛬 Partida y llegada')
        print('ERRORES JS:',errs[:3] or 'ninguno');await b.close()
    srv.shutdown()
asyncio.run(main())
