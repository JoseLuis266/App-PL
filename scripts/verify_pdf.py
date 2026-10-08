"""Independent PDF extraction check. Never promotes legal verification states."""
from datetime import datetime,timezone
import hashlib
import json
import random
import re
import subprocess
import tempfile
from database import connect,export
from network import ROOT

def normalize(text):
    return re.sub(r'\s+',' ',text).strip()

def main():
    db=connect();norm=db.execute("SELECT * FROM normas WHERE id_norma='marco'").fetchone()
    raw=ROOT/norm['archivo_bruto']
    if hashlib.sha256(raw.read_bytes()).hexdigest()!=norm['hash_archivo']:raise ValueError('PDF alterado')
    with tempfile.TemporaryDirectory() as directory:
        path=directory+'/independiente.txt'
        subprocess.run(['pdftotext','-layout',str(raw),path],check=True)
        independent=open(path,encoding='utf-8').read()
    source=normalize(independent)
    candidate=ROOT/'data/marco-extraccion-independiente.txt'
    candidate.write_text(independent,encoding='utf-8')
    candidates=list(db.execute("SELECT * FROM articulos WHERE id_norma='marco' AND tipo='articulo' ORDER BY orden"))
    sample=random.Random('CAIB-Decret40/2019').sample(candidates,5)
    checks=[]
    for article in sample:
        same=normalize(article['texto']) in source
        checks.append(dict(id_articulo=article['id_articulo'],numero=article['numero'],url=article['url_fuente'],hash_texto=article['hash_texto'],resultado='literal_presente_en_extraccion_independiente' if same else 'discordancia_o_intercalacion_notas_pendiente_revision',criterio='Fragmento íntegro contiguo tras normalizar exclusivamente espacios; notas y encabezados no eliminados.'))
    report=dict(fecha=datetime.now(timezone.utc).isoformat(),herramienta='pdftotext -layout',archivo=norm['archivo_bruto'],sha256=norm['hash_archivo'],extraccion_independiente=str(candidate.relative_to(ROOT)),sha256_extraccion=hashlib.sha256(independent.encode()).hexdigest(),muestras=checks,aprobacion_juridica=False,aviso='Una coincidencia confirma la presencia del fragmento, no la ausencia de omisiones en toda la norma ni su vigencia. Ningún estado jurídico se modifica.')
    (ROOT/'data/marco-contraste-independiente.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with db:
        db.execute('INSERT INTO verificaciones(id_norma,fecha,resultado,informe_json) VALUES(?,?,?,?)',('marco',report['fecha'],'contraste_independiente_parcial',json.dumps(report,ensure_ascii=False)))
        if any(c['resultado']!='literal_presente_en_extraccion_independiente' for c in checks):
            existing=db.execute("SELECT id FROM incidencias WHERE id_norma='marco' AND codigo='contraste_pdf_independiente'").fetchone()
            if not existing:
                db.execute('INSERT INTO incidencias(id_norma,codigo,detalle) VALUES(?,?,?)',('marco','contraste_pdf_independiente','Cinco muestras contrastadas con pdftotext: 104, 178, 151, 77 y 49 bis. Discordancias de espacios internos y notas; revisar páginas y extracción candidata antes de sustituir texto. Informe: data/marco-contraste-independiente.json.'))
    export(db)
    print(json.dumps(checks,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
