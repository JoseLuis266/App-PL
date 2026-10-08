import {test,expect} from '@playwright/test';
import type {LiteralCard} from '../src/types';

async function pilot(page:import('@playwright/test').Page,mode='Test',amount='1'){
 await page.goto('/#estudio');await page.getByRole('button',{name:'Tema 2 · Derechos fundamentales',exact:true}).click();
 await page.getByRole('button',{name:new RegExp('^'+mode+' ')}).click();
 await page.getByRole('spinbutton',{name:'Número de ejercicios'}).fill(amount);
 await expect(page.getByRole('button',{name:'Comenzar sesión'})).toBeEnabled();
}

test('test pilot saves real literal correction, summary and targeted retry after reload',async({page})=>{
 await pilot(page);await page.getByRole('button',{name:'Comenzar sesión'}).click();
 const bank=(await (await page.request.get('/legal/manifest.json')).json()).banco_literal as LiteralCard[];
 const prompt=await page.locator('.exercise h2').textContent();
 const current=bank.find(c=>c.cita.slice(0,c.inicio_respuesta)+' [____] '+c.cita.slice(c.inicio_respuesta+c.respuesta.length)===prompt);expect(current).toBeTruthy();
 const options=page.locator('.options button');expect(await options.count()).toBe(4);
 const values=await options.allTextContents();await options.nth(values.findIndex(v=>!v.endsWith(current!.respuesta))).click();
 await page.getByRole('button',{name:'Corregir y guardar'}).click();await expect(page.getByRole('heading',{name:'Para repasar',exact:true})).toBeVisible();
 await expect(page.locator('.official-quote')).toHaveText(current!.cita);await expect(page.locator('.answer-word')).toHaveText(current!.respuesta);
 await page.getByRole('button',{name:'Ver resultados'}).click();await expect(page.getByText('Una sesión más, un paso adelante.')).toBeVisible();
 await page.getByRole('button',{name:'Mis errores',exact:true}).click();await expect(page.getByText('1 fallos',{exact:false})).toBeVisible();
 await page.reload();await page.getByRole('button',{name:'Practicar de nuevo'}).click();await expect(page.locator('.exercise h2')).toHaveText(prompt!);
 const activeSessions=await page.evaluate(()=>new Promise<number>(resolve=>{const req=indexedDB.open('pl-study-personal',2);req.onsuccess=()=>{const db=req.result,tx=db.transaction('sessions'),r=tx.objectStore('sessions').getAll();r.onsuccess=()=>resolve(r.result.filter(s=>s.status==='active').length);tx.oncomplete=()=>db.close();};}));expect(activeSessions).toBe(1);
});

test('flashcard self-assessment is kept when pausing, closing and resuming',async({page})=>{
 await pilot(page,'Flashcards','2');await page.getByRole('button',{name:'Comenzar sesión'}).click();
 await page.getByRole('button',{name:'Revelar respuesta'}).click();await expect(page.locator('.official-quote')).toBeVisible();
 await page.getByRole('button',{name:'Lo recordaba',exact:true}).click();await expect(page.getByRole('button',{name:'Siguiente →'})).toBeVisible();
 await page.getByRole('button',{name:'Pausar · Guardado'}).click();await page.reload();await page.getByRole('button',{name:'Continuar sesión'}).click();
 await expect(page.getByRole('button',{name:'Siguiente →'})).toBeVisible();await page.getByRole('button',{name:'Siguiente →'}).click();
 await page.getByRole('button',{name:'Revelar respuesta'}).click();await page.getByRole('button',{name:'Necesito repasarlo',exact:true}).click();
 await page.getByRole('button',{name:'Ver resultados'}).click();await expect(page.getByText('Recuerdo autoevaluado',{exact:false})).toBeVisible();
 const records=await page.evaluate(()=>new Promise<unknown[]>((resolve,reject)=>{const req=indexedDB.open('pl-study-personal',2);req.onsuccess=()=>{const db=req.result,tx=db.transaction('attempts'),read=tx.objectStore('attempts').getAll();read.onsuccess=()=>resolve(read.result);tx.oncomplete=()=>db.close();};req.onerror=()=>reject(req.error);}));expect(records).toHaveLength(2);
});

