# Soporte Remoto Inteligente y Automatizado

## Segundo avance: interfaz guiada y análisis previo

Ejecute `.\iniciar-demo.cmd`, ingrese la clave temporal y seleccione el equipo conectado.
Ya no necesita copiar sesiones ni escribir identidad y puerto administrativo: el flujo
**Elegir equipo → Analizar → Preparar propuesta → Autorizar → Verificar** obtiene los
datos del agente y muestra supuestos y bloqueos antes de generar el script.

- [Informe, pruebas de laboratorio y guion para el asesor](docs/25-segundo-avance.md).
- [Evidencias reproducibles del segundo avance](docs/evidencias/segundo-avance-2026-10-22/README.md).
- Autoprueba: `.\iniciar-demo.cmd --self-test --port 0`.
- Entrega de fuentes: `.\.venv-mvp\Scripts\python.exe scripts/package_delivery.py`.

La adaptación real sigue limitada a la base preparada CHR v7; los gateways y el
costo igual de los enlaces requieren confirmación. IA y RouterOS son simulados en
la demo. El laboratorio real se inicia por separado con `.\iniciar-lab-v7.cmd`.

## Ensayo supervisado v7

El laboratorio CHR 7.24.5 ya tiene lecturas TLS y conectividad individual reportadas.
Se dispone de una [vista previa PHP v7 offline](docs/22-vista-previa-ecmp-v7.md),
limitada a dos WAN de igual costo y direcciones existentes. Generar el borrador
con `.\.venv-mvp\Scripts\python.exe scripts/preview_v7.py` no aplica cambios.
La [integracion experimental v7](docs/24-integracion-supervisada-v7.md) permite
prechequeo, generacion, aprobacion y ejecucion exclusivamente en el laboratorio
preparado 7.24.5. Esta deshabilitada por defecto y no certifica la version.
El ensayo automatico sobre el CHR real sigue pendiente; la configuracion manual
y las pruebas comunicadas estan en el [registro del laboratorio](docs/23-resultados-laboratorio-manual-v7.md).

## Primer avance listo para demostrar

Desde PowerShell en esta carpeta ejecute ` .\iniciar-demo.cmd ` y abra la URL
mostrada. El arranque coordina PHP, servidor y agente con claves temporales y una
base nueva. La demo utiliza IA y RouterOS **simulados explícitamente**.

- [Instalación, guion para el asesor y evidencias](docs/18-primer-avance.md).
- [Cómo construir el laboratorio VirtualBox/CHR](docs/19-laboratorio-demostracion.md).
- [Informe del primer avance](docs/20-informe-primer-avance.md).

Autoprueba reproducible: `.\iniciar-demo.cmd --self-test --port 0`.
El arranque de demostracion conserva simulacion completa. El laboratorio real
permite diagnostico TLS y, con el arranque experimental separado, un ensayo
supervisado sobre una base preparada.

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
previsto requiere cuatro. La variante experimental v7 esta integrada para el
laboratorio preparado; su aplicacion automatica real sigue pendiente de validacion.

Ya existe un flujo ejecutable con FastAPI, LangGraph, SQLite, generador PHP real y agente independiente. La interfaz del técnico se sirve en `/`; el contrato interactivo está en `/docs`.

La [arquitectura de IA integrada](docs/17-arquitectura-ia-mvp.md) añade planes
Pydantic, validación determinista del catálogo, aprobación vinculada al plan y
análisis estructurado de resultados. Reutiliza los endpoints y el agente existentes;
el proveedor OpenAI es sustituible por simulación explícita para pruebas sin consumo.

**No hay versiones RouterOS certificadas. Las escrituras reales estan bloqueadas por defecto.** La demostracion utiliza explicitamente IA y transporte RouterOS simulados; no existe sustitucion automatica ante fallos reales. La variante heredada v6 se usa unicamente en simulacion. El ensayo v7 exige opt-in en servidor y agente y la version/topologia exactas de laboratorio.

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
