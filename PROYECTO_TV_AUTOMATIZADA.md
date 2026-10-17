# Proyecto TV automatizada — OTT Navigator + Ace Stream + GitHub

> **Documento de arranque para una sesión de desarrollo en GitHub / GitHub Copilot**  
> Versión: 1.0 · Fecha: 17 de octubre de 2026 · Idioma: español

## 0. Objetivo y contexto real

Quiero construir un sistema robusto para mantener **una única lista IPTV M3U propia y actualizable** en una Smart TV con **Android TV / Google TV**, donde ya están instaladas las aplicaciones **OTT Navigator** y **Ace Stream**. La televisión se conecta actualmente por **Wi-Fi**.

### Configuración actual

1. Actualmente utilizo identificadores/enlaces Ace Stream para reproducir emisiones.
2. En mi TV tengo Ace Stream y OTT Navigator.
3. Hasta ahora mantenía una lista o documento alojado en Pastebin y lo asociaba a OTT Navigator.
4. Pastebin ya no me funciona correctamente o ha dejado de ser una solución fiable.
5. A menudo tengo que entrar en OTT Navigator y pulsar manualmente «Actualizar» sobre el proveedor/lista.
6. Quiero dejar de editar enlaces cada día, automatizar la publicación de un M3U y que OTT Navigator recargue la lista periódicamente.
7. También quiero diagnosticar interrupciones, carga lenta y congelaciones de vídeo.

**Meta**: la URL del proveedor añadida en OTT Navigator permanece fija mientras su contenido se actualiza de forma automática. Priorizar simplicidad, mantenimiento nulo, seguridad y compatibilidad con Google TV.

> **Alcance y derechos**: toda automatización de recopilación, publicación y reproducción debe utilizar emisiones y listas que tengo permiso para acceder, copiar y redistribuir. Los enlaces de referencia de webs de terceros recogidos más abajo son solo un inventario del contexto facilitado por el usuario: **no son una autorización para extraer, republicar o automatizar retransmisiones protegidas**. No incorporar motores para eludir controles de acceso, bloqueos geográficos, DRM, captchas, cuentas o límites del proveedor. Para la primera implementación utilizar entradas M3U propias/autorizadas y URLs expresamente permitidas.

---

## 1. Resumen de solución recomendada

```text
[Fuentes M3U/JSON expresamente autorizadas]      [Entradas manuales autorizadas]
                      |                                      |
                      +------------------+-------------------+
                                         |
                                  GitHub Actions
                        (programado + ejecución manual)
                                         |
                                Python 3: normalizar
                      validar -> deduplicar -> agrupar
                                         |
                                  docs/canales.m3u
                                         |
                                    GitHub Pages
                             URL HTTPS pública y fija
                                         |
                              OTT Navigator en la TV
                      recarga periódica con refresh="3"
                                         |
                         Ace Stream Engine + reproductor
```

**Primer diseño**: repositorio GitHub, script Python sin dependencias externas, archivo `config/sources.json`, workflow programado, publicación GitHub Pages y pruebas automáticas. **Evitar introducir un servidor propio** si no es necesario.

### Decisiones de arquitectura

- GitHub Actions ejecuta el trabajo **una vez al día**, más la opción manual `workflow_dispatch`.
- GitHub Pages sirve `https://USUARIO.github.io/NOMBRE_REPO/canales.m3u` si se publica la carpeta `/docs` de la rama principal (confirmar configuración real del repo).
- La primera línea del archivo es `#EXTM3U refresh="3"` para pedir a OTT Navigator una recarga cada tres horas. Este atributo está documentado para OTT Navigator desde v1.6.6.1. La actualización puede estar sujeta al comportamiento de suspensión/caché del dispositivo.
- Priorizar contenido autorizado. **No publicar credenciales, URLs firmadas, listas privadas o datos personales en GitHub Pages público.**
- Si falla una fuente, conservar la última lista válida; no sobrescribir con una lista vacía sin análisis.
- Probar primero el formato `acestream://CONTENT_ID` con la instalación concreta de OTT Navigator/Ace Stream. Si la asociación falla, investigar una representación compatible documentada. No asumir que `localhost` de un runner de GitHub sea el mismo `localhost` de la televisión.

---

## 2. Inventario de enlaces del contexto del usuario

