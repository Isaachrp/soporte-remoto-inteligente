# Interfaz de diagnóstico

Abrir `ecmp-agent.exe` sin argumentos muestra la interfaz. Copiar la carpeta
completa `dist/ecmp-agent`, incluyendo `_internal`, a la PC del cliente.
Para iniciar desde las fuentes, usar `agent/iniciar-diagnostico.cmd`.

Introducir IP o nombre del MikroTik, usuario y contraseña. No se pide certificado.
La PC debe tener conectividad al router; la aplicación no configura
Wi-Fi, VPN ni rutas de Windows. El router debe tener API habilitada en TCP
8728. Esta conexión no cifra las credenciales: usar LAN confiable o VPN y no
exponer el puerto a Internet. Usar una cuenta con
permisos de lectura de las tablas consultadas.

Pulsar **Conectar y diagnosticar** y después **Guardar diagnóstico JSON**.
El técnico transporta ese archivo a su PC y lo carga en el sistema central.
Incluye `snapshot.identity`, `snapshot.version` y todas las tablas permitidas
por el contrato compartido; no contiene usuario, contraseña ni claves privadas.
Un fallo de conexión o lectura no habilita la exportación de información parcial.

La interfaz conserva Arial, fondo gris, panel blanco y botones verdes del sistema.
Se implementa como ventana nativa para funcionar sin servidor ni navegador.
Las opciones de línea de comandos anteriores siguen disponibles.

El diagnóstico no garantiza compatibilidad ECMP: el servidor decide si el router
cumple la variante soportada. La prueba de contrato se realizó con router simulado;
la conexión física al MikroTik debe validarse en el laboratorio.

En WinBox: revisar la IP en **IP > Addresses**; habilitar **api** en
**IP > Services** con puerto 8728 y limitar Available From a la IP de la PC.
El usuario es una cuenta de **System > Users**, con permisos `read` y `api`.
La contraseña es la de esa cuenta del router, no la de Windows ni la del Wi-Fi.
Si no se conoce, solicitarla al administrador o pedir una cuenta dedicada.
El firewall debe permitir TCP 8728 desde esa PC; no deshabilitarlo por completo.

Este cambio afecta solo al diagnóstico gráfico. El ejecutor generado por el
servidor y las opciones TLS anteriores conservan sus requisitos existentes.
