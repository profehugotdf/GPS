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
        # track con zigzag de GPS (±5 m al costado)
        await ev("""window.TR={name:'Ruido',act:'bike',t0:1e12,pts:Array.from({length:500},(_,i)=>{const n=(Math.random()-.5)*10/111320;return [-26.93-i*0.00009+n,-65.715+0.012*Math.sin(i/90)+n,1e12+i*4000,5,2000+i,0]})}""")
        await ev("open3D({line:TR.pts.map(p=>[p[0],p[1]]),track:TR})");await pg.wait_for_function("T3.rel&&T3.vao",timeout=60000);await pg.wait_for_timeout(500)
        # zigzag: ángulo entre tramos consecutivos
        zz=await ev("""(()=>{const f=P=>{let s=0,n=0;for(let i=2;i<P.length;i++){const a=Math.atan2(P[i-1][1]-P[i-2][1],P[i-1][0]-P[i-2][0]),b=Math.atan2(P[i][1]-P[i-1][1],P[i][0]-P[i-1][0]);let d=Math.abs(b-a);if(d>Math.PI)d=2*Math.PI-d;s+=d;n++;}return s/n*180/Math.PI;};
          const raw=TR.pts.map(p=>t3XZ(p[0],p[1]));return [f(raw),f(T3.rel.XZ)];})()""")
        print('   giro medio entre tramos (°): crudo %.1f · suavizado %.1f'%tuple(zz));ok(zz[1]<zz[0]/3,'el zigzag del GPS se suaviza')
        # relieve con pozos y lomos bajo el camino
        rough="(()=>{const R=T3.rel;let s=0,n=0,p=null,pp=null;for(let d=0;d<R.L;d+=8){const {i,t}=t3RelAt(R,d),A=R.XZ[i-1],B=R.XZ[i],h=t3H(A[0]+(B[0]-A[0])*t,A[1]+(B[1]-A[1])*t);if(pp!=null){s+=Math.abs(h-2*p+pp);n++;}pp=p;p=h;}return s/n;})()"
        r0=await ev(rough)
        await ev("for(let q=0;q<T3.H.length;q++)T3.H[q]+=(Math.random()-.5)*12")
        r1=await ev(rough);await ev("t3Carve(T3.line)");r2=await ev(rough)
        print('   lomos (cambio de pendiente cada 8 m, m): terreno %.2f · con pozos de ±6 m %.2f · con la traza abierta %.2f'%(r0,r1,r2))
        ok(r2<r1/3 and r2<r0*1.4,'la traza saca los lomos de burro (queda como el terreno sin pozos)')
        # kayak: superficie plana
        prof="(()=>{const R=T3.rel,a=[];for(let d=0;d<R.L;d+=20){const {i,t}=t3RelAt(R,d),A=R.XZ[i-1],B=R.XZ[i];a.push(t3H(A[0]+(B[0]-A[0])*t,A[1]+(B[1]-A[1])*t));}return [Math.min(...a),Math.max(...a)];})()"
        await ev("close3D()");await ev("TR.act='kayak';open3D({line:TR.pts.map(p=>[p[0],p[1]]),track:TR})");await pg.wait_for_function("T3.rel&&T3.vao",timeout=60000)
        await ev("for(let q=0;q<T3.H.length;q++)T3.H[q]=5+(Math.random()-.5)*8");await ev("t3Carve(T3.line,t3TrackPts(TR).runs)")
        p=await ev(prof);print('   kayak en agua con pozos de ±4 m: altura del camino %.2f a %.2f'%tuple(p));ok(p[1]-p[0]<0.5,'en kayak (lago o mar) el camino queda plano')
        # río con desnivel: baja 60 m a lo largo
        await ev("{const n=T3.n;for(let j=0;j<n;j++)for(let i=0;i<n;i++)T3.H[j*n+i]=400-j*0.6+(Math.random()-.5)*8;}");await ev("t3Carve(T3.line,t3TrackPts(TR).runs)")
        rr=await ev(rough);p=await ev(prof);print('   río: de %.0f a %.0f m, lomos %.3f'%(p[0],p[1],rr));ok(p[1]-p[0]>20 and rr<0.1,'en un río con desnivel baja de a poco, sin lomos')
        # tierra a agua en multideporte: el suelo del mar nunca queda bajo cero
        await ev("close3D();TR.act='kayak';open3D({line:TR.pts.map(p=>[p[0],p[1]]),track:TR})");await pg.wait_for_function("T3.rel&&T3.vao",timeout=60000)
        ok(await ev("T3.H.reduce((a,b)=>Math.min(a,b),1e9)")>=0,'el mar se muestra en la superficie (sin el fondo)')
        await ev("close3D();TR.act='bike';open3D({line:TR.pts.map(p=>[p[0],p[1]]),track:TR})");await pg.wait_for_function("T3.rel&&T3.vao",timeout=60000)
        await ev("t3RelStart()");await pg.wait_for_timeout(3000);await ev("document.querySelector('#t3fp').click()");await pg.wait_for_timeout(2000)
        await pg.screenshot(path='smooth_fpv.png')
        print('ERRORES JS:',errs[:5] or 'ninguno');await b.close()
asyncio.run(main())
