import asyncio,http.server,threading,functools,os,sys
from playwright.async_api import async_playwright
from apps import otra_app
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
KY=otra_app('RUMBO_KAYAK','https://profehugotdf.github.io/Kayak-Indoor-/')
if KY is None:print('SALTEADA: no hay Kayak Indoor para probar');sys.exit(77)
os.makedirs(os.path.join(BUILD,'ky'),exist_ok=True);open(os.path.join(BUILD,'ky','index.html'),'wb').write(KY)
SP=SITE
KP=os.path.join(BUILD,'ky')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
STUB=r"""
window.__terr=(la,lo)=>{const dn=(la+54.85)*111320+Math.sin((lo+68.4)*60)*120;   // canal que serpentea
  let h=dn>300?8+(dn-300)*0.06:dn<-150?20+(-150-dn)*0.12:-1;
  const g=(a,b,H,s)=>{const dy=(la-a)*111320,dx=(lo-b)*111320*0.575;return H*Math.exp(-(dx*dx+dy*dy)/(2*s*s));};
  h+=g(-54.80,-68.36,1100,1800)+g(-54.91,-68.33,900,1500)+g(-54.76,-68.25,1300,2500);
  h+=g(-54.852,-68.215,1200,1500)+g(-54.8455,-68.375,180,250)+g(-54.8535,-68.345,120,200);
  return dn<=300&&dn>=-150&&lo<-68.285?0:h;};
fetchDemList=async(list,z)=>{const m=new Map(),n=2**z;for(const t of list){const a=new Float32Array(65536);
  for(let py=0;py<256;py++){const yy=(t.y+(py+.5)/256)/n,la=Math.atan(Math.sinh(Math.PI*(1-2*yy)))*180/Math.PI;for(let px=0;px<256;px++){const lo=(t.x+(px+.5)/256)/n*360-180;a[py*256+px]=__terr(la,lo);}}
  m.set(t.x+'/'+t.y,a);}return m;};
demMissing=async()=>0;
coastSea=async()=>null;   // sin red: la costa real de OpenStreetMap no combina con este canal inventado (en CI hay internet)
bkPeaks=async()=>[{n:'Cerro Uno',e:1100,la:-54.80,lo:-68.36},{n:'Monte Tres',e:1300,la:-54.76,lo:-68.25}];
satAvg=async(groups)=>groups.map((g,i)=>[60+(i%3)*5,95,55]);
window.confirm=()=>true;
HTMLAnchorElement.prototype.click=function(){window.__href=this.href;};
"""
async def main():
    s1=http.server.ThreadingHTTPServer(('127.0.0.1',8792),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=s1.serve_forever,daemon=True).start()
    s2=http.server.ThreadingHTTPServer(('127.0.0.1',8793),functools.partial(http.server.SimpleHTTPRequestHandler,directory=KP));threading.Thread(target=s2.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append('rumbo: '+str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8792/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate(STUB)
        await pg.evaluate("""async()=>{const ll=[];for(let i=0;i<=200;i++){const lo=-68.40+i*0.0005;ll.push([-54.85-Math.sin((lo+68.4)*60)*120/111320+75/111320,lo]);}
          await kySend({name:'Canal de prueba',ll});}""")
        await pg.wait_for_function('!!window.__href',timeout=120000)
        print('   ',await pg.evaluate("JSON.stringify(KY.last)"))
        last=await pg.evaluate("KY.last")
        ok(last['hz'] and last['peaks']==2,'manda montañas y cerros')
        ok(last['shoreL']>0.9 and last['shoreR']>0.9,'encuentra orillas a los dos lados')
        href=await pg.evaluate("window.__href");ok(href.startswith('https://profehugotdf.github.io/Kayak-Indoor-/#rumbo=z'),'abre Kayak Indoor (%d KB)'%(len(href)//1024))
        # chequeo de las distancias de orilla: ~225 m izq (norte) y ~75 m der
        sh=await pg.evaluate("""()=>{const m=window.__href.match(/#rumbo=z(.*)/);return m[1].length}""")
        await pg.close()
        # Kayak Indoor
        kp=await b.new_page(viewport={'width':412,'height':860});kp.on('pageerror',lambda e:errs.append('kayak: '+str(e)))
        await kp.goto('http://127.0.0.1:8793/index.html'+href[href.index('#'):]);await kp.wait_for_timeout(1500)
        r=await kp.evaluate("rutaActiva&&{n:rutaActiva.nombre,L:rutaActiva.L,hz:!!rutaActiva.hz,sh:!!rutaActiva.sh,o:orillaEn(rutaActiva,100,1),o2:orillaEn(rutaActiva,100,-1)}");print('   ',r)
        ok(r and r['n']=='Canal de prueba' and r['hz'] and r['sh'],'Kayak Indoor guarda y elige el recorrido')
        ok(150<r['o']['d']<300 and 150<r['o2']['d']<300,'orillas: izquierda %d m, derecha %d m'%(r['o']['d'],r['o2']['d']))
        t=await kp.inner_text('#cardRuta');ok('km' in t and 'montañas reales' in t,'tarjeta Recorrido')
        await kp.evaluate("document.getElementById('canvasSesionVivo').scrollIntoView()")
        for i,dd in enumerate([0,1800,4200]):
            await kp.evaluate(f"moverPreviewRuta({dd})");await kp.wait_for_timeout(100)
            import base64
            du=await kp.evaluate("document.getElementById('canvasSesionVivo').toDataURL('image/png')")
            open(os.path.join(BUILD,f'ky_{i}.png'),'wb').write(base64.b64decode(du.split(',')[1]))
        # sesión simulada: la distancia remada mueve la cámara
        await kp.evaluate("iniciarSesion&&0")
        await kp.evaluate("togglePlayRuta()");await kp.wait_for_timeout(700);d=await kp.evaluate("rutaPreviewD");await kp.evaluate("togglePlayRuta()");ok(d>5,'▶ Recorrer sin remar avanza (%d m)'%d)
        # recargar: sigue elegida
        await kp.reload();await kp.wait_for_timeout(1200);ok(await kp.evaluate("rutaActiva&&rutaActiva.nombre")=='Canal de prueba','queda guardada al recargar')
        # v111: viento y clima reales (a mano, sin internet en la prueba)
        r=await kp.evaluate("""(()=>{wxBuscar=async()=>{};document.getElementById('wxManV').value='35';document.getElementById('wxManD').value='90';wxManualUsar();
          WX.lluvia=1.5;WX.nubes=85;let n=0,e=0;const o1=wxCielo,o2=wxEspuma;wxCielo=function(){n++;return o1.apply(this,arguments)};wxEspuma=function(){e++;return o2.apply(this,arguments)};
          rutaPreviewD=600;renderSesionVivo();wxCielo=o1;wxEspuma=o2;
          const vf=velConViento(3.5,6,1.225),vc=velConViento(3.5,-6,1.225);
          return {n,e,info:document.getElementById('wxInfo').textContent,vf,vc,du:document.getElementById('canvasSesionVivo').toDataURL('image/png')};})()""")
        import base64;open(BUILD+'/ky_viento.png','wb').write(base64.b64decode(r['du'].split(',')[1]))
        print('   viento:',r['info'][:90],'· v de frente %.2f, de cola %.2f m/s'%(r['vf'],r['vc']))
        ok(r['n']==1 and r['e']==1 and '35 km/h del este' in r['info'],'kayak: el viento puesto a mano se ve (cielo, espuma) y se anota')
        ok(r['vf']<3.1 and r['vc']>3.5,'kayak: con la misma remada, de frente se avanza menos y de cola más')
        await kp.evaluate("wxGuardarCfg({on:false})")
        # v110: carrera virtual sobre el recorrido
        r=await kp.evaluate("""(async()=>{const P=v=>Array.from({length:61},(_,i)=>({t:i*10,distAcum:i*10*v,cadencia:60,pulso:140}));
          carreraCorredores=[{sesion:{puntos:P(2.2),duracionSeg:600,fecha:new Date().toISOString()},fase:0,color:'#E8B84B'},{sesion:{puntos:P(2.0),duracionSeg:600,fecha:new Date().toISOString()},fase:0,color:'#3d7ec9'}];
          carreraDuracionMax=600;carreraT=300;carreraCamaraIdx=0;rutaCarrera=rutaActiva;cambiarTab('carrera');await poblarRutasCarrera();await new Promise(r=>setTimeout(r,200));
          let n=0;const o1=dibujarEscenaRuta;dibujarEscenaRuta=function(){n++;return o1.apply(this,arguments)};renderCarrera();dibujarEscenaRuta=o1;
          const opts=[...document.getElementById('selRutaCarrera').options].map(o=>o.textContent);
          const du=document.getElementById('canvasCarrera').toDataURL('image/png');
          return {n,opts,du,ok:rutaActiva&&rutaActiva.nombre};})()""")
        import base64;open(BUILD+'/ky_carrera.png','wb').write(base64.b64decode(r['du'].split(',')[1]))
        ok(r['n']==1 and any('Canal de prueba' in x for x in r['opts']),'carrera virtual: se puede correr sobre el recorrido')
        await kp.evaluate("elegirRutaCarrera('')");ok(await kp.evaluate("rutaCarrera===null&&rutaActiva&&rutaActiva.nombre==='Canal de prueba'"),'carrera virtual: volver al lago sin tocar el recorrido de la sesión')
        await kp.evaluate("elegirRuta('')");await kp.wait_for_timeout(300);ok(await kp.evaluate("rutaActiva")is None,'volver al lago de siempre')
        print('ERRORES JS:',errs[:3] or 'ninguno');ok(not errs,'sin errores')
        await b.close()
    s1.shutdown();s2.shutdown()
asyncio.run(main())