En tres capturas de la web **Shickat** aparecen los siguientes sitios, proveedores y directorios. Se registran aquí **como referencias técnicas pendientes de evaluar individualmente**. No se asegura disponibilidad, legitimidad, licencia ni que cualquiera de ellos ofrezca una M3U compatible.

### Directorio general

- https://shickat.online/

### Fuentes vistas en las capturas

| Etiqueta en Shickat | URL | Observaciones técnicas |
|---|---|---|
| NEW ERA | https://k2k4r8lm8tkmuxbc8lkmq1in3v0oya1p6pe9o5bu0hu30br5ko08k2gb.ipns.inbrowser.link | Gateway IPNS; puede ser contenido mutable detrás de URL estable |
| ELCANO principal | https://ipfs.io/ipns/elcano.top | Gateway IPFS/IPNS; no necesariamente M3U |
| ELCANO alternativa 1 | https://ipfs.io/ipns/k51qzi5uqu5di462t7j4vu4akwfhvtjhy88qbupktvoacqfqe9uforjvhyi4wr | Dirección IPNS |
| ELCANO alternativa 2 | https://ipfs.io/ipns/k51qzi5uqu5dh5qej4b9wlcr5i6vhc7rcfkekhrxqek5c9lk6gdaiik820fecs/ | Dirección IPNS |
| ELCANO web alternativa | https://vacaionesenelmar.xo.je/ | Web alternativa que aparece en la captura |
| ACESTREAM UI | https://acestreamui.app | Sitio web; analizar su formato solo si está permitido |
| DVB P | https://dvb-p.com/channels | Directorio web |
| MISTERCHIRE | https://www.misterchire.com | Sitio web |
| CIRIACO | https://ciriaco.netlify.app | Sitio web |
| PLATINSPORT | https://platinsport.com | Sitio web |
| OVERTAKEFANS | https://overtakefans.com/f1-live-stream/sky-sport-f1-live-stream-via-ace-player | Página de emisión, **no** archivo M3U |
| MYFOOTBALL | https://myfootball.pw | Sitio web |
| PIMPLETV | https://www.pimpletv.ru | Sitio web visto en el índice de Shickat |

**Advertencia importante:** este inventario no constituye una lista de feeds autorizados. No conectar automáticamente estos dominios al extractor ni descargar/republicar sus IDs para canales de pago sin derechos. Revisar términos y permisos antes de desarrollar un conector concreto.

### Diferencia entre web, playlist y enlace Ace Stream

- Una **página HTML** puede mostrar un índice de enlaces, pero no sirve necesariamente como URL de proveedor M3U.
- Una **lista M3U** empieza típicamente por `#EXTM3U` e incluye entradas `#EXTINF` y sus URL.
- `acestream://<ID>` es un identificador de contenido para el motor Ace Stream; no es una URL HTTP alojada en Pastebin ni implica por sí misma acceso legítimo.
- Una dirección **IPNS** identifica un nombre mutable publicado mediante IPFS. Puede apuntar a HTML, texto, JSON, M3U o cualquier otro contenido; no asumir un formato.
- La TV deberá leer una **lista M3U válida** alojada en un servidor HTTP(S) y el motor Ace Stream deberá resolver sus enlaces de reproducción.

---

## 3. Documentación y enlaces oficiales de implementación

### OTT Navigator

- FAQ oficial: https://ottnav.github.io/faq.html
- FAQ en repositorio: https://github.com/ottnav/ottnav.github.io/blob/main/faq.md
- Atributo M3U documentado: `refresh="N"`. Para `refresh="3"`, la FAQ indica tres horas; verificar en tu versión.
- Opción JSON/OTC: el formato OTC permite `refresh_minutes`. No migrar a OTC en la v1 salvo necesidad.

### Ace Stream

- Productos oficiales: https://docs.acestream.net/products/
- Documentación de Ace Stream Engine para Android TV: https://acestream.readthedocs.io/en/latest/applications/android/acestream_engine_for_android_tv/
- App Android TV en Google Play: https://play.google.com/store/apps/details?id=org.acestream.core.atv
- Guía oficial de reproducción del motor: https://docs.acestream.media/developers/start-playback/
- API de exportación de playlists del motor: https://wiki.acestream.media/Playlist_API
- Repositorio oficial Ace Stream Engine Android: https://github.com/acestream/acestream-engine-android

