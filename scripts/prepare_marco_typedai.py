#!/usr/bin/env python3
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "export" / "articulos.json"
arts = json.loads(path.read_text(encoding="utf-8"))
segments = [a for a in arts if a.get("id_norma") == "marco" and a.get("id_articulo", "").startswith("marco:pdf-segmento-")]
segments.sort(key=lambda a: (a.get("orden", 10**9), a.get("id_articulo", "")))
if not segments:
    raise SystemExit("No se encontraron segmentos PDF del Decreto 40/2019")

# Join the official consolidated PDF extraction in source order.
parts = []
for a in segments:
    txt = (a.get("texto") or "").strip()
    if txt:
        parts.append(txt)
combined = "\n".join(parts)

# The CAIB consolidated edition is Catalan; original Spanish editions may use Artículo.
pat = re.compile(r"(?im)^(?:article|artículo)\s+(\d{1,3})(\s+bis)?\b[^\n]*")
matches = list(pat.finditer(combined))
if not matches:
    raise SystemExit("No se detectaron encabezados Article/Artículo en el Decreto 40/2019")

found = {}
for i, m in enumerate(matches):
    num = int(m.group(1))
    bis = bool(m.group(2))
    start = m.start()
    end = matches[i+1].start() if i+1 < len(matches) else len(combined)
    chunk = combined[start:end].strip()
    key = f"{num}bis" if bis else str(num)
    # Keep the longest occurrence if a table of contents also happens to contain a heading-like line.
    if len(chunk) > len(found.get(key, "")):
        found[key] = chunk

missing = [str(n) for n in range(48, 127) if str(n) not in found]
if missing:
    raise SystemExit("Faltan artículos 48-126 en extracción consolidada: " + ", ".join(missing))

# Preserve 49 bis (introduced in 2026) inside the T20 material even though the downstream
# PDF builder expects one synthetic record per integer article number.
if "49bis" in found:
    found["49"] = found["49"].rstrip() + "\n\n" + found["49bis"].strip()

# Remove any prior synthetic records and append current ones.
arts = [a for a in arts if not (a.get("id_norma") == "marco" and re.fullmatch(r"marco:a(?:[4-9]\d|1[01]\d|12[0-6])", a.get("id_articulo", "")))]
base_url = segments[0].get("url_fuente", "")
for n in range(48, 127):
    txt = found[str(n)]
    first_line = txt.splitlines()[0].strip()
    arts.append({
        "id_articulo": f"marco:a{n}",
        "id_norma": "marco",
        "bloque_fuente": f"a{n}",
        "orden": 100000 + n,
        "tipo": "articulo",
        "numero": str(n),
        "rubrica": first_line,
        "texto": txt,
        "jerarquia": "{}",
        "url_fuente": base_url,
        "hash_texto": "",
        "texto_xml": "",
        "fecha_publicacion_version": "",
        "fecha_vigencia_version": "",
        "norma_version": "Decreto 40/2019 - consolidado CAIB",
        "estado": "pendiente_revision",
        "notas_fuente": "[\"Extracción automática del PDF consolidado oficial CAIB para T20\"]"
    })

path.write_text(json.dumps(arts, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Preparados 79 artículos sintéticos (48-126); 49 bis incluido={('49bis' in found)}")
print(f"Encabezados detectados en consolidado: {len(matches)}")
