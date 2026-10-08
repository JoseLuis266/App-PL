import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from network import ROOT


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect('file:'+str(ROOT/'temario.db')+'?mode=ro',uri=True)
        self.db.row_factory=sqlite3.Row
    def tearDown(self):self.db.close()
    def test_all_30_topics_and_literal_titles(self):
        program=json.loads((ROOT/'data/programa.json').read_text())
        rows=list(self.db.execute('SELECT id_tema,titulo_oficial_literal FROM temas ORDER BY id_tema'))
        self.assertEqual(list(range(1,31)),[r['id_tema'] for r in rows])
        self.assertEqual([t['titulo_oficial_literal'] for t in program['temas']],[r['titulo_oficial_literal'] for r in rows])
    def test_foreign_keys_and_integrity(self):
        self.assertEqual([],list(self.db.execute('PRAGMA foreign_key_check')))
        self.assertEqual('ok',self.db.execute('PRAGMA integrity_check').fetchone()[0])
    def test_shared_norm_is_not_duplicated(self):
        self.assertEqual(1,self.db.execute("SELECT count(*) FROM normas WHERE id_boe='BOE-A-1978-31229'").fetchone()[0])
        self.assertEqual(4,self.db.execute("SELECT count(DISTINCT id_tema) FROM tema_norma WHERE id_norma='penal' AND id_tema BETWEEN 24 AND 27").fetchone()[0])
    def test_no_expired_blocks_in_study_relationships(self):
        self.assertEqual(0,self.db.execute("SELECT count(*) FROM tema_articulo ta JOIN articulos a USING(id_articulo) WHERE a.estado='historico_no_vigente'").fetchone()[0])
    def test_no_auto_verified_or_generated_content(self):
        self.assertEqual(0,self.db.execute("SELECT count(*) FROM temas WHERE estado_verificacion='verificado'").fetchone()[0])
        self.assertEqual(0,self.db.execute('SELECT count(*) FROM contenido_ia').fetchone()[0])
    def test_special_topic17_support_only(self):
        self.assertEqual('sin_norma_especifica',self.db.execute('SELECT estado_fuente FROM temas WHERE id_tema=17').fetchone()[0])
        self.assertEqual(0,self.db.execute("SELECT count(*) FROM tema_norma WHERE id_tema=17 AND papel!='apoyo'").fetchone()[0])
    def test_hashes_every_legal_fragment(self):
        for row in self.db.execute('SELECT texto,hash_texto FROM articulos'):
            self.assertEqual(hashlib.sha256(row['texto'].encode()).hexdigest(),row['hash_texto'])
    def test_each_unit_traceable_to_archive(self):
        for row in self.db.execute('SELECT archivo_bruto,hash_archivo FROM normas'):
            file=ROOT/row['archivo_bruto'];self.assertTrue(file.is_file())
            self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),row['hash_archivo'])
    def test_assets_available_and_intact(self):
        for row in self.db.execute('SELECT archivo,sha256,estado FROM recursos'):
            self.assertEqual('descargado',row['estado']);p=ROOT/row['archivo']
            self.assertTrue(p.is_file());self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row['sha256'])
    def test_fts_functional(self):
        self.assertGreater(self.db.execute("SELECT count(*) FROM articulos_fts WHERE articulos_fts MATCH 'habeas'").fetchone()[0],0)
    def test_topic26_matches_road_safety_chapter(self):
        rows=list(self.db.execute('SELECT a.texto,a.jerarquia FROM articulos a JOIN tema_articulo ta USING(id_articulo) WHERE ta.id_tema=26'))
        self.assertGreater(len(rows),0)
        self.assertTrue(all('Seguridad Vial' in r['jerarquia'] for r in rows))
    def test_exports_match_database(self):
        for file in sorted((ROOT/'export').glob('*.json')):
            name=file.stem
            rows=[dict(r) for r in self.db.execute('SELECT * FROM '+name+' ORDER BY rowid')]
            self.assertEqual(rows,json.loads(file.read_text()),name)


if __name__=='__main__':unittest.main()
