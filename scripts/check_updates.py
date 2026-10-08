"""Fetch candidate snapshots; never replace the active database implicitly."""
import json
from datetime import datetime,timezone
from boe import parse_norm
from database import connect,insert_dict
from network import ROOT,download

if __name__=='__main__':
    db=connect();report=[]
    for norm in json.loads((ROOT/'data/catalogo.json').read_text()):
        if not norm['id_boe']:
            existing=db.execute("SELECT hash_archivo FROM normas WHERE id_norma='marco'").fetchone()
            path,meta=download('https://www.caib.es/sites/institutestudisautonomics/f/311092',accept='application/pdf',refresh=True)
            report.append(dict(id_norma='marco',cambio=bool(existing and existing[0]!=meta['sha256']),temas_afectados=[20],accion='Revisar PDF y extracción antes de sustituir',fuente=meta))
            continue
        sources={}
        for endpoint in ['metadatos','texto','texto/indice','analisis']:
            path,meta=download(f"https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{norm['id_boe']}/{endpoint}",refresh=True)
            sources[endpoint]=meta
        payload={e:(ROOT/m['archivo']).read_bytes() for e,m in sources.items()}
        data=parse_norm(norm,payload['metadatos'],payload['texto'],payload['texto/indice'],payload['analisis'])
        previous={r['id_articulo']:dict(r) for r in db.execute('SELECT * FROM articulos WHERE id_norma=?',(norm['id_norma'],))}
        current={r['id_articulo']:r for r in data['articles']}
        added=sorted(current.keys()-previous.keys());removed=sorted(previous.keys()-current.keys())
        changed=sorted(k for k in current.keys()&previous.keys() if current[k]['hash_texto']!=previous[k]['hash_texto'] or current[k]['estado']!=previous[k]['estado'])
        affected=[r[0] for r in db.execute('SELECT DISTINCT id_tema FROM tema_norma WHERE id_norma=? ORDER BY id_tema',(norm['id_norma'],))]
        different=bool(added or removed or changed)
        if different:
            raw=sources['texto']
            with db:
                db.execute('INSERT OR IGNORE INTO versiones VALUES(?,?,?,?,?,?,?)',(
                    norm['id_norma']+':'+raw['sha256'],norm['id_norma'],datetime.now(timezone.utc).isoformat(),raw['sha256'],raw['archivo'],'candidata',json.dumps(data,ensure_ascii=False)))
        report.append(dict(id_norma=norm['id_norma'],cambio=different,anadidos=added,eliminados=removed,modificados=changed,temas_afectados=affected if different else [],accion='Revisión requerida; contenido activo conservado' if different else 'Sin cambios de texto detectados'))
        (ROOT/'data/actualizaciones.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(norm['id_norma'],'cambio' if different else 'sin cambios',flush=True)
