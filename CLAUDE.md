# Rumbo (repo GPS)

> Archivo de instrucciones para Claude (y para cualquiera que trabaje en este repo). Se lee solo al arrancar una conversación con este repo. Si algo de acá deja de ser cierto, actualizalo en el mismo cambio.


App de mapas offline, tracks, puertas tipo RaceChrono, rutas, grupo y guardián, 3D, Modo vuelo y Estado del GPS. Hay dos versiones: la web (`profehugotdf.github.io/GPS/`) y el **APK** (Capacitor), que compila GitHub Actions.

## Lo propio de este repo

- `index.html` (~950 KB, ~13.400 líneas). Usa Leaflet: en la web desde `lib/` o unpkg; en el APK, desde npm. No tiene número de versión en la web; el APK muestra su build en Ajustes.
- Almacenamiento: IndexedDB `rumbo` (almacenes `kv` y `tiles`). Claves en `kv`: `track:`, `prx:`, `wpt:`, `edit:`, `net:`, `rec:current` (grabación en curso), `errlog`, `gpslog`.
- **Registro de errores**: `errLog(e, dónde, grave)`. No escribir `catch(e){}` vacíos: usar `catch(e){errLog(e)}`. Lo grave avisa en pantalla. Se ve en Más → Ajustes → 🩺 Diagnóstico.
- **APK** (`.github/workflows/build.yml`):
  - Primero corre el trabajo `pruebas`. Si alguna falla, no se compila ni se publica.
  - `[sin tests]` en el mensaje del commit las saltea, solo para urgencias.
  - Arma el proyecto Android desde cero en cada compilación y le agrega plugins nativos escritos dentro del YAML: `RumboOpen` (abrir GPX/TCX y links) y `RumboGnss` (satélites).
  - Firma fija: hay un chequeo de la huella, y si cambia la firma no se publica.
  - Publica en Releases como `build-N`.
  - Debe haber **un solo** workflow. Hubo una copia `build-1.yml` que compilaba dos APK por cada cambio.
- **Pruebas**: `python3 tests/run_tests.py [filtro]`. Son más de 35, con Playwright y Node; ver `tests/README.md`.
  - Leaflet es de mentira, y las páginas `tests/harness/` toman pedazos de `index.html` buscando textos marcadores. Si cambiás un marcador, el armado falla y lo dice.
  - Para cada función nueva, agregá una `tests/ui_<algo>.py` siguiendo el estilo de las otras.
- El código usa nombres cortos por módulo: `RT` rutas, `REC` grabación, `GRP`/`GD` grupo y guardián, `SH` compartir, `FL` Modo vuelo, `GN` satélites, `PL` trazar ruta, `MS` medir, `T3` 3D, `KY`/`BK` envío a Kayak y a Bici/Correr (`bkSend({app:'correr'})`). El escenario sale de OpenStreetMap: `bkOsm(bb,line)` trae el uso del suelo de la zona y, pegado al camino (`around`), casas y calles; `bkScenes` arma los tramos y `bkLand` los costados cada 25 m (si la consulta grande falla, se usa la de antes).
- **Semáforos 🚦 en el ruteo**:
  - Datos: al bajar calles se pide `node["highway"="traffic_signals"]` y la red guarda `sg:[[id del nodo OSM, lat, lon],…]` (`fetchNet`). `sg` ausente = red bajada antes de esto ("sin datos", `sigK` false); `[]` = se bajó y no hay. Para las redes viejas, Correcciones tiene "🚦 Traer los semáforos de lo que ya bajé" (`dlSignals`/`fetchSignals`, solo nodos, sin volver a bajar calles). El índice `netidx:` lleva `sg` (cantidad, −1 = sin datos). La red regional no trae semáforos. Los mosaicos que se juntan (`mergeGroup`) solo conservan `sg` si todos lo tenían.
  - A mano: Correcciones → "Giros, barreras y semáforos" → 🚦 Semáforo guarda `edit:` con `type:'signal'` (`{lat,lon,name}`); `applyExtras` lo pega al nodo más cercano (o parte el tramo si cae a mitad de cuadra).
  - Grafo: `G.sig` (Set de nodos). `addSignals` ubica los de OSM por id de nodo; `clusterSignals` junta los que están a menos de `SIG_CLUSTER` m por la calle en uno, puesto en la esquina (OSM suele marcar uno por acceso). `Graph.cost` suma al llegar a un semáforo la espera del modo (`cfg.sig`, de `S.sigFoot/sigBike/sigCar`, segundos, 0 = no contar); en "más corta" no cuenta (es distancia); en `'nosig'` ("🚦 Menos semáforos") suma además `SIG_AVOID` s por cada uno.
  - Resultado de `findRoute`: `sig` (cantidad), `sigWait` (s, ya sumados a `time` y `timeBack`), `sigPts` (posiciones) y `sigK`. El semáforo del último nodo no se cuenta (ahí termina la ruta). `joinRoutes` los suma. `sigTxt(r)` arma el texto de la tarjeta y del panel (sin datos de semáforos no muestra nada).
  - Guiarme: `navInit` arma `N.sgs` a partir de `route.sigPts` (no de `hz`, así avisa los mismos que cuenta el tiempo) y `navTick` dice "Semáforo en N metros" (`NAVP[modo].hz.semaforo`); se apaga con `S.sigVoice===false` (Ajustes).
  - Con `timeMode:'avg'` el % de paradas ya incluye parte de la espera: la espera por semáforo se suma igual (es explícita) y Ajustes avisa que conviene bajar uno de los dos. Prueba: `tests/ui_sig.py`.
