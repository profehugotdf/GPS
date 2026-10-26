import re
s=open('index.html',encoding='utf-8').read()
def cut(a,b):
    i=s.index(a);j=s.index(b,i);return s[i:j]
live=cut("/* ---------- 📡 Seguimiento en vivo","/* ---------- Más, ajustes y backup ---------- */")
css=cut("#shpill{","\n#rtp") if "#rtp" in s[s.index("#shpill{"):s.index("#shpill{")+5000] else ""
css=s[s.index("#shpill{"):s.index("@keyframes folp")]+s[s.index('.f1{'):s.index('#fol .f1 .good')]; css+=s[s.index("@keyframes folp"):s.index("\n",s.index("@keyframes folp"))]
fn=lambda n:cut("function "+n+"(","\n}\n")+"\n}\n"
helpers=fn("hav")+fn("pip")+fn("projSeg")+fn("armed")+fn("bearingTo")+fn("crossFrac")+fn("gateAt")+fn("dirOK")+fn("makeGate")+fn("upgradeGate")+fn("gateRoles")+fn("fmtT")+fn("barChart")+fn("raceBlock")+fn("lapBlock")+fn("pointAlong")+fn("polyLen")
helpers+=cut("const ROLE_NAME=","function dirOK(")
helpers+=cut("/* índice de la puerta de vueltas","/* Avisos para mostrar")
helpers+=cut("/* circuito de vueltas con llegada aparte","/* Recalcula vueltas")
helpers+=cut("function bestOf(","/* Estadísticas de un track")
helpers+=re.search(r"const fmtDelta=[^\n]*\n",s).group(0)+re.search(r"const bbKm=[^\n]*\n",s).group(0)
helpers+=cut("/* ====================== SECTORES TIPO FÓRMULA 1","/* ---------- Seguimiento") if "/* ---------- Seguimiento" in s[s.index("SECTORES TIPO"):] else cut("/* ====================== SECTORES TIPO FÓRMULA 1","async function showTrackDetail(")
for k in ["DS_AUTO","DSEP","dec","fmtD","hhmm","esc","uid"]:
    helpers+=re.search(r"(?:const|let) "+k+r"=[^\n]*\n",s).group(0)
html='''<!doctype html><meta charset=utf-8><style>:root{--top:0px;--bot:0px}body{margin:0;font-family:system-ui;background:#cde}'''+css+'''
.card.on{outline:2px solid #000}</style>
<div id="netpill" hidden></div><button id="shpill" hidden onclick="showShare()"></button><div id="fol" hidden></div><div id="grp" hidden></div>
<div id=sheet><div id=sTitle></div><div id=sBody></div></div>
<script>
const rad=Math.PI/180,R_EARTH=6371008.8,pad2=n=>String(n).padStart(2,'0');
const $=(q,r=document)=>r.querySelector(q);
const T={toasts:[],lines:[],fits:0,tgt:null,now:Date.parse('2026-10-18T10:00:00-03:00')};
Date.now=()=>T.now;
const STORE=[];let NID=0;window.REALFETCH=window.fetch;
window.fetch=async(url,o)=>{
  if(T.offline)throw new Error('offline');
  const m=url.match(/ntfy\\.sh\\/([^/?]+)(\\/json\\?poll=1&since=(.*))?$/);
  if(o&&o.method==='POST'){STORE.push({id:'m'+(++NID),topic:m[1],message:o.body,len:o.body.length});return {ok:true,status:200}}
  const since=m[3];let arr=STORE.filter(x=>x.topic===m[1]);
  if(since&&since!=='all'){const i=arr.findIndex(x=>x.id===since);arr=arr.slice(i+1);}
  return {ok:true,status:200,text:async()=>arr.map(x=>JSON.stringify({id:x.id,event:'message',message:x.message})).join('\\n')};
};
window.EventSource=undefined;
function mkG(){const g={items:[],addTo(){return g},clearLayers(){g.items.length=0}};return g}
const L={rectangle:(b,o)=>({on(){return this},addTo(g){g.items.push({t:'rect',b,o});return this}}),imageOverlay:(u,b,o)=>({addTo(g){g.items.push({t:'img',b});return this}}),polygon:(p,o)=>({addTo(g){g.items.push({t:'poly'});return this}}),layerGroup:()=>mkG(),polyline:(ll,o)=>({addTo(g){g.items.push({t:'line',n:ll.length,o})}}),marker:(ll,o)=>({addTo(g){g.items.push({t:'mk',ll,html:o.icon.html})}}),divIcon:o=>o,latLngBounds:x=>x};
const map={fitBounds(){T.fits++},setView(){},getZoom:()=>14,getBounds:()=>({getNorth:()=>-54.795,getSouth:()=>-54.805,getEast:()=>-68.285,getWest:()=>-68.31})};const shareFile=(n,t)=>{T.file=[n,t]};const DB={all:async()=>[]};
const S={};function saveS(){}
const RT={res:null,sel:null,to:null},REC={state:'idle',timers:[]},NAV={on:false};let RUNS=[];const ghostCache={};function bestBy(){return null}function sectorBests(){return []}const activeTimer=()=>{let b=null;for(const t of REC.timers)if(t.gt.cur&&(!b||t.gt.cur.start>b.gt.cur.start))b=t;return b;};let watch=null,lastFix=null;
var isNative=()=>false,plugin=()=>null;const startWatch=async()=>{},toast=t=>T.toasts.push(t),setFollow=()=>{},setTarget=(a,b,c)=>{T.tgt=[a,b,c]},clearTarget=()=>{T.tgt=null};
T.said=[];T.beeps=0;let actx=null;const unlockAudio=()=>{},beep=()=>{T.beeps++},say=t=>{if(S.voice)T.said.push(t)};
const ACT={walk:['🚶','Caminata'],run:['🏃','Correr'],bike:['🚴','Bici'],car:['🚗','Auto'],kayak:['🛶','Kayak'],swim:['🏊','Natación']};
function simplifyDP(p){return p.filter((_,i)=>i%3==0||i==p.length-1)}
let onAct=null,onChg=null;
function openSheet(t,h,a,c){$('#sTitle').textContent=t;$('#sBody').innerHTML=h;onAct=a;onChg=c}
function closeSheet(){$('#sBody').innerHTML='';onAct=null}
$('#sBody').addEventListener('click',e=>{const el=e.target.closest('[data-act]');if(el&&onAct)onAct(el.dataset.act,el.dataset,el)});
$('#sBody').addEventListener('change',e=>{if(onChg)onChg(e.target)});
'''+helpers+'''
</script><script>
'''+live+cut('/* ====================== ⌚ AVISOS AL RELOJ','async function startRec(){')+'''
</script>'''
open('harness_live.html','w',encoding='utf-8').write(html)
print('ok',len(html))
g=html.replace("window.fetch=async(url,o)=>{","window.fetch=window.REALFETCH;window.fetch2=async(url,o)=>{",1)
open('harness_grp.html','w',encoding='utf-8').write(g)
