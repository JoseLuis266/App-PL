import type {Attempt,Memory,StudySession} from './types';
import {nextMemory} from './study';
const DB='pl-study-personal';
export function openPersonal():Promise<IDBDatabase>{return new Promise((resolve,reject)=>{const req=indexedDB.open(DB,2);req.onupgradeneeded=()=>{const db=req.result;if(!db.objectStoreNames.contains('memory'))db.createObjectStore('memory',{keyPath:'articleId'});if(!db.objectStoreNames.contains('attempts'))db.createObjectStore('attempts',{keyPath:'id'});if(!db.objectStoreNames.contains('sessions'))db.createObjectStore('sessions',{keyPath:'id'});};req.onsuccess=()=>{req.result.onversionchange=()=>req.result.close();resolve(req.result);};req.onerror=()=>reject(req.error);req.onblocked=()=>reject(Error('Cierra otras pestañas de PL Study para actualizar tu almacenamiento sin perder datos.'));});}
export async function getAll<T>(store:'memory'|'attempts'|'sessions'):Promise<T[]>{const db=await openPersonal();return new Promise((resolve,reject)=>{const tx=db.transaction(store,'readonly'),req=tx.objectStore(store).getAll();let result:T[]=[];req.onsuccess=()=>{result=req.result;};tx.oncomplete=()=>{db.close();resolve(result);};tx.onerror=()=>{db.close();reject(tx.error);};});}
export async function put(store:'memory'|'attempts'|'sessions',value:Memory|Attempt|StudySession){const db=await openPersonal();return new Promise<void>((resolve,reject)=>{const tx=db.transaction(store,'readwrite');tx.objectStore(store).put(value);tx.oncomplete=()=>{db.close();resolve();};tx.onerror=()=>{db.close();reject(tx.error);};tx.onabort=()=>{db.close();reject(tx.error);};});}
export async function saveAttempt(attempt:Attempt,memory?:Memory){const db=await openPersonal();return new Promise<void>((resolve,reject)=>{const tx=db.transaction(['attempts','memory'],'readwrite');tx.objectStore('attempts').add(attempt);if(memory)tx.objectStore('memory').put(memory);tx.oncomplete=()=>{db.close();resolve();};tx.onerror=()=>{db.close();reject(tx.error);};tx.onabort=()=>{db.close();reject(tx.error);};});}
export async function saveStudyAnswers(attempts:Attempt[],session:StudySession){
 const db=await openPersonal();
 return new Promise<void>((resolve,reject)=>{
  const tx=db.transaction(['attempts','memory','sessions'],'readwrite');
  const groups=new Map<string,Attempt[]>();
  for(const attempt of attempts){tx.objectStore('attempts').add(attempt);groups.set(attempt.articleId,[...(groups.get(attempt.articleId)??[]),attempt]);}
  // Several annex concepts may share one source unit. Schedule that unit once per round,
  // keeping it difficult if any of its attempts failed.
  for(const [articleId,group] of groups){
   const last=group[group.length-1],memory=tx.objectStore('memory').get(articleId);
   memory.onsuccess=()=>{if(memory.result)tx.objectStore('memory').put(nextMemory({id_articulo:articleId,hash_texto:last.sourceHash},memory.result,group.every(a=>a.success),new Date(last.date)));};
  }
  tx.objectStore('sessions').put(session);
  tx.oncomplete=()=>{db.close();resolve();};tx.onerror=()=>{db.close();reject(tx.error);};tx.onabort=()=>{db.close();reject(tx.error);};
 });
}
export async function backup(){return {format:'pl-study-personal',version:1,created:new Date().toISOString(),memory:await getAll<Memory>('memory'),attempts:await getAll<Attempt>('attempts'),sessions:await getAll<StudySession>('sessions')};}
export async function restore(input:unknown){
 const x=input as {format?:string;version?:number;memory?:unknown[];attempts?:unknown[];sessions?:unknown[]};
 if(x?.format!=='pl-study-personal'||x.version!==1||!Array.isArray(x.memory)||!Array.isArray(x.attempts))throw Error('Formato de copia no válido.');
 const date=(v:unknown)=>typeof v==='string'&&Number.isFinite(Date.parse(v));
 const memories=x.memory as Memory[],attempts=x.attempts as Attempt[],sessions=(x.sessions??[]) as StudySession[];
 const modes=['test','flashcard','cloze','match','recall'];
 if(!Array.isArray(sessions)||sessions.some(s=>!s||typeof s.id!=='string'||!date(s.created)||!date(s.updated)||!modes.includes(s.mode)||!['active','completed'].includes(s.status)||!Array.isArray(s.questions)||s.questions.length>100||s.questions.length===0||!Number.isInteger(s.index)||s.index<0||s.index>s.questions.length||s.questionCount!==s.questions.length||!Array.isArray(s.answers)||s.answers.length>s.questions.length||s.answers.some(a=>!a||typeof a.exerciseId!=='string'||typeof a.chosen!=='string'||typeof a.success!=='boolean'||!s.questions.some(q=>q.id===a.exerciseId))||s.questions.some(e=>!e||typeof e.id!=='string'||!modes.includes(e.mode)||typeof e.prompt!=='string'||typeof e.answer!=='string'||!e.article||typeof e.article.id_articulo!=='string'||typeof e.article.hash_texto!=='string'||typeof e.article.texto!=='string'||typeof e.article.url_fuente!=='string'||!Array.isArray(e.topicIds)||e.topicIds.some(n=>!Number.isInteger(n)||n<1||n>30)||(e.options!==undefined&&(!Array.isArray(e.options)||e.options.some(o=>typeof o!=='string'))))))throw Error('La copia contiene sesiones no válidas. No se ha importado.');
 if(memories.some(m=>!m||typeof m.articleId!=='string'||!date(m.first)||!date(m.last)||!date(m.due)||!Number.isFinite(m.interval)||m.interval<1||!Number.isInteger(m.repetitions)||m.repetitions<0||!['memorizado','dificil','dominado'].includes(m.status)||typeof m.sourceHash!=='string'||typeof m.difficulty!=='boolean')||attempts.some(a=>!a||typeof a.id!=='string'||!date(a.date)||typeof a.articleId!=='string'||!Array.isArray(a.topicIds)||a.topicIds.some(n=>!Number.isInteger(n)||n<1||n>30)||typeof a.success!=='boolean'||![a.question,a.chosen,a.correct,a.sourceHash,a.sourceUrl].every(v=>typeof v==='string')||!['test','flashcard','cloze','match','recall'].includes(a.mode)))throw Error('La copia contiene registros no válidos. No se ha importado.');
 const db=await openPersonal();
 try{await new Promise<void>((resolve,reject)=>{const tx=db.transaction(['memory','attempts','sessions'],'readwrite');for(const m of memories){const req=tx.objectStore('memory').get(m.articleId);req.onsuccess=()=>{if(!req.result)tx.objectStore('memory').add(m);};}for(const a of attempts){const req=tx.objectStore('attempts').get(a.id);req.onsuccess=()=>{if(!req.result)tx.objectStore('attempts').add(a);};}for(const s of sessions){const req=tx.objectStore('sessions').get(s.id);req.onsuccess=()=>{if(!req.result)tx.objectStore('sessions').add(s);};}tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error);});}finally{db.close();}
}
