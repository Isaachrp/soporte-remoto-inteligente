# Revision para la adaptacion ECMP a RouterOS v7

Fecha: 15 de octubre de 2026.

## Punto de partida

El tecnico reporto las siguientes pruebas realizadas en VirtualBox. Este registro
resume lo comunicado en la sesion; no sustituye los informes ni las capturas de
las pruebas de trafico.

| Elemento | Configuracion y resultado reportados |
|---|---|
| CHR-LAB | RouterOS `7.24.5 (stable)`, identidad `lab-router` |
| Administracion | `ether4`, `10.255.255.1/24`; Windows `10.255.255.2/24` |
| API TLS | Puerto 8729, certificado `ecmp-lab-api`, CA `ecmp-lab-ca` |
| Agente | Diagnostico real aprobado, salida 0, `lab-local/lectura-02.json` |
| WAN1 | CHR-LAB `192.168.1.2/24`, gateway ISP1 `192.168.1.1` |
| WAN2 | CHR-LAB `192.168.2.2/24`, gateway ISP2 `192.168.2.1` |
| LAN | `ether3`, `172.16.0.1/24`; Lubuntu `172.16.0.10/24` en `enp0s3` |
| Cliente | Perfil NetworkManager `LAB-LAN`, direccion manual, sin ruta predeterminada |
| Pruebas | Ping externo individual desde cada WAN del CHR y ping cliente-router aprobados |
| Recuperacion | Instantaneas `07-lan-conectada` y `07-ip-estatica-lan` confirmadas |

El nombre de cada interfaz WAN debe contrastarse por MAC antes de aplicar
configuracion. Las rutas temporales de las pruebas se retiraron segun la sesion.
Internet desde el cliente, DHCP, ECMP y recuperacion de WAN siguen pendientes.
Las dos WAN comparten la salida fisica de Windows mediante NAT de VirtualBox.

## Revision del codigo actual

1. `server/app/services/generator.py` solicita siempre `routeros_family=v6`.
2. `php/sistema-generador/lib/ecmp-contract.php` rechaza v7.
3. `ecmp-legacy.php` genera `broadcast`, rutas con `routing-mark` y una lista de
   gateways con repeticiones calculadas a partir de las velocidades. No se puede
   declarar compatible con v7 mediante un cambio de etiqueta.
4. `shared/ecmp.py` valida exclusivamente artefactos v6 y su allowlist no incluye
   tablas de enrutamiento v7. La verificacion tambien necesita evolucionar para
   interpretar correctamente los campos que devuelve la API real.
5. El prechequeo rechaza direcciones fuera del puerto administrativo y cualquier
   fila de rutas. El laboratorio ya contiene direcciones de trabajo y RouterOS
   genera rutas conectadas al asignarlas; ese estado debe tratarse explicitamente.
6. `shared/contracts.py` solo admite la variante v6 simulada. Las escrituras
   reales siguen bloqueadas. La lectura TLS aprobada no certifica ECMP.

## Secuencia de adaptacion

1. Recoger el inventario actual de direcciones, rutas, NAT, mangle y DHCP de
   CHR-LAB. Conservar el acceso administrativo y las instantaneas.
2. Definir una variante PHP v7 separada y versionada. Conservar la regresion de
   la salida v6. Preparar primero un artefacto para revision, sin habilitarlo en
   el agente real.
3. Para la primera prueba, proponer ECMP de igual costo con dos WAN. La
   ponderacion heredada por velocidades requiere especificacion y validacion
   propias; no presentar un ECMP igualitario como ponderado.
4. Usar rutas de igual costo en `main`. Si se conserva el marcado de respuestas
   del procedimiento heredado, crear antes las tablas FIB necesarias y utilizar
   `routing-table` en las rutas v7. Revisar expresamente la administracion local.
5. Elegir un contrato de aplicacion: laboratorio limpio preparado o reutilizacion
   controlada de las direcciones existentes. No borrar configuracion ni relajar
   el prechequeo para aceptar cualquier estado previo.
6. Actualizar adaptador, snapshots, prechequeo, seleccion de familia y verificacion
   con pruebas de compatibilidad, integridad y aprobacion. Distinguir rutas
   conectadas esperadas de rutas estaticas o dinamicas ajenas.
7. Revisar el script y las operaciones concretas antes del ensayo de escritura.
   Mantener la version sin certificar hasta completar las pruebas reales.

## Aceptacion pendiente

- Direcciones y acceso administrativo preservados.
- Rutas ECMP, NAT y DHCP correctos en RouterOS 7.24.5.
- Cliente cambiado de IP manual a DHCP durante su prueba correspondiente.
- Acceso externo y DNS desde el cliente.
- Evidencia de trafico por ambos enlaces con multiples flujos; un ping unico
  no demuestra distribucion ni suma de velocidades.
- Caida y recuperacion individual de WAN, distinguiendo la caida del gateway
  de una interrupcion aguas arriba. `check-gateway=ping` al ISP solo comprueba
  ese siguiente salto.
- Auditoria y comportamiento ante aplicacion parcial; recuperacion por snapshot
  documentada, sin afirmar rollback automatico.

## Fuentes tecnicas

- [Decision de enrutamiento y ECMP](https://manual.mikrotik.com/docs/user-guides/routing-and-networking-protocols/routing-decision/).
- [Cambios de RouterOS v6 a v7](https://help.mikrotik.com/docs/spaces/ROS/pages/30474256/Moving%2Bfrom%2BROSv6%2Bto%2Bv7%2Bwith%2Bexamples).

Este documento es una revision y propuesta de trabajo. No implementa la variante
v7 ni habilita escrituras en el agente.

## Actualizacion del 19 de octubre de 2026

El inventario enviado por el tecnico confirma las cuatro direcciones anteriores,
cuatro rutas DAc en `main`, sin rutas estaticas, y tablas NAT, mangle y servidores
DHCP vacias. Se elige conservar las direcciones y los nombres `ether1` a `ether4`.

Se agrega un generador PHP de vista previa, separado del endpoint ejecutable.
Su uso, condiciones pendientes y limites estan en
[Vista previa v7 para el laboratorio](22-vista-previa-ecmp-v7.md).
El workflow, adaptador y prechequeo se integraron despues como
[ensayo experimental supervisado](24-integracion-supervisada-v7.md).
Su aplicacion automatica en el CHR real sigue pendiente de validacion.
