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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "typedai_output"
OUT.mkdir(exist_ok=True)


def load_json(name):
    with open(ROOT / "export" / name, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_text(s):
    if s is None:
        return ""
    s = html.unescape(str(s))
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</p\s*>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def aid(norma, n):
    return f"{norma}:a{n}"


def range_ids(norma, start, end):
    return [aid(norma, n) for n in range(start, end + 1)]


def natural_article_key(obj):
    # Fall back to source order. The database's 'orden' is the authoritative order.
    return (obj.get("orden", 10**9), obj.get("id_articulo", ""))


temas = load_json("temas.json")
rel = load_json("tema_articulo.json")
arts = load_json("articulos.json")
normas = load_json("normas.json")

by_id = {a["id_articulo"]: a for a in arts}
by_norma = {n["id_norma"]: n for n in normas}
relations = {}
for r in rel:
    relations.setdefault(int(r["id_tema"]), []).append(r["id_articulo"])

# Precise overrides for the four ranges that the first automatic import left too broad.
# They are derived from the literal 2026 common syllabus (BOIB 34/2026, anexo 4, 1.A)
# and the official structure/rubrics of each cited norm.
overrides = {
    # T1: constitutional basic principles: Preliminary Title. A short doctrinal/structure note is added separately.
    1: range_ids("ce", 1, 9),
    # T5: General provisions; competences; named institutions through municipalities/local entities;
    # TSJ + competences + president; financing/hacienda general principles.
    5: (
        range_ids("estatuto", 1, 12)
        + range_ids("estatuto", 30, 38)
        + range_ids("estatuto", 39, 75)
        + range_ids("estatuto", 93, 95)
        + range_ids("estatuto", 120, 126)
    ),
    # T20: Decreto 40/2019. Chapter III on basic self-defence/protection equipment (arts. 48-88)
    # plus Title VII Uniformity and equipment, including appearance/presentation/uniformity (arts. 89-126).
    20: range_ids("marco", 48, 126),
    # T22: Local police as judicial police + detention + detainee rights/guarantees + Habeas Corpus.
    22: (
        [aid("ce", 17), aid("fcs", 29), aid("fcs", 53)]
        + range_ids("lecrim", 282, 298)
        + range_ids("lecrim", 489, 501)
        + [aid("lecrim", 520), "lecrim:a520bis", "lecrim:a520ter"]
        + range_ids("lecrim", 521, 527)
        + [x for x in by_id if x.startswith("habeas:")]
    ),
}

# T17 is not tied to one norm in the official syllabus. This is a concise support sheet based on
# DGT/Interior official material, kept visibly separate from literal legislation.
T17_SUPPORT = """
TEMA 17 - APOYO CONCEPTUAL (NO ES TEXTO LITERAL DE UNA ÚNICA NORMA)

El programa oficial exige: accidente de tráfico; definición, tipos, causas y clases; actividad policial; orden cronológico de las actuaciones.

1. Idea de accidente/siniestro vial
Suceso producido con ocasión de la circulación en el que intervienen uno o más usuarios/vehículos y del que pueden derivarse daños personales o materiales. Para estadística oficial, la DGT aplica las definiciones del Registro Nacional de Víctimas de Accidentes de Tráfico (Orden INT/2223/2014).

2. Factores y causas que deben investigarse
La investigación oficial de siniestros analiza de forma conjunta el factor humano, el vehículo y la vía/entorno. Entre los factores humanos pueden aparecer distracción, velocidad inadecuada, alcohol/drogas, cansancio, inexperiencia o enfermedad; también se estudian estado técnico del vehículo, señalización, geometría, visibilidad, firme, meteorología y demás circunstancias de la vía.

3. Clases/tipos útiles para el estudio policial
Pueden clasificarse, entre otros criterios, por consecuencias (solo daños, heridos, fallecidos), por número de unidades implicadas (simple o múltiple) y por la forma de producción (colisión, choque, atropello, salida de vía, vuelco, caída, etc.). La clasificación concreta debe ajustarse a la utilizada en el material docente/estadístico aplicable.

4. Secuencia policial de actuación - esquema operativo de estudio
- Recepción del aviso y valoración inicial.
- Llegada, autoprotección y señalización/protección del lugar.
- Auxilio a víctimas y activación/coordinación de emergencias.
- Regulación del tráfico y prevención de riesgos secundarios.
- Identificación de implicados y testigos; comprobaciones documentales.
- Pruebas legalmente procedentes (por ejemplo alcohol/drogas) y adopción de medidas cautelares si corresponden.
- Preservación, observación y recogida de vestigios; fotografías, mediciones, posiciones, huellas y daños.
- Reconstrucción/investigación de circunstancias y causas cuando proceda.
- Restablecimiento seguro de la circulación y retirada de obstáculos/vehículos conforme proceda.
- Documentación: diligencias, informe/atestado y comunicaciones administrativas/judiciales que correspondan.

Fuentes oficiales de apoyo: Dirección General de Tráfico (investigación de accidentes y Registro Nacional de Víctimas) y normativa de tráfico/LECrim aplicable. Esta ficha no sustituye un manual EBAP/Reisan si la academia exige una clasificación o secuencia literal propia.
""".strip()

T1_SUPPORT = """
APOYO DE ESTRUCTURA (síntesis, no texto literal): la Constitución Española de 1978 se organiza en Preámbulo, Título Preliminar, diez títulos numerados (I-X), disposiciones adicionales, transitorias, derogatoria y final. Para este tema, el núcleo normativo de principios constitucionales básicos es el Título Preliminar (arts. 1-9). La supremacía normativa se refleja, entre otros puntos, en la sujeción de ciudadanos y poderes públicos a la Constitución y al resto del ordenamiento.
""".strip()

# Validate requested ids and preserve requested order.
def selected_ids(topic):
    raw = overrides.get(topic, relations.get(topic, []))
    out, seen = [], set()
    for x in raw:
        if x in by_id and x not in seen:
            out.append(x); seen.add(x)
    return out

# Fonts
font = "Helvetica"
bold = "Helvetica-Bold"
for candidate in [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]:
    if os.path.exists(candidate):
        pass
if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
    pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuBold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    font, bold = "DejaVu", "DejaVuBold"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName=bold, fontSize=20, leading=24, alignment=TA_CENTER, spaceAfter=10))
