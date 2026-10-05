# Primera prueba con tu CHR v7

## Estado y datos que faltan

Dispones de CHR v7 con tres interfaces. Ya se puede probar la conexión API TLS
mediante `--diagnose`, sin iniciar PHP, FastAPI, IA ni registrar una sesión.
La prueba consulta identidad, versión, interfaces y tablas; no aplica ECMP.
La adaptación ECMP v7 y su validación real siguen pendientes: el generador actual
es v6 y ninguna versión real está certificada. No importes ese script en v7.

Hipervisor confirmado: **VirtualBox**. Antes de continuar necesitamos: versión exacta de RouterOS (con sufijo,
si lo muestra), IP e interfaz actuales de administración, confirmación de que es
un CHR de laboratorio y posibilidad de añadir una cuarta interfaz. No compartas
contraseñas, claves API, claves privadas ni archivos de respaldo.

## Construcción del laboratorio

1. Conserva acceso a la consola de la VM y toma un snapshot desde el hipervisor.
2. Para la primera lectura utiliza tu interfaz e IP actuales. No necesitas borrar
   configuración, contratar dos enlaces ni añadir interfaces para esta etapa.
3. Para la etapa posterior de ECMP, apaga la VM y añade una cuarta tarjeta virtual.
   Comprueba en RouterOS qué MAC corresponde a cada red: el orden del hipervisor
   no debe asumirse como el orden de `etherN`.
4. Crea redes virtuales separadas según la tabla. Son direcciones propuestas;
   comprueba que no se superpongan con tu LAN, VPN o redes existentes.

| Puerto propuesto | Red virtual aislada | Dirección propuesta del CHR | Otro extremo |
|---|---|---|---|
| ether1 | LAB-WAN1 | 192.168.1.2/24, etapa ECMP | Router de salida 192.168.1.1 |
| ether2 | LAB-WAN2 | 192.168.2.2/24, etapa ECMP | Router de salida 192.168.2.1 |
| ether3 | LAB-LAN | 172.16.0.1/24, etapa ECMP | VM cliente, solamente en esta LAN |
| ether4 | LAB-MGMT con acceso del host | 10.255.255.1/24 | Windows/agente 10.255.255.2/24 |

No pongas gateway predeterminado ni DNS en la tarjeta LAB-MGMT de Windows.
Para WAN virtuales puedes usar dos routers virtuales auxiliares: cada uno con
una interfaz hacia su LAB-WAN y otra hacia NAT del hipervisor, con enrutamiento y
NAT configurados. Dos interfaces conectadas a la misma red NAT no representan
dos WAN independientes. Una sola salida física compartida permite ensayar la
topología, pero no demuestra redundancia entre proveedores.

Mantén LAB-LAN sin conexión puente a tu red doméstica/empresa para que su futuro
DHCP no afecte otros equipos. La red de administración debe seguir accesible aunque
desconectes ambas WAN. Usa un cliente separado del Windows que ejecuta el agente.

