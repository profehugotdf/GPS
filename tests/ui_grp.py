import asyncio,json,time
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
            req=route.request;url=req.url
            topic=url.split('ntfy.sh/')[1].split('/')[0].split('?')[0]
            if req.method=='POST':
                STORE.append({'id':'m%d'%(len(STORE)+1),'topic':topic,'message':req.post_data});await route.fulfill(status=200,body='{}');return
            since=url.split('since=')[1] if 'since=' in url else 'all'
            arr=[x for x in STORE if x['topic']==topic]
            if since!='all':
                ids=[x['id'] for x in arr];arr=arr[ids.index(since)+1:] if since in ids else arr
            await route.fulfill(status=200,body='\n'.join(json.dumps({'id':x['id'],'event':'message','message':x['message']}) for x in arr))
        await ctx.route('https://ntfy.sh/**',handler)
        A=await ctx.new_page();B=await ctx.new_page()
        for p in (A,B):p.on('pageerror',lambda e:errs.append(str(e)));await p.goto('file://'+BUILD+'/harness_grp.html')
        await A.evaluate("(async()=>{const raw=crypto.getRandomValues(new Uint8Array(16));await grpJoin('rumbo-gTEST',b64u.enc(raw));await grpShareMe('Hugo','meet');window.LK=grpLink();})()")
        link=await A.evaluate("LK");print('   link:',link);ok('#grupo=rumbo-gTEST.' in link,'link de grupo')
        keyB=link.split('.')[-1]
        await B.evaluate(f"(async()=>{{await grpJoin('rumbo-gTEST','{keyB}');await grpShareMe('Marta','meet');}})()")
        # cada uno se mueve
        for i in range(6):
            await A.evaluate(f"T.now+=10000;lastFix={{lat:-54.80+{i}*0.0002,lon:-68.30,acc:5,t:T.now}};shTick(lastFix)")
            await B.evaluate(f"T.now+=10000;lastFix={{lat:-54.805,lon:-68.31+{i}*0.0002,acc:5,t:T.now}};shTick(lastFix)")
            await asyncio.sleep(0.05)
        await A.wait_for_function("!SH.sending");await B.wait_for_function("!SH.sending")
        await A.evaluate("grpPoll(false)");await B.evaluate("grpPoll(false)");await asyncio.sleep(0.3)
        ta=await A.evaluate("$('#grp').innerText.replace(/\\n/g,' | ')");tb=await B.evaluate("$('#grp').innerText.replace(/\\n/g,' | ')")
        print('   panel de Hugo:',ta);print('   panel de Marta:',tb)
        ok('Marta' in ta and 'Hugo' not in ta.split('▼')[1],'Hugo ve a Marta (y no a sí mismo en la lista)')
        ok('Hugo' in tb,'Marta ve a Hugo')
        ok(await A.evaluate("grpLayer.items.some(x=>x.t==='mk'&&/Marta/.test(x.html))"),'marcador con nombre y color')
        await A.click('#grp [data-g=t]');ok(await A.evaluate("T.tgt&&T.tgt[2]==='Marta'"),'🎯 hacia Marta')
        await A.screenshot(path='grp.png')
        await A.evaluate("grpSetName('Hugo C.')");await asyncio.sleep(.2);await B.evaluate("grpPoll(false)");await asyncio.sleep(.3)
        ok('Hugo C.' in await B.evaluate("$('#grp').innerText"),'cambiar el nombre: los demás lo ven')
        ok('vos: Hugo C.' in await A.evaluate("$('#grp .gh').innerText"),'la cabecera muestra tu nombre')
        print('quieto y señal de vida')
        n0=len(STORE)
        for i in range(64):
            await A.evaluate(f"T.now+=10000;lastFix={{lat:-54.80+5*0.0002+{i%2}*0.00003,lon:-68.30,acc:5,t:T.now}};shTick(lastFix)")
            await asyncio.sleep(0.02)
        await A.wait_for_function("!SH.sending")
        sent=len(STORE)-n0;print('   envíos en 10 min quieto:',sent)
        ok(sent<=2,'quieto 10 min: solo 1 o 2 envíos (antes eran ~30)')
        await B.evaluate("grpPoll(false)");await asyncio.sleep(.3)
        ok('quieto' in await B.evaluate("$('#grp').innerText"),'Marta ve “⏸ quieto”')
        for i in range(8):
            await A.evaluate(f"T.now+=10000;lastFix={{lat:-54.80+5*0.0002+{i}*0.0003,lon:-68.30,acc:5,t:T.now}};shTick(lastFix)")
            await asyncio.sleep(0.02)
        await A.wait_for_function("!SH.sending");await B.evaluate("grpPoll(false)");await asyncio.sleep(.3)
        ok('quieto' not in await B.evaluate("$('#grp').innerText"),'se mueve: vuelve el ritmo normal')
        await B.evaluate("T.now+=26*60000;gdSilCheck();grpPanel()")
        tb=await B.evaluate("$('#grp').innerText.replace(/\\n/g,' | ')");print('   Marta:',tb[:200])
        ok('sin señal de vida' in tb and await B.evaluate("T.toasts.some(t=>/sin señal de vida/.test(t))"),'26 min sin nada: aviso amarillo “sin señal de vida”')
        await B.evaluate("grpLeave()");await asyncio.sleep(.1);await A.evaluate("grpPoll(false)");await asyncio.sleep(.2)
        ta=await A.evaluate("$('#grp').innerText");ok('dejó de compartir' in ta,'cuando Marta sale, Hugo lo ve')
        print('ERRORES JS:',errs or 'ninguno')
        await b.close()
asyncio.run(main())
