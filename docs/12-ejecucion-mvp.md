# Ejecutar el MVP local

## Requisitos y entornos

Python 3.12 x64, PHP 8.2 o posterior y Windows para construir/probar el paquete portátil. Los comandos parten de la raíz del repositorio. Se verificó con Python 3.12.14 y el PHP de XAMPP. No reutilizar los `.venv` iniciales de Python 3.14 para estos locks.

```powershell
py -3.12 -m venv .venv-mvp
.\.venv-mvp\Scripts\python.exe -m pip install -r tests/requirements.lock
py -3.12 -m venv agent/.venv-portable
.\agent\.venv-portable\Scripts\python.exe -m pip install -r agent/requirements.lock
```

Para un servidor independiente, instalar `server/requirements.lock` en su propio entorno en vez del lock de pruebas. Los archivos `.txt` declaran dependencias directas; los `.lock` fijan también las transitivas verificadas. Los locks corresponden a Windows/Python 3.12. No se modifican los entornos anteriores.

## Configuración

La [guía de IA integrada](17-arquitectura-ia-mvp.md) describe los planes, resultados,
pruebas sin consumo y activación del proveedor real. No se necesita OpenAI para la
demostración simulada; una clave faltante en modo openai se informa al solicitar IA.

Copiar `server/.env.example` a `server/.env` y `agent/.env.example` a `agent/.env`. No sobrescribir archivos existentes. El servidor y el agente cargan sus archivos respectivos desde la raíz del repositorio. El ejecutable trasladado puede usar variables del proceso o `agent/.env` relativo a su carpeta de trabajo, siempre sin credenciales del router.

Definir **tres tokens aleatorios distintos de al menos 32 caracteres**: técnico, registro de agente y generador. Se puede generar cada valor con `python -c "import secrets; print(secrets.token_urlsafe(32))"`. No reutilizar los tokens de las pruebas. Los tokens se introducen localmente, no en solicitudes de IA ni parámetros ECMP.

| Variable | Componente | Significado |
|---|---|---|
| `ECMP_MODE` | servidor/agente | `real` por defecto; usar `simulated` explícitamente para la demostración |
| `ECMP_AI_MODE` | servidor | `simulated` u `openai`; sin fallback |
| `ECMP_DATABASE` | servidor | Ruta SQLite, por defecto `server/mvp.sqlite3` |
| `ECMP_TECHNICIAN_TOKEN`, `ECMP_TECHNICIAN_ID` | servidor | Credencial e identidad del único técnico del MVP |
| `ECMP_AGENT_TOKEN`, `ECMP_AGENT_ID` | servidor | Credencial de registro y agente permitido |
| `ECMP_GENERATOR_TOKEN` | servidor/PHP | Secreto compartido de la integración HTTP |
| `ECMP_GENERATOR_URL` | servidor | URL fija de `api/ecmp.php` |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | servidor | Clave y modelo; ejemplo `gpt-4o-mini`, sin llamadas en las pruebas |
| `ECMP_SERVER_URL` | agente | URL del backend; HTTPS fuera de loopback |
| `ECMP_ROUTER_ID` | agente | Referencia local del destino; nunca una credencial |
| `ECMP_ROUTER_HOST`, `ECMP_ROUTER_CA` | agente real | Nombre/IP que coincida con SAN del certificado y archivo CA confiable |

El agente solicita el token de registro, usuario y contraseña de RouterOS al iniciar. No los almacena en disco. `--token-stdin` permite suministrar el token por un pipe controlado para pruebas; no aceptarlo mediante argumentos de línea de comandos. La contraseña real del router no tiene opción de persistencia.

PHP lee `ECMP_GENERATOR_TOKEN` del entorno de su proceso; no carga automáticamente su `.env.example`. No necesita `config.php`, MySQL ni una sesión de la interfaz heredada para este endpoint.

## Demostración supervisada

1. Configurar `ECMP_MODE=simulated` en servidor y agente, `ECMP_AI_MODE=simulated` en servidor, `ECMP_SERVER_URL=http://127.0.0.1:8000` y `ECMP_GENERATOR_URL=http://127.0.0.1:8091/api/ecmp.php`.
2. En una terminal, establecer `$env:ECMP_GENERATOR_TOKEN` al mismo valor configurado en servidor y ejecutar:

```powershell
C:\xampp\php\php.exe -S 127.0.0.1:8091 -t php/sistema-generador
```

3. En otra terminal:

```powershell
.\.venv-mvp\Scripts\python.exe -m uvicorn server.app.main:create_app --factory --host 127.0.0.1 --port 8000
```

4. En otra terminal:

```powershell
.\agent\.venv-portable\Scripts\python.exe -m agent.app.main
```

