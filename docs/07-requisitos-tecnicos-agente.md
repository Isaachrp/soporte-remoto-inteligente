# 7. Requisitos técnicos del agente

## 1. Objetivo

Definir las capacidades y requisitos que deberá cumplir el agente local para participar en los procedimientos de soporte remoto.

Para el MVP, el agente será portátil y no se instalará de forma permanente. Podrá ejecutarse en un equipo Windows autorizado que tenga conectividad segura con el servidor central y el MikroTik.

## 2. Función principal

El agente será el componente encargado de ejecutar acciones autorizadas sobre el entorno utilizado para administrar los equipos MikroTik.

Su función principal será convertir las instrucciones de un procedimiento autorizado en acciones concretas y controladas.

El agente no deberá tomar decisiones autónomas sobre qué configuración aplicar.

## 3. Capacidades principales

El agente deberá ser capaz de:

* Recibir instrucciones del sistema principal.
* Identificar la operación a la que pertenece cada instrucción.
* Validar que la instrucción esté autorizada.
* Ejecutar acciones permitidas.
* Obtener información del entorno.
* Interactuar con las herramientas necesarias.
* Ejecutar procedimientos previamente definidos.
* Obtener resultados.
* Reportar errores.
* Informar el estado de la operación.
* Mantener registros de las acciones realizadas.

## 4. Interacción con Windows

El agente deberá poder interactuar con el sistema operativo Windows cuando el procedimiento lo requiera.

Inicialmente se consideran capacidades como:

* Detectar aplicaciones instaladas.
* Abrir aplicaciones autorizadas.
* Cerrar aplicaciones autorizadas.
* Detectar procesos.
* Obtener información básica del sistema.
* Interactuar con ventanas y controles.
* Ejecutar acciones previamente definidas.
* Detectar errores durante la interacción.

Las capacidades exactas dependerán del mecanismo de automatización seleccionado.

## 5. Interacción con la API de RouterOS

Para el procedimiento ECMP, el agente deberá interactuar con la API nativa de RouterOS mediante una conexión segura.

Las capacidades requeridas son:

1. Comprobar la disponibilidad de `api-ssl`.
2. Validar el certificado TLS del router.
3. Autenticarse con una cuenta de servicio autorizada.
4. Detectar si la sesión fue establecida correctamente.
5. Ejecutar las acciones necesarias.
6. Obtener información del MikroTik.
7. Ejecutar el procedimiento autorizado.
8. Obtener información después de la ejecución.
9. Detectar errores.

La implementación deberá utilizar una biblioteca cliente compatible con la API nativa de RouterOS v6 y v7.

## 6. Interacción con MikroTik

El agente deberá ejecutar las operaciones necesarias sobre el MikroTik mediante la API nativa de RouterOS. El canal de producción será preferentemente `api-ssl` sobre TCP 8729.

WinBox y SSH no serán canales automatizados del MVP. Podrán utilizarse manualmente para preparación, diagnóstico o contingencia. REST API tampoco será el canal principal porque el alcance incluye RouterOS v6.

Los requisitos completos se definen en [Selección del canal de comunicación con MikroTik](09-canal-comunicacion-mikrotik.md).

## 7. Ejecución de procedimientos

El agente no deberá recibir comandos arbitrarios.

En lugar de esto, deberá recibir procedimientos o acciones previamente definidas.

Ejemplo conceptual:

```text
Procedimiento: ECMP

1. Conectar al MikroTik
2. Obtener versión de RouterOS
3. Obtener información de las interfaces
4. Obtener IPs
5. Obtener gateways
6. Validar información
7. Esperar autorización
8. Ejecutar script ECMP
9. Verificar rutas
10. Verificar interfaces
11. Verificar estadísticas
12. Reportar resultado
```

El procedimiento determinará qué acciones están permitidas.

## 8. Sistema de acciones permitidas

El agente deberá contar con un conjunto limitado de acciones.

Ejemplo conceptual:

```text
connect_router
collect_router_info
collect_interfaces
collect_routes
collect_mangle_stats
execute_procedure
verify_routes
verify_interfaces
verify_mangle
disconnect_router
```

La lista definitiva se determinará durante el desarrollo.

El sistema principal solamente deberá poder solicitar acciones que el agente reconozca y tenga autorizadas.

## 9. Estados del agente

El agente deberá mantener un estado conocido por el sistema principal.

Estados iniciales:

```text
offline
online
busy
waiting_approval
error
updating
```

Ejemplo:

```text
Agente: AGENT-001
Estado: busy
Operación: OP-0001
Procedimiento: ECMP
```

## 10. Estados de una operación

Cada operación deberá tener su propio estado.

```text
pending
running
waiting_approval
success
failed
cancelled
```

Esto permitirá distinguir el estado del agente del estado de una operación específica.

## 11. Comunicación con el sistema principal

El agente deberá mantener una comunicación segura con el sistema principal.

Deberá poder:

* Recibir operaciones.
* Enviar estados.
* Enviar información obtenida.
* Enviar resultados.
* Informar errores.
* Recibir autorizaciones.
* Informar desconexiones.

