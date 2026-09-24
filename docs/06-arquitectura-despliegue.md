# 6. Arquitectura de despliegue

## 1. Objetivo

Definir dónde se ejecutará cada componente del sistema de soporte remoto inteligente y cómo se relacionan los diferentes equipos involucrados durante una operación.

La arquitectura deberá considerar el equipo del técnico, la computadora del cliente y la infraestructura central del sistema.

## 2. Entornos

El sistema contempla inicialmente tres entornos principales:

### 2.1. Equipo del técnico

Es el equipo utilizado por el técnico para iniciar y supervisar los procedimientos de soporte.

Desde este equipo actualmente se utiliza AnyDesk para acceder a la computadora del cliente.

El técnico podrá utilizar el sistema principal para:

* Iniciar procedimientos.
* Proporcionar información.
* Revisar resultados.
* Autorizar acciones.
* Supervisar operaciones.

### 2.2. Computadora del cliente

Es el equipo Windows al que el técnico accede mediante AnyDesk.

Actualmente, desde esta computadora:

1. Se abre WinBox.
2. Se introducen los datos del MikroTik.
3. Se establece conexión con el router.
4. Se realizan las configuraciones.
5. Se verifican los resultados.

La ejecución del agente local en esta computadora no se establece como decisión definitiva.

Aunque este equipo tiene acceso directo a WinBox y al MikroTik, instalar y ejecutar software adicional en la PC del cliente puede generar problemas relacionados con:

* Compatibilidad del sistema operativo.
* Permisos de instalación y ejecución.
* Antivirus o políticas de seguridad.
* Rendimiento del equipo.
* Restricciones de red.
* Mantenimiento y actualización del agente.
* Privacidad y control sobre el equipo del cliente.
* Disponibilidad de los componentes necesarios.

Por este motivo, se deberán evaluar alternativas antes de definir la ubicación definitiva del agente.

Una posibilidad es que el agente se ejecute en el equipo del técnico o en otra computadora controlada por la empresa y utilice AnyDesk para interactuar remotamente con la PC del cliente.

En ese escenario, el agente podría:

1. Conectarse a la PC del cliente mediante AnyDesk.
2. Interactuar con la sesión remota.
3. Abrir o utilizar WinBox en la PC del cliente.
4. Ejecutar las acciones necesarias.
5. Obtener información y resultados.
6. Enviar los resultados al sistema principal.

Sin embargo, esta alternativa dependerá de las capacidades de automatización e integración que ofrezca AnyDesk. No se debe asumir que AnyDesk permitirá controlar todas sus funciones de forma programática ni que será posible automatizar de manera confiable cada interacción visual.

También deberá evaluarse si el agente puede ejecutar WinBox directamente desde el equipo del técnico o desde otro equipo controlado, conectándose al MikroTik sin utilizar la PC del cliente. Esta opción podría ser más simple y segura si existe conectividad de red suficiente y si el acceso al router puede realizarse sin depender de la red local del cliente.

Por lo tanto, la arquitectura deberá comparar al menos las siguientes alternativas:

### Alternativa A: agente en la PC del cliente

```text
Agente en PC del cliente
        ↓
WinBox
        ↓
MikroTik
```

Ventajas:

* Acceso directo al entorno actual.
* No depende necesariamente de automatizar AnyDesk.
* Puede utilizar la conectividad local existente.

Desventajas:

* Requiere instalar software en la PC del cliente.
* Puede haber problemas de compatibilidad.
* Requiere permisos y mantenimiento.
* Aumenta la superficie de seguridad.
* Puede no ser aceptable para todos los clientes.

### Alternativa B: agente en el equipo del técnico

```text
Agente en equipo del técnico
        ↓
AnyDesk
        ↓
PC del cliente
        ↓
WinBox
        ↓
MikroTik
```

Ventajas:

* No requiere instalar el agente en la PC del cliente.
* El agente se ejecuta en un entorno controlado.
* Facilita las actualizaciones y el mantenimiento.
* Reduce los requisitos sobre el equipo del cliente.

Desventajas:

* Depende de la automatización de AnyDesk.
* Puede ser más difícil controlar la sesión remota.
* La automatización visual puede ser frágil.
* Requiere que AnyDesk esté disponible y correctamente configurado.

### Alternativa C: agente en otro equipo controlado por la empresa

```text
Agente en equipo controlado
        ↓
Conectividad remota o VPN
        ↓
Red del cliente
        ↓
MikroTik
```

Ventajas:

* El agente no se instala en la PC del cliente.
* El entorno de ejecución puede estar estandarizado.
* Facilita la administración centralizada.
* Puede permitir una integración más estable que la automatización visual.

