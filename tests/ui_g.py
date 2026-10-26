import asyncio,http.server,threading,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8789),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8789/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("flStart()");await pg.wait_for_timeout(300)
        # teléfono quieto en el asiento (inclinado): calibra
        await pg.evaluate("""async()=>{const m=(x,y,z)=>{const e=new Event('devicemotion');e.accelerationIncludingGravity={x,y,z};window.dispatchEvent(e);};
          for(let i=0;i<80;i++){m(0,6.93,6.93);await new Promise(r=>setTimeout(r,10));}
          // despegue: empuje hacia atrás 0,3 G (sobre el eje perpendicular a "abajo")
          for(let i=0;i<60;i++){m(0,6.93-2.08,6.93+2.08);await new Promise(r=>setTimeout(r,10));}}""")
        await pg.evaluate("__ok({coords:{latitude:-50.28,longitude:-72.05,accuracy:5,altitude:204,speed:60,heading:0},timestamp:Date.now()});flDraw()")
        x=await pg.evaluate("document.querySelector('#flt .fx').innerText.replace(/\\n/g,' | ')");print('  ',x)
        r=await pg.evaluate("({g:GM.g,gv:GM.gv,gh:GM.gh,max:GM.max,cal:GM.calN})");print('  ',r)
        ok(r['cal']>20 and abs(r['gh']-0.3)<0.06 and abs(r['gv']-1.0)<0.05,'calibra quieto y mide 0,3 G horizontal en el despegue')
        ok('🎢 G:' in x and 'horizontal' in x,'el tablero muestra las G')
        print('ERRORES JS:',errs[:3] or 'ninguno');await b.close()
    srv.shutdown()
asyncio.run(main())
