"""Resolve source structural boundaries; never invent or silently narrow ambiguous ranges."""
import json
import re
import unicodedata
from database import connect,insert_dict,export
from network import ROOT


def fold(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text.casefold()) if unicodedata.category(c)!='Mn')


def rank(row):
    title=fold(row['texto']).lstrip()
    for name,level in [('anexo',0),('annex',0),('libro',0),('titulo',1),('titol',1),('capitulo',2),('capitol',2),('subseccion',4),('seccion',3),('seccio',3)]:
        if title.startswith(name+' '):return level
    return None


def source_scope(db,norm,block):
    rows=list(db.execute('SELECT * FROM estructura WHERE id_norma=? AND activo=1 ORDER BY orden',(norm,)))
    start=next((i for i,r in enumerate(rows) if r['bloque_fuente']==block),None)
    if start is None:raise ValueError('Bloque de alcance inexistente/inactivo: '+norm+':'+block)
    depth=rank(rows[start])
    if depth is None:raise ValueError('No se puede determinar jerarquía de '+norm+':'+block)
    end=len(rows)
    for i in range(start+1,len(rows)):
        other=rank(rows[i])
        if rows[i]['tipo_fuente']=='encabezado' and other is not None and other<=depth:
            end=i;break
    blocks={r['bloque_fuente'] for r in rows[start:end]}
    units=[dict(r) for r in db.execute("SELECT * FROM articulos WHERE id_norma=? AND estado!='historico_no_vigente' ORDER BY orden",(norm,)) if r['bloque_fuente'] in blocks]
    if not units:raise ValueError('Alcance sin unidades: '+norm+':'+block)
    return units,rows[start]['texto']


