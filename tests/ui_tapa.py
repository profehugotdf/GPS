# 🧢 "Tapa": la tierra de frente a la punta del recorrido de kayak (Hugo, 9-nov, Zihuatanejo: llegando a la playa no había costa adelante
# y el muelle parecía estar en medio del agua). Y que una respuesta vacía de un servidor de OpenStreetMap no se tome por "no hay edificios".
import asyncio,http.server,threading,functools,os,sys,base64
from playwright.async_api import async_playwright
from apps import otra_app
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
KY=otra_app('RUMBO_KAYAK','https://profehugotdf.github.io/Kayak-Indoor-/')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
# bahía: mar al sur, playa recta este-oeste a 17.6400 (tierra al norte, sube de a poco). La ruta va hacia el norte y termina 120 m antes de la playa.
STUB=r"""
window.__terr=(la,lo)=>{const dn=(la-17.6400)*111320;return dn>0?4+dn*0.05:0;};
fetchDemList=async(list,z)=>{const m=new Map(),n=2**z;for(const t of list){const a=new Float32Array(65536);
  for(let py=0;py<256;py++){const yy=(t.y+(py+.5)/256)/n,la=Math.atan(Math.sinh(Math.PI*(1-2*yy)))*180/Math.PI;for(let px=0;px<256;px++){const lo=(t.x+(px+.5)/256)/n*360-180;a[py*256+px]=__terr(la,lo);}}
  m.set(t.x+'/'+t.y,a);}return m;};
demMissing=async()=>0;coastSea=async()=>null;bkPeaks=async()=>[];
satAvg=async(groups)=>groups.map(()=>[150,140,110]);
window.confirm=()=>true;HTMLAnchorElement.prototype.click=function(){window.__href=this.href;};
"""
async def main():
    s1=http.server.ThreadingHTTPServer(('127.0.0.1',8811),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=s1.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append('rumbo: '+str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8811/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate(STUB)
        # 1) bkOverPar: el servidor que contesta primero y vacío no gana
        r=await pg.evaluate("""async()=>{const f0=window.fetch;let n=0;
          const resp=(els,ms,extra)=>new Promise(z=>setTimeout(()=>z({ok:true,status:200,json:async()=>Object.assign({elements:els},extra||{})}),ms));
          window.fetch=(url)=>{n++;return url.includes('overpass-api.de')?resp([],10):url.includes('kumi')?resp([{type:'way',id:1}],120):resp([],30,{remark:'runtime error: algo raro'});};
          const a=await bkOverPar('x',5000,true),a0=await bkOverPar('x',5000);
          window.fetch=(url)=>resp([],10);const v=await bkOverPar('x',5000,true),vac=bkOverPar.vacio;
          window.fetch=f0;return {a:a.length,a0:a0.length,v:v.length,vac};}""")
        print('   ',r)
        ok(r['a']==1,'con "lleno", gana el servidor que trae datos aunque otro conteste antes vacío')
        ok(r['a0']==0,'sin "lleno" sigue como antes (la costa: vacío es una respuesta válida)')
        ok(r['v']==0 and r['vac']==3,'si los tres contestan vacío, devuelve [] y dice cuántos (%s)'%r['vac'])
        # 2) edificios y calles: primer intento vacío → segundo intento por rectángulo; y el motivo cuando no hay nada
        r=await pg.evaluate("""async()=>{const P=[[17.630,-101.555,0],[17.6389,-101.555,990]];const qs=[];
          const g=a=>a.map(q=>({lat:q[0],lon:q[1]})),casa=[[17.6405,-101.555],[17.6405,-101.5549],[17.6406,-101.5549],[17.6406,-101.555],[17.6405,-101.555]];
          const o=bkOverPar,visto={};bkOverPar=async(q)=>{qs.push(q);const tipo=q.includes('building')?'b':'h',pri=!visto[tipo];visto[tipo]=1;bkOverPar.vacio=pri?1:0;return pri?[]:q.includes('building')?[{type:'way',geometry:g(casa),tags:{building:'yes'}}]:[{type:'way',geometry:g([[17.6402,-101.556],[17.6402,-101.554]]),tags:{highway:'primary'}}];};
          const e=await edifCollect(P),c=await callesCollect(P);
          bkOverPar=async()=>{bkOverPar.vacio=2;return [];};const e2=await edifCollect(P),c2=await callesCollect(P);
          bkOverPar=async()=>{bkOverPar.vacio=0;bkOverPar.dijo='api.de: no respondió a tiempo · kumi.systems: HTTP 504';throw new Error('x');};const e3=await edifCollect(P);
          bkOverPar=o;return {e:e.list.length,c:c.list.length,nq:qs.length,e2:e2.err,c2:c2.err,e3:e3.err,q0:qs[0]};}""")
        print('   ',r)
        ok(r['e']==1 and r['c']==1 and r['nq']==4,'vacío al primer intento: se vuelve a preguntar de otra forma y llegan (edificios %d, calles %d)'%(r['e'],r['c']))
        ok('around' not in r['q0'] and 'building' in r['q0'],'edificios: el primer intento es por rectángulo (más rápido para el servidor)')
        ok('kumi.systems: HTTP 504' in r['e3'],'si fallan todos, el motivo dice qué contestó cada servidor: "%s"'%r['e3'])
        ok('2 de 3 servidores sin edificios' in r['e2'] and 'sin calles' in r['c2'],'motivo claro cuando no hay: "%s"'%r['e2'])
        # 3) la tapa
        r=await pg.evaluate("""()=>{const rays=kyTapa([17.6389,-101.555],0,0,(la,lo)=>__terr(la,lo),null);
          return {n:rays.length,centro:rays[10].d,lado:rays[0].d,prof:rays[10].prof,bytes:kyTapaBytes(rays,null).length};}""")
        print('   ',r)
        ok(r['n']==21 and r['bytes']==231,'21 rayos, 11 bytes cada uno')
        ok(100<r['centro']<150,'de frente, la playa a ~120 m: %s'%r['centro'])
        ok(r['lado'] is not None and r['lado']>r['centro']*3,'a 80° la playa queda mucho más lejos: %s'%r['lado'])
        ok(r['prof'][6]>r['prof'][1]>0,'perfil tierra adentro que sube: %s'%r['prof'])
        await pg.evaluate("""async()=>{edifCollect=async()=>({list:[[6,0,17.6405,-101.555,12,8,90]],err:'',real:0});const cs=[];for(let i=0;i<=16;i++){const lo=-101.562+i*0.000875;cs.push([2,[[17.6402,lo],[17.6490,lo]]]);}   // un pueblo: 17 calles norte-sur y 13 este-oeste, cada ~90 m
          for(let j=0;j<=12;j++){const la=17.6402+j*0.00073;cs.push([j?2:1,[[la,-101.562],[la,-101.548]]]);}
          cs.push([1,[[17.6345,-101.5575],[17.6345,-101.5525]]]);   // un puente o pasarela que CRUZA el recorrido a mitad de camino
          callesCollect=async()=>({list:cs,err:'',pts:62});
          const ll=[];for(let i=0;i<=40;i++)ll.push([17.630+i*(0.0089/40),-101.555]);await kySend({name:'Bahía de prueba',ll});}""")
        await pg.wait_for_function('!!window.__href',timeout=120000)
        href=await pg.evaluate("window.__href")
        pk=await pg.evaluate("""async()=>{const m=window.__href.match(/#rumbo=z(.*)/),u=Uint8Array.from(atob(m[1].replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
          const o=JSON.parse(await new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).text());return {t:o.tapa&&{n:o.tapa.n,az:o.tapa.fin.az,azi:o.tapa.ini.az,len:o.tapa.fin.d.length}};}""")
        print('   ',pk);ok(pk['t'] and pk['t']['n']==21 and abs(pk['t']['az'])<2 and abs(pk['t']['azi']-180)<2,'el paquete lleva la tapa del final (rumbo 0°) y la del principio (180°)')
        # circuito que cierra en esquina frente a la playa, con otra esquina a mitad de camino: tapas del cierre y de las esquinas
        await pg.evaluate("""async()=>{window.__href=null;const A=[17.6389,-101.555],B=[17.632,-101.555],C=[17.632,-101.561],ll=[],seg=(a,b)=>{for(let i=0;i<20;i++)ll.push([a[0]+(b[0]-a[0])*i/20,a[1]+(b[1]-a[1])*i/20]);};
          seg(A,C);seg(C,B);seg(B,A);ll.push(A);await kySend({name:'Circuito de prueba',ll});}""")
        await pg.wait_for_function('!!window.__href',timeout=120000)
        href2=await pg.evaluate("window.__href")
        pk=await pg.evaluate("""async()=>{const m=window.__href.match(/#rumbo=z(.*)/),u=Uint8Array.from(atob(m[1].replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
          const o=JSON.parse(await new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).text());return {loop:o.loop,fin:o.tapa&&o.tapa.fin&&o.tapa.fin.az,mas:o.tapa&&o.tapa.mas&&o.tapa.mas.length};}""")
        print('   ',pk);ok(pk['loop'] and pk['fin'] is not None and abs(pk['fin'])<3 and pk['mas']==4,'circuito: tapa del cierre (rumbo 0°, mirando a la playa) y 2 esquinas × ida y vuelta')
        await pg.close()
        if KY is None:print('  (sin Kayak Indoor: la parte del dibujo se saltea)')
        else:
            os.makedirs(os.path.join(BUILD,'kyt'),exist_ok=True);open(os.path.join(BUILD,'kyt','index.html'),'wb').write(KY)
            s2=http.server.ThreadingHTTPServer(('127.0.0.1',8812),functools.partial(http.server.SimpleHTTPRequestHandler,directory=os.path.join(BUILD,'kyt')));threading.Thread(target=s2.serve_forever,daemon=True).start()
            kp=await b.new_page(viewport={'width':412,'height':860});kp.on('pageerror',lambda e:errs.append('kayak: '+str(e)))
            await kp.goto('http://127.0.0.1:8812/index.html'+href[href.index('#'):]);await kp.wait_for_timeout(1500)
            r=await kp.evaluate("""()=>{const R=rutaActiva;if(!R||!R.tapas)return null;const e=R.xy[R.xy.length-1];
              const tierra=()=>{moverPreviewRuta(R.L-60);const c=document.getElementById('canvasSesionVivo'),x=c.getContext('2d'),w=c.width,h=c.height,d=x.getImageData(0,0,w,h).data;let n=0;
                for(let y=Math.round(h*0.12);y<Math.round(h*0.3);y++)for(let px=Math.round(w*0.35);px<Math.round(w*0.65);px++){const o=(y*w+px)*4;if(d[o]>d[o+2]+12&&d[o]>110)n++;}return n;};
              const con=tierra(),du=document.getElementById('canvasSesionVivo').toDataURL('image/png');const t=R.tapas;R.tapas=[];const sin=tierra();R.tapas=t;
              return {n:R.tapas.length,zA:tapaSueloZ(R,e[0],e[1]+300),zAgua:tapaSueloZ(R,e[0],e[1]+60),zAtras:tapaSueloZ(R,e[0]+5,e[1]-300)===null?elemSueloZ(R,e[0]+5,e[1]-300):-1,zElem:elemSueloZ(R,e[0],e[1]+300),con,sin,du,info:document.getElementById('infoRuta').textContent};}""")
            ok(r is not None,'Kayak Indoor recibe la ruta con tapas')
            open(os.path.join(BUILD,'ky_tapa.png'),'wb').write(base64.b64decode(r['du'].split(',')[1]));del r['du'];print('   ',r)
            ok(r['n']==2,'dos tapas (principio y final)')
            ok(r['zA']>5 and r['zAgua']==0 and r['zElem']==r['zA'],'altura del suelo de frente: %.1f m a 300 m, 0 en el agua; elemSueloZ la usa'%r['zA'])
            ok(r['con']>r['sin']+300,'llegando a la playa se ve tierra de frente (%d px de arena con tapa, %d sin)'%(r['con'],r['sin']))
            ok('tierra de frente' in r['info'],'la tarjeta Recorrido lo dice')
            # v140 de Kayak: las calles de lejos no forman una franja gris maciza sobre la línea del agua (Hugo, 9-nov)
            g=await kp.evaluate("""()=>{const R=rutaActiva;moverPreviewRuta(60);const c=document.getElementById('canvasSesionVivo'),x=c.getContext('2d'),w=c.width,h=c.height,d=x.getImageData(0,0,w,h).data;let filas=0;
              for(let y=Math.round(h*0.15);y<Math.round(h*0.4);y++){let n=0;for(let px=0;px<w;px++){const o=(y*w+px)*4;if(Math.abs(d[o]-d[o+1])<14&&Math.abs(d[o+1]-d[o+2])<14&&d[o]<125&&d[o]>50)n++;}if(n>w*0.5)filas++;}
              return {filas,calles:R.callesRaw.length,du:c.toDataURL('image/png')};}""")
            open(os.path.join(BUILD,'ky_tapa_calles.png'),'wb').write(base64.b64decode(g['du'].split(',')[1]))
            # al pasar por debajo de una calle que cruza el recorrido, el agua no se pinta entera de gris (captura de las 23:08)
            peor=await kp.evaluate("""()=>{const R=rutaActiva,c=document.getElementById('canvasSesionVivo'),x=c.getContext('2d');let peor=0;
              for(let d=470;d<=505;d+=1.5){moverPreviewRuta(d);const w=c.width,h=c.height,dt=x.getImageData(0,Math.round(h*0.45),w,Math.round(h*0.5)).data;let n=0;
                for(let o=0;o<dt.length;o+=4)if(Math.abs(dt[o]-dt[o+1])<10&&Math.abs(dt[o+1]-dt[o+2])<10&&dt[o]<110&&dt[o]>50)n++;peor=Math.max(peor,n/(dt.length/4));}
              return peor;}""")
            ok(peor<0.25,'pasando bajo una calle que cruza el recorrido el agua no queda gris (peor cuadro: %d %% gris)'%round(peor*100))
            ok(g['calles']==31 and g['filas']==0,'de lejos, las %d calles no pintan una franja gris de lado a lado (%d filas grises)'%(g['calles'],g['filas']))
        # el Kayak publicado puede ser todavía el anterior (se sube un minuto antes que Rumbo y GitHub Pages tarda): sin soporte de tapa.mas, esto se saltea
        if KY is not None and b'T.mas' not in KY:print('  (el Kayak Indoor que se bajó todavía no lee tapa.mas: se saltea)')
        if KY is not None and b'T.mas' in KY:
            k2=await b.new_page(viewport={'width':412,'height':860});k2.on('pageerror',lambda e:errs.append('kayak: '+str(e)))
            await k2.goto('http://127.0.0.1:8812/index.html'+href2[href2.index('#'):]);await k2.wait_for_timeout(1500)
            r=await k2.evaluate("rutaActiva&&{n:rutaActiva.tapas.length,info:document.getElementById('infoRuta').textContent}")
            ok(r and r['n']==6 and 'puntas y esquinas (6)' in r['info'],'Kayak lee las 6 tapas del circuito y lo dice')
        ok(not errs,'sin errores JS: %s'%errs[:2])
        await b.close()
    s1.shutdown()
asyncio.run(main())
