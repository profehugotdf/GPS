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
        await ev("""window.TR={name:'Subida al Ñuñorco',act:'walk',t0:Date.parse('2026-10-12T09:00:00-03:00'),pts:Array.from({length:400},(_,i)=>[-26.925-i*0.000135,-65.70-0.03*Math.sin(i/120),Date.parse('2026-10-12T09:00:00-03:00')+i*36000,5,2000+i*3.2,0]),hr:Array.from({length:400},(_,i)=>120+Math.round(i/10)),pw:Array.from({length:400},(_,i)=>150+(i%30))}""")
        await ev("shownTrack=TR;open3D()");await pg.wait_for_timeout(800)
        ok(await ev("!!T3.rel&&!$('#t3rv').hidden&&$('#t3fly').hidden"),'3D abierto desde Más con un track en el mapa: aparece 🎬 Revivir')
        print('   aviso:',await ev("T.toasts?T.toasts.slice(-1)[0]:''") if await ev("typeof T!=='undefined'") else '')
        await ev("close3D();shownTrack=null")
        await ev("open3D({line:TR.pts.map(p=>[p[0],p[1]]),track:TR,relive:true})")
        await pg.wait_for_function("T3.rel&&T3.rel.go",timeout=60000)
        ok(await ev("!$('#t3rel').hidden&&!$('#t3mk').hidden"),'arranca: datos y marcador visibles')
        await pg.wait_for_timeout(9000)
        t=await ev("$('#t3rel').innerText.replace(/\\n/g,' | ')");print('   datos:',t)
        k=await ev("T3.kp");ok(0<k<1,f'va dibujando el recorrido ({k:.2f})');ok('❤️' in t and '⚡' in t,'muestra pulso y potencia')
        await pg.screenshot(path='rel_mid.png')
        px=await ev("""(()=>{const gl=T3.gl,cv=T3.cv;t3Draw();const w=cv.width,h=cv.height,a=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,a);let o=0,wh=0;for(let i=0;i<a.length;i+=4*7){const r=a[i],g=a[i+1],b=a[i+2];if(r>220&&g>60&&g<120&&b<60)o++;else if(r>205&&g>205&&b>205)wh++;}return {o,wh};})()""")
        print('   píxeles naranja/blanco',px);ok(px['o']>20,'parte recorrida en naranja')
        await ev("T3.rel.dur=2000");await pg.wait_for_function("T3.rel.done",timeout=30000)
        t=await ev("$('#t3rel').innerText.replace(/\\n/g,' | ')");print('   final:',t);ok('🏁' in t and 'prom' in t,'resumen al final con pulso y potencia promedio')
        await pg.screenshot(path='rel_end.png')
        # video
        await ev("t3VidStart()");await ev("T3.rel.dur=2500");await pg.wait_for_timeout(500)
        ok(await ev("!!T3.recr"),'graba video')
        await pg.wait_for_function("!T3.recr",timeout=30000)
        print('   avisos:',await ev("TOASTS"))
        print('ERRORES JS:',errs or 'ninguno')
        await b.close()
asyncio.run(main())
