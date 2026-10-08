import {describe,it,expect} from 'vitest';
import {literalExercises,matchingRound,isLiteralExerciseCurrent} from './study';
import type {Article,Topic,LiteralCard} from './types';
const quote='Pasaje neutral destinado exclusivamente a comprobar mecanismos de estudio.';
const article:Article={id_articulo:'fixture:1',id_norma:'fixture',tipo:'articulo',numero:'1',rubrica:'Fixture neutral',texto:quote,texto_xml:'',jerarquia:{},url_fuente:'https://www.boe.es/',hash_texto:'fixture-hash',estado:'pendiente_revision',notas_fuente:[]};
const topic:Topic={id_tema:2,titulo_oficial_literal:'Fixture',estado_fuente:'ok',estado_verificacion:'pendiente_revision',url_programa:'https://www.caib.es/',localizador:'fixture',articulos:[article.id_articulo],relaciones:[]};
const card:LiteralCard={id_ejercicio:'fixture-literal',id_tema:2,id_articulo:article.id_articulo,hash_texto:article.hash_texto,cita:quote,inicio:0,fin:quote.length,respuesta:'neutral',inicio_respuesta:quote.indexOf('neutral'),opciones:['neutral','mecanismos','estudio','comprobar'],estado:'texto_contrastado',origen:'transformacion_literal',evidencia:{url:'https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/fixture/texto/bloque/1',archivo:'fixture.xml',sha256:'fixture-sha',fecha_contraste:'2026-10-08T12:00:00Z',criterio:'comparacion_independiente_palabra_por_palabra',aprobacion_juridica_global:false}};
describe('granular literal-source practice',()=>{
 it('allows only proven passages without promoting the topic juridically',()=>{const result=literalExercises([card],[article],[topic],'test');expect(result).toHaveLength(1);expect(topic.estado_verificacion).toBe('pendiente_revision');expect(result[0].prompt.replace(' [____] ',result[0].answer)).toBe(quote);expect(result[0].quote).toBe(quote);});
 it('blocks changed text, wrong quote spans, retired content and ambiguous options',()=>{
  for(const changed of [{...card,hash_texto:'changed'},{...card,inicio:1},{...card,estado:'retirado' as const},{...card,inicio_respuesta:0},{...card,opciones:['neutral','neutral','otro','más']},{...card,evidencia:{...card.evidencia,url:'https://example.test'}}])expect(literalExercises([changed],[article],[topic],'test')).toHaveLength(0);
  expect(literalExercises([card],[{...article,estado:'historico_no_vigente'}],[topic],'cloze')).toHaveLength(0);
  expect(literalExercises([card],[article],[{...topic,estado_fuente:'rango_pendiente'}],'flashcard')).toHaveLength(0);
 });
 it('matches unique article references and exact annex concepts without repeating a reference',()=>{
  const items=literalExercises([card],[article],[topic],'match');expect(matchingRound([...items,...items],4)).toHaveLength(1);
  const definition='1. Concepto neutral. Definición neutral destinada exclusivamente a las pruebas.';
  const annex={...article,tipo:'anexo',rubrica:'ANEXO',texto:definition};
  const c={...card,cita:definition,inicio:0,fin:definition.length,inicio_respuesta:definition.indexOf('neutral')};
  const exercise=literalExercises([c],[annex],[topic],'match')[0];expect(exercise.prompt).toBe('Definición neutral destinada exclusivamente a las pruebas.');expect(exercise.referenceLabel).toBe('Concepto neutral · ANEXO, concepto 1');
 });
 it('revalidates stored prompts, answers, options and source quotes before resuming',()=>{
  const e=literalExercises([card],[article],[topic],'test')[0];expect(isLiteralExerciseCurrent(e,[card])).toBe(true);
  for(const changed of [{...e,prompt:'Alterado'},{...e,answer:'otra'},{...e,quote:'cita alterada'},{...e,options:['neutral','neutral','otro','más']},{...e,article:{...e.article,hash_texto:'changed'}}])expect(isLiteralExerciseCurrent(changed,[card])).toBe(false);
 });
});