La tecnología y protocolo de comunicación se definirán posteriormente.

## 12. Seguridad

El agente deberá considerar como requisitos mínimos:

* Autenticación.
* Autorización.
* Cifrado de comunicaciones.
* Validación de solicitudes.
* Control de acciones permitidas.
* Protección de credenciales.
* Registro de operaciones.
* Control de versiones.
* Actualizaciones seguras.

El agente no deberá confiar automáticamente en cualquier solicitud recibida.

## 13. Credenciales

El agente podrá necesitar credenciales para acceder al MikroTik.

Estas credenciales deberán:

* Utilizarse únicamente cuando sean necesarias.
* Transmitirse de forma segura.
* No almacenarse en texto plano.
* No aparecer en logs.
* Eliminarse de memoria cuando ya no sean necesarias, cuando sea técnicamente viable.

El mecanismo definitivo de gestión de credenciales se definirá posteriormente.

## 14. Manejo de errores

El agente deberá detectar y reportar errores.

Ejemplos:

```text
El servicio api-ssl no está disponible.
No se pudo validar el certificado del MikroTik.
No se pudo conectar al MikroTik.
Credenciales inválidas.
No se encontró la interfaz esperada.
La versión de RouterOS no es compatible.
El script no pudo ejecutarse.
La verificación posterior falló.
Se perdió la comunicación con el servidor.
```

Los errores deberán asociarse con la operación correspondiente.

## 15. Recuperación ante fallos

El agente deberá evitar repetir automáticamente acciones que puedan modificar nuevamente la configuración del router sin conocer el estado actual.

Si ocurre una interrupción durante una operación, el sistema deberá:

1. Detectar la interrupción.
2. Registrar el estado conocido.
3. Informar al sistema principal.
4. Determinar si es seguro continuar.
5. Solicitar intervención humana cuando sea necesario.

## 16. Actualización

El agente deberá contar posteriormente con un mecanismo para recibir actualizaciones.

La actualización deberá considerar:

* Autenticidad del paquete.
* Integridad.
* Compatibilidad.
* Recuperación ante errores.
* Registro de la actualización.

No se deberá asumir todavía un mecanismo específico.

## 17. Registro

El agente deberá registrar eventos relevantes.

Ejemplos:

```text
Agente iniciado.
Agente conectado al servidor.
Operación recibida.
Sesión api-ssl iniciada.
Identidad del MikroTik validada.
Conexión autenticada con el MikroTik.
Información obtenida.
Procedimiento autorizado.
Script ejecutado.
Verificación realizada.
Operación finalizada.
Error detectado.
Agente desconectado.
```

Los logs no deberán contener contraseñas ni información sensible innecesaria.

## 18. Requisitos de rendimiento

El agente deberá consumir una cantidad razonable de recursos del equipo donde se ejecute.

Deberá evitar:

* Consumo excesivo de CPU.
* Consumo innecesario de memoria.
* Procesos permanentes que no sean necesarios.
* Ejecución de tareas sin autorización.

Los requisitos cuantitativos de CPU, memoria y almacenamiento se definirán después de seleccionar la tecnología.

## 19. Requisitos de compatibilidad

Inicialmente se deberá considerar compatibilidad con:

* Windows utilizado actualmente por los técnicos y clientes.
* Versiones de WinBox utilizadas por el equipo.
* RouterOS v6 para el procedimiento ECMP.
* RouterOS v7 para el procedimiento ECMP.

La selección del script deberá realizarse según la familia de RouterOS detectada. El agente deberá detener la operación si la versión es incompatible, no está validada o no puede identificarse.

La compatibilidad inicial y el registro de versiones certificadas se definen en [Matriz inicial de versiones de RouterOS](08-matriz-versiones-routeros.md).

## 20. Portabilidad y ubicación

El agente deberá ejecutarse sin instalador, servicio permanente ni autoarranque. Su paquete podrá trasladarse entre equipos Windows autorizados, pero deberá ejecutarse desde una carpeta local y validar su integridad antes de iniciar.

La ubicación se elegirá por operación según la conectividad disponible:

```text
A. PC del cliente accesible mediante AnyDesk

B. Equipo del técnico conectado mediante VPN o red privada

C. Otro equipo controlado por la empresa con conectividad autorizada
```

En todos los casos deberán cumplirse los mismos requisitos de autenticación, autorización, conectividad y auditoría definidos en [Modalidad de ejecución del agente](10-modalidad-agente.md).

## 21. Estado actual

Los requisitos funcionales del agente están definidos de forma preliminar.

Todavía deben determinarse:

* Lenguaje de programación.
* Framework.
* Tecnología de automatización de Windows.
* Biblioteca cliente de la API de RouterOS.
* Administración de certificados para `api-ssl`.
* Protocolo de comunicación con el servidor.
* Sistema de autenticación.
* Sistema de autorización.
* Gestión de credenciales.
* Formato del paquete portátil.
* Firma digital o mecanismo de validación de integridad.
* Procedimiento de distribución y sustitución de versiones.

Estas decisiones forman parte de la siguiente etapa de diseño técnico.