styles.add(ParagraphStyle(name="Tema", parent=styles["Heading1"], fontName=bold, fontSize=15, leading=19, spaceAfter=8))
styles.add(ParagraphStyle(name="Norma", parent=styles["Heading2"], fontName=bold, fontSize=10.5, leading=13, spaceBefore=8, spaceAfter=5))
styles.add(ParagraphStyle(name="Article", parent=styles["Heading3"], fontName=bold, fontSize=9.5, leading=12, spaceBefore=7, spaceAfter=3))
styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontName=font, fontSize=8.4, leading=11.2, spaceAfter=5))
styles.add(ParagraphStyle(name="Note", parent=styles["BodyText"], fontName=font, fontSize=8.2, leading=10.8, leftIndent=7*mm, rightIndent=7*mm, spaceAfter=6, borderWidth=0.5, borderPadding=5))
styles.add(ParagraphStyle(name="Source", parent=styles["BodyText"], fontName=font, fontSize=7.4, leading=9.2, textColor="#555555", spaceAfter=3))


def ptext(text):
    return escape(clean_text(text)).replace("\n", "<br/>")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(font, 7)
    canvas.drawString(18*mm, 10*mm, "Temario común Policía Local Illes Balears - base 2026 - preparado para TypedAI")
    canvas.drawRightString(195*mm, 10*mm, f"Página {doc.page}")
    canvas.restoreState()

pdf_path = OUT / "TEMARIO_PL_BALEARES_2026_TYPEDAI.pdf"
txt_path = OUT / "TEMARIO_PL_BALEARES_2026_TYPEDAI.txt"
coverage_path = OUT / "COBERTURA_TYPEDAI.txt"

doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, leftMargin=16*mm, rightMargin=16*mm, topMargin=17*mm, bottomMargin=16*mm, title="Temario Policía Local Illes Balears 2026 - TypedAI")
story = []

