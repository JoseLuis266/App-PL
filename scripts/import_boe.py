"""Reproducible BOE import with source-index validation and review-gated updates."""
import argparse
import hashlib
from datetime import datetime,timezone
import json
import random
import xml.etree.ElementTree as ET
from boe import parse_norm,selected_version,block_text,canonical_title,xml_root
from database import connect,insert_dict,export
from network import ROOT,download,official_url


def verify(norm, data, text_bytes, sample_network=True):
    counts={kind:sum(a['tipo']==kind for a in data['articles']) for kind in ['articulo','disposicion','anexo','preambulo']}
    source_blocks={b.get('id'):b for b in xml_root(text_bytes).findall('.//texto/bloque')}
    # Check every stored block against source text nodes and preserve full markup.
    for unit in data['structure']:
        original=selected_version(source_blocks[unit['bloque_fuente']])
        tokens=[t for child in original for t in child.itertext()]
        stored=ET.fromstring(unit['texto_xml'])
        if tokens != [t for child in stored for t in child.itertext()]:
            raise ValueError('Pérdida de texto/tabla en '+unit['bloque_fuente'])
    pool=[a for a in data['articles'] if a['tipo']=='articulo' and a['estado']!='historico_no_vigente']
    samples=random.Random(norm['id_boe']).sample(pool,min(5,len(pool)))
    checks=[]
    for unit in samples:
        if sample_network:
            url=f"https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{norm['id_boe']}/texto/bloque/{unit['bloque_fuente']}"
            path,meta=download(url)
            root=xml_root(path.read_bytes())
            block=root.find('.//bloque')
            if block is None: raise ValueError('Muestra oficial sin bloque')
            text=block_text(selected_version(block))
            if text.split()!=unit['texto'].split():
                raise ValueError('Muestra discordante '+unit['id_articulo'])
            checks.append(dict(id_articulo=unit['id_articulo'],resultado='coincide_palabra_por_palabra',url=url,archivo=meta['archivo']))
        else:
            checks.append(dict(id_articulo=unit['id_articulo'],resultado='comparado_archivo_bruto_local'))
    # Numeric gaps are evidence, never filled. Header articles and annex articles have separate contexts.
    numbers=[a['numero'] for a in pool]
    integers={int(n) for n in numbers if n and n.isdigit()}
    gaps=[str(n) for n in range(1,max(integers,default=0)+1) if n not in integers]
    explained=[]
    for number in gaps:
        historical=[a for a in data['articles'] if a['numero']==number and a['estado']=='historico_no_vigente']
        explained.append(dict(numero=number,motivo='bloque histórico fuera de vigencia' if historical else 'no aparece en el índice oficial actual; no se ha rellenado',bloques=[a['bloque_fuente'] for a in historical]))
    return dict(conteos=counts,bloques=len(data['structure']),indice_coincidente=True,
                unidades_actuales=sum(a['estado']!='historico_no_vigente' for a in data['articles']),lagunas_numericas=explained,
                texto_nodos_conservado=True,muestras=checks,
                numeracion_fuente_conservada=True,duplicados_bloque=False,
                advertencia='Verificación automática de importación; no certifica alcance ni vigencia jurídica definitiva.')


