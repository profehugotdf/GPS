import asyncio,json
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
STORE=[]
async def main():
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();ctx=await b.new_context()
        async def handler(route):
            req=route.request;url=req.url;topic=url.split('ntfy.sh/')[1].split('/')[0].split('?')[0]
            if req.method=='POST':STORE.append({'id':'m%d'%(len(STORE)+1),'topic':topic,'message':req.post_data});await route.fulfill(status=200,body='{}');return
            since=url.split('since=')[1] if 'since=' in url else 'all';arr=[x for x in STORE if x['topic']==topic]
            if since!='all':ids=[x['id'] for x in arr];arr=arr[ids.index(since)+1:] if since in ids else arr
            await route.fulfill(status=200,body='\n'.join(json.dumps({'id':x['id'],'event':'message','message':x['message']}) for x in arr))
        await ctx.route('https://ntfy.sh/**',handler)
        A=await ctx.new_page();B=await ctx.new_page()
        for p in (A,B):p.on('pageerror',lambda e:errs.append(str(e)));await p.goto('file://'+BUILD+'/harness_grp.html')
        await A.evaluate("(async()=>{const raw=crypto.getRandomValues(new Uint8Array(16));await grpJoin('rumbo-gSR',b64u.enc(raw));await grpShareMe('Hugo','meet');window.KB=GRP.keyB;})()")
        kb=await A.evaluate("KB")
        print('1) Hugo crea la búsqueda: sectores de 200 m, franja 30 m')
        await A.evaluate("showSearchSetup()");await A.wait_for_timeout(200)
        await A.click('[data-act=m][data-k="200"]');await A.click('[data-act=sw][data-k="30"]');await A.click('[data-act=go]');await A.wait_for_timeout(300)
        n=await A.evaluate("SR.op&&SR.op.cells.length");print('   sectores:',n);ok(n and n>=6,'sectores creados')
        print('2) Marta se suma después y ve la búsqueda')
        await B.evaluate(f"(async()=>{{await grpJoin('rumbo-gSR','{kb}');await grpShareMe('Marta','meet');}})()");await B.wait_for_timeout(300)
        ok(await B.evaluate("SR.op&&SR.op.cells.length")==n,'Marta recibió los mismos sectores')
        print('3) Marta camina por el sector A1 (de oeste a este, ida y vuelta)')
        await B.evaluate("""(async()=>{const op=SR.op,b=srCell(op,'0-0');let t=0;
          for(let pass=0;pass<5;pass++){const lat=b.n-(pass+.5)*(b.n-b.s)/5;for(let k=0;k<=10;k++){const lon=pass%2?b.e-(b.e-b.w)*k/10:b.w+(b.e-b.w)*k/10;T.now+=10000;lastFix={lat,lon,acc:5,t:T.now};shTick(lastFix,true);await new Promise(r=>setTimeout(r,5));}}})()""")
        await B.wait_for_function("!SH.sending");await B.evaluate("shTick(null,true)");await B.wait_for_function("!SH.sending&&SH.queue.length==0")
        await A.evaluate("grpPoll(false)");await A.wait_for_timeout(300);await A.evaluate("srCompute(true)")
        cov=await A.evaluate("SR.cov['0-0']");other=await A.evaluate("SR.cov['0-2']||0");print('   A1 recorrido:',cov,'%  · otro sector:',other,'%')
        ok(cov>=60,'Hugo ve A1 bastante recorrido');ok(other<10,'los demás sectores siguen sin recorrer')
        ok(await A.evaluate("srStatus('0-0')")=='curso','A1 queda "en curso" (no revisado)')
        print('4) Marta lo marca revisado y asigna equipo')
        await B.evaluate("srCompute(true);showSector('0-0')");await B.click('[data-act=tm][data-k="Equipo 2"]');await B.click('[data-act=st][data-k="ok"]');await B.wait_for_timeout(200)
        await A.evaluate("grpPoll(false)");await A.wait_for_timeout(300)
        ok(await A.evaluate("srStatus('0-0')")=='ok' and await A.evaluate("SR.op.st['0-0'].team")=='Equipo 2','Hugo ve A1 revisado por Equipo 2')
        t=await A.evaluate("$('#grp').innerText.replace(/\\n/g,' | ')");print('   panel:',t);ok('Búsqueda' in t and '✅ 1' in t,'resumen en el panel del grupo')
        await A.evaluate("showSearch()");await A.click('[data-act=gj]');f=await A.evaluate("T.file&&T.file[0]");ok(f=='busqueda.geojson','exporta GeoJSON')
        print('ERRORES JS:',errs or 'ninguno')
        await b.close()
asyncio.run(main())
