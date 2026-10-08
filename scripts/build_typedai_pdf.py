#!/usr/bin/env python3
import json, re, html, os
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'typedai_output'; OUT.mkdir(exist_ok=True)
def load_json(name):
    with open(ROOT/'export'/name, encoding='utf-8') as f: return json.load(f)
def clean(s):
    if s is None: return ''
    s=html.unescape(str(s)); s=re.sub(r'<br\s*/?>','\n',s,flags=re.I); s=re.sub(r'</p\s*>','\n',s,flags=re.I); s=re.sub(r'<[^>]+>','',s); s=s.replace('\u00a0',' '); s=re.sub(r'[ \t]+',' ',s); s=re.sub(r'\n{3,}','\n\n',s); return s.strip()
def aid(n,nr): return f'{n}:a{nr}'
def rng(n,a,b): return [aid(n,x) for x in range(a,b+1)]
temas=load_json('temas.json'); rel=load_json('tema_articulo.json'); arts=load_json('articulos.json'); normas=load_json('normas.json')
by_id={a['id_articulo']:a for a in arts}; by_norm={n['id_norma']:n for n in normas}; relations={}
for r in rel: relations.setdefault(int(r['id_tema']),[]).append(r['id_articulo'])
overrides={
1:rng('ce',1,9),
5:rng('estatuto',1,12)+rng('estatuto',30,38)+rng('estatuto',39,75)+rng('estatuto',93,95)+rng('estatuto',120,126),
20:rng('marco',48,126),
22:[aid('ce',17),aid('fcs',29),aid('fcs',53)]+rng('lecrim',282,298)+rng('lecrim',489,501)+[aid('lecrim',520),'lecrim:a520bis','lecrim:a520ter']+rng('lecrim',521,527)+[x for x in by_id if x.startswith('habeas:')]
}
T1='APOYO DE ESTRUCTURA (síntesis, no texto literal): la Constitución Española de 1978 se organiza en Preámbulo, Título Preliminar, diez títulos numerados (I-X), disposiciones adicionales, transitorias, derogatoria y final. Para este tema, el núcleo normativo de principios constitucionales básicos es el Título Preliminar (arts. 1-9). La supremacía normativa se refleja, entre otros puntos, en la sujeción de ciudadanos y poderes públicos a la Constitución y al resto del ordenamiento.'
T17='''TEMA 17 - APOYO CONCEPTUAL (NO ES TEXTO LITERAL DE UNA ÚNICA NORMA)\n\nEl programa oficial exige: accidente de tráfico; definición, tipos, causas y clases; actividad policial; orden cronológico de las actuaciones.\n\nIdea de estudio: el siniestro vial se analiza atendiendo al factor humano, el vehículo y la vía/entorno. Entre los factores concurrentes se estudian distracción, velocidad inadecuada, alcohol/drogas, cansancio, enfermedad, estado técnico del vehículo, señalización, geometría, visibilidad, firme y meteorología.\n\nClasificaciones útiles: por consecuencias (daños, heridos, fallecidos), por número de unidades implicadas (simple/múltiple) y por forma de producción (colisión, choque, atropello, salida de vía, vuelco, caída, etc.).\n\nEsquema operativo de actuación policial: recepción y valoración del aviso; autoprotección y señalización/protección del lugar; auxilio y coordinación de emergencias; regulación del tráfico; identificación de implicados y testigos; comprobaciones y pruebas legalmente procedentes; preservación y recogida de vestigios, fotografías y mediciones; investigación/reconstrucción; restablecimiento seguro de la circulación; diligencias, informe/atestado y comunicaciones procedentes.\n\nFuentes oficiales de apoyo: DGT/Ministerio del Interior sobre investigación de siniestros y Registro Nacional de Víctimas, junto con la normativa de tráfico y LECrim. Esta ficha no sustituye una clasificación o secuencia literal de un manual EBAP/Reisan si la academia exige una formulación concreta.'''
def sel(t):
    raw=overrides.get(t,relations.get(t,[])); out=[]; seen=set()
    for x in raw:
        if x in by_id and x not in seen: out.append(x); seen.add(x)
    return out
