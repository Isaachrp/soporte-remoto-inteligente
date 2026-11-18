# Segundo avance: análisis previo y operación guiada

Fecha: 22 de octubre de 2026.

## Objetivo atendido

Simplificar el sistema para que el técnico seleccione un equipo y un procedimiento, consulte primero la configuración del router y revise una propuesta antes de ejecutar. Se conserva la arquitectura servidor–agente–IA y el generador PHP existente.

## Cambios entregados

| Antes | Segundo avance |
|---|---|
| Copiar sesión, referencia, identidad y puerto de administración | Seleccionar el agente conectado; obtener identidad y administración de la lectura del laboratorio |
| Escribir parámetros antes de conocer el equipo | Analizar primero; mostrar direcciones, interfaces, rutas y conteos de configuración |
| Revisar principalmente código e identificadores | Ver estado, propuesta, supuestos y motivos de incompatibilidad; detalles técnicos desplegables |
| Consultar solicitudes pegando un ID | Abrir solicitudes recientes por equipo, fecha y estado |
| Evidencia del flujo de ejecución | Evidencia con análisis inicial vinculado, nueva lectura previa, script, resultados y auditoría |

La interfaz pide una sola clave de acceso al técnico. Las credenciales del router permanecen en el agente. No se guardan en el navegador ni se envían a la IA.

## Arquitectura y recorrido

1. El agente se autentica ante el servidor y mantiene su sesión mediante heartbeat.
2. La interfaz obtiene del servidor la lista de agentes activos, sin tokens de sesión.
3. Al pulsar **Analizar equipo**, el servidor encola una lectura. El agente consulta RouterOS por API TLS o el simulador explícito de la demo.
4. El servidor recibe un snapshot con campos permitidos: identidad, versión y tablas de configuración. No acepta comandos libres.
5. Un evaluador determinista compara esa configuración con las variantes disponibles. Muestra hechos, supuestos y bloqueos. Esta recomendación inicial es una regla de compatibilidad, no una respuesta generada por IA.
6. Al confirmar la propuesta, la IA interpreta ECMP y propone el plan de acciones. El servidor valida ese plan con el catálogo y solicita una lectura nueva.
7. La versión y el estado observado determinan la variante. PHP genera el script; el servidor valida operaciones y vincula la aprobación al plan, destino, parámetros, script y snapshot.
8. El técnico autoriza o rechaza. El agente vuelve a leer antes de escribir y el servidor emite un permiso de un solo uso. Si cambió la configuración, se bloquea la ejecución.
9. El agente ejecuta operaciones nativas permitidas y realiza otra lectura. El servidor verifica y conserva la auditoría.

El análisis inicial vence para preparar solicitudes después de cinco minutos. Se puede repetir desde Equipos. Una lectura fallida no genera un script ni una tarea de escritura.

## Qué adaptación se implementó

Se selecciona la familia desde la versión observada. En v7 se reutilizan las direcciones WAN/LAN observadas y se comprueba la base exacta del laboratorio; la variante conserva interfaces y direcciones existentes. La identidad y el puerto administrativo se obtienen de la lectura. La demo v6 propone parámetros de una plantilla para puertos de trabajo vacíos.

Los gateways de la base preparada y la igualdad de costo deben confirmarse: no se pueden deducir de las rutas conectadas. `5M` es un valor de plantilla, no una medición. No se inventan datos faltantes como si hubieran sido detectados.

**Alcance real:** dos WAN de igual costo, CHR `7.24.5 (stable)`, administración `10.255.255.1/24` en ether4 y base preparada documentada. Configuraciones distintas se muestran como incompatibles. La adaptación todavía no soporta topologías arbitrarias, migración de reglas existentes ni selección entre PCC, Hotspot u otros procedimientos. La API anterior conserva los parámetros manuales para pruebas técnicas, pero no forman parte del nuevo flujo sencillo.

## Cómo probar la demo sin tocar el laboratorio

Desde PowerShell en la carpeta del proyecto:

```powershell
.\iniciar-demo.cmd
```

1. Abrir la URL mostrada. Mantener la consola abierta.
2. Introducir solamente la **clave temporal del técnico**.
3. Seleccionar el equipo y **Balancear dos conexiones a Internet (ECMP)**.
4. Pulsar **Analizar equipo**. Confirmar que aparece `lab-router`, RouterOS simulado y el puerto administrativo detectado.
5. Leer los datos y los valores propuestos; marcar la confirmación y pulsar **Preparar configuración recomendada**.
6. Esperar **Propuesta lista: falta tu autorización**. Abrir el script. En este punto no se ha escrito en el router.
7. Primero probar **Rechazar propuesta**. Volver a equipos y repetir análisis/preparación.
8. Pulsar **Autorizar y ejecutar**. Esperar **Configuración verificada con comprobaciones pendientes**.
9. Descargar evidencia y consultar el historial sin copiar identificadores.
10. Reiniciar la demo para obtener una base simulada limpia. Analizar después de aplicar también permite mostrar por qué una configuración existente requiere revisión.

Autoprueba de procesos separados, incluido el nuevo análisis guiado:

```powershell
.\iniciar-demo.cmd --self-test --port 0
```

Produce `analisis.json`, `rechazo.json`, `aprobacion.json`, `resultado.json` y `SHA256SUMS` en la carpeta `runtime/demo-...` indicada. No entregar claves, archivos `.env`, bases SQLite ni logs sin revisar.

