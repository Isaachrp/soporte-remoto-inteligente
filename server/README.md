# Sistema central: catálogo PHP y entregas independientes

## Flujo actual (noviembre de 2026)

### IA gratuita con OpenRouter

En `server/.env` configura `ECMP_AI_MODE=openrouter` y estas variables:

```dotenv
OPENROUTER_API_KEY=tu_clave_openrouter
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_MODEL=openrouter/free
OPENROUTER_HTTP_REFERER=http://localhost
OPENROUTER_X_TITLE=Soporte remoto inteligente
```

Arranca con `server/iniciar-central.cmd --ai openrouter`, o sin `--ai` para usar el proveedor del `.env`. Reinicia el servidor tras cambiar las variables. La URL admite el endpoint completo o la base `https://openrouter.ai/api/v1`. Los encabezados de atribución son opcionales y deben usar texto ASCII.

La integración admite `openrouter/free` o modelos terminados en `:free`, solicita JSON estructurado y limita el precio de entrada y salida a cero. No cambia automáticamente a OpenAI ni a simulación. La respuesta se valida con los mismos contratos y políticas del servidor. Los modelos gratuitos tienen límites y disponibilidad variable; si no hay uno compatible se muestra el motivo y puedes reintentar o elegir manualmente. No se envían las claves a la interfaz ni se incluyen en los ejecutables.