5. Abrir `http://127.0.0.1:8000/`. Introducir el token del técnico y la sesión que imprime el agente. Mantener `router-1`, identidad `lab-router` y administración `ether14` para la simulación.
6. Crear la solicitud con el ejemplo precargado. El agente consulta la tarea mediante polling. Cuando aparezca `await_approval`, revisar script, operaciones, prechequeo, hashes y advertencias.
7. Aprobar ese artefacto o rechazarlo. El resultado esperado de la simulación es `configuration_with_warnings`: se comprueba estructura de configuración, pero no se realiza tráfico WAN ni conectividad LAN.
8. Consultar auditoría. Detener el agente con Ctrl+C para cerrar la sesión, conexiones y proceso.

Ejemplo de cuerpo para `POST /requests` (autenticación Bearer del técnico):

```json
{
  "text": "Configurar balanceo ECMP",
  "session_id": "ID-MOSTRADO-POR-EL-AGENTE",
  "target": {"router_id":"router-1","identity":"lab-router","management_interface":"ether14"},
  "parameters": {
    "tipo":"ECMP", "lineas":2,
    "vel1":"5M", "gw1":"192.168.1.1", "ip1":2,
    "vel2":"10M", "gw2":"192.168.2.1", "ip2":2,
    "lan":"172.16.0.1", "dhcp":true
  }
}
```

Obtener el `binding_hash` de `GET /requests/{id}` y enviar `{"decision":"approve","binding_hash":"VALOR-REVISADO"}` a `/requests/{id}/decision`. Cambiar parámetros después de generar exige una solicitud nueva; no hay endpoint que edite el artefacto. Los parámetros omitidos pueden completarse por `PUT /requests/{id}/parameters` únicamente en `await_parameters`.

## Distribución portátil

```powershell
.\agent\.venv-portable\Scripts\python.exe -m pip install -r agent/build.lock
.\agent\.venv-portable\Scripts\python.exe agent/build_portable.py
.\.venv-mvp\Scripts\python.exe agent/verify_package.py dist/ecmp-agent
.\dist\ecmp-agent\ecmp-agent.exe --version
```

Copiar **la carpeta completa** `dist/ecmp-agent`, incluido `_internal`, `VERSION` y `SHA256SUMS`. Incluye runtime Python y dependencias; no necesita el `.venv` de desarrollo en el equipo de destino. El manifiesto debe distribuirse por un canal confiable: un hash dentro de una descarga no autentica por sí solo esa descarga. El verificador rechaza archivos alterados, adicionales o faltantes. No hay firma Authenticode aún.

El build es repetible a partir de fuentes y locks; no se promete identidad binaria bit a bit entre máquinas/fechas. `dist/` y `build/` están ignorados en Git. PyInstaller puede emitir advertencias de módulos opcionales (`tzdata`, módulos experimentales Pydantic); la prueba del ejecutable trasladado es la evidencia de operación, no la mera compilación.

## Pruebas

```powershell
$env:PHP_EXE = 'C:\xampp\php\php.exe'
.\.venv-mvp\Scripts\python.exe -m pytest -q
.\.venv-mvp\Scripts\python.exe -m pytest -q tests/integration
.\.venv-mvp\Scripts\python.exe -m pytest -q tests/e2e
```

Sin paquete construido, la prueba portátil queda omitida con motivo explícito. La prueba de laboratorio también se omite salvo autorización explícita. El resto de las pruebas exige PHP real y falla si no inicia; no lo reemplaza por un mock. Los procesos PHP/Uvicorn/agente iniciados por pruebas se cierran al finalizar. No se consume OpenAI.

## Router real y laboratorio

Preparar manualmente con WinBox un router aislado: certificado con SAN correcto, CA confiable, `api-ssl` TCP 8729 habilitado y restringido a la PC/VPN del agente; cuenta específica con permisos mínimos de lectura. Conservar acceso administrativo dedicado y respaldo fuera del sistema. El agente no habilita servicios ni configura firewall para obtener acceso. No implementa 8728 ni degradación insegura.

El smoke test real es **solo lectura**, se habilita con `ECMP_LAB_AUTHORIZED=1` y variables temporales `ECMP_LAB_USER`, `ECMP_LAB_PASSWORD`, `ECMP_LAB_IDENTITY`, `ECMP_LAB_VERSION`, `ECMP_ROUTER_HOST`, `ECMP_ROUTER_CA`; ejecutar `pytest -q -m lab tests/lab`. Retirar las variables sensibles de la sesión al terminar. No entregar su contenido en reportes.

No existe actualmente una ruta habilitada para escribir en laboratorio. Antes de habilitarla se necesita adaptar/certificar el legado por versión exacta, revisar y ensayar la ejecución nativa de operaciones, probar precondiciones reales, fallos parciales y verificación WAN/LAN. La prueba de lectura no certifica ECMP. Ver matriz y limitaciones.
