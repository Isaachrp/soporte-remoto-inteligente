# Vista previa ECMP v7 para el laboratorio

Fecha: 19 de octubre de 2026.

## Estado

Generador preliminar offline para CHR-LAB `7.24.5 (stable)`. PHP genera el script;
Python lo guarda junto con sus metadatos y SHA-256. No conecta al router, no
inspecciona su estado y no aplica configuracion. La sintaxis generada aun necesita
validacion en ese firmware; una prueba de PHP no la certifica.

El flujo v6 simulado se conserva. Existe ahora un
[ensayo experimental integrado](24-integracion-supervisada-v7.md), con otro
contrato de artefacto y permisos explicitos. Esta herramienta de vista previa
continua siendo offline: no habilita ni aplica esa ejecucion.

## Generacion

En PowerShell, desde la raiz del proyecto:

```powershell
.\.venv-mvp\Scripts\python.exe scripts/preview_v7.py
```

Cada ejecucion crea una carpeta nueva en `lab-local/preview-v7-FECHA-HORA/` con:

- `ecmp-v7-lab.rsc`: borrador para revisar.
- `artefacto.json`: parametros, condiciones previas, limites y hash del script.
- `SHA256SUMS`: huella del archivo RSC, guardado en UTF-8 con saltos LF.

Se admite `--php RUTA` para seleccionar PHP y `--output CARPETA_NUEVA` para guardar
la revision en otro destino. Un destino existente se rechaza para no sobrescribir
evidencias. Los archivos de `lab-local` permanecen fuera de Git.

## Contrato de esta variante

Se reutilizan exactamente las direcciones ya configuradas:

| Interfaz | Direccion | Funcion |
|---|---|---|
| ether1 | 192.168.1.2/24 | WAN1, gateway 192.168.1.1 |
| ether2 | 192.168.2.2/24 | WAN2, gateway 192.168.2.1 |
| ether3 | 172.16.0.1/24 | LAN |
| ether4 | 10.255.255.1/24 | Administracion |

El borrador contiene siete altas, sin comandos de borrado:

1. Dos reglas masquerade de origen `172.16.0.0/24`, una por WAN.
2. Dos rutas predeterminadas en `main`, ambas con distancia 1 y comprobacion de
   gateway mediante ping. Se propone ECMP de igual costo, sin mangle ni PCC.
3. Un pool `172.16.0.50-172.16.0.250`, una red DHCP con gateway `172.16.0.1` y DNS
   externos `1.1.1.1,8.8.8.8`, y un servidor DHCP en ether3 inicialmente deshabilitado.

Se conservan certificados, servicios, usuarios, direcciones y nombres de puertos.
No se modifica DNS del router ni se habilita un resolver. Se omite el marcado de
respuestas entrantes del generador v6: esta prueba cubre trafico saliente LAN, no
servicios publicados ni conexiones entrantes por WAN. No es una configuracion de
produccion ni incorpora una politica nueva de firewall.

Los valores `vel1=vel2=5M` son entradas iguales de prueba, no velocidades medidas
ni limites de ancho de banda. El borrador no usa esos valores para ponderar rutas.
PHP rechaza entradas de distinto peso o topologias diferentes. La funcion admite
omitir DHCP, pero el comando de ejemplo lo prepara deshabilitado.

## Antes de cualquier ensayo de aplicacion

El tecnico ya entrego inventario de direcciones, rutas, NAT, mangle y servidores
DHCP. Antes de aplicar, completar la revision de:

```routeros
/ip firewall filter print detail
/ip pool print detail
/ip dhcp-server network print detail
/interface bridge port print detail
/routing rule print detail
/ip dhcp-client print detail
```

Revisar reglas que puedan impedir el trafico, nombres/pools existentes, reglas
de enrutamiento, membresias de bridge y clientes DHCP. No eliminar configuracion
desconocida para acomodar el borrador. La condicion de aplicacion es un laboratorio
preparado, con solo las rutas conectadas esperadas y sin recursos que colisionen.

Conservar las instantaneas `07-lan-conectada` y `07-ip-estatica-lan` y acceso por
WinBox/consola. No importar aun el RSC completo. Las instrucciones `add` no son
idempotentes; repetirlas crearia duplicados. El ensayo posterior sera por etapas:
NAT, rutas, trafico LAN y finalmente habilitacion/prueba de DHCP. El cliente tiene
`ipv4.never-default=yes`; necesita una etapa explicita de cambio de perfil para
usar gateway o DHCP, no basta con instalar rutas en el CHR.

`check-gateway` prueba al ISP virtual, no su salida aguas arriba. Ambos ISP usan
la conexion fisica de Windows. La distribucion requiere multiples destinos o
flujos segun la politica hash: un solo ping no demuestra balanceo. Se documentaran
sesiones nuevas y existentes al probar perdida y recuperacion de enlaces.

## Referencias

- [Rutas conectadas y ECMP](https://manual.mikrotik.com/docs/user-guides/routing-and-networking-protocols/routing-decision/).
- [NAT y masquerade](https://help.mikrotik.com/docs/spaces/ROS/pages/3211299/NAT).
- [DHCP RouterOS](https://help.mikrotik.com/docs/spaces/ROS/pages/24805500/DHCP).

## Verificacion local del 19 de octubre de 2026

Suite completa: **128 aprobadas, 1 omitida, 1 advertencia**, en 33.86 segundos.
Se probaron integridad del borrador, rechazo de otras topologias y velocidades
desiguales, DHCP opcional, preservacion de revisiones y bloqueo del artefacto en
el adaptador ejecutable existente. La regresion v6 y los recorridos E2E previos
siguen pasando. PHP no detecto errores de sintaxis en la biblioteca nueva.

El primer intento de suite fallo al iniciar la comunicacion local con PHP dentro
del aislamiento. La repeticion con permiso fuera del aislamiento paso completa.
La advertencia restante es la deprecacion preexistente de Starlette/AnyIO. La
prueba omitida corresponde al laboratorio real optativo de la suite, no a las
lecturas que el tecnico ejecuto manualmente.

Se genero una vista previa real mediante PHP y se comprobo su hash en las pruebas.
No se ejecuto el RSC en RouterOS ni se certifico ECMP en esta etapa.
