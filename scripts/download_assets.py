import json
from network import ROOT, download

if __name__ == '__main__':
    queue = json.loads((ROOT/'data/recursos_pendientes.json').read_text())
    results = []
    for i,item in enumerate(queue):
        try:
            path,meta=download(item['url'],accept='image/*')
            results.append(dict(**item,**meta,estado='descargado'))
        except Exception as error:
            results.append(dict(**item,error=str(error),estado='pendiente'))
        (ROOT/'data/recursos_descargados.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
        if i % 25 == 0 or results[-1]['estado']=='pendiente':
            print(i+1,len(queue),results[-1]['estado'],flush=True)
