# 8. Matriz inicial de versiones de RouterOS

## 1. Objetivo

Definir las familias de RouterOS que formarán parte del MVP de ECMP y establecer los criterios mínimos para seleccionar, ejecutar y validar el procedimiento correspondiente.

## 2. Alcance inicial

El MVP deberá contemplar las dos familias principales de RouterOS utilizadas en los equipos MikroTik:

- RouterOS v6.
- RouterOS v7.

El alcance contempla ambas familias, pero no declara compatibilidad operativa por pertenecer a una versión mayor. Cada versión exacta y variante deberá validarse durante las pruebas de laboratorio antes de considerarse certificada.

El generador PHP actual produce una única salida `ECMP` sin declarar la familia de RouterOS. Por ello, las filas v6 y v7 permanecerán pendientes hasta certificar el script actual o implementar variantes separadas, como se detalla en el [inventario inicial de scripts ECMP](11-inventario-scripts-ecmp.md).

## 3. Matriz de compatibilidad

| Familia de RouterOS | Alcance del MVP | Procedimiento | Script requerido | Validación previa | Estado inicial |
|---|---|---|---|---|---|
| v6.x | Incluida | ECMP | Variante ECMP compatible con RouterOS v6 | Detectar la versión exacta y comprobar que la variante v6 esté autorizada | Pendiente de certificación por versiones menores |
| v7.x | Incluida | ECMP | Variante ECMP compatible con RouterOS v7 | Detectar la versión exacta y comprobar que la variante v7 esté autorizada | Pendiente de certificación por versiones menores |
| Anterior a v6 | Excluida | No aplicable | No disponible | Detener la operación | No compatible |
| Posterior a v7 | Excluida hasta validación | No aplicable | No disponible | Detener la operación y solicitar revisión técnica | No validada |
| Versión no identificada | Excluida | No aplicable | No disponible | Detener la operación y solicitar intervención humana | No compatible |

## 4. Reglas de selección

1. El agente deberá obtener la versión completa de RouterOS antes de preparar o ejecutar el script.
2. El sistema deberá clasificar la versión detectada como v6, v7 o no compatible.
3. Para RouterOS v6 se utilizará exclusivamente la variante ECMP autorizada para v6.
4. Para RouterOS v7 se utilizará exclusivamente la variante ECMP autorizada para v7.
5. No se permitirá reutilizar una variante entre familias sin una validación técnica explícita.
6. Si la versión no puede identificarse o no aparece como compatible, la operación deberá detenerse antes de modificar el router.
7. La versión detectada, la variante seleccionada y el resultado de la validación deberán quedar registrados en la auditoría.

## 5. Criterios de certificación

Una versión menor o de parche podrá marcarse como certificada cuando se haya comprobado, en un entorno controlado, que:

- El agente puede identificar correctamente la versión de RouterOS.
- El script ECMP correspondiente se genera con la sintaxis adecuada para esa familia.
- Las validaciones previas impiden ejecutar una variante incompatible.
- La configuración puede aplicarse sin errores atribuibles a la versión.
- Las verificaciones posteriores de rutas, tráfico, conectividad y reglas de Mangle son satisfactorias.
- Los errores y resultados quedan registrados correctamente.

## 6. Registro de pruebas

La matriz se ampliará conforme se certifiquen versiones concretas:

| Versión exacta | Familia | Estado | Fecha de prueba | Evidencia | Observaciones |
|---|---|---|---|---|---|
| Por definir | v6 | Pendiente | — | — | Se completará durante las pruebas técnicas |
| Por definir | v7 | Pendiente | — | — | Se completará durante las pruebas técnicas |

Los estados permitidos serán: `Pendiente`, `En pruebas`, `Certificada`, `Certificada con restricciones` y `No compatible`.

## 7. Estado de implementación al 30-09-2026

**Versiones certificadas: ninguna.** `CERTIFIED` está vacío y `NativeRouter.apply` bloquea escrituras reales. No existe una variable de entorno que convierta una simulación en certificación.

`6.49.18` es únicamente el identificador fijo del simulador para ensayar la variante `legacy-v6-simulation-only`; no se probó ese firmware en hardware ni CHR. Las versiones v7 y cualquier versión desconocida se rechazan antes de solicitar un artefacto ejecutable. La sintaxis heredada `broadcast`, `routing-mark`, rutas ponderadas, DNS y DHCP requiere validación/adaptación en PHP por versión exacta.

La prueba optativa `tests/lab/test_readonly.py` solo verifica lectura TLS/identidad/versión, no ECMP. No se ejecutó por falta de laboratorio. [Resultados y pendientes](14-entrega-mvp.md).

