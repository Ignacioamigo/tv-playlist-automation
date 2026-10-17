# TV automatizada · OTT Navigator + Ace Stream

Lista M3U organizada por secciones, recopilada de siete catálogos públicos. Python 3.12 o posterior y Kubo para resolver las fuentes IPNS. GitHub Actions hace la actualización diaria sin depender de tu ordenador.

**URL corta para OTT Navigator:** <https://da.gd/Q6oqM>

**URL directa:** <https://ignacioamigo.github.io/tv-playlist-automation/canales.m3u>

La publicación de los catálogos recopilados está activada por petición expresa del usuario. La lista corregida separa Content IDs e infohashes; su recuento se puede consultar en `status.json`. La lista inicial contenía **2.312 cadenas hexadecimales únicas**, sin las dos entradas ficticias del ejemplo. El número puede cambiar al actualizar las fuentes. Validar la estructura no garantiza que una emisión esté activa, que tenga pares ni que todos los identificadores correspondan a canales diferentes.

## Configurar la TV

1. Abrir OTT Navigator → Ajustes → Proveedor → añadir una playlist M3U por URL. Los textos pueden variar por versión.
2. Introducir `https://da.gd/Q6oqM` y guardar. Si ya estaba añadido, pulsar **Actualizar** una vez.
3. Comprobar los grupos: LA LIGA, HYPERMOTION, LIGA DE CAMPEONES, DAZN, MOVISTAR DEPORTES y el resto.
4. Para reproducir entradas `acestream://`, el motor Ace Stream debe estar instalado y funcionar en la TV. Abrir Ace Stream Engine antes de volver a OTT Navigator y mantenerlo ejecutándose en la TV: las entradas por infohash utilizan su endpoint HTTP local. Probar primero una emisión directamente en el motor y después desde OTT Navigator.

La cabecera `#EXTM3U refresh="3"` pide recarga cada tres horas. La FAQ de OTT Navigator lo documenta desde v1.6.6.1; hay que verificar el comportamiento en la versión y TV concretas, especialmente después de suspender el dispositivo.

## Actualización automática

