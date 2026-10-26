import asyncio,http.server,threading,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8785),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8785/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("showMoreMenu()");await pg.wait_for_timeout(300)
        await pg.evaluate("S.flDest='SAWH'");await pg.evaluate("document.querySelector('[data-act=fly]').click()");await pg.wait_for_timeout(800)
        # despegue desde Tucumán hacia el sur, subiendo 600 m/min a 450 km/h (sin velocidad del GPS: se calcula)
        await pg.evaluate("""async()=>{let la=-26.84,lo=-65.105,alt=500,t=Date.now()-40000;for(let i=0;i<41;i++){window.__ok({coords:{latitude:la,longitude:lo,accuracy:8,altitude:alt,speed:null,heading:null,altitudeAccuracy:10},timestamp:t});la-=125/111320;alt+=10;t+=1000;await new Promise(r=>setTimeout(r,15));}}""")
        await pg.wait_for_timeout(1200)
        t=await pg.evaluate("document.querySelector('#flt').innerText.replace(/\\n/g,' | ')");print('  ',t)
        ok('Altura' in t and '900' in t,'altura en metros y pies')
        ok('449' in t or '450' in t,'velocidad sobre el suelo calculada (450 km/h)')
        ok('S' in t and '180°' in t,'rumbo al sur')
        ok('↑ 600' in t,'subiendo 600 m/min')
        ok('Ushuaia' in t and 'llegás' in t,'distancia y hora de llegada a Ushuaia')
        ok('San Miguel de Tucumán' in t or 'Tucumán' in t,'sobre qué ciudad está')
        await pg.screenshot(path=BUILD+'/fly.png')
        # altura de cabina: 700 km/h y 750 m durante 3 minutos
        await pg.evaluate("""async()=>{let la=-27.2,t=Date.now()-200000,alt=700;for(let i=0;i<200;i++){window.__ok({coords:{latitude:la,longitude:-65,accuracy:8,altitude:alt,speed:195,heading:150},timestamp:t});la-=195/111320;alt+=0.5;t+=1000;}lastFixWall=Date.now();FL.cab=Date.now()-150000;FL.toff=Date.now()-600000;FL.g0=450;}""")
        await pg.wait_for_timeout(1200);t=await pg.evaluate("document.querySelector('#flt').innerText.replace(/\\n/g,' | ')");print('  ',t[:200])
        ok('por el vuelo' in t and ('6.0' in t or '6.4' in t),'avisa que es la altura de la cabina y estima la real')
        # curiosidades en crucero (altura de GPS real: 10.700 m, 760 km/h)
        await pg.evaluate("FL.cab=0;FL.hist=[];(()=>{const t0=Date.now()-20000;for(let i=0;i<=20;i++)__ok({coords:{latitude:-30-i*0.002,longitude:-62,accuracy:8,altitude:10700,speed:211,heading:180},timestamp:t0+i*1000});})();lastFixWall=Date.now();flDraw()")
        x=await pg.evaluate("document.querySelector('#flt .fx').innerText.replace(/\\n/g,' | ')");print('   crucero:',x)
        ok('°C' in x and 'Horizonte' in x and 'en contra' in x,'crucero: temperatura, horizonte y viento en contra estimado')
        # aproximación a Aeroparque: a 10 km y 560 m
        await pg.evaluate("S.flDest='AEP';FL.hist=[];(()=>{const t0=Date.now()-20000;for(let i=0;i<=20;i++)__ok({coords:{latitude:-34.5592+0.0899-(20-i)*0.0006,longitude:-58.4156,accuracy:6,altitude:560+(20-i)*3,speed:75,heading:180},timestamp:t0+i*1000});})();flDraw()")
        x=await pg.evaluate("document.querySelector('#flt .fx').innerText.replace(/\\n/g,' | ')");print('   aproximación:',x)
        ok('Rampa 3°' in x and ('justo en la rampa' in x or 'alto' in x),'aproximación: compara con la rampa de 3°')
        # el menú y el destino quedan por encima del tablero
        await pg.evaluate("document.querySelector('#flt [data-fl=dest]').click()");await pg.wait_for_timeout(400)
        top=await pg.evaluate("(()=>{const r=document.querySelector('#sheet .item').getBoundingClientRect();const e=document.elementFromPoint(r.left+20,r.top+10);return !!e.closest('#sheet')})()")
        ok(top,'la lista de aeropuertos queda por encima del tablero')
        await pg.evaluate("closeSheet();showMoreMenu()");await pg.wait_for_timeout(400)
        top=await pg.evaluate("(()=>{const b=document.querySelector('[data-act=fly]').getBoundingClientRect();const e=document.elementFromPoint(b.left+20,b.top+20);return !!e.closest('#sheet')})()")
        ok(top,'el menú Más se ve completo (el tablero queda atrás)')
        await pg.evaluate("closeSheet();document.querySelector('#flt [data-fl=min]').click()");await pg.wait_for_timeout(300)
        h=await pg.evaluate("document.querySelector('#flt').getBoundingClientRect().height");t2=await pg.evaluate("document.querySelector('#flt').innerText");print('   compacto:',h,t2.replace('\n',' | '))
        ok(h<130 and 'km/h' in t2,'▴ lo achica a una línea')
        await pg.evaluate("document.querySelector('#flt [data-fl=x]').click()");ok(await pg.evaluate("$('#flt').hidden"),'se cierra')
        print('ERRORES JS:',errs[:3] or 'ninguno');await b.close()
    srv.shutdown()
asyncio.run(main())