- **Velocidades aprendidas (auto)** (`vlLearn`, `vlMatch`, `vlSpeeds`, `vlDeleteDone`, `vlRender`; Ajustes → 📚):
  - Cada salida con `act:'car'` se cruza **una sola vez** con las calles guardadas (`ensureGraph` con el centro del track): por cada par de puntos en movimiento (> 1 m/s, sin saltos ni mala señal) se toma la calle de auto más cercana (≤ 20 m) y casi paralela, y se suma `[metros, segundos, tramos]` en `kv` `vel:car` → `{v:1, done:{idTrack:{t,km,p}}, bins:{'tipo|pendiente|franja':[m,s,n]}}`. Pendiente: `b` bajada, `l` llano, `s` subida (±3 %), `x` sin altura. Franja (hora local de salida): 0 madrugada, 1 mañana, 2 tarde, 3 noche. `done` evita contar una salida dos veces; si menos del 40 % de los puntos cruza con calles, la salida queda pendiente (no se cuenta).
  - Las paradas no cuentan (la espera en semáforos ya se suma aparte con `sigCar`).
  - Uso: con `S.vlOn` (default `false`), `ensureGraph` arma `cfg.vl = vlSpeeds(vl, franja de depMs())` y `wayProfile` usa esa velocidad (m/s) en vez de `kmh·carF` para los tipos de calle con ≥ 1 km y ≥ 30 tramos (la franja propia si alcanza, si no la de todo el día; en auto la pendiente no cambia la velocidad, `slopeFactor` = 1). Si cambia la franja de la hora de salida, el grafo se rearma solo (`G.vlFr`). Con `timeMode:'avg'` el tiempo sigue saliendo del promedio; lo aprendido solo cambia qué camino conviene.
  - **Nada se borra solo.** "Borrar los N tracks de auto ya procesados" (`vlDeleteDone`, con doble toque) borra únicamente los `act:'car'` que están en `done`; el resumen queda. "Olvidar lo aprendido" borra `vel:car`. Pensado para a pie y bici más adelante: la misma estructura con otra clave. Prueba: `tests/ui_vel.py`.
- **Rotonda dibujada** (Calcar → 🔄 Rotonda, `kind:'rotonda'`, tags `highway=tertiary`+`junction=roundabout`): se toca el centro, después el extremo del lado largo (semieje 6–80 m; con eso ya hay un círculo) y, si hace falta un óvalo, un tercer toque (repetible) fija el semieje corto (`rbTap`, `rbOval`, 32 puntos); "Terminar trazo" la guarda; `traceSave` la guarda siempre `oneway:1` y en el sentido del tránsito (`DRIVE_LEFT=false`: antihoraria; si se dibujó a mano al revés, se da vuelta). También sirve cualquier tramo común (p. ej. `calle`) con el tilde **🔄 Es una rotonda** en Propiedades (`props.rotonda` → `junction=roundabout`; hacerlo a mano con `junction=roundabout` en "Otras etiquetas" da lo mismo): `addUser` lo da vuelta si está cerrado y gira al revés del tránsito. Un trazo cerrado que se pueda rutear (rotonda, manzana) queda cerrado en el grafo (`addUser`: el último punto es el mismo nudo que el primero). Las calles se pegan al anillo a ≤ 6 m de cada vértice; Guiarme (`makeSteps`) cuenta como **una** salida los nudos seguidos pegados a la misma calle. Las calles viejas de OSM que atraviesan el centro siguen ahí: se cortan con Correcciones. Prueba: `tests/ui_rb.py`.

