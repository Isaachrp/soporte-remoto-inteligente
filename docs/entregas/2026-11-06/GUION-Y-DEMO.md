# Guion y demostración para el asesor

Duración propuesta: 10–12 minutos. Si dispones de solo 5 minutos, presenta apertura, flujo central, evidencia ECMP y pendientes. No necesitas enseñar todos los archivos ni recorrer las 15 opciones.

## 1. Apertura — 1 minuto

**Di:**

> Mi proyecto organiza el soporte a routers MikroTik. Primero obtiene un diagnóstico, después la IA sugiere configuraciones disponibles y el técnico decide cuál preparar. El script lo produce el generador PHP existente. Finalmente se entrega un ejecutable autorizado para usar en el equipo del cliente.

**Muestra:** el diagrama del informe.

> Hay dos funciones del lado del cliente: recoger el diagnóstico y ejecutar una entrega. El servidor central se usa en la PC del técnico. El intercambio mediante archivos permite que el ejecutable trabaje sin mantener una conexión con ese servidor.

## 2. Qué cambió — 1 minuto

**Di:**

> Antes el flujo estaba limitado a ECMP. En este avance integré las 14 opciones del menú PHP y OpenVPN, añadí recomendaciones basadas en el diagnóstico y simplifiqué la interfaz. No reescribí el generador PHP: lo conecté desde el servidor.

Aclara que hay plantillas V6 y V7; no todas se aplican a cualquier router. La integración del catálogo y la certificación de cada configuración son trabajos distintos.

## 3. Diagnóstico y recomendación — 3 minutos

**Muestra:** un JSON real conocido y luego su carga en el servidor.

> El JSON contiene versión, interfaces, direcciones, rutas y otras tablas permitidas. No es un script. La IA recibe una selección de esos datos y devuelve opciones del catálogo con una razón breve. No le envío la contraseña de acceso al router.

Abre la interfaz, carga el diagnóstico, pulsa **Analizar** y muestra **IA: OpenRouter**. Señala una sugerencia y su razón. El rótulo por sí solo no acredita una llamada exitosa: muestra que realmente aparecieron recomendaciones.

> La sugerencia es una ayuda para elegir; no demuestra que la red funcione ni autoriza cambios. Si falta información, el técnico completa los parámetros.

No leas como verdad técnica todas las frases generadas. Una recomendación guardada describió PCC como reparto por paquetes: esa explicación debe revisarse, porque PCC clasifica conexiones. Usa ese ejemplo solo si el asesor pregunta por las limitaciones de la IA.

## 4. Selección y entrega — 2 minutos

**Muestra:** selector, parámetros y script desplegado.

> Aquí puedo escoger una opción sugerida o una distinta del catálogo. PHP genera el script con los parámetros revisados. Lo inspecciono y autorizo la entrega. Prepararlo o descargarlo todavía no modifica el router.

Para la demostración principal usa ECMP sobre un diagnóstico compatible y conocido. Si ya está configurado, explica **Continuar de todas formas** como conservación y verificación, no como reaplicación.

Si decides mostrar la generación de PCC, detente en revisión o descarga. No ejecutes PCC sobre el laboratorio durante esta entrega: la prueba anterior quedó pendiente de diagnóstico.

La construcción del EXE puede tardar. Si ya ensayaste esa compilación, puedes mostrar la descarga; si no, usa el archivo y la evidencia guardados, identificándolos como resultados previos. No presentes un EXE viejo como recién generado.

## 5. Resultado ECMP — 2 minutos

**Muestra:** `EVIDENCIAS.md` y el resultado ECMP original que guardaste en el escritorio Linux, si está disponible.

> Esta prueba terminó con cero operaciones nuevas porque ya existían los siete elementos de la configuración. El sistema los conservó y los verificó. Esto evita duplicar reglas. El estado con advertencias corresponde a pruebas WAN/LAN no realizadas.

Señala únicamente cuatro datos:

- `completed: 0`: no se aplicaron operaciones nuevas.
- `preserved: 7`: se conservaron elementos existentes.
- Comprobaciones `passed`: verificación estructural satisfactoria.
- `wan_lan_tested: false`: no se comprobó el funcionamiento extremo a extremo.

Esta es evidencia aportada de una ejecución anterior, no una nueva prueba en vivo. No vuelvas a ejecutar la misma entrega para demostrarla: tiene vigencia y protección frente a repetición.

## 6. Fallo conocido y cierre — 2 minutos

**Di:**

> La prueba PCCrV7 terminó solicitando intervención. El registro anterior no conservó el detalle suficiente para afirmar la causa ni descartar cambios parciales. Revisaré permisos y configuración previa. Ya mejoré el reporte por etapas y lo probé con errores controlados, pero todavía no repetí la prueba real. Por eso no presento PCC como aplicación exitosa.

> El avance demuestra la integración del flujo, la recomendación guardada de OpenRouter, la generación de entregas y una verificación ECMP real reportada. El siguiente hito que propongo es validar completamente un procedimiento adicional y medir conectividad y recuperación ante fallos.

**Pregunta al asesor:**

> ¿Le parece adecuado cerrar primero la validación completa de ECMP y PCC en escenarios definidos antes de ampliar las pruebas del resto del catálogo?

## Preparación antes de la reunión

### Material que conviene tener abierto

