"""Negative and integration tests use archived official sources, never app seed fiction."""
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from boe import parse_norm,selected_version,canonical_title
from database import connect
from import_boe import import_one
from network import ROOT,official_url


class ImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.norm=json.loads((ROOT/'data/catalogo.json').read_text())[0]
        rows=json.loads((ROOT/'data/descargas.json').read_text())
        cls.sources={r['endpoint']:r for r in rows if r['id_norma']=='ce' and not r.get('error')}
        cls.blobs={k:(ROOT/r['archivo']).read_bytes() for k,r in cls.sources.items()}

    def parse(self,**replacements):
        b=dict(self.blobs,**replacements)
        return parse_norm(self.norm,b['metadatos'],b['texto'],b['texto/indice'],b['analisis'])

    def test_real_source_index(self):
        d=self.parse()
        self.assertEqual(169,sum(a['tipo']=='articulo' for a in d['articles']))
        self.assertEqual(210,len(d['structure']))
        self.assertIn('Estado social y democrático',next(a['texto'] for a in d['articles'] if a['numero']=='1'))

    def test_missing_block_rejected(self):
        r=ET.fromstring(self.blobs['texto']);parent=r.find('.//texto');parent.remove(parent[3])
        with self.assertRaisesRegex(ValueError,'Índice/texto'):self.parse(texto=ET.tostring(r))

    def test_duplicate_block_rejected(self):
        r=ET.fromstring(self.blobs['texto']);parent=r.find('.//texto');parent.append(copy.deepcopy(parent[3]))
        with self.assertRaisesRegex(ValueError,'Índice/texto'):self.parse(texto=ET.tostring(r))

    def test_wrong_title_rejected(self):
        r=ET.fromstring(self.blobs['metadatos']);r.find('.//titulo').text='TEST WRONG TITLE'
        with self.assertRaisesRegex(ValueError,'Título discordante'):self.parse(metadatos=ET.tostring(r))

    def test_wrong_identity_rejected(self):
        r=ET.fromstring(self.blobs['metadatos']);r.find('.//identificador').text='BOE-A-0000-0'
        with self.assertRaisesRegex(ValueError,'Identificador'):self.parse(metadatos=ET.tostring(r))

    def test_empty_article_rejected(self):
        r=ET.fromstring(self.blobs['texto']);block=r.find('.//bloque[@id="a1"]')
        for version in block.findall('version'):
            for child in list(version):version.remove(child)
        with self.assertRaisesRegex(ValueError,'Unidad vacía'):self.parse(texto=ET.tostring(r))

    def test_future_version_not_selected(self):
        r=ET.fromstring(self.blobs['texto']);block=r.find('.//bloque[@id="a1"]')
        version=copy.deepcopy(block.find('version'));version.set('fecha_vigencia','29990101');block.append(version)
        self.assertNotEqual('29990101',selected_version(block).get('fecha_vigencia'))

    def test_source_allowlist(self):
        for url in ['https://reisan.net/a','https://app.reisan.net/a','http://www.boe.es/a','https://www.boe.es.evil.test/a','https://user:pass@www.boe.es/a']:
            with self.assertRaises(ValueError):official_url(url)
        self.assertEqual('https://www.boe.es/a',official_url('https://www.boe.es/a'))

    def test_sql_fts_and_repeatability(self):
        with tempfile.TemporaryDirectory() as td:
            db=connect(Path(td)/'test.db')
            self.assertEqual('importado',import_one(db,self.norm,self.sources,sample_network=False))
            before=db.execute('SELECT count(*) FROM articulos').fetchone()[0]
            self.assertEqual('sin_cambios',import_one(db,self.norm,self.sources,sample_network=False))
            self.assertEqual(before,db.execute('SELECT count(*) FROM articulos').fetchone()[0])
            self.assertGreater(db.execute("SELECT count(*) FROM articulos_fts WHERE articulos_fts MATCH 'democrático'").fetchone()[0],0)
            self.assertEqual([],db.execute('PRAGMA foreign_key_check').fetchall())

    def test_updates_require_explicit_approval(self):
        with tempfile.TemporaryDirectory() as td:
            db=connect(Path(td)/'test.db');import_one(db,self.norm,self.sources,sample_network=False)
            previous=db.execute("SELECT hash_texto FROM normas WHERE id_norma='ce'").fetchone()[0]
            # Deliberately altered test-only snapshot, never seed/app content.
            root=ET.fromstring(self.blobs['texto']);root.find('.//bloque[@id="a1"]/version/p').text+=' TEST ONLY CHANGE'
            changed=ET.tostring(root);file=Path(td)/'negative-test.xml';file.write_bytes(changed)
            sources=copy.deepcopy(self.sources);sources['texto']['archivo']=str(file)
            sources['texto']['sha256']=hashlib.sha256(changed).hexdigest()
            self.assertEqual('candidata',import_one(db,self.norm,sources,sample_network=False))
            self.assertEqual(previous,db.execute("SELECT hash_texto FROM normas WHERE id_norma='ce'").fetchone()[0])
            self.assertEqual(1,db.execute("SELECT count(*) FROM versiones WHERE estado='candidata'").fetchone()[0])
            self.assertGreater(db.execute('SELECT count(*) FROM articulos').fetchone()[0],0)

    def test_tampered_archive_hash_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            db=connect(Path(td)/'test.db');sources=copy.deepcopy(self.sources)
            sources['texto']['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'Archivo bruto alterado'):
                import_one(db,self.norm,sources,sample_network=False)

    def test_generated_official_separation(self):
        with tempfile.TemporaryDirectory() as td:
            db=connect(Path(td)/'test.db')
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO contenido_ia(id_tema,tipo,contenido,origen,revisado,articulos_fuente,fecha_generacion) VALUES(1,'resumen','TEST','oficial',0,'[]','2026-10-08')")

    def test_title_normalization_does_not_remove_words(self):
        self.assertNotEqual(canonical_title('Ley 4/2013.'),canonical_title('Ley 4/2017.'))


if __name__=='__main__':unittest.main()
