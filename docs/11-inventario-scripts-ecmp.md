# 11. Inventario inicial de scripts ECMP

## 1. Objetivo

Identificar los scripts ECMP que genera actualmente el sistema PHP existente y definir cómo se complementará con el nuevo sistema de soporte remoto.

## 2. Fuente autorizada

El sistema PHP ubicado en `php/sistema-generador` es la fuente actual de generación de scripts de configuración MikroTik.

Para el MVP, el nuevo sistema no sustituirá ni duplicará esta lógica. Sus responsabilidades serán solicitar el script al generador PHP, validar el artefacto recibido, confirmar su compatibilidad con el router, obtener la aprobación requerida, ejecutarlo mediante la API de RouterOS y verificar el resultado.

Archivos principales identificados:

- [index.php](../php/sistema-generador/index.php): selección del tipo de configuración y cantidad de líneas.
- [parametros.php](../php/sistema-generador/parametros.php): captura de parámetros WAN, LAN y DHCP.
- [aplicar.php](../php/sistema-generador/aplicar.php): construcción y presentación del script RouterOS.
- [procesar.php](../php/sistema-generador/mikrotik-modulos/modulos/ia/procesar.php): adaptación de solicitudes estructuradas al flujo del generador existente.

## 3. Inventario encontrado

| Identificador documental | Tipo PHP | Descripción | Estado respecto al MVP |
|---|---|---|---|
| `ECMP-PHP-001` | `ECMP` | Balanceo ECMP con ponderación calculada a partir de la velocidad de cada WAN | Incluido; pendiente de certificación por versión de RouterOS |
| `ECMPR-PHP-001` | `ECMPr` | Balanceo ECMP con rutas recursivas basadas en destinos de comprobación | Existente en PHP, pero excluido del MVP |

La presencia de `ECMPr` en el sistema PHP no amplía el alcance. El único tipo que el nuevo sistema podrá solicitar y ejecutar durante el MVP será `ECMP`.

## 4. Script ECMP incluido en el MVP

### 4.1 Entradas actuales

El generador `ECMP` recibe actualmente:

| Parámetro | Origen actual | Regla observada |
|---|---|---|
| Tipo | `tipo` | Debe ser exactamente `ECMP` |
| Cantidad de WAN | `lineas` | El formulario permite de 2 a 12 líneas |
| Velocidad por WAN | `vel1` a `velN` | Valores predefinidos en K o M; se utilizan para calcular la ponderación |
| Gateway por WAN | `gw1` a `gwN` | Selección de direcciones `192.168.x.1` o `192.168.x.254` |
| Host IP por WAN | `ip1` a `ipN` | Último octeto entre 2 y 253 |
| Dirección LAN | `lan` | Selección dentro del esquema `172.16.x.1` |
| DHCP | `dhcp` | Opción para agregar pool, servidor y red DHCP |

Estas reglas describen el comportamiento actual del código y no deben interpretarse todavía como validaciones suficientes para producción.

### 4.2 Configuración generada

El script `ECMP` construye actualmente comandos para:

- Renombrar interfaces Ethernet como `WAN1` a `WANN` y `LAN`.
- Asignar direcciones IPv4 a las interfaces WAN y LAN.
- Crear reglas NAT `masquerade` por WAN.
- Crear marcas de conexión de entrada y marcas de ruteo de salida.
- Crear una ruta ECMP predeterminada ponderada según las velocidades indicadas.
- Crear rutas predeterminadas asociadas con cada marca de ruteo.
- Configurar servidores DNS y habilitar solicitudes remotas.
- Crear opcionalmente el pool y servidor DHCP para la LAN.

### 4.3 Salida actual

El resultado se construye como texto RouterOS dentro de la variable PHP `$script_ecmp` y se presenta en una sección HTML `<pre>` para copiarlo manualmente.

El código actual no entrega todavía un artefacto estructurado con identificador de generación, versión del generador, familia de RouterOS, suma de integridad o metadatos de validación.

## 5. Compatibilidad con RouterOS

El generador `ECMP` actual no solicita la versión de RouterOS y no contiene una selección explícita entre variantes v6 y v7.

Por lo tanto:

- El script actual no se considerará automáticamente compatible con ambas familias.
- Deberá probarse por separado en RouterOS v6 y v7.
- La sintaxis y el comportamiento de rutas y marcas deberán certificarse para cada familia.
- Si las pruebas demuestran diferencias, el sistema PHP deberá generar variantes separadas y declarar la familia de destino.
- El agente deberá rechazar cualquier script cuya familia de RouterOS no esté declarada y certificada.

El resultado de estas pruebas deberá registrarse en la [matriz inicial de versiones de RouterOS](08-matriz-versiones-routeros.md).

