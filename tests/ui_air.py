import asyncio
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--enable-webgl'])
        pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('file://'+BUILD+'/harness_3d.html');ev=pg.evaluate
        await ev("fake()")
        # vuelo de 60 km (dentro de la zona de prueba): carreteo, despegue a 280 km/h, 700 km/h; altura de CABINA (sube 120 m/min hasta 2.000)
        await ev("""window.TR={name:'Vuelo',act:'plane',t0:1e12,pts:(()=>{const P=[];let la=-26.90,lo=-65.76,t=1e12,alt=450,v=0;
          for(let i=0;i<700;i++){v=i<20?8:i<50?8+(i-20)*9:i<620?195:Math.max(70,195-(i-620)*3);la-=v*5/111320;t+=5000;if(i>40)alt=Math.min(2000,alt+10);if(i>600)alt=Math.max(450,alt-12);P.push([la,lo,t,10,Math.round(alt),0]);}
          return P;})()}""")
        r=await ev("(()=>{const A=airAlts(TR);return {est:A.est,max:Math.round(Math.max(...A.a)),start:Math.round(A.a[0]),end:Math.round(A.a[A.a.length-1])}})()")
        print('  ',r);ok(r['est'] and r['max']>9000,'altura de cabina detectada: perfil estimado con crucero (%d m)'%r['max'])
        await ev("open3D({line:TR.pts.map(p=>[p[0],p[1]]),track:TR,relive:true})")
        await pg.wait_for_function("T3.rel&&T3.rel.go",timeout=60000)
        ok(await ev("T3.air&&!!T3.road&&!!T3.rvao"),'el vuelo tiene su ruta en el aire (sin tocar el relieve)')
        await pg.wait_for_timeout(9000)
        st=await ev("(()=>{const n=T3.rel.now;return {y:Math.round(n.y),ground:Math.round(t3H(n.x,n.z)),airY:Math.round(T3.airY),txt:$('#t3rel').innerText.replace(/\\n/g,' | ')}})()")
        print('  ',st)
        ok(st['y']>st['ground']+1000,'el avión va en el aire, no pegado al suelo')
        ok('ft' in st['txt'] and 'kt' in st['txt'] and 'estimada' in st['txt'],'datos de vuelo: metros y pies, km/h y nudos, "estimada"')
        await pg.screenshot(path=BUILD+'/air_top.png')
        await ev("document.querySelector('#t3fp').click()");await pg.wait_for_timeout(2500);await pg.screenshot(path=BUILD+'/air_fpv.png')
        c=await ev("(()=>{const c=t3Cam();return {eye:Math.round(c.eye[1]/T3.exag),plane:Math.round(T3.airY)}})()");print('  ',c)
        ok(abs(c['eye']-c['plane'])<300,'👁️ detrás del avión, a su altura')
        print('ERRORES JS:',errs[:5] or 'ninguno');await b.close()
asyncio.run(main())
