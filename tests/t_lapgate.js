const fs=require('fs');const src=fs.readFileSync('index.html','utf8');
const cut=(a,b)=>{const i=src.indexOf(a);const j=src.indexOf(b,i);if(i<0||j<0)throw new Error('no '+a);return src.slice(i,j);};
const code=cut('function hav(a,b){','/* Recalcula vueltas')+cut('function analyze(','function bestOf(');
const H=new Function('const rad=Math.PI/180,R_EARTH=6371008.8;'+code+';return {gateRoles,lapGateOf,circType,loopGates,gateCheck,GateTimer,makeGate,analyze,hasLapFin};')();
let ok=0,bad=0;const t=(n,c,x='')=>{c?ok++:bad++;console.log((c?'OK    ':'FALLA ')+n+(x!==''?'  → '+x:''));};
const la0=-34.6,lo0=-58.5,k=111320*Math.cos(la0*Math.PI/180);
const LL=(x,y)=>[la0+y/110540,lo0+x/k];
const G=(x,y,brg,role,w=24)=>H.makeGate({c:LL(x,y),brg,w,dirOnly:true,role});
const circ={id:'c1',name:'Pista',gates:[G(-300,-50,90,'start'),G(-200,-50,90,'split'),G(-100,0,0,'lap'),G(100,0,180,'split'),G(0,20,90,'finish')]};
/* recorrido: ida por y=-50, vueltas al rectángulo en sentido horario, y al final adentro hacia la llegada */
function path(nLoops,{skipStart=false,finishEarlyAfter=null}={}){
  const P=[];const seg=(a,b)=>{const d=Math.hypot(b[0]-a[0],b[1]-a[1]),n=Math.max(1,Math.round(d/8));for(let i=1;i<=n;i++)P.push([a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n]);};
  let cur=skipStart?[-100,-60]:[-350,-50];P.push(cur);
  const go=b=>{seg(cur,b);cur=b;};
  if(!skipStart){go([-100,-50]);}
  go([-100,-100]); /* entra a la pista por la esquina SO */
  for(let i=0;i<nLoops;i++){go([-100,100]);go([100,100]);go([100,-100]);go([-100,-100]);if(finishEarlyAfter===i+1)break;}
  go([-100,20]);go([60,20]);
  return P.map((p,i)=>{const l=LL(p[0],p[1]);return [l[0],l[1],i*2000,5,0,0];});
}
const run=(c,pts,cbs)=>{const gt=new H.GateTimer(c,cbs);for(let i=1;i<pts.length;i++)gt.feed(pts[i-1],pts[i]);gt.flush();return gt;};
t('roles: largada, parcial, vueltas, parcial, llegada',H.gateRoles(circ).join()==='start,split,lap,split,finish',H.gateRoles(circ).join());
t('es un circuito de vueltas (closed) con puerta 🔄 en 2',H.circType(circ)==='closed'&&H.lapGateOf(circ)===2);
t('la vuelta son las puertas 2 y 3',H.loopGates(circ).join()==='2,3');
t('aviso ℹ️ de carrera',H.gateCheck(circ).some(w=>w.includes('Carrera con largada, vueltas y llegada')));
/* 1) sin cantidad: 4 vueltas y llegada */
let ev=[];let gt=run(circ,path(4),{onStart:()=>ev.push('start'),onPre:g=>ev.push('pre'+g),onLoop:()=>ev.push('loop'),onLap:l=>ev.push('lap'+l.n),onFinish:r=>ev.push('fin'),onLapsDone:()=>ev.push('done')});
// la primera pasada por la 🔄 empieza la vuelta 1 (sin contar), luego 4 vueltas cerradas al volver a pasar... la 4ª vuelta termina al pasar la 🔄 en la salida hacia la llegada
t('eventos en orden',ev.join()==='start,pre1,loop,lap1,lap2,lap3,lap4,fin',ev.join());
const R=gt.races[0];
t('carrera: 4 vueltas, tiempo desde la largada',R&&R.laps===4&&R.time>0&&R.app>0,R&&JSON.stringify({laps:R.laps,time:R.time,app:R.app,pre:R.pre,toFin:R.toFin}));
t('cada vuelta tiene 2 sectores',gt.laps.every(l=>l.splits.length===2),gt.laps.map(l=>l.splits.length).join());
t('vueltas parejas (~800 m)',gt.laps.every(l=>Math.abs(l.time-gt.laps[0].time)<=4000),gt.laps.map(l=>l.time/1000).join());
t('quedó esperando otra largada',gt.exp===0&&!gt.race&&!gt.cur);
/* 2) con 3 vueltas pero da 5: deja de contar después de la 3ª y termina en la llegada */
const c3=Object.assign({},circ,{nLaps:3});ev=[];
gt=run(c3,path(5),{onLapsDone:()=>ev.push('done'),onLap:l=>ev.push('lap'+l.n),onFinish:()=>ev.push('fin')});
t('plan de 3 pero da 5: cuenta las 5 y avisa al cumplir el plan',ev.join()==='lap1,lap2,lap3,done,lap4,lap5,fin'&&gt.races[0].laps===5,ev.join());
t('cada vuelta extra con sus sectores',gt.laps.every(l=>l.splits.length===2),gt.laps.map(l=>l.splits.length).join());
const c10=Object.assign({},circ,{nLaps:10});ev=[];
gt=run(c10,path(5),{onFinPend:()=>ev.push('pend'),onFinish:r=>ev.push('fin'+r.laps)});
t('plan de 10 pero da 5 y va a la llegada: cierra con 5',ev.join()==='pend,fin5'&&gt.races[0].laps===5,ev.join());
/* 4 vueltas dadas pero el GPS se saltó un paso por la 🔄 (hueco de señal): termina igual */
const c4=Object.assign({},circ,{nLaps:4});
{const P=path(4);let n=0,inside=false;const Q=P.map(p=>{const x=(p[1]-lo0)*k,y=(p[0]-la0)*110540;const near=Math.abs(x+100)<2&&Math.abs(y)<25;if(near&&!inside){inside=true;n++;}if(!near)inside=false;
   if(near&&n===3){const l=LL(x-45,y);return [l[0],l[1],p[2],p[3],p[4],p[5]];}return p;});
 gt=run(c4,Q,{});t('un paso perdido por el GPS: termina igual',gt.races.length===1,gt.races.map(r=>r.laps).join()+' · vueltas '+gt.laps.length);}