## Cómo probar en tu laboratorio CHR

Usar la preparación de [la integración supervisada v7](24-integracion-supervisada-v7.md). El nuevo flujo sustituye su tabla de captura manual; las condiciones del laboratorio siguen vigentes.

1. Conservar las instantáneas del ensayo manual. Restaurar únicamente CHR-LAB a `10-base-agente-v7` si ya fue creada; si no, seguir la preparación del documento 24 para crearla. Restaurar una instantánea descarta los cambios posteriores de esa VM: guardar antes la evidencia necesaria.
2. Verificar cuatro interfaces y direcciones: ether1 `192.168.1.2/24`, ether2 `192.168.2.2/24`, ether3 `172.16.0.1/24`, ether4 `10.255.255.1/24`. Identidad `lab-router`, versión exacta y solo las cuatro rutas conectadas. Sin NAT/pools/servidores DHCP ni reglas anteriores del procedimiento; DHCP cliente deshabilitado.
3. Mantener ISP1 e ISP2 encendidos, el equipo Windows por administración y Lubuntu exclusivamente en LAB-LAN. Comprobar acceso administrativo y certificado `lab-local/router-ca.crt`.
4. Ejecutar `.\iniciar-lab-v7.cmd`. Introducir en el agente el token solicitado y las credenciales locales del usuario de ensayo según el documento 24. El arranque habilita explícitamente el ensayo real; no aprueba por sí mismo.
5. En la web, ingresar la clave del técnico, seleccionar el agente y **Analizar equipo**. Revisar versión, direcciones, rutas y bloqueos. Descargar el análisis.
6. Confirmar los gateways y los enlaces de igual costo. Preparar. Antes de autorizar, revisar que el script v7 contiene siete operaciones: dos NAT, dos rutas, pool, red DHCP y servidor DHCP. No debe renombrar ni agregar direcciones. Rechazar una primera propuesta es una prueba útil de ausencia de cambios.
7. Repetir y autorizar una sola propuesta. Esperar la verificación y descargar evidencia. Si aparece intervención requerida, conservar el resultado y revisar; no repetir la escritura ni borrar reglas a ciegas.
8. Comprobar desde Lubuntu la concesión en `172.16.0.0/24`, gateway `172.16.0.1`, resolución DNS y acceso a varios destinos. Registrar comandos y salidas con fecha.
9. Revisar en RouterOS ambas rutas por defecto activas y el uso de ambos enlaces con varias conexiones nuevas. Un ping aislado o una descarga única no prueba reparto ECMP.
10. Pausar ISP1, abrir conexiones nuevas y comprobar continuidad por ISP2; recuperar ISP1 y repetir a la inversa. Mantener la administración accesible. Anotar qué ocurre con conexiones existentes sin asumir que deben sobrevivir.
11. Guardar un resultado separado por prueba: esperado, observado, evidencia, aprobado/fallido/no realizado. Conservar la instantánea de base para repetir sin duplicar reglas.

La lectura de tablas valida configuración, no conectividad completa. El estado con advertencias es esperado mientras las pruebas WAN/LAN no formen parte de la verificación automática. No presentar el resultado simulado como prueba real.

## Guion para mostrar al asesor (8–10 minutos)

1. **Problema y observación (1 min):** antes el usuario debía copiar IDs y completar parámetros sin conocer el estado del equipo.
2. **Interfaz (1 min):** mostrar ingreso, selección del agente y un único procedimiento integrado.
3. **Análisis (2 min):** ejecutar lectura, explicar datos detectados frente a supuestos y mostrar un bloqueo por configuración incompatible.
4. **Arquitectura (1 min):** el agente consulta y ejecuta; el servidor coordina, valida y registra; la IA interpreta y estructura el plan; PHP genera el script validado.
5. **Supervisión (2 min):** preparar sin escribir, mostrar script, rechazar una vez y luego autorizar sobre base limpia. Explicar la nueva lectura antes de ejecutar.
6. **Resultados (1 min):** mostrar verificación, historial y evidencia descargable. Si hay prueba real, mostrar además las salidas del cliente y pruebas por ISP.
7. **Límites y siguiente paso (1 min):** adaptación controlada al laboratorio; faltan nuevas variantes y verificación automática de tráfico. No afirmar certificación productiva ni autonomía total de la IA.

Frase sugerida: “El segundo avance convierte la configuración en un flujo guiado. El sistema consulta primero el router, comprueba si una variante disponible es aplicable y prepara una propuesta trazable. La ejecución sigue requiriendo aprobación y vuelve a validar el estado del equipo”.

## Validación de código

Suite: **167 aprobadas, 1 omitida**, con una advertencia de deprecación preexistente de Starlette/AnyIO. La omitida requiere laboratorio real autorizado. Casos nuevos: selección sin secretos, lectura sin escrituras, flujo guiado con PHP, compatibilidad v7, configuración previa incompatible, vencimiento, agente desconectado y cambios después de analizar. También se comprobó el recorrido en navegador con RouterOS e IA simulados.

```powershell
$pruebasSegundo = Join-Path $PWD ('runtime\pytest-segundo-' + [guid]::NewGuid().ToString('N'))
.\.venv-mvp\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp "$pruebasSegundo"
```

No se realizaron conexiones ni escrituras al CHR real durante el desarrollo de este avance.