## Pendientes conversados con Hugo (en orden sugerido)

1. Ordenar el menú Más en grupos (Actividad / Mapa y edición / Grupo y seguridad / Herramientas), sin "modo experto".
2. Una sola pieza para los paneles flotantes (Medir, Trazar ruta, Calcar, Editar puntos, Puertas, Modo vuelo): cerrar, achicar, z-index y modo noche iguales.
3. Pasar a un Web Worker los cálculos pesados: el horizonte para Bici y Kayak, las orillas y el armado de la red de calles.
4. Links de grupo y seguimiento que venzan, con cambio de clave. Los mensajes ya van cifrados con AES-GCM y la clave viaja en el `#` del link; falta escribir el modelo de amenazas.
5. Ideas presentadas, sin respuesta todavía: "niebla de exploración" (para hacer con su señora), que ▶ Guiarme siga con la vuelta. (El tramo "a mano" ya está: en Trazar ruta, cada tramo puede ir 🚶 a pie o 📏 en línea recta, `PL.lm`, y Rutas lo respeta con `RT.legOv`.)
6. Partir `index.html` en módulos que GitHub vuelva a juntar en un solo HTML. Recién ahora que hay pruebas; no es urgente.

## Quién y cómo trabajamos

- Usuario: Hugo (profe de educación física y entrenador de triatlón en Ushuaia). Escribe en castellano rioplatense; la app, los textos y los comentarios del código también van en rioplatense.
- Prueba todo en el teléfono: Brave para Android (Samsung S26 Ultra). Manda capturas o videos de pantalla. En Android no hay herramientas de desarrollador: cualquier diagnóstico tiene que estar **adentro de la app** (una tarjeta o un botón de "copiar").
- Si Hugo pega código o un prompt que viene de otra conversación, **primero mirá cómo está el repo ahora** y después actuá. No lo apliques a ciegas.
- **GitHub es la única fuente de verdad.** Arrancá siempre desde lo que está en `main`, nunca desde una copia vieja de otra conversación. Ya pasó: dos versiones de Mi plan se separaron y hubo que unirlas a mano.

## Filosofía de las apps (todas iguales)

- **Un solo `index.html`** con el CSS y el JS adentro. Sin dependencias externas ni build. Funciona sin conexión.
- Hosting: GitHub Pages en `profehugotdf.github.io/<repo>/`. Lo que se sube a `main` se publica solo, en un minuto.
- Pensada para el celular: botones grandes, tolerante a pantallas apagadas y a cortes de señal.
- **No perder datos nunca.** Si guardar falla, que se vea en pantalla, y la sesión no se descarta. Nada de `catch(e){}` mudos en lo que guarda.
- Cambios aditivos: no tocar lo que ya anda (poses, fórmulas calibradas, claves de almacenamiento) salvo que el pedido sea justo eso.

## Cómo entregar un cambio

1. Leer el código que se va a tocar (y lo que lo usa) antes de editar.
2. Si es un bug, primero reproducirlo con una prueba (Node con el pedazo de JS, o Playwright con la página). Después arreglarlo y ver que la prueba pase.
3. Chequear la sintaxis de cada `<script>` (por ejemplo con `node -e "new Function(código)"` o `node --check` sobre el JS extraído).
4. Si la app muestra un número de versión, subirlo y anotar en el comentario de historial **qué se cambió y por qué** (incluido lo que dijo o mostró Hugo).
5. Commit en castellano, directo a `main`, y avisarle a Hugo en pocas líneas qué cambió y cómo probarlo en el teléfono.

## Lo usan otras personas