/* llegada que se cruza en cada vuelta (mal ubicada sobre la pista): no corta la carrera hasta completar */
const cX=Object.assign({},circ,{nLaps:3,gates:circ.gates.slice(0,4).concat([G(-100,60,0,'finish')])});
gt=run(cX,path(4),{});
t('llegada mal puesta sobre la pista: no corta antes del plan',gt.races.length===1&&gt.races[0].laps===3,gt.laps.length+' vueltas, carreras '+gt.races.map(r=>r.laps).join());
/* 4) empieza a grabar ya en la pista (sin largada): arranca en la 🔄 */
gt=run(circ,path(3,{skipStart:true}),{});
t('sin largada: arranca en la 🔄 y cuenta',gt.races.length===1&&gt.races[0].app===0&&gt.races[0].laps>=2,JSON.stringify(gt.races.map(r=>({l:r.laps,app:r.app}))));
/* 5) la llegada no cuenta en el camino de ida */
const cF=Object.assign({},circ,{gates:circ.gates.slice(0,4).concat([G(-150,-50,90,'finish')])});
t('roles con llegada en la ida',H.gateRoles(cF).join()==='start,split,lap,split,finish');
gt=run(cF,path(0),{});
t('cruzar la llegada antes de entrar a la pista no termina',gt.races.length===0&&gt.race&&gt.race.app!=null,JSON.stringify(gt.race));
/* 6) reglas: 🔄 sin largada aparte → parcial; dos 🔄 → la segunda parcial */
const cx={gates:[G(0,0,0,'startfinish'),G(1,0,0,'lap'),G(2,0,0,'split')]};
t('🔄 en circuito de largada/llegada pasa a parcial',H.gateRoles(cx).join()==='startfinish,split,split');
const cy={gates:[G(0,0,0,'start'),G(1,0,0,'lap'),G(2,0,0,'lap'),G(3,0,0,'finish')]};
t('segunda 🔄 pasa a parcial',H.gateRoles(cy).join()==='start,lap,split,finish');
/* 7) analyze de un track grabado */
const L=H.analyze(path(3),circ);t('analyze: 3 vueltas y 1 carrera',L.length===3&&L.races.length===1&&L.races[0].laps===3);
/* 8) los circuitos viejos siguen igual */
const old={gates:[G(-100,0,0,'startfinish'),G(100,0,180,'split')]};
gt=run(old,path(3,{skipStart:true}),{});t('circuito cerrado clásico sigue contando',gt.laps.length===3,gt.laps.length);
const p2p={type:'p2p',gates:[G(-300,-50,90,'start'),G(-200,-50,90,'split'),G(-100,0,0,'split')]};
t('punto a punto sigue igual',H.circType(p2p)==='p2p'&&run(p2p,path(1),{}).laps.length===1);
console.log(`\n${ok} OK, ${bad} fallas`);process.exit(bad?1:0);
