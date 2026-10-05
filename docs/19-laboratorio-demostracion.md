# Laboratorio de pruebas para presentar el primer avance

## Dos pruebas que puedes demostrar

**A. Flujo completo local:** no requiere máquinas virtuales. Ejecuta la demo del
[documento 18](18-primer-avance.md). Demuestra la integración y autorización con
IA y RouterOS simulados.

**B. Conexión a RouterOS real:** requiere un CHR de laboratorio en VirtualBox.
El agente consulta por API TLS y guarda identidad, versión, interfaces y
comprobaciones. No aplica ECMP. Puedes preparar esta prueba con una sola VM y
una red de administración, dejando las WAN para la siguiente etapa.

La siguiente topología permite ampliar B a pruebas de tráfico cuando se termine
y valide la variante ECMP v7. No importes el script v6 de la demo en el CHR v7.

## Equipo y recursos

- PC Windows con virtualización habilitada, VirtualBox y WinBox.
- Proyecto con el entorno Python instalado como indica el documento 18.
- Imagen CHR obtenida de [MikroTik](https://mikrotik.com/download).
- Para lectura: una VM CHR. Asignación inicial propuesta: 1 CPU y 512 MB de RAM.
- Para tráfico futuro: dos CHR auxiliares con 1 CPU/512 MB cada uno y un cliente
  Linux con 1 CPU/2 GB (ajustar según el sistema elegido). Es una asignación de
  laboratorio propuesta, no una medición de requisitos mínimos.
- Espacio para discos y snapshots; conservar acceso a la consola de cada VM.

Registra la versión exacta de VirtualBox, RouterOS, WinBox y Windows utilizada.
Usa una VM dedicada y no un router que esté prestando servicio.

## Topología objetivo

```text
                         Internet del anfitrión
                          /                  \
                  NAT VirtualBox       NAT VirtualBox
                       |                      |
                  CHR-ISP1               CHR-ISP2
                  192.168.1.1            192.168.2.1
                       | LAB-WAN1              | LAB-WAN2
                       +-------- CHR-LAB ------+
                               ether1 ether2
                                    |
                       ether3       |       ether4
                      LAB-LAN       |       LAB-MGMT
                         |                    |
                    VM cliente         Windows + agente
                                       10.255.255.2
```

| VM | Adaptador de VirtualBox | Red | Dirección propuesta |
|---|---|---|---|
| CHR-LAB | 1, red interna | LAB-WAN1 | 192.168.1.2/24, etapa posterior |
| CHR-LAB | 2, red interna | LAB-WAN2 | 192.168.2.2/24, etapa posterior |
| CHR-LAB | 3, red interna | LAB-LAN | 172.16.0.1/24, etapa posterior |
| CHR-LAB | 4, solo anfitrión | LAB-MGMT | 10.255.255.1/24 |
| CHR-ISP1 | 1 NAT / 2 red interna | NAT / LAB-WAN1 | DHCP / 192.168.1.1/24 |
| CHR-ISP2 | 1 NAT / 2 red interna | NAT / LAB-WAN2 | DHCP / 192.168.2.1/24 |
| Cliente | 1, red interna | LAB-LAN | DHCP en la etapa de tráfico |
| Windows | Adaptador solo anfitrión | LAB-MGMT | 10.255.255.2/24, sin gateway/DNS |

Verifica las MAC: el número de adaptador no garantiza el nombre `etherN`.
Si estas subredes se superponen con tu VPN/red física, define otras antes del
ensayo y ajusta la documentación. Las direcciones propuestas no se deben añadir
a la tarjeta de Internet de Windows.

## Paso 1. Crear el CHR de lectura

1. En VirtualBox crea una VM Linux de 64 bits con el disco CHR compatible con
   VirtualBox descargado y descomprimido. Si ya tienes una VM, toma un snapshot
   antes de cambiar su red; no es necesario reinstalarla.
2. Apágala completamente. En Herramientas → Red crea una red de solo anfitrión.
   Configura la dirección del anfitrión `10.255.255.2/24` y desactiva su DHCP.
3. Asigna adaptadores 1–3 a las redes internas `LAB-WAN1`, `LAB-WAN2`, `LAB-LAN`;
   el 4 a la red de solo anfitrión. Marca «Cable conectado». Para lectura las
   redes internas pueden estar vacías. No uses modo puente.
4. Inicia CHR, establece su contraseña administrativa desde la consola si es una
   instalación nueva y anota su versión exacta. En Interfaces identifica por MAC
   el puerto conectado a administración.
5. Configura la identidad `lab-router` y la IP `10.255.255.1/24` en ese puerto
   mediante WinBox o consola. Conserva la configuración/acceso previo hasta
   comprobar el nuevo. Si hay un bridge, revisa su membresía antes de modificarlo.
6. Comprueba acceso desde WinBox en Windows. Guarda snapshot `01-mgmt`.

Si conservas una VM de tres interfaces, también puedes hacer la lectura por su
interfaz administrativa existente. Usa su nombre/IP reales en todos los pasos.
La cuarta interfaz es necesaria para la topología posterior de dos WAN + LAN +
administración independiente.

## Paso 2. Preparar API TLS y usuario de lectura

En el CHR-LAB, con WinBox y consola disponibles:

1. Revisa fecha/hora. En System → Certificates crea una CA `ecmp-lab-ca`, con
   Common Name del mismo nombre y Key Usage `key-cert-sign,crl-sign`. Fírmala
   como CA y márcala como confiable.
2. Crea certificado `ecmp-lab-api`, Common Name del mismo nombre, SAN
   `IP:10.255.255.1` y Key Usage `digital-signature,key-encipherment,tls-server`.
   Fírmalo con la CA anterior; comprueba vigencia y existencia de clave privada.
3. Exporta solo el certificado público de la CA en PEM, sin clave privada.
   Descárgalo desde Files a `lab-local/router-ca.crt` dentro del proyecto.
4. En IP → Services habilita `api-ssl`, puerto `8729`, certificado `ecmp-lab-api`
   y Available From `10.255.255.2/32`. Mantén deshabilitada API sin TLS (8728).
5. En System → Users → Groups crea `ecmp-reader` con políticas `read,api`. Crea
   un usuario de ese grupo y escribe una contraseña única localmente.
6. Si el firewall bloquea el acceso, permite TCP destino 8729 en input únicamente
   desde `10.255.255.2` y el puerto administrativo, antes del bloqueo pertinente.
   Conserva las otras protecciones. Guarda snapshot `02-api-tls`.

Estos pasos se apoyan en las páginas oficiales de
[certificados RouterOS](https://help.mikrotik.com/docs/spaces/ROS/pages/2555969/Certificates)
y [servicios RouterOS](https://help.mikrotik.com/docs/spaces/ROS/pages/103841820/Services).

## Paso 3. Ejecutar y registrar la lectura real

Desde PowerShell en la raíz del proyecto, crea el directorio antes de copiar el
certificado:

```powershell
New-Item -ItemType Directory -Force lab-local
Test-NetConnection 10.255.255.1 -Port 8729
$versionCHR = Read-Host 'Version exacta mostrada por RouterOS (incluya sufijo si existe)'
.\.venv-mvp\Scripts\python.exe -m agent.app.main --diagnose --host 10.255.255.1 --ca .\lab-local\router-ca.crt --identity lab-router --routeros-version "$versionCHR" --management ether4 --report .\lab-local\lectura-01.json
```

Sustituye `ether4` si la MAC corresponde a otro nombre. El agente solicita usuario
y contraseña; no escribas contraseñas en argumentos ni en el informe. No requiere
PHP, el servidor, token de técnico ni Internet. Antes del comando, el certificado
público debe estar en la ruta indicada.

Aceptación: `Diagnostico: passed`, salida 0 y cuatro comprobaciones verdaderas:
identidad, versión, interfaz administrativa y dirección en esa interfaz. Debe
seguir indicando `read_only: true`, `ecmp_certified: false` y
`real_writes_enabled: false`. Un puerto TCP abierto por sí solo no acredita TLS
ni autenticación.

Para repetir utiliza `lectura-02.json`; el agente no sobrescribe informes. Si
la prueba falla, registra el fallo y corrige red, certificado o parámetros según
el error. No sustituyas el resultado real por un JSON del simulador.

## Paso 4. Preparar las dos WAN para el siguiente avance

Esta sección construye infraestructura; no habilita la ejecución ECMP del sistema.
Puede omitirse en la primera exposición si solo se presentará la lectura real.

1. Crea dos CHR auxiliares nuevos, `CHR-ISP1` y `CHR-ISP2`. Si clonas, genera MAC
   nuevas. Cada VM tiene adaptador 1 NAT y adaptador 2 red interna: LAB-WAN1 o
   LAB-WAN2 respectivamente. Adminístralas desde su consola.
2. En cada auxiliar, identifica interfaces por MAC. En IP → DHCP Client añade un
   cliente en la interfaz NAT con Add Default Route habilitado. Debe quedar bound.
3. En IP → Addresses asigna `192.168.1.1/24` al puerto interno de ISP1 y
   `192.168.2.1/24` al de ISP2. No crees un bridge entre NAT y la red interna.
4. En IP → Firewall → NAT añade una regla `srcnat`, con red origen
   `192.168.1.0/24` (ISP1) o `192.168.2.0/24` (ISP2), salida por la interfaz NAT
   y acción `masquerade`. Si existe un filtro forward restrictivo, permite la
   salida interna→NAT y las respuestas established/related correspondientes.
5. Comprueba desde cada auxiliar la dirección recibida y su ruta predeterminada;
   prueba acceso a un destino externo conocido desde Tools → Ping. Si Internet
   del anfitrión está restringido, documenta esa limitación.
6. Crea la VM cliente con una sola tarjeta en LAB-LAN. En la etapa actual puede
   quedar apagada: CHR-LAB todavía no ofrece la configuración ECMP/DHCP.
7. Conserva snapshots de los auxiliares y un diagrama con sus MAC y direcciones.

Los modos NAT, red interna y solo anfitrión se describen en la
[documentación de redes de VirtualBox](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/networkingdetails.html).
Dos salidas NAT sobre una misma conexión física sirven para ensayar la topología;
no acreditan redundancia entre proveedores. La red de administración debe seguir
disponible al desconectar las dos WAN.

## Matriz de demostración y aceptación

| Caso | Evidencia esperada | Estado en este avance |
|---|---|---|
| Solicitud/aprobación completa | JSON final + script + auditoría | Validado en simulación |
| Rechazo del técnico | Sin evento `approval_consumed` | Validado en simulación |
| Aprobación alterada o repetida | HTTP 409 | Validado en simulación |
| Diagnóstico TLS del CHR | JSON real con 4 comprobaciones verdaderas | Ejecutar al construir el lab |
| Certificado o identidad incorrectos | Diagnóstico fallido, sin escritura | Ensayar en el lab y guardar informe aparte |
| WAN1/WAN2 y conectividad cliente | Tráfico, rutas y capturas del cliente | Pendiente de implementación/validación v7 |
| Pérdida/recuperación de WAN | Sesiones nuevas, rutas, tiempos y acceso MGMT | Pendiente; no probado por esta entrega |

Para aceptar ECMP real después: fijar versión exacta, adaptar generación y
tablas v7, ensayar aplicación sobre snapshot limpio, revisar rutas/NAT/DHCP,
probar tráfico desde el cliente y pérdida de cada WAN, y comprobar preservación
de administración. No cambiar la lista de versiones permitidas para saltarse
esa validación. La restauración actual es manual mediante snapshot.

