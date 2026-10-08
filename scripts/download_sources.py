"""Download evidence only. Errors never become legal content."""
import argparse
import json
from boe import canonical_title,xml_root
from pathlib import Path
from network import ROOT, download


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    catalog = json.loads((ROOT / 'data/catalogo.json').read_text())
    result = []
    for norm in catalog:
        if not norm.get('id_boe'):
            continue
        for endpoint in ['metadatos', 'texto', 'texto/indice', 'analisis']:
            url = f"https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{norm['id_boe']}/{endpoint}"
            try:
                path, meta = download(url, refresh=args.refresh)
                if endpoint=='metadatos':
                    root=xml_root(path.read_bytes())
                    title=root.findtext('.//titulo','')
                    if canonical_title(title)!=canonical_title(norm['titulo_esperado']) or root.findtext('.//identificador')!=norm['id_boe']:
                        raise ValueError('Identidad o título discordantes: '+title)
                result.append(dict(id_norma=norm['id_norma'], endpoint=endpoint, **meta))
                print(norm['id_norma'], endpoint, path.stat().st_size, flush=True)
            except Exception as error:
                result.append(dict(id_norma=norm['id_norma'], endpoint=endpoint, url=url, error=str(error)))
                print(norm['id_norma'], endpoint, 'ERROR', str(error), flush=True)
                if endpoint=='metadatos':
                    (ROOT/'data/descargas.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
                    raise
            (ROOT / 'data/descargas.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
