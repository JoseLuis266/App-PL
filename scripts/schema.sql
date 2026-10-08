PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS ejercicios_literales (
 id_ejercicio TEXT PRIMARY KEY,
 id_tema INTEGER NOT NULL REFERENCES temas,
 id_articulo TEXT NOT NULL REFERENCES articulos,
 hash_texto TEXT NOT NULL,
 cita TEXT NOT NULL, inicio INTEGER NOT NULL, fin INTEGER NOT NULL,
 respuesta TEXT NOT NULL, inicio_respuesta INTEGER NOT NULL,
 opciones TEXT NOT NULL CHECK(json_valid(opciones)),
 evidencia TEXT NOT NULL CHECK(json_valid(evidencia)),
 origen TEXT NOT NULL DEFAULT 'transformacion_literal' CHECK(origen='transformacion_literal'),
 estado TEXT NOT NULL CHECK(estado IN ('texto_contrastado','retirado'))
);
CREATE TABLE IF NOT EXISTS normas (
 id_norma TEXT PRIMARY KEY, id_boe TEXT UNIQUE, titulo_oficial TEXT NOT NULL,
 rango TEXT, fecha_disposicion TEXT, fecha_publicacion TEXT, fecha_consolidacion TEXT,
 fecha_actualizacion_api TEXT, fecha_vigencia TEXT, url_fuente TEXT NOT NULL,
 fuente TEXT NOT NULL CHECK(fuente IN ('BOE','BOIB')), hash_texto TEXT,
 fecha_descarga TEXT, estado TEXT NOT NULL DEFAULT 'pendiente',
 estatus_derogacion TEXT, estado_consolidacion TEXT, clase_texto TEXT NOT NULL DEFAULT 'consolidado',
 archivo_bruto TEXT, hash_archivo TEXT
);
CREATE TABLE IF NOT EXISTS norma_modificaciones (
 id_norma TEXT NOT NULL REFERENCES normas, norma_modificadora TEXT NOT NULL,
 fecha TEXT, url TEXT NOT NULL, relacion TEXT NOT NULL, descripcion_literal TEXT NOT NULL, fecha_fuente TEXT,
 PRIMARY KEY(id_norma,norma_modificadora,relacion,descripcion_literal)
);
CREATE TABLE IF NOT EXISTS articulos (
 id_articulo TEXT PRIMARY KEY, id_norma TEXT NOT NULL REFERENCES normas,
 bloque_fuente TEXT NOT NULL, orden INTEGER NOT NULL,
 tipo TEXT NOT NULL CHECK(tipo IN ('articulo','disposicion','anexo','preambulo')),
 numero TEXT, rubrica TEXT NOT NULL, texto TEXT NOT NULL CHECK(length(texto)>0),
 jerarquia TEXT NOT NULL, url_fuente TEXT NOT NULL, hash_texto TEXT NOT NULL,
 texto_xml TEXT NOT NULL, fecha_publicacion_version TEXT, fecha_vigencia_version TEXT,
 norma_version TEXT, estado TEXT NOT NULL DEFAULT 'pendiente_revision', notas_fuente TEXT NOT NULL DEFAULT '[]',
 UNIQUE(id_norma,bloque_fuente), UNIQUE(id_norma,orden)
);
CREATE TABLE IF NOT EXISTS norma_referencias (
 id_norma TEXT NOT NULL REFERENCES normas, norma_modificadora TEXT NOT NULL,
 fecha TEXT, url TEXT NOT NULL, relacion TEXT NOT NULL, descripcion_literal TEXT NOT NULL, fecha_fuente TEXT,
 PRIMARY KEY(id_norma,norma_modificadora,relacion,descripcion_literal)
);
CREATE TABLE IF NOT EXISTS estructura (
 id_norma TEXT NOT NULL REFERENCES normas, bloque_fuente TEXT NOT NULL,
 orden INTEGER NOT NULL, tipo_fuente TEXT, titulo TEXT NOT NULL, texto_xml TEXT NOT NULL,
 texto TEXT NOT NULL, jerarquia TEXT NOT NULL, activo INTEGER NOT NULL DEFAULT 1,
 PRIMARY KEY(id_norma,bloque_fuente)
);
CREATE TABLE IF NOT EXISTS temas (
 id_tema INTEGER PRIMARY KEY CHECK(id_tema BETWEEN 1 AND 30),
 titulo_oficial_literal TEXT NOT NULL, bloque TEXT NOT NULL DEFAULT 'comun' CHECK(bloque='comun'),
 estado_fuente TEXT NOT NULL CHECK(estado_fuente IN ('ok','sin_norma_especifica','rango_pendiente')),
 estado_verificacion TEXT NOT NULL DEFAULT 'pendiente_revision',
 programa_version TEXT NOT NULL, url_programa TEXT NOT NULL, localizador TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tema_norma (
 id_relacion INTEGER PRIMARY KEY, id_tema INTEGER NOT NULL REFERENCES temas,
 id_norma TEXT NOT NULL REFERENCES normas, desde_articulo TEXT, hasta_articulo TEXT, anexo TEXT,
 rango_pendiente INTEGER NOT NULL CHECK(rango_pendiente IN(0,1)),
 papel TEXT NOT NULL CHECK(papel IN('principal','apoyo','referenciada')),
 justificacion TEXT NOT NULL, fuente_alcance TEXT NOT NULL,
 UNIQUE(id_tema,id_norma,desde_articulo,hasta_articulo,anexo,papel)
);
CREATE TABLE IF NOT EXISTS tema_articulo (
 id_tema INTEGER NOT NULL REFERENCES temas, id_articulo TEXT NOT NULL REFERENCES articulos,
 id_relacion INTEGER NOT NULL REFERENCES tema_norma,
 PRIMARY KEY(id_tema,id_articulo,id_relacion)
);
CREATE TABLE IF NOT EXISTS contenido_ia (
 id INTEGER PRIMARY KEY, id_tema INTEGER NOT NULL REFERENCES temas,
 tipo TEXT NOT NULL CHECK(tipo IN('resumen','esquema','flashcard','cloze','pregunta_test','guion_audio')),
 contenido TEXT NOT NULL, origen TEXT NOT NULL DEFAULT 'IA' CHECK(origen='IA'),
 revisado INTEGER NOT NULL DEFAULT 0 CHECK(revisado IN(0,1)),
 articulos_fuente TEXT NOT NULL CHECK(json_valid(articulos_fuente)), fecha_generacion TEXT NOT NULL,
 aviso TEXT
);
CREATE TABLE IF NOT EXISTS contenido_ia_articulo (
 id INTEGER NOT NULL REFERENCES contenido_ia, id_articulo TEXT NOT NULL REFERENCES articulos,
 PRIMARY KEY(id,id_articulo)
);
CREATE TABLE IF NOT EXISTS verificaciones (
 id INTEGER PRIMARY KEY, id_norma TEXT REFERENCES normas, fecha TEXT NOT NULL,
 resultado TEXT NOT NULL, informe_json TEXT NOT NULL CHECK(json_valid(informe_json))
);
CREATE TABLE IF NOT EXISTS incidencias (
 id INTEGER PRIMARY KEY, id_tema INTEGER REFERENCES temas, id_norma TEXT REFERENCES normas,
 codigo TEXT NOT NULL, detalle TEXT NOT NULL, estado TEXT NOT NULL DEFAULT 'pendiente'
);
CREATE TABLE IF NOT EXISTS versiones (
 id_version TEXT PRIMARY KEY, id_norma TEXT NOT NULL REFERENCES normas,
 fecha TEXT NOT NULL, hash_archivo TEXT NOT NULL, archivo_bruto TEXT NOT NULL,
 estado TEXT NOT NULL CHECK(estado IN('activa','candidata')), datos_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS recursos (
 id_norma TEXT NOT NULL REFERENCES normas, url TEXT NOT NULL, archivo TEXT,
 sha256 TEXT, estado TEXT NOT NULL DEFAULT 'pendiente', PRIMARY KEY(id_norma,url)
);
CREATE VIRTUAL TABLE IF NOT EXISTS articulos_fts USING fts5(rubrica,texto,content='articulos',content_rowid='rowid',tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS articulos_ai AFTER INSERT ON articulos BEGIN
 INSERT INTO articulos_fts(rowid,rubrica,texto) VALUES(new.rowid,new.rubrica,new.texto);
END;
CREATE TRIGGER IF NOT EXISTS articulos_ad AFTER DELETE ON articulos BEGIN
 INSERT INTO articulos_fts(articulos_fts,rowid,rubrica,texto) VALUES('delete',old.rowid,old.rubrica,old.texto);
END;
CREATE TRIGGER IF NOT EXISTS articulos_au AFTER UPDATE ON articulos BEGIN
 INSERT INTO articulos_fts(articulos_fts,rowid,rubrica,texto) VALUES('delete',old.rowid,old.rubrica,old.texto);
 INSERT INTO articulos_fts(rowid,rubrica,texto) VALUES(new.rowid,new.rubrica,new.texto);
END;
