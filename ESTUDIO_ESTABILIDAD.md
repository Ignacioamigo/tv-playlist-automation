# Estudio de estabilidad y selección de enlaces

## Qué está comprobado y qué falta medir

La automatización actual valida formato, duplicados, descarga de catálogos y logos. No prueba la reproducción P2P, el audio/vídeo ni la estabilidad desde la televisión. Un catálogo actualizado puede seguir incluyendo una emisión retirada o que solo esté activa durante un evento.

Se corrigió una conversión incorrecta entre infohash y Content ID. El diagnóstico posterior debe usar el tipo de identificador original y no confundir un error de resolución del transport file con falta de búfer o un fallo de vídeo.

## Prueba inicial recomendada

Seleccionar entre 5 y 10 canales que se utilicen habitualmente y entre 2 y 3 alternativas identificadas de cada uno. No agrupar automáticamente dos canales solo porque compartan marca: conservar número, país y programación; una variante no identificada queda pendiente.

1. Elegir una emisión activa, en la misma TV y conexión habituales.
2. Anotar cuánto tarda cada alternativa en producir la primera imagen. Como criterio experimental, registrar timeout de arranque a los 45 segundos; no declarar por ello que el enlace esté retirado.
3. Hacer una prueba corta de 60–90 segundos para detectar fallos evidentes.
4. A los mejores candidatos hacerles una prueba visible de 15 minutos, anotando interrupciones, duración total detenida, audio y vídeo. Recibir datos no demuestra por sí solo reproducción correcta.
5. Repetir en tres ocasiones y horarios, incluidos momentos de emisión del evento si el enlace es eventual. Los resultados tienen fecha: no son garantías permanentes.
6. Comparar una vez la misma alternativa directamente en Ace Stream y en OTT Navigator.
7. Si hay cortes, repetir una alternativa mediante Ethernet temporal, si está disponible, antes de comprar equipo o cambiar varios ajustes.

No reproducir alternativas en paralelo durante la comparación: competirían por la conexión y los recursos. Una prueba de 60 segundos para cada una de las 2.345 entradas ocuparía unas 39 horas, sin contar esperas, por lo que conviene empezar por los canales habituales.

## Datos que se pueden automatizar con Ace Stream Engine

La API permite iniciar una sesión con `format=json`, obtener `playback_url`, `stat_url` y `command_url`, consultar estado, pares, velocidad de descarga y bytes descargados, y detener la sesión al terminar.

Un comprobador local puede medir tiempo de resolución, tiempo hasta recibir datos, errores, periodos sin avance de descarga y estadísticas del motor. Necesita límites por entrada, ejecución secuencial y cierre de sesión incluso si falla la prueba. Los endpoints de control se deben restringir al motor configurado; no publicar datos de pares o direcciones personales.

Las velocidades y pares son indicadores auxiliares. Más pares no garantizan mejor vídeo; la velocidad debe interpretarse junto al bitrate y al estado del búfer. Distinguir la primera descarga para llenar el búfer de la velocidad de reproducción estable.

Medir desde GitHub Actions caracterizaría la red del runner, no el Wi-Fi ni el dispositivo del usuario. La primera opción para comparar automáticamente es un motor en un equipo local; la comprobación final debe hacerse en la TV. Si solo hay televisión, comenzar por el registro manual, sin abrir el puerto del motor a Internet.

## Clasificación propuesta

- **Preferido:** varias pruebas correctas, arranque razonable y pocos cortes observados.
- **Alternativa:** funciona, pero tarda más o presenta mayor variación.
- **Fallo reciente:** no inició o se interrumpió en una prueba concreta; se conserva para repetir.
- **Solo eventos:** solo se evalúa cuando debería emitir.
- **Sin comprobar:** aún no hay datos suficientes.

Priorizar éxito repetido, menor tiempo detenido y arranque más rápido. No eliminar automáticamente por un único fallo. No utilizar una puntuación universal basada solo en pares ni presentar la resolución declarada en el nombre como una resolución medida.

La mejora de producto sería mantener la lista completa y una selección de favoritos con las alternativas preferidas primero. La clasificación no debe modificar los identificadores ni cambiar Content ID por infohash. Los resultados del usuario solo deben publicarse si así se decide; pueden mantenerse como datos locales.

## Registro del piloto

| Fecha/hora | Canal y variante | Conexión | Reproductor | Arranque (s) | Duración | Cortes | Tiempo detenido (s) | Audio/vídeo | Error |
| --- | --- | --- | --- | ---: | --- | ---: | ---: | --- | --- |
| Pendiente | | | | | | | | | |

Cambiar un solo parámetro en cada comparación. Mantener el motor funcionando en la TV para las entradas HTTP de infohash. Revisar decodificación si el audio continúa mientras la imagen se congela. Probar un ajuste de búfer mayor solo como experimento ante interrupciones y comparar su efecto sobre cortes y latencia.

## Datos necesarios para ejecutar el piloto

- Disponibilidad de un ordenador que pueda ejecutar un motor compatible en la red local, o uso exclusivo de la TV.
- Versiones de OTT Navigator y Ace Stream Engine y modelo de TV.
- Los 5–10 canales habituales y ejemplos de alternativas que funcionan y que fallan.

No se han realizado aún pruebas de reproducción ni medidas de calidad en esta fase.

## Fuentes técnicas

- [Ace Stream: inicio, parámetros, estadísticas y cierre de sesión](https://docs.acestream.media/developers/start-playback/).
- [Ace Stream: referencia de la API](https://docs.acestream.media/developers/api-reference/).
- [FAQ de OTT Navigator](https://ottnav.github.io/faq.html).

## Ensayo de resolución realizado

Se implementó `scripts/check_transport.py` y se probó una muestra de diez entradas con un motor temporal 3.2.17 en Docker, publicado solo en loopback. No se inició vídeo. Hubo timeouts y errores «cannot get transport file», y la API del motor informó `connected=false`. Repetir con la configuración estándar del contenedor no cambió esa señal.

Este ensayo no permite clasificar los enlaces como caídos: hay un problema o limitación del entorno del motor de prueba. Los enlaces se conservan. El comprobador ya detecta esa situación antes de iniciar futuras muestras. La TV real continúa pendiente de comparación y no se afirma que tenga el mismo problema de red.

Como optimización independiente, se priorizan las fuentes directas y se publica una selección de esas fuentes aparte, sin retirar la lista completa ni atribuir a esa selección una disponibilidad medida.
