"""3D en vivo mientras se guía: se arma el relieve alrededor de donde estás, la cámara va detrás tuyo mirando para donde te movés
(con cada posición del GPS), se ven las indicaciones adentro del 3D, y al acercarte al borde se arma otra ventana."""
import asyncio, os
from playwright.async_api import async_playwright
SITE = os.environ.get('RUMBO_SITE', '.'); BUILD = os.environ.get('RUMBO_BUILD', '.')


def ok(c, m):
    print(('  ✔ ' if c else '  ✘ ') + m)
    assert c, m


async def main():
    errs = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'])
        pg = await b.new_page(viewport={'width': 780, 'height': 360})
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        await pg.goto('file://' + BUILD + '/harness_3d.html')
        ev = pg.evaluate
        await ev("fake()")
        # una ruta que va al norte pasando por el centro (la ventana la recorta)
        await ev("""(()=>{const c=[];for(let i=-30;i<=60;i++)c.push([-26.96+i*0.0015,-65.725+0.002*Math.sin(i/12)]);
          NAV.N.route.coords=c;NAV.N.route.steps=[{text:'Salí',at:0,ico:'⬆️',kind:'turn'},{text:'Seguí',at:500,ico:'⬆️',kind:'turn'}];
          lastFix={lat:-26.96,lon:-65.725,t:1,speed:10,brg:0,acc:5};})()""")
        print('1) Se abre en vivo, centrado en vos')
        await ev("navLive3D()")
        await pg.wait_for_function("T3.on&&T3.live&&T3.loaded===T3.total&&T3.total>0", timeout=60000)
        await pg.wait_for_timeout(400)
        info = await ev("({on:T3.on,live:!!T3.live,line:T3.line&&T3.line.length,fly:$('#t3fly').hidden,nav:!$('#t3nav').hidden,mk:$('#t3mk').textContent,zd:T3.zd,x:Math.round(T3.live.x),z:Math.round(T3.live.z)})")
        print('   ', info)
        ok(info['live'] and info['nav'] and info['fly'], 'modo en vivo: se ve la tarjeta de indicaciones y no el botón de sobrevolar')
        ok(info['line'] and info['line'] > 20, 'la ruta que cae en la ventana (%s puntos) viaja al 3D' % info['line'])
        ok(info['mk'] == '🚗', 'el ícono es el del modo de la guía')
        ok(abs(info['x']) < 2600 and abs(info['z']) < 2600, 'la ventana de 17 km se arma alrededor de donde estás (a %d, %d m del centro)' % (info['x'], info['z']))
        px = await ev("""(()=>{const gl=T3.gl,cv=T3.cv;T3.dirty=false;t3Draw();const w=cv.width,h=cv.height,a=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,a);let sky=0,ter=0;for(let i=0;i<a.length;i+=4){const r=a[i],g=a[i+1],bb=a[i+2];if(Math.abs(r-184)<14&&Math.abs(g-209)<14&&Math.abs(bb-230)<14)sky++;else ter++;}return {sky,ter}})()""")
        print('    pixeles', px)
        ok(px['ter'] > px['sky'] * 0.3, 'se ve terreno')

        print('2) La cámara sigue al GPS y mira para donde vas')
        z0 = await ev("T3.live.z")
        for i in range(1, 6):
            await ev("(i)=>{lastFix={lat:-26.96+i*0.0002,lon:-65.725,t:1+i,speed:10,brg:0,acc:5};t3LiveFix(lastFix);}", i)
            await pg.wait_for_timeout(250)
        await pg.wait_for_function("T3.live.z<%f-15" % z0, timeout=20000)
        c = await ev("({tz:T3.cam.tz,z:T3.live.z,az:Math.round(T3.live.az),fo:t3Follow()})")
        print('   ', z0, c)
        ok(c['z'] < z0 - 15, 'al avanzar hacia el norte la cámara avanza con vos (z %.0f → %.0f)' % (z0, c['z']))
        ok(abs(c['tz'] - c['z']) < 1, 'la cámara apunta a tu posición')
        for i in range(6, 14):
            await ev("(i)=>{lastFix={lat:-26.9584,lon:-65.725+(i-5)*0.00025,t:1+i,speed:10,brg:90,acc:5};t3LiveFix(lastFix);}", i)
            await pg.wait_for_timeout(250)
        await pg.wait_for_function("T3.cam.az>60", timeout=20000)
        az = await ev("Math.round(T3.cam.az)")
        print('    rumbo de la cámara', az)
        ok(60 < az < 100, 'al doblar hacia el este la cámara gira para mirar al este (%d°)' % az)
        await ev("T3.live.yaw=40;")
        await pg.click('[data-t3=n]'); ok(await ev("T3.live.yaw")==0, '🧭 vuelve a mirar hacia adelante')

        print('3) A ras del suelo también anda')
        await pg.click('#t3fp'); await pg.wait_for_timeout(500)
        eye = await ev("(()=>{const c=t3CamFpv();return {e:c.eye.map(Math.round),t:c.T.map(Math.round),p:T3.fpvP&&[Math.round(T3.fpvP.x),Math.round(T3.fpvP.z)]}})()")
        print('   ', eye)
        ok(all(isinstance(v, (int, float)) for v in eye['e'] + eye['t']), 'la cámara a ras del suelo se calcula sin errores')
        await pg.click('#t3fp')

        print('4) Las indicaciones se ven adentro del 3D')
        await ev("(()=>{const s=document.querySelector('#t3nTxt');s.textContent='Girá a la derecha';})()")
        box = await ev("(()=>{const r=$('#t3nav').getBoundingClientRect();return {r:r.right,b:r.bottom,w:r.width}})()")
        ok(box['r'] < 780 * 0.62 and box['b'] < 360 * 0.45, 'en horizontal ocupa una esquina (%dx%d)' % (box['r'], box['b']))

        print('5) Cerca del borde se arma otra ventana centrada en vos')
        g0 = await ev("T3.gen")
        await ev("""(()=>{T3.live.re=0;const k=111195;lastFix={lat:-26.96+8000/k,lon:-65.725,t:99,speed:10,brg:0,acc:5};t3LiveFix(lastFix);})()""")
        await pg.wait_for_function("T3.gen>%d" % g0, timeout=30000)
        await pg.wait_for_function("T3.live&&T3.on", timeout=60000)
        z1 = await ev("Math.abs(T3.live.fz)")
        ok(z1 < 2600, 'la ventana nueva queda centrada donde estás (a %d m del centro)' % z1)

        print('6) Cerrar')
        await pg.click('[data-t3=x]')
        ok(await ev("!T3.on&&T3.live==null&&$('#t3nav').hidden"), 'el 3D se cierra y el modo en vivo se apaga')
    print('ERRORES JS:', errs or 'ninguno')
    ok(not errs, 'sin errores')
    await b.close()

asyncio.run(main())