Desventajas:

* Requiere conectividad directa con el MikroTik.
* Puede requerir VPN, reglas de firewall o configuración adicional.
* No siempre será posible acceder al router desde fuera de la red del cliente.
* Puede aumentar la complejidad de la infraestructura.

### Alternativa D: ejecución manual asistida

```text
Sistema principal
        ↓
Procedimiento y script
        ↓
Técnico mediante AnyDesk
        ↓
WinBox
        ↓
MikroTik
```

Ventajas:

* No requiere instalar un agente.
* Funciona con la infraestructura actual.
* Reduce los problemas de compatibilidad.
* Permite validar el procedimiento antes de automatizarlo.

Desventajas:

* Requiere intervención manual.
* No permite automatización completa.
* Puede aumentar el tiempo de ejecución.
* Depende de la atención del técnico.

## Decisión pendiente

La ubicación del agente queda pendiente de evaluación.

Antes de elegir una alternativa, se deberán realizar pruebas para determinar:

* Si AnyDesk permite la automatización necesaria.
* Si AnyDesk dispone de una API o mecanismo de control adecuado.
* Si el agente puede interactuar de forma confiable con una sesión remota.
* Si WinBox puede ejecutarse desde un equipo externo al cliente.
* Si el MikroTik puede administrarse mediante otra vía, como API, SSH o VPN.
* Qué requisitos de red existen en cada escenario.
* Qué permisos requiere cada alternativa.
* Qué riesgos de seguridad presenta cada opción.
* Qué ocurre si la sesión de AnyDesk se interrumpe.
* Qué alternativa es más fácil de mantener y soportar.

Hasta completar estas pruebas, no se deberá asumir que el agente se ejecutará en la PC del cliente.

La arquitectura deberá mantenerse flexible para permitir inicialmente una modalidad de ejecución manual asistida y posteriormente incorporar automatización en el equipo del técnico, en otro equipo controlado o, únicamente si resulta necesario y viable, en la PC del cliente.

### 2.3. Infraestructura central

Será responsable de alojar los componentes centrales del sistema.

Podrá contener:

* Sistema principal.
* Inteligencia artificial.
* Base de conocimiento.
* Gestión de operaciones.
* Gestión de agentes.
* Gestión de aprobaciones.
* Autenticación y autorización.
* Registro y auditoría.

La infraestructura central no tendrá acceso directo al MikroTik. La comunicación con el equipo del cliente se realizará mediante el agente local instalado en la PC del cliente.

La infraestructura exacta será definida posteriormente.

## 3. Distribución inicial

La distribución conceptual será:

```text
                    INTERNET
                        │
                        │
             ┌──────────┴──────────┐
             │                     │
             ↓                     ↓
      ┌─────────────┐       ┌───────────────┐
      │   Técnico   │       │   Servidor    │
      │             │◄─────►│    central    │
      │ Interfaz    │       │               │
      └──────┬──────┘       │ - Sistema     │
             │              │ - IA           │
             │              │ - KB           │
             │              │ - Auditoría    │
             │              └───────┬───────┘
             │                      │
             │ AnyDesk              │
             ↓                      │
      ┌─────────────────┐           │
      │ PC del cliente  │◄──────────┘
      │                 │
      │ - Agente local  │
      │ - WinBox        │
      └────────┬────────┘
               │
               │
               ↓
        ┌──────────────┐
        │   MikroTik   │
        │   Cliente    │
        └──────────────┘
```

## 4. Equipo del técnico

El equipo del técnico tendrá como función principal proporcionar la interfaz de supervisión.

El técnico podrá:

* Iniciar una operación.
* Seleccionar el procedimiento.
* Introducir parámetros.
* Revisar información.
* Aprobar acciones.
* Visualizar resultados.
* Consultar registros.
* Supervisar el estado del agente.

El técnico no deberá necesitar acceso directo al MikroTik fuera del flujo autorizado del sistema.

La conexión mediante AnyDesk seguirá siendo responsabilidad del técnico durante la primera versión.

## 5. PC del cliente

La PC del cliente será el punto donde se ejecutarán las acciones necesarias para administrar el MikroTik.

Inicialmente se considera que el agente local se ejecutará en este equipo.

El agente tendrá acceso a las herramientas necesarias para realizar el procedimiento.

En el caso de ECMP:

```text
Agente
   ↓
WinBox
   ↓
MikroTik
```

## 6. Servidor central

El servidor central coordinará las operaciones.

Entre sus responsabilidades se consideran:

* Recibir solicitudes.
* Gestionar operaciones.
* Comunicarse con la IA.
* Consultar la base de conocimiento.
* Comunicarse con los agentes.
* Gestionar aprobaciones.
* Recibir resultados.
* Registrar auditoría.

