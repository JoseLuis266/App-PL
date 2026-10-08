"""Deterministic literal pilots; independent source comparison, no legal paraphrases or IA."""
from datetime import datetime,timezone
import hashlib
import json
import re
from boe import block_text,selected_version,xml_root
from database import connect,export,insert_dict
from network import ROOT,download

PILOTS={2:('ce',list(map(str,range(10,30)))),7:('trafico',None),26:('penal',None)}
PRIORITY={'derechos','libertad','detención','seguridad','judicial','conductor','conductores','propulsión','interurbana','vehículo','vehículos','circulación','municipal','travesías','domicilio','intimidad','publicidad','asociación','elecciones','reeducación','reinserción','igualdad','prisión','riesgo','administrativa','motivada','autorización','constitución','integridad','sanciones','consentimiento','provisional','alcohólicas','psicotrópicas','ciclomotor','ciclomotores'}
STOP={'asimismo','correspondiente','correspondientes','mediante','aquellos','aquellas','aquella','cualquier','cualesquiera','previstos','previstas','dispuesto','establecido','establecida','establecidos','establecidas','necesario','necesaria','necesarios','necesarias','siguiente','siguientes','respecto'}
FOCUS={
 'ce:a12':['dieciocho años'],'ce:a17':['setenta y dos horas'],'ce:a18':['flagrante delito'],
 'ce:a20':['resolución judicial'],'ce:a21':['autorización previa'],'ce:a22':['resolución judicial motivada'],
 'ce:a24':['presunción de inocencia'],'ce:a25':['privación de libertad'],'ce:a27':['obligatoria y gratuita'],
 'ce:a29':['por escrito'],'trafico:a7':['ordenanza municipal de circulación','exceptuadas las travesías','motivos medioambientales'],
 'trafico:ani':['50 cm³','45 km/h','750 kg','ocho plazas como máximo','más de nueve plazas'],
 'penal:a379':['sesenta kilómetros por hora','ochenta kilómetros por hora','0,60 miligramos por litro','1,2 gramos por litro'],
 'penal:a380':['temeridad manifiesta'],'penal:a381':['manifiesto desprecio por la vida de los demás'],
 'penal:a382':['mitad superior'],'penal:a3-2':['sin que concurra riesgo propio o de terceros'],
 'penal:a383':['seis meses a un año'],'penal:a384':['sin haber obtenido nunca permiso o licencia de conducción'],
 'penal:a385bis':['instrumento del delito'],'penal:a385ter':['en un grado']}

def digest(s):return hashlib.sha256(s.encode()).hexdigest()

