# TV automatizada · OTT Navigator + Ace Stream

Lista M3U organizada por secciones, recopilada de siete catálogos públicos. Python 3.12 o posterior y Kubo para resolver las fuentes IPNS. GitHub Actions hace la actualización diaria sin depender de tu ordenador.

**URL corta para OTT Navigator:** <https://da.gd/Q6oqM>

**URL directa:** <https://ignacioamigo.github.io/tv-playlist-automation/canales.m3u>

La publicación de los catálogos recopilados está activada por petición expresa del usuario. La lista inicial contiene **2.312 identificadores únicos**, sin las dos entradas ficticias del ejemplo. El número puede cambiar al actualizar las fuentes. Validar la estructura no garantiza que una emisión esté activa, que tenga pares ni que todos los identificadores correspondan a canales diferentes.

## Configurar la TV

1. Abrir OTT Navigator → Ajustes → Proveedor → añadir una playlist M3U por URL. Los textos pueden variar por versión.
2. Introducir `https://da.gd/Q6oqM` y guardar. Si ya estaba añadido, pulsar **Actualizar** una vez.
3. Comprobar los grupos: LA LIGA, HYPERMOTION, LIGA DE CAMPEONES, DAZN, MOVISTAR DEPORTES y el resto.
4. Para reproducir entradas `acestream://`, el motor Ace Stream debe estar instalado y funcionar en la TV. Probar primero una emisión directamente en el motor y después desde OTT Navigator.

La cabecera `#EXTM3U refresh="3"` pide recarga cada tres horas. La FAQ de OTT Navigator lo documenta desde v1.6.6.1; hay que verificar el comportamiento en la versión y TV concretas, especialmente después de suspender el dispositivo.

## Actualización automática

El workflow [Update authorized TV playlist](https://github.com/Ignacioamigo/tv-playlist-automation/actions) se ejecuta cada día a las **07:17 Europe/Madrid**, al subir cambios a `main` y mediante **Run workflow**. Las pull requests ejecutan pruebas y validación sin descargar ni desplegar catálogos.

1. Comprueba la lista guardada y ejecuta los tests.
2. Descarga Kubo 0.43.1 de su release oficial y comprueba el SHA-512.
3. Restaura las últimas copias válidas de las fuentes.
4. Resuelve los nombres IPNS actuales de NEW ERA y ELCANO. Descubre el bundle vigente de Ace Stream UI, consulta Overtakefans y descarga la revisión actual de tres Gists.
5. Normaliza las representaciones de los IDs, elimina duplicados y organiza por secciones.
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
