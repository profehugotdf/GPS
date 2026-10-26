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
        # camino de cornisa: zigzag de 8 curvas cerradas subiendo la ladera del cerro (tramos de 400 m separados 70 m)
        await ev("""(()=>{const c=[];let la=-26.955,lo=-65.745;const dl=70/111320,dx=400/(111320*Math.cos(27*Math.PI/180));
          for(let k=0;k<8;k++){const d=k%2?-1:1;for(let i=0;i<=40;i++)c.push([la-k*dl,lo+(d>0?i:40-i)*dx/40]);}
          RT.res={car:{coords:c}};RT.sel='car';window.CR=c;})()""")
        await ev("open3D({})");await pg.wait_for_function("T3.vao&&T3.road",timeout=60000);await pg.wait_for_timeout(500)
        st=await ev("""(()=>{const R=T3.road,h=R.h;let g=0,raw=0;for(let i=3;i<h.length;i++){const ds=R.cum[i]-R.cum[i-3]||1;g=Math.max(g,Math.abs(h[i]-h[i-3])/ds);}
          let rg=0;for(let i=1;i<R.S.length;i++){const a=t3H(R.S[i-1][0],R.S[i-1][1]),b=t3H(R.S[i][0],R.S[i][1]);}
          let poke=0;for(let i=0;i<R.S.length;i++)poke=Math.max(poke,t3H(R.S[i][0],R.S[i][1])-h[i]);
          let sd=0;for(let i=2;i<h.length;i++)sd=Math.max(sd,Math.abs(h[i]-2*h[i-1]+h[i-2]));
          return {L:Math.round(R.L),subida:Math.round(h[h.length-1]-h[0]),gmax:+(g*100).toFixed(1),poke:+poke.toFixed(1),saltos:+sd.toFixed(2)};})()""")
        print('  ',st)
        ok(st['gmax']<=15.5,'auto: el perfil del camino no pasa de ~14 % de pendiente (medido cada 30 m)')
        ok(st['saltos']<0.5,'sin saltos: el cambio de pendiente de un punto al siguiente es mínimo')
        ok(st['poke']<6,'el relieve casi no asoma por encima del camino')
        await ev("document.querySelector('#t3fp').click();t3FlyStart()");await pg.wait_for_timeout(2500)
        ys=await ev("""new Promise(r=>{const a=[];const t=setInterval(()=>{const c=t3Cam();a.push([c.eye[1],T3.fpvP.f]);if(a.length>=25){clearInterval(t);r(a);}},120);})""")
        L=st['L'];sl=[abs(ys[i][0]-ys[i-1][0])/((ys[i][1]-ys[i-1][1])*L) for i in range(1,len(ys)) if ys[i][1]-ys[i-1][1]>0.003]
        print('   cámara: mayor pendiente entre cuadros %.0f %% (con relieve ×1,5)'%(max(sl)*100));ok(max(sl)<0.3,'la cámara a ras del suelo sube parejo, sin saltos')
        ok(await ev("!!T3.rvao&&T3.rn>100"),'se dibuja la cinta del camino')
        await pg.screenshot(path='road_fpv.png')
        await ev("T3.fly=null;T3.flyK=0;document.querySelector('#t3fp').click()");await pg.wait_for_timeout(800);await pg.screenshot(path='road_top.png')
        # bici permite más pendiente que auto
        await ev("close3D();RT.res={bike:{coords:CR}};RT.sel='bike';open3D({})");await pg.wait_for_function("T3.vao&&T3.road",timeout=60000)
        print('   bici: pendiente máx %.1f %%'%await ev("(()=>{const R=T3.road,h=R.h;let g=0;for(let i=1;i<h.length;i++)g=Math.max(g,Math.abs(h[i]-h[i-1])/((R.cum[i]-R.cum[i-1])||1));return g*100})()"))
        print('ERRORES JS:',errs[:5] or 'ninguno');await b.close()
asyncio.run(main())
