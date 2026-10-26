import asyncio
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':800});pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('file://'+BUILD+'/harness_live.html');ev=pg.evaluate
        # cuadrado de 250 m por lado: S1 sube, S2 plano, S3 baja, S4 plano
        await ev("""(()=>{
          const O=[-54.8,-68.3],k=1/(111195*Math.cos(54.8*rad)),la=1/111195;
          const C=[[0,0],[0,250],[250,250],[250,0]];window.SQ=C.map(([n,e])=>[O[0]+n*la,O[1]+e*k]);
          const brgs=[90,0,270,180];
          // puertas en la mitad de cada lado (al principio de cada sector)
          const gates=C.map(([n,e],i)=>{const [n2,e2]=C[(i+1)%4];return makeGate({c:[O[0]+(n+n2)/2*la,O[1]+(e+e2)/2*k],w:30,brg:brgs[i],dirOnly:true,role:i?'split':'startfinish'});});
          window.CIRC={id:'c1',name:'Cuadra',type:'closed',gates,terrain:{n:4,kind:['up','flat','down','flat'],man:[],info:[],shape:['straight','curvy','straight','curvy'],brg:[0,270,180,90]},secs:[{name:'Subida del club'},{name:'Zona de curvas',curr:'con'},{name:'Recta de la costa'},{}]};
          const ent={circ:CIRC};ent.base={hist:{time:200000,splits:[50000,100000,140000,200000]},sb:[48000,49000,39000,59000]};
          ent.gt=new GateTimer(CIRC,{onStart:()=>{SH.tmDirty=true;REC.lastEnt=ent},onGate:()=>{SH.tmDirty=true},onLap:()=>{REC.lastEnt=ent;SH.tmDirty=true}});
          REC.state='rec';REC.timers=[ent];REC.act='kayak';ent.wind={dir:0,spd:20};window.ENT=ent;
        })()""")
        await ev("RT.res=null;showShare()");await pg.fill('#shn','Hugo');await pg.dispatch_event('#shn','change')
        await pg.click('[data-act=go]');await pg.wait_for_function("SH.on&&STORE.length>=1")
        print('1) da 2 vueltas y media (más rápido en la subida, más lento en el llano)')
        await ev("""(async()=>{
          const pts=[];for(let i=0;i<4;i++){const a=SQ[i],b=SQ[(i+1)%4];for(let s=0;s<50;s++)pts.push([a[0]+(b[0]-a[0])*s/50,a[1]+(b[1]-a[1])*s/50,i]);}
          const v=[5.5,4.6,6.5,4.0]; // m/s por lado: subida rápida, llano lento
          let prev=null,j=0;
          for(let step=0;step<200*2.85;step++){
            const p=pts[step%200],lap=Math.floor((step+25)/200),fk=lap==0?1:lap==1?[1.08,0.95,1,0.97][p[2]]:[1.12,0.93,1.04,1][p[2]],dt=5/(v[p[2]]*fk)*1000;T.now+=dt;
            const q=[p[0],p[1],T.now];if(prev)ENT.gt.feed(prev,q);prev=q;
            const f={lat:p[0],lon:p[1],acc:5,t:T.now};lastFix=f;shTick(f);await new Promise(r=>setTimeout(r,1));
          }})()""")
        await pg.wait_for_function("!SH.sending")
        laps=await ev("ENT.gt.laps.map(l=>[l.n,l.time,l.splits])");print('   vueltas:',laps)
        ok(len(laps)==2,'2 vueltas cronometradas')
        ok(await ev("STORE.some(x=>x.len<3900)"),'mensajes chicos')
        h=await ev("f1Html(f1ModelRec(ENT),T.now)")
        await ev("document.body.insertAdjacentHTML('beforeend','<div id=hudt style=\"position:fixed;left:0;right:0;top:0;background:#fff;padding:8px 10px;font-family:system-ui\">'+f1Html(f1ModelRec(ENT),T.now)+'</div>')")
        print('   panel propio:',await ev("document.getElementById('hudt').innerText.replace(/\\n/g,' | ')"))
        print('1b) contra la vuelta anterior')
        await ev("S.f1Ref='prev'")
        hp=await ev("(()=>{const m=f1ModelRec(ENT),c=f1Calc(m,T.now);return [c.refK,c.ref.n,c.L.n,c.cells.filter(x=>x.d!=null).map(x=>Math.round(x.d)).join(',')]})()")
        print('   ',hp);ok(hp[0]=='prev' and hp[1]==2 and hp[2]==3,'compara la vuelta 3 en curso contra la 2')
        lap2=await ev("(()=>{const l=ENT.gt.laps[1];const s=lapSectors(l);return Math.round(s[0])})()")
        cur=await ev("(()=>{const c=ENT.gt.cur;return c.marks.length?Math.round(c.marks[0]-c.start):null})()")
        print('   s1 actual',cur,'s1 vuelta 2',lap2)
        ok(cur is None or abs(int(hp[3].split(',')[0])-(cur-lap2))<=1,'la diferencia del sector es contra el mismo sector de la vuelta anterior')
        ht=await ev("f1Html(f1ModelRec(ENT),T.now)");ok('vs vuelta 2' in ht and '<em' in ht,'el panel dice “vs vuelta 2” y muestra el +/− en cada sector')
        await ev("document.getElementById('hudt').innerHTML=f1Html(f1ModelRec(ENT),T.now)");await pg.screenshot(path='f1_prev.png',clip={'x':0,'y':0,'width':390,'height':160})
        await ev("S.f1Ref='best'")
        print('2) quien sigue')
        link=await ev("shLink()");tk=link.split('#seguir=')[1].split('.')
        await ev(f"folStart('{tk[0]}','{tk[1]}')");await pg.wait_for_function("FOL.pts.length>0&&FOL.tm")
        txt=await ev("$('#fol').innerText.replace(/\\n/g,' | ')");print('   panel:',txt)
        ok('Vuelta 3' in txt,'ve la vuelta en curso')
        ok('Viento en contra' in txt,'en kayak compara por viento (S1 rumbo norte con viento del norte = en contra)')
        ok('Zona de curvas' in txt or 'Recta de la costa' in txt,'muestra el nombre del sector')
        ok(await ev("folLayer.items.filter(x=>x.t==='line').length>=8"),'dibuja las puertas')
        await pg.screenshot(path='f1_live.png')
        await pg.click('#fol .f1');t2=await ev("$('#sBody').innerText")
        ok('Por terreno' in t2 and 'Por trazado' in t2 and 'Por viento' in t2,'tablas por terreno, trazado y viento')
        await ev("$('[data-act=grp][data-k=shape]').click()");t3=await ev("$('#fol').innerText");ok('Curvas' in t3 and 'Rectas' in t3,'cambiar a comparar por trazado cambia el panel del que sigue');print('   tabla:',t2[:400].replace('\n',' | '))
        await pg.screenshot(path='f1_table.png')
        print('ERRORES JS:',errs or 'ninguno')
        await b.close()
asyncio.run(main())
