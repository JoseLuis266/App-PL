import json
from database import connect,export
from network import ROOT

if __name__=='__main__':
    rows=json.loads((ROOT/'data/recursos_descargados.json').read_text())
    db=connect()
    with db:
        for r in rows:
            db.execute('UPDATE recursos SET archivo=?,sha256=?,estado=? WHERE id_norma=? AND url=?',
                       (r.get('archivo'),r.get('sha256'),r['estado'],r['id_norma'],r['url']))
    export(db)
    print('Recursos incorporados:',len(rows))
