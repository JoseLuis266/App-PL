# Fuentes y cuestiones jurídicas pendientes

## Programa adoptado

Se usa el bloque común del **BOIB 34/2026, anexo 4, apartado 1.A**, resolución de la convocatoria unificada de Policía Local. Los 30 títulos proceden de [la publicación oficial](https://www.caib.es/eboibfront/es/2026/12245/712915/resolucion-de-la-consejera-de-presidencia-coordina). `data/programa.json` conserva título, párrafo, HTML, localizador y hash del original.

Se contrastaron las correcciones de 19/03, 28/03 y 14/04/2026: los cambios localizados afectan a convocatorias municipales; no alteran los 30 temas comunes. `data/busqueda-vigente.json` conserva páginas y resultados consultados para localizar convocatorias posteriores. Es la última convocatoria localizada mediante esa búsqueda, no una garantía de ausencia absoluta de otras publicaciones.

El programa oficial de 2022 está archivado en `data/programa2022.json`, con fuente [BOIB 128/2022](https://www.caib.es/eboibfront/es/2022/11632/665117/resolucion-de-la-consejera-de-presidencia-funcion-). Se conserva la comparación literal de ambas ediciones en `data/diferencias-programa.json`. Los 30 números y las normas principales se mantienen; hay diferencias de redacción y terminología. No se han corregido erratas oficiales ni armonizado vocabulario. Las imágenes de academia solo sirvieron de índice inicial, no de fuente de normativa.

El tema 7 del programa oficial incluye competencias municipales y anexo I; no se ha ampliado por memoria. Las referencias al RDL 339/1990 se conservan en los títulos literales del programa y del reglamento, sin tratarlas como una norma actual autónoma del temario.

## Qué se ha comprobado técnicamente

Quince normas BOE: identidad, título oficial, bloques contra índice, selección de versiones publicadas y con entrada en vigor no futura, hashes del archivo bruto y de cada fragmento y ausencia de bloques históricos en las relaciones de estudio. Se contrastaron cinco artículos por norma con el endpoint independiente de bloque del BOE: 75 comparaciones. Los controles de numeración registran lagunas sin fabricar artículos; las rúbricas alfabéticas, bis y ter se conservan.

Los textos normativos se distinguen de notas editoriales. Las tablas y las 732 referencias de imágenes se conservan y descargan con hash. Los preámbulos, disposiciones y anexos tienen tipos distintos a artículo. Todas las unidades siguen pendientes de revisión jurídica; `verificaciones.resultado=superada` describe controles técnicos concretos, nunca una aprobación jurídica global.

La base contiene 3.791 unidades, de las cuales 71 son históricas y 3.720 están disponibles en la proyección del lector. El recuento no representa 3.791 artículos estrictos ni una cobertura jurídica del 100 %. Las relaciones usan unidades compartidas sin duplicar el texto por tema.

## Decreto 40/2019

Se archiva el [original BOIB español](https://www.caib.es/eboibfront/eli/es-ib/d/2019/05/24/40/dof/spa/pdf) completo y el [consolidado informativo CAIB](https://www.caib.es/sites/institutestudisautonomics/f/311092) de 104 páginas, en catalán, actualizado a 13/06/2026. La CAIB advierte del carácter informativo del consolidado. Son documentos separados, no intercambiables.

La extracción identifica 204 artículos contando el artículo único, los artículos 1–201 y dos bis. La separación por tamaño de letra es una heurística pendiente de contraste. Se conservan PDF, texto completo por página, texto candidato y notas para poder revisar cualquier omisión. Se contrastaron cinco artículos con `pdftotext -layout`: 104, 178, 151, 77 y 49 bis. Las cinco comparaciones estrictas registran diferencias de extracción o intercalación de notas. Se localizaron espacios internos de palabras introducidos por la extracción pypdf (por ejemplo, `adeq uats` frente a `adequats`) y marcadores de nota. El resultado no se presenta como superado; se conserva una extracción independiente candidata en `data/marco-extraccion-independiente.txt` y el informe en `data/marco-contraste-independiente.json`. Antes de sustituir fragmentos se deben contrastar las páginas visualmente y separar notas con precisión.

El propio consolidado abrevia con `(...)` los anexos 2(A), 2(B), 4, 5 y 6. Se registra la falta y se conserva el original; no se ha rellenado el consolidado desde una versión antigua.

Se registran las cuatro referencias modificadoras que cita la CAIB: corrección de 26/07/2019, decretos leyes 6/2021 y 6/2022 y Ley 4/2026. La Ley 4/2026 consta en BOE-A-2026-15579: disposición 11/06/2026, publicación BOIB 13/06/2026, entrada en vigor indicada 14/06/2026 y publicación BOE 17/07/2026. La fecha de disposición, publicación, consolidación y entrada en vigor se mantienen separadas. Las referencias del análisis BOE también distinguen normas modificadoras de desarrollo y otras menciones.

## Pendientes de alcance y vigencia

- Tema 1: delimitación de conceptos constitucionales; Constitución completa como referencia provisional.
- Tema 5: selección de instituciones, Poder Judicial y financiación; Estatuto completo como referencia provisional.
- Tema 17: el programa no identifica una norma específica para definiciones, causas y orden cronológico de actuaciones. Las normas de tráfico, policía judicial y seguridad vial son solo apoyo. Falta fuente oficial específica.
- Tema 20: revisión del PDF, lengua, anexos y límites materiales del equipo, armas, uniformidad y presentación.
- Tema 22: delimitar policía judicial y detención. Las relaciones candidatas y la LECrim completa siguen visibles como referencia pendiente.
- Revisión jurídica de vigencia y correspondencia material de los 30 temas. Veinticinco tienen alcance documentado por rúbricas; este estado no los convierte en jurídicamente verificados.

## Estudio y datos personales

El motor distingue la revisión jurídica global de la comprobación granular del literal. Los estados jurídicos de artículos y temas siguen pendientes. Se habilitan únicamente ejercicios sobre pasajes con cita exacta, hash de la unidad activa, relación temática documentada y comparación independiente del bloque BOE palabra por palabra. No se cambian los estados de los 30 temas para abrir el banco.

Tres pilotos: 60 pasajes del tema 2, 60 del tema 7 y 21 del tema 26; 141 en total, con 35 unidades BOE contrastadas. El informe `data/pilotos-estudio-informe.json` conserva URLs, hashes, fechas y criterio. Cada respuesta es un intervalo del texto, cada alternativa procede de otro pasaje contrastado y la explicación muestra la cita. El origen es transformación literal determinista; la tabla `contenido_ia` sigue vacía. Los pasajes retirados se conservan y no se usan.

Los tests piden completar el literal con cuatro alternativas. No equivalen a un banco revisado de casos prácticos de oposición. Las relaciones presentan pasajes y referencias, o definiciones del anexo I y sus conceptos literales. Flashcards y recuperación libre se autoevalúan después de revelar la cita. No se puntúa jurídicamente una redacción libre.

Las sesiones, respuestas y arrastre se guardan de forma atómica, con identificación de ejercicio y fuente. Se puede pausar y continuar tras cerrar la página. Si cambia o se retira una fuente de la sesión se conserva el historial y se bloquea su continuación. La migración IndexedDB de versión 1 a 2 crea el almacén de sesiones sin borrar los de memoria e intentos; las copias antiguas siguen siendo válidas.

La memorización personal sí funciona, con fecha individual y grupos, sin alterar la verificación jurídica. Los intervalos amplían el repaso al recordar, se reinician al fallar y vuelven a un día si cambia el hash del texto. La exportación/importación permite trasladar progreso sin sobrescribir registros existentes. Una modificación jurídica no borra intentos históricos.

La revisión completa de accesibilidad, instalación PWA, sincronización y funcionamiento integral sin conexión quedan pendientes. No se ha realizado publicación, despliegue ni push.
