# Revisión de fuentes del documento

**Actualización:** el [estudio ampliado](research/ESTUDIO.md) ha localizado y extraído 2.312 identificadores únicos a una lista local. Las secciones siguientes conservan los resultados de las primeras inspecciones; ya no describen por sí solas el estado final de la investigación.

Fecha: 17 de octubre de 2026. Inspección de páginas públicas mediante herramienta web; no se extrajeron ni publicaron identificadores de emisiones. Una consulta fallida no demuestra que un sitio esté caído, y la ausencia de una licencia visible no demuestra por sí sola una infracción.

| Fuente | Resultado de la inspección | Incorporación |
| --- | --- | --- |
| [Shickat](https://shickat.online/) | HTML con directorio y entradas etiquetadas como canales comerciales, incluidos Movistar y DAZN. No se verificó permiso de redistribución en el contenido consultado. | Pendiente de autorización verificable; no es una M3U directa. |
| [NEW ERA](https://k2k4r8lm8tkmuxbc8lkmq1in3v0oya1p6pe9o5bu0hu30br5ko08k2gb.ipns.inbrowser.link) | La herramienta web no pudo consultar el destino. | Formato y permisos no verificados. |
| [ELCANO principal](https://ipfs.io/ipns/elcano.top) | La herramienta web no pudo consultar el destino. | Formato y permisos no verificados. |
| ELCANO alternativas IPNS 1 y 2 (URLs completas en el documento original) | Ninguna pudo consultarse con la herramienta web. | Formato y permisos no verificados. |
| [ELCANO web alternativa](https://vacaionesenelmar.xo.je/) | La herramienta web no pudo consultar el destino. | Formato y permisos no verificados. |
| [Ace Stream UI](https://acestreamui.app/) | Respuesta HTML con contenido insuficiente en la extracción. | No se verificaron M3U ni licencia. |
| [DVB P](https://dvb-p.com/channels/) | Respuesta HTML con contenido insuficiente en la extracción. | No se verificaron M3U ni licencia. |
| [MisterChire](https://www.misterchire.com/) | Página HTML con aviso de bloqueador de anuncios e interfaz de búsqueda. | No se verificaron M3U ni permiso; no se sortearon controles. |
| [Ciriaco](https://ciriaco.netlify.app/) | Agenda HTML de eventos con referencias a múltiples operadores, incluidos canales de pago. | No es M3U; permiso de redistribución no verificado. |
| [Platinsport](https://platinsport.com) | Error de consulta de la herramienta web. | Formato y permisos no verificados. |
| [Overtakefans](https://overtakefans.com/f1-live-stream/sky-sport-f1-live-stream-via-ace-player/) | Página HTML de Sky Sport F1 vía Ace Player; la herramienta devolvió contenido indexado antiguo. | No es M3U; disponibilidad actual y permiso no verificados. |
| [Myfootball](https://myfootball.pw) | Error de consulta de la herramienta web. | Formato y permisos no verificados. |
| [PimpleTV](https://www.pimpletv.ru/) | Página HTML dedicada a emisiones deportivas. | No se verificaron M3U ni permiso de redistribución. |

## Resultado

No se ha verificado en esta revisión una fuente directa con permiso de publicación que permita activar canales reales en GitHub Pages siguiendo el alcance del documento original. La lista pública continúa con los ejemplos ficticios, sin afirmar que sean emisiones operativas.

El trabajo de inspección está realizado y no requiere que el usuario vuelva a proporcionar los mismos enlaces. Para incorporar una fuente concreta falta verificar el permiso del titular y su contrato técnico; acceder públicamente a una página no establece ese permiso. Las fuentes no verificadas no se han marcado artificialmente como `authorized: true`.

La infraestructura de generación y publicación está operativa. Este informe no certifica derechos ni disponibilidad de vídeo y no sustituye una prueba desde la TV.

## Segunda comprobación: conexión directa y DNSLink

Se consultaron las cinco direcciones señaladas también desde el equipo, fuera de la herramienta web, con límite de 2 MiB y timeout de 15 segundos por conexión:

- NEW ERA en `inbrowser.link`: HTTP 403.
- ELCANO principal y las dos alternativas de `ipfs.io`: HTTP 429.
- Web alternativa `vacaionesenelmar.xo.je`: timeout.

La consulta DNS TXT de `_dnslink.elcano.top` devolvió:

```text
dnslink=/ipns/k51qzi5uqu5dgg9al11vomikugim0o1i3l3fxp3ym3jwaswmy9uz8pq4brg1u9
```

Ese nombre IPNS es diferente de las dos alternativas anotadas en el documento inicial. Es un dato de resolución DNS, no una playlist ni una prueba de disponibilidad del contenido.

Se hizo una comprobación adicional mediante `dweb.link` para ese nombre actual y el nombre IPNS de NEW ERA; ambas devolvieron HTTP 429. No se reintentaron las peticiones ni se resolvieron captchas o controles de acceso. Los códigos observados no permiten atribuir el fallo con certeza al editor, al gateway o a un intermediario de red.

Resultado: se encontró la referencia DNSLink actual de ELCANO, pero no se obtuvo el cuerpo de una lista. Ningún canal real se añadió a la publicación. La siguiente comprobación técnica posible es resolver el nombre con un nodo IPFS nativo; esta sesión no ha instalado ni ejecutado uno. No debe confundirse el nombre IPNS resuelto con una URL M3U compatible con OTT Navigator.

Referencia del mecanismo: [documentación oficial de IPNS](https://docs.ipfs.tech/concepts/ipns/).
