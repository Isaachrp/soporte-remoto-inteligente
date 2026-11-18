# Entrega al asesor — 6 de noviembre de 2026

Material preparado con el estado observado del proyecto. No se modificó el sistema ni se ejecutaron pruebas nuevas sobre el router para preparar esta entrega.

## Abre estos archivos

1. **INFORME.md**: documento para compartir con el asesor.
2. **GUION-Y-DEMO.md**: qué decir, qué mostrar, preparación y contingencias.
3. **EVIDENCIAS.md**: resultados, su procedencia y sus límites.
4. **evidencias-resumidas.json**: extracto de las entregas locales y transcripción resumida de los resultados comunicados por el alumno. No es un diagnóstico importable ni un paquete ejecutable.

## Mensaje central

> El avance integra diagnóstico, recomendaciones de IA, selección supervisada y generación de entregas independientes usando el generador PHP existente. Se demostró la verificación de ECMP sin duplicar su configuración. La aplicación PCC todavía tiene un fallo pendiente de diagnóstico.

## Alcance de esta carpeta

Es un paquete documental. No contiene claves, `.env`, bases SQLite, contraseñas, ejecutables ni scripts listos para aplicar. Los IDs se conservan para relacionar las evidencias con el historial local.

Los documentos 18–25 del proyecto describen avances anteriores. Para exponer el flujo actual usa primero este paquete: el servidor central recibe un JSON y entrega archivos, sin requerir un agente conectado permanentemente.

El ZIP hermano de esta carpeta contiene los mismos documentos para enviarlos al asesor. El código y el laboratorio permanecen en el proyecto original.
