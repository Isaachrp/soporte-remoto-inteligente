# 4. Arquitectura del sistema

## 1. Objetivo

Definir los componentes principales del sistema de soporte remoto inteligente y la relación entre ellos.

La arquitectura deberá permitir interpretar las solicitudes del técnico, consultar procedimientos previamente definidos, generar o utilizar configuraciones autorizadas, ejecutar acciones mediante un agente local y registrar los resultados.

## 2. Componentes principales

El sistema estará compuesto inicialmente por los siguientes componentes:

1. Interfaz del técnico.
2. Sistema de inteligencia artificial.
3. Base de conocimiento.
4. Aplicación existente de generación de scripts.
5. Agente local.
6. WinBox.
7. MikroTik del cliente.
8. Sistema de registro y auditoría.
9. Mecanismo de aprobación humana.

## 3. Diagrama general

```text
                         ┌──────────────────┐
                         │     Técnico      │
                         └────────┬─────────┘
                                  │
                                  ↓
                         ┌──────────────────┐
                         │ Interfaz /       │
                         │ Sistema principal│
                         └────────┬─────────┘
                                  │
                     ┌────────────┴────────────┐
                     ↓                         ↓
             ┌───────────────┐         ┌─────────────────┐
             │ Inteligencia  │         │ Base de         │
             │ artificial    │◄───────►│ conocimiento    │
             └───────┬───────┘         └─────────────────┘
                     │
                     ↓
             ┌─────────────────┐
             │ Procedimiento   │
             │ autorizado      │
             └────────┬────────┘
                      │
          ┌───────────┴───────────┐
          ↓                       ↓
┌─────────────────────┐   ┌─────────────────────┐
│ Aplicación existente│   │ Mecanismo de        │
│ generadora de       │   │ aprobación humana   │
│ scripts             │   └──────────┬──────────┘
└──────────┬──────────┘              │
           │                         │
           └────────────┬────────────┘
                        ↓
                ┌─────────────────┐
                │   Agente local  │
                └────────┬────────┘
                         │
                         ↓
                      WinBox
                         │
                         ↓
                ┌─────────────────┐
                │     MikroTik    │
                │    del cliente  │
                └────────┬────────┘
                         │
                         ↓
                ┌─────────────────┐
                │ Verificación y  │
                │ resultados      │
                └────────┬────────┘
                         │
                         ↓
                ┌─────────────────┐
                │ Registro y      │
                │ auditoría       │
                └─────────────────┘
```

## 4. Interfaz del técnico

Será el punto mediante el cual el técnico interactuará con el sistema.

Permitirá:

* Iniciar un procedimiento.
* Proporcionar información del cliente.
* Seleccionar o solicitar un procedimiento.
* Revisar la información detectada.
* Autorizar acciones sensibles.
* Consultar el resultado.
* Consultar el historial de operaciones.

La interfaz exacta será definida posteriormente.

## 5. Inteligencia artificial

La inteligencia artificial será responsable de interpretar las solicitudes y coordinar el procedimiento correspondiente.

Sus funciones incluirán:

* Interpretar la solicitud del técnico.
* Identificar el procedimiento.
* Consultar la base de conocimiento.
* Identificar los parámetros requeridos.
* Analizar información obtenida por el agente.
* Identificar posibles inconsistencias.
* Analizar los resultados de las verificaciones.
* Comunicar el resultado al técnico.

La IA estará limitada por los procedimientos y permisos definidos por el sistema.

No tendrá autorización para ejecutar comandos arbitrarios directamente sobre los equipos de los clientes.

## 6. Base de conocimiento

La base de conocimiento almacenará la información necesaria para ejecutar los procedimientos.

Podrá contener:

* Procedimientos técnicos.
* Scripts autorizados.
* Parámetros requeridos.
* Reglas de validación.
* Pasos de ejecución.
* Pasos de verificación.
* Compatibilidad por versión de RouterOS.
* Errores conocidos.
* Soluciones conocidas.
* Información técnica relacionada.

La base de conocimiento será una fuente controlada para las acciones que pueda ejecutar el sistema.

