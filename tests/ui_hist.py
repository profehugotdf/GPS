# Historial de un circuito desde el track: botón "📈 Historial de …" y en el circuito "📋 Todas las pasadas"
# (Hugo: "¿puedo ver el historial de este recorrido? No sólo la última pasada")
import asyncio,http.server,threading,functools,os
from playwright.async_api import async_playwright
SITE=os.environ.get('RUMBO_SITE','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8805),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8805/index.html');await pg.wait_for_function('!!window.__ok')
        r=await pg.evaluate("""async()=>{
          const c={id:'c1',name:'Escuela-Casa',type:'p2p',gates:[{a:[-54.8,-68.3],b:[-54.8,-68.301]},{a:[-54.81,-68.3],b:[-54.81,-68.301]}],watch:true};await DB.put('kv','circuit:c1',c);
          const t0=Date.now()-30*864e5,tiempos=[700000,656400,690000,710000,680000];
          RUNS=RUNS.filter(x=>x.cid!=='c1');
          tiempos.forEach((ms,i)=>RUNS.push({id:'t'+i+'#c1#1',cid:'c1',act:'car',tid:'t'+i,n:1,t0:t0+i*864e5,time:ms,splits:[ms]}));
          const pts=Array.from({length:20},(_,i)=>[-54.8-i*0.0005,-68.3,t0+4*864e5+i*1000]);
          const tr={id:'t4',name:'Salida',t0:t0+4*864e5,act:'car',pts,stats:{dist:5300,time:678000,mov:640000,avg:8,max:16,gain:138,loss:33},res:[{cid:'c1',name:'Escuela-Casa',type:'p2p',laps:[{n:1,start:t0+4*864e5,time:680000,splits:[680000]}]}]};
          await DB.put('kv','track:t4',tr);await showTrackDetail('t4');await new Promise(z=>setTimeout(z,200));
          const btn=[...document.querySelectorAll('[data-act=chist]')].map(x=>x.textContent);
          document.querySelector('[data-act=chist]').click();await new Promise(z=>setTimeout(z,300));
          const txt=document.querySelector('#sheet').innerText;
          return {btn,tiene:/Todas las pasadas \\(5\\)/.test(txt),items:(txt.match(/vs\\. la anterior/g)||[]).length,record:/🏆 10:56/.test(txt)};}""")
        print('  ',r)
        ok(r['btn'] and '5 pasadas' in r['btn'][0],'el track muestra el botón del historial del circuito')
        ok(r['tiene'] and r['items']==4 and r['record'],'el circuito lista todas las pasadas, con el récord y la diferencia con la anterior')
        print('ERRORES JS:',errs[:3] or 'ninguno');ok(not errs,'sin errores');await b.close()
    srv.shutdown()
asyncio.run(main())
