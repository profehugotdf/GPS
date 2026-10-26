import asyncio,re,http.server,threading,os,functools
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
SP=SITE
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
import sys
from apps import otra_app
CORRER=otra_app('RUMBO_CORRER','https://profehugotdf.github.io/Carrera-virtual/')
if CORRER is None:print('SALTEADA: no hay Correr para probar');sys.exit(77)
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8798),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[];berrs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();ctx=await b.new_context(viewport={'width':412,'height':860})
        await ctx.route('https://profehugotdf.github.io/Carrera-virtual/**',lambda r:r.fulfill(status=200,content_type='text/html',body=CORRER))
        pg=await ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8798/index.html');await pg.wait_for_function('!!window.__ok')
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
            // casas al norte (derecha, yendo al oeste) entre 0,8 y 1,5 km, a 20 m del eje; cada tanto un edificio de 6 pisos
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
            await pg.evaluate("bkSend({app:'correr',name:'Subida para correr',ll:LL,grade:.35})")
        cp=await pinfo.value;cp.on('pageerror',lambda e:berrs.append(str(e)))
        last=await pg.evaluate("BK.last");print('   Rumbo:',{k:(round(v,3) if isinstance(v,float) else v) for k,v in last.items() if k!='scenes'})
        ok(last['hz'] and last['peaks']==2 and last['ground'],'Rumbo manda montañas, cerros y suelo')
        await cp.wait_for_load_state();await cp.wait_for_timeout(2500)
        st=await cp.evaluate("""(()=>{const r=rutaActiva();return {h:location.hash,esc:escenarioActual,nombre:r&&r.nombre,L:r&&r.longitudM,p:!!(r&&r.paisaje&&r.paisaje.hz),sc:r&&r.paisaje&&r.paisaje.scenes&&r.paisaje.scenes.length,e:!!(r&&r.e)}})()""")
        print('   Correr:',st)
        ok(st['nombre']=='Subida para correr' and st['L']>5800 and st['e'],'Correr: recorrido guardado con la altura')
        ok(st['esc']=='ruta' and st['p'] and st['sc']>=3,'Correr: elegido como escenario, con paisaje y tramos')
        ok(st['h']=='','Correr: el link se limpia')
        ld=await cp.evaluate("""(()=>{const r=rutaActiva(),P=paisajeDe(r);if(!P||!P.land)return null;const L=P.land;
          return [1000,2500,4800].map(d=>{const m=landEn(L,d);return {c:m.c,b:m.b,dist:m.dist,via:m.v&15,unp:!!(m.v&16),ver:!!(m.v&128),ancho:+landAncho(L,d,5.2).toFixed(1)};});})()""")
        print('   costados (1 km, 2,5 km, 4,8 km):',ld)
        ok(ld is not None,'Correr recibe los costados del camino (land)')
        ok(ld[0]['c'][1]==1 and ld[0]['b'][1]>0 and 10<=ld[0]['dist'][1]<=30 and ld[0]['b'][0]==0,'a 1 km: barrio con casas a la derecha, a la distancia real')
        ok(ld[0]['via']==4 and ld[0]['ver'],'a 1 km: calle con vereda')
        ok(ld[1]['c']==[5,5] and ld[1]['via']==5 and ld[1]['unp'],'a 2,5 km: campo a los dos lados, huella de ripio')
        ok(ld[2]['c']==[7,7] and ld[2]['via']==6 and ld[2]['ancho']<1.5,'a 4,8 km: bosque y sendero angosto')
        for km in (1.0,2.5,4.8):
            du=await cp.evaluate("""(km=>{const c=document.createElement('canvas');c.width=412;c.height=300;const x=c.getContext('2d');const ruta=rutaActiva();const d=km*1000;
              roadBands(x,412,300,d,dd=>valorRuta(ruta.b,ruta.paso,dd),dd=>valorRuta(ruta.e,ruta.paso,dd),ruta,escenaRumboEn(ruta,d),null);return c.toDataURL('image/png');})""",km)
            import base64;open(BUILD+'/cr_land_%s.png'%str(km).replace('.','_'),'wb').write(base64.b64decode(du.split(',')[1]))
        ms=await cp.evaluate("""(()=>{const c=document.createElement('canvas');c.width=412;c.height=300;const x=c.getContext('2d');const ruta=rutaActiva();
          const t0=performance.now();for(let k=0;k<40;k++){const d=900+k*5;roadBands(x,412,300,d,dd=>valorRuta(ruta.b,ruta.paso,dd),dd=>valorRuta(ruta.e,ruta.paso,dd),ruta,escenaRumboEn(ruta,d),null);}return (performance.now()-t0)/40;})()""")
        print('   un cuadro en el barrio: %.1f ms'%ms);ok(ms<30,'dibujar el barrio no es lento (%.1f ms por cuadro)'%ms)
        r=await cp.evaluate("""(()=>{const c=document.createElement('canvas');c.width=412;c.height=240;c.id='tstc';document.body.appendChild(c);const x=c.getContext('2d');
          let used=0,lab=[];const o1=dibujarHorizonteReal;dibujarHorizonteReal=function(){used++;return o1.apply(this,arguments)};
          const ft=x.fillText.bind(x);x.fillText=(t,a,b)=>{lab.push(t);ft(t,a,b)};
          const ruta=rutaActiva(),P=paisajeDe(ruta),pk=P.peaks[0],pos=latLonEnRuta(ruta,4000),tb=Math.atan2((pk.lo-pos.lon)*Math.cos(pos.lat*Math.PI/180),pk.la-pos.lat);
          roadBands(x,412,240,4000,()=>tb,dd=>valorRuta(ruta.e,ruta.paso,dd),ruta,escenaRumboEn(ruta,4000),null);
          const kinds=[0.5,2,4.5].map(km=>escenaRumboEn(ruta,km*1000).label);
          const kk=[0.5,2,4.5];
          return {used,lab,kinds};})()""")
        print('   Correr a los 4 km:',r)
        ok(r['used']>0,'Correr dibuja el horizonte real')
        ok(any('Cerro Prueba' in l for l in r['lab']),'Correr muestra el cerro con nombre')
        ok(len(set(r['kinds']))>=2,'el escenario cambia por tramo: %s'%r['kinds'])
        import base64
        du=await cp.evaluate("document.getElementById('tstc').toDataURL('image/png')");open(BUILD+'/cr_hz.png','wb').write(base64.b64decode(du.split(',')[1]))
        print('ERRORES JS Rumbo:',errs[:3] or 'ninguno',' · Correr:',berrs[:3] or 'ninguno');ok(not errs and not berrs,'sin errores')
        await b.close()
    srv.shutdown()
asyncio.run(main())
