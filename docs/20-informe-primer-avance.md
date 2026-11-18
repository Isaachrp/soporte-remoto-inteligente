# Informe de primer avance

**Proyecto:** Soporte Remoto Inteligente y Automatizado para MikroTik  
**Fecha:** 4 de octubre de 2026  
**Etapa:** prototipo integrado de soporte supervisado, con demostración local reproducible

## Problema y objetivo

La configuración de equipos de red durante el soporte técnico requiere capturar
parámetros, elegir procedimientos, aplicar instrucciones y revisar resultados.
La ejecución manual dificulta mantener un registro uniforme y comprobar qué se
autorizó antes de modificar un equipo.

El proyecto propone un sistema que centraliza las solicitudes del técnico,
selecciona procedimientos de un catálogo controlado y coordina un agente local.
El técnico conserva la aprobación de los cambios y el sistema registra las
acciones y sus resultados. Este primer avance se concentra en ECMP.

## Alcance logrado

Se dispone de un recorrido ejecutable desde una interfaz web hasta un agente
independiente, con generación PHP real y almacenamiento SQLite. La demostración
usa explícitamente IA y RouterOS simulados para evaluar la integración sin
intervenir equipos de servicio ni consumir un proveedor externo.

| Componente | Implementación y alcance |
|---|---|
| Interfaz del técnico | Solicitud, parámetros WAN/LAN, revisión, aprobación/rechazo, resultado y exportación JSON |
| Servidor | FastAPI y flujo LangGraph; validación de estados, parámetros y acciones |
| Interpretación | Contratos estructurados y catálogo cerrado; proveedor sustituible, simulación explícita en la entrega |
| Generador | Integración HTTP con PHP existente; script y huellas de integridad |
| Agente | Proceso independiente con consulta de tareas, prechequeo y ejecución autorizada |
| Autorización | Vinculada al artefacto, destino, parámetros y estado previo; consumo único y vencimiento |
| Verificación | Contraste de operaciones con tablas del simulador; WAN/LAN se informan como no verificadas |
| Auditoría | Eventos y resultados persistidos; informe autenticado por solicitud |
| Diagnóstico real | Modo independiente de solo lectura mediante API TLS 8729; ejecución sobre CHR pendiente |

## Arquitectura

```text
Técnico → interfaz web → FastAPI / LangGraph → intérprete y validación de catálogo
                                 |
                         generador PHP por HTTP
                                 |
                      script + operaciones + huellas
                                 |
                       aprobación explícita del técnico
                                 |
                    agente independiente → RouterOS simulado
                                 |
                   verificación → SQLite → informe y auditoría

Ensayo real independiente: agente --diagnose → api-ssl → CHR de laboratorio
```

El proveedor de IA no autoriza directamente escrituras ni genera comandos libres
para ejecutarlos. Sus propuestas deben cumplir el catálogo y las validaciones.
Los parámetros de red se capturan explícitamente en el formulario.

## Trabajo realizado para esta entrega

Sobre la implementación existente se añadió un arranque único para Windows que
coordina los tres procesos, genera credenciales temporales y separa cada ensayo
en su propia base de datos. Se añadió una autoprueba reproducible con evidencias
y hashes, un endpoint autenticado de informe y acceso a la exportación desde la
interfaz. La interfaz identifica los modos de IA/router y muestra los estados y
comprobaciones con textos comprensibles.

Se prepararon instrucciones de instalación, guion de exposición, construcción
del laboratorio y criterios de aceptación. Se conservaron los cambios locales
previos del proyecto.

## Validación realizada

Pruebas ejecutadas el 4 de octubre de 2026 en el entorno local Windows:

| Validación | Resultado observado |
|---|---|
| Suite automatizada completa | **119 aprobadas, 1 omitida**, 28.21 segundos |
| Dependencias Python | `pip check`: sin dependencias incompatibles |
| Formato de cambios rastreados | `git diff --check`: sin errores |
| Autoprueba con PHP, servidor y agente separados | Aprobada; salida 0 |
| Rechazo de solicitud | Sin consumo de aprobación ni ejecución autorizada |
| Hash de aprobación alterado | HTTP 409 |
| Aprobación reutilizada | HTTP 409 |
| Aplicación simulada de dos WAN | 19 comprobaciones estructurales aprobadas, 0 fallidas, 2 no realizadas |
| Exportación API | Informe completo autenticado; prueba de ausencia de tokens del sistema |
| Recorrido en navegador | Solicitud, aprobación, resultado y consulta persistente después de recargar |

La prueba omitida requiere un laboratorio real autorizado y configurado. La suite
incluye una advertencia de deprecación de AnyIO usada por Starlette, que no impidió
su ejecución. Los ensayos de empaquetado incluidos utilizan el binario portátil
ya presente; esta entrega no reconstruyó el ejecutable.

El navegador integrado mostró el resultado y solicitó el informe con HTTP 200;
su herramienta no confirmó el guardado de la descarga JSON. La exportación por
API y el guardado de archivos mediante `--self-test` sí se comprobaron. Para una
entrega reproducible se incluyen esos archivos guardados, independientemente del
comportamiento de descarga del navegador.

Evidencias: [índice y archivos de aceptación](evidencias/primer-avance-2026-10-04/README.md).
La captura de interfaz corresponde a una segunda ejecución manual del mismo
caso; su ID difiere del informe de autoprueba.

## Interpretación de resultados

El estado `configuration_with_warnings` confirma que las operaciones previstas
aparecen en las tablas del simulador. No confirma acceso a Internet, reparto
de tráfico entre enlaces, rendimiento, recuperación de WAN ni conectividad
de un cliente LAN. Esas dos últimas verificaciones permanecen expresamente
marcadas como no realizadas en el resultado.

El avance demuestra la viabilidad de integrar la generación existente con un
flujo supervisado y auditable. No constituye todavía una solución de producción
ni una certificación de ECMP en MikroTik real.

## Laboratorio y siguiente etapa

La primera prueba física propuesta utiliza Windows conectado por una red de
solo anfitrión a un CHR de VirtualBox. Se configura API TLS, una CA confiable y
un usuario de lectura. El agente comprueba identidad, versión, interfaz y
dirección administrativa, y genera un informe independiente.

La ampliación usa cuatro puertos en CHR-LAB: dos WAN aisladas, una LAN para un
cliente y administración dedicada. Dos routers auxiliares proporcionan las
salidas de prueba. Los pasos y direcciones se especifican en la
[guía de laboratorio](19-laboratorio-demostracion.md).

Trabajo pendiente, en orden de dependencia:

1. Construir el laboratorio y obtener evidencia real de lectura TLS.
2. Fijar la versión exacta de RouterOS y adaptar la variante ECMP v7.
3. Ensayar aplicación y verificación de rutas, NAT, DHCP y acceso administrativo.
4. Medir tráfico del cliente y pérdida/recuperación de cada WAN.
5. Validar el proveedor de IA real y evaluar precisión sobre solicitudes definidas.
6. Evaluar distribución portátil en otros equipos y controles de operación multiusuario.

Las escrituras reales permanecen bloqueadas. No se realizaron llamadas a OpenAI
ni conexiones a un MikroTik real durante esta preparación.

## Reproducción

```powershell
.\iniciar-demo.cmd
# Autoprueba independiente, sin aprobación manual ni router real:
.\iniciar-demo.cmd --self-test --port 0
# Suite de pruebas:
.\.venv-mvp\Scripts\python.exe -m pytest -q
```

La instalación y la secuencia exacta de la exposición están en el
[documento 18](18-primer-avance.md).