### GitHub

- GitHub Actions, sintaxis de workflow y cron: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- Eventos programados: https://docs.github.com/en/actions/reference/events-that-trigger-workflows#schedule
- GitHub Pages: https://docs.github.com/en/pages
- Configurar una fuente de publicación para Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- Permisos automáticos del `GITHUB_TOKEN`: https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication
- Gestión de secretos: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
- Python: https://docs.python.org/3/
- Formato cron: https://crontab.guru/

### IPFS e IPNS

- Introducción al sistema IPNS: https://docs.ipfs.tech/concepts/ipns/
- Gateway público IPFS: https://ipfs.io/

**Nota**: las páginas externas cambian. Verificar el estado actual y las versiones antes de basarse en una opción concreta.

---

## 4. Requisitos funcionales

### Imprescindibles (MVP)

- [ ] Crear un repositorio `tv-playlist-automation`.
- [ ] Configurar una fuente de contenidos M3U propia o autorizada.
- [ ] Leer entradas de fuentes explícitamente declaradas, no rastrear Internet.
- [ ] Aceptar solo esquemas URL válidos y los orígenes aprobados.
- [ ] Normalizar nombres e información `#EXTINF`.
- [ ] Detectar y eliminar duplicados exactos; preservar variantes claramente diferentes.
- [ ] Generar archivo M3U determinista con cabecera de recarga.
- [ ] Publicar en URL fija.
- [ ] Programar generación una vez al día y permitir ejecución manual.
- [ ] Validar sintaxis del archivo generado antes de publicarlo.
- [ ] Mantener última versión válida si todas las fuentes fallan.
- [ ] Probar la recarga automática en OTT Navigator y documentar los pasos reales de la versión instalada.

### Deseables después del MVP

- [ ] Informe `status.json` sin secretos: fecha de generación, fuentes válidas, número de canales, errores.
- [ ] Logs cortos y legibles de ejecución.
- [ ] Detección de cambios para evitar commits innecesarios.
- [ ] Backups de las últimas listas válidas.
- [ ] Grupos por categoría (`TV`, `Radio`, `Pruebas`) y país cuando los metadatos lo permitan.
- [ ] Aliases y normalización de nombres.
- [ ] Orden configurable.
- [ ] Herramienta CLI local para validar una playlist.
- [ ] Alertas por fallo del workflow sin publicar tokens.
- [ ] Pruebas unitarias y de integración sobre datos sintéticos.
- [ ] Evaluar almacenamiento privado autenticado si aparecen fuentes privadas.

### Fuera de alcance de la v1

- Scraping indiscriminado o extracción masiva de webs sin permiso.
- Eludir DRM, restricciones territoriales, captchas, paywalls o autenticación.
- Guardar tokens o URLs de acceso privado en un repositorio público.
- Reemitir/retransmitir vídeo desde un servidor externo.
- Verificación automática de disponibilidad real de cada emisión P2P.
- Cambios masivos y automáticos de configuración dentro de Android TV.

---

## 5. Estructura propuesta del repositorio

```text
tv-playlist-automation/
├── .github/
│   └── workflows/
│       └── update-playlist.yml
├── config/
│   └── sources.json
├── examples/
│   └── canales-demo.m3u
├── scripts/
│   ├── build_playlist.py
│   └── validate_playlist.py
├── tests/
│   └── test_playlist.py
├── docs/
│   ├── .nojekyll
│   └── canales.m3u
├── .gitignore
├── README.md
└── PROYECTO_TV_AUTOMATIZADA.md
```

`docs/` es el directorio elegido para GitHub Pages cuando se publica desde la rama principal. El archivo `.nojekyll` evita transformaciones innecesarias.

---

## 6. Ejemplo de configuración de fuentes

Archivo `config/sources.json`:

```json
{
  "refresh_hours": 3,
  "timeout_seconds": 15,
  "max_source_bytes": 2097152,
  "sources": [
    {
      "id": "demo_local",
      "type": "local_m3u",
      "path": "examples/canales-demo.m3u",
      "enabled": true,
      "authorized": true
    }
  ]
}
```

En v1 empezamos con entradas locales. Después se puede agregar un tipo `remote_m3u` **solo** para URLs directas y expresamente autorizadas. Nunca permitir destinos arbitrarios introducidos por terceros: restringir dominios, HTTPS y tamaño máximo.

