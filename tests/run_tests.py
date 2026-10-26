#!/usr/bin/env python3
"""Pruebas automáticas de Rumbo.

Uso (desde la raíz del repo):   python3 tests/run_tests.py            → todas
                                python3 tests/run_tests.py ui_plan g   → solo las que contienen esos textos

Necesita: Python 3 con Playwright (pip install playwright && playwright install chromium) y Node.

Qué hace:
  1. Arma tests/_build/: una copia de index.html servida con un Leaflet de mentira (el mapa no se dibuja,
     todo lo demás corre de verdad) y las páginas de prueba ("harness") que toman pedazos de index.html.
  2. Corre cada prueba por separado. Una prueba falla si termina con error (cada una chequea lo suyo con
     ✔ / ✘ y además que no haya errores de JavaScript). Código 77 = salteada (por ejemplo, sin Bici Indoor).
  3. Al final, un resumen. Sale con código 1 si alguna falló: en GitHub eso frena la compilación del APK.
"""
import os, sys, shutil, subprocess, time, glob

T = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(T)
BUILD = os.path.join(T, '_build')
SITE = os.path.join(BUILD, 'site')
TIMEOUT = 300
# pruebas que dependen de tiempos de animación: si fallan, se reintentan una vez antes de darlas por falladas
REINTENTO = {'ui_multi.py', 'ui_rel.py', 'ui_fpv.py', 'ui_air.py', 'ui_3d.py', 'ui_live.py', 'ui_guard.py'}


def preparar():
    if os.path.exists(BUILD):
        shutil.rmtree(BUILD)
    os.makedirs(os.path.join(SITE, 'lib'))
    shutil.copy(os.path.join(ROOT, 'index.html'), os.path.join(SITE, 'index.html'))
    for f in glob.glob(os.path.join(T, 'lib', '*')):
        shutil.copy(f, os.path.join(SITE, 'lib'))
    shutil.copy(os.path.join(ROOT, 'index.html'), os.path.join(BUILD, 'index.html'))
    for b in sorted(glob.glob(os.path.join(T, 'harness', 'build_*.py'))):
        r = subprocess.run([sys.executable, b], cwd=BUILD, capture_output=True, text=True)
        if r.returncode:
            print(f'✘ No pude armar {os.path.basename(b)} (¿cambió un pedazo de index.html que usa?):\n{r.stderr[-1500:]}')
            sys.exit(1)
    # las páginas de prueba toman pedazos de index.html: el registro de errores (errLog) vive al principio y no
    # siempre entra en el pedazo; acá se agrega uno mínimo que anota en window.__ERRS
    for h in glob.glob(os.path.join(BUILD, 'harness*.html')):
        t = open(h, encoding='utf-8').read()
        stub = '<script>window.__ERRS=[];window.errLog=window.errLog||function(e){window.__ERRS.push(String(e&&e.message||e));};</script>'
        i = t.find('<script')
        open(h, 'w', encoding='utf-8').write(t[:i] + stub + t[i:] if i >= 0 else stub + t)


def correr(f):
    env = dict(os.environ, RUMBO_SITE=SITE, RUMBO_BUILD=BUILD, PYTHONPATH=T + os.pathsep + os.environ.get('PYTHONPATH', ''))
    cmd = ['node', f] if f.endswith('.js') else [sys.executable, f]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=BUILD, env=env, capture_output=True, text=True, timeout=TIMEOUT)
        out, code = r.stdout + r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, code = (e.stdout or b'').decode('utf8', 'replace') if isinstance(e.stdout, bytes) else (e.stdout or ''), -9
        out += f'\n(se pasó de {TIMEOUT} s)'
    # en las pruebas de Node, una línea "FALLA" también cuenta como falla
    if f.endswith('.js') and code == 0 and '\nFALLA' in '\n' + out:
        code = 1
    return code, out, time.time() - t0


def main():
    filtro = sys.argv[1:]
    pruebas = sorted(glob.glob(os.path.join(T, 'ui_*.py'))) + sorted(glob.glob(os.path.join(T, 't_*.js')))
    if filtro:
        pruebas = [p for p in pruebas if any(x in os.path.basename(p) for x in filtro)]
    preparar()
    ok, mal, salt = [], [], []
    for p in pruebas:
        n = os.path.basename(p)
        code, out, dt = correr(p)
        if code not in (0, 77) and n in REINTENTO:
            code, out, dt = correr(p)
        if code == 0:
            ok.append(n); print(f'✔ {n}  ({dt:.0f} s)')
        elif code == 77:
            salt.append(n); print(f'– {n}  salteada')
        else:
            mal.append(n); print(f'✘ {n}  ({dt:.0f} s)')
            lineas = [l for l in out.splitlines() if 'GET /' not in l and 'code 404' not in l]
            print('    ' + '\n    '.join(lineas[-25:]))
            if os.environ.get('GITHUB_ACTIONS'):   # en GitHub: queda como anotación visible en la página de la compilación
                malas = [l.strip() for l in lineas if '✘' in l or 'Error' in l][-3:]
                print(f'::error title=Falló {n}::' + ' | '.join(malas or lineas[-3:]).replace('%', '%25').replace('\r', '').replace('\n', ' ')[:900])
        sys.stdout.flush()
    print(f'\n{len(ok)} bien · {len(mal)} mal · {len(salt)} salteadas')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as fh:
            fh.write(f'### Pruebas de Rumbo: {len(ok)} bien · {len(mal)} mal · {len(salt)} salteadas\n' + ''.join(f'- ✘ {x}\n' for x in mal) + ''.join(f'- – {x} (salteada)\n' for x in salt))
    if mal:
        print('Fallaron: ' + ', '.join(mal))
        sys.exit(1)


if __name__ == '__main__':
    main()
