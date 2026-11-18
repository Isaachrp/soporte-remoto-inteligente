# Matriz de evidencias y límites

Fecha de corte: 6 de noviembre de 2026. Se distingue evidencia local inspeccionada, resultados comunicados por el alumno y resultados de pruebas reportados en esta sesión de trabajo.

## A. ECMP: conservación y verificación

- Entrega: `cdee4e78-bf13-4f20-9749-7c6b89e33acc`.
- Base local inspeccionada: entrega autorizada, proveedor `openrouter`, recomendaciones guardadas, política `preserve_existing`, cero operaciones por aplicar.
- Resultado original: comunicado por el alumno en el chat tras ejecutar el EXE Windows con Wine en Linux.
- Resultado: `configuration_with_warnings`, `completed: 0`, `preserved: 7`.
- Comprobaciones comunicadas: siete elementos aprobados; direcciones, interfaces, rutas conectadas, conteos y señal ECMP aprobados.
- Pendiente: tráfico WAN y conectividad LAN, ambos `not_performed`.

**Conclusión defendible:** el ensayo verificó configuración coincidente sin agregar duplicados. No acredita una aplicación desde cero ni balanceo medido de tráfico.

## B. PCCrV7: fallo de ejecución

- Entrega: `c161bdb4-ff67-4752-ab78-39318c1f83d3`.
- Base local inspeccionada: entrega autorizada, proveedor `openrouter`, recomendaciones guardadas y política `original_php`.
- Diagnóstico previo: cuatro direcciones, seis rutas, dos NAT, un servidor DHCP y un pool; no era un router vacío.
- Terminal aportada: primer intento cancelado por escribir `APLICAR -lab-router`; segundo intento confirmado correctamente con `APLICAR lab-router`.
- Cuenta utilizada: `ecmp-reader`. Sus permisos efectivos no se comprobaron; el nombre no basta para concluir que es de solo lectura.
- Resultado comunicado: `intervention_required`, `functionality_verified: false`.

**Conclusión defendible:** la entrega se generó y se intentó ejecutar, pero no hay evidencia suficiente para afirmar aplicación completa, ausencia de cambios o causa exacta. No presentar como éxito ni recomendar repetir a ciegas.

El reporte del ejecutable se mejoró después para distinguir etapa y categoría del fallo sin exponer mensajes sensibles. Cuatro pruebas locales pasaron; todavía no hay un nuevo resultado real con ese reporte.

## C. Recomendaciones de OpenRouter

Las dos entregas inspeccionadas contienen recomendaciones guardadas y no tienen `analysis_error`. La segunda incluye ECMP, PCCrV7, Firewall y Hotspot. Esto respalda que el flujo obtuvo recomendaciones; no demuestra que todas sean técnicamente acertadas ni ejecutables en ese estado.

La IA usa evidencia parcial. Por ejemplo, una LAN con DHCP no demuestra por sí sola que sea necesario Hotspot. La selección final sigue siendo del técnico.

## D. Pruebas automáticas reportadas

| Ejecución | Resultado | Interpretación |
|---|---|---|
| Ampliación general del catálogo, excluyendo compilaciones | 231 aprobadas, 1 omitida, 1 fallida | Falló el arranque del agente portable; la prueba equivalente con Python pasó |
| Empaquetado del ejecutable del catálogo | 1 aprobada | EXE construido y validado sin conectar al router en esa prueba |
| Integración OpenRouter y regresión seleccionada | 122 aprobadas, 4 excluidas | Respuestas de proveedor controladas, sin validar disponibilidad permanente del servicio |
| Retirada del certificado del ejecutable ECMP | Prueba de transporte aprobada; compilación completada; validación de ejecución bloqueada por Windows | No presentar ese bloqueo como prueba aprobada de ejecución en Windows |
| Reporte por etapas del ejecutable del catálogo | 4 aprobadas | Casos de permisos, sintaxis, limpieza y ejecución parcial con doble de router |

Estos conjuntos se solapan y corresponden a momentos diferentes: **no sumar los números**. Las pruebas con dobles de RouterOS no equivalen a ensayos físicos. No se repitió la suite ni se probó el laboratorio al preparar este dossier.

## E. Archivos originales para conservar localmente

Conserva el JSON diagnóstico que utilizaste, los JSON originales de resultado del escritorio Linux y la salida de terminal. El ZIP documental incluye solo un resumen identificado como tal. No incluye el paquete ejecutable completo porque puede contener parámetros o credenciales generadas, y tiene una vigencia limitada.

No compartir `.env`, claves API, claves temporales del técnico, contraseñas, bases SQLite completas ni resultados sin revisar. Las direcciones mostradas en el diagrama y ejemplos corresponden al laboratorio descrito, no a una red de cliente anonimizada automáticamente.
