# Si OpenStreetMap no responde, el escenario para Bici/Correr igual trae los costados con las calles que Rumbo ya
# tiene guardadas (redes bajadas para calcular rutas), y un barrio de calles residenciales queda como "urbana".
# (Hugo: un recorrido por la ciudad llegaba a Correr con "1 tramo de escenario · sin los costados")
import asyncio,http.server,threading,functools,os
from playwright.async_api import async_playwright
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',8804),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=srv.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();ctx=await b.new_context(viewport={'width':412,'height':860})
        await ctx.route('https://profehugotdf.github.io/**',lambda r:r.fulfill(status=200,content_type='text/html',body='<html><body>app</body></html>'))
        pg=await ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};window.confirm=()=>true;")
        await pg.goto('http://127.0.0.1:8804/index.html');await pg.wait_for_function('!!window.__ok')
        await pg.evaluate("""async()=>{
          const lo=km=>-65.20-km*1000/(111320*Math.cos(26.83*Math.PI/180)),la=-26.83;
          fetchDemList=async(list,z)=>{const m=new Map();for(const t of list)m.set(t.x+'/'+t.y,new Float32Array(65536).fill(450));return m;};
          demMissing=async()=>0;bkPeaks=async()=>[];bkGround=async()=>null;
          bkOver=async()=>{throw new Error('HTTP 429 (overpass-api.de)')};
          // la calle por la que va el recorrido y las paralelas: todas residenciales asfaltadas
          const ways=[{id:1,t:{highway:'residential',name:'Calle'},n:[1,2],p:[la,lo(0),la,lo(2.2)]},{id:2,t:{highway:'residential'},n:[3,4],p:[la+0.001,lo(0),la+0.001,lo(2.2)]}];
          await DB.put('kv','net:tst',{id:'tst',bb:{s:la-0.02,n:la+0.02,w:-65.25,e:-65.15},date:Date.now(),ways,hz:[]});
          window.LL=Array.from({length:201},(_,i)=>[la,lo(i*0.01)]);
        }""")
        async with ctx.expect_page() as pinfo:
            await pg.evaluate("bkSend({app:'correr',name:'Barrio',ll:LL,grade:.35})")
        np=await pinfo.value;await np.wait_for_load_state()
        href=np.url;await np.close()
        o=await pg.evaluate("""async(h)=>{const m=h.match(/#rumbo=z(.*)/);const s=m[1].replace(/-/g,'+').replace(/_/g,'/'),u=Uint8Array.from(atob(s+'==='.slice((s.length+3)%4)),c=>c.charCodeAt(0));
          const txt=await new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).text();const o=JSON.parse(txt);
          const L=o.land,U=L?Uint8Array.from(atob(L.d.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0)):null;let calle=0;if(U)for(let q=0;q<L.n;q++)if((U[q*7+6]&15)===4)calle++;
          return {land:!!L,calle:L?calle/L.n:0,scenes:o.scenes.map(x=>x.scene),osm:o.osm};}""",href)
        print('   paquete:',o)
        ok(o['land'] and o['calle']>0.8,'sin OpenStreetMap, los costados salen de las calles guardadas (%d %% de calle)'%round(o['calle']*100))
        ok(all(s=='urbana' for s in o['scenes']),'el barrio de calles residenciales queda como urbano')
        ok('429' in o['osm'],'el paquete dice cómo respondió OpenStreetMap')
        print('ERRORES JS:',errs[:3] or 'ninguno');ok(not errs,'sin errores');await b.close()
    srv.shutdown()
asyncio.run(main())
