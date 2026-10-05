# Entrega del MVP local — 30-09-2026

## Resultado

| Criterio | Evidencia real | Estado |
|---|---|---|
| Integración local | PHP real, FastAPI/LangGraph/SQLite reales, HTTP entre tres procesos; IA y RouterOS simulados | Verificada |
| Ejecución de laboratorio | No se proporcionó router/CHR, certificado ni credenciales de laboratorio | Pendiente; escrituras bloqueadas |
| Modalidad portátil | Binario PyInstaller copiado a carpeta distinta, hashes comprobados, sin `.venv`, flujo HTTP y salida 0 en Windows 11 | Smoke test verificado con RouterOS simulado; aceptación completa con api-ssl pendiente |

No se certificó ninguna versión RouterOS. No se consumió OpenAI ni se modificó un router real.

## Estado inicial encontrado

- No se encontraron archivos `AGENTS.md` en el repositorio ni ancestros examinados.
- `server`, `agent`, `shared` y pruebas tenían estructura preparada, sin implementación Python ni pruebas. Los `.venv` existentes contenían Python 3.14.6; no acreditaban una aplicación funcional.
- Había cambios locales en `.gitignore`, README y ocho documentos de diseño/caso de uso; cuatro documentos 08–11 y todo `php/` estaban sin seguimiento. Se conservaron; no se hizo commit, push, reset ni reescritura de historial.
- El recorrido manual era `index.php → parametros.php → aplicar.php → legacy_ecmp()`. La función ya estaba extraída y conectada: no se creó un segundo generador en Python.
- `procesar.php` invoca `consultarIAOR`, convierte JSON a parámetros y carga `aplicar.php`. `openai.php` pertenece a la integración heredada OpenRouter pese al nombre del archivo. Las propuestas de `proponer.php` son otro recorrido que puede producir scripts libres; se dejó fuera del nuevo workflow.
- El diagnóstico PHP consultaba RouterOS con puerto predeterminado 8728; su cliente deshabilita validación de certificado/nombre. No se reutilizó para el agente TLS ni se alteró ese módulo como parte de una migración no solicitada.
- La documentación aún contenía propuestas de interacción con Windows/WinBox. Se aplicaron las decisiones específicas posteriores: solo ECMP, API nativa y agente portátil.

## Archivos y decisiones

Nuevos componentes: `server/app` (API, configuración, IA encapsulada, cliente PHP, coordinación, LangGraph, SQLite e interfaz), `agent/app` (CLI, polling, prevalidación y transportes), `shared` (esquemas, hashes, allowlist/adaptación y verificación), pruebas `tests/integration`, `tests/e2e` y laboratorio optativo `tests/lab`.

Se añadieron manifiestos y locks separados, `.env.example` sin secretos, build/verificador portátil, fixture del PHP anterior, `pytest.ini` y documentos 12–14. Se modificaron `.gitignore`, README, documentos 08/10/11 y dos archivos PHP existentes (`aplicar.php`, `lib/ecmp-legacy.php`). Se añadieron `lib/ecmp-contract.php`, `api/ecmp.php` y ejemplo de entorno PHP. Los demás cambios documentales mostrados por Git ya existían al iniciar.

Dependencias directas: FastAPI 0.115.12, Uvicorn 0.34.2, Pydantic 2.11.4, LangGraph 0.4.8, OpenAI SDK 1.82.0, httpx 0.28.1, python-dotenv 1.1.0; agente con librouteros 3.4.1; pytest 8.3.5; empaquetado PyInstaller 6.14.0. Se eligió Python 3.12.14 después de que la instalación en el entorno previo Python 3.14 fallara compilando pydantic-core. El entorno previo no se eliminó ni reconstruyó.

Biblioteca RouterOS: capacidades de `ssl_wrapper`, identidad TLS, timeout y cierre comprobadas mediante lectura de su código instalado y pruebas con dobles. Handshake/semántica real no comprobados. No se implementó el puerto inseguro 8728.

Los [endpoints, acciones y controles](13-implementacion-mvp.md) y los [comandos completos](12-ejecucion-mvp.md) describen el estado implementado.

## Pruebas realizadas

Comando final en este workspace:

```powershell
.\.venv-mvp\Scripts\python.exe -m pytest -q
```

Resultado: **73 passed, 1 skipped, 1 warning in 22.73s**.

