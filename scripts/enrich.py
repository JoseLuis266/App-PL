"""Rebuild modifier/reference records from raw analysis; enrich dates idempotently."""
import hashlib
import json
import xml.etree.ElementTree as ET
from database import connect,export,insert_dict
from network import ROOT,download

REFERENCE_ONLY={'SE DICTA DE CONFORMIDAD','SE DICTA EN RELACIÓN','Recurso','Cuestión'}

def main():
    db=connect();records=[];results=[];dates={}
    rows=json.loads((ROOT/'data/descargas.json').read_text())
    for norm in json.loads((ROOT/'data/catalogo.json').read_text()):
        if not norm['id_boe']:continue
        files={r['endpoint']:ROOT/r['archivo'] for r in rows if r['id_norma']==norm['id_norma'] and not r.get('error')}
        version_dates={}
        for v in ET.parse(files['texto']).findall('.//version'):
            key=v.get('id_norma');date=v.get('fecha_publicacion')
            if key and date:version_dates[key]=min(version_dates.get(key,date),date)
        for node in ET.parse(files['analisis']).findall('.//posterior'):
            ident=node.findtext('id_norma');relation=node.findtext('relacion','')
            if not ident:continue
            url='https://www.boe.es/diario_boe/xml.php?id='+ident
            if ident not in dates:
                try:
                    cache_key=hashlib.sha256((url+'\napplication/xml').encode()).hexdigest()
                    if (ROOT/'data/cache'/(cache_key+'.json')).exists() or ident not in version_dates:
                        path,meta=download(url);root=ET.parse(path)
                        received=root.findtext('.//identificador')
                        if received and received!=ident:raise ValueError('Identificador discordante')
                        date=root.findtext('.//fecha_publicacion')
                        if not date:raise ValueError('Fecha de publicación ausente')
                        diario=root.findtext('.//diario','BOE')
                        dates[ident]=(date,'publicacion_documento_'+diario)
                        results.append(dict(id=ident,fecha_publicacion=date,**meta))
                    else:dates[ident]=(version_dates[ident],'version_texto_consolidado')
                except Exception as error:
                    dates[ident]=(version_dates.get(ident),'version_texto_consolidado' if version_dates.get(ident) else 'pendiente')
                    results.append(dict(id=ident,url=url,error=str(error)))
            date,origin=dates[ident]
            records.append(dict(id_norma=norm['id_norma'],norma_modificadora=ident,fecha=date,
                fecha_fuente=origin,url='https://www.boe.es/buscar/doc.php?id='+ident,
                relacion=relation,descripcion_literal=node.findtext('texto','')))
    with db:
        # Recreate only BOE-derived records; retain CAIB modifier records.
        for table in ['norma_modificaciones','norma_referencias']:
            db.execute("DELETE FROM "+table+" WHERE id_norma!='marco'")
        for row in records:
            table='norma_referencias' if row['relacion'] in REFERENCE_ONLY else 'norma_modificaciones'
            insert_dict(db,table,row)
    (ROOT/'data/fechas-referencias.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    export(db)
    print('Modificaciones',db.execute('SELECT count(*) FROM norma_modificaciones').fetchone()[0],
          'referencias',db.execute('SELECT count(*) FROM norma_referencias').fetchone()[0],
          'fechas pendientes',db.execute('SELECT count(*) FROM norma_modificaciones WHERE fecha IS NULL').fetchone()[0])

if __name__=='__main__':main()
