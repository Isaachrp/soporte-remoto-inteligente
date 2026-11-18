# Primer avance: instalación y demostración

Fecha de entrega preparada: 4 de octubre de 2026.

El entregable es un prototipo funcional de soporte supervisado: solicitud → plan
validado → diagnóstico → script PHP → aprobación → ejecución simulada →
verificación → auditoría exportable. El servidor, PHP, HTTP y SQLite funcionan
realmente; el router y la IA están simulados en la demostración reproducible.
La lectura TLS de un CHR es una prueba independiente. No se certifica todavía
la aplicación de ECMP sobre RouterOS real.

## 1. Preparación en esta computadora

Abra PowerShell en la raíz del proyecto:

```powershell
Set-Location C:\xampp\htdocs\soporte-remoto-inteligente
.\iniciar-demo.cmd
```

El entorno `.venv-mvp` ya está disponible en esta computadora. El comando inicia
PHP, FastAPI y el agente en segundo plano, todos ligados a `127.0.0.1`; muestra
la URL, la clave temporal del técnico y la sesión del agente. Mantenga la terminal
abierta. No necesita iniciar Apache, MySQL, AnyDesk ni disponer de Internet.

Abra la URL mostrada, normalmente [interfaz del técnico](http://127.0.0.1:8000).
La [documentación de la API](http://127.0.0.1:8000/docs) también está disponible.
Si el puerto está ocupado:

```powershell
.\iniciar-demo.cmd --port 8001
```

No se reemplazan archivos `.env`, bases de datos previas ni procesos ajenos.
Las claves cambian en cada arranque; no se guardan en los informes. La clave
visible en la terminal es solo de esta demo y no debe aparecer en capturas.

## 2. Instalación en otra computadora

Copie el código y los archivos de dependencias. Necesita Windows, Python 3.12 x64
y PHP 8.2 o posterior (por ejemplo, el PHP de XAMPP). Desde la raíz:

```powershell
py -3.12 -m venv .venv-mvp
.\.venv-mvp\Scripts\python.exe -m pip install -r tests/requirements.lock
.\iniciar-demo.cmd --php C:\xampp\php\php.exe
```

La instalación de dependencias requiere Internet; la demo posterior no.
Si la ruta de PHP es diferente, sustituya el argumento `--php` por la ruta real.
No copie un entorno virtual de otra computadora. El lock de pruebas incluye las
dependencias del servidor y del agente necesarias para este arranque.

## 3. Guion para el asesor (8–10 minutos)

1. **Problema (1 minuto):** configurar soporte de red manualmente implica capturar
   parámetros, elegir scripts y verificar resultados. El proyecto busca centralizar
   ese recorrido y conservar autorización y trazabilidad.
2. **Alcance (1 minuto):** mostrar el aviso de modo simulado. Explicar que el primer
   procedimiento es ECMP; la demo no acredita tráfico ni balanceo real.
3. **Solicitud (2 minutos):** seleccionar ECMP y dos líneas; introducir la clave
   temporal que imprime la terminal. Pulsar Continuar. Mantener WAN1 `5M`, gateway
   `192.168.1.1`, IP `2`; poner WAN2 `10M`, gateway `192.168.2.1`, IP `2`.
   Mantener LAN `172.16.0.1` y DHCP marcado. Pegar la sesión del agente.
   Conservar `router-1`, `lab-router` y `ether14` (estos son datos del simulador).
4. **Rechazo (1 minuto):** generar, esperar «Pendiente de aprobación», revisar el
   script y pulsar Rechazar. Descargar evidencia; mostrar que no hubo ejecución.
5. **Aprobación (2 minutos):** volver a configuración y generar una nueva solicitud.
   Abrir «Evidencia, operaciones y hashes» y explicar que la autorización se vincula
   al script exacto, destino, parámetros y estado previo. Aprobar dentro de cinco
   minutos. Esperar «Configuración verificada con advertencias».
6. **Resultados (1 minuto):** mostrar las comprobaciones por línea, las pruebas de
   WAN/LAN como «No realizadas» y la auditoría. Descargar el JSON final.
7. **Laboratorio (1–2 minutos):** mostrar la topología del documento 19. Si ya se
   preparó el CHR, ejecutar el diagnóstico TLS y abrir su JSON, distinguiéndolo de
   la ejecución simulada.

Después de una aplicación, el router simulado conserva su configuración durante
esa ejecución. Para repetir una aplicación limpia, use Ctrl+C en la terminal y
vuelva a ejecutar `iniciar-demo.cmd`. Cada inicio conserva los datos anteriores
en otra carpeta; recargue el navegador e introduzca la nueva clave y sesión.
La sesión dura una hora. No deje el arranque de la exposición preparado desde el día anterior.

## 4. Autoprueba y evidencias

```powershell
.\iniciar-demo.cmd --self-test --port 0
```

Ejecuta los procesos reales, rechaza una solicitud, intenta una aprobación
alterada, aprueba otra solicitud en simulación, verifica su resultado e intenta
reutilizar la aprobación. Solo esta opción realiza una aprobación automática
como prueba; el arranque interactivo requiere el clic del técnico.

Éxito: `AUTOPRUEBA APROBADA` y código de salida 0. Los procesos se cierran al
terminar. Un fallo produce salida distinta de cero; revisar los logs, no editar
la evidencia para cambiar el resultado.

La carpeta `runtime/demo-FECHA-HORA-ID/` contiene:

| Archivo | Uso |
|---|---|
| `resultado.json` | Resumen de aceptación; identifica IA y router simulados |
| `aprobacion.json` | Solicitud, plan, script, comprobaciones y auditoría |
| `rechazo.json` | Evidencia de rechazo sin consumo de aprobación |
| `SHA256SUMS` | Huellas para detectar cambios en los tres informes |
| `conexion.json` | URL y referencias de sesión, sin claves |
| `demo.sqlite3` | Base de datos de esa ejecución local |
| `server.log`, `php.log`, `agent.log` | Diagnóstico de procesos |

Los tres primeros informes y las huellas se generan con `--self-test`. En el
recorrido manual se descarga el informe mediante «Descargar evidencia JSON».
Los JSON contienen datos de topología y auditoría; revise su contenido antes de
compartir datos de un laboratorio propio. No entregue `.env`, claves privadas,
contraseñas ni la base de datos completa.

Pruebas automatizadas generales:

```powershell
.\.venv-mvp\Scripts\python.exe -m pytest -q
```

## 5. Qué entregar

Para generar un ZIP del código y los documentos de este avance:

```powershell
.\.venv-mvp\Scripts\python.exe scripts/package_delivery.py
```

El paquete queda en `dist/primer-avance-FECHA-HORA.zip` e incluye manifiesto de
integridad. Usa una lista de archivos permitidos: solo incluye del PHP heredado
el endpoint, las bibliotecas y las imágenes que necesita el prototipo. Excluye
credenciales, entornos virtuales, datos de ejecución y la aplicación comercial
heredada. La instalación del paquete requiere seguir el paso 2 de esta guía.

- [Informe para el asesor](20-informe-primer-avance.md).
- Código: `server/`, `agent/`, `shared/`, `scripts/`, `tests/`, `php/` y archivos
  de arranque/dependencias, excluyendo archivos sensibles del sistema heredado.
- Esta guía y la [construcción del laboratorio](19-laboratorio-demostracion.md).
- [Evidencias de aceptación guardadas](evidencias/primer-avance-2026-10-04/README.md).
- Capturas de revisión/aprobación y resultado; diagnóstico CHR solo si se ejecutó.

El archivo histórico 14 describe una entrega anterior. El informe 20 y las
evidencias de esta carpeta documentan este primer avance preparado para exposición.

## 6. Problemas frecuentes

| Síntoma | Acción |
|---|---|
| Puerto ocupado | Arrancar con `--port 8001` o `--port 0` |
| No abre la página | Mantener la terminal abierta y usar su URL exacta |
| No autorizado | Usar la clave del último arranque; recargar la página |
| Sesión vencida/no encontrada | Reiniciar demo y usar la nueva sesión |
| Se queda esperando | Revisar `agent.log` y `server.log`; comprobar que los procesos sigan vivos |
| Requiere intervención tras otra ejecución | Conservar informe y reiniciar para obtener simulador limpio |
| Falta módulo Python | Instalar el lock con el Python de `.venv-mvp` |
| Error de PHP | Comprobar su ruta con `--php`; revisar `php.log` |
| Fallo de certificado CHR | Revisar CA/SAN/reloj según documento 19; no desactivar TLS |