El diseño del ejecutor exige administración dedicada: con tres interfaces puedes
probar lectura, pero no satisfacer dos WAN + LAN + administración de este MVP.
La licencia gratuita CHR permite ensayos funcionales y limita salida a 1 Mbps por
interfaz; no sirve para evaluar rendimiento de enlaces rápidos.
[Documentación de licencia CHR](https://manual.mikrotik.com/docs/getting-started/routeros-licensing/chr/chr-licensing/).

## Preparación de api-ssl en WinBox

### Pasos específicos de VirtualBox

Para preparar la topología de cuatro puertos en una VM exclusiva de pruebas:

1. Toma un snapshot y apaga el CHR (no lo dejes en estado guardado).
2. En Herramientas → Red / administrador de redes de anfitrión, crea una red
   de solo anfitrión. Configura IPv4 del host `10.255.255.2`, máscara
   `255.255.255.0` y desactiva el DHCP de VirtualBox en esa red.
3. En Configuración del CHR → Red, habilita las cuatro tarjetas y marca
   «Cable conectado». Configura:

   | Adaptador | Conectado a | Nombre |
   |---|---|---|
   | 1 | Red interna | LAB-WAN1 |
   | 2 | Red interna | LAB-WAN2 |
   | 3 | Red interna | LAB-LAN |
   | 4 | Adaptador solo anfitrión | La red creada en el paso 2 |

4. Arranca el CHR, entra por la consola de VirtualBox y compara las MAC de
   Interfaces con las de los adaptadores. En IP → Addresses asigna
   `10.255.255.1/24` al puerto que realmente corresponde a administración, si
   esa dirección todavía no está configurada. No la dupliques ni elimines la
   dirección anterior hasta comprobar el nuevo acceso.
5. Desde Windows comprueba acceso con WinBox a `10.255.255.1`. Mantén la consola
   abierta hasta confirmar. Si ese puerto forma parte de un bridge existente,
   revisa la configuración antes de separarlo: no cambies a ciegas tu acceso.
6. Para la prueba inicial deja las redes internas sin otras VMs. Para la fase
   de tráfico añade los dos routers de salida y el cliente de la tabla anterior;
   el cliente debe tener una sola tarjeta en LAB-LAN.

Si solamente quieres probar la lectura ahora, conserva los tres adaptadores y tu
IP actual; no es obligatorio reconstruir la topología todavía. Estos pasos están
basados en los [modos de red de VirtualBox](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/networkingdetails.html).

### Certificado y usuario de lectura

Realiza esto únicamente en el CHR de laboratorio, con la consola disponible.
Usa la IP actual de administración para la primera prueba. El ejemplo siguiente
supone que ya preparaste LAB-MGMT con 10.255.255.1 y Windows con 10.255.255.2.
Si usas otra IP, cambia tanto SAN como restricciones y comando del agente.

1. Revisa fecha y hora de Windows y CHR.
2. En **System → Certificates**, crea una CA `ecmp-lab-ca`, con Common Name
   `ecmp-lab-ca`, Key Usage `key-cert-sign,crl-sign`; fírmala como CA y confía en ella.
3. Crea `ecmp-lab-api`, con Common Name `ecmp-lab-api`, Subject Alt Name
   `IP:10.255.255.1` y Key Usage `digital-signature,key-encipherment,tls-server`.
   Fírmalo con `ecmp-lab-ca` y comprueba que tenga clave privada y esté vigente.
4. Exporta solamente el certificado público de `ecmp-lab-ca` en PEM, sin exportar
   su clave privada. Descarga el `.crt` desde Files a una carpeta local, por ejemplo
   `C:\ecmp-lab\router-ca.crt`. El agente acepta PEM con extensión `.crt`.
5. En **IP → Services**, habilita `api-ssl`, puerto `8729`, asigna `ecmp-lab-api`
   y restringe Available From a `10.255.255.2/32`. No habilites API sin TLS.
6. Si el firewall input bloquea ese tráfico, añade desde WinBox una regla TCP 8729
   limitada a la IP de Windows y la interfaz administrativa, antes del bloqueo
   correspondiente. No deshabilites todo el firewall ni expongas API en las WAN.
7. En **System → Users → Groups**, crea `ecmp-reader` con políticas `read,api`.
   Crea un usuario de laboratorio de ese grupo con una contraseña única introducida
   localmente. No uses una cuenta de administrador para esta lectura.

Los nombres de opciones pueden variar con la versión de WinBox/RouterOS.
Referencias oficiales: [certificados](https://help.mikrotik.com/docs/spaces/ROS/pages/2555969/Certificates)
y [servicios](https://help.mikrotik.com/docs/spaces/ROS/pages/103841820/Services).

## Ejecutar la primera prueba

En Windows, comprueba primero la conectividad:

```powershell
Test-NetConnection 10.255.255.1 -Port 8729
```

Desde la raíz del proyecto ejecuta lo siguiente, sustituyendo la identidad,
versión exacta e interfaz por las que muestra tu CHR. `7.X.Y (stable)` es un
marcador: no lo uses literalmente. La carpeta de salida debe existir.

```powershell
.\dist\ecmp-agent\ecmp-agent.exe --diagnose --host 10.255.255.1 --ca C:\ecmp-lab\router-ca.crt --identity lab-router --routeros-version "7.X.Y (stable)" --management ether4 --report C:\ecmp-lab\prueba-01.json
```

Alternativa desde fuentes, con las mismas opciones:

```powershell
.\.venv-mvp\Scripts\python.exe -m agent.app.main --diagnose --host 10.255.255.1 --ca C:\ecmp-lab\router-ca.crt --identity lab-router --routeros-version "7.X.Y (stable)" --management ether4 --report C:\ecmp-lab\prueba-01.json
```

El usuario y la contraseña se piden por consola. No se necesita token del servidor,
OpenAI, PHP ni archivos `.env`. Copia toda la carpeta `dist/ecmp-agent` si ejecutas
el agente en otro Windows, no solamente el `.exe`.

Resultado esperado: `Diagnostico: passed`, código de salida 0 e informe con cuatro
comprobaciones aprobadas. El informe contiene identidad, versión, nombres de
interfaces y cantidades de filas; no contiene contraseñas, direcciones de tablas
ni configuración completa. `ecmp_certified` y `real_writes_enabled` siguen en false.
El programa no sobrescribe informes: usa `prueba-02.json` en otro intento.

Si falla TLS, revisa CA, SAN, vigencia y reloj. Si hay timeout, revisa red virtual,
IP y firewall. Si falla conexión/lectura, revisa usuario, políticas y servicio.
Si falla una comprobación, compara identidad, versión e interfaz esperadas con
las reales en WinBox. No desactives la validación de certificados para continuar.

## Qué enviar después y qué falta para ECMP

Comparte el JSON de diagnóstico (puedes anonimizar la identidad) y responde los
datos pendientes del principio. Para la etapa ECMP necesitaremos además las dos
subredes/gateways WAN y confirmar la red LAN y la cuarta interfaz.

Queda por implementar y ensayar la variante v7: tablas/routing marks, generación,
prechequeo de rutas conectadas dinámicas, ejecución, preservación de administración,
verificación desde el cliente LAN y pérdida/recuperación de cada WAN. La prueba de
lectura no sustituye esos ensayos. Conserva el snapshot para restauración manual.
No se ha conectado ni modificado tu CHR desde esta sesión.
