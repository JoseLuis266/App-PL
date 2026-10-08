"""CAIB consolidated PDF import. PDF extraction remains explicitly pending review."""
from datetime import datetime,timezone
import hashlib
import html
import json
import re
from pypdf import PdfReader
from bs4 import BeautifulSoup
from database import connect,insert_dict,export
from boe import digest
from network import ROOT,download

CONSOLIDATED='https://www.caib.es/sites/institutestudisautonomics/f/311092'
ORIGINAL='https://www.caib.es/eboibfront/eli/es-ib/d/2019/05/24/40/dof/spa/pdf'
PAGE='https://www.caib.es/sites/institutestudisautonomics/ca/n/decret_402019_de_24_de_maig_pel_qual_saprova_el_reglament_marc_de_coordinacio_de_les_policies_locals_de_les_illes_balears_i_es_modifica_el_decret_552017_de_15_de_desembre_del_fons_de_seguretat_publica'

def import_modifiers(db):
    page,meta=download(PAGE,accept='text/html')
    soup=BeautifulSoup(page.read_bytes(),'html.parser')
    paragraphs=[e.get_text(' ',strip=True) for e in soup.find_all(['p','li'])]
    wanted=[('26 de juliol de 2019','CAIB-correccio-2019','20190727','https://www.caib.es/eboibfront/pdf/ca/2019/103/1039774'),
            ('Decret llei 6/2021','CAIB-DL-6-2021','20210710','https://www.caib.es/eboibfront/pdf/ca/2021/92/1092792'),
            ('Decret llei 6/2022','CAIB-DL-6-2022','20220616','https://www.caib.es/eboibfront/pdf/ca/2022/78/1113675'),
            ('Llei 4/2026','BOE-A-2026-15579','20260613','https://www.boe.es/buscar/doc.php?id=BOE-A-2026-15579')]
    records=[]
    for needle,ident,date,url in wanted:
        matches=[p for p in paragraphs if needle in p]
        if len(matches)!=1:raise ValueError('Referencia CAIB no inequívoca: '+needle)
        records.append(dict(id_norma='marco',norma_modificadora=ident,fecha=date,url=url,relacion='referencia_modificadora_CAIB',descripcion_literal=matches[0],fecha_fuente='publicacion_BOIB_indicada_por_CAIB'))
    with db:
        db.execute("DELETE FROM norma_modificaciones WHERE id_norma='marco' AND relacion='referencia_modificadora_CAIB'")
        for row in records:insert_dict(db,'norma_modificaciones',row)


def extract_pdf(path):
    reader=PdfReader(path)
    pages=[]
    for i,page in enumerate(reader.pages):
        body,notes=[],[]
        def visit(text,cm,tm,font,size):
            (body if size>=11.9 else notes).append(text)
        full=page.extract_text(visitor_text=visit)
        pages.append(dict(pagina=i+1,texto=''.join(body),notas=''.join(notes),texto_completo_extraido=full))
    text='\n'.join(p['texto'] for p in pages)
    headings=list(re.finditer(r'(?m)^[ \t]*(Article\s+(?:\d+(?:\s+(?:bis|ter))?|únic)|Disposició\s+[^\n.]+|ANNEX\s+\d+(?:\s*\([AB]\))?|TÍTOL\s+[IVX]+|Capítol\s+[IVX]+|Secció\s+\d+)[^\n]*',text))
    if not headings or 'DECRET 40/2019' not in text[:1000]:raise ValueError('Identidad/formato del PDF CAIB no reconocidos')
    numbers=re.findall(r'(?m)^[ \t]*Article\s+(\d+(?:\s+(?:bis|ter))?|únic)',text)
    if len(numbers)!=len(set(numbers)) or any(str(n) not in numbers for n in range(1,202)):
        raise ValueError('Artículos del Reglamento incompletos o duplicados')
    # All page text and the PDF itself remain archived, including low-font fragments.
    entries=[];hierarchy={};starts=[];offset=0
    for page in pages:
        starts.append((offset,page['pagina']));offset+=len(page['texto'])+1
    boundaries=[(0,None)]+[(m.start(),m) for m in headings]+[(len(text),None)]
    for order,((start,match),(end,_)) in enumerate(zip(boundaries,boundaries[1:])):
        chunk=text[start:end]
        if not chunk.strip():continue
        title=match.group(0).strip() if match else 'PREÀMBUL'
        tipo='articulo' if title.startswith('Article') else 'disposicion' if title.startswith('Disposició') else 'anexo' if title.startswith('ANNEX') else 'preambulo' if match is None else None
        if tipo is None:
            level=title.split()[0]
            rank={'TÍTOL':1,'Capítol':2,'Secció':3}.get(level,0)
            for key in list(hierarchy):
                if {'TÍTOL':1,'Capítol':2,'Secció':3}.get(key,0)>=rank:hierarchy.pop(key)
            hierarchy[level]=chunk
        page=next(pg for pos,pg in reversed(starts) if pos<=start)
        id_block=f'pdf-segmento-{order}'
        number=re.match(r'Article\s+(\d+(?:\s+(?:bis|ter))?|únic)',title)
        entries.append(dict(bloque_fuente=id_block,orden=order,tipo=tipo,numero=number.group(1) if number else title,
            rubrica=title,texto=chunk,jerarquia=json.dumps(hierarchy,ensure_ascii=False),
            texto_xml='<fragmento fuente="PDF" pagina="'+str(page)+'">'+html.escape(chunk)+'</fragmento>',
            url_fuente=CONSOLIDATED+'#page='+str(page),hash_texto=digest(chunk)))
    return pages,entries


