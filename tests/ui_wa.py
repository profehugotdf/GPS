import asyncio
from playwright.async_api import async_playwright
import os
SITE=os.environ.get('RUMBO_SITE','.');BUILD=os.environ.get('RUMBO_BUILD','.')
def ok(c,m):
    print(('  ✔ ' if c else '  ✘ ')+m);assert c,m
async def main():
    errs=[]
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await b.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('file://'+BUILD+'/harness_live.html');ev=pg.evaluate
        await ev("""(()=>{
          window.SENT=[];window.isNative=()=>true;
          const LN={createChannel:async()=>{},schedule:async o=>{SENT.push({t:T.now,title:o.notifications[0].title})},cancel:async()=>{},checkPermissions:async()=>({display:'granted'}),requestPermissions:async()=>({display:'granted'})};
          window.plugin=n=>n==='LocalNotifications'?LN:null;
          const O=[-54.8,-68.3],k=1/(111195*Math.cos(54.8*rad)),la=1/111195;
          const C=[[0,0],[0,100],[100,100],[100,0]];window.SQ=C.map(([n,e])=>[O[0]+n*la,O[1]+e*k]);const brgs=[90,0,270,180];
          const gates=C.map(([n,e],i)=>{const [n2,e2]=C[(i+1)%4];return makeGate({c:[O[0]+(n+n2)/2*la,O[1]+(e+e2)/2*k],w:30,brg:brgs[i],dirOnly:true,role:i?'split':'startfinish'});});
          window.CIRC={id:'c1',name:'Pileta del lago',type:'closed',gates,secs:[{name:'Ida'},{},{name:'Vuelta'},{}]};
          const ent={circ:CIRC};
          ent.ref=skip=>{let b=null;const ls=skip?ent.gt.laps.slice(0,-1):ent.gt.laps;for(const l of ls)if(!b||l.time<b.time)b={time:l.time,splits:l.splits,t0:l.start,tid:REC.id};return b;};
          ent.gt=new GateTimer(CIRC,{
            onStart:()=>{ent.d0=REC.dist;ent.wNext=null;ent.wPrev=0;waProfile(ent);},
            onGate:()=>{const cs=ent.gt.cur,secs=cs.marks.map((m,i,a)=>m-(i?a[i-1]:cs.start));waSector(ent,secs,ent.ref(false),ent.gt.laps.length+1);},
            onLap:lap=>{waSector(ent,lapSectors(lap),ent.ref(true),lap.n);if(ent.gt.cur){ent.d0=REC.dist;ent.wNext=null;ent.wPrev=0;waProfile(ent);}}});
          Object.assign(REC,{state:'rec',timers:[ent],id:'R1',pts:[],dist:0,act:'swim'});window.ENT=ent;
          S.watch={on:true,gates:true,every:50,only:'all',tol:1,n:3,gap:3};
        })()""")
        print('1) nada 3 vueltas de 400 m: la 2ª más rápida en la ida, la 3ª más lenta en todo')
        await ev("""(async()=>{
          const pts=[];for(let i=0;i<4;i++){const a=SQ[i],b=SQ[(i+1)%4];for(let s=0;s<20;s++)pts.push([a[0]+(b[0]-a[0])*s/20,a[1]+(b[1]-a[1])*s/20,i]);}
          let prev=null;
          for(let step=0;step<80*3+12;step++){
            const lap=Math.floor((step+10)/80),p=pts[step%80];
            const v=lap==0?1.1:lap==1?(p[2]<2?1.2:1.1):1.0;
            const dt=5/v*1000;T.now+=dt;
            const q=[p[0],p[1],T.now];
            if(prev){REC.dist+=hav(prev,q);ENT.gt.feed(prev,q);}
            prev=q;REC.pts.push([q[0],q[1],q[2],5,null,0]);
            lastFix={lat:p[0],lon:p[1],acc:5,t:T.now};
            waTick();waPump();
            await new Promise(r=>setTimeout(r,1));
          }
          const end=T.now+20000;while(T.now<end){T.now+=1000;waPump();await new Promise(r=>setTimeout(r,1));}
        })()""")
        sent=await ev("SENT.map(x=>x.title)")
        for x in sent:print('   ',x)
        ok(any('S1 Ida' in x and x.startswith('✅') for x in sent),'vuelta 2, sector Ida más rápido: 1 aviso ✅')
        bad=[x for x in sent if x.startswith('⚠️') and 'S1' in x]
        ok(len(bad)>=3,'vuelta 3 más lenta: avisos ⚠️ repetidos (3)')
        ok(any(' m: tramo' in x for x in sent),'avisos cada 50 m contra el récord, sin pisar los de puerta')
        await ev("SENT.length=0;S.watch.only='bad';waSignal(true,'x','y');waSignal(false,'z','w')");await ev("T.now+=10000;waPump()")
        ok(await ev("SENT.length===1||SENT.every(x=>x.title.startsWith('⚠️'))"),'“solo si voy peor” no avisa lo bueno')
        print('ERRORES JS:',errs or 'ninguno')
        await b.close()
asyncio.run(main())