Archivo `examples/canales-demo.m3u`, con valores de marcador que **no reproducen ningún canal real**:

```m3u
#EXTM3U
#EXTINF:-1 tvg-id="demo-1" group-title="Pruebas",Canal demo 1
acestream://0123456789abcdef0123456789abcdef01234567
#EXTINF:-1 tvg-id="demo-2" group-title="Pruebas",Canal demo 2
https://example.org/stream-demo.m3u8
```

Los enlaces anteriores son deliberadamente ficticios. Sustituirlos únicamente por fuentes de prueba o emisiones propias/autorizadas.

---

## 7. Código inicial: generador M3U sin dependencias

Crear `scripts/build_playlist.py`:

```python
#!/usr/bin/env python3
"""Build a deterministic M3U from explicitly authorized local M3U files."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "sources.json"
OUTPUT = ROOT / "docs" / "canales.m3u"
EXTINF = re.compile(r"^#EXTINF:.*,")
ACE_ID = re.compile(r"^acestream://[a-fA-F0-9]{40}$")


def is_usable_url(url: str) -> bool:
    # Local illustrative validator. Remote HTTPS sources should undergo
    # additional domain, license, scheme and safety checks.
    if ACE_ID.fullmatch(url):
        return True
    return url.startswith("https://") and " " not in url


def read_entries(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    if not text.lstrip().startswith("#EXTM3U"):
        raise ValueError(f"Invalid M3U header: {path}")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for idx, line in enumerate(lines):
        if EXTINF.match(line) and idx + 1 < len(lines):
            url = lines[idx + 1]
            if not url.startswith("#") and is_usable_url(url):
                yield line, url


def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    hours = int(cfg.get("refresh_hours", 3))
    if hours < 1 or hours > 23:
        raise ValueError("refresh_hours must be 1..23")
    seen = set()
    output_entries = []
    errors = []

    for source in cfg.get("sources", []):
        if not source.get("enabled", False):
            continue
        if not source.get("authorized", False):
            raise ValueError(f"Source not marked authorized: {source.get('id')}")
        if source.get("type") != "local_m3u":
            raise ValueError("v1 only supports local_m3u")
        path = (ROOT / source["path"]).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError("Source path must stay inside repository")
        try:
            for extinf, url in read_entries(path):
                if url not in seen:
                    seen.add(url)
                    output_entries.append((extinf, url))
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{source['id']}: {exc}")

    if not output_entries:
        raise RuntimeError("No valid items: existing output preserved. " + "; ".join(errors))

    text = "\n".join(
        [f'#EXTM3U refresh="{hours}"']
        + [line for entry in output_entries for line in entry]
    ) + "\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUTPUT.with_suffix(".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(OUTPUT)
    print(f"Published {len(output_entries)} entries to {OUTPUT.relative_to(ROOT)}")
    for error in errors:
        print("WARN", error)


if __name__ == "__main__":
    main()
```

**Limitaciones deliberadas del prototipo:**

- El validador solo acepta `acestream://` seguido de 40 caracteres hexadecimales o URL HTTPS simples. El formato específico de tus listas legítimas podría necesitar ampliaciones.
- La deduplicación se hace por URL, no por identidad del canal; dos URLs diferentes del mismo canal permanecen como alternativas.
- El parser es básico; para listas complejas con opciones VLC, metadatos extendidos o cabeceras auxiliares, diseñar un parser y tests específicos.
- No se hace conexión a ningún sitio ni scraping.
- No se verifica que el vídeo esté activo; se verifica estructura.
- Si no hay entradas válidas, el script falla y **no sustituye** el archivo previamente válido.

---

## 8. GitHub Actions: generación diaria automática

Crear `.github/workflows/update-playlist.yml`:

```yaml
name: Update authorized TV playlist

on:
  workflow_dispatch:
  schedule:
    - cron: '17 7 * * *'
      timezone: 'Europe/Madrid'

permissions:
  contents: write

concurrency:
  group: update-playlist
  cancel-in-progress: false

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          persist-credentials: true
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Build playlist
        run: python scripts/build_playlist.py
      - name: Check output
        run: |
          test -s docs/canales.m3u
          head -n 1 docs/canales.m3u | grep -q '^#EXTM3U'
      - name: Commit if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add docs/canales.m3u
          if git diff --cached --quiet; then
            echo "No changes"
          else
            git commit -m "chore: update authorized M3U playlist"
            git push
          fi
```

