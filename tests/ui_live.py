import asyncio
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':800});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('file://'+BUILD+'/harness_live.html');ev=pg.evaluate
        await ev("""(()=>{const A=[-54.8065,-68.3029],k=1/(111195*Math.cos(54.8*rad));const pts=[];for(let i=0;i<=100;i++)pts.push([A[0],A[1]+i*50*k]);for(let i=99;i>=0;i--)pts.push([A[0],A[1]+i*50*k]);
          RT.res={foot:{coords:pts,dist:10000}};RT.sel='foot';RT.to={label:'Llegada'};})()""")
        print('1) compartir')
        await ev("showShare()");ok('Mostrar también la ruta' in await ev("$('#sBody').textContent"),'ofrece mandar el circuito')
        await pg.fill('#shn','Hugo');await pg.dispatch_event('#shn','change')
        await pg.click('[data-act=go]');await pg.wait_for_function("SH.on&&STORE.length>=1")
        ok(await ev("STORE[0].len<3900"),f'meta con circuito: {await ev("STORE[0].len")} bytes')
        ok(await ev("!/Hugo|-54/.test(STORE[0].message)"),'en el servidor queda ilegible')
        ok(await ev("!$('#shpill').hidden"),'aparece la pastilla 📡')
        link=await ev("shLink()");print('   link:',link);ok('#seguir=rumbo-' in link,'link con clave en el #')
        print('2) corre 25 min a 3 m/s, con 4 min sin señal')
        await ev("""(async()=>{const A=[-54.8065,-68.3029],k=1/(111195*Math.cos(54.8*rad));
          for(let t=0;t<=2500;t+=5){T.now+=5000;T.offline=(t>600&&t<840);const d=3*t,pos=d<=5000?d:10000-d;
            const f={lat:A[0]+0.00003,lon:A[1]+pos*k,acc:6,t:T.now};lastFix=f;shTick(f);await new Promise(r=>setTimeout(r,2));}
          T.offline=false;})()""")
        await pg.wait_for_function("!SH.sending");await ev("shTick(null,true)");await pg.wait_for_function("!SH.sending&&SH.queue.length==0")
        n=await ev("STORE.length");np=await ev("SH.seq")
        ok(np>=70 and np<=86,f'{np} envíos de posiciones (~1 cada 30 s, la mitad que antes; los del corte salen juntos)')
        ok(await ev("Math.max(...STORE.map(x=>x.len))<3900"),'todos los mensajes < 3900 bytes')
        await ev("shStop()");await pg.wait_for_function("!SH.on")
        print('3) quien sigue abre el link (después de terminar)')
        T=await ev("T.now");await ev("T.now+=40000")
        tk=link.split('#seguir=')[1].split('.')
        await ev(f"folStart('{tk[0]}','{tk[1]}')");await pg.wait_for_function("FOL.pts.length>0")
        npts=await ev("FOL.pts.length");ok(npts>=160,f'recibió {npts} puntos (cada 15 s)')
        txt=await ev("$('#fol').textContent");print('   panel:',txt)
        ok('Hugo' in txt and '7,45 de 10,0 km' in txt,'muestra avance sobre el circuito (pasó la vuelta)')
        ok('5:33 /km' in txt,'ritmo de corredor')
        ok('Terminó' in txt,'avisa que terminó de compartir')
        print('4) en vivo: nueva sesión, la siguen mientras corre')
        await ev("folStop();STORE.length=0");await ev("showShare()");await pg.click('[data-act=go]');await pg.wait_for_function("SH.on&&STORE.length>=1")
        link=await ev("shLink()");tk=link.split('#seguir=')[1].split('.')
        await ev("""(async()=>{const A=[-54.8065,-68.3029],k=1/(111195*Math.cos(54.8*rad));
          for(let t=0;t<=900;t+=5){T.now+=5000;const d=3.3*t;const f={lat:A[0],lon:A[1]+d*k,acc:6,t:T.now};shTick(f);await new Promise(r=>setTimeout(r,2));}})()""")
        await pg.wait_for_function("!SH.sending")
        await ev(f"folStart('{tk[0]}','{tk[1]}')");await pg.wait_for_function("FOL.pts.length>0")
        txt=await ev("$('#fol').textContent");print('   panel:',txt)
        ok('Llega a las' in txt and 'km 3:' in txt,'hora estimada de llegada y próximos km')
        ok(await ev("folLayer.items.some(x=>x.t==='mk'&&/Hugo/.test(x.html))"),'marcador con el nombre')
        await pg.click('#fol [data-f=g]');ok(await ev("T.tgt&&T.tgt[2]==='Hugo'"),'🎯 apunta a la última posición')
        await pg.screenshot(path='live.png')
        print('5) link roto');await ev("folStop()");await ev("folStart('rumbo-x','AAAA')");ok(await ev("!FOL.on"),'clave inválida: avisa y no sigue')
        print('ERRORES JS:',errs or 'ninguno')
        await b.close()
asyncio.run(main())
