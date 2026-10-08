import json
from database import connect
from network import ROOT,download

if __name__=='__main__':
    db=connect();results=[]
    rows=list(db.execute('SELECT id_norma,url_fuente FROM normas ORDER BY rowid'))
    db.close()
    for row in rows:
        try:
            path,m=download(row['url_fuente'],accept='text/html,application/pdf')
            results.append(dict(id_norma=row['id_norma'],resultado='respuesta_200',**m))
        except Exception as error:results.append(dict(id_norma=row['id_norma'],url=row['url_fuente'],resultado='error',error=str(error)))
        (ROOT/'data/enlaces-verificados.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print('Enlaces',len(results),'errores',sum(r['resultado']=='error' for r in results))
