# Integracion experimental supervisada ECMP v7

Fecha: 19 de octubre de 2026.

## Alcance

PHP, servidor, aprobacion, agente y verificacion estan integrados para un ensayo
exclusivo sobre CHR-LAB `7.24.5 (stable)` y la topologia preparada del documento 23.
El ensayo manual fue reportado por el tecnico. La aplicacion automatica en el CHR
real aun no se ha realizado. Los locks no requieren dependencias nuevas.

`CERTIFIED` sigue vacio. Las escrituras reales estan bloqueadas por defecto. El
servidor requiere `ECMP_V7_LAB_ENABLED=1` con modo real y el agente `--lab-v7`.
El agente limita el destino a `10.255.255.1`. Otras versiones, velocidades
desiguales, topologias diferentes y estados previos incompatibles se rechazan.
Activar las opciones solo permite un ensayo; no certifica una version.

## Preparar la base

1. Conservar `09-ecmp-dhcp-validado` y `09-cliente-dhcp`, confirmadas por el
   tecnico. Guardan el ensayo manual funcional.
2. Apagar CHR-LAB ordenadamente con `/system shutdown` en su consola y confirmar
   cuando lo solicite. En VirtualBox restaurar `07-lan-conectada` de CHR-LAB,
   conservando las instantaneas posteriores. No restaurar los ISP.
3. Iniciar CHR-LAB; comprobar WinBox, fecha/hora, version y cuatro direcciones.
   Deben existir solo sus cuatro rutas DAc, sin NAT, rutas estaticas, pools ni DHCP.
   No eliminar las rutas conectadas.
4. Detener el cliente DHCP heredado que la instantanea puede recuperar:

```routeros
/ip dhcp-client disable [find where name="client1"]
/ip dhcp-client print detail
/ip route print detail
```

5. Mantener ISP1 e ISP2 encendidos. Lubuntu puede conservar el perfil DHCP de 09:
   esperara concesion hasta aplicar. Mantenerlo solo en LAB-LAN, sin otro NAT/puente.
6. Conservar ecmp-reader de lectura y crear un grupo separado de ensayo:

```routeros
/user group add name=ecmp-lab-writer policy=read,write,api
```

En WinBox System / Users crear usuario `ecmp-lab-writer`, grupo del mismo nombre,
Allowed Address `10.255.255.2/32` y contrasena local propia. No guardar esa
contrasena en el proyecto ni compartirla. Si ya existe, revisar y no duplicar.
No ampliar ecmp-reader.

7. Guardar `10-base-agente-v7`: cuatro direcciones, DHCP cliente detenido,
   usuario de ensayo y sin reglas/rutas/DHCP del procedimiento.

El prechequeo inspecciona NAT/mangle/filtro, pools, servidores y redes DHCP,
bridges, reglas/tablas de enrutamiento y clientes DHCP. Exige esas tablas vacias,
salvo main FIB y clientes DHCP deshabilitados. No elimina configuracion por si solo.

## Arranque coordinado

En PowerShell, desde la raiz:

```powershell
.\iniciar-lab-v7.cmd
```

El comando verifica `lab-local/router-ca.crt`, inicia PHP/FastAPI en loopback y
abre el agente en la misma consola. Activa el ensayo explicito, genera tres claves
temporales diferentes y una base SQLite por ejecucion. No altera `.env`, no usa
OpenAI ni aprueba solicitudes automaticamente. El prechequeo del router se realiza
al enviar una solicitud, no antes de mostrar la URL.

La terminal muestra URL, clave del tecnico y token del agente. Copiar el token
en el prompt del agente; introducir despues usuario ecmp-lab-writer y contrasena.
El agente muestra su sesion tras autenticar TLS. No compartir capturas de claves.
No se pasan tokens por argumentos ni se guardan credenciales RouterOS en archivos.

Logs PHP/servidor y base quedan en `runtime/lab-v7-.../`; la salida del agente
queda en consola. No publicar la base. Ctrl+C termina los procesos de este
arranque, sin revertir RouterOS. Para puerto ocupado usar `--port 8002` o `--port 0`.
La CA admite `--ca RUTA`, siempre valida para la IP fija. El binario portatil
anterior no se reconstruyo: usar este arranque con Python de `.venv-mvp`.

## Solicitud y aprobacion

Abrir la URL e introducir la clave del tecnico. Completar:

| Parametro | Valor |
|---|---|
| Lineas | 2 |
| Velocidades | 5M / 5M, iguales; no son medicion ni shaping |
| Gateways | 192.168.1.1 / 192.168.2.1 |
| Octetos IP WAN | 2 / 2 |
| LAN / DHCP | 172.16.0.1 / activado |
| Sesion | La que muestra el agente |
| Referencia / identidad | router-1 / lab-router |
| Administracion | ether4; sustituir ether14 si aparece |

El servidor selecciona familia desde la version observada; la IA no la elige.
PHP recibe `v7-lab` y genera un artefacto ejecutable de laboratorio distinto de
la vista previa. Un artefacto `preview_only=true` no puede entrar al ejecutor.

