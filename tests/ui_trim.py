import asyncio,http.server,threading,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8787),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8787/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("""async()=>{const P=[];let la=-34.0,t=Date.now()-3600e3;for(let i=0;i<1000;i++){la-=200/111320;t+=1000;P.push([la,-58.4,t,10,10000-i*9,0]);}
          await DB.put('kv','track:v1',{id:'v1',name:'Vuelo',act:'plane',t0:P[0][2],pts:P,stats:calcStats(P),src:'rec',res:[]});}""")
        await pg.evaluate("showTrim('v1')");await pg.wait_for_timeout(500)
        await pg.evaluate("const a=$('#trA');a.value=700;a.dispatchEvent(new Event('input'));")
        t=await pg.evaluate("$('#trO').innerText");print('  ',t.replace('\n',' | '))
        ok('Queda' in t and '59,9' in t,'muestra cuánto queda del recorte')
        await pg.evaluate("document.querySelector('#sheet [data-act=new]').click()");await pg.wait_for_timeout(600)
        r=await pg.evaluate("(async()=>{const ks=(await DB.keys('kv','track:'));const all=[];for(const k of ks){const x=await DB.get('kv',k);all.push({id:x.id,n:x.pts.length,name:x.name,act:x.act,a0:x.pts[0][4]});}return all;})()")
        print('  ',r)
        ok(any(x['name']=='Vuelo (recorte)' and 290<x['n']<310 and x['act']=='plane' for x in r),'track nuevo con el último 30 % (la aproximación)')
        ok(any(x['id']=='v1' and x['n']==1000 for x in r),'el original queda entero')
        # aproximación automática
        await pg.evaluate("flStart()");await pg.wait_for_timeout(500)
        await pg.evaluate("S.flDest='AEP';S.flApprKm=80;FL.auto='down';")
        await pg.evaluate("__ok({coords:{latitude:-33.6,longitude:-58.4,accuracy:10,altitude:3000,speed:200,heading:180},timestamp:Date.now()});flDraw()")
        await pg.wait_for_timeout(300);ok(await pg.evaluate("REC.state")=='idle','a 107 km todavía no graba')
        await pg.evaluate("__ok({coords:{latitude:-34.0,longitude:-58.4,accuracy:10,altitude:2500,speed:180,heading:180},timestamp:Date.now()});flDraw()")
        await pg.wait_for_timeout(800);r=await pg.evaluate("({st:REC.state,act:REC.act,txt:$('#flt').innerText})");print('  ',r['st'],r['act'])
        ok(r['st']=='rec' and r['act']=='plane','a menos de 80 km de Aeroparque empieza a grabar como ✈️')
        # en tierra 1 minuto casi quieto → guarda solo
        await pg.evaluate("__ok({coords:{latitude:-34.5592,longitude:-58.4156,accuracy:5,altitude:10,speed:2,heading:0},timestamp:Date.now()});FL.slow=Date.now()-61000;flDraw()")
        await pg.wait_for_timeout(1500)
        r=await pg.evaluate("(async()=>{const out=[];for(const k of await DB.keys('kv','track:')){const x=await DB.get('kv',k);out.push(x.name);}return {st:REC.state,names:out}})()");print('  ',r)
        ok(r['st']=='idle' and any(n.startswith('Aterrizaje') for n in r['names']),'al quedar quieto en tierra, guarda "Aterrizaje …" solo')
        # despegue: carreteo y aceleración en la pista
        await pg.evaluate("""async()=>{FL.auto='up';FL.autoOn=0;FL.hist=[];const t0=Date.now()-30000;let la=-34.56;
          for(let i=0;i<30;i++){const v=i<10?3:(i-10)*2;la-=v/111320;__ok({coords:{latitude:la,longitude:-58.41,accuracy:5,altitude:10,speed:v,heading:180},timestamp:t0+i*1000});}
          __ok({coords:{latitude:la-0.0003,longitude:-58.41,accuracy:5,altitude:20,speed:40,heading:180},timestamp:Date.now()});flDraw();}""")
        await pg.wait_for_timeout(1500)
        r=await pg.evaluate("({st:REC.state,n:REC.pts.length,act:REC.act})");print('  ',r)
        ok(r['st']=='rec' and r['n']>=20,'al acelerar en la pista empieza a grabar, con los 40 s de antes')
        await pg.evaluate("(()=>{FL.hist=[];const t0=Date.now()-20000;for(let i=0;i<=20;i++)__ok({coords:{latitude:-35.5-i*0.002,longitude:-58.41,accuracy:5,altitude:2300,speed:230,heading:180},timestamp:t0+i*1000});flDraw();FL.lvl=Date.now()-181000;flDraw();})()")
        await pg.wait_for_timeout(1500)
        r=await pg.evaluate("(async()=>{const out=[];for(const k of await DB.keys('kv','track:')){const x=await DB.get('kv',k);out.push(x.name);}return {st:REC.state,names:out}})()");print('  ',r)
        ok(r['st']=='idle' and any(n.startswith('Despegue') for n in r['names']),'nivelado en crucero: guarda "Despegue …" solo')
        # sobre Tucumán volando a México
        await pg.evaluate("flPickOver()");await pg.wait_for_timeout(400)
        await pg.evaluate("const q=$('#flq');q.value='tucuman';q.dispatchEvent(new Event('input'))")
        vis=await pg.evaluate("[...document.querySelectorAll('#fll .item')].filter(i=>i.style.display!=='none').map(i=>i.innerText)");print('   búsqueda:',vis)
        ok(any('San Miguel de Tucumán' in v for v in vis),'buscar "tucuman" (sin tilde) encuentra San Miguel de Tucumán')
        await pg.evaluate("[...document.querySelectorAll('#fll .item')].find(i=>i.innerText.includes('San Miguel de Tucumán')).click()");await pg.wait_for_timeout(300)
        ok(await pg.evaluate("FL.auto==='over'&&S.flOver.name==='San Miguel de Tucumán'"),'queda elegido Tucumán')
        await pg.evaluate("__ok({coords:{latitude:-27.6,longitude:-65.0,accuracy:10,altitude:11000,speed:240,heading:0},timestamp:Date.now()});flDraw()");await pg.wait_for_timeout(300)
        ok(await pg.evaluate("REC.state")=='idle','a 88 km todavía no graba')
        await pg.evaluate("__ok({coords:{latitude:-26.9,longitude:-65.2,accuracy:10,altitude:11000,speed:240,heading:0},timestamp:Date.now()});flDraw()");await pg.wait_for_timeout(1000)
        ok(await pg.evaluate("REC.state")=='rec','al pasar a menos de 50 km de Tucumán, graba')
        await pg.evaluate("__ok({coords:{latitude:-26.2,longitude:-65.3,accuracy:10,altitude:11000,speed:240,heading:0},timestamp:Date.now()});flDraw()");await pg.wait_for_timeout(1500)
        r=await pg.evaluate("(async()=>{const out=[];for(const k of await DB.keys('kv','track:')){const x=await DB.get('kv',k);out.push(x.name);}return {st:REC.state,names:out}})()");print('  ',r)
        ok(r['st']=='idle' and any(n.startswith('Sobre San Miguel de Tucumán') for n in r['names']),'al alejarse guarda "Sobre San Miguel de Tucumán …"')
        # de manga a manga
        await pg.evaluate("FL.auto=null;FL.autoOn=0;__ok({coords:{latitude:-34.559,longitude:-58.416,accuracy:12,altitude:10,speed:0,heading:0},timestamp:Date.now()})")
        await pg.evaluate("flDraw();document.querySelector('#flt [data-fl=appr]').click()");await pg.wait_for_timeout(400)
        await pg.evaluate("document.querySelector('#sheet [data-act=full]').click()");await pg.wait_for_timeout(300)
        # GPS que salta adentro del avión parado (±15 m, velocidades falsas)
        await pg.evaluate("""async()=>{const t0=Date.now()-60000;for(let i=0;i<30;i++){__ok({coords:{latitude:-34.559+(Math.random()-.5)*0.00025,longitude:-58.416+(Math.random()-.5)*0.00025,accuracy:15,altitude:10,speed:Math.random()*2,heading:0},timestamp:t0+i*1000});flDraw();}}""")
        ok(await pg.evaluate("REC.state")=='idle','parado en la manga (GPS saltando) no arranca')
        # empuje hacia atrás y carreteo: 2,5 m/s durante 20 s
        await pg.evaluate("""async()=>{let la=-34.559;const t0=Date.now()-20000;for(let i=0;i<=20;i++){la+=2.5/111320;__ok({coords:{latitude:la,longitude:-58.416,accuracy:8,altitude:10,speed:2.5,heading:0},timestamp:t0+i*1000});FL.mvT=FL.mvT&&FL.mvT>Date.now()-11000?Date.now()-11000:FL.mvT;flDraw();}}""")
        await pg.wait_for_timeout(1000);ok(await pg.evaluate("REC.state")=='rec','al moverse el avión empieza a grabar')
        await pg.evaluate("__ok({coords:{latitude:-30,longitude:-60,accuracy:8,altitude:11000,speed:230,heading:0},timestamp:Date.now()});flDraw()")
        await pg.evaluate("__ok({coords:{latitude:-26.84,longitude:-65.10,accuracy:8,altitude:400,speed:0,heading:0},timestamp:Date.now()});FL.slow=Date.now()-181000;flDraw()");await pg.wait_for_timeout(1500)
        r=await pg.evaluate("(async()=>{const out=[];for(const k of await DB.keys('kv','track:')){const x=await DB.get('kv',k);out.push(x.name);}return {st:REC.state,names:out}})()");print('  ',r)
        ok(r['st']=='idle' and any(n.startswith('Vuelo 2') for n in r['names']),'detenido 3 min después de volar: guarda "Vuelo …" de manga a manga')
        print('ERRORES JS:',errs[:3] or 'ninguno');await b.close()
    srv.shutdown()
asyncio.run(main())
