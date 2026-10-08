# Estado de PL Study · 08/10/2026

## Trabajo conservado

- Base jurídica `temario.db`: 30 temas, 16 normas, 3.791 unidades, 79 relaciones de alcance y 2.223 enlaces tema/unidad. 71 unidades históricas excluidas del estudio. Originales y recursos archivados por hash; exportación completa en `export/`.
- Importación BOE, consolidado CAIB y original BOIB separado, programa oficial 2026 y comparación 2022. Caché, límite de peticiones, controles técnicos, búsqueda FTS y detección de candidatas.
- `COBERTURA.md`, `NOTAS.md`, `PRUEBAS.md`, `README.md` y registros en `data/`.
- Interfaz React/TypeScript: catálogo, selección de uno/varios/30 temas, selección de unidades, lector, búsqueda, tablas, imágenes y fuentes.
- Motores de cinco métodos, corrección literal, autoevaluación para recuerdo, intentos con referencias y versión, Mis errores, estadísticas por tema/artículo y evolución diaria.
- Memorización por unidades o grupos, fechas independientes, dificultad, intervalos adaptativos, calendario, progreso IndexedDB y copias JSON aditivas.
- 27 pruebas Python, 13 Vitest y 10 Playwright superadas; compilación correcta. Fuentes y datos activos no marcados automáticamente como jurídicamente verificados.

## Estado por fase

1. **Importación y organización realizadas; revisión jurídica pendiente.** Quedan temas 1, 5, 17, 20 y 22 con incidencias específicas, revisión de vigencia/alcance de todos los temas y resolución de las cinco discordancias del contraste PDF independiente.
2. **Tres pilotos de práctica literal funcionales:** temas 2, 7 y 26, con 141 pasajes y 35 unidades BOE contrastadas. Test de cuatro opciones, flashcards, cloze, relaciones y recuperación libre. La revisión jurídica global no se marca como completada; faltan casos prácticos y preguntas interpretativas revisadas.
3. **Registro y estadísticas funcionales y probados con el banco real.** Sesiones recuperables, resumen, repetición del ejercicio fallado y estadísticas. Las respuestas se guardan con fuente, cita y versión; se conservan los intentos anteriores.
4. **Memorización, planificación individual y repaso manual funcionales.** Los ejercicios actualizan el arrastre si la unidad ya está memorizada, dentro de la misma transacción que el intento.
5. **Comprobaciones automáticas y responsive realizadas.** Pendientes auditoría completa de accesibilidad y navegador iPhone real.

## Siguiente trabajo

1. Revisar `COBERTURA.md` y cada incidencia sin cambiar estados globales a ciegas. Resolver delimitación por fuente oficial y confirmar la interpretación material cuando sea necesario.
2. Revisar las páginas completas y notas de `data/marco-paginas.json` contra el PDF original archivado. Revisar las cinco discordancias registradas en `data/marco-contraste-independiente.json` y la extracción candidata de pdftotext; los anexos `(...)` continúan pendientes aunque la extracción pase.
3. Obtener fuente EBAP oficial para el tema 17. No elaborar doctrina de accidentes desde memoria.
4. Mantener la revisión jurídica global pendiente y la comprobación de pasajes separada. No basta `estado_fuente=ok`: cada ejercicio literal necesita evidencia independiente, cita y respuesta exactas, hash activo y alcance documentado.
5. Revisar pedagógica y jurídicamente los tres pilotos literales antes de ampliar al resto del temario o introducir casos prácticos. Mantener IA separada y pendiente hasta su revisión.
6. Después, añadir PWA/offline y auditoría de accesibilidad. La publicación de la app fue autorizada; las actualizaciones de esta versión mantienen los avisos de revisión pendiente.

## Reanudar

```bash
cd /workspace/App-PL
PIP_CACHE_DIR=/workspace/.pip-cache .venv/bin/python -m pip install -r requirements.txt
npm --cache /workspace/.npm-cache ci
.venv/bin/python scripts/reports.py
npm run data
.venv/bin/python -m unittest discover -s tests -v
npm test
npm run build
npm run test:e2e
npm run dev -- --port 4173
```

La base no debe reconstruirse ni reimportarse por rutina si ya está presente y es correcta. Para revisar nuevas versiones ejecutar `scripts/check_updates.py`; conserva las activas y registra candidatas. Para una reconstrucción aislada usar `PLSTUDY_DB=/tmp/plstudy-rebuild.db PLSTUDY_EXPORT=/tmp/plstudy-rebuild-export .venv/bin/python scripts/build.py`.

Actualización: el usuario autorizó publicar la versión de prueba. Los archivos compilados se han subido a `gh-pages` (commit `3a959a6c564bfff659f7ea3d68d6789cffd7a290`); falta activar/comprobar GitHub Pages porque la API y el sitio están bloqueados desde este entorno. Ver `PUBLICACION.md`. El código de desarrollo y la base están conservados en el checkout. La configuración reutilizable de instalación y arranque se guarda como borrador del entorno; guardar ese borrador no publica la aplicación.