Antes de aprobar revisar siete operaciones: dos NAT para origen LAN, dos rutas
en main con distancia 1, pool, red y servidor DHCP habilitado al final. No hay
renombres, altas de direcciones, cambios de certificados/usuarios/servicios,
mangle ni comandos libres. Probar rechazo antes de cualquier aplicacion si se
desea conservar la base intacta para la solicitud aprobada.

La aprobacion vincula artefacto, operaciones, parametros, destino, variante,
plan y snapshot. Servidor/agente revalidan el estado antes del permiso de uso
unico y de escribir. Un permiso desactivado o cambio de estado bloquea el ensayo.
No hay reintento de escritura ni rollback automatico ante aplicacion parcial.

## Resultado y evidencia

El agente ejecuta por API TLS y vuelve a consultar. La verificacion v7 normaliza
booleanos y duracion DHCP, comprueba conteos, rutas activas y preservacion de
interfaces/direcciones. Si la API no entrega la marca ECMP, esa comprobacion
queda expresamente no realizada.

El resultado esperado es `configuration_with_warnings`. Las tablas no prueban
trafico del cliente, DNS, concesiones ni failover. Repetir en esta nueva ejecucion
direccion/ruta/DNS de Lubuntu, pings, destinos multiples, uso de ambos NAT y
pausa/recuperacion individual de ISP para conexiones nuevas. Conservar acceso
administrativo y guardar informe JSON y salidas cliente/router sin secretos.
No reutilizar los resultados manuales como evidencia del ensayo automatico.

Ante intervencion requerida conservar evidencia, no repetir las altas. La
reconciliacion solo consulta. Para un nuevo ensayo restaurar/revisar la base y
crear nueva solicitud/aprobacion; no editar SQLite ni CERTIFIED para omitir controles.

## Limites

No se certifican produccion, portabilidad v7, otras topologias/versiones,
ponderacion, PCC, conexiones entrantes por WAN ni deteccion de Internet aguas
arriba. Ambos ISP usan la misma conexion fisica. El laboratorio no tiene firewall
productivo ni gestion multiusuario. Medir convergencia y sesiones existentes
requiere pruebas adicionales; los contadores NAT no miden todo el trafico.

## Verificacion de esta integracion

Suite completa: **156 aprobadas, 1 omitida, 1 advertencia en 43.62 s**. Incluye
28 casos nuevos del flujo v7, con PHP real y una API RouterOS exclusivamente en
memoria: aprobacion, rechazo, dos permisos, version exacta, conflictos previos,
drift, operaciones falsificadas, aplicacion parcial sin reintento, normalizacion
de snapshots/booleanos/duracion y preservacion de v6. El launcher se comprobo con
`--help`; su recorrido interactivo con el CHR real queda para el ensayo del tecnico.

Se verifico sintaxis PHP en ambas bibliotecas. La prueba real optativa sigue
omitida y la advertencia de Starlette/AnyIO es preexistente. No se hicieron
conexiones al CHR ni escrituras reales durante estas pruebas de codigo.

Para reproducir evitando las carpetas temporales/caches con permisos conflictivos:

```powershell
$pruebasV7 = Join-Path $PWD ('runtime\pytest-v7-' + [guid]::NewGuid().ToString('N'))
.\.venv-mvp\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp "$pruebasV7"
```

## Correccion del primer prechequeo real

La primera solicitud real completo la lectura TLS pero quedo en intervencion
antes de generar artefacto. El snapshot observado devolvio la tabla main como
`{"fib":"","name":"main"}`: fib es un switch, no necesariamente un booleano.
El prechequeo esperaba exclusivamente `true` y rechazo esa representacion.
La [referencia RouterOS](https://manual.mikrotik.com/docs/cli-reference/routing/table/)
identifica fib como switch.

Se admite ahora el valor presente vacio solo para la unica tabla main, ademas de
`true`. Una clave ausente, valores false/no o tablas distintas siguen rechazados.
No se normaliza el snapshot ni se cambia el hash vinculado a aprobacion.

Se conserva una proyeccion del snapshot real sin credenciales, identificadores de
sesion ni tokens en `tests/fixtures/v7-precheck-main-fib-flag.json`. La regresion
reproduce lectura -> generacion PHP -> espera de aprobacion sin escribir en un
router. Se agregaron tambien casos negativos para clave ausente/false/no y otra tabla.

La solicitud afectada solo tuvo get_ecmp_precheck completado, sin artefacto ni
tarea de escritura. Conservarla como evidencia. Detener el launcher con Ctrl+C,
iniciarlo de nuevo para cargar la correccion y crear una solicitud nueva con
las nuevas claves/sesion; no editar el registro anterior ni restaurar el router
para este error de interpretacion.

Verificacion tras corregir: **161 aprobadas, 1 omitida, 1 advertencia en 44.35 s**.
El snapshot real capturado pasa tambien el prechequeo directamente, sin conexion
de red ni modificaciones del router.
