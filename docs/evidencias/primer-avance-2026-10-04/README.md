# Evidencias del primer avance — 4 de octubre de 2026

Los JSON se generaron ejecutando `scripts/demo.py --self-test --port 0`, con
PHP, FastAPI y agente en procesos separados. IA y RouterOS se simularon de forma
explícita. No hay pruebas de un router real en esta carpeta.

- [Resultado de aceptación](resultado.json): 5 controles aprobados y recuentos de verificación.
- [Solicitud aprobada](aprobacion.json): plan, script PHP, operaciones, verificación y auditoría.
- [Solicitud rechazada](rechazo.json): sin consumo de aprobación.
- [Huellas SHA-256](SHA256SUMS): integridad de los tres JSON originales.
- [Captura de la interfaz](interfaz.jpg): segunda ejecución manual, con un ID distinto.

La autoprueba obtuvo 19 comprobaciones estructurales aprobadas, 0 fallidas y
2 no realizadas (tráfico WAN y conectividad LAN). No confundir los recuentos de
verificación de este caso con las 119 pruebas automatizadas de la suite.

Los informes no incluyen las claves temporales del sistema. No se copió la base
de datos, archivos `.env` ni logs del arranque. Las huellas detectan modificaciones,
pero no constituyen firma digital ni certificación de RouterOS.

Para producir una nueva evidencia:

```powershell
.\iniciar-demo.cmd --self-test --port 0
```

El comando imprime la nueva carpeta de salida. Cada ejecución tiene sus propios
IDs y marcas temporales; no se espera que sus hashes coincidan con los de aquí.
