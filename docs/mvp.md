# 2. Definición del MVP

## 2.1 Objetivo del MVP

La primera versión del sistema tendrá como objetivo validar la automatización segura y supervisada del procedimiento de configuración de balanceo ECMP en equipos MikroTik de clientes.

El sistema utilizará inteligencia artificial para interpretar la solicitud del técnico y conducir el flujo definido para ECMP. Un agente portátil para Windows será responsable de ejecutar bajo demanda las acciones autorizadas durante la sesión de soporte.

El sistema utilizará el procedimiento ECMP y el script producido por el sistema PHP existente, evitando que la inteligencia artificial genere o modifique libremente comandos para los equipos de los clientes.

## 2.2 Alcance funcional

El MVP incluye únicamente el caso de uso ECMP y deberá permitir:

1. Recibir una solicitud de configuración ECMP.
2. Recopilar y validar los parámetros requeridos por el procedimiento.
3. Solicitar al sistema PHP existente y validar el script ECMP autorizado.
4. Ejecutar las acciones permitidas mediante el agente local, con las aprobaciones humanas definidas.
5. Verificar el resultado de la configuración.
6. Informar el resultado al técnico y registrar la operación para auditoría.

El procedimiento deberá admitir RouterOS v6 y RouterOS v7 mediante variantes ECMP específicas para cada familia, conforme a la [matriz inicial de versiones de RouterOS](08-matriz-versiones-routeros.md).

El agente se distribuirá sin instalación permanente y se ejecutará únicamente durante la sesión, conforme a la [modalidad de ejecución del agente](10-modalidad-agente.md).

La fuente, contenido e integración del script se definen en el [inventario inicial de scripts ECMP](11-inventario-scripts-ecmp.md).

Quedan fuera del alcance del MVP:

- PCC, Hotspot y cualquier procedimiento distinto de ECMP.
- La generación libre de configuraciones no contempladas por el procedimiento autorizado.
- El acceso ilimitado o no supervisado de la inteligencia artificial a los equipos del cliente.
- La automatización directa de AnyDesk.

La incorporación de otros procedimientos se considerará en versiones posteriores y requerirá una definición, validación y aprobación independientes.

## 2.3 Criterio de finalización

El MVP se considerará funcionalmente completo cuando el flujo ECMP pueda ejecutarse de principio a fin en el entorno de validación: captura y validación de parámetros, preparación y ejecución controlada del script, verificación del resultado, gestión de errores y registro de auditoría.

---

## 2.4 Flujo actual

Actualmente, el procedimiento general de configuración es:

1. El técnico identifica el tipo de configuración que necesita el cliente.
2. Selecciona un script de configuración previamente establecido.
3. Adapta el script de acuerdo con las características del cliente, cuando es necesario.
4. Se conecta mediante AnyDesk al equipo del cliente.
5. Desde el equipo del cliente abre WinBox.
6. Se conecta al router MikroTik.
7. Ingresa y ejecuta el script de configuración.
8. Verifica que la configuración se haya aplicado correctamente.

Este proceso requiere que el técnico realice manualmente varias acciones que pueden ser repetitivas cuando se atienden diferentes clientes con configuraciones similares.

---

## 2.5 Flujo propuesto

El sistema buscará automatizar las tareas repetitivas del proceso manteniendo al técnico como responsable de supervisar y autorizar las acciones correspondientes.

El flujo general propuesto será:

1. El técnico proporciona una solicitud al sistema.
2. La inteligencia artificial interpreta la solicitud.
3. La inteligencia artificial confirma que la solicitud corresponde al procedimiento ECMP; si no corresponde, la rechaza como fuera del alcance del MVP.
4. El sistema consulta la base de conocimiento de ECMP.
5. El sistema PHP existente genera el script ECMP y el nuevo sistema valida el artefacto recibido.
6. El sistema identifica los parámetros necesarios para adaptar el procedimiento ECMP al cliente.
7. El agente local establece una sesión segura con la API de RouterOS.
8. El agente valida la versión y el estado inicial del MikroTik.
9. El procedimiento autorizado es ejecutado mediante la API de RouterOS.
10. El sistema verifica el resultado de la operación.
11. El resultado es informado al técnico.
12. La operación queda registrada en el sistema de auditoría.

De forma general:

```text
Técnico
   │
   │ Solicitud
   ▼
┌──────────────────────┐
│         IA           │
│                      │
│ Interpreta solicitud │
│ Identifica problema  │
│ Selecciona           │
│ procedimiento        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Base de conocimiento │
│                      │
│ Procedimientos       │
│ Scripts              │
│ Parámetros           │
│ Manuales             │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    Agente local      │
│      Windows         │
│                      │
│ Ejecuta acciones     │
│ autorizadas          │
└──────────┬───────────┘
           │
           ▼
 RouterOS API (`api-ssl`)
           │
           ▼
        MikroTik
           │
           ▼
      Configuración
           │
           ▼
       Verificación
           │
           ▼
    Registro / Auditoría