Además de Hugo, usan las apps su primo, su hermano y compañeros, cada uno en su teléfono y con sus datos (que quedan solo en ese teléfono).

- **Nada personal en el código.** Nada de valores por defecto pensados para Hugo: peso, edad, umbrales, calibraciones de sus equipos, su ciudad, su nombre en los ejemplos. Lo personal se pregunta o se toma del perfil compartido (`entrenamiento_perfil`, `entrenamiento_umbrales`), y si no hay nada, se usa un valor neutro.
- **Los cambios en cómo se guardan los datos tienen que leer lo viejo** (migrar), nunca empezar de cero ni borrar. Una actualización les llega a todos al instante.
- Lo que depende de un equipo (rodillo, sensor, ergómetro) tiene que decir qué hace falta y cómo calibrarlo, para quien no lo tiene configurado.

## Ecosistema compartido (mismo origen profehugotdf.github.io)

Todas las apps comparten `localStorage` (unos 5 MB en total para todas) y pueden leer las claves de las otras.

- `entrenamiento_forma_registro`: `[{fecha:'AAAA-MM-DD', deporte, tss, id, calorias?}]`. Es la Forma combinada (CTL/ATL/TSB con EWMA). Cada app hace upsert **por id** y **nunca** pisa las entradas de otra. La fecha es **local**: no usar `toISOString().slice(0,10)`, porque corre el día (bug que ya pasó).
- `entrenamiento_umbrales`: `{ritmoUmbralCarreraSegKm, pulsoUmbralCarrera, ftpBici, pulsoUmbralBici, pulsoUmbralKayak, historial}`. Se leen como respaldo cuando la app no tiene uno propio. Al escribir, leer el objeto entero y tocar solo lo propio.
- `entrenamiento_perfil`: `{pesoKg, fechaNacimiento, sexo, historialPeso…}`. Mismo criterio que umbrales.
- Resúmenes que lee Mi plan: `correr_sesiones`, `bici_sesiones`, `kayak_sesiones`, `fuerza_sesiones`, `rumbo_sesiones`. Lo pesado (muestras, tracks) va a IndexedDB, y en localStorage queda un resumen sin muestras (`_resumen:true`) con la misma clave.
- TSS:
  - Correr y Kayak: `100 × horas × (valor/umbral)²`.
  - Bici: potencia normalizada/FTP.
  - Fuerza: sRPE de Foster (`RPE × min / 6`).
  - Rumbo: NGP con pendiente para correr, potencia estimada/FTP para bici.
  - Una salida grabada por Rumbo **y** por la app dedicada cuenta una sola vez, la de la dedicada.
- Rumbo abre las otras apps con `#rumbo=` en el link:
  - Bici, Correr y Kayak: `z` + base64url de JSON comprimido con deflate-raw. Bici y Correr reciben el mismo paquete (gpx con la altura, escenas, horizonte, cerros, suelo y `land`: qué hay a cada costado cada 25 m: uso del suelo, casa más cercana con pisos y distancia, tipo de camino); Kayak recibe `app:'kayak'`, puntos, orillas y perfil, horizonte y cerros.
  - Mi plan: base64 de `{v,s:[sesiones]}`, sin comprimir.
