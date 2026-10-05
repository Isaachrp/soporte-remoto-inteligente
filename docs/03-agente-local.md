# 3. Agente local

## 1. Objetivo

El agente local será el componente encargado de ejecutar las acciones autorizadas necesarias para realizar los procedimientos de soporte técnico desde la computadora utilizada para acceder al equipo del cliente.

El agente deberá actuar de acuerdo con procedimientos previamente definidos y no deberá ejecutar instrucciones arbitrarias generadas por la inteligencia artificial.

## 2. Entorno de ejecución

El agente local se distribuirá como una aplicación portátil para Windows. Se iniciará manualmente para cada sesión de soporte y no requerirá instalación, servicio residente ni autoarranque.

Podrá ejecutarse en la computadora del cliente a la que el técnico accede mediante AnyDesk o en otro equipo autorizado con conectividad segura hacia el MikroTik y el servidor central.

En el flujo actual, el técnico utiliza WinBox. Para la automatización del MVP, el agente establecerá comunicación directa con el router mediante la API nativa de RouterOS, preferentemente a través de `api-ssl`.

## 3. Responsabilidades

Inicialmente, el agente deberá poder realizar las siguientes funciones:

* Establecer una sesión segura con la API de RouterOS utilizando los datos autorizados.
* Validar el certificado y autenticar la cuenta de servicio.
* Obtener información del router.
* Ejecutar procedimientos previamente definidos.
* Ejecutar el script correspondiente al procedimiento.
* Obtener información después de la ejecución.
* Realizar verificaciones automáticas.
* Informar los resultados.
* Registrar las acciones realizadas.

## 4. Acciones relacionadas con ECMP

Para el procedimiento ECMP, el agente deberá poder realizar conceptualmente las siguientes acciones:

### Preparación

1. Recibir el procedimiento que debe ejecutar.
2. Recibir los parámetros necesarios.
3. Comprobar que los datos requeridos estén disponibles.
4. Preparar el entorno de ejecución.

### Acceso

1. Comprobar la conectividad con el servicio `api-ssl` del MikroTik.
2. Validar el certificado TLS.
3. Autenticarse con la cuenta de servicio autorizada.
4. Confirmar que la sesión con la API se realizó correctamente.

### Obtención de información

El agente deberá obtener la información necesaria para validar el estado inicial del router:

* IP de las líneas.
* Gateways.
* Información relacionada con las interfaces WAN.
* Versión de RouterOS.

### Validación

El agente deberá comparar la información obtenida con los parámetros esperados por el procedimiento.

Si existe una diferencia que pueda representar un riesgo, deberá detener el procedimiento y solicitar intervención del técnico.

### Ejecución

Una vez autorizada la ejecución:

1. Preparar el script ECMP.
2. Introducir el script mediante el mecanismo definido.
3. Ejecutar el procedimiento.
4. Detectar posibles errores.
5. Obtener el resultado de la operación.

### Verificación

Después de ejecutar el script, el agente deberá realizar las verificaciones automáticas que sean técnicamente viables.

Inicialmente se consideran:

* Estado de las rutas.
* Estado de los gateways.
* Tráfico de las interfaces WAN.
* Estadísticas de las reglas relacionadas con el balanceo.
* Otras verificaciones que sean definidas posteriormente.

## 5. Límites del agente

El agente no deberá:

* Generar comandos MikroTik arbitrarios.
* Ejecutar comandos proporcionados directamente por la IA sin validación.
* Modificar configuraciones fuera del procedimiento autorizado.
* Ejecutar procedimientos no autorizados.
* Tomar decisiones sobre cambios de configuración que no estén definidos en el procedimiento.
* Almacenar credenciales de clientes de forma insegura.

## 6. Relación con la inteligencia artificial

La inteligencia artificial y el agente local tendrán responsabilidades diferentes.

### Inteligencia artificial

La IA será responsable de:

* Interpretar la solicitud del técnico.
* Identificar el procedimiento correspondiente.
* Determinar qué procedimiento de la base de conocimiento debe utilizarse.
* Identificar los parámetros necesarios.
* Analizar información obtenida durante el procedimiento.
* Informar resultados y posibles problemas.

### Agente local

El agente será responsable de:

* Ejecutar las acciones autorizadas.
* Interactuar con las aplicaciones.
* Obtener información.
* Ejecutar procedimientos previamente definidos.
* Realizar verificaciones.
* Informar resultados a los componentes correspondientes.

La IA no deberá tener acceso directo e ilimitado al sistema operativo ni al router.

## 7. Aprobación humana

Las acciones que puedan modificar la configuración del cliente deberán poder requerir aprobación del técnico.

El agente deberá detenerse cuando una acción requiera autorización y continuar únicamente después de recibir la aprobación correspondiente.

## 8. Auditoría

El agente deberá generar información suficiente para registrar:

* Acción ejecutada.
* Fecha y hora.
* Procedimiento.
* Resultado.
* Errores.
* Aprobaciones recibidas.
* Información obtenida durante las verificaciones.

## 9. Estado actual

El agente local todavía no ha sido implementado.

La tecnología y arquitectura específica que se utilizará para desarrollarlo serán determinadas en la etapa de diseño técnico.

La modalidad de ejecución para el MVP ya está definida como portátil en [Modalidad de ejecución del agente](10-modalidad-agente.md).

## 10. Pendientes

Se deberá definir:

* Lenguaje de programación.
* Formato de empaquetado portátil.
* Mecanismo de firma o validación de integridad del paquete.
* Forma de comunicación con el sistema principal.
* Biblioteca cliente para la API de RouterOS.
* Modelo exacto de operaciones permitidas para consultar y modificar el MikroTik.
* Forma de ejecutar mediante la API las variantes autorizadas del procedimiento ECMP.
* Sistema de permisos.
* Manejo de credenciales.
* Sistema de logs.
* Mecanismo de aprobación.
* Manejo de errores.
* Seguridad del agente.
