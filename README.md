# Soporte Remoto Inteligente y Automatizado

Sistema de soporte remoto orientado a agilizar y automatizar procedimientos técnicos repetitivos en equipos MikroTik de clientes.

El sistema utilizará inteligencia artificial para interpretar las solicitudes del técnico y determinar el procedimiento correspondiente. Un agente local será responsable de ejecutar acciones autorizadas en el equipo Windows utilizado para proporcionar el soporte remoto.

## Objetivo

Desarrollar un sistema inteligente capaz de asistir y automatizar procedimientos de soporte técnico sobre equipos MikroTik, reduciendo las tareas manuales y repetitivas realizadas actualmente por los técnicos.

El sistema utilizará procedimientos y scripts previamente definidos, manteniendo supervisión humana sobre las acciones que puedan modificar la configuración de los equipos de los clientes.

## Componentes principales

El sistema contempla los siguientes componentes:

- **AnyDesk:** acceso remoto al equipo del cliente.
- **Agente local:** ejecución de acciones autorizadas en Windows y recopilación de información.
- **Inteligencia artificial:** interpretación de solicitudes y selección del procedimiento correspondiente.
- **Automatización:** ejecución de tareas repetitivas necesarias para realizar los procedimientos.
- **Base de conocimiento:** almacenamiento de procedimientos, scripts, parámetros, manuales y soluciones.
- **Registro y auditoría:** almacenamiento de las acciones realizadas y sus resultados.
- **Aprobación humana:** supervisión y autorización de acciones sensibles.

## MVP

La primera versión del sistema contempla tres procedimientos de configuración para equipos MikroTik:

1. ECMP — Balanceo ECMP.
2. PCC — Balanceo PCC.
3. Hotspot.

El sistema utilizará scripts y procedimientos previamente establecidos para estos casos.

## Flujo general

```text
Técnico
   ↓
Solicitud
   ↓
IA
   ↓
Identificación del procedimiento
   ↓
Base de conocimiento
   ↓
Procedimiento / Script
   ↓
Agente local
   ↓
Equipo del cliente
   ↓
WinBox
   ↓
MikroTik
   ↓
Verificación
   ↓
Registro / Auditoría