def fragments(article):
    for match in re.finditer(r'[^\n]+',article['texto']):
        quote=match.group().strip()
        if len(quote)<45 or len(quote)>1800 or re.search(r'\b(?:Derogado|Suprimido)\b',quote,re.I):continue
        offset=match.start()+len(match.group())-len(match.group().lstrip())
        focused=[term for term in FOCUS.get(article['id_articulo'],[]) if quote.count(term)==1]
        # Exact text fragments and spans; punctuation and negations are never changed.
        words=[m.group() for m in re.finditer(r'\b[\wÁÉÍÓÚáéíóúñÑ]{7,}\b',quote) if quote.count(m.group())==1 and m.group().lower() not in STOP]
        concepts=[word for word in words if word.lower() in PRIORITY]
        targets=focused or (concepts[:1] if concepts else words[len(words)//2:len(words)//2+1])
        for answer in targets:
            yield dict(cita=quote,inicio=offset,fin=offset+len(quote),respuesta=answer,inicio_respuesta=quote.index(answer))

def main(refresh=False):
    db=connect();records=[];proofs={};failures=[]
    for topic,(norm,allowed_numbers) in PILOTS.items():
        rows=[dict(r) for r in db.execute("SELECT DISTINCT a.* FROM articulos a JOIN tema_articulo ta USING(id_articulo) JOIN tema_norma tn USING(id_relacion) WHERE ta.id_tema=? AND a.id_norma=? AND a.estado!='historico_no_vigente' AND tn.rango_pendiente=0 AND tn.papel='principal' ORDER BY a.orden",(topic,norm))]
        rows=[a for a in rows if a['tipo'] in ('articulo','anexo') and (allowed_numbers is None or a['numero'] in allowed_numbers)]
        candidates=[]
        for article in rows:
            url=f"https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{db.execute('SELECT id_boe FROM normas WHERE id_norma=?',(norm,)).fetchone()[0]}/texto/bloque/{article['bloque_fuente']}"
            path,meta=download(url,refresh=refresh)
            root=xml_root(path.read_bytes());block=root.find('.//bloque')
            if block is None:raise ValueError('Fuente sin bloque oficial: '+url)
            independent=block_text(selected_version(block))
            if independent.split()!=article['texto'].split():
                failures.append(dict(id_articulo=article['id_articulo'],motivo='Texto distinto a la versión activa; se mantiene excluido'))
                continue
            if digest(article['texto'])!=article['hash_texto']:raise ValueError('Hash de artículo incorrecto')
            evidence=dict(url=url,archivo=meta['archivo'],sha256=meta['sha256'],fecha_contraste=datetime.now(timezone.utc).isoformat(),fecha_descarga=meta['fecha_descarga'],criterio='comparacion_independiente_palabra_por_palabra',aprobacion_juridica_global=False)
            proofs[article['id_articulo']]=evidence
            for fragment in fragments(article):candidates.append(dict(id_tema=topic,id_articulo=article['id_articulo'],hash_texto=article['hash_texto'],**fragment,evidencia=dict(evidence)))
        # Keep all focused passages plus balanced, bounded coverage across source units.
        focused=[c for c in candidates if c['respuesta'] in FOCUS.get(c['id_articulo'],[])]
        regular=[c for c in candidates if c not in focused]
        balanced=[]
        by_article={a['id_articulo']:[c for c in regular if c['id_articulo']==a['id_articulo']] for a in rows}
        for i in range(max((len(v) for v in by_article.values()),default=0)):
            for values in by_article.values():
                if i<len(values):balanced.append(values[i])
        selected=(focused+balanced)[:60]
        for c in selected:
            # Alternatives are literal tokens from the contrasted pilot corpus. They are choices,
            # never presented as legal assertions. Their separate locations are retained.
            alternatives=[]
            pool=[x for x in selected if x['respuesta']!=c['respuesta']]
            for other in pool:
                term=other['respuesta']
                if term not in alternatives and term not in c['respuesta'] and c['respuesta'] not in term:
                    alternatives.append(term)
                if len(alternatives)==3:break
            options=[c['respuesta'],*alternatives] if len(alternatives)==3 else []
            c['evidencia']['alternativas']=[dict(texto=o,id_articulo=next(x['id_articulo'] for x in selected if x['respuesta']==o),hash_texto=next(x['hash_texto'] for x in selected if x['respuesta']==o)) for o in alternatives]
            c['id_ejercicio']='literal:'+digest(str(topic)+'|'+c['id_articulo']+'|'+c['hash_texto']+'|'+str(c['inicio'])+'|'+str(c['inicio_respuesta']))[:24]
            c['opciones']=json.dumps(options,ensure_ascii=False)
            c['evidencia']=json.dumps(c['evidencia'],ensure_ascii=False)
            c['estado']='texto_contrastado'
            records.append(c)
        print('Piloto',topic,':',len(rows),'unidades consultadas;',len(selected),'pasajes seleccionados',flush=True)
    with db:
        current={c['id_ejercicio'] for c in records}
        for old in db.execute("SELECT id_ejercicio FROM ejercicios_literales WHERE estado='texto_contrastado'").fetchall():
            if old[0] not in current:db.execute("UPDATE ejercicios_literales SET estado='retirado' WHERE id_ejercicio=?",(old[0],))
        for c in records:
            if db.execute('SELECT 1 FROM ejercicios_literales WHERE id_ejercicio=?',(c['id_ejercicio'],)).fetchone():continue
            insert_dict(db,'ejercicios_literales',c)
    report=dict(fecha=datetime.now(timezone.utc).isoformat(),pilotos=list(PILOTS),pasajes=len(records),unidades_contrastadas=len(proofs),fuentes=proofs,excluidos=failures,origen='transformacion_literal',contenido_ia_generado=0,revision_juridica_global='pendiente')
    (ROOT/'data/pilotos-estudio-informe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    export(db);print('Pasajes contrastados',len(records),'; estados jurídicos globales conservados.')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');args=parser.parse_args();main(args.refresh)