**Nota sobre horario:** GitHub documenta `timezone` para workflows programados; usar `Europe/Madrid` permite gestionar cambios de horario, sujeto a las reglas de su infraestructura. Las ejecuciones programadas pueden retrasarse, por lo que no garantizar una ejecución exacta a las 07:17. Si la instancia concreta no admite la clave `timezone`, eliminarla y usar cron UTC documentando el cambio horario. Por simplicidad se recomienda una hora no redonda y no crítica.

**Nota sobre permisos:** si `git push` falla con `403` o el repositorio tiene reglas de protección de rama, revisar `Settings → Actions → General → Workflow permissions`, permisos del token y políticas de rama. Para repositorios más protegidos, se puede publicar mediante un despliegue Pages en lugar de hacer commit automatizado sobre `main`.

**Seguridad adicional:** para producción conviene fijar las actions a hashes SHA verificados en lugar de referencias de versión; mantener permisos al mínimo y revisar actualizaciones de dependencias.

---

## 9. Crear y publicar GitHub Pages

1. Crear repositorio en GitHub llamado `tv-playlist-automation`.
2. Añadir los archivos descritos y el archivo `docs/.nojekyll` vacío.
3. Ejecutar el generador localmente para que exista `docs/canales.m3u`.
4. Subir todo a la rama `main`.
5. Ir a `Settings → Pages`.
6. En `Build and deployment`, elegir `Deploy from a branch`.
7. Seleccionar rama `main` y carpeta `/docs`.
8. Guardar y verificar que Pages se despliega correctamente.
9. La URL habitual en repositorios de proyecto será:

```text
https://TU_USUARIO.github.io/tv-playlist-automation/canales.m3u
```

10. Abrir esa URL desde un navegador y comprobar que el contenido empieza por `#EXTM3U refresh="3"`.
11. Si muestra HTML o 404, revisar la configuración Pages, ruta, capitalización y tiempo de despliegue.
12. **No usar GitHub Pages como protección de privacidad:** asumir que el archivo es públicamente legible y replicable.

### Prueba local

```bash
python3 scripts/build_playlist.py
python3 -m http.server 8000 --directory docs
```

Abrir `http://localhost:8000/canales.m3u` en el mismo ordenador. La TV no puede acceder a `localhost` de ese ordenador; para pruebas desde otros dispositivos habría que emplear su IP local y comprobar cortafuegos.

---

## 10. Configurar OTT Navigator en Android TV / Google TV

### Añadir el proveedor

1. Abrir OTT Navigator en la televisión.
2. Entrar en `Ajustes → Proveedor` (el texto exacto puede variar por versión).
3. Añadir un proveedor de tipo **playlist/M3U por URL**.
4. Pegar **la URL pública de GitHub Pages**, no el enlace del archivo en la vista HTML de github.com.
5. Guardar, actualizar una vez manualmente para comprobar la primera importación y revisar que aparecen los canales de prueba.
6. Comprobar en la información del proveedor la fecha o momento de la última actualización, si la app lo expone.
7. Dejar la cabecera `#EXTM3U refresh="3"` en la lista; comprobar que la versión instalada la reconoce.

### ¿La TV actualizará incluso apagada?

No hay garantía. Android TV puede suspender procesos en segundo plano y OTT Navigator no tiene por qué despertar el televisor. El objetivo realista es que al volver a usar la aplicación se efectúe la recarga prevista, sin necesitar pulsar manualmente «Actualizar». Verificar el comportamiento real en el modelo concreto.

### Si sigue requiriendo actualización manual

- Revisar versión instalada de OTT Navigator: `refresh` exige v1.6.6.1 o posterior.
- Confirmar que el archivo servido contiene el encabezado correcto **en la primera línea**.
- Confirmar que la URL recibe un M3U y no una página HTML/404.
- Comprobar opciones de refresco del proveedor dentro de la app.
- Reiniciar la app y observar si se hace la recarga.
- Considerar caché HTTP/CDN o que Android suspenda tareas en segundo plano.
- No implementar automatizaciones de pulsaciones en pantalla hasta descartar primero el método soportado oficialmente.

---

## 11. Ajustes sugeridos de reproducción