- Este guion y el informe; evita usar la documentación del segundo avance como descripción del flujo actual.
- Un diagnóstico JSON real conocido, sin editar para forzar compatibilidad.
- El resultado ECMP original y el resultado PCC fallido.
- La interfaz del sistema central y, solo si ayuda, WinBox para mostrar el equipo.
- El ZIP documental como respaldo y material para compartir.

### Arranque del servidor

Desde PowerShell, en la raíz del proyecto:

```powershell
.\server\iniciar-central.cmd --ai openrouter
```

Abre la URL exacta que imprima la consola: el puerto puede cambiar. Ingresa la clave temporal del técnico. No proyectes ni compartas el `.env` ni las claves de API. Verifica antes de la reunión que una consulta devuelve sugerencias; la cuota gratuita puede agotarse.

Si solo vas a cargar un JSON guardado y presentar evidencias, no necesitas todas las VM encendidas. Para obtener un diagnóstico nuevo sí necesitas el MikroTik y una PC con acceso a su API. No restaures instantáneas ni borres configuración para preparar esta exposición.

El permiso de lectura sirve para diagnosticar. La aplicación de configuraciones requiere permisos adicionales; no afirmes que la cuenta `ecmp-reader` puede escribir sin comprobar su grupo.

### Ensayo breve, sin aplicar cambios

1. Abre informe y evidencias para verificar que los encuentras rápidamente.
2. Inicia el servidor y entra con la clave temporal.
3. Carga un JSON real conocido y revisa el proveedor y las sugerencias.
4. Selecciona una configuración y revisa el formulario; si preparas una propuesta, no la ejecutes en el router.
5. Practica explicar el resultado ECMP en menos de un minuto.
6. Practica explicar el fallo PCC sin atribuirle una causa todavía no comprobada.

## Si algo falla durante la demostración

| Situación | Qué hacer | Qué decir |
|---|---|---|
| OpenRouter no responde o limita consultas | Mostrar las recomendaciones guardadas del expediente | «Esta parte depende de un proveedor externo. Aquí está la respuesta obtenida en la prueba anterior.» |
| El EXE tarda en construirse | Continuar con el resultado guardado | «La compilación no aplica cambios. Les muestro ahora la evidencia de la ejecución anterior.» |
| Windows bloquea un EXE | No desactivar protecciones durante la sesión | «El empaquetado necesita resolver su distribución y confianza en este entorno. La prueba previa se ejecutó bajo Wine.» |
| Router o VM sin conexión | Usar el JSON real guardado | «Voy a mostrar la fase central sobre un diagnóstico previamente capturado; no es una lectura en vivo.» |
| Paquete vencido o ejecución ya registrada | Mostrar evidencia previa, sin borrar registros | «La entrega tiene vigencia y control de repetición. No voy a forzar su reutilización.» |
| Se pide aplicar PCC | Explicar el fallo y el plan de validación | «Esa aplicación todavía no está validada; prefiero delimitar el avance a la evidencia disponible.» |

## Preguntas probables y respuestas

**¿Qué hace realmente la IA?** Analiza una proyección del diagnóstico y propone opciones del catálogo. En el flujo ECMP también participa en el plan. Las validaciones y la autorización no se delegan al modelo.

**¿La IA escribe los comandos?** No. Los comandos proceden del generador PHP existente. La integración valida entradas y conserva la propuesta autorizada.

**¿Por qué no usar directamente PHP?** El aporte es conectar diagnóstico, recomendación, selección, autorización, empaquetado independiente y evidencia del resultado alrededor del generador.

**¿Funciona sin Internet?** La recomendación con OpenRouter necesita Internet. La entrega ya generada no necesita el servidor central, pero sí conectividad con el router.

**¿Por qué cero operaciones es un resultado útil?** Porque la política elegida conserva lo que coincide. Si todo está presente, verificar sin duplicar es el resultado esperado; no es una nueva aplicación.

**¿Las 15 opciones están probadas en un router?** No. Se comprobó la generación e integración del catálogo. La validación real por procedimiento sigue pendiente; PCC reportó un fallo.

**¿El sistema corrige cualquier configuración previa?** No. ECMP del laboratorio tiene conservación específica. Las otras opciones ejecutan el script original y no hacen una migración automática.

**¿Ya es seguro para producción?** No se presenta como producto certificado. Esta fase usa API sin cifrado dentro de LAN/VPN y tiene pruebas funcionales pendientes.

**¿Qué pasa si se interrumpe la ejecución?** Se conserva un registro y se solicita revisión. No hay rollback automático general ni garantía de que no existan cambios parciales.

**¿Qué pruebas respaldan el avance?** La matriz de evidencias separa pruebas automáticas con dobles, generación PHP y resultados reales comunicados. Los distintos recuentos de pruebas pertenecen a ejecuciones diferentes; no se suman.

## Si te piden enseñar código

Muestra solo el archivo relacionado con la pregunta:

| Tema | Archivo desde la raíz del proyecto |
|---|---|
| Catálogo y formulario | `server/app/generator_catalog.py` |
| Recomendación y proyección del diagnóstico | `server/app/services/catalog_ai.py` |
| Conexión OpenRouter | `server/app/services/openrouter.py` |
| Uso del PHP sin modificarlo | `server/php_bridge.php` |
| Preparación y aprobación | `server/app/services/catalog_delivery.py` |
| Ejecución de scripts del catálogo | `server/app/catalog_runner.py` |
| Conservación ECMP | `server/app/existing_ecmp.py` |

No abras archivos de entorno ni bases de datos completas para explicar la arquitectura.
