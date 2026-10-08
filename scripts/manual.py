"""Register a manually downloaded official API bundle, always pending source review."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from database import connect,export
from import_boe import import_one
from network import ROOT,official_url

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--norma',required=True)
    parser.add_argument('--metadatos',type=Path,required=True)
    parser.add_argument('--texto',type=Path,required=True)
    parser.add_argument('--indice',type=Path,required=True)
    parser.add_argument('--analisis',type=Path,required=True)
    args=parser.parse_args()
    norm=next(n for n in json.loads((ROOT/'data/catalogo.json').read_text()) if n['id_norma']==args.norma)
    if not norm['id_boe']:parser.error('Para BOIB conservar el PDF y la URL de procedencia; la extracción requiere revisión específica con import_boib.py.')
    sources={}
    for endpoint,file in [('metadatos',args.metadatos),('texto',args.texto),('texto/indice',args.indice),('analisis',args.analisis)]:
        content=file.read_bytes();sha=hashlib.sha256(content).hexdigest()
        path=ROOT/'data/raw'/(sha+'.xml');path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():path.write_bytes(content)
        url=official_url(f"https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{norm['id_boe']}/{endpoint}")
        sources[endpoint]=dict(archivo=str(path.relative_to(ROOT)),sha256=sha,url_solicitada=url,url_final=url,
            fecha_descarga=datetime.now(timezone.utc).isoformat(),modo='manual_sin_contraste',
            aviso='URL declarada; autenticidad y fecha original de descarga pendientes de contraste')
    (ROOT/'data'/('manual-'+norm['id_norma']+'.json')).write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
    db=connect();print(import_one(db,norm,sources,sample_network=False));export(db)