## 6. Integración con el nuevo sistema

```text
Técnico / Sistema principal
            │
            │ Parámetros ECMP validados
            ▼
Generador PHP existente
            │
            │ Script y metadatos de generación
            ▼
Nuevo sistema
            │
            ├── Valida tipo, versión, parámetros e integridad
            ├── Compara contra el estado real del MikroTik
            ├── Solicita aprobación humana
            ▼
Agente portátil
            │
            │ api-ssl
            ▼
Router MikroTik
            │
            ▼
Verificación y auditoría
```

### 6.1 Responsabilidades del sistema PHP

- Mantener la lógica autorizada de generación de ECMP.
- Validar los parámetros propios del generador.
- Producir el script correspondiente sin intervención de la IA.
- Identificar la versión del generador utilizada.
- Declarar la familia de RouterOS de destino cuando existan variantes certificadas.
- Entregar un resultado reproducible para el mismo conjunto de entradas y versión.

### 6.2 Responsabilidades del nuevo sistema

- Aceptar únicamente el tipo `ECMP` durante el MVP.
- Recopilar y validar los parámetros de la operación.
- Solicitar la generación al sistema PHP.
- No alterar silenciosamente el script generado.
- Verificar que el script corresponda con los parámetros aprobados y la familia de RouterOS detectada.
- Calcular o verificar la suma de integridad del artefacto.
- Registrar el script o su referencia inmutable, sus metadatos y la aprobación.
- Entregarlo al agente portátil solamente después de completar las validaciones.
- Ejecutarlo mediante el canal autorizado y verificar el resultado.

## 7. Contrato de salida requerido

Para evitar depender de la lectura de HTML, el sistema PHP deberá proporcionar una interfaz de integración que entregue, como mínimo:

| Campo | Descripción |
|---|---|
| `generation_id` | Identificador único de la generación |
| `procedure` | Valor fijo `ECMP` para el MVP |
| `generator_version` | Versión del código o plantilla utilizada |
| `routeros_family` | `v6` o `v7`, una vez certificada la variante |
| `parameters` | Parámetros normalizados utilizados para generar el script |
| `script` | Texto exacto autorizado para ejecutar |
| `script_hash` | Suma criptográfica del texto generado |
| `warnings` | Advertencias o restricciones aplicables |
| `generated_at` | Fecha y hora de generación |

El formato y transporte definitivos de esta interfaz quedan pendientes de diseño. Hasta que exista, la transferencia manual del script podrá utilizarse únicamente para pruebas controladas y deberá quedar registrada.

## 8. Reglas de control

- La IA no generará ni modificará comandos RouterOS para el MVP.
- No se aceptará un tipo distinto de `ECMP` aunque el sistema PHP pueda producirlo.
- El script deberá regenerarse si cambian los parámetros aprobados.
- El hash deberá calcularse nuevamente si cambia cualquier carácter del script.
- El agente ejecutará exactamente el artefacto aprobado.
- Una incompatibilidad de versión, parámetros o integridad detendrá la operación.
- Los secretos no formarán parte del script ni de sus metadatos persistentes.

## 9. Pendientes de certificación

- Asignar una versión formal al generador PHP actual.
- Crear pruebas reproducibles para `ECMP-PHP-001`.
- Determinar si el script actual corresponde a RouterOS v6, v7 o requiere dos variantes.
- Definir el formato y transporte de la interfaz entre el sistema PHP y el nuevo sistema.
- Agregar identificador, familia RouterOS, hash y advertencias a la salida.
- Validar límites y formatos de todos los parámetros recibidos.
- Definir el almacenamiento inmutable de cada artefacto generado y aprobado.

## 10. Integración implementada (30-09-2026)

El generador `ECMP-PHP-001/1.0.0` expone `POST api/ecmp.php` autenticado. `lib/ecmp-legacy.php` ahora separa `ecmp_text()` de `legacy_ecmp()` (presentación manual); `lib/ecmp-contract.php` valida los formatos originales y devuelve el contrato JSON con SHA-256. `aplicar.php` valida parámetros ECMP antes del flujo manual. No se migra el módulo OpenRouter ni se conectan propuestas libres a la ejecución.

La regresión compara ocho combinaciones de líneas/DHCP con la implementación anterior. Una prueba separada cubre la corrección documentada de comas en los gateways ponderados de la última WAN. Backend y agente verifican la normalización UTF-8/LF, parámetros, metadatos y representación restringida de operaciones. SQLite conserva el artefacto y la aprobación vinculada.

La salida declara familia candidata v6 y advertencia de **no certificación**. La API rechaza v7. La escritura real continúa bloqueada; estos avances no modifican el estado de certificación de la matriz. Ver [arquitectura implementada](13-implementacion-mvp.md).

