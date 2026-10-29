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
bkPeaks=async()=>[{n:'Cerro Uno',e:1100,la:-54.80,lo:-68.36},{n:'Monte Tres',e:1300,la:-54.76,lo:-68.25}];
satAvg=async(groups)=>groups.map((g,i)=>[60+(i%3)*5,95,55]);
window.confirm=()=>true;
HTMLAnchorElement.prototype.click=function(){window.__href=this.href;};
"""

STUB2=r"""
window.__bkOverCalls=0;
bkOver=async(q)=>{if(!String(q).includes('man_made"="pier'))return [];window.__bkOverCalls++;window.__q=q;
  // pilote de OSM al norte de la ruta, puente que la cruza, y un "puente" a 3 km (debe quedar afuera)
  const g=(a)=>a.map(p=>({lat:p[0],lon:p[1]}));
  return [
   {type:'way',id:11,tags:{man_made:'pier',name:'Muelle OSM'},geometry:g([[-54.8490,-68.3600],[-54.8494,-68.3600]])},
   {type:'way',id:12,tags:{bridge:'yes',highway:'primary',name:'Puente OSM'},geometry:g([[-54.8480,-68.3500],[-54.8520,-68.3500]])},
   {type:'way',id:13,tags:{tunnel:'culvert'},geometry:g([[-54.8480,-68.3400],[-54.8481,-68.3400]])},
   {type:'way',id:14,tags:{embankment:'yes',highway:'trunk'},geometry:g([[-54.8470,-68.3300],[-54.8470,-68.3250]])},
   {type:'way',id:15,tags:{bridge:'yes'},geometry:g([[-54.7800,-68.3500],[-54.7810,-68.3500]])}];};
"""
def_ok=0
async def main():
    s1=http.server.ThreadingHTTPServer(('127.0.0.1',8794),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SP));threading.Thread(target=s1.serve_forever,daemon=True).start()
    s2=http.server.ThreadingHTTPServer(('127.0.0.1',8795),functools.partial(http.server.SimpleHTTPRequestHandler,directory=KP));threading.Thread(target=s2.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append('rumbo: '+str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8794/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate(STUB);await pg.evaluate(STUB2)
        # lógica pura
        r=await pg.evaluate("""()=>{const o=elFromOsm([{type:'way',id:1,tags:{bridge:'yes',tunnel:'building_passage'},geometry:[{lat:0,lon:0},{lat:0,lon:1}]},{type:'way',id:2,tags:{tunnel:'culvert'},geometry:[{lat:0,lon:0},{lat:0,lon:1}]},{type:'way',id:3,tags:{cutting:'yes'},geometry:[{lat:0,lon:0},{lat:0,lon:1}]},{type:'way',id:4,tags:{highway:'residential'},geometry:[{lat:0,lon:0},{lat:0,lon:1}]}]);
          const man=[{k:'puente',pts:[[0,0],[0,0.0001]],man:1}],osm=[{k:'puente',pts:[[0,0.0001],[0,0.0002]]},{k:'puente',pts:[[1,1],[1,1.1]]},{k:'muelle',pts:[[0,0],[0,0.0001]]}];
          const pts=Array.from({length:500},(_,i)=>[i*1e-4,Math.sin(i/5)*1e-4]);
          return {k:o.map(e=>e.k).join(','),m:elMerge(man,osm).map(e=>e.k+(e.man?'*':'')).join(','),s:elSimplify(pts,40).length,r:elResumen([{k:'puente'},{k:'puente'},{k:'tunel'},{k:'terraplen'}])};}""")
        print('   ',r)
        ok(r['k']=='puente,tunel,desmonte','OSM: puente, túnel y desmonte; el alcantarillado y las calles comunes no')
        ok(r['m']=='puente*,puente,muelle','lo marcado a mano manda sobre OSM a menos de 40 m')
        ok(r['s']<=40,'simplifica a 40 puntos como máximo')
        ok(r['r']=='2 puentes, 1 túnel, 1 terraplén','resumen en castellano')
        # lo marcado a mano con Calcar (terraplén con altura propia, y un desmonte)
        await pg.evaluate("""async()=>{await DB.put('kv','edit:t1',{id:'t1',type:'path',kind:'terraplen',name:'Terraplén mío',pts:[[-54.8475,-68.3200],[-54.8475,-68.3150]],props:{alto:6}});
          await DB.put('kv','edit:t2',{id:'t2',type:'path',kind:'muelle',name:'',pts:[[-54.9,-60.0],[-54.9,-60.001]],props:{}});}""")
        await pg.evaluate("""async()=>{const ll=[];for(let i=0;i<=200;i++){const lo=-68.40+i*0.0005;ll.push([-54.85-Math.sin((lo+68.4)*60)*120/111320+75/111320,lo]);}
          await kySend({name:'Canal de prueba',ll});}""")
        await pg.wait_for_function('!!window.__href',timeout=120000)
        last=await pg.evaluate("KY.last");print('   ',last)
        ok(await pg.evaluate("__bkOverCalls")==1,'pide a OpenStreetMap una sola vez')
        ok(last['elems']=={'muelle':1,'puente':1,'terraplen':2,'tunel':0} or last['elems']=={'muelle':1,'puente':1,'terraplen':2},'manda: muelle, puente OSM y 2 terraplenes (OSM + mano); lo lejano y lo de otro lado quedan afuera: %s'%last['elems'])
        href=await pg.evaluate("window.__href");await pg.close()
        kp=await b.new_page(viewport={'width':412,'height':860});kp.on('pageerror',lambda e:errs.append('kayak: '+str(e)))
        await kp.goto('http://127.0.0.1:8795/index.html'+href[href.index('#'):]);await kp.wait_for_timeout(1500)
        r=await kp.evaluate("rutaActiva&&{n:rutaActiva.nombre,e:(rutaActiva.elemsRaw||[]).map(e=>e.k+':'+(e.man?'m':'o')+':'+e.a)}");print('   ',r)
        ok(r and sorted(r['e'])==sorted(['muelle:o:null','puente:o:null','terraplen:o:null','terraplen:m:6']),'Kayak recibe los elementos con su altura y su origen')
        t=await kp.inner_text('#cardRuta');ok('puente' in t and 'terrapl' in t,'tarjeta Recorrido los menciona')
        print('ERRORES JS:',errs[:3] or 'ninguno');ok(not errs,'sin errores')
        await b.close()
    s1.shutdown();s2.shutdown()
asyncio.run(main())
