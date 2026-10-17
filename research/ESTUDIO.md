# Estudio ampliado de fuentes y listas

Revisión del 17 de octubre de 2026. Se inspeccionaron las 14 direcciones del inventario (contando Shickat), se revisaron referencias indexadas y se descargaron recursos HTTP y después se resolvieron y descargaron las fuentes IPFS con un nodo nativo temporal.

**Resultado local: 2312 identificadores Ace Stream únicos**, desde 4331 entradas tras deduplicar dentro de cada recurso; 2019 repeticiones eliminadas entre recursos y formatos.

La M3U resultante está en `.research/canales-candidatos.m3u`; la procedencia de cada aparición queda en `.research/extracted.json`. Estos archivos locales no se incluyen en Git ni se publican en Pages. Se ha validado la estructura M3U, no la reproducción de las emisiones ni los derechos de publicación.

## Recursos de los que se obtuvieron identificadores

| Recurso descargado | IDs únicos dentro del recurso |
| --- | ---: |
| [Ace Stream UI · catálogo estático](https://acestreamui.app/static/js/main.b5a296a7.js) | 1531 |
| [Overtakefans](https://overtakefans.com/f1-live-stream/sky-sport-f1-live-stream-via-ace-player/) | 12 |
| [Gist 430bd27d303a095a5b200cbddb8efd5f](https://gist.githubusercontent.com/jahoyos/430bd27d303a095a5b200cbddb8efd5f/raw/2af0698929eaed954b4075782053feeb7fef0365/Canales.m3u) | 302 |
| [Gist e596fead1e99b92c38e47f87b0808ba8](https://gist.githubusercontent.com/tristansp-arch/e596fead1e99b92c38e47f87b0808ba8/raw/3047238da380f90b9079666e6faaa4bee30e4f62/lista_stremio.m3u) | 401 |
| [Gist 1704843b4b26589687f2adf03456c50c](https://gist.githubusercontent.com/Redrusiam/1704843b4b26589687f2adf03456c50c/raw/459bfa05b69c41b15b10c67045aeac2af3fa4ec9/gistfile1.m3u) | 391 |

Los tres Gists son copias de terceros encontradas al buscar NEW ERA y ELCANO. Contienen etiquetas que los mencionan, pero no se ha comprobado que sus autores sean los editores originales ni que todas las entradas sigan vigentes. Los totales por recurso se solapan: sumarlos no da el total global único.

Ace Stream UI incorpora una lista inicial en su JavaScript. Su búsqueda dinámica utiliza el motor del dispositivo (`localhost:6878`, endpoint `/search?page_size=1000`); la web por sí sola no es una fuente M3U HTTP fija. La extracción local aprovecha el catálogo estático, sin conectarse a un motor de la TV.

## Comprobación directa de todas las direcciones

| Fuente | Resultado desde el equipo | IDs detectados en la página raíz |
| --- | --- | ---: |
| [SHICKAT](https://shickat.online/) | URLError | No evaluable |
| [NEW ERA](https://k2k4r8lm8tkmuxbc8lkmq1in3v0oya1p6pe9o5bu0hu30br5ko08k2gb.ipns.inbrowser.link) | HTTP 403 | No evaluable |
| [ELCANO principal](https://ipfs.io/ipns/elcano.top) | HTTP 429 | No evaluable |
| [ELCANO alternativa 1](https://ipfs.io/ipns/k51qzi5uqu5di462t7j4vu4akwfhvtjhy88qbupktvoacqfqe9uforjvhyi4wr) | HTTP 429 | No evaluable |
| [ELCANO alternativa 2](https://ipfs.io/ipns/k51qzi5uqu5dh5qej4b9wlcr5i6vhc7rcfkekhrxqek5c9lk6gdaiik820fecs/) | HTTP 429 | No evaluable |
| [ELCANO web alternativa](https://vacaionesenelmar.xo.je/) | URLError | No evaluable |
| [ACESTREAM UI](https://acestreamui.app) | HTTP 200; html | 0 |
| [DVB P](https://dvb-p.com/channels) | URLError | No evaluable |
| [MISTERCHIRE](https://www.misterchire.com) | URLError | No evaluable |
| [CIRIACO](https://ciriaco.netlify.app) | URLError | No evaluable |
| [PLATINSPORT](https://platinsport.com) | URLError | No evaluable |
| [OVERTAKEFANS](https://overtakefans.com/f1-live-stream/sky-sport-f1-live-stream-via-ace-player) | HTTP 200; html | 12 |
| [MYFOOTBALL](https://myfootball.pw) | HTTP 403 | No evaluable |
| [PIMPLETV](https://www.pimpletv.ru) | URLError | No evaluable |

La cifra 0 de Ace Stream UI corresponde al HTML inicial: los 1.531 identificadores se localizaron después dentro del JavaScript enlazado. Los fallos de red no se interpretan como ausencia de canales.

Comprobaciones adicionales: Shickat agotó el timeout; Ciriaco devolvió un reinicio de conexión; DVB P no resolvió mediante el DNS de este equipo. La herramienta web sí pudo mostrar contenido indexado de Shickat, Ciriaco, MisterChire y PimpleTV. Eso no equivale a haber descargado sus recursos dinámicos ni una M3U actual.

Se localizó además una referencia indexada a una antigua M3U de NEW ERA en IPNS (`data/listas/lista_iptv.m3u`), pero no se confirmó su descarga ni vigencia. [Referencia de descubrimiento](https://www.mediavida.com/foro/hard-soft/el-hilo-de-acestream-708012/74). No se añadió al recuento de fuentes descargadas.

## Repetir el estudio

```bash
python3 scripts/inspect_sources.py
python3 scripts/extract_candidates.py
python3 scripts/validate_playlist.py .research/canales-candidatos.m3u
python3 -m unittest discover -s tests -v
```

Para incorporar los archivos ya descargados de IPFS sin repetir peticiones HTTP: `python3 scripts/extract_candidates.py --merge-ipfs`.

El inspector limita tamaños, concurrencia y cantidad de recursos enlazados. No ejecuta JavaScript, no reintenta errores HTTP ni usa credenciales o proxies. La extracción genera únicamente archivos locales de investigación. El workflow de publicación no ejecuta estos scripts ni incorpora sus resultados.

Los inventarios y resultados resumidos están en `research/`. Las URL de los Gists están fijadas a revisiones concretas para hacer reproducible la descarga; no son feeds que sigan automáticamente la última revisión. La URL del bundle de Ace Stream UI también puede cambiar al actualizar la aplicación.

## Resultado de la consulta IPFS nativa

Se descargó Kubo 0.43.1 para macOS ARM64 desde la release oficial de `ipfs/kubo` en GitHub y se verificó el SHA-512 publicado. Se utilizó un repositorio aislado en `.research/tools/repo`, API y gateway limitados a loopback y sin listeners Swarm. El nodo se detuvo al terminar.

- NEW ERA resolvió al snapshot `/ipfs/QmNPHsCoXSjN56mxWymaAbPbWTdfPZFa63otJAHTdzmFfU`.
- Ambas alternativas ELCANO resolvieron al mismo snapshot `/ipfs/Qma1Yfo8aKs8Vev1Fs3QFnepWro8buUgQicTaZjTrKRC4g`. No son dos catálogos distintos.
- La referencia actual encontrada mediante DNSLink no terminó de resolver dentro del plazo de 25 segundos; no se afirma que las alternativas correspondan a esa referencia actual.
- Tras un primer timeout al listar `data/listas`, una segunda consulta de NEW ERA completó el listado y la descarga.

| Fuente | Archivos descargados | Entradas M3U | IDs únicos por catálogo |
| --- | --- | ---: | ---: |
| NEW ERA | `lista_fuera_iptv.m3u`, `lista_iptv.m3u`, `lista_kodi.m3u`, `listaplana.txt`, `index.html` | 372 en cada M3U | 371 |
| ELCANO (alternativas 1 y 2) | `hashes.m3u`, `hashes_acestream.m3u`, `hashes_kodi.m3u`, `hashes.json`, `hashes.txt` | 70 en cada M3U | 70 |

Las distintas M3U representan los mismos IDs con `acestream://`, el endpoint local `/ace/getstream?id=...` o el plugin Horus de Kodi. La extracción de investigación los convierte a `acestream://` para unificar el recuento; no intenta conectarse a esas direcciones locales ni ejecutar plugins.

Los resultados nativos y CIDs de cada archivo están en `ipns-native.json`, `ipfs-files.json` y `new-era-native.json`. Los originales están en `.research/ipfs/`. Las referencias IPNS son mutables y los snapshots CID representan únicamente el contenido recuperado en esta revisión.

Para repetir la inspección de estos snapshots, con el binario Kubo y el repositorio aislado ya preparados: `python3 scripts/inspect_ipfs.py`. Este script depende de los snapshots resueltos registrados, limita la exploración y detiene el nodo incluso ante un error. No instala Kubo ni configura un servicio persistente. El inspector HTTP mantiene un máximo de 2 MiB por recurso; la descarga puntual del HTML de NEW ERA permitió hasta 8 MiB y recuperó aproximadamente 6,7 MB.

**Validación final:** 2.312 entradas en la M3U fusionada y 17 pruebas automáticas correctas. La cifra corresponde a identificadores únicos, no a 2.312 canales distintos ni a emisiones activas comprobadas.
