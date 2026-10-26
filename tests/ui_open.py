import asyncio
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--enable-webgl'])
        pg=await b.new_page(viewport={'width':390,'height':800});errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('file://'+BUILD+'/harness_globe.html');ev=pg.evaluate
        # textura ya guardada de una sesión anterior: se arma una vez
        await ev("map._z=5;openGlobe()");await pg.wait_for_function("GB.tex===true",timeout=30000);await ev("closeGlobe()")
        # sesión nueva simulada: se pierde el contexto pero queda la base de datos
        await pg.reload();await ev("KV.clear?0:0")
        print('A) antes de abrir, preparado en segundo plano:',end=' ')
        # reponer base de datos (el reload la borra en el arnés): volver a guardar la textura
        await ev("map._z=5;openGlobe()");await pg.wait_for_function("GB.tex===true",timeout=30000);await ev("closeGlobe();GB.tex=false;GB.tx=null;GB.gl=null;GB_PREP=null;GB.texLayer=null")
        await pg.reload()
        print('(el arnés pierde la base al recargar; se prueba la preparación directamente)')
        await ev("map._z=5;openGlobe()");await pg.wait_for_function("GB.tex===true",timeout=30000);await ev("closeGlobe()")
        await ev("GB.gl=null;GB.tex=false;GB.texLayer=null;GB_PREP=null;GB.tx=null")
        # NOTA: al soltar GB.gl se reinicia el contexto; ahora se prepara y se mide
        t=await ev("""(async()=>{const t0=performance.now();await gbPrepare();return [performance.now()-t0,GB.tex,!!GB.gl]})()""")
        print('B) gbPrepare (contexto + shader + imagen):',round(t[0]),'ms · textura lista',t[1],'· GL',t[2])
        assert t[1] and t[2]
        t=await ev("""(async()=>{map._z=4;const t0=performance.now();T.animH({zoom:3,center:{lat:-30,lng:-60}});await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return [performance.now()-t0,GB.on,GB.tex,GB.D-1,document.getElementById('globe').hidden]})()""")
        print('C) zoomanim a z3 → globo abierto en',round(t[0]),'ms · visible',not t[4],'· textura ya cargada',t[2],'· altura',round(t[3],2))
        assert t[1] and t[2]
        await ev("closeGlobe();T.animH({zoom:4,center:{lat:0,lng:0}})");print('D) zoomanim a z4 (>3.5): no abre =',not await ev("GB.on"))
        await ev("map._z=2;T.animH({zoom:3,center:{lat:0,lng:0}})");print('E) acercando (3>2): no abre =',not await ev("GB.on"))
        await ev("S.globeAuto=false;map._z=4;T.animH({zoom:3,center:{lat:0,lng:0}})");print('F) ajuste apagado: no abre =',not await ev("GB.on"))
        print('errores:',errs or 'ninguno');await b.close()
asyncio.run(main())
