# Resultados del ensayo manual ECMP v7

Fecha de registro: 19 de octubre de 2026.

## Origen y alcance de la evidencia

Resultados comunicados por el tecnico en la sesion, con salidas de consola y
capturas para parte de las comprobaciones. No son un informe generado por el
workflow del agente. Las configuraciones se aplicaron manualmente desde WinBox.
El agente solo tiene comprobada la lectura real TLS en esta etapa.

## Entorno

- CHR-LAB: RouterOS `7.24.5 (stable)`, identidad `lab-router`.
- Administracion: ether4 `10.255.255.1/24`; Windows `10.255.255.2/24`.
- WAN1: ether1 `192.168.1.2/24`, gateway CHR-ISP1 `192.168.1.1`.
- WAN2: ether2 `192.168.2.2/24`, gateway CHR-ISP2 `192.168.2.1`.
- LAN: ether3 `172.16.0.1/24`, red interna LAB-LAN.
- Cliente Lubuntu: enp0s3, MAC `08:00:27:F5:44:A9`, perfil LAB-LAN.
- ISP1 e ISP2 salen por NAT de VirtualBox sobre la misma conexion fisica.

## Cambios manuales aplicados

Se conservaron las cuatro direcciones y las interfaces. Se deshabilito el
cliente DHCP heredado `client1` de ether1: la salida mostro marca X y estado
stopped. Se agregaron dos reglas masquerade para origen `172.16.0.0/24`, con
comentarios ECMP7-LAB-NAT1 y ECMP7-LAB-NAT2.

Se agregaron dos rutas `0.0.0.0/0` en main, distancia 1 y check-gateway=ping,
una por cada ISP. Ambas mostraron As+ y su siguiente salto por ether1/ether2.

Se creo el pool ecmp7_lab_pool `172.16.0.50-172.16.0.250`, la red DHCP
`172.16.0.0/24` con gateway `172.16.0.1` y DNS `1.1.1.1,8.8.8.8`, y el servidor
ecmp7_lab_dhcp en ether3, lease-time 8h. Se preparo deshabilitado y luego se
habilito. El cliente se cambio de direccion manual a metodo IPv4 automatico,
eliminando del perfil los valores manuales de direccion, gateway y DNS.

## Resultados observados o reportados

| Prueba | Resultado | Evidencia recibida |
|---|---|---|
| Rutas ECMP | Dos rutas activas As+, gateways distintos | Salida RouterOS |
| Cliente con IP manual | Gateway correcto, ping externo 4/4 y DNS correcto | Captura Lubuntu |
| Varios destinos | Los seis destinos respondieron | Confirmacion del tecnico |
| Uso de WAN1/WAN2 | NAT1: 5100 bytes, 27 paquetes; NAT2: 8505 bytes, 53 paquetes | Salida de contadores NAT |
| Pausa ISP1 | WAN1 inactiva, pings nuevos exitosos, ruta recuperada al reanudar | Confirmacion del tecnico |
| Pausa ISP2 | Ensayo equivalente exitoso | Confirmacion del tecnico |
| Asignacion DHCP | Cliente recibio 172.16.0.250, concesion dinamica bound y MAC coincidente | Salida de concesiones |
| Conectividad tras DHCP | Ping al gateway y externo exitosos; consulta DNS devuelve direcciones | Confirmacion del tecnico |

## Limites y trabajo restante

Estos resultados respaldan la configuracion manual del laboratorio, no la
certificacion del sistema automatico. El generador preliminar permanece offline;
la seleccion v7 del servidor, adaptador, prechequeo, verificacion y escritura
autorizada deben probarse sobre el CHR real desde una instantanea base. La
integracion de codigo esta descrita en el documento 24.
No modificar CERTIFIED para omitir esas pruebas.

Los contadores NAT indican coincidencias al inicio de conexiones, no todo el
trafico ni un reparto exacto o una suma de velocidades. Los ensayos de pausa
validan perdida del gateway virtual, no perdida de Internet aguas arriba. No se
midieron tiempos de convergencia, rendimiento ni continuidad de sesiones previas.
Las pruebas de caida precedieron al cambio del cliente a DHCP; no se ha registrado
su repeticion posterior ni una renovacion tras reiniciar el cliente.

Las instantaneas 07-lan-conectada y 07-ip-estatica-lan fueron confirmadas por el
tecnico. Se solicito ademas 08-ecmp-salida-lan antes de las pruebas de caida.
El tecnico confirmo ademas las instantaneas 09-ecmp-dhcp-validado en CHR-LAB y
09-cliente-dhcp en CLIENTE-LAN. Conservar las instantaneas base para ensayar la
aplicacion automatica sin duplicar configuracion.
