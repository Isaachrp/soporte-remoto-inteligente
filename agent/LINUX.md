# Agente de diagnóstico para Linux

Esta edición utiliza exactamente la misma interfaz y lógica que Windows:
IP/nombre, usuario, contraseña y diagnóstico de solo lectura
por API TCP 8728 sin certificado, y exportación del JSON completo para el servidor.
La conexión no cifra las credenciales: usar LAN confiable o VPN.
Arial puede ser sustituida por la fuente equivalente instalada en Linux.

Es una distribución de fuentes ejecutables con Python, no un binario autónomo.
Requiere escritorio gráfico, Python 3.10 o posterior, Tk y venv.

Extraer `agente-diagnostico-linux.tar.gz` y abrir una terminal en `agente-linux`:

```bash
# Solo si faltan dependencias del sistema en Ubuntu/Debian:
sudo apt install python3 python3-tk python3-venv
bash agent/preparar-linux.sh
bash agent/iniciar-diagnostico.sh
```

La preparación descarga las dependencias Python y las instala en un entorno
local del agente, sin modificar Python del sistema. Requiere Internet durante
esa preparación. Los siguientes arranques solo requieren acceso al router.
No ejecutar la aplicación como root.

Introducir IP, usuario y contraseña del router. Habilitar el servicio api
en TCP 8728, limitado a la PC del cliente. Guardar el JSON y entregarlo al
técnico para cargarlo en el servidor. Las credenciales no se exportan.
La aplicación no configura Wi-Fi, VPN, rutas ni el MikroTik.
