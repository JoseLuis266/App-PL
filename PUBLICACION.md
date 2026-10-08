# Publicación de PL Study

Publicación autorizada por el usuario el 08/10/2026. El usuario confirmó que pudo abrir la primera versión.

- `main`: código, base jurídica, originales y pruebas. Primera incorporación: `f86e7984a00329521c399cb06fca2a9e93d4dd77`.
- `gh-pages`: compilación para Pages. Actualización de estudio: `381066148c9bcf2bada2a9718d3fdfddfa29fa5b`.
- URL: `https://joseluis266.github.io/App-PL/`.

La actualización contiene 141 pasajes de los temas 2, 7 y 26 contrastados con 35 unidades BOE, cinco métodos y sesiones persistentes. Los estados jurídicos globales siguen pendientes y el contenido de IA sigue vacío. No se suben credenciales ni datos personales del navegador.

## Comprobación

Se confirmaron ambos commits mediante `git ls-remote`. Se recuperó por HTTPS el manifiesto de la rama publicada y se comprobaron los 141 pasajes. La compilación bajo `/App-PL/` fue probada en Chromium móvil: inicio de un test penal, corrección con cita, resumen y ausencia de errores JavaScript o desbordamiento.

La API de GitHub y el dominio de Pages siguen bloqueados por el proxy de esta sesión. No se ha observado directamente la finalización del último despliegue público; confirmar la rama no equivale a confirmar ese despliegue. Pages usa la rama `gh-pages` configurada por el usuario. Se conservan assets anteriores para que las páginas en caché sigan cargando durante la actualización.

## Actualizar

Ejecutar pruebas y `npm run build`; copiar `dist/` sobre el directorio de publicación conservando `.nojekyll` y una página 404. Crear un commit de `gh-pages` y subir sin `--force`. Guardar código y documentación en `main`. No modificar la rama de origen de Pages ni borrar historial por rutina.

Directorio de publicación usado: `/tmp/pl-study-pages-9oopjss4`. Si falta en otra sesión, clonar `gh-pages` como directorio temporal de publicación conservando siempre el checkout de desarrollo.
