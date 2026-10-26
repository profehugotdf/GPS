import asyncio
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
async def main():
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':800})
        pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' else None)
        await pg.goto('file://'+BUILD+'/harness.html')
        await pg.evaluate("""async()=>{
          const t0=Date.parse('2026-09-30T18:13:00-03:00');
          const W=(id,la,lo,z)=>({id,t:{},n:[id*10,id*10+1],p:[la,lo,la+.001,lo+.001],z:z?[5,6]:undefined});
          const mk=(i,bb,date,ways,reg)=>KV.set('net:'+i,{id:i,bb,date,ways,hz:[{lat:bb.s+.01,lon:bb.w+.01,k:'lomo'}],regional:!!reg});
          const c=-34.6,o=-58.5;
          // A y A2: la misma zona bajada dos veces por accidente (casi iguales)
          mk('A',{s:c,w:o,n:c+.2,e:o+.2},t0,[W(1,c+.1,o+.1,1),W(50,c+.1,o+.15,1)]);
          mk('A2',{s:c+.01,w:o+.01,n:c+.21,e:o+.21},t0+60000,[W(1,c+.1,o+.1,1),W(50,c+.1,o+.15,1),W(51,c+.2,o+.2,1)]);
          // B al este, tocando; C encima de los dos (puente)
          mk('B',{s:c,w:o+.2,n:c+.2,e:o+.4},t0+120000,[W(2,c+.1,o+.3,1)]);
          mk('C',{s:c+.05,w:o+.15,n:c+.15,e:o+.25},t0+180000,[W(3,c+.1,o+.2,1)]);
          // D lejos (otro día) y un regional
          mk('D',{s:-54.9,w:-68.4,n:-54.7,e:-68.2},t0+86400000,[W(7,-54.8,-68.3,1)]);
          mk('R',{s:-60,w:-80,n:-20,e:-50},t0+90000000,[W(8,-30,-60,0)],true);
          await showMapMgr();
        }""")
        txt=lambda sel:pg.eval_on_selector_all(sel,"e=>e.map(x=>x.innerText.replace(/\\n/g,' | '))")
        # 1 modo normal
        btns=await pg.eval_on_selector_all('[data-act]',"e=>e.map(x=>x.dataset.act)")
        assert 'senter' in btns and 'gpick' in btns, btns
        print('1) modo normal: hay botón "☑️ Elegir mosaicos" y "☑️ Elegir" en el grupo:',[t for t in await txt('[data-act=senter],[data-act=gpick]')])
        # 2 entrar a selección
        await pg.click('[data-act=senter]');await pg.wait_for_selector('[data-act=ssel]')
        rows=await txt('#sBody .item:has([data-act=ssel])')
        for r in rows: print('   ',r[:110])
        warn=[r for r in rows if '⚠️' in r]
        assert len(rows)==5 and len(warn)==4, (len(rows),len(warn))
        print('2) selección: 5 mosaicos (el regional no está), 4 con ⚠️ (A, A2, B, C), D sin aviso')
        rects=await pg.evaluate("selLayer.rects.length");assert rects==5;print('   rectángulos dibujados en el mapa:',rects)
        # 2b nombre del par y foco en el mapa
        hints=await pg.eval_on_selector_all('#sBody .item:has([data-act=ssel]) small[style]',"e=>e.map(x=>x.innerText)")
        for h in hints: print('   aviso:',h)
        assert all('calles' in h and '%' in h for h in hints) and len(hints)==4
        await pg.click('[data-act=sone][data-id=A]')
        cols=await pg.evaluate("selLayer.rects.map(r=>r.o.color)")
        blue=cols.count('#1E6BFF');yel=cols.count('#E0A100')
        print('2b) Ver en A: azul =',blue,'| amarillos (los que se pisan con A) =',yel,'| el último dibujado es el azul =',cols[-1]=='#1E6BFF')
        assert blue==1 and yel==2 and cols[-1]=='#1E6BFF'
        await pg.click('[data-act=sone][data-id=A]');cols=await pg.evaluate("selLayer.rects.map(r=>r.o.color)");assert '#1E6BFF' not in cols;print('    tocar Ver otra vez quita el resaltado')
        await pg.evaluate("document.querySelector('[data-act=spair][data-id=B]').click()")
        print('    "Elegir con su par" en B:',await pg.inner_text('#nselN'),'| toast:',await pg.evaluate("REC.toasts.at(-1)"))
        assert await pg.inner_text('#nselN')=='2 elegidos'
        sel=await pg.evaluate("[...NSEL].sort().join()");assert sel=='B,C',sel
        await pg.click('[data-act=snone]');assert await pg.evaluate("NFOC===null")
        # 3 superpuestos
        await pg.click('[data-act=sovl]')
        print('3) "Los superpuestos":',await pg.inner_text('#nselN'),'| botón:',await pg.inner_text('[data-act=smerge]'),'| naranjas en el mapa:',await pg.evaluate("selLayer.rects.filter(r=>r.o.color==='#F04A1C').length"))
        assert await pg.inner_text('#nselN')=='4 elegidos'
        # 4 tocar uno en el lugar, sin saltar arriba
        await pg.evaluate("sBody.scrollTop=60")
        before=await pg.evaluate("sBody.scrollTop")
        await pg.evaluate("document.querySelector('[data-act=ssel][data-id=C]').click()")
        after=await pg.evaluate("sBody.scrollTop")
        print('4) quitar C de la selección: ',await pg.inner_text('#nselN'),'| botón de C =',await pg.inner_text('[data-act=ssel][data-id=C]'),'| scroll',before,'→',after)
        assert await pg.inner_text('#nselN')=='3 elegidos' and after==before and before>0
        await pg.evaluate("document.querySelector('[data-act=ssel][data-id=C]').click()");assert await pg.inner_text('#nselN')=='4 elegidos'
        # 5 Ver elegidos
        await pg.click('[data-act=sview]');fit=await pg.evaluate("REC.fit.at(-1)")
        print('5) Ver: encuadra',[round(x,2) for x in fit['b'][0]+fit['b'][1]],'con margen abajo',fit['o']['paddingBottomRight'])
        assert fit['o']['paddingBottomRight'][1]>0
        # 6 unir con doble toque; puente C junta todo
        await pg.click('[data-act=smerge]');t1=await pg.inner_text('[data-act=smerge]');await pg.click('[data-act=smerge]');await pg.wait_for_function('!document.querySelector("[data-act=smerge]")||document.querySelector("#nselN").innerText==="0 elegidos"');await pg.wait_for_timeout(300)
        print('6) Unir: primer toque dice "'+t1+'"; toast:',await pg.evaluate("REC.toasts.at(-1)"))
        nets=await pg.evaluate("DB.all('kv','net:').then(l=>l.map(n=>({id:n.id,reg:!!n.regional,ways:n.ways.map(w=>w.id).sort((a,b)=>a-b).join(','),hz:n.hz.length})))")
        print('   redes:',nets)
        merged=[n for n in nets if n['ways']=='1,2,3,50,51']
        assert len(nets)==3 and len(merged)==1 and merged[0]['hz']==4,'4 mosaicos (A, A2, B, C) en un solo bloque, calles 1 y 50 una sola vez'
        assert {n['id'] for n in nets if n['id'] in('D','R')}=={'D','R'}
        print('   A, A2, B y C → 1 bloque (calles 1 y 50 repetidas quedaron una vez); D y el regional intactos')
        print('   tras unir, la selección quedó:',await pg.inner_text('#nselN'),'| mosaicos en la lista:',len(await txt('#sBody .item:has([data-act=ssel])')))
        # 7 borrar elegidos
        await pg.click('[data-act=ssel][data-id=D]');await pg.click('[data-act=sdel]');t2=await pg.inner_text('[data-act=sdel]');await pg.click('[data-act=sdel]');await pg.wait_for_timeout(600)
        keys=await pg.evaluate("DB.keys('kv','net:')")
        print('7) Borrar elegidos: primer toque =',t2,'| quedan',keys)
        assert 'net:D' not in keys and 'net:R' in keys and len(keys)==2
        # 8 salir y cerrar reinicia
        await pg.click('[data-act=sexit]');await pg.wait_for_function('!document.querySelector("#nselN")');print('8) Salir vuelve a lo normal:',await pg.evaluate("NSEL===null"),'| rectángulos de selección:',await pg.evaluate("selLayer.rects.length"))
        print('   con un solo mosaico guardado no se ofrece "Elegir" =',await pg.query_selector('[data-act=senter]') is None)
        await pg.evaluate("closeSheet()");print('   cerrar la hoja reinicia la selección:',await pg.evaluate("NSEL===null"))
        # 9 gpick desde un grupo
        await pg.evaluate("""async()=>{KV.clear();const t0=Date.now()-600000;for(const i of [1,2,3])KV.set('net:g'+i,{id:'g'+i,bb:{s:-30+i*.1,w:-60,n:-29.9+i*.1,e:-59.9},date:t0+i*60000,ways:[{id:900+i,t:{},n:[1,2],p:[-30,-60,-29.99,-59.99]}],hz:[],regional:false});await showMapMgr();}""")
        await pg.click('[data-act=gpick]');await pg.wait_for_selector('[data-act=ssel]');print('9) "☑️ Elegir" en un grupo de 3 deja elegidos:',await pg.inner_text('#nselN'))
        assert await pg.inner_text('#nselN')=='3 elegidos'
        await b.close()
    print('ERRORES JS:',errs or 'ninguno')
asyncio.run(main())
