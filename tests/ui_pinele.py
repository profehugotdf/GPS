# ⛰️ Altura sobre el nivel del mar del punto tocado en el mapa (Hugo, 10-nov: "además de las coordenadas")
import asyncio,http.server,threading,functools,os
from playwright.async_api import async_playwright
SITE=os.environ.get('RUMBO_SITE','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8814),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8814/index.html');await pg.wait_for_function('!!window.__ok')
        r=await pg.evaluate("""async()=>{
          window.__ped=[];ensureGraph=async()=>null;
          fetchDemList=async(list,z)=>{__ped.push(z+':'+list.length);const m=new Map();for(const t of list)m.set(t.x+'/'+t.y,new Float32Array(65536).fill(137.4));return m;};
          DB.has=async()=>false;
          await onMapTap({latlng:{lat:-54.8258,lng:-68.31959}});await new Promise(r=>setTimeout(r,150));
          const con=$('#pinSub').textContent,ele=PIN.ele;
          hidePin();const m0=S.dataMode;S.dataMode='never';
          await onMapTap({latlng:{lat:-54.83,lng:-68.32}});await new Promise(r=>setTimeout(r,150));
          const sin=$('#pinSub').textContent;S.dataMode=m0;hidePin();
          return {con,ele,sin,ped:__ped};}""")
        print('   ',r)
        ok('-54.82580, -68.31959' in r['con'] and '≈ 137 m s. n. m.' in r['con'],'la tarjeta del punto dice las coordenadas y la altura')
        ok(r['ele']==137 and r['ped']==['13:1'],'pide una sola tesela de relieve y guarda la altura en el punto')
        ok('sin la altura guardada' in r['sin'] and len(r['ped'])==1,'sin datos permitidos y sin la zona guardada: lo dice y no baja nada')
        ok(not errs,'sin errores JS: %s'%errs[:2])
        await b.close()
    srv.shutdown()
asyncio.run(main())
