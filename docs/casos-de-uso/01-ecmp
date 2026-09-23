# Caso de uso: ECMP

## 1. Objetivo

Automatizar y agilizar el procedimiento de configuración de balanceo ECMP en equipos MikroTik, reduciendo las tareas manuales que actualmente realiza el técnico durante la configuración y verificación.

El sistema deberá utilizar la aplicación existente para generar el script de configuración y posteriormente coordinar las acciones necesarias para acceder al MikroTik, validar la información, ejecutar el script y verificar el resultado.

## 2. Descripción general

El procedimiento comienza cuando el técnico solicita realizar una configuración de balanceo ECMP para un cliente.

Actualmente, el técnico utiliza una aplicación desarrollada por el equipo para generar el script de configuración. El técnico selecciona ECMP, indica la cantidad de líneas de Internet del cliente y captura los datos correspondientes a cada línea.

La aplicación genera automáticamente un script de configuración que posteriormente es aplicado al router MikroTik.

El sistema de soporte automatizado deberá encargarse principalmente de las etapas posteriores a la generación del script y coordinar el procedimiento completo.

## 3. Datos de entrada

Para generar la configuración ECMP se requieren los siguientes datos por cada línea de Internet:

* Velocidad contratada.
* Gateway proporcionado por el proveedor.
* IP asignada por el proveedor.

Además, se requiere conocer:

* Cantidad de líneas de Internet.
* IP de acceso al MikroTik.
* Credenciales necesarias para acceder al router.
* Información necesaria para establecer la conexión mediante AnyDesk.

## 4. Generación del script

La generación del script será realizada por la aplicación existente desarrollada por el equipo.

El técnico deberá:

1. Acceder a la aplicación.
2. Seleccionar la opción de balanceo ECMP.
3. Indicar la cantidad de líneas de Internet.
4. Capturar la velocidad de cada línea.
5. Capturar el gateway de cada línea.
6. Capturar la IP de cada línea.
7. Enviar el formulario.
8. Obtener el script generado.

El sistema de soporte no deberá generar arbitrariamente comandos de configuración.

La configuración deberá provenir del procedimiento y del generador previamente establecido.

## 5. Acceso al equipo del cliente

Una vez generado el script, el procedimiento continúa mediante acceso remoto.

El técnico utiliza AnyDesk para acceder a la computadora del cliente.

Desde la computadora del cliente:

1. Se abre WinBox.
2. Se proporciona la IP del MikroTik.
3. Se proporcionan las credenciales correspondientes.
4. Se establece conexión con el router.

AnyDesk será considerado el medio de acceso remoto a la computadora del cliente y no será responsable de determinar qué configuración debe realizarse.

## 6. Información que debe verificarse en el MikroTik

Antes de ejecutar el script, el sistema deberá obtener o verificar información del router.

### Datos de las líneas

Para cada línea de Internet se deberá verificar:

* IP.
* Gateway.
* Información relacionada con la conexión de la línea.
* Velocidad correspondiente, cuando esta información pueda ser obtenida o validada desde el entorno disponible.

### Información del router

También deberá obtenerse:

* Versión de RouterOS.

La información obtenida deberá poder compararse con los datos utilizados para generar el script.

## 7. Validación previa

Antes de ejecutar la configuración, el sistema deberá comprobar que la información necesaria esté disponible y sea coherente.

Entre las validaciones consideradas se encuentran:

* Que exista la cantidad esperada de líneas.
* Que las IP correspondan con las líneas configuradas.
* Que los gateways correspondan con las líneas.
* Que la versión de RouterOS sea compatible con el procedimiento.
* Que el script corresponda con los datos proporcionados.

Si existe una discrepancia que pueda provocar una configuración incorrecta, el procedimiento deberá detenerse y solicitar intervención del técnico.

## 8. Ejecución del script

Una vez completadas las validaciones, el sistema deberá ejecutar el script ECMP generado por la aplicación existente.

La ejecución deberá realizarse mediante acciones autorizadas y previamente definidas.