Estas recomendaciones son un **punto de partida**; los nombres del menú pueden variar por versión, motor y fabricante.

| Ajuste | Inicial | Si falla |
|---|---|---|
| Reproductor | Interno OTT Navigator | Probar alternativa compatible si la app lo permite |
| Decodificación | Hardware / compatibilidad | Cambiar a otro modo y comparar |
| Búfer | Mínimo para diagnosticar | Probar mayor búfer si hay pérdidas de red |
| Resolución | Fuente estable 1080p | Comparar una opción de menor bitrate |
| Ventanas PiP | Desactivadas | Mantener una sola emisión para ahorrar recursos |
| Wi-Fi | 5 GHz con buena señal | Probar 2,4 GHz si 5 GHz llega débil; Ethernet como prueba |
| Actualización M3U | Cada 3 horas | Revisar logs/fecha de recarga |
| EPG | Opcional; no es imprescindible | Deshabilitar si añade carga innecesaria |

**No existe un valor universal óptimo de búfer.** Probar 10–15 minutos con un cambio cada vez. Más búfer puede ayudar ante fluctuaciones, pero añade latencia y no corrige ausencia de pares.

### Wi-Fi: comprobaciones

1. Verificar que la TV esté conectada a una red de 5 GHz con intensidad estable; si está lejos del router, comparar con 2,4 GHz.
2. Reiniciar TV y router si se observan desconexiones reproducibles.
3. Evitar descargar archivos grandes mientras se reproduce la emisión de prueba.
4. Si se puede, hacer una prueba temporal con **Ethernet** para separar problemas de Wi-Fi de problemas de fuentes P2P.
5. No comprar repetidores ni dispositivos adicionales antes de comprobar el cuello de botella.
6. La latencia, fluctuación y pérdidas de paquetes pueden importar más que la velocidad máxima anunciada.

### Ace Stream Engine

- Confirmar que esté instalado y sea una versión adecuada para Android TV desde los canales oficiales.
- Permitir que el motor funcione mientras OTT Navigator reproduce una emisión autorizada.
- Mantener almacenamiento libre y evitar que la TV cierre el motor por falta de recursos.
- No exponer puertos del motor públicamente ni desactivar el firewall sin un diagnóstico específico.
- No asumir que un fallo en P2P lo resolverá una configuración de vídeo del reproductor.

---

## 12. Diagnóstico sistemático de cortes

**Prueba 1: plataforma convencional**. Reproducir 15 minutos de YouTube en 1080p. Si falla, priorizar Wi-Fi, congestión, hardware y sistema operativo.

**Prueba 2: fuente autorizada en Ace Stream directamente**. Reproducir 15 minutos la misma emisión. Si YouTube va bien y Ace Stream se corta, revisar disponibilidad de pares, estabilidad de origen y motor.

**Prueba 3: la misma emisión en OTT Navigator**. Si va bien en la app Ace Stream y mal en OTT Navigator, revisar asociación con motor, hardware decode y búfer de OTT.

**Prueba 4: repetir mediante Ethernet temporal**. Si mejora significativamente, el Wi-Fi era parte del problema.

**Prueba 5: variar solo un parámetro por vez**. Registrar fecha, duración, fuente, tipo de interrupción y ajuste usado.

### Tabla de observaciones

| Síntoma | Hipótesis razonables | Siguiente comprobación |
|---|---|---|
| Se queda cargando antes de empezar | Inicio de pares P2P, fuente inactiva, asociación con motor | Probar directamente en Ace Stream |
| Se para cada pocos minutos | Pérdidas Wi-Fi, insuficiente aporte de pares, búfer | Probar Ethernet / fuente estable / otro búfer |
| El audio sigue pero el vídeo se congela | Decodificación/render | Probar otro modo de hardware decode |
| Canales no aparecen | Lista inválida, sin actualizar, URL equivocada | Abrir M3U desde navegador y revisar logs |
| La lista carga pero no se reproduce | Motor Ace Stream, protocolo o fuente | Prueba directa en motor; revisar formato |
| Actualiza manualmente, no sola | Recarga automática no aplicada o app suspendida | Revisar `refresh`, versión y suspensión |
| GitHub Pages muestra 404 | Despliegue o ruta incorrecta | Revisar Settings → Pages y Actions |

### Registro sugerido

