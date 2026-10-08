# Validación realizada · 08/10/2026

## Resultados

| Comprobación | Resultado |
|---|---|
| Python `unittest discover -s tests -v` | 27 pruebas superadas |
| Vitest `npm test` | 13 pruebas superadas |
| Playwright/Chromium `npm run test:e2e` | 10 pruebas superadas |
| TypeScript y Vite `npm run build` | Compilación correcta |
| Reinstalación `npm ci` | Lockfile respetado; instalación correcta |
| SQLite `integrity_check` / `foreign_key_check` | Integridad correcta; cero referencias inválidas |
| Reconstrucción aislada desde originales | Hashes, estados, temas y relaciones iguales a la base activa |
| Fuentes principales | 16 URLs oficiales con respuesta 200 archivada |
| Actualizaciones | 16 normas contrastadas; cero cambios de texto detectados |
| Imágenes de normativa | 732 referencias descargadas y hashes comprobados |

## Qué cubren

Las pruebas Python contrastan identidad y título, índice, bloques ausentes y duplicados, artículos vacíos, rechazo de originales alterados, futuras versiones, URLs no oficiales, FTS, conservación de candidatas y separación del contenido de IA. Comprueban además los 30 títulos literales, ausencia de históricos en relaciones de estudio, hashes de todos los fragmentos, originales e imágenes y concordancia íntegra de las exportaciones JSON con SQLite.

Vitest comprueba que la revisión pendiente y los alcances inciertos bloquean ejercicios; que los tests tienen cuatro alternativas distintas con una sola respuesta literal; que el cloze reconstruye el fragmento; y que flashcards/recuperación revelan el texto. Comprueba intervalos, fallo, cambio de versión, persistencia entre conexiones, importación sin sobrescritura, validación de copias y transacción atómica de intento y repaso. Las fixtures unitarias son neutras y no se importan a la base.

Playwright comprueba la aplicación con datos reales: catálogo, selección múltiple, lectura del artículo 14 de la Constitución, enlace BOE, bloqueo de ejercicios sin comprobación granular de fuente, memorización tras recargar, dificultad, calendario, descarga de copia y diseño a 390×844 sin desbordamiento horizontal. Se registra una captura móvil en `test-results/mobile-fuentes.png`.

Las pruebas de estudio usan el banco real de 141 pasajes de los temas 2, 7 y 26. Comprueban test con cita y corrección, flashcards, cloze, relación de referencias, recuperación escrita, resumen, repetición del fallo concreto, pausa y recuperación tras recargar y ausencia de sesiones duplicadas. La migración desde IndexedDB versión 1 conserva una primera memorización existente.

Las dos pruebas Python del banco comprueban cada cita, intervalo de respuesta, hash de unidad, original independiente, cuatro opciones distintas y procedencia de cada distractor. Comprueban además que no se han promovido los estados jurídicos ni generado contenido de IA. Las pruebas unitarias de sesión verifican transacción conjunta de intento, sesión y arrastre, rollback ante duplicados y validación de la copia. Se bloquean sesiones cuyo pasaje, respuesta u opciones ya no coincidan con el banco vigente.

## Límites

Las comprobaciones son técnicas; no equivalen a revisión jurídica de vigencia o alcance. El contraste independiente de cinco artículos del PDF CAIB se ejecutó y encontró cinco discordancias de extracción/notas que requieren revisión; continúan pendientes su resolución, los anexos abreviados de ese documento y la delimitación de temas señalada en `COBERTURA.md` y `NOTAS.md`.

Se ha comprobado navegación con teclado y etiquetas básicas; no se ha realizado una auditoría completa WCAG, ni pruebas en Safari/iPhone real, ni una comprobación exhaustiva de todas las tablas y figuras. No hay validación de PWA ni de sincronización. La proyección carga normativa por norma y los recursos bajo demanda.
