import type {Attempt} from './types';
export function Analytics({attempts}:{attempts:Attempt[]}){
 const days=[...new Set(attempts.map(a=>a.date.slice(0,10)))].sort().slice(-14);
 const ids=[...new Set(attempts.map(a=>a.articleId))];
 return <><h2>Evolución por día</h2><div className="table-scroll"><table><thead><tr><th>Fecha</th><th>Intentos</th><th>Aciertos</th><th>Porcentaje</th></tr></thead><tbody>{days.map(day=>{const list=attempts.filter(a=>a.date.startsWith(day)),success=list.filter(a=>a.success).length;return <tr key={day}><td>{day}</td><td>{list.length}</td><td>{success}</td><td>{Math.round(success*100/list.length)} %</td></tr>;})}</tbody></table></div><h2>Rendimiento por artículo</h2><div className="table-scroll"><table><thead><tr><th>Artículo</th><th>Intentos</th><th>Aciertos</th><th>Errores</th><th>Frecuencia de error</th></tr></thead><tbody>{ids.map(id=>{const list=attempts.filter(a=>a.articleId===id),errors=list.filter(a=>!a.success).length;return <tr key={id}><td>{id}</td><td>{list.length}</td><td>{list.length-errors}</td><td>{errors}</td><td>{Math.round(errors*100/list.length)} %</td></tr>;})}</tbody></table></div></>;
}
