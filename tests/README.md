# Pruebas de Rumbo

Cada `ui_*.py` abre Rumbo en un Chromium sin pantalla (Playwright) y prueba una parte con datos inventados:
puertas y vueltas, rutas y paradas, ida y vuelta, trazado punto por punto, modo vuelo, fuerzas G, satélites,
3D, Bici Indoor, Kayak Indoor, grupo y guardián, etc. Los `t_*.js` son pruebas de Node de la lógica pura.

Cómo correrlas en la compu:

    pip install playwright && playwright install chromium
    python3 tests/run_tests.py            # todas (unos minutos)
    python3 tests/run_tests.py plan via   # solo las que tienen "plan" o "via" en el nombre

En GitHub corren solas antes de compilar el APK: si una falla, no se publica.
Para compilar igual (una urgencia), poné `[sin tests]` en el mensaje del commit.

Detalles:
- El mapa (Leaflet) es de mentira (`tests/lib/leaflet.js`): no dibuja, pero todo lo demás corre de verdad.
- `tests/harness/` arma páginas de prueba con pedazos de `index.html`. Si al cambiar el código un pedazo deja
  de encontrarse, el armado falla y lo dice.
- `ui_bk.py` y `ui_ky.py` prueban el paso de rutas a Bici Indoor y Kayak Indoor: usan la versión publicada
  de esas apps (o un archivo local con `RUMBO_BICI` / `RUMBO_KAYAK`). Sin ellas, se saltean.
- `_build/` es lo que se arma para correr; no se sube.
