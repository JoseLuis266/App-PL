"""Import the official common syllabus, retaining source HTML and exact wording."""
import json
import re
from bs4 import BeautifulSoup
from database import connect,export
from network import ROOT,download

SOURCE='https://www.caib.es/eboibfront/es/2026/12245/712915/resolucion-de-la-consejera-de-presidencia-coordina'


def extract(html):
    soup=BeautifulSoup(html,'html.parser')
    body=soup.select_one('#contenidoEdicto')
    if body is None:raise ValueError('Programa sin cuerpo de edicto')
    paragraphs=body.find_all('p')
    start=next((i for i,p in enumerate(paragraphs) if p.get_text().lstrip().startswith('1. La Constitución española')),None)
    if start is None:raise ValueError('No se encuentra el inicio del bloque común')
    result=[]
    for p in paragraphs[start:]:
        text=p.get_text()
        match=re.match(r'^\s*(\d+)\.\s+',text)
        if not match:break
        n=int(match.group(1))
        result.append(dict(id_tema=n,titulo_oficial_literal=text[match.end():].rstrip(),
                           parrafo_literal=text,html_fuente=str(p),localizador=f'#contenidoEdicto p[{paragraphs.index(p)+1}]'))
    if [r['id_tema'] for r in result]!=list(range(1,31)):
        raise ValueError('El bloque oficial no contiene exactamente los temas 1–30 en orden')
    return result


def main():
    path,meta=download(SOURCE,accept='text/html')
    rows=extract(path.read_bytes())
    document=dict(programa_version='BOIB-34-2026-anexo4-1A',fuente=meta,temas=rows,
                  correcciones=['BOIB 35/2026: incorporación de Santanyí, bloque municipal',
                                'BOIB 40/2026: ordenanzas del bloque municipal',
                                'BOIB 48/2026: ordenanzas de Palma del bloque municipal'])
    (ROOT/'data/programa.json').write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n')
    db=connect()
    with db:
        for r in rows:
            old=db.execute('SELECT titulo_oficial_literal,programa_version FROM temas WHERE id_tema=?',(r['id_tema'],)).fetchone()
            if old and (old[0]!=r['titulo_oficial_literal'] or old[1]!=document['programa_version']):
                raise ValueError('Programa cambiado: revisar diferencias antes de sustituir los temas')
            db.execute('INSERT OR IGNORE INTO temas(id_tema,titulo_oficial_literal,estado_fuente,programa_version,url_programa,localizador) VALUES(?,?,?,?,?,?)',
                       (r['id_tema'],r['titulo_oficial_literal'],'sin_norma_especifica' if r['id_tema']==17 else 'rango_pendiente',document['programa_version'],SOURCE,r['localizador']))
    export(db)
    print('Programa oficial 2026: 30 temas importados; sin correcciones didácticas.')


if __name__=='__main__':main()
