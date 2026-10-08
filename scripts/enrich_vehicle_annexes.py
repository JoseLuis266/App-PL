#!/usr/bin/env python3
"""Fill Tema 15/16 annex bodies from the official consolidated BOE HTML.

Tema 15 requires the full Annex II (definitions and vehicle categories).
Tema 16, according to the literal 2026 syllabus, requires Annex XVIII only through
'I. Colores e inscripciones' and 'II. Contraseñas de las placas'.
"""
import json
import re
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
ARTS_PATH = ROOT / "export" / "articulos.json"
# 26 June 2026 is the latest consolidated version currently published by BOE for this regulation.
BOE_URL = "https://www.boe.es/buscar/act.php?id=BOE-A-1999-1826&p=20260626&tn=0"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()


def heading_text(tag) -> str:
    return norm(tag.get_text(" ", strip=True))


def find_heading(soup, exact: str):
    exact_n = norm(exact).casefold()
    candidates = []
    for tag in soup.find_all(re.compile(r"^h[1-6]$")):
        if heading_text(tag).casefold() == exact_n:
            candidates.append(tag)
    if not candidates:
        raise RuntimeError(f"No se encontró encabezado oficial: {exact}")
    # The body heading is normally the last exact heading; this avoids TOC duplicates.
    return candidates[-1]


def extract_between(start, stop_pred):
    out = []
    seen_tables = set()
    for tag in start.find_all_next():
        if tag is start:
            continue
        if re.fullmatch(r"h[1-6]", tag.name or "") and stop_pred(heading_text(tag)):
            break
        if tag.name in {"h4", "h5", "h6", "p"}:
            text = norm(tag.get_text(" ", strip=True))
            if text and text.lower() not in {"subir"}:
                out.append(text)
        elif tag.name == "table":
            # Preserve each table row as a compact 'cell | cell' line so TypedAI can
            # learn definitions, categories and province/state codes without images.
            key = id(tag)
            if key in seen_tables:
                continue
            seen_tables.add(key)
            rows = []
            for tr in tag.find_all("tr"):
                cells = [norm(c.get_text(" ", strip=True)) for c in tr.find_all(["th", "td"])]
                cells = [c for c in cells if c]
                if cells:
                    rows.append(" | ".join(cells))
            if rows:
                out.extend(rows)
    # De-duplicate only adjacent exact lines; preserve repeated legal wording elsewhere.
    cleaned = []
    for line in out:
        if not cleaned or cleaned[-1] != line:
            cleaned.append(line)
    return "\n".join(cleaned).strip()


req = urllib.request.Request(
    BOE_URL,
    headers={"User-Agent": "Mozilla/5.0 (compatible; App-PL-study-import/1.0)"},
)
with urllib.request.urlopen(req, timeout=60) as r:
    raw = r.read()
if len(raw) < 100_000:
    raise RuntimeError(f"Respuesta BOE inesperadamente corta: {len(raw)} bytes")

soup = BeautifulSoup(raw, "html.parser")

h2 = find_heading(soup, "ANEXO II")
annex2 = extract_between(
    h2,
    lambda txt: txt.casefold() == "anexo iii",
)
if len(annex2) < 10_000 or "A. Definiciones" not in annex2 or "B. Clasificación por criterios de construcción" not in annex2:
    raise RuntimeError(f"Extracción incompleta del Anexo II ({len(annex2)} caracteres)")

h18 = find_heading(soup, "ANEXO XVIII")
annex18 = extract_between(
    h18,
    lambda txt: txt.casefold().startswith("iii. número y ubicación de las placas"),
)
if len(annex18) < 5_000 or "I. Colores e inscripciones" not in annex18 or "II. Contraseñas de las placas" not in annex18:
    raise RuntimeError(f"Extracción incompleta del Anexo XVIII I-II ({len(annex18)} caracteres)")
# Defensive check: Tema 16 must not absorb sections III/IV outside the literal syllabus wording.
if "III. Número y ubicación de las placas" in annex18:
    raise RuntimeError("El Anexo XVIII extrajo por error la sección III")

arts = json.loads(ARTS_PATH.read_text(encoding="utf-8"))
updated = set()
for a in arts:
    if a.get("id_articulo") == "vehiculos:anii":
        a["texto"] = "ANEXO II\nDEFINICIONES Y CATEGORÍAS DE LOS VEHÍCULOS\n" + annex2
        a["url_fuente"] = BOE_URL + "#anii"
        a["estado"] = "pendiente_revision"
        notes = ["Texto recuperado automáticamente del HTML consolidado oficial BOE, versión 26/06/2026"]
        a["notas_fuente"] = json.dumps(notes, ensure_ascii=False)
        updated.add("vehiculos:anii")
    elif a.get("id_articulo") == "vehiculos:anxviii":
        a["texto"] = "ANEXO XVIII\nPLACAS DE MATRÍCULA\n" + annex18
        a["url_fuente"] = BOE_URL + "#anxviii"
        a["estado"] = "pendiente_revision"
        notes = ["Solo secciones I y II, conforme al literal del Tema 16 del programa 2026; texto del HTML consolidado oficial BOE 26/06/2026"]
        a["notas_fuente"] = json.dumps(notes, ensure_ascii=False)
        updated.add("vehiculos:anxviii")

if updated != {"vehiculos:anii", "vehiculos:anxviii"}:
    raise RuntimeError(f"No se localizaron ambos registros de anexos en articulos.json: {sorted(updated)}")

ARTS_PATH.write_text(json.dumps(arts, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Anexo II: {len(annex2):,} caracteres")
print(f"Anexo XVIII I-II: {len(annex18):,} caracteres")
print("T15 y T16 completados desde BOE oficial consolidado 26/06/2026")