def main():
    path,meta=download(CONSOLIDATED,accept='application/pdf')
    original,original_meta=download(ORIGINAL,accept='application/pdf')
    pages,entries=extract_pdf(path)
    (ROOT/'data/marco-paginas.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/marco-consolidado-fuente.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/marco-original-fuente.json').write_text(json.dumps(original_meta,ensure_ascii=False,indent=2)+'\n')
    # The publisher itself omits some annexes with (...). These are never filled from memory.
    missing=[e['rubrica'] for e in entries if e['tipo']=='anexo' and '(...)' in e['texto']]
    title='\n'.join(pages[0]['texto'].split('PREÀMBUL')[0].strip().splitlines())
    first=pages[0]['texto_completo_extraido']
    date=re.search(r'actualitzada a (\d{2})/(\d{2})/(\d{4})',first)
    if not date:raise ValueError('Fecha de consolidación no encontrada')
    consolidation=date.group(3)+date.group(2)+date.group(1)
    db=connect();old=db.execute("SELECT hash_archivo FROM normas WHERE id_norma='marco'").fetchone()
    if old and old[0]!=meta['sha256']:raise ValueError('Nueva versión PDF; revisión requerida antes de sustitución')
    if not old:
        with db:
            insert_dict(db,'normas',dict(id_norma='marco',id_boe=None,titulo_oficial=title,rango='Decret',
                fecha_disposicion='20190524',fecha_publicacion='20190525',fecha_consolidacion=consolidation,
                url_fuente=CONSOLIDATED,fuente='BOIB',hash_texto=digest(json.dumps(entries,ensure_ascii=False)),
                fecha_descarga=meta['fecha_descarga'],estado='pendiente_revision_pdf',estado_consolidacion='Consolidación informativa CAIB, sin validez jurídica',
                archivo_bruto=meta['archivo'],hash_archivo=meta['sha256']))
            for e in entries:
                if e['tipo']:
                    insert_dict(db,'articulos',dict(id_articulo='marco:'+e['bloque_fuente'],id_norma='marco',**e,
                        estado='pendiente_revision_pdf',notas_fuente='[]'))
                insert_dict(db,'estructura',dict(id_norma='marco',bloque_fuente=e['bloque_fuente'],orden=e['orden'],
                    tipo_fuente='encabezado' if not e['tipo'] else e['tipo'],titulo=e['rubrica'],texto_xml=e['texto_xml'],
                    texto=e['texto'],jerarquia=e['jerarquia']))
            insert_dict(db,'versiones',dict(id_version='marco:'+meta['sha256'],id_norma='marco',
                fecha=datetime.now(timezone.utc).isoformat(),hash_archivo=meta['sha256'],archivo_bruto=meta['archivo'],estado='activa',datos_json=json.dumps(entries,ensure_ascii=False)))
            db.execute('INSERT INTO incidencias(id_norma,codigo,detalle) VALUES(?,?,?)',('marco','pdf_revision','Texto en catalán. Separación por tamaño de letra pendiente de contraste: conservar PDF, páginas completas y notas. Anexos abreviados en la fuente: '+', '.join(missing)))
            db.execute('INSERT INTO verificaciones(id_norma,fecha,resultado,informe_json) VALUES(?,?,?,?)',(
                'marco',datetime.now(timezone.utc).isoformat(),'pendiente',json.dumps(dict(articulos=204,lagunas_1_201=False,duplicados=False,
                    anexos_incompletos_fuente=missing,comparacion_5_articulos='pendiente_revision',idioma='ca'),ensure_ascii=False)))
    import_modifiers(db)
    export(db)
    print('Decreto 40/2019: PDF consolidado importado, 204 artículos; revisión PDF pendiente. Anexos abreviados:',missing)


if __name__=='__main__':main()
