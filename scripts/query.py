import argparse
from database import connect

if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--tema',type=int);group.add_argument('--buscar')
    args=parser.parse_args();db=connect()
    if args.tema:
        row=db.execute('SELECT * FROM temas WHERE id_tema=?',(args.tema,)).fetchone()
        if row is None:parser.error('Tema inexistente')
        print(row['titulo_oficial_literal']);print('Estado:',row['estado_fuente'],row['estado_verificacion'])
        rows=db.execute('SELECT DISTINCT a.id_articulo,a.rubrica,a.url_fuente FROM tema_articulo ta JOIN articulos a USING(id_articulo) WHERE ta.id_tema=? ORDER BY a.id_norma,a.orden',(args.tema,))
    else:
        rows=db.execute("SELECT a.id_articulo,a.rubrica,a.url_fuente FROM articulos_fts f JOIN articulos a ON a.rowid=f.rowid WHERE articulos_fts MATCH ? AND a.estado!='historico_no_vigente' ORDER BY rank LIMIT 25",(args.buscar,))
    for r in rows:print(r['id_articulo'],r['rubrica'],r['url_fuente'])
