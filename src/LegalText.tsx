import {createElement,useMemo,Fragment} from 'react';
import type {ReactNode} from 'react';
import type {Article} from './types';
const allowed=new Set(['p','div','span','b','strong','i','em','u','sup','sub','br','ul','ol','li','table','thead','tbody','tfoot','tr','td','th','caption','h3','h4','h5']);
export function LegalText({article,assets}:{article:Article;assets:Record<string,string>}){
 const tree=useMemo(()=>{
  if(article.id_norma==='marco')return <div className="literal">{article.texto}</div>;
  const doc=new DOMParser().parseFromString(article.texto_xml,'text/xml');
  if(doc.querySelector('parsererror'))return <div className="literal">{article.texto}</div>;
  function node(n:Node,key:number):ReactNode{
   if(n.nodeType===Node.TEXT_NODE)return n.textContent;
   if(n.nodeType!==Node.ELEMENT_NODE)return null;
   const e=n as Element,tag=e.tagName.toLowerCase();
   if(['script','style','iframe'].includes(tag)||(e.parentNode===doc.documentElement&&(tag==='blockquote'||(e.getAttribute('class')??'').includes('nota'))))return null;
   if(tag==='img'){const original=new URL(e.getAttribute('src')??'',article.url_fuente).href;const local=assets[original];return local?<img key={key} src={import.meta.env.BASE_URL+local} alt={e.getAttribute('alt')||'Figura de la fuente oficial'} loading="lazy"/>:<a key={key} href={original} target="_blank" rel="noreferrer">Figura en fuente oficial</a>;}
   const children=Array.from(e.childNodes).map((child,i)=>node(child,i));
   if(!allowed.has(tag))return <Fragment key={key}>{children}</Fragment>;
   const props:Record<string,unknown>={key};
   if(tag==='td'||tag==='th'){for(const attr of ['colspan','rowspan']){const v=Number(e.getAttribute(attr));if(v>0&&v<100)props[attr==='colspan'?'colSpan':'rowSpan']=v;}}
   return createElement(tag,props,...children);
  }
  return node(doc.documentElement,0);
 },[article,assets]);
 return <div className="legal-text">{tree}</div>;
}