El workflow [Update authorized TV playlist](https://github.com/Ignacioamigo/tv-playlist-automation/actions) se ejecuta cada día a las **07:17 Europe/Madrid**, al subir cambios a `main` y mediante **Run workflow**. Las pull requests ejecutan pruebas y validación sin descargar ni desplegar catálogos.

1. Comprueba la lista guardada y ejecuta los tests.
2. Descarga Kubo 0.43.1 de su release oficial y comprueba el SHA-512.
3. Restaura las últimas copias válidas de las fuentes.
4. Resuelve los nombres IPNS actuales de NEW ERA y ELCANO. Descubre el bundle vigente de Ace Stream UI, consulta Overtakefans y descarga la revisión actual de tres Gists.
5. Conserva la diferencia entre Content IDs e infohashes, elimina duplicados del mismo tipo y organiza por secciones.
6. Valida y publica `docs/canales.m3u` mediante GitHub Pages, conservando la misma URL.

GitHub puede retrasar ejecuciones y desactiva la programación de repositorios públicos tras 60 días sin actividad. Revisar Actions periódicamente.

## Fuentes y copias de respaldo

`config/remote-sources.json` distingue `enabled` (recopilar) y `publish` (incluir en la publicación por decisión del usuario). Las siete fuentes están habilitadas para ambas operaciones. Este campo expresa una decisión de publicación, no una certificación de derechos de terceros. No incluir credenciales, URLs privadas ni emisiones cuya publicación no esté permitida.

Cada descarga válida se guarda en `.research/source-cache/`. GitHub Actions conserva esa carpeta mediante caché entre ejecuciones; si la caché no existe, se usan las copias iniciales de `data/source-snapshots/`. Si una fuente falla y existe una copia válida, se mantienen sus enlaces sin bloquear las actualizaciones del resto. El informe marca esa fuente con `cached: true` y conserva el error de descarga.

Si una fuente publicable falla sin respaldo válido, o fallan todas las descargas, se cancela la publicación y Pages mantiene el último despliegue correcto. No se sustituye la lista con una demo ni con una lista vacía. Un respaldo puede contener identificadores antiguos: mantiene disponibilidad de la lista, no garantiza reproducción.

Los errores 403/429 no se sortean ni se reintentan. Overtakefans falló desde los runners en las primeras pruebas, aunque funcionó desde el equipo; su respaldo evita perder los enlaces ya recopilados.

## Secciones

`config/sections.json` configura las reglas y el orden. Cada bloque tiene un separador `# ===== SECCIÓN =====` y sus entradas comparten `group-title` para OTT Navigator. Se consideran los nombres alternativos de un mismo ID; los casos sin coincidencia quedan en OTROS / SIN CLASIFICAR. Se conservan las variantes con ID diferente.

## Ejecutar localmente

```bash
python3 -m unittest discover -s tests -v
python3 scripts/refresh_sources.py --ipfs-bin /ruta/a/ipfs
python3 scripts/validate_playlist.py docs/canales.m3u
python3 -m http.server 8000 --directory docs
```

Abrir <http://localhost:8000/canales.m3u>. Desde la TV se necesita la IP local del ordenador, con ambos dispositivos en la misma red. Detener el servidor con Ctrl+C. No hace falta mantenerlo funcionando para utilizar la URL pública.

El actualizador utiliza un repositorio IPFS temporal, con API y gateway en loopback y sin listeners Swarm; detiene el nodo al terminar. Las descargas HTTPS restringen dominios, redirecciones y destinos DNS, verifican TLS y limitan tamaño y tiempo. Nunca se reproduce vídeo ni se ejecuta código obtenido de las fuentes.

Los scripts originales `build_playlist.py` y `config/sources.json` conservan el ejemplo local del MVP para pruebas. **No son el proceso de actualización de producción**: el workflow utiliza `refresh_sources.py` y no ejecuta el generador de la demo.

## Informes y diagnóstico

- `docs/status.json`: generación publicada, recuentos, grupos, hash y fuentes que utilizaron respaldo.
- Artefacto `refresh-report` de cada ejecución: informe de ese intento, incluso si falla; retención de 14 días.
- `.research/refresh-status.json`: informe local.
- [Estudio de las fuentes](research/ESTUDIO.md): resultados de la investigación inicial; sus recuentos son históricos.
- [REGISTRO_TV.md](REGISTRO_TV.md): pruebas pendientes de reproducción, refresco y suspensión en la TV real.

Ante cortes, comparar sesiones de 15 minutos en YouTube, Ace Stream y OTT Navigator, y repetir con Ethernet si es posible. Una lista actualizada no corrige una emisión sin pares ni un problema de Wi-Fi.

## Publicación y referencias

El repositorio usa **Settings → Pages → Source → GitHub Actions**. El workflow tiene lectura del repositorio para construir y permisos `pages: write` e `id-token: write` solo para desplegar. No necesita tokens personales ni un servidor propio.

El enlace corto es una redirección externa: si falla, usar la URL directa. El acceso público a una fuente no demuestra por sí solo permiso de redistribución. No se han verificado los derechos de terceros ni la reproducción individual de las emisiones.

- [FAQ oficial de OTT Navigator](https://ottnav.github.io/faq.html).
- [GitHub: programación y zonas horarias](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
- [GitHub: despliegues de Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

## Corrección de «cannot get transport file»

Se detectó y corrigió una conversión incorrecta del catálogo estático de Ace Stream UI: su campo `infohash` se había tratado como Content ID. La propia aplicación solicita `get_content_id` al motor antes de abrir un enlace `acestream://`. No se puede sustituir esa conversión copiando el mismo hexadecimal.

Ahora los Content IDs explícitos siguen como `acestream://...`; los infohashes utilizan el endpoint documentado `http://127.0.0.1:6878/ace/getstream?infohash=...`. Esa dirección se abre en la TV y requiere que Ace Stream Engine esté ejecutándose allí con el puerto HTTP predeterminado. No se intenta acceder al localhost del runner de GitHub. Las copias antiguas de Ace Stream UI se migran al leerlas para evitar reintroducir el error desde la caché.

No se ha comprobado físicamente este cambio en la TV del usuario. Corrige la representación de los identificadores, pero no recupera emisiones retiradas ni garantiza pares disponibles. Si falla una entrada, comparar el mismo identificador en Ace Stream directamente permite distinguir un problema del origen de uno de integración.

Referencia: [parámetros Content ID e infohash en la documentación oficial de Ace Stream](https://docs.acestream.media/developers/start-playback/).

## Logos de canales

El generador escribe `tvg-logo` en todas las entradas y conserva los logos declarados por las M3U de origen. El actualizador de logos cruza nombres normalizados con `picons_dobleM` y el catálogo de `iptv-org`, sin mezclar Movistar LaLiga con DAZN LaLiga ni cambiar la numeración de sus variantes. Descarga las imágenes PNG y comprueba estado HTTP, firma y dimensiones antes de alojarlas en `docs/logos/`.

Los nombres de canal no siempre bastan para identificar una marca. Cuando no hay coincidencia inequívoca o imagen válida, se utiliza un icono neutro de TV; no se inventa un logo. `docs/logo-status.json` detalla cuántas entradas tienen logo identificado y cuáles quedan pendientes. La comprobación automática acredita descarga y correspondencia por nombre, no una revisión visual de cada marca ni del renderizado de la TV.

El workflow revisa los logos en cada actualización y conserva los archivos anteriores mediante caché para que una lista aún cacheada en la TV no pierda sus imágenes. Las fuentes y URLs originales de cada imagen se registran en `config/logo-index.json`. Si OTT Navigator muestra imágenes antiguas después de actualizar el proveedor, comprobar si su versión ofrece recarga o limpieza específica de la caché de logos; los textos exactos del menú dependen de la versión.

Fuentes del catálogo: [picons_dobleM](https://github.com/davidmuma/picons_dobleM) y [API iptv-org](https://github.com/iptv-org/api).

## Reducir errores y comparar fuentes

La lista completa conserva todos los enlaces recopilados, pero las referencias de NEW ERA y ELCANO aparecen primero dentro de cada sección. El criterio es la procedencia del catálogo, no una prueba de reproducción. Así se evita situar por delante copias históricas por una simple ordenación alfabética.

También se publica una lista separada en <https://ignacioamigo.github.io/tv-playlist-automation/directos.m3u>, limitada a esas dos fuentes y actualizada por el mismo workflow. No elimina ni sustituye el catálogo completo. Todas sus entradas requieren Ace Stream: «directos» se refiere a las fuentes de catálogo, no a un vídeo HTTP independiente del motor. Puede usar el último respaldo si una descarga falla, como la lista completa.

La investigación detectó que algunas referencias retiradas de NEW ERA seguían presentes en Gists y por eso reaparecían al fusionar todo. La lista reducida excluye esas copias por procedencia; no se debe presentar como una lista de canales comprobados o garantizados.

Para comprobar archivos de transporte con un motor ejecutándose en el mismo equipo:

```bash
python3 scripts/check_transport.py --engine http://127.0.0.1:6878 --playlist docs/directos.m3u --max-items 10
```

El comprobador consulta `get_version`, `get_network_connection_status` y `get_media_files`. Distingue Content ID e infohash, limita los tiempos y no inicia vídeo. Si el motor informa `connected=false`, detiene el estudio sin marcar canales como caídos. Resolver un transporte tampoco garantiza vídeo ni estabilidad.

En la prueba local se utilizó un contenedor temporal Android 3.2.17. Ninguna de las diez muestras resolvió a tiempo; el motor informó `connected=false` y hubo errores de conexión/resolución dentro del entorno. El resultado es inconcluso y no describe la TV del usuario. No se ha eliminado ningún enlace por ese ensayo. El contenedor se detuvo al finalizar y el resumen está en [research/transport-diagnostic.json](research/transport-diagnostic.json).

Los pasos para medir estabilidad y comparar con la televisión están en [ESTUDIO_ESTABILIDAD.md](ESTUDIO_ESTABILIDAD.md).
