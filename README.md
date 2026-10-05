# Soporte Remoto Inteligente y Automatizado

## Primer avance listo para demostrar

Desde PowerShell en esta carpeta ejecute ` .\iniciar-demo.cmd ` y abra la URL
mostrada. El arranque coordina PHP, servidor y agente con claves temporales y una
base nueva. La demo utiliza IA y RouterOS **simulados explícitamente**.

- [Instalación, guion para el asesor y evidencias](docs/18-primer-avance.md).
- [Cómo construir el laboratorio VirtualBox/CHR](docs/19-laboratorio-demostracion.md).
- [Informe del primer avance](docs/20-informe-primer-avance.md).

Autoprueba reproducible: `.\iniciar-demo.cmd --self-test --port 0`.
La configuración ECMP real sigue bloqueada hasta su validación; el laboratorio
real de esta etapa permite diagnóstico de solo lectura por TLS.

Sistema de soporte remoto orientado a agilizar y automatizar procedimientos técnicos repetitivos en equipos MikroTik de clientes.

El sistema utilizará inteligencia artificial para interpretar las solicitudes del técnico y determinar el procedimiento correspondiente. Un agente local será responsable de ejecutar acciones autorizadas en el equipo Windows utilizado para proporcionar el soporte remoto.

## Objetivo

Desarrollar un sistema inteligente capaz de asistir y automatizar procedimientos de soporte técnico sobre equipos MikroTik, reduciendo las tareas manuales y repetitivas realizadas actualmente por los técnicos.

El sistema utilizará procedimientos y scripts previamente definidos, manteniendo supervisión humana sobre las acciones que puedan modificar la configuración de los equipos de los clientes.

## Componentes principales

El sistema contempla los siguientes componentes:

- **AnyDesk:** acceso remoto al equipo del cliente.
- **Agente portátil:** ejecución bajo demanda de acciones autorizadas en Windows y recopilación de información, sin instalación permanente.
- **Inteligencia artificial:** interpretación de solicitudes y selección del procedimiento correspondiente.
- **Automatización:** ejecución de tareas repetitivas necesarias para realizar los procedimientos.
- **Base de conocimiento:** almacenamiento de procedimientos, scripts, parámetros, manuales y soluciones.
- **Registro y auditoría:** almacenamiento de las acciones realizadas y sus resultados.
- **Aprobación humana:** supervisión y autorización de acciones sensibles.

## MVP

La primera versión del sistema se limita exclusivamente a un procedimiento de configuración para equipos MikroTik:

1. ECMP — Balanceo ECMP.

El sistema utilizará el script y el procedimiento previamente establecidos para ECMP. Cualquier otro procedimiento, incluidos PCC y Hotspot, queda fuera del alcance del MVP y podrá evaluarse para versiones posteriores.

El MVP contempla RouterOS v6 y v7 mediante variantes específicas del procedimiento. Consulte la [matriz inicial de versiones de RouterOS](docs/08-matriz-versiones-routeros.md).

El agente se comunicará con los routers mediante la API nativa de RouterOS, utilizando preferentemente `api-ssl` sobre TCP 8729. Consulte la [selección del canal de comunicación](docs/09-canal-comunicacion-mikrotik.md).

Para la primera versión, el agente será una aplicación portátil para Windows: se ejecutará bajo demanda y no requerirá instalación ni un servicio permanente. Consulte la [modalidad de ejecución del agente](docs/10-modalidad-agente.md).

Los scripts ECMP seguirán siendo generados por el sistema PHP existente. El nuevo sistema complementará ese flujo mediante validación, aprobación, ejecución y auditoría. Consulte el [inventario inicial de scripts ECMP](docs/11-inventario-scripts-ecmp.md).

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
RouterOS API (`api-ssl`)
       ↓
MikroTik
   ↓
Verificación
   ↓
Registro / Auditoría
```

## Implementación MVP local (30-09-2026)

Para la primera prueba con un **CHR v7**, consulta la
[guía del laboratorio y diagnóstico de solo lectura](docs/16-primer-laboratorio-chr-v7.md).
El agente incorpora `--diagnose`: prueba API TLS sin servidor ni tokens y genera
un informe JSON. Tres interfaces bastan para esta lectura; el laboratorio ECMP
previsto requiere cuatro. La configuración ECMP v7 sigue pendiente de implementación
y validación con el equipo real.

Ya existe un flujo ejecutable con FastAPI, LangGraph, SQLite, generador PHP real y agente independiente. La interfaz del técnico se sirve en `/`; el contrato interactivo está en `/docs`.

La [arquitectura de IA integrada](docs/17-arquitectura-ia-mvp.md) añade planes
Pydantic, validación determinista del catálogo, aprobación vinculada al plan y
análisis estructurado de resultados. Reutiliza los endpoints y el agente existentes;
el proveedor OpenAI es sustituible por simulación explícita para pruebas sin consumo.

**No hay versiones RouterOS certificadas. Las escrituras reales están bloqueadas.** La demostración utiliza explícitamente IA y transporte RouterOS simulados; no existe sustitución automática ante fallos reales. La variante heredada v6 se usa únicamente en simulación. v7 permanece pendiente.

- [Instalación, configuración, arranque y ejemplo completo](docs/12-ejecucion-mvp.md).
- [Arquitectura implementada, seguridad y recuperación](docs/13-implementacion-mvp.md).
- [Entrega, resultados de pruebas y limitaciones](docs/14-entrega-mvp.md).
- [Matriz de compatibilidad y evidencia pendiente](docs/08-matriz-versiones-routeros.md).

Pruebas locales (Python 3.12 y PHP en `PATH`, o variable `PHP_EXE`):

```powershell
py -3.12 -m venv .venv-mvp
.\.venv-mvp\Scripts\python.exe -m pip install -r tests/requirements.lock
.\.venv-mvp\Scripts\python.exe -m pytest -q
```

Los entornos anteriores se conservan. El agente tiene dependencias independientes en `agent/requirements.lock`; el servidor, en `server/requirements.lock`. No se requiere Docker, Redis ni un servicio de Windows.
