import asyncio
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m)
    if not c: raise SystemExit(1)
async def main():
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch(args=['--use-gl=swiftshader','--enable-unsafe-swiftshader']);pg=await b.new_page(viewport={'width':412,'height':860})
        pg.on('pageerror',lambda e:errs.append(str(e)));await pg.goto('file://'+BUILD+'/harness_3d.html');ev=pg.evaluate
        await ev("""(()=>{window.calcStats=window.calcStats||(p=>{let d=0;for(let i=1;i<p.length;i++)d+=hav(p[i-1],p[i]);return {dist:d}});window.guessAct=window.guessAct||(()=>null);
          const T0=Date.parse('2026-11-03T07:32:00-03:00');let la=-26.93,lo=-65.72;
          const mk=(name,act,n,dt,dl,hr0)=>{const pts=[],hr=[];const t0=window.TT||T0;for(let i=0;i<n;i++){la+=dl[0];lo+=dl[1];pts.push([la,lo,t0+i*dt,5,2000,0]);hr.push(hr0+(i%7));}window.TT=t0+n*dt+60000;return {id:name,name,act,pts,hr};};
          window.LEGS=[mk('Natación','swim',120,18000,[0.00003,0],140),mk('T1','walk',20,9000,[0,0.00002],150),mk('Bici','bike',300,20000,[0,0.0006],155),mk('T2','walk',15,8000,[0.00002,0],150),mk('Correr','run',200,25000,[-0.0002,0],160)];
          window.MT=multiTrack(LEGS);})()""")
        lg=await ev("JSON.stringify(MT.legs.map(l=>[l.act,l.lab||'',Math.round(l.dur/60000)]))");print('   etapas:',lg)
        ok(await ev("MT.legs.length===5&&MT.legs[1].lab==='T1'&&MT.legs[3].lab==='T2'&&!MT.legs[0].lab&&MT.hr.length===MT.pts.length"),'une las 5 etapas, marca T1 y T2 y junta el pulso')
        await ev("open3D({line:MT.pts.map(p=>[p[0],p[1]]),track:MT,relive:true})")
        await pg.wait_for_function("T3.rel&&T3.rel.go",timeout=60000)
        await ev("T3.rel.dur=12000;T3.rel.t0=null")
        seen=set()
        for k in range(40):
            await pg.wait_for_timeout(350)
            t=await ev("[$('#t3mk').textContent,$('#t3rel').innerText.split('\\n')[0]]");seen.add(t[0]+' '+t[1])
            if await ev("T3.rel.done"):break
        print('   visto:',sorted(seen))
        ok(any('🏊' in x and 'etapa 1 de 5' in x for x in seen) and any('⏱️ T1' in x for x in seen) and any('🚴' in x and 'etapa 3' in x for x in seen) and any('🏃' in x for x in seen),'el ícono y el cartel cambian por etapa (🏊 → T1 → 🚴 → T2 → 🏃)')
        await pg.wait_for_function("T3.rel.done",timeout=30000)
        t=await ev("$('#t3rel').innerText.replace(/\\n/g,' | ')");print('   final:',t)
        ok('T1' in t and 'T2' in t and '🚴' in t and 'Multideporte' in t,'resumen con el tiempo de cada etapa')
        await pg.screenshot(path='multi.png')
        print('barra de tiempo')
        print('   dbg',await ev("[$('#t3tl').hidden,$('#t3tk').innerHTML.length,!!T3.rel]"))
        ok(await ev("!$('#t3tl').hidden&&$('#t3tk').querySelectorAll('b').length===5"),'barra visible con las 5 etapas marcadas')
        await ev("const sb=$('#t3sb');sb.value=600;sb.dispatchEvent(new Event('input'))");await pg.wait_for_timeout(300)
        st=await ev("[T3.rel.go,Math.round(T3.rel.k*1000),$('#t3rel').innerText.split('\\n')[0],$('#t3tt').textContent,$('#t3rv').textContent]");print('   en 60%:',st)
        ok(st[0]==False and st[1]==600 and 'Bici' in st[2],'arrastrar a 60%: queda pausado en la bici')
        await ev("const sb=$('#t3sb');sb.value=950;sb.dispatchEvent(new Event('input'))");await pg.wait_for_timeout(200)
        ok('Correr' in await ev("$('#t3rel').innerText.split('\\n')[0]"),'arrastrar a 95%: corriendo')
        await ev("const sb=$('#t3sb');sb.value=850;sb.dispatchEvent(new Event('input'))");await pg.click('#t3pp');await pg.wait_for_timeout(500)
        k=await ev("T3.rel.k");ok(await ev("T3.rel.go") and k>0.85,'▶ sigue desde ahí (%.3f)'%k)
        await pg.click('#t3pp');k1=await ev("T3.rel.k");await pg.wait_for_timeout(400);ok(not await ev("T3.rel.go") and await ev("T3.rel.k")==k1,'⏸ pausa')
        print('mi vista')
        await ev("T3.cam.tilt=20;T3.cam.dist=900;T3.cam.az=135;t3MyView()")
        ok(await ev("$('#t3cm').textContent")=='📌','cambiar el ángulo activa 📌 Mi vista')
        await ev("const sb=$('#t3sb');sb.value=300;sb.dispatchEvent(new Event('input'))");await pg.wait_for_timeout(200)
        c=await ev("[T3.cam.tilt,T3.cam.dist,T3.cam.az,Math.round(T3.cam.tx),Math.round(T3.rel.now.x)]");print('   cámara',c)
        ok(c[0]==20 and c[1]==900 and c[2]==135 and c[3]==c[4],'mover la barra conserva ángulo, altura y orientación y sigue al ícono')
        await pg.click('#t3pp');await pg.wait_for_timeout(600);await pg.click('#t3pp')
        c=await ev("[T3.cam.tilt,T3.cam.dist,T3.cam.az]");ok(c==[20,900,135],'al seguir también la conserva')
        await pg.click('#t3cm');await pg.wait_for_timeout(200)
        ok(await ev("$('#t3cm').textContent")=='🎥' and await ev("T3.cam.tilt")==60,'🎥 vuelve a la cámara automática')
        await pg.screenshot(path='multi_tl.png')
        print('ERRORES JS:',errs or 'ninguno');await b.close()
asyncio.run(main())