story += [
    Spacer(1, 35*mm),
    Paragraph("TEMARIO COMÚN - POLICÍA LOCAL ILLES BALEARS", styles["CoverTitle"]),
    Paragraph("30 temas · compilación para estudio activo en TypedAI", styles["CoverTitle"]),
    Spacer(1, 8*mm),
    Paragraph("Base del programa: BOIB 34/2026, anexo 4, apartado 1.A. Texto jurídico: consolidaciones oficiales BOE/BOIB/CAIB importadas en el proyecto el 08/10/2026. El documento separa el texto normativo de las síntesis de apoyo.", styles["Note"]),
    Paragraph("Importante: el contenido legal consolidado sirve para estudio, pero la convocatoria y las modificaciones normativas posteriores prevalecen siempre. El Tema 17 no corresponde a una única norma y se incluye como ficha conceptual de apoyo, claramente identificada.", styles["Note"]),
    PageBreak(),
]

text_lines = ["TEMARIO COMÚN POLICÍA LOCAL ILLES BALEARS - 2026\n"]
coverage = []

for t in sorted(temas, key=lambda x: int(x["id_tema"])):
    num = int(t["id_tema"])
    title = clean_text(t.get("titulo_oficial_literal", ""))
    story.append(Paragraph(f"TEMA {num}", styles["Tema"]))
    story.append(Paragraph(ptext(title), styles["BodySmall"]))
    story.append(Paragraph("Programa oficial: BOIB 34/2026, anexo 4, apartado 1.A.", styles["Source"]))
    text_lines += [f"\n\n{'='*80}\nTEMA {num}\n{title}\n{'='*80}\n"]

    if num == 1:
        story.append(Paragraph(ptext(T1_SUPPORT), styles["Note"]))
        text_lines.append("\n" + T1_SUPPORT + "\n")
    if num == 17:
        story.append(Paragraph(ptext(T17_SUPPORT), styles["Note"]))
        text_lines.append("\n" + T17_SUPPORT + "\n")

    ids = selected_ids(num)
    coverage.append((num, len(ids), t.get("estado_fuente", ""), t.get("estado_verificacion", "")))

    current_norm = None
    for art_id in ids:
        a = by_id[art_id]
        norm = a.get("id_norma", art_id.split(":",1)[0])
        if norm != current_norm:
            n = by_norma.get(norm, {})
            ntitle = clean_text(n.get("titulo_oficial", norm))
            story.append(Paragraph(ptext(ntitle), styles["Norma"]))
            url = n.get("url_fuente", "")
            if url:
                story.append(Paragraph(ptext("Fuente oficial: " + url), styles["Source"]))
            text_lines += [f"\nNORMA: {ntitle}\n"]
            if url:
                text_lines.append(f"Fuente: {url}\n")
            current_norm = norm

        tipo = clean_text(a.get("tipo", "artículo"))
        numero = clean_text(a.get("numero", ""))
        rubrica = clean_text(a.get("rubrica", ""))
        if tipo.lower().startswith("art"):
            heading = f"Artículo {numero}" if numero else "Artículo"
        else:
            heading = f"{tipo} {numero}".strip()
        if rubrica:
            heading += f". {rubrica}"
        body = clean_text(a.get("texto", ""))
        story.append(Paragraph(ptext(heading), styles["Article"]))
        if body:
            # Split huge article text into paragraphs to keep Platypus stable.
            for chunk in re.split(r"\n\s*\n", body):
                if chunk.strip():
                    story.append(Paragraph(ptext(chunk), styles["BodySmall"]))
        text_lines += [f"\n{heading}\n{body}\n"]

    if not ids and num != 17:
        msg = "No se encontró contenido normativo enlazado para este tema en la base importada."
        story.append(Paragraph(msg, styles["Note"]))
        text_lines.append("\n" + msg + "\n")

    if num != 30:
        story.append(PageBreak())

# build PDF and text

doc.build(story, onFirstPage=footer, onLaterPages=footer)
txt_path.write_text("".join(text_lines), encoding="utf-8")

cov_lines = [
    "COBERTURA DEL PDF TYPEDAI\n",
    "Programa: BOIB 34/2026, anexo 4, 1.A.\n",
    "Los temas 1, 5, 20 y 22 usan delimitación manual por rúbricas del programa; el 17 usa ficha de apoyo conceptual.\n\n",
]
for num, count, sf, sv in coverage:
    cov_lines.append(f"Tema {num:02d}: {count} unidades normativas | fuente={sf} | verificación_repo={sv}\n")
coverage_path.write_text("".join(cov_lines), encoding="utf-8")

print(pdf_path)
print(txt_path)
print(coverage_path)