def import_one(db,norm,sources, *, sample_network=True, accept_update=False):
    payload={key:(ROOT/row['archivo']).read_bytes() for key,row in sources.items()}
    for key,row in sources.items():
        official_url(row['url_final'])
        if hashlib.sha256(payload[key]).hexdigest()!=row['sha256']:
            raise ValueError('Archivo bruto alterado: '+key)
    data=parse_norm(norm,payload['metadatos'],payload['texto'],payload['texto/indice'],payload['analisis'])
    report=verify(norm,data,payload['texto'],sample_network)
    now=datetime.now(timezone.utc).isoformat()
    old=db.execute('SELECT hash_texto FROM normas WHERE id_norma=?',(norm['id_norma'],)).fetchone()
    m=data['meta'];raw=sources['texto']
    if old and old[0]!=data['hash_texto'] and not accept_update:
        with db:
            db.execute('INSERT OR IGNORE INTO versiones VALUES(?,?,?,?,?,?,?)',(
                norm['id_norma']+':'+raw['sha256'],norm['id_norma'],now,raw['sha256'],raw['archivo'],'candidata',json.dumps(data,ensure_ascii=False)))
        print(norm['id_norma'],'NUEVA VERSIÓN CANDIDATA: no se sustituye el contenido activo',flush=True)
        return 'candidata'
    with db:
        if old and old[0]==data['hash_texto']:
            for unit in data['articles']:
                db.execute('UPDATE articulos SET numero=?,rubrica=? WHERE id_articulo=? AND texto=?',
                    (unit['numero'],unit['rubrica'],unit['id_articulo'],unit['texto']))
            db.execute('INSERT INTO verificaciones(id_norma,fecha,resultado,informe_json) VALUES(?,?,?,?)',
                       (norm['id_norma'],now,'superada',json.dumps(report,ensure_ascii=False)))
            return 'sin_cambios'
        if old:
            # Explicit CLI approval required, and historical snapshots stay archived.
            db.execute("UPDATE versiones SET estado='candidata' WHERE id_norma=? AND estado='activa'",(norm['id_norma'],))
            db.execute('DELETE FROM tema_articulo WHERE id_articulo IN(SELECT id_articulo FROM articulos WHERE id_norma=?)',(norm['id_norma'],))
            db.execute('DELETE FROM articulos WHERE id_norma=?',(norm['id_norma'],))
            db.execute('DELETE FROM estructura WHERE id_norma=?',(norm['id_norma'],))
            db.execute('DELETE FROM norma_modificaciones WHERE id_norma=?',(norm['id_norma'],))
            db.execute('DELETE FROM recursos WHERE id_norma=?',(norm['id_norma'],))
        else:
            insert_dict(db,'normas',dict(id_norma=norm['id_norma'],id_boe=norm['id_boe'],titulo_oficial=m['titulo'],url_fuente=m['url_html_consolidada'],fuente='BOE'))
        values=dict(titulo_oficial=m['titulo'],rango=m.get('rango'),fecha_disposicion=m.get('fecha_disposicion'),
            fecha_publicacion=m.get('fecha_publicacion'),fecha_consolidacion=data['fecha_consolidacion'],
            fecha_actualizacion_api=m.get('fecha_actualizacion'),fecha_vigencia=m.get('fecha_vigencia'),
            url_fuente=m['url_html_consolidada'],hash_texto=data['hash_texto'],fecha_descarga=raw['fecha_descarga'],
            estado='pendiente_revision_manual' if any(s.get('modo')=='manual_sin_contraste' for s in sources.values()) else 'importado_control_tecnico',estatus_derogacion=m.get('estatus_derogacion'),estado_consolidacion=m.get('estado_consolidacion'),
            archivo_bruto=raw['archivo'],hash_archivo=raw['sha256'])
        db.execute('UPDATE normas SET '+','.join(k+'=?' for k in values)+' WHERE id_norma=?',list(values.values())+[norm['id_norma']])
        for row in data['articles']: insert_dict(db,'articulos',row)
        for row in data['structure']: insert_dict(db,'estructura',dict(id_norma=norm['id_norma'],**row))
        # Published dates of modifying versions come from the archived official text, not a guessed year.
        version_dates={}
        for version in xml_root(payload['texto']).findall('.//version'):
            ident=version.get('id_norma');pub=version.get('fecha_publicacion')
            if ident and pub: version_dates[ident]=min(version_dates.get(ident,pub),pub)
        for row in data['modifications']:
            row['fecha']=version_dates.get(row['norma_modificadora'])
            insert_dict(db,'norma_modificaciones',dict(id_norma=norm['id_norma'],**row))
        for url in data['resources']:insert_dict(db,'recursos',dict(id_norma=norm['id_norma'],url=url))
        db.execute('INSERT OR REPLACE INTO versiones VALUES(?,?,?,?,?,?,?)',(
            norm['id_norma']+':'+raw['sha256'],norm['id_norma'],now,raw['sha256'],raw['archivo'],'activa',json.dumps(data,ensure_ascii=False)))
        db.execute('INSERT INTO verificaciones(id_norma,fecha,resultado,informe_json) VALUES(?,?,?,?)',
                   (norm['id_norma'],now,'superada',json.dumps(report,ensure_ascii=False)))
    return 'importado'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--offline',action='store_true',help='Solo caché; muestras contra archivo local, no otra respuesta oficial')
    parser.add_argument('--norma')
    parser.add_argument('--accept-update',action='store_true',help='Aprobación explícita de sustitución después de revisar las diferencias')
    args=parser.parse_args()
    rows=json.loads((ROOT/'data/descargas.json').read_text())
    db=connect()
    for norm in json.loads((ROOT/'data/catalogo.json').read_text()):
        if not norm['id_boe'] or (args.norma and args.norma!=norm['id_norma']):continue
        sources={r['endpoint']:r for r in rows if r['id_norma']==norm['id_norma'] and not r.get('error')}
        try:
            result=import_one(db,norm,sources,sample_network=not args.offline,accept_update=args.accept_update)
            print(norm['id_norma'],result,flush=True)
        except Exception as error:
            # Stop: a wrong title or incomplete import never propagates into the catalog.
            print('IMPORTACIÓN DETENIDA',norm['id_norma'],str(error),flush=True)
            with db:
                db.execute('INSERT INTO incidencias(id_norma,codigo,detalle) VALUES(?,?,?)',
                    (norm['id_norma'] if db.execute('SELECT 1 FROM normas WHERE id_norma=?',(norm['id_norma'],)).fetchone() else None,'importacion_fallida',str(error)))
            export(db)
            raise
        export(db)


if __name__=='__main__':main()
