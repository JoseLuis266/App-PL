import json
import os
import sqlite3
from network import ROOT


def connect(path=None):
    db = sqlite3.connect(path or os.environ.get('PLSTUDY_DB') or ROOT/'temario.db',timeout=30)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript((ROOT/'scripts/schema.sql').read_text())
    # Additive migration for existing initial imports.
    if 'notas_fuente' not in [r[1] for r in db.execute('PRAGMA table_info(articulos)')]:
        db.execute("ALTER TABLE articulos ADD COLUMN notas_fuente TEXT NOT NULL DEFAULT '[]'")
    if 'activo' not in [r[1] for r in db.execute('PRAGMA table_info(estructura)')]:
        db.execute('ALTER TABLE estructura ADD COLUMN activo INTEGER NOT NULL DEFAULT 1')
    for table in ['norma_modificaciones','norma_referencias']:
        if 'fecha_fuente' not in [r[1] for r in db.execute('PRAGMA table_info('+table+')')]:
            db.execute('ALTER TABLE '+table+' ADD COLUMN fecha_fuente TEXT')
    return db


def insert_dict(db,table,row):
    keys=list(row)
    db.execute(f"INSERT INTO {table} ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",[row[k] for k in keys])


def export(db):
    from pathlib import Path
    target=Path(os.environ.get('PLSTUDY_EXPORT') or ROOT/'export');target.mkdir(parents=True,exist_ok=True)
    tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'articulos_fts%'")]
    for table in tables:
        rows=[dict(row) for row in db.execute(f'SELECT * FROM {table} ORDER BY rowid')]
        (target/(table+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