## 7. Aplicación existente

El equipo ya dispone de una aplicación capaz de generar scripts de configuración.

Para ECMP, esta aplicación recibe:

* Cantidad de líneas.
* Velocidad de cada línea.
* Gateway de cada línea.
* IP de cada línea.

A partir de estos datos genera el script correspondiente.

Esta aplicación formará parte del ecosistema del proyecto.

La forma exacta de integración con ella será definida posteriormente.

## 8. Agente local

El agente local será el componente encargado de ejecutar acciones sobre el equipo Windows utilizado durante el soporte.

Entre sus responsabilidades estarán:

* Abrir aplicaciones.
* Interactuar con WinBox.
* Establecer la conexión con el MikroTik.
* Obtener información.
* Ejecutar procedimientos autorizados.
* Ejecutar scripts autorizados.
* Realizar verificaciones.
* Reportar resultados.
* Registrar acciones.

El agente deberá operar bajo permisos y acciones previamente definidos.

## 9. AnyDesk

AnyDesk será utilizado como mecanismo de acceso remoto a la computadora del cliente.

El flujo actual consiste en que el técnico se conecta mediante AnyDesk a la computadora del cliente y desde allí utiliza WinBox.

La arquitectura deberá considerar esta dependencia.

La integración automática con AnyDesk no forma parte todavía de una decisión técnica definitiva.

## 10. WinBox

WinBox es actualmente la herramienta utilizada para administrar los equipos MikroTik desde Windows.

Dentro del flujo inicial será el medio mediante el cual el agente podrá interactuar con el router.

La forma exacta de automatizar WinBox deberá determinarse durante el diseño técnico.

## 11. MikroTik

El MikroTik será el equipo sobre el cual se realizarán las configuraciones.

El sistema deberá:

* Obtener información del router.
* Validar las condiciones necesarias.
* Ejecutar procedimientos autorizados.
* Verificar el resultado.
* Reportar errores o inconsistencias.

El acceso deberá estar controlado y limitado a las operaciones necesarias para el procedimiento.

## 12. Aprobación humana

El técnico conservará el control sobre las acciones sensibles.

Antes de ejecutar modificaciones importantes sobre el router, el sistema podrá solicitar confirmación.

La aprobación deberá quedar registrada en el sistema de auditoría.

## 13. Registro y auditoría

Todas las operaciones relevantes deberán poder registrarse.

El sistema deberá considerar información como:

* Técnico.
* Cliente.
* Equipo.
* Procedimiento.
* Fecha y hora.
* Acciones ejecutadas.
* Parámetros utilizados.
* Aprobaciones.
* Resultados.
* Errores.
* Verificaciones realizadas.

## 14. Flujo de comunicación

De forma conceptual, el flujo será:

```text
Técnico
   ↓
Sistema principal
   ↓
IA
   ↓
Base de conocimiento
   ↓
Procedimiento autorizado
   ↓
Aplicación generadora / parámetros
   ↓
Agente local
   ↓
WinBox
   ↓
MikroTik
   ↓
Resultados
   ↓
Agente local
   ↓
Sistema principal
   ↓
IA
   ↓
Técnico
```

## 15. Principio de seguridad

La arquitectura deberá aplicar el principio de mínimo privilegio.

Cada componente deberá tener únicamente los permisos necesarios para realizar sus funciones.

La inteligencia artificial no deberá tener acceso directo e ilimitado al sistema operativo ni al MikroTik.

Las modificaciones de configuración deberán ejecutarse mediante procedimientos autorizados.

## 16. Estado actual

La arquitectura presentada es conceptual.

Todavía no se han definido:

* Lenguajes de programación.
* Frameworks.
* Base de datos.
* Protocolo de comunicación entre componentes.
* Arquitectura del agente.
* Método de integración con la aplicación generadora.
* Método de automatización de WinBox.
* Método de comunicación con MikroTik.
* Sistema de autenticación.
* Sistema de permisos.
* Infraestructura de despliegue.

Estas decisiones serán tomadas durante las siguientes etapas del proyecto.
