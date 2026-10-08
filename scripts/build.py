"""One norma at a time, with verification before moving to the next."""
import json
from boe import canonical_title,xml_root
from database import connect,export
from import_boe import import_one
from network import ROOT,download
from programa import main as import_program
from import_boib import main as import_boib
from relations import main as relations

if __name__=='__main__':
    import_program();db=connect();downloads=[];assets=[]
    for norm in json.loads((ROOT/'data/catalogo.json').read_text()):
        if not norm['id_boe']:
            import_boib();continue
        sources={}
        for endpoint in ['metadatos','texto','texto/indice','analisis']:
            path,meta=download(f"https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{norm['id_boe']}/{endpoint}")
            if endpoint=='metadatos':
                root=xml_root(path.read_bytes())
                if root.findtext('.//identificador')!=norm['id_boe'] or canonical_title(root.findtext('.//titulo',''))!=canonical_title(norm['titulo_esperado']):
                    raise ValueError('Identidad discordante '+norm['id_norma'])
            sources[endpoint]=meta;downloads.append(dict(id_norma=norm['id_norma'],endpoint=endpoint,**meta))
        print(norm['id_norma'],import_one(db,norm,sources),flush=True)
        assets.extend(dict(id_norma=norm['id_norma'],url=r['url']) for r in db.execute('SELECT url FROM recursos WHERE id_norma=?',(norm['id_norma'],)))
        export(db)
    (ROOT/'data/descargas.json').write_text(json.dumps(downloads,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/recursos_pendientes.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2)+'\n')
    relations()
