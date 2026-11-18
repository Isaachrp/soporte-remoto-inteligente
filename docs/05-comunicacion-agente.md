# 5. Comunicación entre sistema principal y agente local

## 1. Objetivo

Definir la información que deberá intercambiarse entre el sistema principal y el agente local durante la ejecución de los procedimientos de soporte.

La comunicación permitirá que el sistema principal indique al agente qué procedimiento debe ejecutar, mientras que el agente enviará información del equipo, resultados y errores.

## 2. Componentes involucrados

La comunicación se realizará principalmente entre:

* Sistema principal.
* Agente local.

El sistema principal estará encargado de coordinar el procedimiento.

El agente local será responsable de ejecutar las acciones autorizadas sobre el equipo Windows y obtener información del entorno.

## 3. Flujo general

El flujo conceptual será:

```text
Sistema principal
       │
       │ 1. Solicitud de ejecución
       ↓
Agente local
       │
       │ 2. Estado / información
       ↓
Sistema principal
       │
       │ 3. Validación / autorización
       ↓
Agente local
       │
       │ 4. Ejecución
       ↓
Agente local
       │
       │ 5. Resultado
       ↓
Sistema principal
```

## 4. Registro del agente

Cuando un agente esté disponible, deberá identificarse ante el sistema principal.

Debido a que el agente será portátil, este registro se realizará al inicio de cada ejecución y creará una sesión temporal.

La información de registro podrá incluir:

* Identificador del agente.
* Identificador de la sesión de ejecución.
* Estado del agente.
* Versión del agente.
* Sistema operativo.
* Fecha y hora de conexión.
* Capacidades disponibles.

El identificador deberá ser único.

Al cerrar el agente, la sesión deberá marcarse como desconectada y no deberá asumirse que el agente permanecerá disponible para operaciones posteriores.

## 5. Estado del agente

El sistema deberá poder conocer el estado del agente.

Inicialmente se consideran los siguientes estados:

* `offline`
* `online`
* `busy`
* `error`
* `waiting_approval`

Ejemplo:

```text
Agente: AGENT-001
Estado: online
Sistema operativo: Windows
Versión: 0.1.0
```

## 6. Solicitud de procedimiento

El sistema principal podrá enviar al agente una solicitud de ejecución.

La solicitud deberá identificar como mínimo:

* ID de la operación.
* Procedimiento.
* Parámetros necesarios.
* Acciones permitidas.
* Nivel de autorización requerido.

Ejemplo conceptual:

```json
{
  "operation_id": "OP-0001",
  "procedure": "ECMP",
  "action": "prepare",
  "parameters": {
    "wan_count": 2
  }
}
```

El formato anterior es únicamente conceptual y podrá cambiar durante la implementación.

## 7. Identificación de la operación

Cada procedimiento deberá tener un identificador de operación único.

Esto permitirá relacionar:

* Solicitud.
* Acciones ejecutadas.
* Resultados.
* Errores.
* Aprobaciones.
* Registro de auditoría.

Ejemplo:

```text
OP-0001
```

Todas las comunicaciones relacionadas con una misma ejecución deberán poder asociarse con este identificador.

## 8. Respuesta del agente

El agente deberá informar el resultado de las operaciones solicitadas.

La respuesta deberá poder indicar:

* Operación.
* Acción realizada.
* Estado.
* Datos obtenidos.
* Errores.
* Fecha y hora.

Ejemplo conceptual:

```json
{
  "operation_id": "OP-0001",
  "action": "collect_router_info",
  "status": "success",
  "data": {
    "routeros_version": "..."
  }
}
```

## 9. Estados de una operación

Una operación podrá pasar por diferentes estados.

Inicialmente se consideran:

```text
pending
   ↓
running
   ↓
waiting_approval
   ↓
running
   ↓
success
```

También podrá finalizar en:

```text
failed
cancelled
```

No todas las operaciones necesitarán pasar por `waiting_approval`.

## 10. Comunicación durante ECMP

Para el procedimiento ECMP, la comunicación podrá seguir una secuencia similar a:

