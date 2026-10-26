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
        await ev("RT.res={foot:{coords:Array.from({length:60},(_,i)=>[-26.925-i*0.0009,-65.70-0.03*Math.sin(i/18)])}};RT.sel='foot'")
        await ev("open3D({route:true})")
        await pg.wait_for_function("T3.loaded===T3.total&&T3.total>0",timeout=60000)
        await pg.wait_for_timeout(500)
        info=await ev("({zd:T3.zd,zs:T3.zs,tex:T3.texSize,n:T3.n,hasZ:T3.hasZ,h:[Math.round(T3.H.reduce((a,b)=>Math.min(a,b),1e9)),Math.round(T3.H.reduce((a,b)=>Math.max(a,b),-1e9))],cam:T3.cam,msg:$('#t3msg').textContent})")
        print('  ',info)
        ok(info['hasZ'] and info['h'][1]-info['h'][0]>800,'relieve cargado')
        await pg.screenshot(path='t3_a.png')
        px=await ev("""(()=>{const gl=T3.gl,cv=T3.cv;T3.dirty=false;t3Draw();const w=cv.width,h=cv.height,a=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,a);let sky=0,o=0,ter=0;for(let i=0;i<a.length;i+=4*97){const r=a[i],g=a[i+1],b=a[i+2];if(Math.abs(r-184)<12&&Math.abs(g-209)<12&&Math.abs(b-230)<12)sky++;else if(r>200&&g<120)o++;else ter++;}return {sky,o,ter};})()""")
        print('  pixels',px);ok(px['ter']>px['sky']*0.3 and px['o']>0,'se ve terreno y la ruta')
        # gestos: arrastrar con mouse
        c0=await ev("JSON.stringify(T3.cam)")
        await pg.mouse.move(200,500);await pg.mouse.down();await pg.mouse.move(260,420,steps=5);await pg.mouse.up()
        ok(await ev("JSON.stringify(T3.cam)")!=c0,'arrastrar mueve la vista')
        await pg.click('[data-t3=ex][data-ex="2"]');ok(await ev("T3.exag")==2,'exageración ×2')
        await pg.click('#t3fly');ok(await ev("!!T3.fly"),'sobrevuelo arranca')
        await pg.wait_for_timeout(3000);await pg.screenshot(path='t3_fly.png')
        ok(await ev("T3.cam.tilt")==58,'cámara del sobrevuelo')
        mk=await ev("(()=>{const m=$('#t3mk'),r=m.getBoundingClientRect();return {vis:!m.hidden&&m.style.display!=='none',x:r.left+r.width/2,y:r.top+r.height/2,t:m.textContent,k:T3.flyK,km:T3.km}})()")
        print('  marcador',mk);ok(mk['vis'] and 0<mk['x']<pg.viewport_size['width'] and 0<mk['y']<pg.viewport_size['height'] and mk['km']==1 and 0<mk['k']<1,'ícono que marca por dónde va el sobrevuelo, y lo recorrido pintado')
        await pg.mouse.move(200,500);await pg.mouse.down();await pg.mouse.up();k1=await ev("T3.flyK")
        ok(await ev("!T3.fly"),'tocar pausa');await pg.click('#t3fly');await pg.wait_for_timeout(600)
        ok(await ev("T3.flyK")>=k1,'sigue desde donde estaba')
        await pg.click('[data-t3=x]');ok(await ev("!T3.on&&$('#t3').hidden"),'cerrar')
        print('ERRORES JS:',errs or 'ninguno')
        await b.close()
asyncio.run(main())
