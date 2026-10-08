"""Generate coverage from SQLite facts, avoiding a misleading completeness percentage."""
from datetime import datetime,timezone
import json
from database import connect,export
from network import ROOT


def main():
    db=connect()
    topics=list(db.execute('SELECT * FROM temas ORDER BY id_tema'))
    assert [t['id_tema'] for t in topics]==list(range(1,31))
    assert not list(db.execute('PRAGMA foreign_key_check'))
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    lines=['# Cobertura del bloque común','',f"Informe generado: {datetime.now(timezone.utc).isoformat()}",'',
           'Programa: BOIB 34/2026, anexo 4, apartado 1.A. Los estados `ok` de fuente/rango indican una relación documentada con texto importado; no equivalen a un tema jurídicamente verificado. Todos los temas conservan revisión jurídica pendiente.',
           '', '| Tema | Normas principales / apoyo | Unidades enlazadas distintas | Artículos estrictos | Estado fuente/rango | Verificación |',
           '|---|---|---:|---:|---|---|']
    for t in topics:
        n=t['id_tema']
        norms=[r[0]+(' (apoyo)' if r[1]=='apoyo' else '') for r in db.execute('SELECT DISTINCT id_norma,papel FROM tema_norma WHERE id_tema=? ORDER BY id_norma,papel',(n,))]
        count=db.execute('SELECT count(DISTINCT id_articulo) FROM tema_articulo WHERE id_tema=?',(n,)).fetchone()[0]
        articles=db.execute("SELECT count(DISTINCT a.id_articulo) FROM tema_articulo ta JOIN articulos a USING(id_articulo) WHERE ta.id_tema=? AND a.tipo='articulo'",(n,)).fetchone()[0]
        lines.append(f"| {n} | {', '.join(norms)} | {count} | {articles} | {t['estado_fuente']} | {t['estado_verificacion']} |")
    lines+=['','Los recuentos incluyen preámbulos, disposiciones y anexos cuando están vinculados; la columna de artículos estrictos los distingue. Los rangos pendientes pueden enlazar una norma completa como referencia. Los artículos compartidos no se duplican en la tabla `articulos`.','',
            'Temas creados: 30. Temas con texto principal importado: 29; el tema 17 contiene solo apoyo normativo. Temas con alcance delimitado mediante correspondencia de rúbricas: 25. Temas con rango pendiente: 1, 5, 20 y 22. Temas totalmente verificados jurídicamente: 0.',
            '', '## Pendientes', '',
            '- Tema 1: conceptos constitucionales y delimitación de artículos; norma completa como referencia pendiente.',
            '- Tema 5: confirmar selección exacta de instituciones y Poder Judicial; Estatuto completo como referencia pendiente.',
            '- Tema 17: no hay norma específica en el programa. Falta fuente EBAP para definiciones, tipos, causas y secuencia de actuaciones.',
            '- Tema 20: consolidación CAIB en catalán; revisión de extracción PDF, límites materiales y anexos. El propio consolidado abrevia los anexos 2(A), 2(B), 4, 5 y 6 con (...). Se conserva el original completo separado, sin rellenar el consolidado.',
            '- Tema 22: precisar policía judicial y detención; relaciones candidatas y LECrim completa como referencia pendiente.',
            '- Revisión jurídica de vigencia y alcance de todos los temas. Los consolidados tienen valor informativo y los controles automáticos no sustituyen esta revisión.','', '## Resumen por tema','']
    for t in topics:lines.append(f"- Tema {t['id_tema']}: {t['estado_fuente']}; {t['titulo_oficial_literal']}")
    (ROOT/'COBERTURA.md').write_text('\n'.join(lines)+'\n')
    gaps=[]
    for row in db.execute("SELECT id_norma,informe_json FROM verificaciones WHERE resultado='superada' ORDER BY id"):
        data=json.loads(row['informe_json'])
        if data.get('lagunas_numericas'):gaps.append(dict(id_norma=row['id_norma'],lagunas=data['lagunas_numericas']))
    (ROOT/'data/lagunas-numeracion.json').write_text(json.dumps(gaps,ensure_ascii=False,indent=2)+'\n')
    for table in ['temas','normas','articulos','tema_norma','tema_articulo']:
        print(table,db.execute('SELECT count(*) FROM '+table).fetchone()[0])
    print('SQLite: integridad y claves foráneas correctas')
    export(db)


if __name__=='__main__':main()
