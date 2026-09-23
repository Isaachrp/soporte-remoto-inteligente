
### `docs/01-definicion-del-problema.md`

```md
# 1. Definición del problema

## Problema

El soporte técnico remoto a clientes que utilizan equipos MikroTik requiere actualmente que un técnico realice manualmente una serie de procedimientos para aplicar configuraciones y solucionar problemas.

El proceso puede involucrar la selección y adaptación de scripts de configuración, el acceso remoto al equipo del cliente mediante AnyDesk, la apertura de WinBox, la conexión al router MikroTik, la ejecución del script y la posterior verificación de la configuración.

Cuando estos procedimientos se repiten para diferentes clientes, varias de las acciones realizadas por el técnico son repetitivas y pueden consumir tiempo.

El proyecto busca agilizar este proceso mediante un sistema inteligente que permita identificar el procedimiento correspondiente y automatizar las acciones repetitivas, manteniendo mecanismos de supervisión y aprobación humana.

## Usuario

El sistema será utilizado principalmente por técnicos encargados de proporcionar soporte remoto a clientes que utilizan equipos MikroTik.

## Entorno

El soporte se realizará sobre equipos MikroTik pertenecientes a los clientes.

Actualmente, el técnico utiliza AnyDesk para acceder remotamente al equipo del cliente y, desde dicho equipo, utiliza WinBox para conectarse al router MikroTik y realizar las configuraciones correspondientes.

## Objetivo general

Desarrollar un sistema inteligente de soporte remoto que permita agilizar y automatizar procedimientos técnicos repetitivos en equipos MikroTik, utilizando inteligencia artificial para interpretar las solicitudes del técnico, identificar el procedimiento correspondiente y coordinar su ejecución mediante un agente local.

## Enfoque del sistema

El sistema estará compuesto conceptualmente por diferentes componentes con responsabilidades específicas:

### AnyDesk

Se utilizará como medio de acceso remoto al equipo del cliente.

### Agente local

Será responsable de ejecutar acciones autorizadas en el equipo Windows utilizado para proporcionar el soporte, así como de recopilar información y resultados de las operaciones.

### Inteligencia artificial

Interpretará las solicitudes realizadas por el técnico y determinará qué procedimiento corresponde.

La IA no tendrá control directo e ilimitado sobre los equipos de los clientes. Sus acciones estarán limitadas a procedimientos previamente definidos y autorizados.

### Automatización

Se encargará de ejecutar las tareas repetitivas necesarias para realizar los procedimientos de soporte, como abrir aplicaciones, interactuar con ellas, introducir scripts y realizar verificaciones.

### Base de conocimiento

Contendrá los procedimientos, scripts, parámetros, manuales y soluciones necesarias para que el sistema pueda identificar y ejecutar los procedimientos disponibles.

### Registro y auditoría

Almacenará información sobre las operaciones realizadas, incluyendo las acciones ejecutadas, fecha, hora, procedimiento utilizado y resultado.

### Aprobación humana

El técnico mantendrá supervisión sobre el proceso y podrá requerirse su autorización antes de ejecutar acciones sensibles o que modifiquen la configuración del equipo del cliente.

## Situación actual

Actualmente se dispone de diferentes configuraciones y scripts utilizados por los técnicos para atender clientes MikroTik.

Entre las configuraciones existentes se encuentran:

- ECMP — Balanceo ECMP.
- ECMPr — Balanceo ECMP con DNS recursivo.
- PCC — Balanceo PCC.
- PCCr — Balanceo PCC con DNS recursivo V6.
- PCCrV7 — Balanceo PCC con DNS recursivo V7.
- PCC-DYNAMIC — Balanceo PCC Dinámico.
- PBr — Balanceo PBR con DNS recursivo V6.
- PBrV7 — Balanceo PBR con DNS recursivo V7.
- NTH — Balanceo NTH.
- NTHr — Balanceo NTH con DNS recursivo.
- Hotspot.
- Tickets — Tickets Hotspot.
- Firewall.
- Residenciales — Clientes residenciales.

Estas configuraciones representan el conjunto de procedimientos actualmente disponibles, pero no todas formarán parte de la primera versión del sistema.

## Alcance inicial

El alcance inicial se limitará a un conjunto reducido de procedimientos que permitan desarrollar y validar el concepto de soporte automatizado.

Los primeros procedimientos considerados para el MVP son:

- ECMP.
- PCC.
- Hotspot.

Los demás procedimientos podrán incorporarse posteriormente dependiendo de los resultados obtenidos durante el desarrollo del proyecto.

## Consideraciones

La automatización no deberá otorgar a la inteligencia artificial acceso ilimitado al equipo del cliente.

Las acciones deberán basarse en procedimientos previamente definidos, y las operaciones que impliquen modificaciones sensibles deberán contar con mecanismos de aprobación y supervisión por parte del técnico.

El mecanismo específico mediante el cual el agente local interactuará con WinBox y con los equipos MikroTik será definido durante la etapa de diseño de la arquitectura.

## Estado de la definición

Esta definición es preliminar.

Todavía deben determinarse:

- Los procedimientos exactos que se automatizarán.
- Los scripts que utilizará cada procedimiento.
- Los parámetros necesarios para adaptar los scripts.
- Las acciones que ejecutará el agente local.
- El nivel de autonomía de la inteligencia artificial.
- Las acciones que requerirán aprobación humana.
- El método de verificación de cada procedimiento.
- El mecanismo de comunicación con los equipos MikroTik.
- Los requisitos de seguridad.