- Omitida: `tests/lab/test_readonly.py`, porque no se habilitó un laboratorio autorizado.
- Advertencia: deprecación `anyio.abc.BlockingPortal` utilizada por `starlette.testclient`. No se ocultó ni se desactivaron pruebas.
- PHP 8.2.12 CLI real atendió las solicitudes HTTP de generación en todas las integraciones.
- Regresión manual de la función de generación: ocho casos 2/3/6/12 WAN × DHCP activado/desactivado. No se probó el login/flujo comercial MySQL completo de la interfaz PHP heredada.
- Esquemas/límites, procedimientos excluidos, autenticación, TLS configurado, timeout/desconexión, normalización, rechazo de sintaxis, compatibilidad cerrada, parámetros posteriores bloqueados, aprobación alterada/reutilizada/vencida, duplicados iguales/conflictivos, sesiones ajenas, reinicio en espera de aprobación, escritura parcial y reconciliación de solo lectura.
- E2E con procesos separados: PHP real, Uvicorn real y agente Python; luego ejecutable trasladado a otra carpeta y sin rutas del intérprete de desarrollo. El router/IA estuvieron simulados explícitamente en ambos.
- Resultado no inferido de aceptación API: se inspeccionan tablas simuladas después de aplicar; un NAT faltante provoca fallo. WAN/LAN constan como no realizados.
- Sintaxis PHP comprobada en `aplicar.php`, `lib/ecmp-legacy.php`, `lib/ecmp-contract.php` y `api/ecmp.php`: sin errores.
- `pip check`: `No broken requirements found.`
- `git diff --check`: sin errores; Git avisa normalización LF/CRLF de `.gitignore`.
- `agent/verify_package.py dist/ecmp-agent`: paquete íntegro, **73 archivos**.

El build emitió advertencias de imports opcionales (`tzdata`, Pydantic experimental y módulos no Windows). La prueba funcional del binario fue satisfactoria; no se afirma que cubra rutas opcionales ni routers reales.

El ejecutable generado tiene SHA-256 `fb798ff4d72171eaa67f0effbca4296f1d95f0c26bf7a125435e32f045b59322`. El manifiesto completo está en `dist/ecmp-agent/SHA256SUMS`; se debe publicar por un canal confiable. Los resultados de build están ignorados en Git, disponibles en el workspace.

## Límites y trabajo pendiente

1. Laboratorio real v6/v7: versiones exactas, configuración previa, sintaxis legacy, preservación de acceso, fallos parciales, routing marks/tablas v7, DNS/DHCP y verificación WAN/LAN. No existen variantes certificadas ni ejecutor de escritura nativa habilitado. `NativeRouter.apply` rechaza toda escritura real.
2. La IA real está encapsulada pero no se invocó. Clasifica vocabulario cerrado; captura de parámetros desde prosa libre pendiente. Los parámetros se completan explícitamente en formulario.
3. La recuperación consulta y registra estado real/simulado, conserva la incertidumbre y bloquea nuevas escrituras. No hay rollback ni resolución automática de incidentes. La liberación de un router en intervención exige un procedimiento posterior revisado; no editar datos para omitir controles.
4. La portabilidad completa requiere cuenta estándar independiente, otros equipos Windows, política antivirus, distribución autenticada/firma y flujo api-ssl real. El ensayo ejecutado prueba traslado y ausencia de dependencia del `.venv`; no acredita todos esos entornos.
5. Seguridad/operación inicial: un técnico y un agente configurados, sin RBAC multiusuario, rotación administrada de tokens, cifrado de SQLite ni despliegue productivo. Se requiere proteger archivo y directorio mediante permisos Windows. El endpoint HTTP local no debe exponerse como producción.
6. Interfaz nueva servida por FastAPI; no se migra el login PHP/MySQL. Se probaron sus APIs; no se realizó una prueba visual de navegador.
7. Prechequeo conservador para laboratorio preparado. No se aplican cambios a redes existentes ni se infiere que ausencia de tráfico equivalga a fallo ECMP.

## Git

Se conserva el trabajo previo. El diff de archivos ya rastreados incluye cambios iniciales del usuario; PHP completo y las implementaciones nuevas no aparecen en `git diff --stat` por estar sin seguimiento. El inventario separado y salida final están en [estado Git de entrega](15-estado-git-mvp.txt). No se hicieron commits ni push.
