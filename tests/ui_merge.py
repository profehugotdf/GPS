import asyncio,http.server,threading,functools,os
from playwright.async_api import async_playwright
SITE=os.environ.get('RUMBO_SITE','.')
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8767),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':800})
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8767/index.html');await pg.wait_for_function('!!window.__ok')
        # 4 mosaicos vecinos (2x2, con calles repetidas en los bordes) de una misma descarga + 1 suelto otro día + 1 regional
        await pg.evaluate("""async()=>{
          const t0=Date.parse('2026-09-30T18:13:00-03:00');
          const mk=(i,bb,date,ways,regional)=>DB.put('kv','net:t'+i,{id:'t'+i,bb,date,ways,hz:[{lat:bb.s+.01,lon:bb.w+.01,k:'lomo'}],regional:!!regional});
          const W=(id,la,lo,z)=>({id,t:{highway:'residential'},n:[id*10,id*10+1],p:[la,lo,la+.001,lo+.001],z:z?[5,6]:undefined});
          const c=-34.6,o=-58.5;
          await mk(1,{s:c,w:o,n:c+.2,e:o+.2},t0,[W(1,c+.1,o+.1,1),W(99,c+.1,o+.19,1)]);          // 99 está en el borde: repetida
          await mk(2,{s:c,w:o+.2,n:c+.2,e:o+.4},t0+3*60000,[W(2,c+.1,o+.3,1),W(99,c+.1,o+.19,1)]);
          await mk(3,{s:c+.2,w:o,n:c+.4,e:o+.2},t0+4*60000,[W(3,c+.3,o+.1,1)]);
          await mk(4,{s:c+.2,w:o+.2,n:c+.4,e:o+.4},t0+6*60000,[W(4,c+.3,o+.3,1)]);
          await mk(5,{s:-54.9,w:-68.4,n:-54.7,e:-68.2},t0+86400000,[W(5,-54.8,-68.3,1)]);
          await mk(6,{s:-60,w:-80,n:-20,e:-50},t0+90000000,[W(6,-30,-60,0)],true);
          netsChanged();
        }""")
        await pg.evaluate("showMapMgr()");await pg.wait_for_selector('[data-act=gmerge]')
        cards=await pg.evaluate("[...document.querySelectorAll('#sheet .card')].map(c=>c.innerText.replace(/\\n/g,' | ').slice(0,150)).filter(t=>/calles|mosaicos|regional/.test(t))")
        for c in cards: print('  ',c)
        assert any('4 mosaicos' in c for c in cards), 'grupo de 4'
        assert sum('regional' in c for c in cards)==1
        print('1) lista agrupada: 1 grupo de 4 + 1 suelto + 1 regional =',len(cards),'tarjetas (antes eran 6)')
        # ver zona del grupo
        await pg.click('[data-act=gview]');await pg.wait_for_timeout(500)
        bb=await pg.evaluate("(()=>{const b=map.getBounds();return [b.getSouth().toFixed(2),b.getWest().toFixed(2),b.getNorth().toFixed(2),b.getEast().toFixed(2)]})()");print('2) Ver zona encuadra el conjunto:',bb)
        await pg.evaluate("showMapMgr()");await pg.wait_for_selector('[data-act=gmerge]')
        # unir (dos toques)
        await pg.click('[data-act=gmerge]');await pg.click('[data-act=gmerge]');await pg.wait_for_timeout(1500)
        left=await pg.evaluate("DB.all('kv','net:').then(l=>l.map(n=>({n:n.ways.length,hz:n.hz.length,reg:!!n.regional,ids:n.ways.map(w=>w.id).sort((a,b)=>a-b).join(',')})))")
        print('3) tras unir:',left)
        grp=[x for x in left if not x['reg'] and x['n']>2]
        assert len(left)==3 and len(grp)==1 and grp[0]['ids']=='1,2,3,4,99' and grp[0]['hz']==4, 'unión'
        print('   4 mosaicos → 1 bloque, la calle 99 quedó una sola vez, los 4 lomos se conservan')
        print('   toast:',await pg.evaluate("document.querySelector('#toast')?.innerText||''"))
        idx=await pg.evaluate("DB.all('kv','netidx:').then(l=>l.length)");print('   índice =',idx,'entradas')
        # el grafo se arma con la red unida
        await pg.evaluate("showMapMgr()");await pg.wait_for_selector('.card')
        cards=await pg.evaluate("[...document.querySelectorAll('#sheet .card')].map(c=>c.innerText.replace(/\\n/g,' | ').slice(0,120)).filter(t=>/calles|tramos/.test(t))")
        for c in cards: print('  ',c)
        await pg.evaluate("map.setView([-34.5,-58.3],13)")
        ok=await pg.evaluate("ensureGraph({center:[-34.5,-58.3]}).then(g=>!!g)");print('4) ensureGraph con la red unida:',ok)
        # borrar todo de un grupo (probar con un grupo de 2 nuevo)
        await pg.evaluate("""async()=>{const t=Date.parse('2026-10-01T10:00:00-03:00');for(let i=0;i<2;i++)await DB.put('kv','net:b'+i,{id:'b'+i,bb:{s:-30+i*.1,w:-60,n:-29.9+i*.1,e:-59.9},date:t+i*60000,ways:[{id:700+i,t:{},n:[1,2],p:[-30,-60,-29.99,-59.99]}],hz:[],regional:false});netsChanged();}""")
        await pg.evaluate("showMapMgr()");await pg.wait_for_selector('[data-act=gdel]')
        await pg.click('[data-act=gdel]');await pg.click('[data-act=gdel]');await pg.wait_for_timeout(600)
        print('5) borrar grupo: quedan',await pg.evaluate("DB.keys('kv','net:').then(k=>k.length)"),'redes (esperado 3)')
        await b.close()
    print('ERRORES JS:',errs or 'ninguno')
asyncio.run(main())
