# PL Study · Policía Local de Illes Balears

Aplicación React/TypeScript con catálogo de los 30 temas del bloque común, lector de normativa oficial, selección múltiple, búsqueda y progreso personal. SQLite es la base jurídica; el navegador consume una proyección JSON por norma. La aplicación funciona sin cuentas ni credenciales.

La importación técnica está disponible. **La revisión jurídica sigue pendiente**: ningún tema se etiqueta como totalmente verificado. Hay tres pilotos de práctica literal: temas 2, 7 y 26, con 141 pasajes contrastados y 35 unidades verificadas contra el endpoint de bloque del BOE. Esa comprobación del texto no aprueba jurídicamente el tema completo. No se han generado resúmenes ni legislación de IA.

## Arranque

Desde `/workspace/App-PL`, con Python 3.12 y Node 24:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
npm --cache /workspace/.npm-cache ci
npm run data
npm run dev -- --port 4173
```

Si la base no está presente, reconstruir primero con `.venv/bin/python scripts/build.py`. La reconstrucción inicial necesita acceso HTTPS a BOE/CAIB; el desarrollo con la base y los archivos archivados no necesita descargar legislación. `npm run data` lee SQLite sin modificarla y prepara recursos locales, tablas e imágenes.

## Funciones

- Catálogo de 30 temas con títulos literales del programa oficial BOIB 34/2026; selección individual, múltiple y completa.
- Lector por tema y norma, búsqueda en los temas seleccionados, jerarquía, tablas e imágenes y enlace a la fuente. El listado limita la presentación a 150 resultados e invita a filtrar.
- Test de cuatro opciones sobre pasajes literales, flashcards, completar texto, relacionar artículos/conceptos con pasajes y recuperación libre. Tres pilotos disponibles con comprobación granular de fuente; los otros temas siguen pendientes.
- Sesiones persistentes que se pueden pausar y continuar, resumen de resultados y práctica de fallos. Registro de intentos con respuesta, fecha, tema, artículo, pasaje, hash, fuente y fecha de contraste. Mis errores permite repetir el ejercicio concreto con la misma versión.
- Primera memorización por artículo o grupo, fecha elegida, dificultad, intervalos adaptativos y calendario mensual. Marcar como memorizado es una anotación personal, no una aprobación jurídica.
- Progreso y sesiones en IndexedDB (migración aditiva a versión 2), exportación JSON e importación aditiva validada. No se sobrescriben registros existentes al importar una copia. No hay sincronización entre dispositivos.

## Pilotos de estudio

En **Estudiar**, elige Derechos fundamentales (tema 2), Tráfico (7), Seguridad vial penal (26) o los tres mezclados. Selecciona método y número de ejercicios; puedes filtrar solo errores pendientes o artículos con repaso previsto. Para elegir artículos concretos usa las casillas del lector.

Las respuestas y explicaciones usan el pasaje exacto de la norma. Los distractores son términos de otros pasajes contrastados, presentados como alternativas, no como afirmaciones jurídicas. Cada selección conserva su fuente. Los casos prácticos y las interpretaciones de alcance siguen fuera del banco hasta su revisión.

El banco se conserva separado en `ejercicios_literales` con origen `transformacion_literal`; `contenido_ia` sigue vacío. Para reconstruirlo usa `.venv/bin/python scripts/build_study.py`; para contrastarlo de nuevo con el BOE usa `--refresh`. No cambia estados jurídicos globales.

## Base jurídica y actualización

```bash
.venv/bin/python scripts/build.py
.venv/bin/python scripts/enrich.py
.venv/bin/python scripts/download_assets.py
.venv/bin/python scripts/sync_assets.py
.venv/bin/python scripts/reports.py
.venv/bin/python scripts/verify_pdf.py
npm run data
```

Las descargas usan caché, TLS verificado, identificador de cliente y límite compartido de una petición por segundo. `data/raw` conserva originales inmutables por SHA-256; `data/cache` conserva procedencia y fecha. `export/` contiene tablas completas. Las unidades históricas se archivan pero no se enlazan al estudio.

```bash
.venv/bin/python scripts/check_updates.py
.venv/bin/python scripts/query.py --tema 26
.venv/bin/python scripts/query.py --buscar habeas
```

`check_updates.py` detecta cambios sin sustituir contenido activo; guarda candidatas e informe `data/actualizaciones.json`. Antes de aceptar una actualización, revisar el contenido, fechas y temas afectados, conservar copias y después usar el mecanismo explícito `import_boe.py --accept-update`. No automatizar esa aceptación. Una modificación de PDF CAIB obliga a revisión específica.

Para registrar un paquete API descargado manualmente:

```bash
.venv/bin/python scripts/manual.py --norma ce --metadatos /ruta/metadatos.xml --texto /ruta/texto.xml --indice /ruta/indice.xml --analisis /ruta/analisis.xml
```

El paquete manual conserva hash y URL declarada pero sigue pendiente de autenticidad; no se convierte en fuente verificada. Los PDF oficiales pueden conservarse y extraerse con `import_boib.extract_pdf`; la revisión de esa extracción sigue siendo obligatoria.

## Comprobaciones

```bash
.venv/bin/python -m unittest discover -s tests -v
npm test
npm run build
npm run test:e2e
```

Playwright usa Chromium instalado en `/usr/bin/chromium`; se puede indicar otra ruta con `PLSTUDY_CHROMIUM`. Las pruebas de navegador arrancan y cierran su propio servidor en el puerto 4180, separado del desarrollo en 4173. Ver resultados y límites en `PRUEBAS.md`.

## Consultas SQLite de ejemplo

```sql
-- Fuentes del tema sin duplicar normas compartidas.
SELECT DISTINCT n.titulo_oficial, tn.papel
FROM tema_norma tn JOIN normas n USING(id_norma) WHERE tn.id_tema=26;

-- Artículos del tema, ordenados según la fuente.
SELECT DISTINCT a.id_norma,a.numero,a.rubrica,a.url_fuente
FROM tema_articulo ta JOIN articulos a USING(id_articulo)
WHERE ta.id_tema=26 ORDER BY a.id_norma,a.orden;

-- Texto íntegro y hash de una unidad concreta.
SELECT texto,hash_texto,texto_xml FROM articulos WHERE id_articulo='ce:a14';

-- Revisiones de alcance pendientes.
SELECT id_tema,titulo_oficial_literal FROM temas WHERE estado_fuente!='ok';

-- Versiones candidatas que no han sustituido las activas.
SELECT id_norma,fecha,hash_archivo FROM versiones WHERE estado='candidata';
```

## Límites y despliegue

Consultar `COBERTURA.md`, `NOTAS.md` y `ESTADO_PROYECTO.md`. `npm run build` produce `dist/` con rutas relativas aptas para alojamiento bajo una subruta. No se ha publicado ni desplegado. La instalación PWA y el funcionamiento completo sin conexión están pendientes; guardar progreso local no equivale a disponer de toda la legislación sin conexión.
