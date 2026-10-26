import asyncio,http.server,threading,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
CAP=r"""
window.__L={};window.__calls=[];
const mk=n=>new Proxy({},{get:(t,k)=>{
  if(k==='then')return undefined;
  if(k==='addListener')return (ev,cb)=>{(__L[n+':'+ev]=__L[n+':'+ev]||[]).push(cb);return Promise.resolve({remove(){__L[n+':'+ev]=(__L[n+':'+ev]||[]).filter(x=>x!==cb);}});};
  return (...a)=>{__calls.push(n+'.'+String(k));
    if(n==='RumboGnss'&&k==='info')return Promise.resolve({sdk:35,device:'samsung SM-S948B',model:'BCM4778',year:2025,gpsOn:true,perm:true});
    if(n==='BackgroundGeolocation'&&k==='addWatcher'){window.__ok=(p)=>a[1]({latitude:p.coords.latitude,longitude:p.coords.longitude,accuracy:p.coords.accuracy,altitude:p.coords.altitude,speed:p.coords.speed,bearing:p.coords.heading,time:p.timestamp});return Promise.resolve('w1');}
    return Promise.resolve({});};}});
window.Capacitor={isNativePlatform:()=>true,getPlatform:()=>'android',registerPlugin:mk,Plugins:new Proxy({},{get:(t,k)=>mk(k)})};
window.__emit=(ev,d)=>(__L['RumboGnss:'+ev]||[]).forEach(cb=>cb(d));
"""
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8790),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch()
        # 1) web
        pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8790/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("__ok({coords:{latitude:-54.8,longitude:-68.3,accuracy:6,altitude:20,speed:1,heading:0},timestamp:Date.now()})")
        await pg.click('#pill');await pg.wait_for_timeout(300)
        t=await pg.inner_text('#sheet');ok('APK' in t or 'app (APK)' in t,'web: explica que el detalle es en la app');ok('±6 m' in t,'web: muestra la precisión')
        await pg.close()
        # 2) app
        pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script(CAP+"window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8790/index.html');await pg.wait_for_timeout(1500)
        await pg.evaluate("showGnss()");await pg.wait_for_timeout(300)
        calls=await pg.evaluate("__calls.filter(c=>c.startsWith('RumboGnss'))");print('  ',calls)
        ok('RumboGnss.start' in calls,'arranca el receptor')
        # satélites: GPS L1+L5, Galileo E1+E5a, GLONASS, BeiDou
        sats=[]
        import random;random.seed(3)
        for c,ids,dual in [(1,[2,5,12,14,25,29,31],True),(6,[3,8,13,26,33],True),(3,[4,11,20,21],False),(5,[19,22,35,44,59],True),(2,[48],False)]:
            for k,i in enumerate(ids):
                el=random.uniform(5,85);az=random.uniform(0,360);cn=random.uniform(18,46);used=1 if cn>24 and c!=2 else 0
                fl=used|6
                f={1:1575.42,6:1575.42,3:1602.56,5:1561.098,2:1575.42}[c]
                sats.append([c,i,round(cn,1),round(el,1),round(az,1),fl,f])
                if dual and k%2==0:sats.append([c,i,round(cn-4,1),round(el,1),round(az,1),fl,1176.45])
        sats.append([1,30,0,0,0,2,0])
        await pg.evaluate("s=>{__emit('gnssFix',{ttff:4200});__emit('gnssLoc',{lat:-54.8,lon:-68.3,acc:3.2,alt:24.5,vacc:4.1,speed:0.4,t:Date.now(),sats:22});__emit('gnssNmea',{n:'$GNGSA,A,3,02,05,12,,,,,,,,,,1.4,0.8,1.1,1*30'});__emit('gnssNmea',{n:'$GPGGA,120000.00,5448.0,S,06818.0,W,1,22,0.8,24.5,M,14.2,M,,*5C'});__emit('gnss',{s,t:Date.now()})}",sats)
        await pg.wait_for_timeout(1100);await pg.evaluate("gnTick(true)")
        t=await pg.inner_text('#gnBody');print('   '+t[:900].replace('\n',' | '))
        ok('en uso' in t and 'Galileo' in t and 'BeiDou' in t,'resumen por sistema')
        ok('±3 m' in t,'precisión del GPS solo')
        ok('4,2 s' in t,'primera posición')
        ok('0,8' in t,'HDOP')
        ok('en uso con L5/E5a' in t,'doble frecuencia')
        svg=await pg.evaluate("document.querySelectorAll('#gnBody svg circle').length");ok(svg>20,'mapa del cielo con satélites (%d círculos)'%svg)
        await pg.screenshot(path='gnss_1.png',full_page=False)
        await pg.evaluate("document.querySelector('#sBody').scrollTop=700");await pg.wait_for_timeout(200);await pg.screenshot(path='gnss_2.png')
        await pg.evaluate("document.querySelector('#sBody').scrollTop=1400");await pg.wait_for_timeout(200);await pg.screenshot(path='gnss_3.png')
        # cerrar: se apaga
        await pg.click('#sX');await pg.evaluate("__emit('gnss',{s:[],t:Date.now()})");await pg.wait_for_timeout(1700)
        calls=await pg.evaluate("__calls.filter(c=>c.startsWith('RumboGnss'))");ok(calls[-1]=='RumboGnss.stop','al cerrar la hoja se apaga');ok(await pg.evaluate("!GN.P&&!GN.own.size"),'sin dueños')
        # modo vuelo usa la línea
        await pg.evaluate("flStart()");await pg.wait_for_timeout(300)
        await pg.evaluate("s=>{__emit('gnss',{s,t:Date.now()});__ok({coords:{latitude:-54.8,longitude:-68.3,accuracy:5,altitude:20,speed:70,heading:0},timestamp:Date.now()});flDraw()}",sats)
        x=await pg.evaluate("document.querySelector('#flt .fx').innerText");print('   ',x.replace('\n',' | '))
        ok('🛰️ Satélites' in x,'modo vuelo muestra los satélites')
        await pg.evaluate("flStop()");calls=await pg.evaluate("__calls.filter(c=>c.startsWith('RumboGnss'))");ok(calls[-1]=='RumboGnss.stop','al salir del modo vuelo se apaga')
        # APK viejo sin plugin
        await pg.evaluate("Capacitor.registerPlugin=n=>n==='RumboGnss'?{info:()=>Promise.reject(new Error('not implemented')),addListener:()=>Promise.resolve({remove(){}}),start:()=>Promise.reject(new Error('\"RumboGnss\" plugin is not implemented on android')),stop:()=>Promise.resolve()}:{} ;showGnss()")
        await pg.wait_for_timeout(400);t=await pg.inner_text('#gnBody');ok('actualizá la app' in t,'APK viejo: pide actualizar')
        print('ERRORES JS:',errs[:3] or 'ninguno');ok(not errs,'sin errores')
        await b.close()
    srv.shutdown()
asyncio.run(main())