```text
Fecha/hora:
TV / Android TV versión:
Versión OTT Navigator:
Versión Ace Stream:
SSID / banda (2.4 o 5 GHz):
Distancia aproximada al router:
Fuente de prueba autorizada:
Duración antes del primer corte:
Comportamiento (buffer / congelación / error):
Reproductor y modo de decodificación:
Configuración de búfer:
Comparación con Ethernet:
Resultado:
```

---

## 13. Pruebas y criterios de aceptación

### Pruebas del generador

- [ ] El archivo resultante inicia exactamente por `#EXTM3U refresh="3"`.
- [ ] Cada entrada `#EXTINF` tiene una URL no vacía a continuación.
- [ ] No hay duplicados idénticos.
- [ ] No se publican credenciales, emails ni tokens.
- [ ] La ejecución es determinista: mismo input → mismo output.
- [ ] Si faltan fuentes, queda intacta la última playlist válida.
- [ ] Un archivo inválido no se publica accidentalmente.
- [ ] Los logs explican cuántos canales se han incorporado y cuáles se han rechazado.

### Pruebas de automatización

- [ ] La opción `Run workflow` aparece en GitHub Actions.
- [ ] La ejecución manual termina correctamente.
- [ ] Se genera/actualiza `docs/canales.m3u`.
- [ ] GitHub Pages publica el cambio sin modificar la URL pública.
- [ ] La programación diaria se dispara normalmente, aceptando posibles retrasos.

### Pruebas de TV

- [ ] OTT Navigator abre la URL pública M3U.
- [ ] Se importa el canal demo autorizado.
- [ ] La app puede usar Ace Stream como motor para entradas Ace Stream compatibles y autorizadas.
- [ ] Tras modificar una entrada de prueba, la nueva versión aparece sin borrar/crear el proveedor.
- [ ] La recarga periódica funciona en los ciclos reales de uso de la TV.
- [ ] Se documenta si la TV dormida retrasa la actualización hasta abrir la app.

---

## 14. Seguridad, privacidad, derechos y fiabilidad

- Utilizar **solo contenido propio o permitido**.
- No interpretar que una URL públicamente visible da permiso para capturarla y redistribuirla.
- Mantener público el repositorio únicamente si los datos incluidos son publicables.
- Si hay credenciales o suscripciones privadas, no se deben introducir en Pages o archivos públicos; diseñar otra arquitectura de distribución privada.
- Evitar el scraping sin límites, incluyendo sobrecarga de sitios.
- Respetar robots, términos y límites de fuentes si se aprueba un futuro conector.
- En fuentes remotas permitidas, implementar validación de DNS, HTTPS, allowlist, límites de tamaño/tiempo, redirects y ausencia de SSRF.
- Nunca ejecutar código obtenido de una playlist o web externa.
- No almacenar IPs P2P, identificadores personales ni datos sensibles en logs públicos.
- No abrir el puerto 6878 hacia Internet por comodidad. El endpoint local es una superficie de control del motor; analizar red y permisos antes de cualquier exposición.
- Tratar GitHub Actions como infraestructura compartida con cuotas, no como garantía de hora exacta.
- Backups y rollback deben evitar quedarse sin canales al fallar una fuente.

---

## 15. Fases de desarrollo sugeridas para GitHub Copilot

### Fase A — MVP funcionando

1. Crear el repositorio y archivos base.
2. Generar y validar M3U local desde una lista demo.
3. Añadir workflow manual y cron.
4. Configurar Pages y confirmar descarga desde URL fija.
5. Dar de alta el proveedor en OTT Navigator y probar refresco.

### Fase B — Robustez

1. Pruebas unitarias con listas válidas/inválidas.
2. Control de errores y fuentes caídas.
3. Logs, `status.json` y validación de schema.
4. Reporte de ejecución.
5. Mejorar agrupación y alias de nombres.

### Fase C — Nuevas fuentes autorizadas

1. Definir contrato por tipo `remote_m3u` o `remote_json`.
2. Permitir únicamente dominios aprobados y fuentes con licencia/permiso.
3. Descargar de forma segura con timeout, límite de tamaño y backoff.
4. Añadir tests con fixtures locales; nunca depender de una web real en pruebas unitarias.
5. No ampliar automáticamente a los sitios del inventario de Shickat sin verificar permisos.