El sistema no deberá permitir que la inteligencia artificial genere comandos arbitrarios para modificar el router.

## 9. Verificación posterior

Después de ejecutar el script, se deberá comprobar que la configuración haya producido el resultado esperado.

### 9.1 Estado de las rutas

Se deberá revisar la tabla de rutas del MikroTik.

Se deberá comprobar principalmente:

* Existencia de las rutas esperadas.
* Estado activo de las rutas correspondientes.
* Estado de los gateways.
* Funcionamiento de `check-gateway=ping`, cuando forme parte de la configuración.

### 9.2 Estado del tráfico

Se deberá verificar el tráfico de las interfaces WAN.

Se deberá comprobar que exista tráfico en las líneas involucradas en el balanceo.

### 9.3 Pruebas desde la LAN

Cuando corresponda, se podrán realizar pruebas de conectividad desde los equipos de la red LAN.

Entre las pruebas consideradas se encuentran:

* Acceso a Internet.
* Comprobación de diferentes salidas públicas.
* Traceroute.
* Otras pruebas definidas posteriormente para validar el balanceo.

### 9.4 Estadísticas de Mangle

Cuando el procedimiento utilice reglas de Mangle, se deberán revisar sus estadísticas.

Se deberán comprobar los contadores de:

* Bytes.
* Paquetes.
* Reglas relacionadas con las conexiones WAN.
* Reglas relacionadas con el marcado de tráfico.

Los contadores deberán presentar actividad cuando exista tráfico que corresponda con las reglas.

## 10. Resultado esperado

El procedimiento deberá finalizar indicando uno de los siguientes estados:

### Configuración exitosa

La configuración ECMP fue aplicada y las verificaciones definidas para el procedimiento fueron satisfactorias.

### Configuración con advertencias

La configuración fue aplicada, pero alguna de las verificaciones requiere revisión del técnico.

### Configuración fallida

La configuración no pudo aplicarse correctamente o alguna condición crítica impidió completar el procedimiento.

### Intervención requerida

El sistema detectó una situación que requiere una decisión o acción del técnico.

## 11. Intervención humana

El técnico deberá conservar el control sobre las operaciones sensibles.

Antes de modificar la configuración del MikroTik, el sistema podrá solicitar confirmación al técnico.

También deberá solicitar intervención cuando:

* Los datos proporcionados no coincidan con los datos del router.
* La versión de RouterOS no sea compatible.
* Exista información insuficiente.
* Ocurra un error durante la ejecución.
* Las verificaciones posteriores indiquen un problema.
* Se requiera una acción que no esté contemplada dentro del procedimiento autorizado.

## 12. Registro de la operación

El sistema deberá registrar información relacionada con la ejecución del procedimiento.

Como mínimo se deberá considerar:

* Fecha y hora.
* Técnico responsable.
* Cliente.
* Equipo MikroTik.
* Procedimiento ejecutado.
* Datos utilizados para la configuración.
* Resultado de las validaciones.
* Resultado de la ejecución.
* Resultado de las verificaciones.
* Errores encontrados.
* Intervenciones o aprobaciones realizadas por el técnico.

## 13. Límites del caso de uso

Este caso de uso se limita inicialmente a la configuración ECMP.

No incluye en esta primera etapa:

* Generación libre de comandos MikroTik por parte de la IA.
* Configuraciones diferentes a ECMP.
* Modificación automática de procedimientos existentes.
* Ejecución de comandos que no formen parte del procedimiento autorizado.
* Automatización completa de situaciones no contempladas.

## 14. Pendientes

Todavía deben definirse técnicamente:

* Cómo se integrará el sistema con la aplicación existente que genera los scripts.
* Cómo obtendrá el agente la información del MikroTik.
* Cómo interactuará automáticamente con WinBox.
* Cómo se ejecutará el script.
* Qué verificaciones serán automáticas.
* Qué verificaciones requerirán intervención humana.
* Cómo se manejarán las credenciales.
* Cómo se realizará el registro de auditoría.
* Qué versiones de RouterOS serán compatibles.
* Qué hacer ante errores durante la ejecución.
