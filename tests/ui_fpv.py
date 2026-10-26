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
        pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
        await pg.goto('file://'+BUILD+'/harness_3d.html');ev=pg.evaluate
        await ev("fake()")
        await ev("""window.TR={name:'Ruta',act:'bike',t0:1e12,pts:Array.from({length:400},(_,i)=>[-26.925-i*0.000135,-65.70-0.03*Math.sin(i/120),1e12+i*36000,5,2000+i*3.2,0])}""")
        await ev("open3D({line:TR.pts.map(p=>[p[0],p[1]]),track:TR,relive:true})")
        await pg.wait_for_function("T3.rel&&T3.rel.go",timeout=60000);await pg.wait_for_timeout(4000)
        await ev("document.querySelector('#t3fp').click()");await pg.wait_for_timeout(1500)
        cam=await ev("(()=>{const c=t3Cam(),g=t3H(c.eye[0],c.eye[2])*T3.exag;return {h:c.eye[1]-g,dx:c.T[0]-c.eye[0],dz:c.T[2]-c.eye[2],dy:c.T[1]-c.eye[1],follow:t3Follow(),on:$('#t3fp').classList.contains('on')}})()")
        print('  ',cam)
        ok(cam['on'] and cam['follow'],'👁️ activo y siguiendo el recorrido')
        ok(5<cam['h']<40,'cámara a pocos metros del suelo')
        import math;ok(abs(math.degrees(math.atan2(cam['dy'],math.hypot(cam['dx'],cam['dz']))))<45,'mira hacia adelante y algo abajo (el terreno de prueba es muy empinado)')
        mk=await ev("(()=>{const m=$('#t3mk');return m.style.display!=='none'&&!m.hidden?[parseFloat(m.style.left),parseFloat(m.style.top)]:null})()")
        print('   marcador en',mk);ok(mk and 100<mk[0]<320 and 430<mk[1]<860,'el ícono se ve adelante y abajo, en el medio')
        await pg.screenshot(path='fpv_rel.png')
        await ev("document.querySelector('[data-t3=out]').click();document.querySelector('[data-t3=out]').click()");await pg.wait_for_timeout(500)
        ok(await ev("T3.fpvH")>30,'− sube la cámara')
        await ev("document.querySelector('[data-t3=in]').click();document.querySelector('[data-t3=in]').click()")
        # pausa + mirar alrededor con un dedo
        await ev("t3RelPlay()");await pg.wait_for_timeout(300)
        bx=await ev("(()=>{const r=T3.cv.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()")
        await pg.mouse.move(bx[0],bx[1]);await pg.mouse.down();await pg.mouse.move(bx[0]+120,bx[1],steps=6);await pg.mouse.up()
        ok(abs(await ev("T3.fpvYaw"))>10,'pausado: un dedo mira hacia los costados')
        await ev("document.querySelector('[data-t3=n]').click()");ok(await ev("T3.fpvYaw")==0,'🧭 vuelve a mirar adelante')
        # sin seguir: caminar
        await ev("close3D()");await ev("open3D({line:TR.pts.map(p=>[p[0],p[1]])})");await pg.wait_for_timeout(2500)
        ok(await ev("T3.fpv&&$('#t3fp').classList.contains('on')"),'al volver a abrir el 3D se mantiene 👁️')
        z0=await ev("T3.cam.tz");await pg.mouse.move(bx[0],bx[1]);await pg.mouse.down();await pg.mouse.move(bx[0],bx[1]-150,steps=6);await pg.mouse.up()
        ok(await ev("T3.cam.tz")!=z0,'caminando: arrastrar hacia arriba avanza')
        await ev("t3FlyStart()");await pg.wait_for_timeout(3000);ok(await ev("t3Follow()"),'sobrevolar a ras del suelo sigue la línea')
        await pg.screenshot(path='fpv_fly.png')
        await ev("document.querySelector('#t3fp').click()");ok(await ev("!T3.fpv"),'👁️ de nuevo vuelve a la vista de arriba')
        print('ERRORES JS:',errs[:5] or 'ninguno');await b.close()
asyncio.run(main())