```text
Sistema principal
        │
        │ Iniciar ECMP
        ↓
Agente
        │
        │ Confirmar disponibilidad
        ↓
Sistema principal
        │
        │ Solicitar información del router
        ↓
Agente
        │
        │ Obtener información
        ↓
Sistema principal
        │
        │ Analizar / validar
        ↓
Sistema principal
        │
        │ Solicitar aprobación
        ↓
Técnico
        │
        │ Aprobar
        ↓
Sistema principal
        │
        │ Autorizar ejecución
        ↓
Agente
        │
        │ Ejecutar procedimiento
        ↓
MikroTik
        │
        │ Resultado
        ↓
Agente
        │
        │ Enviar resultado
        ↓
Sistema principal
        │
        │ Verificar resultado
        ↓
Técnico
```

## 11. Separación entre decisión y ejecución

La comunicación deberá mantener una separación clara entre:

### Sistema principal

Se encargará de:

* Coordinar.
* Interpretar.
* Validar.
* Solicitar información.
* Solicitar aprobación.
* Autorizar procedimientos.
* Recibir resultados.

### Agente

Se encargará de:

* Ejecutar acciones autorizadas.
* Obtener información.
* Interactuar con aplicaciones.
* Ejecutar procedimientos.
* Informar resultados.

El agente no deberá decidir por sí mismo qué configuración aplicar.

## 12. Control de acciones

Las solicitudes enviadas al agente deberán corresponder con acciones previamente autorizadas.

Por ejemplo:

```text
Acciones permitidas:

- connect_router_api_ssl
- validate_router_identity
- authenticate_router
- collect_router_info
- execute_ecmp_procedure
- collect_routes
- collect_interface_stats
- collect_mangle_stats
- disconnect_router_api
```

Esta lista es inicial y deberá definirse con mayor precisión durante el diseño del agente.

## 13. Aprobaciones

Cuando una operación requiera aprobación humana, el sistema principal deberá detener el procedimiento.

El agente no deberá ejecutar la acción sensible hasta recibir una autorización válida.

La aprobación deberá asociarse con:

* Operación.
* Acción.
* Técnico.
* Fecha y hora.
* Resultado de la autorización.

## 14. Manejo de errores

El agente deberá comunicar los errores al sistema principal.

Los errores deberán incluir, cuando sea posible:

* Código de error.
* Descripción.
* Acción que produjo el error.
* Información adicional.
* Fecha y hora.

Ejemplo:

```text
Operación: OP-0001
Acción: connect_router
Estado: failed
Error: No fue posible establecer conexión con el MikroTik.
```

## 15. Seguridad

La comunicación entre el sistema principal y el agente deberá protegerse contra accesos no autorizados.

Como mínimo, durante el diseño técnico deberán considerarse:

* Autenticación del agente.
* Autorización de acciones.
* Cifrado de comunicación.
* Identificación de operaciones.
* Protección contra solicitudes no autorizadas.
* Registro de operaciones.
* Expiración de sesiones o credenciales.
* Protección de información sensible.

## 16. Credenciales

Las credenciales del cliente no deberán almacenarse innecesariamente.

El sistema deberá definir posteriormente:

* Dónde se introducen las credenciales.
* Cuánto tiempo permanecen disponibles.
* Quién puede acceder a ellas.
* Cómo se transmiten al agente.
* Cómo se eliminan después de su utilización.

Las credenciales no deberán almacenarse en texto plano dentro de los registros de auditoría.

## 17. Desconexión del agente

Si el agente pierde comunicación durante una operación, el sistema deberá poder detectar la situación.

Dependiendo de la etapa del procedimiento, deberá:

1. Intentar determinar el estado de la operación.
2. Evitar ejecutar nuevamente una acción de forma automática si existe riesgo de duplicarla.
3. Informar al técnico.
4. Registrar la interrupción.

## 18. Estado actual

La arquitectura de comunicación es conceptual.

Todavía no se ha definido:

* Protocolo de comunicación.
* Tecnología de comunicación.
* Formato definitivo de mensajes.
* Sistema de autenticación.
* Sistema de autorización.
* Gestión de sesiones.
* Manejo de reconexiones.
* Implementación del agente.

Estas decisiones serán tomadas durante el diseño técnico.

## 19. Principio fundamental

El sistema deberá mantener una separación entre:

```text
Decisión
   ↓
Autorización
   ↓
Ejecución
   ↓
Verificación
   ↓
Auditoría
```

Esta separación permitirá mantener control sobre las acciones realizadas en los equipos de los clientes y evitar que una decisión de la inteligencia artificial se convierta directamente en una acción no controlada.