test('cloze uses the exact source answer; case normalization is accepted',async({page})=>{
 await pilot(page,'Completar');await page.getByRole('button',{name:'Comenzar sesión'}).click();
 const data=await (await page.request.get('/legal/manifest.json')).json(),prompt=await page.locator('.exercise h2').textContent();
 const card=(data.banco_literal as LiteralCard[]).find(c=>c.cita.slice(0,c.inicio_respuesta)+' [____] '+c.cita.slice(c.inicio_respuesta+c.respuesta.length)===prompt)!;
 await page.getByRole('textbox',{name:'Completa el hueco'}).fill(card.respuesta.toLocaleUpperCase('es-ES'));
 await page.getByRole('button',{name:'Corregir y guardar'}).click();await expect(page.getByRole('heading',{name:'Respuesta correcta',exact:true})).toBeVisible();
});

test('matching is an interactive round with unique source references',async({page})=>{
 await pilot(page,'Relacionar','4');await page.getByRole('button',{name:'Comenzar sesión'}).click();
 const selects=page.locator('.match-item select');await expect(selects).toHaveCount(4);
 const stored=await page.evaluate(()=>new Promise<any>((resolve,reject)=>{const req=indexedDB.open('pl-study-personal',2);req.onsuccess=()=>{const db=req.result,tx=db.transaction('sessions'),r=tx.objectStore('sessions').getAll();r.onsuccess=()=>resolve(r.result.find(s=>s.status==='active'));tx.oncomplete=()=>db.close();};req.onerror=()=>reject(req.error);}));
 for(let i=0;i<4;i++)await selects.nth(i).selectOption(stored.questions[i].matchKey??stored.questions[i].article.id_articulo);
 await page.getByRole('button',{name:'Corregir y guardar'}).click();await expect(page.locator('.answer-status.success')).toHaveCount(4);
 await page.getByRole('button',{name:'Ver resultados'}).click();await expect(page.getByText('100%',{exact:true})).toBeVisible();
});

test('free recall reveals the complete literal passage and stores written recall',async({page})=>{
 await pilot(page,'Recuperación libre');await page.getByRole('button',{name:'Comenzar sesión'}).click();
 await page.getByRole('textbox',{name:'Mi recuerdo (opcional)'}).fill('Mi respuesta personal de prueba');
 await page.getByRole('button',{name:'Revelar respuesta'}).click();await expect(page.locator('.official-quote')).toBeVisible();
 await page.getByRole('button',{name:'Necesito repasarlo',exact:true}).click();await page.getByRole('button',{name:'Ver resultados'}).click();
 await page.getByRole('button',{name:'Mis errores',exact:true}).click();await expect(page.getByText('Tu respuesta: Mi respuesta personal de prueba',{exact:true})).toBeVisible();
});

test('old version-1 progress survives the IndexedDB schema migration',async({page})=>{
 await page.route('**/fixture-start',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><html lang="es"><body>Fixture de migración</body></html>'}));
 await page.goto('/fixture-start');
 await page.evaluate(()=>new Promise<void>((resolve,reject)=>{const req=indexedDB.open('pl-study-personal',1);req.onupgradeneeded=()=>{req.result.createObjectStore('memory',{keyPath:'articleId'});req.result.createObjectStore('attempts',{keyPath:'id'});};req.onsuccess=()=>{const db=req.result,tx=db.transaction('memory','readwrite');tx.objectStore('memory').put({articleId:'ce:a14',first:'2026-01-01T12:00:00Z',last:'2026-01-01T12:00:00Z',due:'2026-01-02T12:00:00Z',interval:1,repetitions:1,difficulty:false,status:'memorizado',sourceHash:'fixture-existing'});tx.oncomplete=()=>{db.close();resolve();};};req.onerror=()=>reject(req.error);}));
 await page.goto('/#repasos');await expect(page.getByText('Primera memorización: 1/1/2026',{exact:false})).toBeVisible();
 const version=await page.evaluate(()=>new Promise<number>(resolve=>{const req=indexedDB.open('pl-study-personal');req.onsuccess=()=>{resolve(req.result.version);req.result.close();};}));expect(version).toBe(2);
});

test('mobile study and all-topic selection retain responsive layout',async({page})=>{
 await page.setViewportSize({width:390,height:844});await pilot(page);await page.getByRole('button',{name:'Mezclar los tres pilotos →'}).click();
 await expect(page.getByRole('button',{name:'Comenzar sesión'})).toBeEnabled();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'test-results/mobile-estudio.png',fullPage:true});
 await page.getByRole('button',{name:'Comenzar sesión'}).click();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