### Fase D — Optimización de TV

1. Medir estabilidad en 5 GHz y Ethernet.
2. Registrar versión de OTT y Ace Stream.
3. Probar hardware decoding y búfer individualmente.
4. Documentar mecanismo de refresco observado.
5. No cambiar la arquitectura hasta demostrar que existe un cuello de botella.

---

## 16. Prompt listo para pegar en GitHub Copilot / sesión de desarrollo

> Actúa como un ingeniero senior de Python, CI/CD y Android TV. Quiero crear un repositorio `tv-playlist-automation` que genere una playlist M3U válida y pública para OTT Navigator desde fuentes **propias o explícitamente autorizadas**. Lee `PROYECTO_TV_AUTOMATIZADA.md` por completo. Implementa la estructura indicada, un parser robusto, `config/sources.json`, generación determinista, validación, tests con datos sintéticos, logging de errores, workflow programado para `Europe/Madrid`, ejecución manual, publicación en GitHub Pages y README paso a paso. Conserva la última lista válida cuando fallen entradas. Incluye `#EXTM3U refresh="3"`. No raspees terceros, no extraigas enlaces de emisiones protegidas, no eludas DRM/controles, no publiques listas privadas. Señala cualquier supuesto que necesite verificar en la TV. Primero construye el MVP sin dependencias externas, ejecútale tests y documenta la URL final en formato plantilla para que yo la complete tras crear el repo.

---

## 17. FAQ de operación

**¿Por qué reemplazar Pastebin?**  
Porque un repositorio y GitHub Pages permiten versionar, validar, regenerar y distribuir una única lista con URL fija sin depender de un paste editado a mano.

**¿Se actualizará la lista sola cada día?**  
Sí, si GitHub Actions ejecuta correctamente el workflow y el repositorio mantiene su configuración. Las ejecuciones programadas pueden retrasarse.

**¿Se actualizará sola en la televisión?**  
OTT Navigator documenta `refresh="3"`; hay que comprobar versión, caché y comportamiento en segundo plano de la TV. No prometer funcionamiento durante suspensión profunda.

**¿IPNS reemplaza a GitHub Pages?**  
No necesariamente. IPNS permite nombres mutables, pero GitHub Pages simplifica la entrega HTTPS de nuestro M3U final. Las URL IPNS vistas en fuentes de terceros no equivalen a feeds aprobados.

**¿Es necesario alojar Ace Stream en GitHub?**  
No. GitHub aloja solo el archivo de texto M3U. El motor de reproducción sigue en la TV.

**¿Hace falta una VPN?**  
No como requisito técnico para la playlist. No añadir VPN o proxies como supuesto remedio universal para buffering.

**¿Servirá para arreglar cortes de cualquier emisión?**  
No. Una lista actualizada no incrementa el número de pares P2P ni corrige una fuente caída. Diagnosticar por separado infraestructura, reproductor y origen.

**¿Conviene publicar el archivo como GitHub Raw?**  
Para una URL de distribución estable y con ruta propia, preferir Pages. Los enlaces a la vista HTML de GitHub no son playlists válidas.

**¿Qué ocurre si la app no entiende `acestream://`?**  
Confirmar versiones e integración; evaluar representaciones documentadas por Ace Stream para el motor ejecutándose en el dispositivo correcto. No hardcodear IPs ni localhost de un sistema diferente.

---

## 18. Checklist final de entrega

- [ ] Repo GitHub creado y con este documento.
- [ ] Código y tests en `main`.
- [ ] M3U público de prueba sin derechos de terceros.
- [ ] GitHub Actions programado y manual probado.
- [ ] URL GitHub Pages comprobada en navegador.
- [ ] Lista añadida en OTT Navigator.
- [ ] Recarga automática observada en uso real.
- [ ] Ace Stream integrado para enlaces autorizados de prueba.
- [ ] Estabilidad comparada en Wi-Fi 5 GHz y Ethernet.
- [ ] No hay secretos publicados ni redistribución no autorizada.

## 19. Resultado deseado para esta sesión

Entregar el repositorio funcional, con instrucciones comprensibles para una persona que no quiere mantener servidores y un proceso que no requiera entrar a editar manualmente Pastebin o el proveedor de la televisión. **Mantener los detalles no verificados como pendientes, en lugar de inventar configuraciones**.