def main():
    db=connect();records=[]
    program=json.loads((ROOT/'data/programa.json').read_text())
    source=program['fuente']['url_final']
    def add(topic,norm,scopes=None,*,pending=False,role='principal',article=None,reason=None):
        if not db.execute('SELECT 1 FROM normas WHERE id_norma=?',(norm,)).fetchone():
            raise ValueError('Norma no importada '+norm)
        if scopes:
            groups=[]
            for block in scopes:
                units,heading=source_scope(db,norm,block);groups.append((units,heading,block))
        elif article:
            units=[dict(r) for r in db.execute("SELECT * FROM articulos WHERE id_norma=? AND bloque_fuente=? AND estado!='historico_no_vigente'",(norm,article))]
            if len(units)!=1:raise ValueError('Artículo no localizado '+norm+':'+article)
            groups=[(units,units[0]['rubrica'],article)]
        else:
            groups=[([dict(r) for r in db.execute("SELECT * FROM articulos WHERE id_norma=? AND estado!='historico_no_vigente' ORDER BY orden",(norm,))], 'Norma completa como referencia; no supone alcance completo verificado.' if pending else 'Norma citada sin delimitación parcial.',None)]
        for units,heading,block in groups:
            nums=[r['numero'] for r in units if r['tipo']=='articulo']
            annex=units[0]['numero'] if units and units[0]['tipo']=='anexo' else None
            relation=dict(id_tema=topic,id_norma=norm,desde_articulo=nums[0] if nums else None,hasta_articulo=nums[-1] if nums else None,
                anexo=annex,rango_pendiente=int(pending),papel=role,
                justificacion=(reason+' ' if reason else '')+heading,fuente_alcance=source+f' [tema {topic}]; '+db.execute('SELECT url_fuente FROM normas WHERE id_norma=?',(norm,)).fetchone()[0]+(('#'+block) if block else ''))
            insert_dict(db,'tema_norma',relation);rel_id=db.execute('SELECT last_insert_rowid()').fetchone()[0]
            for unit in units:insert_dict(db,'tema_articulo',dict(id_tema=topic,id_articulo=unit['id_articulo'],id_relacion=rel_id))
            records.append(dict(**relation,bloque_fuente=block,articulos=[r['id_articulo'] for r in units]))
    with db:
        db.execute('DELETE FROM tema_articulo');db.execute('DELETE FROM tema_norma')
        db.execute("DELETE FROM incidencias WHERE codigo IN('alcance_pendiente','tema17_sin_norma')")
        add(1,'ce',pending=True,reason='Materia conceptual: falta una delimitación inequívoca de los artículos exigibles.')
        add(2,'ce',['ti']);add(3,'ce',['tii','tiii','tiv','tv','tvi','tix']);add(4,'ce',['tviii'])
        add(5,'estatuto',pending=True,reason='La enumeración de instituciones y aspectos del Poder Judicial no permite certificar un rango único sin revisión.')
        add(6,'local',['ci','ciii','civ','cvi','ciii-4'])
        add(7,'trafico',['tpreliminar','ani']);add(7,'trafico',article='a7')
        add(8,'circulacion',['ci','ciii','civ','cv']);add(9,'circulacion',['tii'])
        add(10,'circulacion',['ci-4','cii-4','s1-15'])
        add(11,'conductores',['ci']);add(12,'vehiculos',['ti']);add(13,'vehiculos',['tiii'])
        add(14,'vehiculos',['ci-3','cii-3']);add(15,'vehiculos',['anii']);add(16,'vehiculos',['anxviii'])
        # Support only: the syllabus has no specific normative source for accident taxonomy.
        add(17,'circulacion',['cvi-2'],role='apoyo',reason='Comportamiento en caso de emergencia; no cubre taxonomía didáctica.')
        for row in db.execute("SELECT bloque_fuente FROM articulos WHERE id_norma='trafico' AND tipo='articulo' AND rubrica LIKE '%accidente%' AND estado!='historico_no_vigente'"):
            add(17,'trafico',article=row[0],role='apoyo',reason='Obligaciones en caso de accidente localizadas en la rúbrica oficial.')
        add(17,'penal',['tix','civ-6'],role='apoyo')
        units,_,=source_scope(db,'lecrim','tiii-2')
        for unit in units:
            if 'atestado' in fold(unit['texto']):add(17,'lecrim',article=unit['bloque_fuente'],role='apoyo',reason='Artículo sobre atestados localizado en texto oficial; no es un protocolo completo de accidente.')
        add(18,'policias',['ti','tii','tiv']);add(19,'policias',['ci-5','cii-5','ciii-4'])
        add(20,'marco',pending=True,reason='Texto consolidado CAIB en catalán: extracción PDF y límites concretos pendientes de revisión.')
        add(21,'fcs',['cii','ciii','tv'])
        add(22,'habeas');add(22,'ce',article='a17');add(22,'lecrim',['tiii-2','cii-8','civ-3'],pending=True,
            reason='Relación candidata de policía judicial/detención; el alcance exacto requiere revisión. Se amplía además a la norma completa como referencia pendiente según la regla del usuario.')
        add(22,'lecrim',pending=True,reason='Referencia completa mientras no se confirme la delimitación de detención/policía judicial.')
        add(22,'fcs',article='acincuentaytres',role='apoyo',reason='Funciones de policía judicial de los cuerpos de policía local; artículo cincuenta y tres localizado en la fuente.')
        add(23,'lecrim',['tprimero-2']);add(24,'penal',['ti','tii'])
        add(25,'penal',['ci-11','cii-11','civ-4','cv-3','cvi-3','cix'])
        add(26,'penal',['civ-6']);add(27,'penal',['s1-12'])
        add(28,'datos',['ti','ti-2','ti-3']);add(29,'igualdad',['tp','ti-2','tv'])
        add(30,'lgtbi',['tp','ci-3','ci-7'])
        for topic in range(1,31):
            pending=db.execute('SELECT count(*) FROM tema_norma WHERE id_tema=? AND rango_pendiente=1',(topic,)).fetchone()[0]
            db.execute('UPDATE temas SET estado_fuente=? WHERE id_tema=?',('sin_norma_especifica' if topic==17 else 'rango_pendiente' if pending else 'ok',topic))
            if pending:db.execute('INSERT INTO incidencias(id_tema,codigo,detalle) VALUES(?,?,?)',(topic,'alcance_pendiente','La referencia amplia no acredita que toda la norma sea exigible. Revisar el alcance antes de verificar el tema.'))
        db.execute('INSERT INTO incidencias(id_tema,codigo,detalle) VALUES(17,?,?)',('tema17_sin_norma','El programa no cita norma específica. Solo fuentes de apoyo verificables; definiciones, tipos, causas y secuencia de actuación pendientes de fuente EBAP. No se ha generado contenido IA.'))
    (ROOT/'data/relaciones-temas-fuentes.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    export(db)
    print('Relaciones documentadas:',len(records))


if __name__=='__main__':main()
