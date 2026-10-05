# 9. Selección del canal de comunicación con MikroTik

## 1. Objetivo

Definir el canal que utilizará el agente local para consultar, configurar y verificar los routers MikroTik durante el procedimiento ECMP del MVP.

## 2. Decisión

El canal principal de comunicación será la API nativa de RouterOS.

En entornos operativos deberá utilizarse preferentemente el servicio `api-ssl`, mediante TCP 8729 y validación del certificado TLS. El servicio `api`, mediante TCP 8728 sin cifrado, solo podrá utilizarse de forma excepcional en un entorno de pruebas aislado y autorizado; no se utilizará para operaciones de producción.

La decisión aplica a las familias RouterOS v6 y v7 contempladas por el MVP.

## 3. Justificación

La API nativa de RouterOS se selecciona porque:

- Es compatible con RouterOS v6 y v7.
- Permite consultar el estado del router, modificar la configuración y ejecutar operaciones sin automatización visual.
- Sigue de forma cercana la estructura de comandos de la interfaz de línea de comandos de RouterOS.
- Proporciona respuestas estructuradas que pueden validarse y registrarse.
- Reduce la dependencia de WinBox, de la resolución de pantalla y de cambios en la interfaz gráfica.
- Facilita la implementación de listas de operaciones permitidas, controles previos y verificaciones posteriores.

## 4. Alternativas consideradas

| Canal | Decisión para el MVP | Motivo |
|---|---|---|
| API nativa con TLS (`api-ssl`) | Seleccionado | Compatible con RouterOS v6 y v7, automatizable y cifrado |
| API nativa sin TLS (`api`) | Solo pruebas aisladas | Compatible, pero transmite la comunicación sin la protección requerida para producción |
| REST API | No seleccionado | Está disponible en RouterOS v7 y no cubre el requisito de compatibilidad con v6 |
| SSH | Contingencia técnica, no canal principal | Es automatizable, pero exige procesar salidas de texto y ofrece menos estructura para el flujo |
| WinBox | Uso manual auxiliar | Es adecuado para el técnico, pero la automatización visual es más frágil |
| AnyDesk | Fuera del canal router-agente | Permite acceso remoto a una PC, pero no constituye una interfaz de administración de RouterOS |

## 5. Arquitectura de comunicación

```text
Sistema principal
       │
       │ Procedimiento autorizado
       ▼
Agente local
       │
       │ RouterOS API con TLS
       │ TCP 8729
       ▼
Router MikroTik
```

La ubicación del agente portátil podrá variar, pero deberá existir conectividad IP entre el agente y el router. AnyDesk no transportará ni sustituirá la conexión de la API. La modalidad se define en [Modalidad de ejecución del agente](10-modalidad-agente.md).

## 6. Flujo de conexión

1. El agente recibe la operación ECMP autorizada y un identificador de correlación.
2. Obtiene la dirección del router y una referencia segura a las credenciales.
3. Comprueba la conectividad hacia el puerto configurado de `api-ssl`.
4. Establece la sesión TLS y valida la identidad presentada por el router.
5. Se autentica con una cuenta de servicio exclusiva.
6. Consulta la versión de RouterOS y determina si corresponde a v6 o v7.
7. Selecciona la variante ECMP autorizada para la familia detectada.
8. Obtiene y valida el estado inicial requerido.
9. Solicita aprobación humana antes de modificar la configuración, cuando corresponda.
10. Ejecuta únicamente las operaciones autorizadas para ECMP.
11. Consulta el estado posterior y realiza las verificaciones definidas.
12. Cierra la sesión y registra el resultado de la operación.

## 7. Requisitos de seguridad

- Utilizar `api-ssl` con un certificado cuya identidad pueda validarse.
- Restringir el servicio por dirección de origen y mediante reglas de firewall.
- No exponer los puertos de la API directamente a Internet.
- Utilizar una VPN o una red privada cuando el agente no se encuentre en la red del cliente.
- Crear una cuenta de servicio individual con los permisos mínimos requeridos para ECMP.
- No utilizar la cuenta predeterminada de administración.
- Mantener las credenciales fuera de scripts, registros y mensajes enviados a la inteligencia artificial.
- Registrar los intentos de conexión, la versión detectada, las operaciones autorizadas, las aprobaciones, los errores y el resultado, sin almacenar secretos.
- Aplicar límites de tiempo, cierre de sesión y control de reintentos.
- Detener la operación si falla la validación TLS, la autenticación o la comprobación de compatibilidad.

## 8. Habilitación inicial

Si `api-ssl` no está habilitado o no dispone de un certificado válido, el sistema no intentará habilitarlo automáticamente mediante un canal inseguro.

El técnico deberá preparar el router de forma manual y controlada, utilizando WinBox u otro mecanismo administrativo autorizado para:

1. Configurar el certificado.
2. Habilitar `api-ssl`.
3. Restringir las direcciones de origen permitidas.
4. Configurar las reglas de firewall necesarias.
5. Crear la cuenta de servicio con permisos mínimos.
6. Verificar la conectividad desde el equipo donde se ejecutará el agente.

## 9. Manejo de errores

El agente deberá detener la operación y solicitar intervención técnica cuando:

- El servicio de API no esté disponible.
- El certificado no pueda validarse.
- Las credenciales sean rechazadas.
- La versión de RouterOS no sea compatible o no pueda identificarse.
- La respuesta del router sea incompleta o inesperada.
- Una operación solicitada no pertenezca a la lista permitida para ECMP.
- Se pierda la conexión antes de confirmar el resultado.

La pérdida de conexión no deberá interpretarse como reversión automática. Antes de reintentar una modificación, el agente deberá volver a consultar el estado del router y determinar qué acciones se aplicaron.

## 10. Criterios de aceptación

La integración se considerará aceptada cuando las pruebas para RouterOS v6 y v7 demuestren que el agente puede:

- Establecer una conexión segura y autenticada mediante `api-ssl`.
- Identificar la versión de RouterOS.
- Consultar interfaces, direcciones IP, gateways, rutas y reglas necesarias para ECMP.
- Ejecutar exclusivamente una variante ECMP autorizada después de la aprobación requerida.
- Detectar y reportar errores de conexión, autenticación y ejecución.
- Verificar el resultado y generar un registro de auditoría completo.

## 11. Referencias

- [API de RouterOS](https://help.mikrotik.com/docs/spaces/ROS/pages/47579160/API).
- [Servicios y puertos de RouterOS](https://help.mikrotik.com/docs/spaces/ROS/pages/103841820/Services).
- [REST API de RouterOS](https://help.mikrotik.com/docs/spaces/ROS/pages/47579162/REST%2BAPI).

