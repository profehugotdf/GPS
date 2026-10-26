"""Las apps hermanas (Bici Indoor, Kayak Indoor) para las pruebas que cruzan de una app a otra.
Primero un archivo local (variable de entorno con la ruta), si no, la versión publicada en GitHub Pages.
Si no hay ninguna de las dos, devuelve None y la prueba se saltea (no falla)."""
import os,urllib.request
def otra_app(var,url):
    p=os.environ.get(var)
    if p and os.path.exists(p):
        return open(p,'rb').read()
    try:
        with urllib.request.urlopen(url,timeout=20) as r:
            b=r.read()
            return b if len(b)>10000 else None
    except Exception:
        return None
