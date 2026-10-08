"""Read-only, reproducible web projection; never changes legal verification states."""
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
from network import ROOT

def write(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')

def main():
    db=sqlite3.connect('file:'+str(ROOT/'temario.db')+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    target=ROOT/'public/legal';target.mkdir(parents=True,exist_ok=True)
    media=target/'media';media.mkdir(exist_ok=True)
    assets={}
    for row in db.execute("SELECT * FROM recursos WHERE estado='descargado'"):
        source=ROOT/row['archivo'];raw=source.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Recurso alterado: '+str(source))
        extension='.png' if raw.startswith(b'\x89PNG') else '.jpg' if raw.startswith(b'\xff\xd8') else '.gif' if raw.startswith(b'GIF8') else '.svg' if b'<svg' in raw[:1000] else '.webp' if raw[8:12]==b'WEBP' else '.bin'
        name=row['sha256']+extension;dest=media/name
        if not dest.exists():shutil.copyfile(source,dest)
        assets[row['url']]='legal/media/'+name
    norms=[dict(r) for r in db.execute('SELECT * FROM normas ORDER BY rowid')]
    for norm in norms:
        rows=[dict(r) for r in db.execute("SELECT * FROM articulos WHERE id_norma=? AND estado!='historico_no_vigente' ORDER BY orden",(norm['id_norma'],))]
        for r in rows:
            r['jerarquia']=json.loads(r['jerarquia']);r['notas_fuente']=json.loads(r['notas_fuente'])
        write(target/(norm['id_norma']+'.json'),rows)
    topics=[dict(r) for r in db.execute('SELECT * FROM temas ORDER BY id_tema')]
    for t in topics:
        t['articulos']=[r[0] for r in db.execute('SELECT DISTINCT id_articulo FROM tema_articulo WHERE id_tema=? ORDER BY id_articulo',(t['id_tema'],))]
        t['relaciones']=[dict(r) for r in db.execute('SELECT * FROM tema_norma WHERE id_tema=? ORDER BY id_relacion',(t['id_tema'],))]
    updates=ROOT/'data/actualizaciones.json'
    bank=[]
    exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ejercicios_literales'").fetchone()
    if exists:
        for r in db.execute("SELECT e.* FROM ejercicios_literales e JOIN articulos a USING(id_articulo) JOIN temas t ON t.id_tema=e.id_tema WHERE e.estado='texto_contrastado' AND e.hash_texto=a.hash_texto AND a.estado!='historico_no_vigente' AND t.estado_fuente='ok' ORDER BY e.id_tema,e.rowid"):
            item=dict(r);item['opciones']=json.loads(item['opciones']);item['evidencia']=json.loads(item['evidencia'])
            source=db.execute('SELECT rubrica,url_fuente,id_norma,tipo FROM articulos WHERE id_articulo=?',(item['id_articulo'],)).fetchone()
            item.update(rubrica_fuente=source['rubrica'],url_fuente=source['url_fuente'],id_norma_fuente=source['id_norma'],tipo_fuente=source['tipo']);bank.append(item)
    manifest=dict(temas=topics,normas=norms,banco_literal=bank,recursos=assets,incidencias=[dict(r) for r in db.execute("SELECT * FROM incidencias WHERE estado='pendiente'")],actualizaciones=json.loads(updates.read_text()) if updates.exists() else [])
    write(target/'manifest.json',manifest)
    db.close()
    print(f'Web: {len(topics)} temas, {len(norms)} normas, {len(assets)} recursos. Verificación conservada.')

if __name__=='__main__':main()
