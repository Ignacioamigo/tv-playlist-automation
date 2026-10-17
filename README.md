# TV automatizada · OTT Navigator + Ace Stream

Genera una lista M3U pública y estable desde archivos locales propios o autorizados. Python 3.12 o posterior, sin paquetes externos ni servidores permanentes.

**Estado:** proyecto publicado en [GitHub](https://github.com/Ignacioamigo/tv-playlist-automation), con Pages activo y URL M3U comprobada (HTTP 200 y dos entradas válidas). Los dos canales de ejemplo son ficticios: permiten comprobar la importación, pero no reproducen vídeo. Las emisiones autorizadas reales y las pruebas físicas en la TV están pendientes.

**URL para OTT Navigator:** <https://ignacioamigo.github.io/tv-playlist-automation/canales.m3u>

## Empezar

Desde la carpeta del proyecto:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_playlist.py
python3 scripts/validate_playlist.py docs/canales.m3u
python3 -m http.server 8000 --directory docs
```

Abrir <http://localhost:8000/canales.m3u>. Detener el servidor con Ctrl+C. Desde la TV hay que usar la IP local del ordenador, por ejemplo `http://192.168.1.20:8000/canales.m3u`, con ambos dispositivos en la misma red y el cortafuegos permitiendo la conexión.

## Añadir tus canales

1. Sustituir los ejemplos de `examples/canales-demo.m3u` por enlaces que tengas permiso para publicar.
2. Declarar los dominios HTTPS exactos (también de logos) en `allowed_stream_hosts` de `config/sources.json`. No se admiten comodines. Los enlaces Ace Stream no necesitan dominio.
3. Para añadir otro archivo, crear otra fuente `local_m3u`, con `id` único, ruta dentro del proyecto, `enabled: true` y `authorized: true`.
4. Ejecutar generador y validador; revisar el M3U antes de subirlo a GitHub.

```m3u
#EXTM3U
#EXTINF:-1 tvg-id="mi-canal" group-title="TV",Mi canal
https://mi-dominio.example/emision.m3u8
```

Añadir `mi-dominio.example` a los dominios aprobados para utilizar ese ejemplo. La configuración inicial solo permite `example.org`.

El parser admite duración numérica, nombre, `tvg-id`, `tvg-name`, `tvg-logo` y `group-title`, con atributos entre comillas dobles. Normaliza espacios, Unicode y duración a `-1`; conserva comas en nombres y atributos. Permite comentarios simples entre metadatos y URL. Rechaza directivas extendidas no soportadas para evitar eliminarlas silenciosamente.

Se admiten identificadores `acestream://` de 40 caracteres hexadecimales y HTTPS con dominio aprobado. Se rechazan HTTP, credenciales, parámetros de consulta, fragmentos, IPs literales, puertos especiales y extensiones de URL del reproductor. Es una política conservadora: una URL legítima con parámetros requiere diseñar una ampliación antes de usarla. El generador nunca conecta con las emisiones ni descarga fuentes remotas.

No hay detección universal de secretos: un token dentro de una ruta o un dato personal en el nombre puede parecer texto normal. Revisa siempre archivos, metadatos y permisos de redistribución antes de publicarlos. Todo el contenido de `docs/` será público.

## Qué ocurre al generar

- Cabecera exacta `#EXTM3U refresh="3"` con la configuración inicial; `refresh_hours` acepta enteros entre 1 y 23.
- Orden estable por grupo, nombre y URL. Se eliminan entradas completamente idénticas tras normalizar. Se conservan variantes con URL o metadatos diferentes.
- Todas las fuentes activas deben estar autorizadas, caber en el límite de tamaño y ser válidas por completo. Una fuente con errores impide sustituir la lista, incluso si otras funcionan.
- Escritura mediante archivo temporal y reemplazo atómico. Si el contenido no cambia, no se reescribe el M3U.
- `docs/status.json` registra el intento, recuentos y hash, sin copiar URLs ni errores originales. Su fecha cambia en cada ejecución; el M3U sigue siendo determinista.
- Un fallo devuelve código 1. En GitHub se detiene el despliegue y continúa disponible la última publicación correcta. El informe de ese intento fallido se consulta en Actions; el `status.json` público seguirá siendo el de la última publicación.
- Los errores de configuración se abortan antes de procesar fuentes y pueden dejar el informe anterior intacto. No se mantienen backups adicionales; las fuentes se versionan con Git y Pages conserva la publicación mientras no haya otro despliegue correcto.

La ejecución diaria vuelve a generar los archivos declarados. **No descubre nuevos enlaces ni sustituye automáticamente enlaces caducados.** Una futura fuente remota necesita su propio conector autorizado y controles de red; no está implementada en esta versión.

## Publicar en GitHub Pages

El workflow usa el despliegue oficial mediante Actions, por lo que en Pages hay que seleccionar **GitHub Actions**. Es una adaptación respecto al ejemplo de publicación desde rama del documento de partida; evita commits automáticos y permisos de escritura sobre el código.

1. Crear en tu cuenta un repositorio vacío llamado `tv-playlist-automation`. Revisa la visibilidad: los archivos publicados por Pages se deben considerar públicos.
2. Subir el proyecto a la rama `main`. Si todavía no tienes Git inicializado:

   ```bash
   git init -b main
   git add .
   git commit -m "Implement authorized TV playlist automation"
   git remote add origin https://github.com/TU_USUARIO/tv-playlist-automation.git
   git push -u origin main
   ```

3. En GitHub, abrir **Settings → Pages → Build and deployment → Source → GitHub Actions**.
4. Abrir **Actions → Update authorized TV playlist → Run workflow**, elegir `main` y ejecutar. El workflow también comprueba pull requests y ejecuta generación y despliegue tras cada push a `main`.
5. Revisar que los trabajos `build` y `deploy` terminan correctamente. El entorno `github-pages` mostrará la dirección publicada.
6. Abrir la URL fija y comprobar la primera línea:

   ```text
   https://TU_USUARIO.github.io/tv-playlist-automation/canales.m3u
   ```

El repositorio puede llamarse de otra manera: sustituye también el nombre en la URL. Una vista de archivo de `github.com` no sirve como URL del proveedor.

La ejecución está programada cada día a las **07:17 Europe/Madrid**, con cambios de horario gestionados por GitHub. GitHub puede retrasar u omitir ejecuciones bajo carga y desactiva programaciones en repositorios públicos tras 60 días sin actividad. Revisar Actions periódicamente; esta limitación impide prometer mantenimiento literalmente nulo.

El workflow tiene permisos de lectura para construir y solo `pages: write` e `id-token: write` para desplegar. No necesita tokens personales ni secretos de fuentes. Las actions usan etiquetas de versión; para endurecer la cadena de suministro se pueden fijar a SHA verificados y mantenerlos actualizados.

Si hay un 404, comprobar nombre del repositorio, rama `main`, configuración de Pages y ejecución del despliegue. Si falla el despliegue por permisos, revisar la política del repositorio/organización y las aprobaciones del entorno `github-pages`.

## Configurar la televisión

1. En OTT Navigator, abrir Ajustes → Proveedor y añadir una playlist M3U por URL. Los nombres exactos dependen de la versión instalada.
2. Introducir la URL HTTPS de Pages, guardar y actualizar manualmente la primera vez.
3. Comprobar que aparecen las entradas. Los ejemplos incluidos no reproducen contenido real.
4. Sustituir una entrada autorizada, subir el cambio y esperar un despliegue correcto; comprobar después la recarga del mismo proveedor.
5. La FAQ documenta `refresh="3"` desde v1.6.6.1 como recarga cada tres horas. Verificarlo en el uso real: Android puede suspender la aplicación y retrasar la actualización hasta volver a abrirla.
6. Probar una emisión Ace Stream autorizada primero directamente en el motor y después desde OTT Navigator. La asociación de `acestream://` depende de las versiones y del dispositivo; queda pendiente de validación física.

GitHub solo publica texto: el motor Ace Stream debe ejecutarse en la TV. `localhost` del ordenador o de GitHub Actions no es la TV.

## Diagnosticar cortes

Comparar sesiones de 15 minutos: YouTube a 1080p, emisión autorizada directamente en Ace Stream y la misma emisión en OTT Navigator. Si es posible, repetir mediante Ethernet. Cambiar un solo ajuste cada vez: modo de decodificación, búfer o bitrate. Consultar el apartado 12 de [PROYECTO_TV_AUTOMATIZADA.md](PROYECTO_TV_AUTOMATIZADA.md) para interpretar los síntomas.

Anotar las pruebas en [REGISTRO_TV.md](REGISTRO_TV.md). Una lista actualizada no corrige una fuente P2P sin pares.

## Verificación de entrega

- Implementados: configuración local, parser, validación CLI, generación determinista, deduplicación, control de orígenes, conservación ante fallos, informe, pruebas sintéticas y workflow.
- Comprobado localmente: 20 pruebas automáticas, generación de dos entradas ficticias y validación del resultado.
- Comprobado en GitHub: repositorio público creado, Pages activo, workflows por push y ejecución manual correctos y URL pública válida.
- Pendientes: observar la primera ejecución programada, aportar emisiones autorizadas reales y probar recarga/reproducción en la TV. La ejecución manual validada está en [Actions](https://github.com/Ignacioamigo/tv-playlist-automation/actions/runs/39035177657).

## Referencias verificadas

- [FAQ oficial de OTT Navigator: atributos de playlist](https://ottnav.github.io/faq.html).
- [GitHub: programación, zonas horarias y limitaciones](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
- [GitHub: despliegues personalizados de Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

No se ha conectado ni extraído contenido de los directorios de terceros inventariados en el documento original.

La inspección de todos los enlaces inventariados está documentada en [REVISION_FUENTES.md](REVISION_FUENTES.md), con resultados y limitaciones por fuente.

## Investigación ampliada de enlaces

El [estudio de todas las fuentes](research/ESTUDIO.md) obtuvo **2.312 identificadores únicos** de recursos públicos HTTP e IPFS descargados. Se generó una lista local en `.research/canales-candidatos.m3u`, con procedencia por entrada y validación de estructura. Son candidatos sin comprobación de reproducción ni derechos; no se incorporan automáticamente a Pages. Los scripts y resultados resumidos están incluidos en el repositorio.

Las listas de candidatos se organizan automáticamente por secciones, siguiendo el ejemplo facilitado: LA LIGA, HYPERMOTION, LIGA DE CAMPEONES, 1RFEF, DAZN y MOVISTAR DEPORTES, más categorías para el resto del catálogo. Cada bloque tiene un separador `# ===== SECCIÓN =====` y sus entradas comparten `group-title` para OTT Navigator. Las reglas y el orden se ajustan en `config/sections.json`; se consideran los nombres alternativos de cada ID y los casos sin coincidencia quedan en OTROS / SIN CLASIFICAR. La agrupación se aplica al regenerar o fusionar candidatos y conserva los 2.312 identificadores.
