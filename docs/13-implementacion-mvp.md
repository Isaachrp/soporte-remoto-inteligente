# Arquitectura implementada y controles

## Estado frente al diseño previo

Este documento describe código implementado. Los documentos 03–11 conservan decisiones y antecedentes; sus listas de capacidades propuestas no prueban implementación. El MVP no automatiza Windows, WinBox o AnyDesk y no conecta scripts libres del módulo OpenRouter al nuevo agente.

La interfaz del técnico llama FastAPI. `server/app/api` expone rutas; `services` contiene interpretación, generador y coordinación; `workflow.py` utiliza LangGraph; `storage.py` mantiene SQLite. `shared` contiene contratos y adaptación restringida. `agent` es una aplicación independiente con HTTP polling y transporte nativo TLS de lectura o simulador explícito.

## Workflow durable

Actualización de IA: la [arquitectura de planificación y evaluación](17-arquitectura-ia-mvp.md)
extiende este flujo con generación/validación de planes y respuesta final tipada.
El vínculo de las solicitudes nuevas incluye también el hash del plan. Los controles
de ejecución y la compatibilidad cerrada descritos aquí siguen vigentes.

`received → clasificación → parámetros → await_precheck → compatibilidad → PHP → validación → await_approval → await_execution → await_verification → resultado`.

LangGraph ejecuta únicamente las transiciones disponibles para un evento. Al llegar a una espera retorna; no espera sincrónicamente al agente. Una transacción `BEGIN IMMEDIATE` persiste el estado del grafo, la tarea pendiente y auditoría. Cada evento posterior recarga ese estado e invoca el grafo. Esta implementación usa checkpoints explícitos en SQLite a nivel de evento, no `MemorySaver` ni un proceso esperando `interrupt()` en memoria.

No se persiste el texto libre de la solicitud. Se conserva clasificación/estado y datos estructurados. Faltantes esperan `PUT parameters`; solicitudes distintas de ECMP terminan fuera de alcance. Fallos de precondiciones/integraciones terminan en intervención. Los nodos que llaman PHP/IA pueden repetirse si cae el servidor antes del commit: son generación/clasificación, nunca escritura en router.

## Autenticación y aprobación

Un técnico identificado y un agente identificado mediante tokens distintos (alcance inicial monousuario). Generador con tercer token separado. Sesiones aleatorias, token aleatorio guardado únicamente como SHA-256, expiración fija de una hora y heartbeat. En red se exige HTTPS; HTTP se admite en loopback para desarrollo. El servidor se ejecuta con TLS directo mediante Uvicorn si se expone remotamente; no confiar ciegamente en encabezados de proxy ni abrirlo a Internet.

La aprobación vincula técnico, solicitud, sesión, router, parámetros, modo, versión del generador, variante, generación, hash del script, versión/hash de operaciones y snapshot previo. Se registra fecha, vencimiento a cinco minutos y uso. La UI muestra script, advertencias y representación antes de aprobar.

El agente solicita un `claim` en línea con su sesión autenticada y un prechequeo nuevo. SQLite consume la aprobación de forma atómica. El servidor y el agente recalculan los vínculos. Un hash recalculado sobre contenido alterado no sirve para reutilizar una autorización previa. No hay `approved=true`, comandos externos ni endpoint genérico de ejecución.

No existe endpoint para modificar artefactos. Se conservan como objetos separados; se rechaza sustituir un `generation_id` existente por otro contenido. Los hashes detectan alteración; los tokens y TLS proporcionan autenticación. Un administrador con control total del código o SQLite queda fuera del modelo de amenaza: proteger ambos mediante permisos del sistema operativo y copias controladas.

## Generador PHP y adaptación

`ecmp_text()` es la fuente de texto RouterOS. `legacy_ecmp()` es el adaptador de presentación que conserva `<br>` para la pantalla manual. `/api/ecmp.php` devuelve JSON directamente desde esa fuente, sin renderizar o extraer HTML de `aplicar.php`.

Normalización: CRLF/CR a LF, espacios finales eliminados por línea, blancos extremos eliminados, un LF final. SHA-256 de UTF-8 sin BOM. Python reproduce esta normalización para comprobar el hash. Entradas: tipo exacto ECMP, 2–12 WAN, lista original de velocidades, gateways `192.168.0..254.{1,254}`, octetos WAN enteros 2–253, LAN `172.16.0..254.1`, DHCP booleano. Se rechazan subredes WAN superpuestas, campos desconocidos y datos faltantes.

`shared/ecmp.py` traduce únicamente las secciones, verbos y claves conocidos del legado. Rechaza `remove`, reset, expresiones, variables, escapes, otras secciones o argumentos desconocidos. El selector de Ethernet es exclusivamente `default-name=etherN`. Cada operación conserva el número de línea fuente y se incluye en un hash conjunto con versión de adaptador. No genera configuraciones ni pesos en Python.

**Escritura real aún bloqueada:** la representación describe llamadas como `/ip/address/add` con argumentos separados. El ejecutor nativo resuelve un único `.id` mediante consulta para `/interface/ethernet/set`, consume las respuestas para detectar errores y no reintenta operaciones. No envía bloques de terminal. Su puerta de compatibilidad rechaza todas las versiones reales: únicamente el simulador está habilitado. La conversión nativa se probó con una API doble; certificarla sigue siendo trabajo de laboratorio pendiente.

Se corrigió en PHP un defecto concreto de ponderación: gateways repetidos de la última WAN se separaban con espacios. Ahora toda lista utiliza comas y un espacio antes del siguiente argumento. La salida manual de casos no afectados se compara con una copia previa del generador guardada como fixture; el caso corregido tiene prueba específica. No se ajustó silenciosamente la sintaxis `broadcast`/`routing-mark` ni se inventó compatibilidad v7.

