# Avance: sistema central de soporte MikroTik asistido por IA

**Fecha de corte:** 6 de noviembre de 2026.  
**Proyecto:** Soporte Remoto Inteligente y Automatizado.  
**Estado:** prototipo funcional con validación parcial en laboratorio.

## Problema y objetivo

La preparación manual de configuraciones requiere consultar el estado del router, elegir un procedimiento, capturar parámetros y conservar evidencia de lo realizado. El proyecto organiza ese proceso para que un técnico trabaje con un diagnóstico previo y autorice una entrega asociada al equipo del cliente.

El objetivo de este avance fue ampliar el servidor central para integrar el catálogo del generador PHP existente, incorporar recomendaciones de IA a partir del diagnóstico y producir un ejecutable independiente. El generador PHP se conserva sin modificaciones en esta ampliación.

## Arquitectura actual

```text
PC del cliente                         PC del técnico
Agente de diagnóstico                  Servidor central
  │ API RouterOS                         │
  ▼                                      │
MikroTik → diagnóstico JSON ──────────────┤
                                         ├─ IA OpenRouter: sugerencias
                                         ├─ Técnico: selección y parámetros
                                         ├─ PHP existente: script
                                         ├─ Validación y autorización
                                         └─ Entrega JSON / ejecutable
PC del cliente                           │
Ejecutable independiente ◄───────────────┘
  └─ Comprobación del router → confirmación → ejecución/verificación → resultado
```

El agente de diagnóstico y el ejecutable de resultado cumplen funciones distintas. El primero recoge información; el segundo lleva integrada una entrega autorizada. El agente actual no importa por sí mismo todas las entregas JSON. La ejecución independiente no necesita conectarse al servidor central; la recomendación por OpenRouter sí requiere Internet.

El servidor usa FastAPI, LangGraph para el análisis y los flujos definidos, validación con Pydantic, almacenamiento SQLite y el generador PHP. El técnico trabaja desde una interfaz web local.

## Funciones implementadas

- Importación del diagnóstico JSON obtenido por el agente.
- Proyección de datos para la IA, excluyendo identidad, comentarios y credenciales de conexión al router.
- Sugerencias entre opciones del catálogo; el técnico conserva la decisión.
- Catálogo de 14 opciones del menú PHP más el generador independiente OpenVPN. La disponibilidad de ejecución depende de la versión y requisitos de la plantilla.
- Captura de parámetros, revisión de script y autorización antes de descargar.
- Entregas independientes con diagnóstico asociado, controles de integridad, vigencia y resultado local.
- ECMP V7: conservar elementos coincidentes, agregar solo faltantes o verificar sin escrituras si ya está completo.
- Otras configuraciones: ejecutar el script original PHP con autorización; no equivalen a una migración automática desde la configuración existente.
- Interfaz reducida a diagnóstico, configuración y descarga; detalles técnicos plegados.

El modo actual usa OpenRouter con modelos gratuitos. No hay cambio automático a un proveedor de pago. Sus límites o indisponibilidad se muestran como errores y permiten elegir manualmente del catálogo.

## Evidencia disponible

| Caso | Observado | Lo que permite afirmar |
|---|---|---|
| Recomendación IA | Dos entregas locales contienen sugerencias y `ai_mode: openrouter` | Hay respuestas de recomendación guardadas, no solo un rótulo de proveedor |
| ECMP existente | Resultado comunicado: 0 operaciones nuevas, 7 elementos conservados y comprobaciones estructurales aprobadas | Se verificó la configuración existente sin duplicarla |
| PCCrV7 | Resultado comunicado: `intervention_required` | Hubo un fallo; no se conoce aún el paso ni se descartan cambios parciales |
| Catálogo PHP | Pruebas locales de generación de las 15 opciones | Se integró la generación, no se certificó cada procedimiento en hardware |
| Pruebas automáticas | Regresión previa: 231 aprobadas, 1 omitida y 1 fallida; después se ejecutaron conjuntos específicos | Existe cobertura automatizada con una incidencia conocida del agente portable |

La prueba ECMP fue ejecutada por el alumno en Linux mediante Wine con un ejecutable Windows. Eso no equivale a disponer de un ejecutable de resultado Linux nativo.

## Límites y trabajo pendiente

1. Diagnosticar PCCrV7: comprobar permisos de la cuenta utilizada, estado del router y compatibilidad del script original. El diagnóstico previo ya contenía ECMP, NAT y DHCP.
2. El ejecutable anterior guardó un error demasiado general. Se implementó un reporte por etapa y categoría, probado localmente; falta usar esa nueva versión en el laboratorio.
3. Completar pruebas de tráfico WAN/LAN y conmutación ante fallos. Las comprobaciones de tablas no demuestran conectividad completa.
4. Validar cada plantilla en un escenario compatible. Tener una opción en el catálogo no certifica su aplicación real.
5. Resolver la incidencia de arranque del agente portable en la prueba integral; la ejecución mediante Python pasó.
6. El diagnóstico actual no recoge todas las tablas de Hotspot, colas, certificados y PPP. La IA no puede deducir su ausencia.

Para esta fase se usa API 8728 sin certificado, a solicitud del alumno; requiere LAN o VPN y no cifra por sí misma las credenciales. La IA recomienda y puede equivocarse: no genera libremente el script ni sustituye la revisión técnica. Los hashes comprueban integridad, pero no son una firma digital del distribuidor.

## Propuesta de siguiente hito

Acordar con el asesor la validación completa de un procedimiento adicional, con escenario preparado, permisos revisados, evidencia antes/después y pruebas de conectividad. Esta propuesta no se ejecuta como parte de la preparación de la entrega.
