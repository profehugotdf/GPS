import re,json
s=open('index.html',encoding='utf-8').read()
def cut(a,b):
    i=s.index(a);j=s.index(b,i);return s[i:j]
sheetpart=cut("let NSEL=null;","/* ---------- Ubicación ---------- */")
armed=cut("function armed(el){","\n}\n")+"\n}\n"
netIndex=cut("async function netIndex(){","async function drawCoverage(){")
i=s.index("/* Mosaicos de una misma descarga");j=s.index("\n}\n",s.index("async function showMapMgr(){"))+3
mgr=s[i:j]
fmt=re.search(r"const fmtDate=[^\n]*\n",s).group(0)
uid=re.search(r"const uid=[^\n]*\n",s).group(0)
html='''<!doctype html><meta charset=utf-8><style>#sheet{position:fixed;left:0;right:0;bottom:0;height:300px;background:#fff}#sBody{height:240px;overflow:auto}.btn{padding:4px}</style>
<div id=sheet><div id=sTitle></div><button id=sX></button><div id=sBody></div></div>
<script>
const KV=new Map();
const DB={async get(s,k){return KV.get(k)},async put(s,k,v){KV.set(k,JSON.parse(JSON.stringify(v)))},async del(s,k){KV.delete(k)},async keys(s,p){return [...KV.keys()].filter(k=>k.startsWith(p))},async all(s,p){return [...KV.entries()].filter(([k])=>k.startsWith(p)).map(([,v])=>v)},async countp(){return 0}};
const $=(s,r=document)=>r.querySelector(s);
const REC={rects:[],fit:[],toasts:[],changed:0,cov:0};
function mkGroup(){const g={rects:[],addTo(){return g},clearLayers(){g.rects.length=0},addLayer(){}};return g}
const L={layerGroup:()=>mkGroup(),rectangle:(b,o)=>({addTo(g){g.rects.push({b,o})}})};
const map={getCenter:()=>({lat:0,lng:0}),fitBounds:(b,o)=>REC.fit.push({b,o})};
const S={},LAYERS={},OVL=[];let sheetTitle=null,onAct=null,onChg=null,editingCirc=null,draw=false;function refreshGates(){}
const esc=x=>String(x),mbf=x=>String(x),toast=(t)=>REC.toasts.push(t),zoneMissing=async()=>false;
const drawCoverage=()=>{REC.cov++},netsChanged=()=>{REC.changed++};
const clearTiles=async()=>{},dlNet=async()=>false,openCap=()=>{};
'''+fmt+uid+'''
</script><script>
'''+sheetpart+armed+netIndex+mgr+'''
</script>'''
open('harness.html','w',encoding='utf-8').write(html)
print('harness',len(html))
