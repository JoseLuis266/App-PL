import {describe,it,expect} from 'vitest';
import type {Article,Topic} from './types';
import {exercises,nextMemory,isDue,verifiedArticles,normalizeAnswer} from './study';
// Neutral fixtures exercise mechanics; no fictional legislation is added to the app.
const articles=Array.from({length:4},(_,i)=>({id_articulo:'fixture:'+i,id_norma:'fixture',tipo:'articulo',numero:String(i),rubrica:'Etiqueta de prueba '+i,texto:'Etiqueta de prueba '+i+'\nContenido neutral destinado exclusivamente a pruebas.',texto_xml:'',jerarquia:{},url_fuente:'https://www.boe.es/',hash_texto:'hash'+i,estado:'verificado',notas_fuente:[]} satisfies Article));
const topic:Topic={id_tema:1,titulo_oficial_literal:'Fixture neutral',estado_fuente:'ok',estado_verificacion:'verificado',url_programa:'https://www.caib.es/',localizador:'fixture',articulos:articles.map(a=>a.id_articulo),relaciones:[]};
describe('exercise safety and mechanics',()=>{
 it('never admits pending article or topic or uncertain scope',()=>{expect(verifiedArticles(articles.map(a=>({...a,estado:'pendiente_revision'})),[topic])).toHaveLength(0);expect(exercises(articles,[{...topic,estado_verificacion:'pendiente_revision'}],'test')).toHaveLength(0);expect(exercises(articles,[{...topic,estado_fuente:'rango_pendiente'}],'flashcard')).toHaveLength(0);});
 it('test answers are four distinct verified literal rubrics, exactly one correct',()=>{for(const e of exercises(articles,[topic],'test')){expect(new Set(e.options).size).toBe(4);expect(e.options?.filter(o=>o===e.answer)).toHaveLength(1);expect(e.article.url_fuente).toContain('boe.es');}expect(exercises(articles.slice(0,2),[topic],'test')).toHaveLength(0);});
 it('cloze can restore the original literal fragment',()=>{for(const e of exercises(articles,[topic],'cloze'))expect(e.article.texto).toContain(e.prompt.replace(' [____] ',e.answer));});
 it('flashcards and recall reveal the literal source',()=>{for(const mode of ['flashcard','recall'] as const)for(const e of exercises(articles,[topic],mode))expect(e.answer).toBe(e.article.texto);});
 it('normalizes spacing and case without dropping accents or numbers',()=>{expect(normalizeAnswer('  DÍA  20 ')).toBe('día 20');expect(normalizeAnswer('dia')).not.toBe(normalizeAnswer('día'));});
});
describe('individual adaptive review',()=>{
 it('starts on the chosen date, grows with success, resets on failure',()=>{const now=new Date('2026-01-01T12:00:00Z');const first=nextMemory(articles[0],undefined,true,now);expect(first.interval).toBe(1);expect(first.due).toBe('2026-01-02T12:00:00.000Z');const good=nextMemory(articles[0],first,true,now);expect(good.interval).toBe(2);const failed=nextMemory(articles[0],good,false,now);expect(failed.interval).toBe(1);expect(failed.status).toBe('dificil');expect(failed.first).toBe(first.first);expect(isDue(first,new Date('2026-01-03'))).toBe(true);});
 it('changed source resets the growing interval and pins new hash',()=>{const old=nextMemory(articles[0]);old.interval=40;const result=nextMemory({...articles[0],hash_texto:'changed'},old);expect(result.interval).toBe(1);expect(result.sourceHash).toBe('changed');});
});
