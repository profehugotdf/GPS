import asyncio,http.server,threading,functools,os,sys
from playwright.async_api import async_playwright
SITE=os.environ.get('RUMBO_SITE','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    s1=http.server.ThreadingHTTPServer(('127.0.0.1',8797),functools.partial(http.server.SimpleHTTPRequestHandler,directory=SITE));threading.Thread(target=s1.serve_forever,daemon=True).start()
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':412,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script("navigator.geolocation.watchPosition=(ok)=>{window.__ok=ok;return 1};navigator.geolocation.clearWatch=()=>{};")
        await pg.goto('http://127.0.0.1:8797/index.html');await pg.wait_for_function('!!window.__ok')
        r=await pg.evaluate("""async()=>{
          const la=-54.80,lo=-68.30,K=111320,kc=Math.cos(la*Math.PI/180);
          // rectángulo de 20 × 8 m con el lado largo orientado a 30° del norte
          const a=30*Math.PI/180,u=[Math.sin(a),Math.cos(a)],v=[Math.cos(a),-Math.sin(a)];
          const pt=(s,t)=>[la+(u[1]*s+v[1]*t)/K,lo+(u[0]*s+v[0]*t)/(K*kc)];
          const poly=[pt(-10,-4),pt(10,-4),pt(10,4),pt(-10,4),pt(-10,-4)];
          const g=p=>p.map(q=>({lat:q[0],lon:q[1]}));
          const els=[{type:'way',geometry:g(poly),tags:{building:'house',height:'7,5'}},
            {type:'way',geometry:g(poly),tags:{building:'apartments','building:levels':'5'}},
            {type:'way',geometry:g(poly),tags:{building:'church'}},
            {type:'way',geometry:g(poly),tags:{building:'yes'}},
            {type:'way',geometry:g([[la,lo],[la+1e-5,lo],[la+1e-5,lo+1e-5],[la,lo]]),tags:{building:'shed'}},   // de menos de 20 m²
            {type:'relation',tags:{building:'yes'}}];
          const out=edifFromOsm(els);
          // bkOver simulado: una consulta
          let q=null;bkOver=async(s)=>{q=s;return els.slice(0,2).map(e=>Object.assign({},e));};
          const P=[[la,lo+.01,0],[la,lo+.011,100]];const c=await edifCollect(P);
          return {out,q:q&&q.includes('way["building"]'),c:{n:c.list.length,real:c.real,err:c.err},rect:edifRect(poly)};}""")
        print('   ',r)
        o=r['out']
        ok(len(o)==4,'4 edificios (el de menos de 20 m² y la relación no entran): %d'%len(o))
        ok(o[0][0]==7.5 and o[0][1]==1,'height manda (con coma): 7,5 real')
        ok(o[1][0]==16 and o[1][1]==1,'building:levels = 5 pisos → 16 m real')
        ok(o[2][0]==12 and o[2][1]==0 and o[3][0]==6 and o[3][1]==0,'sin altura: típica del tipo, marcada como estimada')
        rc=r['rect'];ok(abs(rc['w']-20)<.6 and abs(rc['d']-8)<.6,'rectángulo orientado 20 × 8 m: %.1f × %.1f'%(rc['w'],rc['d']))
        ok(abs(rc['ang']-30)<=3,'el lado largo está a 30° del norte: %s'%rc['ang'])
        ok(r['q'] and r['c']['n']==2 and r['c']['real']==2 and not r['c']['err'],'edifCollect: arma la consulta y devuelve los 2 de la zona: %s'%r['c'])
        ok(not errs,'sin errores JS: %s'%errs[:2])
        await b.close()
    s1.shutdown()
asyncio.run(main())