## 7. Flujo de una operación

Un procedimiento típico tendrá el siguiente flujo:

```text
1. Técnico inicia operación
          ↓
2. Sistema central recibe solicitud
          ↓
3. IA identifica procedimiento
          ↓
4. Sistema consulta base de conocimiento
          ↓
5. Se obtienen parámetros y procedimiento
          ↓
6. Sistema localiza agente disponible
          ↓
7. Técnico accede a PC del cliente mediante AnyDesk
          ↓
8. Agente prepara el entorno
          ↓
9. Agente interactúa con WinBox
          ↓
10. Agente obtiene información del MikroTik
          ↓
11. Sistema valida información
          ↓
12. Técnico aprueba si es necesario
          ↓
13. Agente ejecuta procedimiento
          ↓
14. Agente verifica resultado
          ↓
15. Resultado enviado al sistema central
          ↓
16. Sistema registra la operación
          ↓
17. Técnico recibe resultado
```

## 8. Relación con AnyDesk

AnyDesk continuará siendo el mecanismo utilizado para acceder remotamente a la PC del cliente.

En la primera versión, el sistema no controlará directamente AnyDesk.

El técnico realizará la conexión mediante AnyDesk y posteriormente podrá utilizar el agente local para ejecutar las acciones necesarias en la computadora del cliente.

La integración automática con AnyDesk podrá evaluarse posteriormente.

AnyDesk y la comunicación del agente con el servidor serán canales independientes:

```text
Técnico ───────► AnyDesk ───────► PC del cliente

Agente local ◄───────────────────► Servidor central
```

## 9. Disponibilidad del agente

El sistema deberá conocer qué agentes están disponibles y asociados con cada entorno de cliente.

Un agente podrá informar:

* Identificador.
* Estado.
* Versión.
* Sistema operativo.
* Capacidades.
* Última comunicación.

Esto permitirá determinar si el entorno está preparado para ejecutar un procedimiento.

## 10. Asociación entre operación y cliente

Cada operación deberá poder asociarse con:

```text
Operación
   ↓
Técnico
   ↓
Cliente
   ↓
PC del cliente
   ↓
Agente
   ↓
MikroTik
   ↓
Procedimiento
```

Esto permitirá mantener trazabilidad durante todo el proceso.

## 11. Seguridad de la arquitectura

La arquitectura deberá considerar que el agente se encuentra en un equipo externo al servidor central.

Por lo tanto, deberán existir mecanismos para:

* Autenticar agentes.
* Autorizar operaciones.
* Validar solicitudes.
* Proteger la comunicación.
* Evitar que un agente ejecute solicitudes de otro usuario no autorizado.
* Registrar las operaciones.
* Proteger credenciales.
* Limitar las acciones disponibles.

## 12. Consideración sobre la PC del cliente

La ejecución del agente en la PC del cliente implica que el agente tendrá acceso al entorno desde el cual se administra el MikroTik.

Por esta razón, el diseño deberá considerar especialmente:

* Permisos del agente.
* Instalación y actualización.
* Seguridad.
* Protección de credenciales.
* Comunicación con el servidor.
* Aislamiento de acciones.
* Desinstalación.
* Registro de actividad.

## 13. Arquitectura inicial propuesta

La arquitectura inicial queda definida conceptualmente de la siguiente manera:

```text
┌────────────────────┐
│  Equipo del técnico│
│                    │
│  Interfaz          │
│  Supervisión       │
│  Aprobaciones      │
└─────────┬──────────┘
          │
          │ Internet
          │
          ↓
┌────────────────────────────┐
│      Servidor central      │
│                            │
│  Sistema principal         │
│  Inteligencia artificial   │
│  Base de conocimiento      │
│  Gestión de operaciones    │
│  Auditoría                 │
└────────────┬───────────────┘
             │
             │ Internet
             │
             ↓
┌────────────────────────────┐
│      PC del cliente        │
│                            │
│  Agente local              │
│  WinBox                    │
└────────────┬───────────────┘
             │
             ↓
      ┌──────────────┐
      │   MikroTik   │
      └──────────────┘
```

## 14. Estado actual

La arquitectura de despliegue es una propuesta inicial.

Todavía deben definirse:

* Infraestructura del servidor.
* Requisitos del agente.
* Método de instalación del agente.
* Método de autenticación.
* Comunicación agente-servidor.
* Requisitos de red.
* Puertos necesarios.
* Seguridad.
* Actualización del agente.
* Recuperación ante fallos.
* Gestión de múltiples clientes y agentes.
