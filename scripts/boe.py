"""Parse BOE consolidated XML; preserve all blocks and raw inline/table markup."""
from datetime import date
import hashlib
import json
import re
import xml.etree.ElementTree as ET


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def canonical_title(text):
    # Presentation-only differences; words must still match, accents included.
    return re.sub(r'[«»“”".]', '', ' '.join(text.split())).casefold()


def xml_root(data):
    root = ET.fromstring(data)
    for node in root.iter():
        node.tag = node.tag.split('}')[-1]
    code = root.findtext('./status/code')
    if code and code != '200':
        raise ValueError('La API devuelve estado ' + code)
    return root


def selected_version(block, today=None):
    today = (today or date.today()).strftime('%Y%m%d')
    versions = block.findall('version')
    valid = [v for v in versions if v.get('fecha_publicacion', '') <= today
             and v.get('fecha_vigencia', v.get('fecha_publicacion', '')) <= today]
    if not valid:
        raise ValueError('Bloque sin versión vigente seleccionable: ' + str(block.get('id')))
    return max(valid, key=lambda v: (v.get('fecha_vigencia', v.get('fecha_publicacion', '')),
                                    v.get('fecha_publicacion', '')))


def block_text(version):
    # Only layout separators added; every text node inside source elements is retained.
    return '\n'.join(''.join(child.itertext()) for child in version
                     if child.tag != 'blockquote' and 'nota' not in child.get('class',''))


def update_hierarchy(hierarchy, title, version):
    texts = [title] + [''.join(n.itertext()) for n in version]
    for text in texts:
        match = re.match(r'\s*(LIBRO|T[IÍ]TULO|CAP[IÍ]TULO|SECCI[OÓ]N|SUBSECCI[OÓ]N)\b', text, re.I)
        if match:
            key = match.group(1).upper().replace('Í','I').replace('Ó','O')
            levels = ['LIBRO','TITULO','CAPITULO','SECCION','SUBSECCION']
            position = levels.index(key)
            for lower in levels[position+1:]:
                hierarchy.pop(lower, None)
            hierarchy[key] = block_text(version)
            break


def classify(block):
    title = block.get('titulo', '')
    tipo = block.get('tipo', '')
    if tipo == 'preambulo': return 'preambulo', None
    article = re.match(r'Art[ií]culo\s+(.+?)(?:[.\s]|$)', title, re.I)
    if article:
        full = re.match(r'Art[ií]culo\s+(\d+(?:\s+(?:bis|ter|quater|quinquies|sexies|septies|octies|nonies|decies))?|[uú]nico)',title,re.I)
        return 'articulo', full.group(1) if full else re.sub(r'^Art[ií]culo\s+','',title,flags=re.I).split('.')[0].strip()
    if re.match(r'ANEXO\b',title,re.I): return 'anexo', title.split('.')[0]
    if re.match(r'Disposici[oó]n\b',title,re.I): return 'disposicion', title.split('.')[0]
    return None, None


def parse_norm(norm, metadata_bytes, text_bytes, index_bytes, analysis_bytes):
    meta_root = xml_root(metadata_bytes)
    meta = meta_root.find('.//metadatos')
    if meta is None: raise ValueError('Metadatos inexistentes')
    title = meta.findtext('titulo', '')
    if meta.findtext('identificador') != norm['id_boe']:
        raise ValueError('Identificador BOE discordante')
    if canonical_title(title) != canonical_title(norm['titulo_esperado']):
        raise ValueError(f"Título discordante: esperado {norm['titulo_esperado']!r}; recibido {title!r}")
    root = xml_root(text_bytes)
    blocks = root.findall('.//texto/bloque')
    index = xml_root(index_bytes)
    entries = index.findall('./data/bloque')
    expected = [b.findtext('id') for b in entries]
    actual = [b.get('id') for b in blocks]
    if not actual or actual != expected or len(actual) != len(set(actual)):
        raise ValueError('Índice/texto: bloques vacíos, duplicados, fuera de orden u omitidos')
    structure, articles, resources = [], [], set()
    hierarchy = {}
    annex = None
    for order, block in enumerate(blocks):
        version = selected_version(block)
        title_block = block.get('titulo', '')
        active = not (block.get('fecha_caducidad') and block.get('fecha_caducidad') <= date.today().strftime('%Y%m%d'))
        if active and re.match(r'ANEXO\b',title_block,re.I):
            annex = title_block
            hierarchy = {'ANEXO':block_text(version).split('\n')[0]}
        if active and block.get('tipo') == 'encabezado':
            update_hierarchy(hierarchy, title_block, version)
        texto = block_text(version)
        markup = ET.tostring(version,encoding='unicode')
        structure.append(dict(bloque_fuente=block.get('id'),orden=order,tipo_fuente=block.get('tipo'),
                              titulo=title_block,texto_xml=markup,texto=texto,jerarquia=json.dumps(hierarchy,ensure_ascii=False),activo=int(active)))
        tipo, numero = classify(block)
        if tipo is None and annex and block.get('tipo') == 'encabezado' and texto.strip() and block.get('id') != 'ir' and not re.match(r'ANEXO\b',title_block,re.I):
            # Annex subsections are separate source blocks, not discardable headings.
            tipo,numero='anexo',title_block
        if tipo:
            if not texto.strip(): raise ValueError('Unidad vacía: ' + block.get('id'))
            articles.append(dict(id_articulo=norm['id_norma']+':'+block.get('id'),id_norma=norm['id_norma'],
                bloque_fuente=block.get('id'),orden=order,tipo=tipo,numero=numero,
                rubrica=next((''.join(p.itertext()) for p in version if p.get('class')=='articulo'),title_block),
                texto=texto,jerarquia=json.dumps(hierarchy,ensure_ascii=False),
                url_fuente=f"https://www.boe.es/buscar/act.php?id={norm['id_boe']}#{block.get('id')}",
                hash_texto=digest(texto),texto_xml=markup,
                fecha_publicacion_version=version.get('fecha_publicacion'),fecha_vigencia_version=version.get('fecha_vigencia'),
                norma_version=version.get('id_norma'),estado='pendiente_revision' if active else 'historico_no_vigente',
                notas_fuente=json.dumps([''.join(c.itertext()) for c in version if c.tag=='blockquote' or 'nota' in c.get('class','')],ensure_ascii=False)))
        for image in version.findall('.//img'):
            if image.get('src'):
                from urllib.parse import urljoin
                resources.add(urljoin('https://www.boe.es/',image.get('src')))
    modifications = []
    for posterior in xml_root(analysis_bytes).findall('.//posteriores/posterior'):
        ident = posterior.findtext('id_norma')
        relation = posterior.findtext('relacion','')
        if ident:
            modifications.append(dict(norma_modificadora=ident,fecha=None,
                url='https://www.boe.es/buscar/doc.php?id='+ident,relacion=relation,
                descripcion_literal=posterior.findtext('texto','')))
    consolidations=[a['fecha_publicacion_version'] for a in articles if a['fecha_publicacion_version']]
    return dict(meta={n.tag: ''.join(n.itertext()) for n in meta},structure=structure,articles=articles,
                modifications=modifications,resources=sorted(resources),
                fecha_consolidacion=max(consolidations) if consolidations else None,
                hash_texto=digest(json.dumps(structure,ensure_ascii=False,sort_keys=True)))
