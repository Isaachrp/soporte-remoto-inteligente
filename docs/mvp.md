# 2. Definición del MVP

## 2.1 Objetivo del MVP

La primera versión del sistema tendrá como objetivo agilizar y automatizar procedimientos técnicos repetitivos relacionados con la configuración y soporte de equipos MikroTik de clientes.

El sistema utilizará inteligencia artificial para interpretar las solicitudes del técnico y determinar qué procedimiento corresponde. Un agente local será responsable de ejecutar las acciones autorizadas en el equipo Windows utilizado para proporcionar el soporte remoto.

El sistema utilizará procedimientos y scripts de configuración previamente establecidos, evitando que la inteligencia artificial tenga control directo e ilimitado sobre los equipos de los clientes.

---

## 2.2 Flujo actual

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

## 2.3 Flujo propuesto

El sistema buscará automatizar las tareas repetitivas del proceso manteniendo al técnico como responsable de supervisar y autorizar las acciones correspondientes.

El flujo general propuesto será:

1. El técnico proporciona una solicitud al sistema.
2. La inteligencia artificial interpreta la solicitud.
3. La inteligencia artificial identifica el procedimiento correspondiente.
4. El sistema consulta la base de conocimiento.
5. Se obtiene el procedimiento y el script correspondiente.
6. El sistema identifica los parámetros necesarios para adaptar el procedimiento al cliente.
7. El agente local realiza las acciones autorizadas en el equipo Windows.
8. El agente utiliza las aplicaciones necesarias para realizar el procedimiento.
9. El procedimiento es ejecutado sobre el equipo MikroTik.
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
        AnyDesk
           │
           ▼
   Equipo del cliente
           │
           ▼
         WinBox
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