## Catálogo y endpoints

| Acción | Parámetros de tarea | Riesgo | Límite | Autorización |
|---|---|---|---|---|
| `get_ecmp_precheck` | destino y parámetros validados | Lectura | 60 s | Sesión autenticada |
| `apply_approved_ecmp` | artefacto, operaciones, hashes, vínculo y prechequeo | Escritura simulada; real bloqueada | 120 s | Claim de un solo uso |
| `verify_ecmp` | destino y representación aprobada | Lectura | 60 s | Sesión, incluso reconciliación |

Las consultas agrupan identidad, versión exacta, Ethernet, direcciones, rutas, NAT, Mangle, DNS, pools, DHCP y puertos bridge. Esquemas en `shared/contracts.py` y `shared/snapshot.py`. No se consulta usuarios, contraseñas, PPP secrets o exports completos.

| Método/ruta | Autenticación / propósito |
|---|---|
| `GET /`, `/docs`, `/health` | Interfaz, OpenAPI, salud sin secretos |
| `GET /actions` | Técnico; catálogo |
| `POST /requests` | Técnico; crear solicitud |
| `GET /requests/{id}` | Técnico; estado, script, evidencia |
| `PUT /requests/{id}/parameters` | Técnico; completar solo antes de generación |
| `POST /requests/{id}/decision` | Técnico; aprobar/rechazar vínculo revisado |
| `GET /requests/{id}/audit` | Técnico; eventos ordenados |
| `POST /requests/{id}/reconcile` | Técnico; consulta de estado tras incertidumbre |
| `POST /agent/sessions` | Token de registro del agente; sesión temporal |
| `POST /agent/sessions/{id}/heartbeat` | Token de sesión |
| `DELETE /agent/sessions/{id}` | Token de sesión; cierre |
| `GET /agent/sessions/{id}/tasks` | Token de sesión; entrega única |
| `POST /agent/sessions/{id}/tasks/{task_id}/claim` | Token de sesión + snapshot actual; consumir aprobación |
| `POST /agent/sessions/{id}/tasks/{task_id}/result` | Token de sesión; correlación y deduplicación |
| PHP `POST /api/ecmp.php` | Token generador; artefacto JSON v6 no certificado |

## Precondiciones, tiempo y recuperación

Puerto administrativo dedicado fuera de ether1…etherN+1, identidad esperada, interfaces suficientes y sin renombrar, ausencia de bridges/configuraciones previas en áreas afectadas. Es un prechequeo deliberadamente conservador para un laboratorio preparado; no permite fusionar configuraciones existentes. Las rutas conectadas reales y otras diferencias de estado deben validarse en laboratorio antes de autorizar una variante.

Polling cada 2 s; heartbeat en cada ciclo; inactividad máxima 45 s, sesión 3600 s; aprobación 300 s; tarea pendiente 300 s; tareas entregadas según catálogo. Socket RouterOS 5 s, HTTP agente 20 s, PHP 15 s, OpenAI 20 s sin reintentos de modelo. Un prechequeo real muy lento puede provocar expiración conservadora del heartbeat; no da autorización adicional. Barrido cada 5 s y antes de entrega/claim/resultado/consulta. Valores centralizados en `Settings`, catálogo y transportes.

Tareas entregadas no se vuelven a entregar. Si una escritura entregada/consumida pierde su resultado se marca incierta y se bloquea una nueva operación para ese router. Una desconexión nunca significa rollback. El mismo resultado puede reenviarse; un duplicado diferente, resultado tardío o sesión ajena se rechazan. Reanudar el servidor conserva aprobaciones, tareas y resultados.

`reconcile` puede asignar una lectura a una sesión nueva del mismo router/modo. Guarda la comparación con la configuración esperada pero mantiene intervención requerida. No reusa la aprobación, no libera automáticamente el bloqueo ni promete rollback. La resolución de incidentes y habilitación de una nueva operación tras intervención requieren revisión manual fuera del MVP; no editar SQLite para simular éxito.

## Verificación y secretos

Se contrastan propiedades generadas de interfaces, direcciones, rutas activas/gateways, NAT, Mangle, DNS y DHCP. No basta que la aplicación acepte operaciones. Faltantes provocan `configuration_failed`. Tráfico WAN y pruebas LAN aparecen como `not_performed`, por lo que el flujo de simulación termina con advertencias y no con éxito total.

El prompt OpenAI solo recibe vocabulario cerrado detectado, no texto libre, configuración del router ni credenciales. La extracción de todos los parámetros desde lenguaje natural está pendiente; se completan en el formulario estructurado. Los errores HTTP de validación no reflejan los valores enviados y los fallos externos se registran mediante códigos, sin mensajes crudos. La auditoría guarda eventos e identificadores, no tokens. Las credenciales reales se solicitan en el agente y solo permanecen en memoria de proceso; Python no garantiza borrado criptográfico de strings.

## Referencias consultadas

- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs): salida tipada Pydantic para la clasificación; SDK encapsulado, sin prueba de servicio remoto.
- [LangGraph interrupts y persistencia](https://docs.langchain.com/oss/python/langgraph/interrupts): referencia de pausas; aquí se implementan mediante estados de espera y transacciones por evento.
- [librouteros 3.4.1, análisis API](https://librouteros.readthedocs.io/en/3.4.1/api_analysis.html): protocolo y operaciones separadas. Además se inspeccionaron `connect` y `create_transport` instalados: soportan `ssl_wrapper`, puerto, timeout y cierre. Se prueba el contexto `CERT_REQUIRED`, hostname y ausencia de fallback; eso no verifica un handshake con un MikroTik real.