- **Costa de OSM para limpiar el relieve** (`coastSea(bb)`, `coastSeaFn(ways)`, `demSinMar(f,sea)`, `t3Flat`): el relieve (AWS Terrarium, de radar) trae picos falsos sobre el mar (barcos, muelles). Se baja a 0 m lo que OpenStreetMap (`natural=coastline`, tierra a la izquierda del sentido del tramo) dice que es mar. Se usa en `kySend` (orillas y horizonte para Kayak), `bkSend` (horizonte para Bici/Correr) y en el 3D (se abre enseguida y se aplana cuando llega la costa). Guarda en `kv` la clave `coast:s,w,n,e`. El paquete de Kayak lleva `mar:1` si se aplicó. Devuelve "no se sabe" (null) a más de 4 km de la costa o sin costa, y entonces no toca nada. Solo mar, no lagos. Prueba: `tests/ui_coast.py`.
- **Muelles y barcos sobre el relieve** (`elemMask(list)`, `demSinElems`): lo que se define como muelle o barco (Calcar u OpenStreetMap, `ELEMK`) reemplaza al relieve de abajo (0 m): contorno cerrado = adentro o a ≤ 5 m; línea = a ≤ 12 m (muelle), 8 m (velero, lancha) o 30 m (buques). `kySend` busca los `elems` **antes** de las orillas y se los aplica a `demS` y al horizonte. Además `kyShores` pide que la tierra siga siéndolo a +12, +45 y +90 m: un barco o muelle angosto sobre el agua no es orilla. `coastSea.why` dice por qué no se pudo bajar la costa (sin internet, OpenStreetMap no respondió, sin costa en la zona) y el paquete de Kayak lo lleva como `marWhy` cuando `mar` es 0. Prueba: `tests/ui_orilla.py`.
- `edif` (paquete de Kayak): edificios de la costa de OpenStreetMap (`edifCollect`, `edifQ`, `edifFromOsm`, `edifRect`): `[altura m, real 0/1, lat, lon, ancho, fondo, rumbo° del lado largo]`, rectángulo orientado de menor área, hasta `EDIF_R` = 1500 m de la ruta y `EDIF_MAX` = 900 (los más cercanos). Altura real si trae `height` o `building:levels` (×3 + 1); si no, típica del tipo (`EDIF_H`) con `real` 0. Se salta lo de menos de 20 m². Sin internet o si tarda más de 55 s, no va (no frena el envío). Prueba: `tests/ui_edif.py`.
- `calles` (paquete de Kayak): calles de OpenStreetMap (`callesCollect`, `callesQ`, `callesFromOsm`): `[clase, [[lat,lon]…]]`, clase 1 avenida o ruta (suele ser la costanera), 2 calle, 3 servicio o huella, 4 peatonal, sendero o ciclovía (`CALLE_CLASE`); sin escaleras; simplificadas a 2,5 m; hasta `CALLES_R` = 1500 m de la ruta, `CALLES_MAX` = 500 tramos y `CALLES_PTS` = 7000 puntos (los más cercanos). Misma regla que `edif`: sin internet o a los 55 s no va y no frena el envío. Los acantilados no viajan (Kayak los saca de la pendiente del perfil). Prueba: `tests/ui_edif.py`.
- `elems` (paquete de Kayak; Bici y Correr lo van a leer igual): infraestructura con posición real, `{k:'muelle'|'puente'|'tunel'|'terraplen'|'desmonte', n:nombre, a:altura m|null, m:1 si es a mano, d:distancia a la ruta, p:[[lat,lon]…≤40]}`. Sale de `elCollect()` (OpenStreetMap con `elOsmQ` + lo marcado con Calcar de esos tipos, `ELEMK`); lo manual pisa lo de OSM a menos de 40 m; corredor de 900 m, máx. 300. Los tipos de `ELEMK` no entran al ruteo (`NOROUTE`) ni al mapa vectorial. Talud estándar 1:2 lo pone la app que dibuja (Kayak: `ELEM_TALUD`); la altura es la típica salvo que se cargue "Altura" en Calcar. Prueba: `tests/ui_elem.py`. Mantener el formato igual en las tres apps. Barcos (`BARCOK`): velero, carguero, **naval** (🛡️ buque de las fuerzas navales, típico de la base de Ushuaia), crucero, lancha, encallado; "Altura" es el largo. Cada app que dibuja necesita su largo típico por tipo (Kayak: `BARCO_LARGO`): un tipo nuevo acá no se ve allá hasta agregarlo. Prueba: `tests/ui_naval.py`.
- `infra` (paquete de Bici y Correr): puentes, túneles, terraplenes y desmontes pasados a **tramos del recorrido**, porque esas apps miran por el camino: `[[tipo, desde m, hasta m, lado, altura m|null],…]` (`infraDeElems`, `infraCollect`, `INFRA_K`). Lado 0 = por el propio camino (a ≤ 10 m del eje), 1 = izquierda de la marcha, −1 = derecha. Mismos `elems` que Kayak (OSM + Calcar), corredor de 150 m, tope de 40 s; si falla no frena el envío. Prueba: `tests/ui_infra.py`.
- Hay una app de Backup (`profehugotdf.github.io`) que exporta y restaura localStorage e IndexedDB de todas.
