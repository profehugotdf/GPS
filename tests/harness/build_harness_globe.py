import re
s=open('index.html',encoding='utf-8').read()
def cut(a,b):
    i=s.index(a);j=s.index(b,i);return s[i:j]
css=cut("#globe{transition","#netpill{position:fixed;")
html=cut('<div id="globe" hidden>','<div id="toast">')
hav=cut("function hav(a,b){","\n}\n")+"\n}\n"
rad=re.search(r"const rad=Math\.PI/180, R_EARTH=[^\n]*\n",s).group(0)
fmtD=re.search(r"const fmtD=[^\n]*\n",s).group(0)
wind=re.search(r"const WIND=[^\n]*\n",s).group(0)
layers=cut("const LAYERS={","const tileUrl=")
tileurl=re.search(r"const tileUrl=[^\n]*\n",s).group(0)
bt=cut("function bearingTo(a,b){","\n}\n")+"\n}\n"
cw=re.search(r"(const|function) compassWord[^\n]*\n",s).group(0)
tp=cut("function tgtPath(","\nfunction updTarget")
gb=cut("/* ---------- 🌍 Globo:","\n\n/* ---------- Copia de seguridad completa")
page=f'''<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<style>:root{{--top:0px;--bot:0px;--paper:#fff;--ink:#0E2A36}}body{{margin:0;background:#334}}.btn{{padding:6px 10px}}{css}</style>
<div id="map" style="position:fixed;inset:0"></div>
{html}
<script>
const KV=new Map();
const DB={{async get(s,k){{return KV.get(k)}},async put(s,k,v){{KV.set(k,v)}},async all(s,p){{return [...KV.entries()].filter(([k])=>k.startsWith(p)).map(([,v])=>v)}}}};
const $=(s,r=document)=>r.querySelector(s);
const T={{views:[],toasts:[],targets:[],fetches:0,netOk:true,zoomH:null,finds:0}};
const toast=t=>T.toasts.push(t);const showFind=()=>T.finds++;
const map={{_z:2,getCenter(){{return {{lat:-30,lng:-60}}}},getZoom(){{return this._z}},setView(c,z){{T.views.push({{c,z}});this._z=z}},on(ev,fn){{if(ev==='zoomend')T.zoomH=fn;if(ev==='zoomanim')T.animH=fn}}}};
const S={{}};function saveS(){{}}
const REC={{state:'idle'}},NAV={{on:false}},RT={{res:null,sel:null}};
let lastFix={{lat:-54.80,lon:-68.30}};
const TGT={{on:false,lat:0,lon:0}};function setTarget(a,b,l){{TGT.on=true;TGT.lat=a;TGT.lon=b;T.targets.push([a,b,l]);}}
async function netAllowed(){{return T.netOk}}const netBlocked=()=>!T.netOk;
/* mundo sintético en Mercator, 2048 px */
const MASTER=document.createElement('canvas');MASTER.width=MASTER.height=2048;
(function(){{const c=MASTER.getContext('2d');c.fillStyle='#1c4f7a';c.fillRect(0,0,2048,2048);
 const mx=lon=>(lon+180)/360*2048,my=lat=>(0.5-Math.log(Math.tan(Math.PI/4+lat*Math.PI/360))/(2*Math.PI))*2048;
 c.fillStyle='#3a7d3a';c.fillRect(mx(-75),my(10),mx(-35)-mx(-75),my(-55)-my(10));
 c.strokeStyle='rgba(255,255,255,.55)';c.lineWidth=1.5;
 for(let lo=-180;lo<=180;lo+=15){{c.beginPath();c.moveTo(mx(lo),0);c.lineTo(mx(lo),2048);c.stroke();}}
 for(let la=-80;la<=80;la+=15){{c.beginPath();c.moveTo(0,my(la));c.lineTo(2048,my(la));c.stroke();}}
 const dot=(la,lo,col,r)=>{{c.fillStyle=col;c.beginPath();c.arc(mx(lo),my(la),r,0,7);c.fill();}};
 dot(-54.8,-68.3,'#ff0000',9);dot(-26.83,-65.2,'#00ff00',9);dot(0,0,'#ffff00',9);dot(0,179.5,'#ff00ff',9);dot(0,-179.5,'#ff00ff',9);dot(40,100,'#00ffff',9);
}})();
async function getTileBlob(url){{T.fetches++;const m=url.match(/tile\\/(\\d+)\\/(\\d+)\\/(\\d+)/),z=+m[1],y=+m[2],x=+m[3],sc=Math.pow(2,z-3);const c=document.createElement('canvas');c.width=c.height=256;const g=c.getContext('2d');g.drawImage(MASTER,x*256/sc,y*256/sc,256/sc,256/sc,0,0,256,256);if(z>3){{g.strokeStyle='#ff00ff';g.fillStyle='#ff00ff';g.fillRect(100,100,24,24);}}return new Promise(r=>c.toBlob(r,'image/png'));}}
{rad}{hav}{tp}{bt}{cw}{fmtD}{wind}{layers}{tileurl}
</script><script>
{gb}
</script>'''
open('harness_globe.html','w',encoding='utf-8').write(page)
print(len(page))
