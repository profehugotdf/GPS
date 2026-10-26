import asyncio,math
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
rad=math.pi/180
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--enable-webgl'])
        pg=await b.new_page(viewport={'width':390,'height':800});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('file://'+BUILD+'/harness_globe.html');ev=pg.evaluate
        await ev("map._z=5;openGlobe()");await pg.wait_for_function("GB.tex===true",timeout=30000)
        async def count(col):
            return await ev("""(col)=>{const gl=GB.gl,cv=document.getElementById('gbGL');const w=cv.width,h=cv.height;GB.dirty=false;gbDraw();const px=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,px);let sx=0,sy=0,n=0;
              for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=(y*w+x)*4,r=px[i],g=px[i+1],b=px[i+2];const k=col==='r'?(r>170&&g<100&&b<100):(r>200&&b>200&&g<90);if(k){sx+=x;sy+=h-1-y;n++;}}
              return n?{n,x:sx/n/GB.dpr,y:sy/n/GB.dpr}:{n:0};}""",col)
        print('1) lejos: sin detalle')
        await ev("gbSetView(-54.8*rad,-68.3*rad,0);GB.D=1+gbHofZ(2.5,-54.8*rad);GB.hint=false;gbKick()");await pg.wait_for_timeout(400)
        ok(await ev("!GB.dt"),'no se arma detalle a zoom 2.5');ok((await count('m'))['n']==0,'sin marcas de detalle')
        print('2) cerca: se arma solo')
        f0=await ev("T.fetches")
        await ev("GB.D=1+gbHofZ(3.9,-54.8*rad);gbKick()");await pg.wait_for_function("GB.dt&&GB.dt.ready",timeout=20000)
        print('   teselas nuevas:',await ev("T.fetches")-f0,'| z =',await ev("GB.dt.z"),'| caja',await ev("GB.dt.box.map(x=>+x.toFixed(3))"))
        ok(await ev("GB.dt.z")==4,'usa nivel 4 a zoom 3.9');await pg.wait_for_timeout(100)
        m=await count('m');ok(m['n']>200,f'se ven las marcas de las teselas de detalle ({m["n"]} px)')
        r=await count('r');p=await ev("gbProj(-54.8,-68.3)");d=math.hypot(r['x']-p['x'],r['y']-p['y'])
        await ev("GB.dt.ready=false");r0=await count('r');d0=math.hypot(r0['x']-p['x'],r0['y']-p['y']);await ev("GB.dt.ready=true;gbKick()")
        ok(abs(d-d0)<1.2 and d<4,f'con detalle dif {d:.2f}px vs solo base {d0:.2f}px (mismo corrimiento: la marca es grande y la cortan los bordes)')
        await pg.screenshot(path='lod_z4.png')
        print('3) más cerca: nivel 5; moverse fuera de la caja rearma')
        await ev("GB.D=1+gbHofZ(4.2,-54.8*rad);gbKick()");await pg.wait_for_function("GB.dt&&GB.dt.ready&&GB.dt.z==5",timeout=20000);ok(True,'nivel 5')
        c0=await ev("[GB.dt.x0,GB.dt.y0]")
        await ev("gbSetView(-40*rad,-50*rad,0);gbKick()");await pg.wait_for_function("GB.dt&&GB.dt.x0!=%d"%c0[0],timeout=20000);ok(True,f'rearmó en otra zona {c0} → {await ev("[GB.dt.x0,GB.dt.y0]")}')
        f1=await ev("T.fetches");await ev("gbSetView(-54.8*rad,-68.3*rad,0);gbKick()");await pg.wait_for_function("GB.dt&&GB.dt.x0==%d"%c0[0],timeout=20000)
        ok(await ev("T.fetches")==f1,'al volver usa las teselas guardadas (0 bajadas)')
        print('4) sin internet y sin teselas: usa la base sin huecos')
        await ev("T.netOk=false;KV.forEach((v,k)=>{if(k.startsWith('gd/'))KV.delete(k)});GB.dt=null;gbSetView(-20*rad,-60*rad,0);gbKick()");await pg.wait_for_timeout(1500)
        ok(await ev("!GB.dt||!GB.dt.ready"),'sin detalle disponible no rompe');await pg.screenshot(path='lod_off.png')
        print('ERRORES JS:',errs or 'ninguno')
        await b.close()
asyncio.run(main())
