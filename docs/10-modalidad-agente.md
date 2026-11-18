# 10. Modalidad de ejecución del agente

## 1. Objetivo

Definir si el agente del MVP será portátil, instalado o sustituido por una ejecución manual asistida.

## 2. Decisión

Para la primera versión se utilizará un agente portátil para Windows.

El agente se distribuirá como un paquete autocontenido que el técnico podrá copiar o descargar desde una fuente autorizada, extraer en una carpeta local y ejecutar bajo demanda. No requerirá un proceso de instalación permanente.

El agente estará activo únicamente durante la sesión de soporte y deberá cerrarse al finalizar la operación.

## 3. Comparación de modalidades

| Modalidad | Decisión para el MVP | Motivo |
|---|---|---|
| Agente portátil | Seleccionada | Facilita pruebas, distribución y ejecución en distintos equipos sin instalación permanente |
| Agente instalado | No seleccionada | Añade servicios, persistencia, permisos de instalación, desinstalación y mantenimiento que no son necesarios para validar el MVP |
| Ejecución manual asistida sin agente | Contingencia | Permite continuar de forma manual, pero no valida la automatización completa del flujo ECMP |

## 4. Características obligatorias

El agente portátil deberá:

- Ejecutarse en Windows desde una carpeta local autorizada.
- Incluir o localizar de forma controlada las dependencias necesarias.
- Iniciarse manualmente por el técnico.
- Funcionar sin crear un servicio de Windows.
- No configurarse para iniciar automáticamente con el sistema.
- No requerir privilegios de administrador para su operación normal.
- No modificar el registro de Windows ni directorios del sistema, salvo que una necesidad técnica sea aprobada expresamente.
- Identificarse y autenticarse ante el sistema central al iniciar.
- Mantener una sesión temporal asociada con la operación de soporte.
- Comunicarse con el MikroTik mediante `api-ssl`, conforme a la decisión del canal de comunicación.
- Liberar sesiones, archivos temporales y secretos al finalizar.

## 5. Ubicación de ejecución

La portabilidad no significa que el agente pueda ejecutarse desde cualquier red sin controles.

Para cada operación, el técnico deberá ejecutarlo en un equipo Windows autorizado que tenga:

- Conectividad segura con el servidor central.
- Conectividad IP con el servicio `api-ssl` del MikroTik.
- Acceso a la cadena de confianza necesaria para validar el certificado del router.
- Permisos suficientes para ejecutar el agente y crear únicamente sus archivos temporales.

En la primera versión, el equipo podrá ser la PC del cliente a la que se accede mediante AnyDesk o un equipo controlado por la empresa conectado mediante VPN o red privada. La selección dependerá de la conectividad disponible para la operación.

## 6. Ciclo de vida por sesión

```text
Obtener paquete autorizado
          ↓
Validar integridad y versión
          ↓
Extraer en carpeta local
          ↓
Iniciar agente manualmente
          ↓
Registrar sesión temporal
          ↓
Ejecutar operación ECMP
          ↓
Enviar resultado y auditoría
          ↓
Cerrar conexiones y limpiar secretos
          ↓
Finalizar agente
```

El agente no deberá permanecer ejecutándose después de la sesión de soporte salvo que el técnico lo autorice expresamente para completar una operación en curso.

## 7. Distribución e integridad

- El paquete deberá proceder de una ubicación controlada por la empresa.
- Cada versión deberá tener un identificador único.
- Antes de ejecutarlo se deberá validar su firma digital o, como mínimo durante el prototipo, una suma criptográfica publicada por un canal confiable.
- El agente deberá informar su versión al sistema central.
- El servidor deberá poder rechazar versiones obsoletas o no autorizadas.
- La actualización consistirá en sustituir el paquete completo por una versión aprobada; el MVP no requerirá un actualizador residente.

## 8. Datos locales y limpieza

El agente no deberá almacenar credenciales de forma permanente.

Los archivos temporales y registros locales deberán limitarse a lo necesario para la operación. Al finalizar:

- Los secretos deberán eliminarse de memoria cuando sea técnicamente viable.
- Las sesiones con el servidor y el MikroTik deberán cerrarse.
- Los registros requeridos deberán enviarse al sistema central.
- Los archivos temporales sensibles deberán eliminarse.
- Los registros locales que deban conservarse deberán excluir contraseñas, tokens y otros secretos.

La eliminación del paquete portátil será manual y podrá realizarse después de confirmar que la auditoría fue recibida correctamente.

## 9. Manejo de interrupciones

Si el agente se cierra o pierde conectividad durante una modificación:

1. El sistema central marcará la sesión como interrumpida.
2. No se repetirá automáticamente una operación de escritura.
3. El técnico volverá a iniciar el agente cuando exista conectividad.
4. El agente consultará el estado actual del MikroTik antes de proponer una continuación.
5. La reanudación requerirá una nueva validación y, cuando corresponda, aprobación humana.

## 10. Criterios de aceptación

La modalidad portátil se considerará validada cuando el agente pueda:

- Ejecutarse en un equipo Windows compatible sin instalador ni servicio permanente.
- Registrarse temporalmente ante el servidor central.
- Completar el flujo ECMP mediante la API de RouterOS.
- Finalizar sin dejar procesos residentes ni credenciales persistentes.
- Ser sustituido por una nueva versión mediante el reemplazo controlado del paquete.
- Producir evidencia suficiente para comprobar su versión, integridad y operación.

## 11. Evidencia del prototipo (30-09-2026)

Se implementó un agente de inicio manual, HTTP polling y cierre de sesión. Se construyó `dist/ecmp-agent` con PyInstaller, runtime incluido, versión y manifiesto SHA-256. La prueba E2E copia toda la distribución a otra carpeta temporal, verifica sus hashes, elimina `PYTHONPATH`/`PYTHONHOME`, ejecuta el binario con PHP/FastAPI reales y completa el flujo con RouterOS simulado; el proceso termina con código 0.

Esto verifica un smoke test portátil en Windows 11 con transporte simulado. La aceptación completa que exige ECMP mediante `api-ssl`, otros equipos Windows, políticas antivirus y cuenta estándar independiente sigue pendiente. No hay servicio, autoarranque ni instalador. Instrucciones reproducibles en [Ejecución MVP](12-ejecucion-mvp.md).