font='Helvetica'; bold='Helvetica-Bold'
if os.path.exists('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
    pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')); pdfmetrics.registerFont(TTFont('DVB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')); font='DV'; bold='DVB'
styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name='Cov',parent=styles['Title'],fontName=bold,fontSize=20,leading=24,alignment=TA_CENTER)); styles.add(ParagraphStyle(name='TemaX',parent=styles['Heading1'],fontName=bold,fontSize=15,leading=19)); styles.add(ParagraphStyle(name='NormX',parent=styles['Heading2'],fontName=bold,fontSize=10.5,leading=13)); styles.add(ParagraphStyle(name='ArtX',parent=styles['Heading3'],fontName=bold,fontSize=9.5,leading=12)); styles.add(ParagraphStyle(name='BodyX',parent=styles['BodyText'],fontName=font,fontSize=8.4,leading=11.2,spaceAfter=5)); styles.add(ParagraphStyle(name='NoteX',parent=styles['BodyText'],fontName=font,fontSize=8.2,leading=10.8,leftIndent=7*mm,rightIndent=7*mm,borderWidth=.5,borderPadding=5,spaceAfter=6)); styles.add(ParagraphStyle(name='SrcX',parent=styles['BodyText'],fontName=font,fontSize=7.3,leading=9,textColor='#555555'))
def pp(s): return escape(clean(s)).replace('\n','<br/>')
def footer(c,d):
    c.saveState(); c.setFont(font,7); c.drawString(16*mm,10*mm,'Temario común Policía Local Illes Balears - base 2026 - TypedAI'); c.drawRightString(195*mm,10*mm,f'Página {d.page}'); c.restoreState()
pdf=OUT/'TEMARIO_PL_BALEARES_2026_TYPEDAI.pdf'; txt=OUT/'TEMARIO_PL_BALEARES_2026_TYPEDAI.txt'; cov=OUT/'COBERTURA_TYPEDAI.txt'
doc=SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,topMargin=17*mm,bottomMargin=16*mm,title='Temario PL Baleares 2026 TypedAI')
story=[Spacer(1,35*mm),Paragraph('TEMARIO COMÚN - POLICÍA LOCAL ILLES BALEARS',styles['Cov']),Paragraph('30 temas · compilación para estudio activo en TypedAI',styles['Cov']),Spacer(1,8*mm),Paragraph('Base del programa: BOIB 34/2026, anexo 4, apartado 1.A. Texto jurídico: consolidaciones oficiales BOE/BOIB/CAIB importadas en el proyecto el 08/10/2026. Se separa el texto normativo de las síntesis de apoyo.',styles['NoteX']),Paragraph('La convocatoria y cualquier modificación normativa posterior prevalecen. El Tema 17 no corresponde a una única norma y se incluye como ficha conceptual de apoyo identificada como tal.',styles['NoteX']),PageBreak()]
lines=['TEMARIO COMÚN POLICÍA LOCAL ILLES BALEARS - 2026\n']; cover=[]
for t in sorted(temas,key=lambda x:int(x['id_tema'])):
    n=int(t['id_tema']); title=clean(t.get('titulo_oficial_literal','')); story += [Paragraph(f'TEMA {n}',styles['TemaX']),Paragraph(pp(title),styles['BodyX']),Paragraph('Programa oficial: BOIB 34/2026, anexo 4, apartado 1.A.',styles['SrcX'])]; lines += [f"\n\n{'='*80}\nTEMA {n}\n{title}\n{'='*80}\n"]
    if n==1: story.append(Paragraph(pp(T1),styles['NoteX'])); lines.append('\n'+T1+'\n')
    if n==17: story.append(Paragraph(pp(T17),styles['NoteX'])); lines.append('\n'+T17+'\n')
    ids=sel(n); cover.append((n,len(ids),t.get('estado_fuente',''),t.get('estado_verificacion',''))); current=None
    for artid in ids:
        a=by_id[artid]; norm=a.get('id_norma',artid.split(':',1)[0])
        if norm!=current:
            meta=by_norm.get(norm,{}); nt=clean(meta.get('titulo_oficial',norm)); story.append(Paragraph(pp(nt),styles['NormX'])); url=meta.get('url_fuente','');
            if url: story.append(Paragraph(pp('Fuente oficial: '+url),styles['SrcX']))
            lines.append(f'\nNORMA: {nt}\n');
            if url: lines.append(f'Fuente: {url}\n')
            current=norm
        tipo=clean(a.get('tipo','artículo')); num=clean(a.get('numero','')); rub=clean(a.get('rubrica','')); heading=(f'Artículo {num}' if tipo.lower().startswith('art') else f'{tipo} {num}'.strip()) + (f'. {rub}' if rub else ''); body=clean(a.get('texto',''))
        story.append(Paragraph(pp(heading),styles['ArtX']))
        for chunk in re.split(r'\n\s*\n',body):
            if chunk.strip(): story.append(Paragraph(pp(chunk),styles['BodyX']))
        lines.append(f'\n{heading}\n{body}\n')
    if n!=30: story.append(PageBreak())
doc.build(story,onFirstPage=footer,onLaterPages=footer); txt.write_text(''.join(lines),encoding='utf-8')
c=['COBERTURA DEL PDF TYPEDAI\n','Programa: BOIB 34/2026, anexo 4, 1.A.\n','T1, T5, T20 y T22 usan delimitación manual por rúbricas; T17 usa ficha oficial-conceptual de apoyo.\n\n']
for n,count,sf,sv in cover: c.append(f'Tema {n:02d}: {count} unidades normativas | fuente={sf} | verificación_repo={sv}\n')
cov.write_text(''.join(c),encoding='utf-8'); print(pdf); print(txt); print(cov)
