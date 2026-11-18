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

El agente podrá ejecutarse en esta computadora como aplicación portátil cuando sea el equipo autorizado con conectividad hacia el MikroTik.

Aunque este equipo tiene acceso directo al MikroTik, ejecutar software adicional en la PC del cliente puede generar problemas relacionados con:

* Compatibilidad del sistema operativo.
* Permisos de ejecución.
* Antivirus o políticas de seguridad.
* Rendimiento del equipo.
* Restricciones de red.
* Distribución y sustitución del paquete portátil.
* Privacidad y control sobre el equipo del cliente.
* Disponibilidad de los componentes necesarios.

Por este motivo, se deberán evaluar alternativas antes de definir la ubicación definitiva del agente.

Una posibilidad es que el agente se ejecute en el equipo del técnico o en otra computadora controlada por la empresa y utilice AnyDesk para interactuar remotamente con la PC del cliente.

En ese escenario, el agente deberá disponer de conectividad IP hacia el MikroTik y utilizar la API nativa de RouterOS. AnyDesk podrá utilizarse en paralelo por el técnico para supervisión o contingencia, pero no será el transporte del canal automatizado.

También deberá evaluarse si el agente puede conectarse desde el equipo del técnico o desde otro equipo controlado mediante VPN o una red privada. Esta opción puede simplificar la automatización si existe conectividad suficiente hacia `api-ssl` sin exponer el servicio directamente a Internet.

Por lo tanto, la arquitectura deberá comparar al menos las siguientes alternativas:

### Alternativa A: agente portátil en la PC del cliente

```text
Agente en PC del cliente
        ↓
RouterOS API (`api-ssl`)
        ↓
MikroTik
```

Ventajas:

* Acceso directo al entorno actual.
* No depende necesariamente de automatizar AnyDesk.
* Puede utilizar la conectividad local existente.

Desventajas:

* Requiere copiar y ejecutar temporalmente el paquete en la PC del cliente.
* Puede haber problemas de compatibilidad.
* Requiere permisos y mantenimiento.
* Aumenta la superficie de seguridad.
* Puede no ser aceptable para todos los clientes.

### Alternativa B: agente portátil en el equipo del técnico

```text
Agente en equipo del técnico
        ↓
VPN o red privada
        ↓
RouterOS API (`api-ssl`)
        ↓
MikroTik
```

Ventajas:

* No requiere ejecutar el agente en la PC del cliente.
* El agente se ejecuta en un entorno controlado.
* Facilita las actualizaciones y el mantenimiento.
* Reduce los requisitos sobre el equipo del cliente.

Desventajas:

* Requiere conectividad IP segura hacia el MikroTik.
* Puede requerir VPN, rutas y reglas de firewall adicionales.
* El servicio `api-ssl` debe estar preparado previamente en el router.

### Alternativa C: agente portátil en otro equipo controlado por la empresa

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

* El agente no se ejecuta en la PC del cliente.
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

## Decisión para el MVP

El agente se distribuirá como una aplicación portátil para Windows, sin instalación permanente, servicio residente ni autoarranque.

El técnico lo iniciará bajo demanda en un equipo autorizado con conectividad segura hacia el servidor central y `api-ssl` del MikroTik. El equipo concreto podrá variar por operación: PC del cliente, equipo del técnico conectado mediante VPN o un equipo controlado por la empresa.

Las pruebas deberán determinar:

* Desde qué ubicación existirá conectividad IP segura hacia `api-ssl`.
* Cómo se establecerá la VPN o red privada cuando el agente sea externo.
* Cómo se aprovisionarán certificados, cuentas de servicio y reglas de firewall.
* Qué requisitos de red existen en cada escenario.
* Qué permisos requiere cada alternativa.
* Qué riesgos de seguridad presenta cada opción.
* Qué ocurre si la sesión de AnyDesk se interrumpe.
* Qué alternativa es más fácil de mantener y soportar.

La ejecución manual asistida quedará como contingencia cuando no sea posible utilizar el agente portátil. Los requisitos de empaquetado, ejecución y limpieza se detallan en [Modalidad de ejecución del agente](10-modalidad-agente.md).

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

La infraestructura central no tendrá acceso directo al MikroTik. La comunicación se realizará mediante una instancia temporal del agente portátil ejecutada en un equipo con acceso autorizado al router.

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
      │ Equipo autorizado│◄─────────┘
      │                 │
      │ - Agente portátil│
      │ - Cliente API   │
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

Cuando sea necesario utilizar la PC del cliente, la conexión mediante AnyDesk seguirá siendo responsabilidad del técnico durante la primera versión.

## 5. Equipo de ejecución del agente

El agente portátil se ejecutará bajo demanda en un equipo Windows autorizado. En muchos casos podrá ser la PC del cliente, pero también podrá ser el equipo del técnico u otro equipo controlado por la empresa si dispone de VPN o conectividad privada hacia el router.

No se instalará como servicio ni permanecerá activo después de finalizar la sesión.

En el caso de ECMP:

```text
Agente
   ↓
RouterOS API (`api-ssl`)
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
6. Sistema prepara la operación y valida la versión requerida del agente
          ↓
7. Técnico inicia el agente portátil en el equipo autorizado
          ↓
8. Agente se registra temporalmente y prepara el entorno
          ↓
9. Agente establece sesión con la API de RouterOS
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

Cuando el equipo autorizado sea la PC del cliente, el técnico realizará la conexión mediante AnyDesk e iniciará manualmente el agente portátil.

La integración automática con AnyDesk podrá evaluarse posteriormente.

AnyDesk y la comunicación del agente con el servidor serán canales independientes:

```text
Técnico ───────► AnyDesk ───────► PC del cliente

Agente local ◄───────────────────► Servidor central
```

## 9. Disponibilidad del agente

El sistema deberá conocer qué sesiones temporales del agente están disponibles y asociadas con cada entorno de cliente.

Un agente podrá informar:

* Identificador.
* Estado.
* Versión.
* Sistema operativo.
* Capacidades.
* Última comunicación.

Esto permitirá determinar si el entorno está preparado para ejecutar un procedimiento. Al finalizar el proceso del agente, su estado deberá cambiar a `offline` y la sesión no podrá reutilizarse.

## 10. Asociación entre operación y cliente

Cada operación deberá poder asociarse con:

```text
Operación
   ↓
Técnico
   ↓
Cliente
   ↓
Equipo de ejecución
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

## 12. Consideraciones sobre el agente portátil

La ejecución del agente portátil implica acceso temporal al entorno desde el cual se administra el MikroTik.

Por esta razón, el diseño deberá considerar especialmente:

* Permisos del agente.
* Integridad y procedencia del paquete.
* Sustitución controlada de versiones.
* Seguridad.
* Protección de credenciales.
* Comunicación con el servidor.
* Aislamiento de acciones.
* Limpieza de archivos temporales y secretos.
* Finalización sin procesos residentes.
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
│ Equipo Windows autorizado │
│                            │
│  Agente portátil           │
│  Cliente RouterOS API      │
└────────────┬───────────────┘
             │
             │ api-ssl / TCP 8729
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
* Formato y firma del paquete portátil.
* Método de autenticación.
* Comunicación agente-servidor.
* Requisitos de red.
* Puertos necesarios.
* Seguridad.
* Distribución y sustitución de versiones del agente.
* Recuperación ante fallos.
* Gestión de múltiples clientes y agentes.