Referencias: [router gratuito](https://openrouter.ai/docs/guides/routing/routers/free-router) y [salidas estructuradas](https://openrouter.ai/docs/guides/features/structured-outputs).

1. Cargar el diagnóstico JSON del agente. En modo OpenAI, LangGraph envía una proyección del diagnóstico (sin identidad, comentarios ni credenciales) para recomendar hasta cuatro opciones del catálogo; nunca solicita scripts a la IA. Si el proveedor falla, se informa el error y se permite reintentar o elegir manualmente.
2. Elegir configuración y completar sus parámetros. El catálogo incluye las 14 opciones del menú PHP y OpenVPN. Las plantillas de otra versión permanecen visibles con su incompatibilidad. Los datos no recogidos por el agente, como Hotspot, colas y certificados, no se consideran ausentes.
3. Revisar, autorizar y descargar el ejecutable. Los detalles del script quedan plegados. El ejecutable funciona sin servidor central.

`server/php_bridge.php` incluye los generadores existentes desde CLI y recupera su salida; únicamente convierte los saltos HTML `<br>` a saltos de línea. No modifica archivos ni comandos del generador. `PHP_EXE` configura el intérprete PHP. Los parámetros se validan en el servidor antes de invocarlo.

Las entregas del catálogo usan `php-generator-offline/1`. El técnico autoriza el **script original**, que puede cambiar o reemplazar configuración. El ejecutable pide IP, usuario y contraseña, usa API 8728 en LAN/VPN, compara el diagnóstico antes y después de la confirmación y ejecuta el script mediante `/system/script/run`. Guarda evidencia local y deja un marcador por entrega en el router para impedir repeticiones; al terminar vacía el código del marcador. Un error o desconexión se informa como ejecución parcial o incierta, sin reintentar. `script_executed` significa que RouterOS aceptó la ejecución, no que se probó el servicio ni el tráfico. API 8728 no cifra credenciales; no usar en una red no confiable.

El usuario RouterOS necesita permisos para las operaciones de la plantilla y para crear/ejecutar scripts. Tickets requiere su perfil Hotspot existente. OpenVPN requiere la CA `ca` y el servidor preparado; el `.ovpn` generado es una plantilla pendiente de certificados. Los paquetes de Tickets/OpenVPN contienen credenciales generadas o introducidas: conservar su procedencia y acceso restringido. El diagnóstico actual no permite verificar automáticamente todos estos requisitos.

ECMP V7 conserva el flujo supervisado anterior, incluida la opción de conservar coincidencias y agregar solo lo faltante. Desde el 6 de noviembre sus ejecutables usan API 8728 sin certificado, con IP, usuario y contraseña; mantienen el contrato de laboratorio y el destino 10.255.255.1. No se modificó el agente ni el generador PHP. Reinicia el servidor y vuelve a descargar la entrega para reconstruir el EXE; los ejecutables descargados anteriormente no se actualizan solos.

Validación del catálogo: generación real de las 15 opciones PHP, recorridos HTTP de autorización y descarga, respuestas de IA controladas, alteraciones, caducidad, conflicto de versiones y ejecución con doble de RouterOS; también empaquetado Windows y `--validate-only`. No equivale a ensayos en un MikroTik físico ni a una llamada real a OpenAI.

Regresión de esta ampliación: 231 aprobadas, 1 omitida y 1 fallo en `test_full_http_processes[True]`: el agente portable existente se detiene antes de abrir sesión. El recorrido con agente Python pasa. Ese portable no se modificó por quedar fuera del alcance del servidor. La construcción y validación independiente del nuevo ejecutable del catálogo pasa.

Referencias de implementación: [salidas estructuradas de OpenAI](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat) y [ejecución de scripts RouterOS](https://help.mikrotik.com/docs/spaces/ROS/pages/47579229/Scripting).

## Documentación del flujo ECMP conservado

Avance del 27 de octubre de 2026. Alcance acordado: trabajar únicamente en el
sistema central, conservar estilos y arquitectura, recibir un diagnóstico previo
y entregar instrucciones estructuradas y un ejecutable independiente. Solo ECMP.

## Arranque

Abrir `server/iniciar-central.cmd`, o ejecutar desde la raíz:

```powershell
.\server\iniciar-central.cmd
```

Se inician exclusivamente PHP y el servidor central en localhost. La consola
muestra la URL y una clave temporal para el técnico. Mantenerla abierta; Ctrl+C
cierra los dos procesos. El historial se conserva en `runtime/central/real.sqlite3`.
Si el puerto 8000 está ocupado, usar `server/iniciar-central.cmd --port 0`.

El arranque predeterminado prepara entregas para la base real CHR 7.24.5 descrita
en la documentación previa; no se conecta ni escribe en el router. La IA es
simulada explícitamente por defecto. Para reutilizar el proveedor real ya existente,
configurar su clave localmente como antes y arrancar con `--ai openai`.

Para una demostración sin router:

```powershell
.\server\iniciar-central.cmd --simulate
```

Ese modo guarda un historial separado y produce ejecutables que solo simulan.
No hay conversión automática de una entrega simulada en una entrega real.
Los lanzadores anteriores se conservan para los avances anteriores; no son
el punto de entrada de este avance.

## Uso

1. Entrar con la clave del técnico.
2. Cargar un diagnóstico JSON completo. Se acepta un objeto `Snapshot`
   (`identity`, `version`, `tables`), un análisis con `snapshot`, un registro con
   `precheck`, o la evidencia anterior con `inspection.snapshot`.
3. Revisar equipo, direcciones y compatibilidad. Confirmar gateways, enlaces de
   igual costo y DHCP. Los valores de plantilla no se presentan como mediciones.
4. Preparar la propuesta. Se reutilizan IA, LangGraph, validadores y generador PHP.
5. Revisar plan y script, y autorizar o rechazar. Autorizar no ejecuta acciones.
6. Descargar el JSON y/o `ECMP-cliente.exe`. El ejecutable se construye y valida
   en la primera descarga; las siguientes reutilizan el mismo archivo verificado.

El diagnóstico resumido `ecmp-lab-readonly/1` producido por el modo `--diagnose`
anterior no incluye las tablas: no basta para generar una entrega y se rechaza
con una explicación. Usar el análisis completo descargado por la interfaz anterior.
Para repetir la demostración del avance hay un diagnóstico capturado en
`tests/fixtures/v7-precheck-main-fib-flag.json`; no demuestra el estado actual
de ningún equipo. El ejecutable siempre consulta nuevamente el destino.

## Qué se entrega

**JSON `ecmp-offline/1`:** identidad de entrega, modo, fechas, destino, parámetros,
diagnóstico completo y hash, variante, artefacto PHP, operaciones nativas,
clasificación y plan validados, hash del plan y hash del paquete.

El archivo no contiene contraseñas, certificados privados, claves de IA ni tokens.
Es el contrato de entrega para el agente. El agente existente no se modificó y
todavía no implementa importación de este formato. Para ejecutar este avance se
utiliza el `.exe` independiente; no se afirma compatibilidad automática con el
importador del agente.

**EXE Windows:** incluye el runtime, dependencias y una copia interna del mismo
JSON aprobado. No necesita Python, servidor central ni agente instalado en la PC
del cliente. No acepta scripts libres ni un JSON externo que sustituya su propuesta.
Solo aplica las operaciones nativas admitidas por los contratos existentes.

Para construirlo, el servidor reutiliza el entorno de empaquetado ya presente en
`agent/.venv-portable/Scripts/python.exe`, sin modificarlo. Se puede indicar otro
Python Windows preparado con las dependencias de `agent/build.lock` mediante
`ECMP_BUILD_PYTHON`. PHP se puede localizar mediante `PHP_EXE`. No se instalan
dependencias desde la interfaz. Los binarios y logs se guardan en
`runtime/central-deliveries/<id>/`.

## Ejecución en el cliente

1. Copiar el `.exe` a una carpeta local con permiso de escritura.
2. Mantener conectividad con el MikroTik por LAN o VPN y habilitar API 8728.
3. Abrirlo. En modo real solicita IP, usuario y contraseña RouterOS, sin certificado.
   El destino ECMP real sigue siendo `10.255.255.1:8728`, sin cifrado y con la base
   preparada CHR `7.24.5 (stable)`; no amplía el alcance del laboratorio existente.
4. Revisa configuración e identidad y muestra el script. Escribir
   `APLICAR lab-router` confirma localmente. Cualquier otro texto cancela.
5. Vuelve a validar el paquete y a leer el router después de la confirmación;
   cambios respecto al diagnóstico bloquean la ejecución.
6. Antes de escribir, crea de forma exclusiva un registro local. Aplica una vez,
   verifica y guarda `resultado-<id>.json` junto al ejecutable.

Una ejecución parcial o incierta conserva evidencia y exige revisión; no se
reintenta ni se revierte automáticamente. El registro previo bloquea repetir la
misma entrega en esa carpeta. No existe bloqueo global entre copias en equipos
distintos: al ser offline, no se promete uso único distribuido. La lectura de
configuración rechaza una base ya modificada.

Las entregas vencen 24 horas después de autorizarse y no pueden revocarse a
distancia una vez copiadas. Se necesita un reloj correcto. Para otra entrega,
importar un diagnóstico y aprobar una nueva propuesta.

Los hashes detectan alteraciones accidentales; no son una firma del emisor.
El EXE no tiene firma Authenticode. Distribuir los archivos por un canal confiable.
Una futura importación del JSON por el agente debe validar su procedencia y
repetir las comprobaciones; no debe interpretar su hash como autorización firmada.

## Arquitectura conservada

- Interfaz del técnico: `server/app/central.html`, con el mismo CSS y logo existentes.
- Coordinación central: `server/app/api/central.py` y `services/central_delivery.py`.
- IA, grafo, base de datos y generador: componentes existentes reutilizados.
- Contrato de salida: `server/app/offline_contract.py`.
- Plantilla fija del ejecutable generado: `server/app/offline_runner.py`. Reutiliza
  el transporte y validadores existentes, sin editar `agent`, `shared` ni PHP.
- El punto de entrada central no expone endpoints de sesiones ni tareas del agente.

El flujo online previo conserva su entrada `server.app.main:create_app`.
El nuevo flujo usa `server.app.central:create_app`.

## Validación y límites

Pruebas nuevas (incluyen PHP real, dos compilaciones EXE y ejecución simulada):

```powershell
.\.venv-mvp\Scripts\python.exe -m pytest server/tests/test_central.py -q
```

Regresión conjunta:

```powershell
.\.venv-mvp\Scripts\python.exe -m pytest tests server/tests -q
```

Se comprueban importación sin agente, aprobación/rechazo, persistencia, vencimiento,
alteraciones, cambio de configuración durante la confirmación, fallos parciales,
registro previo a escrituras y construcción/validación de los EXE. Se verificó
también el recorrido en navegador, con ambas descargas y sin errores de consola.

No se realizaron escrituras al MikroTik real ni llamadas facturables de IA en
esta entrega. La ejecución real y las pruebas de tráfico WAN/LAN, DNS y failover
requieren el laboratorio; el resultado estructural no certifica conectividad.

Resultado final de la regresión: **185 aprobadas, 1 omitida** (laboratorio real),
con una advertencia preexistente de Starlette/AnyIO. Incluye las 18 pruebas nuevas
del sistema central. El guardado del resultado tolera bloqueos temporales de
archivos en Windows sin repetir la escritura en RouterOS.
# Continuar con ECMP existente

Al cargar un diagnóstico v7 con elementos ECMP coincidentes aparece **Continuar de todas formas**. Marca primero la confirmación de gateways, enlaces y DHCP. Se conservan las entradas coincidentes y se agregan únicamente las faltantes; si todo está completo, la entrega solo verifica, sin escrituras. Las reglas incompatibles, duplicadas o ajenas a la base admitida siguen bloqueando el proceso.

La revisión muestra las operaciones efectivas. El script PHP completo es una referencia de la plantilla y no debe aplicarse manualmente sobre la configuración existente. Estas entregas usan `ecmp-offline/2` con `execution_policy: preserve_existing`; las entregas normales conservan `ecmp-offline/1`. El ejecutable revalida el diagnóstico antes y después de la confirmación local, conserva el registro de ejecución y verifica la configuración completa. La verificación no prueba tráfico WAN/LAN.

