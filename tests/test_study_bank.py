"""Check every pilot passage against archived independent official evidence."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from boe import block_text,selected_version,xml_root
from network import ROOT,official_url

class LiteralBankTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect('file:'+str(ROOT/'temario.db')+'?mode=ro',uri=True);self.db.row_factory=sqlite3.Row
    def tearDown(self):self.db.close()
    def test_all_pilot_fragments_answers_and_options_traceable(self):
        rows=list(self.db.execute("SELECT * FROM ejercicios_literales WHERE estado='texto_contrastado'"));self.assertGreater(len(rows),100)
        for r in rows:
            a=self.db.execute('SELECT * FROM articulos WHERE id_articulo=?',(r['id_articulo'],)).fetchone()
            self.assertEqual(a['hash_texto'],r['hash_texto']);self.assertEqual(a['texto'][r['inicio']:r['fin']],r['cita'])
            self.assertEqual(r['respuesta'],r['cita'][r['inicio_respuesta']:r['inicio_respuesta']+len(r['respuesta'])])
            self.assertEqual(1,r['cita'].count(r['respuesta']))
            e=json.loads(r['evidencia']);official_url(e['url']);raw=(ROOT/e['archivo']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),e['sha256'])
            original=block_text(selected_version(xml_root(raw).find('.//bloque')))
            self.assertEqual(a['texto'].split(),original.split());self.assertFalse(e['aprobacion_juridica_global'])
            options=json.loads(r['opciones']);self.assertEqual(4,len(set(options)));self.assertEqual(1,options.count(r['respuesta']))
            for alternative in e['alternativas']:
                source=self.db.execute('SELECT texto,hash_texto FROM articulos WHERE id_articulo=?',(alternative['id_articulo'],)).fetchone()
                self.assertIn(alternative['texto'],source['texto']);self.assertEqual(alternative['hash_texto'],source['hash_texto'])
    def test_scope_and_legal_states_are_not_promoted(self):
        for r in self.db.execute("SELECT * FROM ejercicios_literales WHERE estado='texto_contrastado'"):
            self.assertIn(r['id_tema'],[2,7,26]);self.assertEqual('transformacion_literal',r['origen'])
            self.assertGreater(self.db.execute('SELECT count(*) FROM tema_articulo ta JOIN tema_norma tn USING(id_relacion) WHERE ta.id_tema=? AND ta.id_articulo=? AND tn.rango_pendiente=0',(r['id_tema'],r['id_articulo'])).fetchone()[0],0)
        self.assertEqual(0,self.db.execute("SELECT count(*) FROM temas WHERE estado_verificacion='verificado'").fetchone()[0])
        self.assertEqual(0,self.db.execute('SELECT count(*) FROM contenido_ia').fetchone()[0])

if __name__=='__main__':unittest.main()
