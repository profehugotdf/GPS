# Arma harness_3d.html: la plantilla con el segmento 3D de index.html (de "VISTA 3D" hasta "❤️ Banda") metido adentro.
s=open('index.html',encoding='utf-8').read()
a='/* ====================== 🏔️ VISTA 3D';b='/* ---------- ❤️ Banda'
i=s.index(a);j=s.index(b,i)
import os
tpl=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'harness_3d.tpl.html'),encoding='utf-8').read()
assert tpl.count('/*@@SLICE@@*/')==1
open('harness_3d.html','w',encoding='utf-8').write(tpl.replace('/*@@SLICE@@*/',s[i:j]))
