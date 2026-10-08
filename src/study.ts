import type {Article,Topic,Exercise,Mode,Memory,LiteralCard} from './types';
export function literalExercises(bank:LiteralCard[],articles:Article[],topics:Topic[],mode:Mode):Exercise[]{
 const byId=new Map(articles.map(a=>[a.id_articulo,a]));
 return bank.flatMap(card=>{
  const a=byId.get(card.id_articulo),topic=topics.find(t=>t.id_tema===card.id_tema);
  if(!a||!topic||topic.estado_fuente!=='ok'||!topic.articulos.includes(a.id_articulo)||a.estado==='historico_no_vigente'||card.estado!=='texto_contrastado'||card.origen!=='transformacion_literal'||a.hash_texto!==card.hash_texto||a.texto.slice(card.inicio,card.fin)!==card.cita||card.cita.slice(card.inicio_respuesta,card.inicio_respuesta+card.respuesta.length)!==card.respuesta||card.evidencia.criterio!=='comparacion_independiente_palabra_por_palabra'||!/^https:\/\/www\.boe\.es\//.test(card.evidencia.url))return [];
  if(mode==='test'&&(card.opciones.length!==4||new Set(card.opciones).size!==4||card.opciones.filter(o=>o===card.respuesta).length!==1))return [];
  const prompt=card.cita.slice(0,card.inicio_respuesta)+' [____] '+card.cita.slice(card.inicio_respuesta+card.respuesta.length);
  const definition=a.tipo==='anexo'?card.cita.match(/^(\d+)\.\s+([^.:]+)[.:]\s+([\s\S]+)$/):null;
  const referenceLabel=definition?`${definition[2].trim()} · ${a.rubrica}, concepto ${definition[1]}`:`${a.id_norma.toUpperCase()} · ${a.rubrica}`;
  return [{id:card.id_ejercicio+':'+mode,literalId:card.id_ejercicio,article:a,topicIds:[card.id_tema],mode,prompt:mode==='match'?(definition?.[3]??card.cita):prompt,answer:mode==='match'?referenceLabel:card.respuesta,options:mode==='test'?card.opciones:undefined,quote:card.cita,sourceCheck:card.evidencia.fecha_contraste,matchKey:definition?`${a.id_articulo}:concepto-${definition[1]}`:a.id_articulo,referenceLabel,explanation:'Este es el pasaje literal contrastado con el BOE. La comprobación de fuente no certifica la revisión jurídica global del tema.'}];
 });
}
export function shuffled<T>(items:T[]):T[]{const result=[...items];for(let i=result.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[result[i],result[j]]=[result[j],result[i]];}return result;}
export function matchingRound(items:Exercise[],size=4){const ids=new Set<string>();return shuffled(items).filter(e=>{const key=e.matchKey??e.article.id_articulo;if(ids.has(key))return false;ids.add(key);return true;}).slice(0,size);}
export function isLiteralExerciseCurrent(e:Exercise,bank:LiteralCard[]){
 const c=bank.find(c=>c.id_ejercicio===e.literalId&&c.hash_texto===e.article.hash_texto&&c.estado==='texto_contrastado');
 if(!c||c.id_articulo!==e.article.id_articulo||e.quote!==c.cita||e.topicIds.length!==1||e.topicIds[0]!==c.id_tema)return false;
 if((c.rubrica_fuente&&e.article.rubrica!==c.rubrica_fuente)||(c.url_fuente&&e.article.url_fuente!==c.url_fuente)||(c.id_norma_fuente&&e.article.id_norma!==c.id_norma_fuente)||(c.tipo_fuente&&e.article.tipo!==c.tipo_fuente))return false;
 const topic={id_tema:c.id_tema,estado_fuente:'ok',articulos:[c.id_articulo]} as Topic;
 const expected=literalExercises([c],[e.article],[topic],e.mode)[0];
 if(!expected||e.prompt!==expected.prompt||e.answer!==expected.answer||e.explanation!==expected.explanation||e.sourceCheck!==expected.sourceCheck)return false;
 return e.mode!=='test'||(e.options?.length===4&&new Set(e.options).size===4&&e.options.every(o=>expected.options?.includes(o)));
}
export function verifiedArticles(articles:Article[],topics:Topic[]){return articles.filter(a=>a.tipo==='articulo'&&a.estado==='verificado'&&topics.some(t=>t.estado_verificacion==='verificado'&&t.estado_fuente==='ok'&&t.articulos.includes(a.id_articulo)));}
export function exercises(articles:Article[],topics:Topic[],mode:Mode):Exercise[]{
 const eligible=verifiedArticles(articles,topics);
 return eligible.flatMap((a,index)=>{
  const common={id:a.id_articulo+':'+mode,article:a,topicIds:topics.filter(t=>t.estado_verificacion==='verificado'&&t.articulos.includes(a.id_articulo)).map(t=>t.id_tema),mode,explanation:'Comprueba el texto literal del artículo y su fuente oficial.'};
  if(mode==='test'||mode==='match'){
   const others=[...new Set(eligible.filter(b=>b.id_articulo!==a.id_articulo&&b.rubrica!==a.rubrica).map(b=>b.rubrica))].slice(0,3);
   if(others.length<3)return [];
   const options=[a.rubrica,...others];const shift=index%4;const ordered=[...options.slice(shift),...options.slice(0,shift)];
   return [{...common,prompt:`Relaciona el artículo ${a.numero} (${a.id_norma}) con su rúbrica literal.`,answer:a.rubrica,options:ordered}];
  }
  if(mode==='cloze'){
   const literal=a.texto.split('\n').filter(s=>s.trim()&&s.trim()!==a.rubrica).slice(0,2).join('\n');
   const matches=[...literal.matchAll(/\b\d+\b|[\p{L}]{7,}/gu)];const match=matches[Math.floor(matches.length/2)];
   if(!match||match.index===undefined)return [];
   return [{...common,prompt:literal.slice(0,match.index)+' [____] '+literal.slice(match.index+match[0].length),answer:match[0]}];
  }
  return [{...common,prompt:`Recuerda el contenido de ${a.rubrica} (${a.id_norma}).`,answer:a.texto}];
 });
}
export function nextMemory(article:Pick<Article,'id_articulo'|'hash_texto'>,old?:Memory,success=true,now=new Date()):Memory{
 const changed=!!old&&old.sourceHash!==article.hash_texto;
 const repetitions=success&&!changed?(old?.repetitions??0)+1:0;
 const interval=success&&!changed?(old?Math.min(180,Math.max(1,Math.round(old.interval*2.2))):1):1;
 const due=new Date(now);due.setDate(due.getDate()+interval);
 return {articleId:article.id_articulo,first:old?.first??now.toISOString(),last:now.toISOString(),due:due.toISOString(),interval,repetitions,difficulty:!success,status:!success?'dificil':repetitions>=4?'dominado':'memorizado',sourceHash:article.hash_texto};
}
export function isDue(m:Memory,now=new Date()){return new Date(m.due)<=now;}
export function normalizeAnswer(s:string){return s.normalize('NFC').trim().toLocaleLowerCase('es').replace(/\s+/g,' ');}
