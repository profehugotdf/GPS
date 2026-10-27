import asyncio,re,http.server,threading,os,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
import sys
from apps import otra_app
BICI=otra_app('RUMBO_BICI','https://profehugotdf.github.io/Bici-Indoor-/')
if BICI is None:print('SALTEADA: no hay Bici Indoor para probar');sys.exit(77)
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8779),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[];berrs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();ctx=await b.new_context(viewport={'width':412,'height':860})
        await ctx.route('https://profehugotdf.github.io/Bici-Indoor-/**',lambda r:r.fulfill(status=200,content_type='text/html',body=BICI))
        pg=await ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8779/index.html');await pg.wait_for_function('!!window.__ok')
        # relieve inventado: sube 6 % hacia el oeste, con ruido de ±8 m, y una ladera al norte del camino entre 2 y 3,5 km
        await pg.evaluate("""()=>{
          window.E=(la,lo)=>{const xw=(-65.20-lo)*111320*Math.cos(26.8*Math.PI/180),yn=(la+26.80)*111320;let h=500+0.06*Math.max(0,xw)+8*Math.sin(xw/23)*Math.cos(yn/17);
            if(xw>2000&&xw<3500&&yn>5)h+=Math.min(60,yn*1.2);return h;};
          fetchDemList=async(list,z)=>{const m=new Map();for(const t of list){const a=new Float32Array(65536);for(let j=0;j<256;j++)for(let i=0;i<256;i++){const X=t.x+(i+.5)/256,Y=t.y+(j+.5)/256,lo=X/2**z*360-180,la=Math.atan(Math.sinh(Math.PI*(1-2*Y/2**z)))*180/Math.PI;a[j*256+i]=E(la,lo);}m.set(t.x+'/'+t.y,a);}return m;};
          demMissing=async()=>0;
          const ring=(s,w,n,e)=>[{lat:s,lon:w},{lat:s,lon:e},{lat:n,lon:e},{lat:n,lon:w},{lat:s,lon:w}];
          const lo=km=>-65.20-km*1000/(111320*Math.cos(26.8*Math.PI/180));
          bkOsm=async()=>[
            {type:'way',tags:{natural:'coastline'},geometry:[{lat:-26.8008,lon:lo(0)},{lat:-26.8008,lon:lo(1.2)}]},      // agua a la izquierda (sur) los primeros 1,2 km... 
            {type:'way',tags:{landuse:'residential'},geometry:ring(-26.81,lo(1.5),-26.79,lo(0.8))},
            {type:'way',tags:{landuse:'forest'},geometry:ring(-26.81,lo(5.5),-26.79,lo(4))},
            {type:'way',tags:{landuse:'farmland'},geometry:ring(-26.81,lo(3.5),-26.79,lo(2))},
            ...Array.from({length:46},(_,i)=>({type:'way',tags:i%7?{building:'house'}:{building:'apartments','building:levels':'6'},center:{lat:-26.80+20/111320,lon:lo(0.8+i*0.015)}})),
            {type:'way',tags:{highway:'residential',sidewalk:'both',lit:'yes'},geometry:[{lat:-26.80,lon:lo(0.75)},{lat:-26.80,lon:lo(1.55)}]},
            {type:'way',tags:{highway:'track',tracktype:'grade3'},geometry:[{lat:-26.80,lon:lo(2)},{lat:-26.80,lon:lo(3.4)}]},
            {type:'way',tags:{highway:'path'},geometry:[{lat:-26.80,lon:lo(4)},{lat:-26.80,lon:lo(5.6)}]}];
          const E0=window.E;window.E=(la,lo)=>{const xw=(-65.20-lo)*111320*Math.cos(26.8*Math.PI/180),yn=(la+26.80)*111320;return E0(la,lo)+1500*Math.exp(-((xw-3000)**2+(yn-8000)**2)/(2*2500**2));};
          bkPeaks=async()=>[{n:'Cerro Prueba',e:2185,la:+(-26.80+8000/111320).toFixed(5),lo:+lo(3).toFixed(5)},{n:'Escondido',e:520,la:-26.75,lo:lo(3)}];
          getTileBlob=async(url)=>{const m=url.match(/tile\\/(\\d+)\\/(\\d+)\\/(\\d+)/),z=+m[1],y=+m[2],c=document.createElement('canvas');c.width=c.height=256;const g=c.getContext('2d');
            for(let j=0;j<256;j++){const Y=y+(j+.5)/256,la=Math.atan(Math.sinh(Math.PI*(1-2*Y/2**z)))*180/Math.PI;g.fillStyle=la>-26.80?'rgb(40,110,40)':'rgb(170,140,80)';g.fillRect(0,j,256,1);}
            return await new Promise(r=>c.toBlob(r));};
          window.LL=Array.from({length:601},(_,i)=>[-26.80+(Math.random()-.5)*6/111320,lo(i*0.01)]);
        }""")
        async with ctx.expect_page() as pinfo:
            await pg.evaluate("bkSend({name:'Subida de prueba',ll:LL,grade:.25})")
        bp=await pinfo.value;bp.on('pageerror',lambda e:berrs.append(str(e)))
        last=await pg.evaluate("BK.last");print('   Rumbo:',{k:(round(v,3) if isinstance(v,float) else v) for k,v in last.items() if k!='scenes'})
        for x in last['scenes']:print('     km %5.2f %-8s agua:%s %s'%(x['km'],x['scene'],x['water'],x['waterKind'] if x['water'] else ''))
        ok(abs(last['L']-6000)<300,'largo de la ruta (el ruido de ±3 m del GPS de prueba lo alarga un poco)')
        ok(last['gm']<=0.251,'pendiente máxima respetada (relieve con lomas de ±8 m): %.1f %%'%(last['gm']*100))
        sc=last['scenes'];kinds=[x['scene'] for x in sc]
        ok(any(x['water'] and x['waterKind']=='mar' for x in sc),'costa detectada')
        ok('urbana' in kinds and 'bosque' in kinds and 'cornisa' in kinds,'ciudad, bosque y cornisa en su lugar')
        ok(last['len']<120000,'link de %d caracteres'%last['len'])
        ok(last['hz'] and last['peaks']==2 and last['ground'],'montañas reales (%d puntos), cerros y colores del suelo'%last['hzN'])
        await bp.wait_for_load_state();await bp.wait_for_timeout(1500)
        st=await bp.evaluate("""({h:location.hash,mode:$('modeSel').value,fname,total:Math.round(total),saved:!!loadRoutesMap()[fname],sc:(loadScenes()[fname]||[]).length,sm:$('smoothM').value,info:$('routeinfo').textContent,log:$('log')?$('log').innerText.slice(0,400):''})""")
        print('   Bici:',{k:v for k,v in st.items() if k!='log'});print('   log:',st['log'].replace('\n',' | ')[:300])
        ok(st['mode']=='gpx' and st['saved'] and st['total']>5800,'Bici: ruta guardada y cargada en modo Recorrido')
        ok(st['sc']==len(sc),'Bici: escenario guardado con %d tramos'%st['sc'])
        ok(st['sm']=='20','Bici: suavizado 20 m para esta ruta')
        ok(st['h']=='','Bici: el link se limpia')
        # volver a una ruta común restituye tu suavizado
        await bp.evaluate("""()=>{fname='otra.gpx';parseGpx('<gpx><trk><trkseg>'+Array.from({length:50},(_,i)=>`<trkpt lat="-26.8" lon="${-65.2-i*0.0005}"><ele>${500+i}</ele></trkpt>`).join('')+'</trkseg></trk></gpx>')}""")
        ok(await bp.evaluate("$('smoothM').value")=='100','Bici: con una ruta común vuelve tu suavizado (100 m)')
        await bp.evaluate("renderRoutesList()")
        ok(await bp.evaluate("[...document.querySelectorAll('#routesList button')].some(b=>b.textContent.includes('Usar'))"),'Bici: botón ▶ Usar en Rutas guardadas')
        await bp.evaluate("[...document.querySelectorAll('#routesList .srow')].find(r=>r.textContent.includes('Subida')).querySelector('button').click()")
        ok(await bp.evaluate("fname==='Subida de prueba.gpx'&&$('smoothM').value==='20'"),'Bici: ▶ Usar carga la ruta de Rumbo con su suavizado')
        # vista del camino en Bici a los 4 km, mirando hacia el cerro grande (al norte)
        r=await bp.evaluate("""()=>{const c=document.createElement('canvas');c.width=412;c.height=240;document.body.appendChild(c);c.id='tst';const x=c.getContext('2d');
          const rt={pts:points,dist};let used=0,lab=[];const o1=drawRealHorizon;drawRealHorizon=function(){used++;return o1.apply(this,arguments)};
          const ft=x.fillText.bind(x);x.fillText=(t,a,b)=>{lab.push(t);ft(t,a,b)};
          const ps=posAtDistance(rt,4000),pk=routeExtra(fname).peaks[0],tb=Math.atan2((pk.lo-ps.lon)*Math.cos(ps.lat*Math.PI/180),pk.la-ps.lat);roadBands(x,412,240,4000,()=>tb,dd=>eleRoute(rt,dd),fname);
          const gs=groundSides(routeExtra(fname),3000,sceneAt(fname,3000));
          return {used,lab,gs,cam:bearingRoute(rt,3000)*180/Math.PI};}""")
        print('   Bici a los 3 km:',r)
        print('   dbg:',await bp.evaluate("""(()=>{const rx=routeExtra(fname),rt={pts:points,dist},pos=posAtDistance(rt,4000),p=rx.peaks[0],camB=Math.atan2((p.lo-pos.lon)*Math.cos(pos.lat*Math.PI/180),p.la-pos.lat),kc=Math.cos(pos.lat*Math.PI/180);
          const dy=(p.la-pos.lat)*111320,dx=(p.lo-pos.lon)*111320*kc,DD=Math.hypot(dx,dy);let rel=Math.atan2(dx,dy)-camB;rel=Math.atan2(Math.sin(rel),Math.cos(rel));const camE=eleRoute(rt,4000);
          const ang=Math.atan((p.e-camE-1.6)/DD)*180/Math.PI,v=hzSample(rx.hz,4000,camB+rel);return {n:rx.peaks.length,DD,rel,ang,v,camE,geo:!!rx.geo};})()"""))
        ok(r['used']>0,'Bici dibuja el horizonte real')
        ok(any('Cerro Prueba' in l for l in r['lab']) and not any('Escondido' in l for l in r['lab']),'muestra el cerro que se ve y no el que queda tapado')
        el=await bp.query_selector('#tst');await el.screenshot(path=BUILD+'/bk_hz.png')
        wh=await bp.evaluate("""()=>{const rx=routeExtra(fname);rx.hz.snow=1500;const c=$('tst'),x=c.getContext('2d'),rt={pts:points,dist};const ps=posAtDistance(rt,4000),pk=rx.peaks[0],tb=Math.atan2((pk.lo-ps.lon)*Math.cos(ps.lat*Math.PI/180),pk.la-ps.lat);
          roadBands(x,412,240,4000,()=>tb,dd=>eleRoute(rt,dd),fname);const d=x.getImageData(0,0,412,120).data;let n=0;for(let i=0;i<d.length;i+=4)if(d[i]===238&&d[i+1]===243&&d[i+2]===247)n++;return n;}""")
        ok(wh>200,'nieve en las cumbres por encima de la cota (%d píxeles)'%wh)
        await el.screenshot(path=BUILD+'/bk_snow.png')
        await bp.evaluate("openSceneEditor('Subida de prueba.gpx',total,'routes')");await bp.wait_for_timeout(800)
        await bp.evaluate("sceneScrubKm=0.5;drawScenePreview()");await bp.wait_for_timeout(300)
        el=await bp.query_selector('#sceneCard');await el.screenshot(path=BUILD+'/bk_scene.png')
        print('   editor:',await bp.evaluate("$('scenePrevInfo').textContent"))
        # v167: costados reales (casas, calle, campo, sendero)
        ld=await bp.evaluate("""(()=>{const rx=routeExtra(fname);if(!rx||!rx.land)return null;const L=rx.land;return [1000,2500,4800].map(d=>{const m=landEn(L,d);return {c:m.c,b:m.b,via:m.v&15,ancho:+landAncho(L,d,5.2).toFixed(1)};});})()""")
        print('   Bici, costados:',ld)
        ok(ld and ld[0]['c'][1]==1 and ld[0]['b'][1]>0 and ld[1]['c']==[5,5] and ld[1]['via']==5 and ld[2]['via']==6,'Bici recibe los costados del camino (casas, campo, sendero)')
        import base64
        for km in (1.0,2.5,4.8):
            du=await bp.evaluate("""(km=>{const c=document.createElement('canvas');c.width=412;c.height=300;const x=c.getContext('2d'),rt={pts:points,dist},d=km*1000;
              roadBands(x,412,300,d,dd=>bearingRoute(rt,dd),dd=>eleRoute(rt,dd),fname);return c.toDataURL('image/png');})""",km)
            open(BUILD+'/bk_land_%s.png'%str(km).replace('.','_'),'wb').write(base64.b64decode(du.split(',')[1]))
        # v168: viento real del recorrido (a mano: 30 km/h del oeste; el recorrido va al oeste → de frente)
        await bp.evaluate("wxBuscar=async()=>{};")
        r=await bp.evaluate("""(()=>{wxCfgSet({on:true,pct:100});WX=wxManual(30,270);mode='gpx';
          const rel=wxRelativo(WX,bearingAt(1000),0),still=0.5*RHO*0.32*8*8,con=wxAire_v(8,0.32,rel).F;
          const vuelta=wxRelativo(WX,bearingAt(1000)+Math.PI,0);
          state='riding';distanceM=1000;wxRelAhora=rel;fitRoad();road3d=true;
          const c=document.createElement('canvas');c.width=412;c.height=300;const x=c.getContext('2d');WX.lluvia=2;WX.nubes=80;
          let cielo=0;const o1=wxCielo;wxCielo=function(){cielo++;return o1.apply(this,arguments)};
          roadBands(x,412,300,2500,dd=>bearingRoute({pts:points,dist},dd),dd=>eleRoute({pts:points,dist},dd),fname);wxCielo=o1;
          wxAire(x,412,300,132,WX,rel,3,8);wxFlecha(x,376,36,WX,rel);
          state='idle';wxCfgSet({on:false});
          return {fr:rel.frente,vu:vuelta.frente,still,con,cielo,du:c.toDataURL('image/png')};})()""")
        open(BUILD+'/bk_viento.png','wb').write(base64.b64decode(r['du'].split(',')[1]))
        print('   viento:',{k:round(v,1) for k,v in r.items() if k!='du'})
        ok(r['fr']>5 and r['vu']<-5,'viento del oeste yendo al oeste: de frente; a la vuelta, de cola')
        ok(r['con']>r['still']*2,'con viento de frente el aire frena mucho más (%.0f N vs %.0f N)'%(r['con'],r['still']))
        ok(r['cielo']>=1,'la vista 3D dibuja el cielo con el clima')
        print('ERRORES JS Rumbo:',errs[:3] or 'ninguno',' · Bici:',berrs[:3] or 'ninguno');ok(not errs and not berrs,'sin errores');await b.close()
    srv.shutdown()
asyncio.run(main())
